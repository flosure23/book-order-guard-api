from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

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
    return {
        "status": "ok",
        "service": "Book Order Guard API"
    }