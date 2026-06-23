import os

MODEL_MODE = os.getenv("MODEL_MODE", "mlflow")

MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "sqlite:///mlflow.db",
)

MODEL_NAME = "book-order-review-model"

MODEL_URI = os.getenv(
    "MODEL_URI",
    f"models:/{MODEL_NAME}@champion",
)

RISK_LEVEL_LOW_MAX = 0.40
RISK_LEVEL_MEDIUM_MAX = 0.50

EXPERIMENT_NAME = "book-order-review-risk"