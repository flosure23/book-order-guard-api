from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
import app.order_ml as order_ml_module
from app.ml_schemas import ModelInfoResponse
from app.order_ml import get_risk_level

client = TestClient(main_module.app)


class FakeModel:
    named_steps = {
        "classifier": SimpleNamespace(classes_=[0, 1]),
    }

    def predict_proba(self, input_df):
        expected_columns = [
            "unit_price",
            "quantity",
            "stock",
            "customer_age_days",
            "previous_order_count",
            "recent_order_count_7d",
            "coupon_usage_count_30d",
            "member_grade",
            "coupon_code",
            "region",
            "is_preorder",
            "address_risk_level",
        ]
        assert list(input_df.columns) == expected_columns
        return [[0.20, 0.80] for _ in range(len(input_df))]


@pytest.fixture(autouse=True)
def mock_serving_model(monkeypatch):
    fake_model = FakeModel()
    fake_info = ModelInfoResponse(
        model_name="book-order-review-model",
        model_uri="models:/book-order-review-model@champion",
        model_type="FakeModelForTest",
        f1_score=0.90,
        run_id="test-run-id",
        loaded=True,
    )

    monkeypatch.setattr(order_ml_module, "load_model", lambda: fake_model)
    monkeypatch.setattr(order_ml_module, "get_model_info", lambda: fake_info)
    monkeypatch.setattr(main_module, "load_model", lambda: fake_model)
    monkeypatch.setattr(main_module, "get_model_info", lambda: fake_info)
    monkeypatch.setattr(main_module, "save_prediction_log", lambda payload, result: None)
    monkeypatch.setattr(main_module, "save_feedback", lambda payload: None)


def make_ml_order(**overrides):
    base_order = {
        "book_id": "B-ML-001",
        "title": "MLOps Practice Book",
        "unit_price": 90000,
        "quantity": 2,
        "stock": 20,
        "member_grade": "BASIC",
        "coupon_code": "WELCOME10",
        "region": "NORMAL",
        "customer_age_days": 6,
        "previous_order_count": 0,
        "recent_order_count_7d": 4,
        "coupon_usage_count_30d": 5,
        "is_preorder": False,
        "address_risk_level": "HIGH",
    }

    base_order.update(overrides)
    return base_order


def test_model_health():
    response = client.get("/model/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["model_loaded"] is True


def test_model_health_returns_503_when_model_cannot_load(monkeypatch):
    def raise_load_error():
        raise FileNotFoundError("test model missing")

    monkeypatch.setattr(main_module, "load_model", raise_load_error)

    response = client.get("/model/health")

    assert response.status_code == 503


def test_model_info():
    response = client.get("/model/info")

    assert response.status_code == 200

    data = response.json()

    assert data["model_name"] == "book-order-review-model"
    assert "loaded" in data


def test_risk_level_thresholds():
    assert get_risk_level(0.10) == "LOW"
    assert get_risk_level(0.40) == "MEDIUM"
    assert get_risk_level(0.49) == "MEDIUM"
    assert get_risk_level(0.50) == "HIGH"
    assert get_risk_level(0.95) == "HIGH"


def test_validate_with_ml_response_structure():
    response = client.post(
        "/orders/validate-with-ml",
        json=make_ml_order(),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["rule_status"] in ["APPROVED", "REJECTED", "REVIEW"]
    assert data["review_risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert data["ml_recommendation"] in ["APPROVED", "REVIEW"]
    assert data["final_status"] in ["APPROVED", "REJECTED", "REVIEW"]
    assert isinstance(data["risk_reasons"], list)
    assert 0.0 <= data["review_risk_score"] <= 1.0


def test_rule_rejection_has_priority_over_high_ml_risk():
    response = client.post(
        "/orders/validate-with-ml",
        json=make_ml_order(quantity=30, stock=20),
    )

    assert response.status_code == 200
    assert response.json()["rule_status"] == "REJECTED"
    assert response.json()["final_status"] == "REJECTED"


def test_invalid_ml_input_returns_422():
    response = client.post(
        "/orders/validate-with-ml",
        json=make_ml_order(customer_age_days=-1),
    )

    assert response.status_code == 422


def test_feedback_api():
    response = client.post(
        "/feedback",
        json={
            "order_id": "ORDER-TEST-001",
            "order": make_ml_order(),
            "prediction": "REVIEW",
            "correct_label": "APPROVED",
            "score": 0.82,
            "serving_model": "book-order-review-model@champion",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"


def test_rejected_order_feedback_is_not_saved():
    response = client.post(
        "/feedback",
        json={
            "order_id": "ORDER-REJECTED-001",
            "order": make_ml_order(quantity=30, stock=20),
            "prediction": "REVIEW",
            "correct_label": "REVIEW",
            "score": 0.82,
            "serving_model": "book-order-review-model@champion",
        },
    )

    assert response.status_code == 400