import logging

import pandas as pd

from app.config import RISK_LEVEL_LOW_MAX, RISK_LEVEL_MEDIUM_MAX
from app.ml_schemas import (
    MlRecommendation,
    OrderRiskRequest,
    OrderRiskResponse,
    ReviewRiskLevel,
)
from app.model_loader import get_model_info, load_model
from app.rules import validate_order
from app.schemas import OrderRequest, OrderStatus

logger = logging.getLogger("book-order-guard-ml")

FEATURE_COLUMNS = [
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


def to_order_request(payload: OrderRiskRequest) -> OrderRequest:
    return OrderRequest(
        book_id=payload.book_id,
        title=payload.title,
        unit_price=payload.unit_price,
        quantity=payload.quantity,
        stock=payload.stock,
        member_grade=payload.member_grade,
        coupon_code=payload.coupon_code,
        region=payload.region,
    )


def build_feature_row(payload: OrderRiskRequest) -> dict:
    return {
        "unit_price": payload.unit_price,
        "quantity": payload.quantity,
        "stock": payload.stock,
        "customer_age_days": payload.customer_age_days,
        "previous_order_count": payload.previous_order_count,
        "recent_order_count_7d": payload.recent_order_count_7d,
        "coupon_usage_count_30d": payload.coupon_usage_count_30d,
        "member_grade": payload.member_grade,
        "coupon_code": payload.coupon_code or "NONE",
        "region": payload.region,
        "is_preorder": int(payload.is_preorder),
        "address_risk_level": payload.address_risk_level,
    }


def get_risk_level(score: float) -> ReviewRiskLevel:
    if score < RISK_LEVEL_LOW_MAX:
        return "LOW"
    if score < RISK_LEVEL_MEDIUM_MAX:
        return "MEDIUM"
    return "HIGH"


def get_ml_recommendation(risk_level: ReviewRiskLevel) -> MlRecommendation:
    if risk_level == "HIGH":
        return "REVIEW"
    return "APPROVED"


def get_final_status(rule_status: OrderStatus, risk_level: ReviewRiskLevel) -> OrderStatus:
    if rule_status == "REJECTED":
        return "REJECTED"

    if rule_status == "REVIEW":
        return "REVIEW"

    if rule_status == "APPROVED" and risk_level == "HIGH":
        return "REVIEW"

    return "APPROVED"


def generate_risk_reasons(payload: OrderRiskRequest, score: float, risk_level: ReviewRiskLevel) -> list[str]:
    reasons: list[str] = []

    original_price = payload.unit_price * payload.quantity
    remaining_stock = payload.stock - payload.quantity

    if payload.customer_age_days <= 30 and original_price >= 50_000:
        reasons.append("신규 고객의 고액 주문입니다.")

    if payload.recent_order_count_7d >= 3:
        reasons.append("최근 7일 주문 횟수가 많습니다.")

    if payload.coupon_usage_count_30d >= 3:
        reasons.append("최근 30일 쿠폰 사용 횟수가 많습니다.")

    if remaining_stock <= 2:
        reasons.append("주문 후 잔여 재고가 낮습니다.")

    if payload.is_preorder and payload.quantity >= 2:
        reasons.append("예약판매 상품의 다량 주문입니다.")

    if payload.address_risk_level == "HIGH":
        reasons.append("배송지 위험도가 높습니다.")

    if risk_level == "HIGH" and not reasons:
        reasons.append("여러 주문 조건이 복합적으로 검토 위험을 높였습니다.")

    if risk_level == "LOW" and not reasons:
        reasons.append("검토 위험을 높이는 주요 조건이 발견되지 않았습니다.")

    if risk_level == "MEDIUM" and not reasons:
        reasons.append("일부 조건에서 검토 가능성이 있으나 고위험 수준은 아닙니다.")

    return reasons


def predict_review_risk_score(payload: OrderRiskRequest) -> float:
    model = load_model()
    feature_row = build_feature_row(payload)
    input_df = pd.DataFrame([feature_row], columns=FEATURE_COLUMNS)

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(input_df)[0]

        classifier = getattr(model, "named_steps", {}).get("classifier")
        classes = list(getattr(classifier, "classes_", [0, 1]))

        if 1 in classes:
            positive_index = classes.index(1)
            return float(probabilities[positive_index])

        return float(max(probabilities))

    prediction = model.predict(input_df)[0]
    return 1.0 if int(prediction) == 1 else 0.0


def evaluate_order_with_ml(payload: OrderRiskRequest) -> OrderRiskResponse:
    rule_result = validate_order(to_order_request(payload))

    score = predict_review_risk_score(payload)
    risk_level = get_risk_level(score)
    ml_recommendation = get_ml_recommendation(risk_level)
    final_status = get_final_status(rule_result.status, risk_level)
    risk_reasons = generate_risk_reasons(payload, score, risk_level)
    model_info = get_model_info()

    logger.info(
        "ML order risk evaluated book_id=%s rule_status=%s score=%.4f risk_level=%s final_status=%s",
        payload.book_id,
        rule_result.status,
        score,
        risk_level,
        final_status,
    )

    return OrderRiskResponse(
        rule_status=rule_result.status,
        review_risk_score=round(score, 4),
        review_risk_level=risk_level,
        ml_recommendation=ml_recommendation,
        final_status=final_status,
        risk_reasons=risk_reasons,
        model_info=model_info,
    )