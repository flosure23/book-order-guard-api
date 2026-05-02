from app.schemas import OrderRequest, PriceResult

MEMBER_DISCOUNT_RATES = {
    "BASIC": 0,
    "SILVER": 5,
    "GOLD": 10,
    "VIP": 15,
}

FREE_SHIPPING_THRESHOLD = 30_000
SHIPPING_FEE = 3_000
WELCOME_COUPON_CODE = "WELCOME10"
WELCOME_COUPON_RATE = 10


def calculate_price(order: OrderRequest) -> PriceResult:
    original_price = order.unit_price * order.quantity

    member_rate = MEMBER_DISCOUNT_RATES[order.member_grade]
    member_discount = original_price * member_rate // 100

    after_member_discount = original_price - member_discount

    coupon_discount = 0
    if order.coupon_code == WELCOME_COUPON_CODE:
        coupon_discount = after_member_discount * WELCOME_COUPON_RATE // 100

    discounted_price = after_member_discount - coupon_discount

    shipping_fee = 0 if discounted_price > FREE_SHIPPING_THRESHOLD else SHIPPING_FEE
    final_price = discounted_price + shipping_fee

    return PriceResult(
        original_price=original_price,
        member_discount=member_discount,
        coupon_discount=coupon_discount,
        shipping_fee=shipping_fee,
        final_price=final_price,
    )