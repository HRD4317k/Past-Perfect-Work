"""Entry point kept for backward compatibility (Procfile / deployments run `api:app`).

The service now lives in ml_service/ (FastAPI + SQLAlchemy). POST /predict still
accepts {"product_type", "original_price"} and returns "predicted_depreciation",
so the Flask web app works unchanged.
"""
import uvicorn

from ml_service.main import app  # noqa: F401

if __name__ == "__main__":
    uvicorn.run("ml_service.main:app", host="0.0.0.0", port=8000)
