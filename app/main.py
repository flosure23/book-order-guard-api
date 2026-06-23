import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.feedback import save_feedback
from app.logging_config import setup_logging
from app.ml_schemas import (
    FeedbackRequest,
    FeedbackResponse,
    ModelInfoResponse,
    OrderRiskRequest,
    OrderRiskResponse,
)
from app.model_loader import get_model_info, load_model
from app.order_ml import evaluate_order_with_ml, to_order_request
from app.prediction_logger import save_prediction_log
from app.rules import get_rules, validate_order
from app.schemas import OrderRequest, OrderResponse

setup_logging()
logger = logging.getLogger("book-order-guard")

app = FastAPI(title="Book Order Guard ML API")

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def home():
    index_path = STATIC_DIR / "index.html"

    if index_path.exists():
        return index_path.read_text(encoding="utf-8")

    return """
    <html>
        <body>
            <h1>Book Order Guard ML API</h1>
            <p>UI page is not ready yet.</p>
        </body>
    </html>
    """


@app.get("/health")
def health_check():
    logger.info("health check requested")
    return {
        "status": "ok",
        "service": "Book Order Guard ML API",
    }


@app.post("/orders/validate", response_model=OrderResponse)
def validate_book_order(order: OrderRequest):
    logger.info(
        "order validation requested book_id=%s quantity=%s grade=%s region=%s",
        order.book_id,
        order.quantity,
        order.member_grade,
        order.region,
    )

    result = validate_order(order)

    logger.info(
        "order validation result status=%s final_price=%s reasons=%s",
        result.status,
        result.price.final_price,
        result.reasons,
    )

    return result


@app.post("/orders/validate-with-ml", response_model=OrderRiskResponse)
def validate_book_order_with_ml(order: OrderRiskRequest):
    logger.info("order validation with ML requested book_id=%s", order.book_id)

    result = evaluate_order_with_ml(order)
    save_prediction_log(order, result)

    logger.info(
        "order validation with ML result rule_status=%s risk_score=%s risk_level=%s final_status=%s",
        result.rule_status,
        result.review_risk_score,
        result.review_risk_level,
        result.final_status,
    )

    return result


@app.get("/model/health")
def model_health():
    try:
        load_model()
        info = get_model_info()
        return {
            "status": "ok",
            "model_loaded": info.loaded,
            "model_name": info.model_name,
            "model_uri": info.model_uri,
        }
    except Exception as exc:
        logger.exception("model health check failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "model_loaded": False,
                "message": str(exc),
            },
        ) from exc


@app.get("/model/info", response_model=ModelInfoResponse)
def model_info():
    return get_model_info()


@app.post("/feedback", response_model=FeedbackResponse)
def feedback(payload: FeedbackRequest):
    rule_result = validate_order(to_order_request(payload.order))

    if rule_result.status == "REJECTED":
        raise HTTPException(
            status_code=400,
            detail="REJECTED 주문은 검토 필요 예측의 재학습 데이터에서 제외합니다.",
        )

    save_feedback(payload)

    logger.info(
        "feedback saved order_id=%s prediction=%s correct_label=%s score=%s",
        payload.order_id,
        payload.prediction,
        payload.correct_label,
        payload.score,
    )

    return FeedbackResponse(
        status="ok",
        message="피드백 저장을 완료했습니다.",
    )


@app.get("/rules")
def rules():
    return {
        "rules": get_rules(),
        "ml_risk_level_rules": [
            {
                "name": "낮음(LOW)",
                "description": "위험 점수가 0.00 이상 0.40 미만인 경우입니다.",
            },
            {
                "name": "중간(MEDIUM)",
                "description": "위험 점수가 0.40 이상 0.50 미만인 경우입니다.",
            },
            {
                "name": "높음(HIGH)",
                "description": "위험 점수가 0.50 이상인 경우이며, 룰상 주문 가능 상태라도 검토 필요(REVIEW)로 전환합니다.",
            },
        ],
    }


@app.get("/logs-test")
def logs_test():
    logger.info("logs test endpoint requested")
    logger.warning("this is a warning log for operation check")
    return {
        "message": "log test completed",
    }