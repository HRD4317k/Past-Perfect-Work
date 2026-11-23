"""PastPerfect pricing & demand service (FastAPI + SQLAlchemy).

Endpoints
    GET  /health                    model version + status
    POST /predict                   price suggestion for one item (backward compatible with
                                    the old {"product_type", "original_price"} payload)
    POST /predict/batch             many items in one call
    POST /observations              record a realised sale (feeds retraining)
    POST /retrain                   retrain in the background; promote only if better
    GET  /demand/top                Demand Board: top categories by open buyer requests

Every response carries an `X-Process-Time-ms` header so latency can be measured
under load (see loadtest/locustfile.py).
"""
import os
import threading
import time
from contextlib import asynccontextmanager
from typing import List, Optional

import pandas as pd
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from ml_service.db import Demand, ModelVersion, PriceObservation, SessionLocal, init_db
from ml_service.pricing import PriceModel, train_and_compare

MODEL_PATH = os.getenv("PRICE_MODEL_PATH", "artifacts/price_model.joblib")
SEED_DATA = os.getenv("PRICE_SEED_CSV", "")          # optional CSV merged into retraining data

_state = {"model": None, "version": None}
_retrain_lock = threading.Lock()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db(include_demand=os.getenv("CREATE_DEMAND_TABLE", "0") == "1")
    if os.path.exists(MODEL_PATH):
        _state["model"] = PriceModel.load(MODEL_PATH)
        _state["version"] = _state["model"].model_name
    yield


app = FastAPI(title="PastPerfect Pricing Service", version="2.0.0", lifespan=lifespan)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.middleware("http")
async def _timing(request: Request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time-ms"] = f"{(time.perf_counter() - t0) * 1000:.2f}"
    return response


# ── Schemas ───────────────────────────────────────────────────────────────────

class ProductInput(BaseModel):
    product_type: str = Field(..., min_length=1, max_length=64)
    original_price: float = Field(..., gt=0, le=1_000_000)
    age_months: Optional[float] = Field(None, ge=0, le=240)
    condition: Optional[int] = Field(None, ge=1, le=5)


class PriceOutput(BaseModel):
    predicted_depreciation: float
    suggested_price: float
    price_low: Optional[float]
    price_high: Optional[float]
    model: str


class Observation(ProductInput):
    sale_price: float = Field(..., ge=0)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": _state["model"] is not None, "model": _state["version"]}


def _require_model() -> PriceModel:
    if _state["model"] is None:
        raise HTTPException(503, "No price model loaded. Train one with train_price_model.py.")
    return _state["model"]


@app.post("/predict", response_model=PriceOutput)
def predict(item: ProductInput):
    model = _require_model()
    p = model.predict([item.model_dump()])[0]
    return PriceOutput(model=model.model_name, **{k: p[k] for k in
                       ("predicted_depreciation", "suggested_price", "price_low", "price_high")})


@app.post("/predict/batch", response_model=List[PriceOutput])
def predict_batch(items: List[ProductInput]):
    if not items or len(items) > 500:
        raise HTTPException(400, "send between 1 and 500 items")
    model = _require_model()
    preds = model.predict([i.model_dump() for i in items])
    return [PriceOutput(model=model.model_name, **{k: p[k] for k in
            ("predicted_depreciation", "suggested_price", "price_low", "price_high")}) for p in preds]


@app.post("/observations", status_code=201)
def add_observation(obs: Observation, db: Session = Depends(get_db)):
    if obs.sale_price > obs.original_price * 1.5:
        raise HTTPException(422, "sale_price is implausibly high for the original price")
    db.add(PriceObservation(**obs.model_dump()))
    db.commit()
    return {"stored": True}


def _retrain_job() -> None:
    if not _retrain_lock.acquire(blocking=False):
        return                                   # a retrain is already running
    try:
        with SessionLocal() as db:
            rows = db.execute(select(PriceObservation)).scalars().all()
            df = pd.DataFrame([{c: getattr(r, c) for c in
                                ("product_type", "original_price", "sale_price", "age_months", "condition")}
                               for r in rows])
            if SEED_DATA and os.path.exists(SEED_DATA):
                df = pd.concat([pd.read_csv(SEED_DATA), df], ignore_index=True)
            report = train_and_compare(df)
            new = report["model"]
            current = _state["model"]
            if current is not None and current.metrics and \
                    new.metrics["mae_rs"] > current.metrics.get("mae_rs", float("inf")):
                return                           # not better: keep serving the current model
            new.save(MODEL_PATH)
            _state["model"], _state["version"] = new, new.model_name
            acc_key = next(k for k in new.metrics if k.startswith("accuracy"))
            db.add(ModelVersion(model_name=new.model_name, path=MODEL_PATH, n_train=report["n_rows"],
                                holdout_mae=new.metrics["mae_rs"], holdout_accuracy=new.metrics[acc_key]))
            db.commit()
    finally:
        _retrain_lock.release()


@app.post("/retrain", status_code=202)
def retrain(background: BackgroundTasks):
    if _retrain_lock.locked():
        return {"status": "already_running"}
    background.add_task(_retrain_job)
    return {"status": "scheduled"}


@app.get("/demand/top")
def demand_top(college: Optional[str] = None, limit: int = 4, db: Session = Depends(get_db)):
    """Demand Board ranking: one GROUP BY over open buyer requests."""
    t0 = time.perf_counter()
    q = select(Demand.sub_cat, func.count(Demand.id).label("requests"))
    if college:
        q = q.where(Demand.college == college)
    q = q.group_by(Demand.sub_cat).order_by(desc("requests")).limit(max(1, min(limit, 20)))
    rows = db.execute(q).all()
    return {"college": college, "top": [{"category": r.sub_cat, "requests": r.requests} for r in rows],
            "query_ms": round((time.perf_counter() - t0) * 1000, 2)}
