import csv
from datetime import datetime
from pathlib import Path

from app.ml_schemas import OrderRiskRequest, OrderRiskResponse

PREDICTION_LOG_PATH = Path("logs/predictions.csv")


def save_prediction_log(payload: OrderRiskRequest, result: OrderRiskResponse) -> None:
    PREDICTION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    is_new = not PREDICTION_LOG_PATH.exists()

    with PREDICTION_LOG_PATH.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if is_new:
            writer.writerow(
                [
                    "time",
                    "book_id",
                    "title",
                    "rule_status",
                    "review_risk_score",
                    "review_risk_level",
                    "ml_recommendation",
                    "final_status",
                    "serving_model",
                ]
            )

        writer.writerow(
            [
                datetime.now().isoformat(timespec="seconds"),
                payload.book_id,
                payload.title,
                result.rule_status,
                result.review_risk_score,
                result.review_risk_level,
                result.ml_recommendation,
                result.final_status,
                result.model_info.model_uri or result.model_info.model_name,
            ]
        )