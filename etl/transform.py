"""
transform.py — Transform layer of the Heart Disease ETL pipeline.
"""

import logging
from pathlib import Path

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

PROCESSED_PATH = Path(__file__).resolve().parents[1] / "data" / "processed"


def transform(df: pd.DataFrame) -> dict:
    df = df.copy()
    stats = {}

    # 1. Drop surrogate index
    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])
        logger.info("Dropped surrogate index column")

    # 2. Handle missing values
    null_before = df.isnull().sum().sum()
    for col in ["Ca", "Thal"]:
        if df[col].isnull().any():
            fill_val = df[col].mode()[0]
            df[col] = df[col].fillna(fill_val)
            logger.info("Filled %s nulls with mode=%s", col, fill_val)
    null_after = df.isnull().sum().sum()
    stats["nulls_removed"] = int(null_before - null_after)

    # 3. Rename columns to snake_case
    rename_map = {
        "Age": "age",
        "Sex": "sex",
        "ChestPain": "chest_pain",
        "RestBP": "rest_bp",
        "Chol": "cholesterol",
        "Fbs": "fasting_blood_sugar",
        "RestECG": "rest_ecg",
        "MaxHR": "max_hr",
        "ExAng": "exercise_angina",
        "Oldpeak": "st_depression",
        "Slope": "slope",
        "Ca": "ca_vessels",
        "Thal": "thal",
        "AHD": "heart_disease",
    }
    df = df.rename(columns=rename_map)
    logger.info("Columns renamed to snake_case")

    # 4. Cast types
    df["ca_vessels"] = df["ca_vessels"].astype(int)
    df["heart_disease"] = df["heart_disease"].str.strip()

    # 5. Feature engineering
    df["age_group"] = pd.cut(
        df["age"],
        bins=[0, 40, 50, 60, 100],
        labels=["<40", "40-50", "50-60", "60+"],
    )
    df["chol_risk"] = pd.cut(
        df["cholesterol"],
        bins=[0, 200, 239, 9999],
        labels=["Desirable", "Borderline", "High"],
    )
    df["hr_reserve"] = (220 - df["age"]) - df["max_hr"]
    df["target"] = (df["heart_disease"] == "Yes").astype(int)

    logger.info("Feature engineering complete — added age_group, chol_risk, hr_reserve, target")
    stats["rows"] = len(df)
    stats["features"] = len(df.columns)

    # 6. Build ML-ready encoded copy
    encoded = df.copy()

    # One-hot encode categoricals — cast booleans to int immediately
    for col in ["chest_pain", "thal"]:
        dummies = pd.get_dummies(encoded[col], prefix=col, drop_first=False).astype(int)
        encoded = pd.concat([encoded.drop(columns=[col]), dummies], axis=1)

    # Label-encode ordinal categoricals
    encoded["age_group"] = encoded["age_group"].cat.codes
    encoded["chol_risk"] = encoded["chol_risk"].cat.codes

    # Drop the string target (keep binary 'target')
    encoded = encoded.drop(columns=["heart_disease"])

    # Ensure all columns are numeric
    encoded = encoded.apply(pd.to_numeric, errors="coerce")

    logger.info("Encoding complete — ML dataset has %d columns", len(encoded.columns))
    stats["ml_features"] = len(encoded.columns)

    return {"cleaned": df, "encoded": encoded, "summary": stats}
