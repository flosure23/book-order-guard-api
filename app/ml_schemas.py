from typing import Literal

from pydantic import BaseModel, Field

from app.schemas import MemberGrade, OrderStatus, RegionCode


AddressRiskLevel = Literal["LOW", "MEDIUM", "HIGH"]
ReviewRiskLevel = Literal["LOW", "MEDIUM", "HIGH"]
MlRecommendation = Literal["APPROVED", "REVIEW"]


class OrderRiskRequest(BaseModel):
    book_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    unit_price: int = Field(gt=0)
    quantity: int = Field(gt=0)
    stock: int = Field(ge=0)
    member_grade: MemberGrade
    coupon_code: str | None = None
    region: RegionCode = "NORMAL"

    customer_age_days: int = Field(ge=0)
    previous_order_count: int = Field(ge=0)
    recent_order_count_7d: int = Field(ge=0)
    coupon_usage_count_30d: int = Field(ge=0)
    is_preorder: bool = False
    address_risk_level: AddressRiskLevel = "LOW"


class ModelInfoResponse(BaseModel):
    model_name: str
    model_uri: str | None = None
    model_type: str | None = None
    f1_score: float | None = None
    run_id: str | None = None
    loaded: bool


class OrderRiskResponse(BaseModel):
    rule_status: OrderStatus
    review_risk_score: float = Field(ge=0.0, le=1.0)
    review_risk_level: ReviewRiskLevel
    ml_recommendation: MlRecommendation
    final_status: OrderStatus
    risk_reasons: list[str]
    model_info: ModelInfoResponse


class FeedbackRequest(BaseModel):
    order_id: str = Field(min_length=1)
    order: OrderRiskRequest
    prediction: MlRecommendation
    correct_label: MlRecommendation
    score: float = Field(ge=0.0, le=1.0)
    serving_model: str = "unknown"


class FeedbackResponse(BaseModel):
    status: str
    message: str