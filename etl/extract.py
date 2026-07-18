"""
extract.py — Extract layer of the Heart Disease ETL pipeline.

Reads raw Heart.csv from the data/raw directory,
performs schema validation, and returns a clean DataFrame
ready for the transform stage.
"""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

RAW_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "Heart.csv"

EXPECTED_COLUMNS = {
    "Unnamed: 0": "int64",
    "Age": "int64",
    "Sex": "int64",
    "ChestPain": "object",
    "RestBP": "int64",
    "Chol": "int64",
    "Fbs": "int64",
    "RestECG": "int64",
    "MaxHR": "int64",
    "ExAng": "int64",
    "Oldpeak": "float64",
    "Slope": "int64",
    "Ca": "float64",
    "Thal": "object",
    "AHD": "object",
}


def extract(source_path=None) -> pd.DataFrame:
    """
    Load raw CSV from *source_path* and validate its schema.

    Returns
    -------
    pd.DataFrame
        Raw DataFrame with all original columns present.
    """
    if source_path is None:
        source_path = RAW_PATH
    source_path = Path(source_path)

    if not source_path.exists():
        raise FileNotFoundError(f"Raw data not found at: {source_path}")

    logger.info("Extracting data from %s", source_path)
    df = pd.read_csv(source_path)
    logger.info("Loaded %d rows x %d columns", *df.shape)

    missing = set(EXPECTED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    logger.info("Schema validation passed")
    return df
