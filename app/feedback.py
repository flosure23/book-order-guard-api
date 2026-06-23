import csv
from datetime import datetime
from pathlib import Path

from app.ml_schemas import FeedbackRequest

FEEDBACK_LOG_PATH = Path("logs/feedback.csv")


def save_feedback(payload: FeedbackRequest) -> None:
    FEEDBACK_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    is_new = not FEEDBACK_LOG_PATH.exists()

    with FEEDBACK_LOG_PATH.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if is_new:
            writer.writerow(
                [
                    "time",
                    "order_id",
                    "book_id",
                    "title",
                    "unit_price",
                    "quantity",
                    "stock",
                    "member_grade",
                    "coupon_code",
                    "region",
                    "customer_age_days",
                    "previous_order_count",
                    "recent_order_count_7d",
                    "coupon_usage_count_30d",
                    "is_preorder",
                    "address_risk_level",
                    "prediction",
                    "correct_label",
                    "score",
                    "serving_model",
                    "manual_review_needed",
                ]
            )

        label = 1 if payload.correct_label == "REVIEW" else 0

        writer.writerow(
            [
                datetime.now().isoformat(timespec="seconds"),
                payload.order_id,
                payload.order.book_id,
                payload.order.title,
                payload.order.unit_price,
                payload.order.quantity,
                payload.order.stock,
                payload.order.member_grade,
                payload.order.coupon_code or "NONE",
                payload.order.region,
                payload.order.customer_age_days,
                payload.order.previous_order_count,
                payload.order.recent_order_count_7d,
                payload.order.coupon_usage_count_30d,
                int(payload.order.is_preorder),
                payload.order.address_risk_level,
                payload.prediction,
                payload.correct_label,
                round(float(payload.score), 4),
                payload.serving_model,
                label,
            ]
        )