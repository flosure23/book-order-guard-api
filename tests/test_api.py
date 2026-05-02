from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def make_order(**overrides):
    base_order = {
        "book_id": "B001",
        "title": "Database Systems",
        "unit_price": 20000,
        "quantity": 1,
        "stock": 5,
        "member_grade": "BASIC",
        "coupon_code": None,
        "region": "NORMAL",
    }
    base_order.update(overrides)
    return base_order


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_approved_order():
    response = client.post(
        "/orders/validate",
        json=make_order(
            unit_price=20000,
            quantity=1,
            stock=5,
            member_grade="BASIC",
            region="NORMAL",
        ),
    )

    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "APPROVED"
    assert data["reasons"] == []


def test_rejected_when_out_of_stock():
    response = client.post(
        "/orders/validate",
        json=make_order(
            quantity=6,
            stock=5,
        ),
    )

    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "REJECTED"
    assert "OUT_OF_STOCK" in data["reasons"]


def test_invalid_quantity_zero():
    response = client.post(
        "/orders/validate",
        json=make_order(quantity=0),
    )

    assert response.status_code == 422


def test_invalid_unit_price_zero():
    response = client.post(
        "/orders/validate",
        json=make_order(unit_price=0),
    )

    assert response.status_code == 422


def test_gold_member_discount():
    response = client.post(
        "/orders/validate",
        json=make_order(
            unit_price=50000,
            quantity=1,
            stock=5,
            member_grade="GOLD",
        ),
    )

    data = response.json()

    assert response.status_code == 200
    assert data["price"]["original_price"] == 50000
    assert data["price"]["member_discount"] == 5000


def test_welcome_coupon_discount():
    response = client.post(
        "/orders/validate",
        json=make_order(
            unit_price=50000,
            quantity=1,
            stock=5,
            member_grade="BASIC",
            coupon_code="WELCOME10",
        ),
    )

    data = response.json()

    assert response.status_code == 200
    assert data["price"]["coupon_discount"] == 5000


def test_free_shipping_boundary():
    response = client.post(
        "/orders/validate",
        json=make_order(
            unit_price=30000,
            quantity=1,
            stock=5,
            member_grade="BASIC",
        ),
    )

    data = response.json()

    assert response.status_code == 200
    assert data["price"]["shipping_fee"] == 0


def test_remote_island_region_needs_review():
    response = client.post(
        "/orders/validate",
        json=make_order(
            unit_price=20000,
            quantity=1,
            stock=5,
            region="REMOTE_ISLAND",
        ),
    )

    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "REVIEW"
    assert "REGION_REVIEW_REQUIRED" in data["reasons"]


def test_low_stock_needs_review():
    response = client.post(
        "/orders/validate",
        json=make_order(
            unit_price=20000,
            quantity=4,
            stock=5,
        ),
    )

    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "REVIEW"
    assert "LOW_STOCK_REVIEW" in data["reasons"]


def test_overseas_region_rejected():
    response = client.post(
        "/orders/validate",
        json=make_order(
            unit_price=20000,
            quantity=1,
            stock=5,
            region="OVERSEAS",
        ),
    )

    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "REJECTED"
    assert "OVERSEAS_NOT_SUPPORTED" in data["reasons"]