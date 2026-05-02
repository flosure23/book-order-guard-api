from app.pricing import WELCOME_COUPON_CODE, calculate_price
from app.schemas import OrderRequest, OrderResponse

REVIEW_REGIONS = {"REMOTE_ISLAND", "MILITARY_PO_BOX"}
REJECTED_REGIONS = {"OVERSEAS"}


def validate_order(order: OrderRequest) -> OrderResponse:
    rejected_reasons: list[str] = []
    review_reasons: list[str] = []

    if order.coupon_code not in (None, "", WELCOME_COUPON_CODE):
        rejected_reasons.append("INVALID_COUPON")

    if order.region in REJECTED_REGIONS:
        rejected_reasons.append("OVERSEAS_NOT_SUPPORTED")

    if order.quantity > order.stock:
        rejected_reasons.append("OUT_OF_STOCK")

    if not rejected_reasons:
        remaining_stock = order.stock - order.quantity

        if remaining_stock <= 1:
            review_reasons.append("LOW_STOCK_REVIEW")

        if order.region in REVIEW_REGIONS:
            review_reasons.append("REGION_REVIEW_REQUIRED")

    price = calculate_price(order)

    if rejected_reasons:
        return OrderResponse(
            status="REJECTED",
            message="주문을 처리할 수 없습니다.",
            price=price,
            reasons=rejected_reasons,
        )

    if review_reasons:
        return OrderResponse(
            status="REVIEW",
            message="주문 확인이 필요합니다.",
            price=price,
            reasons=review_reasons,
        )

    return OrderResponse(
        status="APPROVED",
        message="주문이 승인되었습니다.",
        price=price,
        reasons=[],
    )


def get_rules() -> list[dict[str, str]]:
    return [
        {
            "name": "재고 검사",
            "description": "주문 수량이 재고보다 많으면 주문 불가로 처리합니다.",
        },
        {
            "name": "입력값 검사",
            "description": "단가, 수량, 재고, 회원 등급 등 기본 입력값을 검증합니다.",
        },
        {
            "name": "회원 등급 할인",
            "description": "BASIC 0%, SILVER 5%, GOLD 10%, VIP 15% 할인을 적용합니다.",
        },
        {
            "name": "쿠폰 할인",
            "description": "WELCOME10 쿠폰 입력 시 추가 10% 할인을 적용합니다.",
        },
        {
            "name": "무료배송 기준",
            "description": "할인 적용 후 상품 금액이 30,000원 이상이면 배송비를 0원으로 계산합니다.",
        },
        {
            "name": "배송 지역 검사",
            "description": "해외 배송은 주문 불가, 도서산간/군부대 사서함은 확인 필요로 처리합니다.",
        },
        {
            "name": "낮은 잔여 재고 검사",
            "description": "주문 후 잔여 재고가 1권 이하이면 확인 필요로 처리합니다.",
        },
    ]