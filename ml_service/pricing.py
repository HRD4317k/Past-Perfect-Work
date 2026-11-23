"""Resale price models: Linear Regression vs Bayesian Ridge.

Target: depreciation ratio = 1 - sale_price / original_price, so one model
serves items from Rs 50 to Rs 50,000. Features: product category (one-hot),
log original price, and optionally age (months) and condition (1-5).

Bayesian Ridge also returns a predictive standard deviation, which the API turns
into a suggested price *range* instead of a single number.

Metrics reported on a held-out split:
    MAE (Rs), R^2 on sale price, and accuracy = share of predictions within
    +/- `tolerance` (default 15%) of the realised sale price.
"""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import BayesianRidge, LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

CATEGORICAL = ["product_type"]
NUMERIC_ALWAYS = ["original_price"]
NUMERIC_OPTIONAL = ["age_months", "condition"]
MODELS = {"linear_regression": LinearRegression, "bayesian_ridge": BayesianRidge}


def _numeric_columns(df: pd.DataFrame) -> List[str]:
    return NUMERIC_ALWAYS + [c for c in NUMERIC_OPTIONAL if c in df.columns and df[c].notna().any()]


def build_pipeline(model_name: str, numeric_cols: List[str]) -> Pipeline:
    numeric = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("log_price", FunctionTransformer(_log_first_column, feature_names_out="one-to-one")),
        ("scale", StandardScaler()),
    ])
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
        ("num", numeric, numeric_cols),
    ])
    return Pipeline([("pre", pre), ("model", MODELS[model_name]())])


def _log_first_column(x):
    x = np.array(x, dtype=float, copy=True)
    x[:, 0] = np.log1p(np.clip(x[:, 0], 0, None))   # original_price is always first
    return x


def within_tolerance(y_true: np.ndarray, y_pred: np.ndarray, tol: float = 0.15) -> float:
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    return float(np.mean(np.abs(y_pred - y_true) <= tol * np.abs(y_true)))


def validate_frame(df: pd.DataFrame) -> pd.DataFrame:
    missing = {"product_type", "original_price", "sale_price"} - set(df.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    df = df.copy()
    df["product_type"] = df["product_type"].astype(str).str.strip().str.lower()
    df = df[(df["original_price"] > 0) & (df["sale_price"] >= 0) & (df["sale_price"] <= df["original_price"] * 1.5)]
    if len(df) < 20:
        raise ValueError("need at least 20 valid rows to train")
    return df


@dataclass
class PriceModel:
    model_name: str
    pipeline: Pipeline
    numeric_cols: List[str]
    metrics: Dict[str, float] = field(default_factory=dict)

    def _frame(self, rows: List[Dict]) -> pd.DataFrame:
        df = pd.DataFrame(rows)
        df["product_type"] = df["product_type"].astype(str).str.strip().str.lower()
        for c in self.numeric_cols:
            if c not in df.columns:
                df[c] = np.nan
        return df[CATEGORICAL + self.numeric_cols]

    def predict(self, rows: List[Dict]) -> List[Dict[str, Optional[float]]]:
        X = self._frame(rows)
        price = X["original_price"].to_numpy(float)
        if self.model_name == "bayesian_ridge":
            ratio, std = self.pipeline.predict(X, return_std=True)
        else:
            ratio, std = self.pipeline.predict(X), None
        ratio = np.clip(ratio, 0.0, 0.95)
        out = []
        for i, r in enumerate(ratio):
            item = {"depreciation_ratio": float(r), "predicted_depreciation": float(r * price[i]),
                    "suggested_price": float(price[i] * (1 - r)), "price_low": None, "price_high": None}
            if std is not None:
                lo, hi = np.clip(r + 1.645 * std[i], 0, 0.95), np.clip(r - 1.645 * std[i], 0, 0.95)
                item["price_low"], item["price_high"] = float(price[i] * (1 - lo)), float(price[i] * (1 - hi))
            out.append(item)
        return out

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)), suffix=".tmp")
        os.close(fd)
        joblib.dump(self, tmp)
        os.replace(tmp, path)                     # atomic: readers never see a half-written file

    @staticmethod
    def load(path: str) -> "PriceModel":
        return joblib.load(path)


def train_and_compare(df: pd.DataFrame, tolerance: float = 0.15, seed: int = 42,
                      test_size: float = 0.2) -> Dict:
    """Fit both models on the same split; return metrics for each and the best model."""
    df = validate_frame(df)
    numeric_cols = _numeric_columns(df)
    y_ratio = 1.0 - df["sale_price"] / df["original_price"]
    stratify = df["product_type"] if df["product_type"].value_counts().min() >= 2 else None
    tr, te = train_test_split(df.index, test_size=test_size, random_state=seed, stratify=stratify)

    results, fitted = {}, {}
    for name in MODELS:
        pipe = build_pipeline(name, numeric_cols).fit(df.loc[tr, CATEGORICAL + numeric_cols], y_ratio.loc[tr])
        pm = PriceModel(name, pipe, numeric_cols)
        pred_price = np.array([p["suggested_price"] for p in pm.predict(df.loc[te].to_dict("records"))])
        true_price = df.loc[te, "sale_price"].to_numpy(float)
        pm.metrics = {
            "mae_rs": float(mean_absolute_error(true_price, pred_price)),
            "r2_sale_price": float(r2_score(true_price, pred_price)),
            f"accuracy_within_{int(tolerance * 100)}pct": within_tolerance(true_price, pred_price, tolerance),
        }
        results[name], fitted[name] = pm.metrics, pm

    best = min(results, key=lambda n: results[n]["mae_rs"])
    # refit the winner on all rows for serving
    final = PriceModel(best, build_pipeline(best, numeric_cols).fit(df[CATEGORICAL + numeric_cols], y_ratio),
                       numeric_cols, metrics=results[best])
    return {
        "n_rows": int(len(df)), "n_categories": int(df["product_type"].nunique()),
        "n_train": int(len(tr)), "n_holdout": int(len(te)), "tolerance": tolerance,
        "features": CATEGORICAL + numeric_cols, "results": results, "best_model": best, "model": final,
    }


def report_json(report: Dict) -> str:
    return json.dumps({k: v for k, v in report.items() if k != "model"}, indent=2)
