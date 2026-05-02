import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.logging_config import setup_logging
from app.rules import get_rules, validate_order
from app.schemas import OrderRequest, OrderResponse

setup_logging()
logger = logging.getLogger("book-order-guard")

app = FastAPI(title="Book Order Guard API")

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
            <h1>Book Order Guard API</h1>
            <p>UI page is not ready yet.</p>
        </body>
    </html>
    """


@app.get("/health")
def health_check():
    logger.info("health check requested")
    return {
        "status": "ok",
        "service": "Book Order Guard API"
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


@app.get("/rules")
def rules():
    return {
        "rules": get_rules()
    }


@app.get("/logs-test")
def logs_test():
    logger.info("logs test endpoint requested")
    logger.warning("this is a warning log for operation check")
    return {
        "message": "log test completed"
    }