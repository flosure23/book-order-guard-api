from typing import Literal

from pydantic import BaseModel, Field


MemberGrade = Literal["BASIC", "SILVER", "GOLD", "VIP"]
RegionCode = Literal["NORMAL", "REMOTE_ISLAND", "MILITARY_PO_BOX", "OVERSEAS"]
OrderStatus = Literal["APPROVED", "REJECTED", "REVIEW"]


class OrderRequest(BaseModel):
    book_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    unit_price: int = Field(gt=0)
    quantity: int = Field(gt=0)
    stock: int = Field(ge=0)
    member_grade: MemberGrade
    coupon_code: str | None = None
    region: RegionCode = "NORMAL"


class PriceResult(BaseModel):
    original_price: int
    member_discount: int
    coupon_discount: int
    shipping_fee: int
    final_price: int


class OrderResponse(BaseModel):
    status: OrderStatus
    message: str
    price: PriceResult
    reasons: list[str]