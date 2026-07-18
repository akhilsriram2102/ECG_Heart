"""
tests/test_etl.py — Unit tests for the ETL pipeline.

Run:
    pytest tests/ -v
"""

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Minimal fixture data that mirrors the real schema
FIXTURE_DATA = {
    "Unnamed: 0": [1, 2, 3, 4, 5],
    "Age":         [63, 67, 37, 41, 56],
    "Sex":         [1,  1,  1,  0,  1],
    "ChestPain":   ["typical", "asymptomatic", "nonanginal", "nontypical", "asymptomatic"],
    "RestBP":      [145, 160, 130, 130, 120],
    "Chol":        [233, 286, 250, 204, 236],
    "Fbs":         [1, 0, 0, 0, 0],
    "RestECG":     [2, 2, 0, 2, 0],
    "MaxHR":       [150, 108, 187, 172, 178],
    "ExAng":       [0, 1, 0, 0, 0],
    "Oldpeak":     [2.3, 1.5, 3.5, 1.4, 0.8],
    "Slope":       [3, 2, 3, 1, 1],
    "Ca":          [0.0, 3.0, 0.0, 0.0, 0.0],
    "Thal":        ["fixed", "normal", "normal", "normal", "normal"],
    "AHD":         ["No", "Yes", "No", "No", "No"],
}


@pytest.fixture
def raw_df():
    return pd.DataFrame(FIXTURE_DATA)


@pytest.fixture
def csv_file(raw_df, tmp_path):
    path = tmp_path / "Heart.csv"
    raw_df.to_csv(path, index=False)
    return path


# ── Extract tests ──────────────────────────────────────────────────────────────

def test_extract_returns_dataframe(csv_file):
    from etl.extract import extract
    df = extract(csv_file)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 5


def test_extract_missing_file():
    from etl.extract import extract
    with pytest.raises(FileNotFoundError):
        extract("/nonexistent/path/Heart.csv")


def test_extract_schema_validation(csv_file):
    """All expected columns must be present after extraction."""
    from etl.extract import extract, EXPECTED_COLUMNS
    df = extract(csv_file)
    for col in EXPECTED_COLUMNS:
        assert col in df.columns, f"Missing column: {col}"


# ── Transform tests ────────────────────────────────────────────────────────────

def test_transform_output_keys(raw_df):
    from etl.transform import transform
    result = transform(raw_df)
    assert set(result.keys()) == {"cleaned", "encoded", "summary"}


def test_transform_drops_surrogate_index(raw_df):
    from etl.transform import transform
    result = transform(raw_df)
    assert "Unnamed: 0" not in result["cleaned"].columns


def test_transform_renames_columns(raw_df):
    from etl.transform import transform
    df = transform(raw_df)["cleaned"]
    assert "age" in df.columns
    assert "cholesterol" in df.columns
    assert "heart_disease" in df.columns


def test_transform_feature_engineering(raw_df):
    from etl.transform import transform
    df = transform(raw_df)["cleaned"]
    assert "age_group" in df.columns
    assert "chol_risk" in df.columns
    assert "hr_reserve" in df.columns
    assert "target" in df.columns


def test_transform_target_binary(raw_df):
    from etl.transform import transform
    df = transform(raw_df)["cleaned"]
    assert set(df["target"].unique()).issubset({0, 1})


def test_transform_null_imputation():
    """Ca and Thal nulls should be filled."""
    from etl.transform import transform
    data = FIXTURE_DATA.copy()
    data["Ca"][0] = None
    data["Thal"][1] = None
    df = pd.DataFrame(data)
    result = transform(df)["cleaned"]
    assert result["ca_vessels"].isnull().sum() == 0
    assert result["thal"].isnull().sum() == 0


def test_transform_encoded_all_numeric(raw_df):
    from etl.transform import transform
    encoded = transform(raw_df)["encoded"]
    non_numeric = encoded.select_dtypes(exclude="number").columns.tolist()
    assert len(non_numeric) == 0, f"Non-numeric columns in encoded df: {non_numeric}"


# ── Load tests ─────────────────────────────────────────────────────────────────

def test_load_creates_csv_files(raw_df, tmp_path, monkeypatch):
    from etl import transform as transform_module
    from etl import load as load_module

    monkeypatch.setattr(load_module, "PROCESSED_PATH", tmp_path / "processed")
    monkeypatch.setattr(load_module, "REPORTS_PATH", tmp_path / "reports")

    from etl.transform import transform
    from etl.load import load

    transformed = transform(raw_df)
    outputs = load(transformed)

    assert Path(outputs["cleaned_csv"]).exists()
    assert Path(outputs["encoded_csv"]).exists()
    assert Path(outputs["report"]).exists()


def test_load_report_is_valid_json(raw_df, tmp_path, monkeypatch):
    from etl import load as load_module
    monkeypatch.setattr(load_module, "PROCESSED_PATH", tmp_path / "processed")
    monkeypatch.setattr(load_module, "REPORTS_PATH", tmp_path / "reports")

    from etl.transform import transform
    from etl.load import load

    transformed = transform(raw_df)
    outputs = load(transformed)

    with open(outputs["report"]) as fh:
        report = json.load(fh)
    assert "run_timestamp" in report
    assert "rows" in report
