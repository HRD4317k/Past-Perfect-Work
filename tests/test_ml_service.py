"""Tests for the pricing service. Synthetic data here is only for testing the code."""
import os
import tempfile

import numpy as np
import pandas as pd
import pytest

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["PRICE_MODEL_PATH"] = f"{_tmp}/price_model.joblib"
os.environ["CREATE_DEMAND_TABLE"] = "1"

from fastapi.testclient import TestClient  # noqa: E402

from ml_service import main as svc  # noqa: E402
from ml_service.db import Demand, SessionLocal  # noqa: E402
from ml_service.pricing import PriceModel, train_and_compare, within_tolerance  # noqa: E402

RATES = {"calculator": 0.25, "cycle": 0.40, "course_books": 0.55, "lab_coat": 0.30, "earbuds": 0.50}


def synthetic(n=600, seed=0):
    rng = np.random.default_rng(seed)
    cats = rng.choice(list(RATES), n)
    price = rng.uniform(200, 15000, n)
    age = rng.uniform(1, 36, n)
    cond = rng.integers(1, 6, n)
    ratio = np.array([RATES[c] for c in cats]) + 0.004 * age + 0.03 * cond + rng.normal(0, 0.03, n)
    return pd.DataFrame({"product_type": cats, "original_price": price, "age_months": age,
                         "condition": cond, "sale_price": price * (1 - np.clip(ratio, 0, 0.9))})


def test_within_tolerance():
    assert within_tolerance([100, 100, 100], [110, 120, 86], 0.15) == pytest.approx(2 / 3)


def test_train_compares_both_models_and_picks_lower_mae():
    rep = train_and_compare(synthetic())
    assert set(rep["results"]) == {"linear_regression", "bayesian_ridge"}
    best = rep["best_model"]
    assert all(rep["results"][best]["mae_rs"] <= m["mae_rs"] for m in rep["results"].values())
    assert rep["results"][best]["accuracy_within_15pct"] > 0.5
    assert rep["features"] == ["product_type", "original_price", "age_months", "condition"]


def test_bayesian_model_returns_price_range(tmp_path):
    rep = train_and_compare(synthetic())
    from ml_service.pricing import build_pipeline
    pm = PriceModel("bayesian_ridge", build_pipeline("bayesian_ridge", rep["model"].numeric_cols).fit(
        synthetic()[["product_type", "original_price", "age_months", "condition"]],
        1 - synthetic()["sale_price"] / synthetic()["original_price"]), rep["model"].numeric_cols)
    p = pm.predict([{"product_type": "cycle", "original_price": 5000, "age_months": 12, "condition": 3}])[0]
    assert p["price_low"] <= p["suggested_price"] <= p["price_high"]
    pm.save(str(tmp_path / "m.joblib"))
    assert PriceModel.load(str(tmp_path / "m.joblib")).predict([{"product_type": "cycle", "original_price": 5000}])


def test_validation_rejects_bad_frames():
    with pytest.raises(ValueError):
        train_and_compare(pd.DataFrame({"product_type": ["a"], "original_price": [1]}))


@pytest.fixture(scope="module")
def client():
    with TestClient(svc.app) as c:
        yield c


def test_api_flow(client):
    assert client.post("/predict", json={"product_type": "cycle", "original_price": 5000}).status_code == 503

    df = synthetic(300)
    for row in df.to_dict("records"):
        assert client.post("/observations", json=row).status_code == 201
    assert client.post("/retrain").status_code == 202          # TestClient runs background tasks

    health = client.get("/health").json()
    assert health["model_loaded"] is True

    r = client.post("/predict", json={"product_type": "cycle", "original_price": 5000})
    assert r.status_code == 200
    body = r.json()
    assert 0 < body["suggested_price"] < 5000
    assert body["predicted_depreciation"] == pytest.approx(5000 - body["suggested_price"])
    assert float(r.headers["X-Process-Time-ms"]) >= 0

    batch = client.post("/predict/batch", json=[{"product_type": "lab_coat", "original_price": 800}] * 3)
    assert batch.status_code == 200 and len(batch.json()) == 3


def test_input_validation(client):
    assert client.post("/predict", json={"product_type": "cycle", "original_price": -5}).status_code == 422
    bad = {"product_type": "cycle", "original_price": 100, "sale_price": 1000}
    assert client.post("/observations", json=bad).status_code == 422


def test_demand_top(client):
    with SessionLocal() as db:
        for cat, n in [("cycle", 5), ("calculator", 3), ("mattress", 7), ("kettle", 1), ("lab_coat", 2)]:
            db.add_all([Demand(sub_cat=cat, college="IIT Kharagpur") for _ in range(n)])
        db.add(Demand(sub_cat="kettle", college="IIT Bombay"))
        db.commit()
    body = client.get("/demand/top", params={"college": "IIT Kharagpur"}).json()
    assert [t["category"] for t in body["top"]] == ["mattress", "cycle", "calculator", "lab_coat"]
    assert body["top"][0]["requests"] == 7
