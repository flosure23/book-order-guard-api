import os
from pathlib import Path
import joblib

import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.config import EXPERIMENT_NAME, MLFLOW_TRACKING_URI, MODEL_NAME


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ARTIFACT_DIR = Path(
    os.getenv("MODEL_ARTIFACT_DIR", str(BASE_DIR / "artifacts"))
)

TRAIN_DATA_PATH = Path(
    os.getenv("TRAIN_DATA_PATH", str(DATA_DIR / "orders_train.csv"))
)
TEST_DATA_PATH = DATA_DIR / "orders_test.csv"

LABEL_COLUMN = "manual_review_needed"

NUMERIC_FEATURES = [
    "unit_price",
    "quantity",
    "stock",
    "customer_age_days",
    "previous_order_count",
    "recent_order_count_7d",
    "coupon_usage_count_30d",
]

CATEGORICAL_FEATURES = [
    "member_grade",
    "coupon_code",
    "region",
    "is_preorder",
    "address_risk_level",
]

FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def load_data():
    train_df = pd.read_csv(TRAIN_DATA_PATH)
    test_df = pd.read_csv(TEST_DATA_PATH)

    x_train = train_df[FEATURE_COLUMNS]
    y_train = train_df[LABEL_COLUMN]

    x_test = test_df[FEATURE_COLUMNS]
    y_test = test_df[LABEL_COLUMN]

    return train_df, test_df, x_train, y_train, x_test, y_test


def build_pipeline(model):
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", model),
        ]
    )


def get_candidate_models():
    return {
        "LogisticRegression": LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=42,
        ),
        "RandomForestClassifier": RandomForestClassifier(
            n_estimators=120,
            max_depth=5,
            class_weight="balanced",
            random_state=42,
        ),
    }


def write_classification_report(model_type: str, y_test, y_pred) -> Path:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    report_path = ARTIFACT_DIR / f"classification_report_{model_type}.txt"

    report = classification_report(
        y_test,
        y_pred,
        zero_division=0,
    )

    report_path.write_text(report, encoding="utf-8")

    return report_path


def smoke_test_model(model_path: Path, sample_df: pd.DataFrame) -> None:
    model = joblib.load(model_path)
    probabilities = model.predict_proba(sample_df)[0]

    if len(probabilities) != 2:
        raise RuntimeError("binary classification probability output is required")

    if not all(0.0 <= float(value) <= 1.0 for value in probabilities):
        raise RuntimeError("prediction probability is outside the valid range")

    print(f"Smoke test probability={probabilities.tolist()}")


def main():
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_registry_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    train_df, test_df, x_train, y_train, x_test, y_test = load_data()

    results = []

    for model_type, model in get_candidate_models().items():
        pipeline = build_pipeline(model)

        with mlflow.start_run(run_name=f"{model_type}-order-risk") as run:
            pipeline.fit(x_train, y_train)

            y_pred = pipeline.predict(x_test)
            score = f1_score(y_test, y_pred, zero_division=0)

            report_path = write_classification_report(model_type, y_test, y_pred)

            local_model_path = ARTIFACT_DIR / f"{model_type}_review_risk_model.joblib"
            joblib.dump(pipeline, local_model_path)

            mlflow.log_param("model_type", model_type)
            mlflow.log_param("train_file", TRAIN_DATA_PATH.name)
            mlflow.log_param("test_file", TEST_DATA_PATH.name)
            mlflow.log_param("train_row_count", len(train_df))
            mlflow.log_param("test_row_count", len(test_df))
            mlflow.log_param("feature_count", len(FEATURE_COLUMNS))
            mlflow.log_param("label", LABEL_COLUMN)

            mlflow.log_metric("f1_score", score)

            mlflow.log_artifact(str(report_path))
            mlflow.log_artifact(str(local_model_path))

            mlflow.sklearn.log_model(
                sk_model=pipeline,
                name="model",
                registered_model_name=MODEL_NAME,
            )

            results.append(
                {
                    "run_id": run.info.run_id,
                    "model_type": model_type,
                    "f1_score": score,
                    "local_model_path": local_model_path,
                }
            )

            print(f"{model_type} f1_score={score:.4f}")

    best_result = max(results, key=lambda item: item["f1_score"])

    best_model_path = ARTIFACT_DIR / "review_risk_model.joblib"
    best_pipeline = joblib.load(best_result["local_model_path"])
    joblib.dump(best_pipeline, best_model_path)
    smoke_test_model(best_model_path, x_test.iloc[[0]])

    print("Best model selected")
    print(f"model_type={best_result['model_type']}")
    print(f"f1_score={best_result['f1_score']:.4f}")
    print(f"local_best_model={best_model_path}")
    print("Champion alias is not changed automatically.")
    print("Check the MLflow Model Registry and assign @champion manually.")


if __name__ == "__main__":
    main()