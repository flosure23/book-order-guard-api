import pandas as pd

import app.feedback as feedback_module
from app.feedback import save_feedback
from app.ml_schemas import FeedbackRequest, OrderRiskRequest
from ml.build_retraining_data import build_retraining_data


def make_feedback_request() -> FeedbackRequest:
    order = OrderRiskRequest(
        book_id="B-FEEDBACK-001",
        title="Feedback MLOps Book",
        unit_price=90000,
        quantity=2,
        stock=20,
        member_grade="BASIC",
        coupon_code="WELCOME10",
        region="NORMAL",
        customer_age_days=6,
        previous_order_count=0,
        recent_order_count_7d=4,
        coupon_usage_count_30d=5,
        is_preorder=False,
        address_risk_level="HIGH",
    )

    return FeedbackRequest(
        order_id="ORDER-FEEDBACK-001",
        order=order,
        prediction="REVIEW",
        correct_label="REVIEW",
        score=0.82,
        serving_model="book-order-review-model@champion",
    )


def test_save_feedback_contains_training_features(tmp_path, monkeypatch):
    feedback_path = tmp_path / "feedback.csv"
    monkeypatch.setattr(
        feedback_module,
        "FEEDBACK_LOG_PATH",
        feedback_path,
    )

    save_feedback(make_feedback_request())

    saved_df = pd.read_csv(feedback_path)

    assert saved_df.loc[0, "unit_price"] == 90000
    assert saved_df.loc[0, "address_risk_level"] == "HIGH"
    assert saved_df.loc[0, "manual_review_needed"] == 1


def test_build_retraining_data(tmp_path):
    base_path = tmp_path / "orders_train.csv"
    feedback_path = tmp_path / "feedback.csv"
    output_path = tmp_path / "orders_retrain.csv"

    base_df = pd.DataFrame(
        [
            {
                "unit_price": 20000,
                "quantity": 1,
                "stock": 10,
                "member_grade": "BASIC",
                "coupon_code": "NONE",
                "region": "NORMAL",
                "customer_age_days": 300,
                "previous_order_count": 5,
                "recent_order_count_7d": 1,
                "coupon_usage_count_30d": 0,
                "is_preorder": 0,
                "address_risk_level": "LOW",
                "manual_review_needed": 0,
            }
        ]
    )
    feedback_df = pd.DataFrame(
        [
            {
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
                "is_preorder": 0,
                "address_risk_level": "HIGH",
                "manual_review_needed": 1,
            }
        ]
    )

    base_df.to_csv(base_path, index=False)
    feedback_df.to_csv(feedback_path, index=False)

    result = build_retraining_data(
        base_train_path=base_path,
        feedback_path=feedback_path,
        output_path=output_path,
    )

    assert output_path.exists()
    assert len(result) == 2
    assert set(result["manual_review_needed"]) == {0, 1}