import logging
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient

from app.config import (
    LOCAL_MODEL_PATH,
    MLFLOW_TRACKING_URI,
    MODEL_MODE,
    MODEL_NAME,
    MODEL_URI,
)
from app.ml_schemas import ModelInfoResponse

logger = logging.getLogger("book-order-guard-ml")

_model = None
_model_info: ModelInfoResponse | None = None


def _get_mlflow_model_info(loaded: bool) -> ModelInfoResponse:
    try:
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        mlflow.set_registry_uri(MLFLOW_TRACKING_URI)
        client = MlflowClient()

        champion = client.get_model_version_by_alias(MODEL_NAME, "champion")
        run = client.get_run(champion.run_id)

        return ModelInfoResponse(
            model_name=MODEL_NAME,
            model_uri=MODEL_URI,
            model_type=run.data.params.get("model_type"),
            f1_score=run.data.metrics.get("f1_score"),
            run_id=champion.run_id,
            loaded=loaded,
        )
    except Exception as exc:
        logger.warning("failed to get MLflow model info: %s", exc)
        return ModelInfoResponse(
            model_name=MODEL_NAME,
            model_uri=MODEL_URI,
            model_type=None,
            f1_score=None,
            run_id=None,
            loaded=loaded,
        )


def _load_model_from_mlflow():
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_registry_uri(MLFLOW_TRACKING_URI)
    logger.info("loading model from MLflow model_uri=%s", MODEL_URI)
    model = mlflow.sklearn.load_model(MODEL_URI)
    info = _get_mlflow_model_info(loaded=True)
    return model, info


def _load_model_from_local_artifact():
    local_path = Path(LOCAL_MODEL_PATH)

    if not local_path.exists():
        raise FileNotFoundError(f"local model not found: {local_path}")

    logger.info("loading local fallback model path=%s", local_path)
    model = joblib.load(local_path)

    info = ModelInfoResponse(
        model_name=MODEL_NAME,
        model_uri=str(local_path),
        model_type="local_fallback_model",
        f1_score=None,
        run_id=None,
        loaded=True,
    )

    return model, info


def load_model():
    global _model, _model_info

    if _model is not None:
        return _model

    if MODEL_MODE == "local":
        _model, _model_info = _load_model_from_local_artifact()
        return _model

    try:
        _model, _model_info = _load_model_from_mlflow()
    except Exception as exc:
        logger.warning("MLflow model loading failed. fallback to local model. error=%s", exc)
        _model, _model_info = _load_model_from_local_artifact()

    return _model


def clear_model_cache() -> None:
    global _model, _model_info
    _model = None
    _model_info = None


def get_model_info() -> ModelInfoResponse:
    global _model_info

    if _model_info is None:
        try:
            load_model()
        except Exception as exc:
            logger.exception("model info check failed: %s", exc)
            return ModelInfoResponse(
                model_name=MODEL_NAME,
                model_uri=MODEL_URI,
                model_type=None,
                f1_score=None,
                run_id=None,
                loaded=False,
            )

    return _model_info