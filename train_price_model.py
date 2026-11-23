#!/usr/bin/env python3
"""Train and compare the resale price models.

Input CSV columns: product_type, original_price, sale_price
Optional columns:  age_months, condition (1-5)

    python train_price_model.py --data data/resale_listings.csv
    python train_price_model.py --from-db          # use price_observations in DATABASE_URL

Writes the best model to artifacts/price_model.joblib and the comparison report
(Linear Regression vs Bayesian Ridge: MAE, R^2, accuracy within +/-15%) to
reports/price_model_report.json.
"""
import argparse
from pathlib import Path

import pandas as pd

from ml_service.pricing import report_json, train_and_compare


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path)
    ap.add_argument("--from-db", action="store_true")
    ap.add_argument("--tolerance", type=float, default=0.15)
    ap.add_argument("--model-out", default="artifacts/price_model.joblib")
    ap.add_argument("--report-out", type=Path, default=Path("reports/price_model_report.json"))
    args = ap.parse_args()

    if args.from_db:
        from ml_service.db import engine
        df = pd.read_sql_table("price_observations", engine)
    elif args.data:
        df = pd.read_csv(args.data)
    else:
        ap.error("pass --data CSV or --from-db")

    report = train_and_compare(df, tolerance=args.tolerance)
    report["model"].save(args.model_out)
    args.report_out.parent.mkdir(parents=True, exist_ok=True)
    args.report_out.write_text(report_json(report))
    print(report_json(report))
    print(f"\nBest model: {report['best_model']} -> {args.model_out}")


if __name__ == "__main__":
    main()
