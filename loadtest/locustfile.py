"""Load test for the pricing service.

    uvicorn ml_service.main:app --workers 4 --port 8000
    locust -f loadtest/locustfile.py --host http://localhost:8000 \
           --users 5000 --spawn-rate 250 --run-time 3m --headless \
           --csv reports/loadtest

Locust writes reports/loadtest_stats.csv with request counts, failures and the
p50 / p95 / p99 response times per endpoint.
"""
import random

from locust import FastHttpUser, between, task

CATEGORIES = ["calculator", "cycle", "course_books", "lab_coat", "ed_drafter", "mattress",
              "earbuds", "office_chair", "kettle", "watch", "speaker", "novels"]
COLLEGES = ["IIT Kharagpur", "IIT Bombay", "IIT Delhi"]


class MarketplaceUser(FastHttpUser):
    wait_time = between(0.5, 2.0)

    @task(5)
    def predict(self):
        self.client.post("/predict", json={
            "product_type": random.choice(CATEGORIES),
            "original_price": random.randint(100, 20000),
            "age_months": random.randint(1, 48),
            "condition": random.randint(1, 5),
        }, name="/predict")

    @task(2)
    def demand_board(self):
        self.client.get("/demand/top", params={"college": random.choice(COLLEGES)}, name="/demand/top")

    @task(1)
    def health(self):
        self.client.get("/health")
