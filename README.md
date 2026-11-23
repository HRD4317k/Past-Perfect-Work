# PastPerfect

A campus resale marketplace with an **inverse marketplace** twist: buyers post what they need, a **Demand Board** shows sellers the most-requested categories on their campus, and an ML **price service** suggests a fair resale price.

## Architecture

| Component | Tech | Where |
|---|---|---|
| Web app (auth, listings, orders, admin, Demand Board) | Flask, Flask-Login, SQLAlchemy, PostgreSQL, Gunicorn | `app.py`, `templates/` |
| Pricing & demand service | **FastAPI + SQLAlchemy**, scikit-learn | `ml_service/`, `api.py` |
| Media pipeline | Pillow → WebP (quality 85, in memory) → AWS S3 | `app.py` (`/sell`) |
| Payments | PhonePe Standard Checkout, server-side order-status verification | `app.py` |
| Email OTP & notifications | Brevo (sib-api) | `email_notifications.py` |

```
Browser ──► Flask app ──► PostgreSQL
               │   ├──► S3 (WebP images, UUID keys)
               │   ├──► PhonePe (pay → server-side status check before confirming)
               │   └──► Pricing service (FastAPI) ──► price_observations / model_versions / demand
```

## Pricing service (`ml_service/`)

* **Models:** Linear Regression and **Bayesian Ridge** are trained on the same split and compared; the one with lower hold-out MAE is served. Bayesian Ridge also returns a predictive standard deviation, so the API returns a **price range** (`price_low` – `price_high`) as well as a point estimate.
* **Target:** depreciation ratio `1 − sale_price / original_price`, so one model covers items from ₹50 to ₹50,000.
* **Features:** product category (one-hot), log original price, and, when available, age in months and condition (1–5).
* **Metrics** (hold-out): MAE in ₹, R² on sale price, and **accuracy = share of predictions within ±15% of the realised sale price**.
* **Safe retraining:** `POST /observations` stores realised sales; `POST /retrain` retrains in the background (one at a time), and the new model is promoted **only if its hold-out MAE is no worse** than the current one. Model files are written atomically and every promotion is logged in `model_versions`.

| Endpoint | Purpose |
|---|---|
| `GET /health` | status and model in use |
| `POST /predict` | price suggestion (backward compatible with `{"product_type", "original_price"}`) |
| `POST /predict/batch` | up to 500 items per call |
| `POST /observations` | record a realised sale |
| `POST /retrain` | background retrain + guarded promotion |
| `GET /demand/top?college=…` | Demand Board: top categories by open buyer requests (single `GROUP BY`) |

Every response carries an `X-Process-Time-ms` header.

## Run locally

```bash
pip install -r requirements.txt

# 1. Train and compare models on the listings export
#    CSV columns: product_type, original_price, sale_price[, age_months, condition]
python train_price_model.py --data data/resale_listings.csv
#    -> artifacts/price_model.joblib, reports/price_model_report.json

# 2. Start the pricing service
DATABASE_URL=postgresql://... uvicorn ml_service.main:app --workers 4 --port 8000

# 3. Start the web app (points at the service via PRICE_API_URL)
PRICE_API_URL=http://localhost:8000/predict gunicorn app:app
```

## Measure it

```bash
# Model comparison (Linear Regression vs Bayesian Ridge)
cat reports/price_model_report.json

# Load test: 5,000 concurrent users against /predict and /demand/top
locust -f loadtest/locustfile.py --host http://localhost:8000 \
       --users 5000 --spawn-rate 250 --run-time 3m --headless --csv reports/loadtest
#    -> reports/loadtest_stats.csv (requests, failures, p50 / p95 / p99 latency per endpoint)
```

Commit the generated `reports/` files so the numbers quoted about this project can be traced to a run.

## Tests

```bash
pytest -q tests/     # model comparison, price range, validation, API flow, guarded retrain, Demand Board
```

## Maintainer

**Rishabh Dehariya** — IIT Kharagpur · [github.com/HRD4317k](https://github.com/HRD4317k)
