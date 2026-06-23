from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

BASE_TRAIN_PATH = BASE_DIR / "data" / "orders_train.csv"
FEEDBACK_PATH = PROJECT_DIR / "logs" / "feedback.csv"
OUTPUT_PATH = BASE_DIR / "data" / "orders_retrain.csv"

FEATURE_COLUMNS = [
    "unit_price",
    "quantity",
    "stock",
    "member_grade",
    "coupon_code",
    "region",
    "customer_age_days",
    "previous_order_count",
    "recent_order_count_7d",
    "coupon_usage_count_30d",
    "is_preorder",
    "address_risk_level",
]

LABEL_COLUMN = "manual_review_needed"
TRAIN_COLUMNS = FEATURE_COLUMNS + [LABEL_COLUMN]


def build_retraining_data(
    base_train_path: Path = BASE_TRAIN_PATH,
    feedback_path: Path = FEEDBACK_PATH,
    output_path: Path = OUTPUT_PATH,
) -> pd.DataFrame:
    if not feedback_path.exists():
        raise FileNotFoundError(
            f"feedback file not found: {feedback_path}. "
            "Submit feedback from the UI before retraining."
        )

    base_df = pd.read_csv(base_train_path)
    feedback_df = pd.read_csv(feedback_path)

    missing_columns = [
        column for column in TRAIN_COLUMNS if column not in feedback_df.columns
    ]
    if missing_columns:
        raise ValueError(
            f"feedback file is missing training columns: {missing_columns}"
        )

    feedback_train_df = feedback_df[TRAIN_COLUMNS].copy()
    feedback_train_df["coupon_code"] = (
        feedback_train_df["coupon_code"].fillna("NONE").replace("", "NONE")
    )
    feedback_train_df["is_preorder"] = (
        feedback_train_df["is_preorder"]
        .replace({True: 1, False: 0, "True": 1, "False": 0})
        .astype(int)
    )
    feedback_train_df[LABEL_COLUMN] = (
        feedback_train_df[LABEL_COLUMN].astype(int)
    )

    combined_df = pd.concat(
        [base_df[TRAIN_COLUMNS], feedback_train_df],
        ignore_index=True,
    )
    combined_df = combined_df.drop_duplicates(
        subset=FEATURE_COLUMNS,
        keep="last",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined_df.to_csv(output_path, index=False, encoding="utf-8")

    print(f"base rows={len(base_df)}")
    print(f"feedback rows={len(feedback_train_df)}")
    print(f"retraining rows={len(combined_df)}")
    print(f"output={output_path}")

    return combined_df


def main() -> None:
    build_retraining_data()


if __name__ == "__main__":
    main()