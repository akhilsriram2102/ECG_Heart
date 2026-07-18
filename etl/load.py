"""
load.py — Load layer of the Heart Disease ETL pipeline.

Persists transformed DataFrames to the data/processed directory
and generates a run-level JSON summary report.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

PROCESSED_PATH = Path(__file__).resolve().parents[1] / "data" / "processed"
REPORTS_PATH = Path(__file__).resolve().parents[1] / "data" / "reports"


def load(transform_output: dict) -> dict:
    """
    Save cleaned and encoded DataFrames as CSV/Parquet.
    Write a JSON pipeline summary report.

    Parameters
    ----------
    transform_output : dict
        Output of etl.transform.transform()

    Returns
    -------
    dict of output file paths
    """
    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
    REPORTS_PATH.mkdir(parents=True, exist_ok=True)

    cleaned: pd.DataFrame = transform_output["cleaned"]
    encoded: pd.DataFrame = transform_output["encoded"]
    summary: dict = transform_output["summary"]

    run_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # CSV outputs (human-readable)
    cleaned_csv = PROCESSED_PATH / "heart_cleaned.csv"
    encoded_csv = PROCESSED_PATH / "heart_encoded.csv"
    cleaned.to_csv(cleaned_csv, index=False)
    encoded.to_csv(encoded_csv, index=False)
    logger.info("Wrote %s", cleaned_csv)
    logger.info("Wrote %s", encoded_csv)

    # Parquet outputs (columnar, efficient)
    try:
        cleaned_parquet = PROCESSED_PATH / "heart_cleaned.parquet"
        encoded_parquet = PROCESSED_PATH / "heart_encoded.parquet"
        cleaned.to_parquet(cleaned_parquet, index=False)
        encoded.to_parquet(encoded_parquet, index=False)
        logger.info("Wrote parquet files")
    except Exception as exc:
        logger.warning("Parquet write skipped: %s", exc)
        cleaned_parquet = encoded_parquet = None

    # Profile summary
    profile = {
        "run_timestamp": run_ts,
        "pipeline": "heart-disease-etl",
        "rows": summary.get("rows"),
        "features_cleaned": summary.get("features"),
        "features_ml": summary.get("ml_features"),
        "nulls_removed": summary.get("nulls_removed"),
        "target_distribution": cleaned["heart_disease"].value_counts().to_dict(),
        "age_stats": cleaned["age"].describe().round(2).to_dict(),
        "chol_stats": cleaned["cholesterol"].describe().round(2).to_dict(),
        "outputs": {
            "cleaned_csv": str(cleaned_csv),
            "encoded_csv": str(encoded_csv),
        },
    }

    report_path = REPORTS_PATH / f"pipeline_report_{run_ts}.json"
    with open(report_path, "w") as fh:
        json.dump(profile, fh, indent=2)
    logger.info("Pipeline report saved to %s", report_path)

    return {
        "cleaned_csv": str(cleaned_csv),
        "encoded_csv": str(encoded_csv),
        "report": str(report_path),
    }
