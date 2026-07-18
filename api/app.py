"""
app.py — FastAPI service for the Heart Disease data pipeline.

Endpoints:
    GET  /              health check
    POST /pipeline/run  trigger the ETL pipeline
    GET  /data/summary  summary statistics of the cleaned dataset
    GET  /data/records  paginated records from the cleaned dataset
    GET  /reports       list all pipeline reports
    GET  /reports/{ts}  retrieve a specific pipeline report
"""

import json
import logging
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Paths
BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORTS_DIR = BASE_DIR / "data" / "reports"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Heart Disease Data Pipeline API",
    description=(
        "A data engineering REST API that exposes ETL pipeline controls "
        "and analytical endpoints over the Heart Disease dataset."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _load_cleaned() -> pd.DataFrame:
    path = PROCESSED_DIR / "heart_cleaned.csv"
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Cleaned dataset not found. Run /pipeline/run first.",
        )
    return pd.read_csv(path)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def health_check():
    """Basic liveness probe."""
    return {"status": "ok", "service": "heart-disease-pipeline"}


@app.post("/pipeline/run", tags=["Pipeline"])
def run_pipeline():
    """
    Trigger the full ETL pipeline: Extract → Transform → Load.
    Returns paths to generated output files.
    """
    try:
        from etl.pipeline import run_pipeline as _run
        outputs = _run()
        return {"status": "success", "outputs": outputs}
    except Exception as exc:
        logger.exception("Pipeline failed")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/data/summary", tags=["Data"])
def data_summary():
    """Return descriptive statistics of the cleaned dataset."""
    df = _load_cleaned()

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    desc = df[numeric_cols].describe().round(3).to_dict()

    return {
        "rows": len(df),
        "columns": list(df.columns),
        "target_distribution": df["heart_disease"].value_counts().to_dict(),
        "sex_distribution": df["sex"].map({1: "Male", 0: "Female"}).value_counts().to_dict(),
        "age_group_distribution": df["age_group"].value_counts().to_dict(),
        "chest_pain_distribution": df["chest_pain"].value_counts().to_dict(),
        "numeric_stats": desc,
    }


@app.get("/data/records", tags=["Data"])
def get_records(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Records per page"),
    heart_disease: Optional[str] = Query(None, description="Filter by 'Yes' or 'No'"),
    chest_pain: Optional[str] = Query(None, description="Filter by chest pain type"),
):
    """Return paginated records from the cleaned dataset with optional filters."""
    df = _load_cleaned()

    if heart_disease:
        df = df[df["heart_disease"].str.lower() == heart_disease.lower()]
    if chest_pain:
        df = df[df["chest_pain"].str.lower() == chest_pain.lower()]

    total = len(df)
    start = (page - 1) * page_size
    end = start + page_size
    page_df = df.iloc[start:end]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": -(-total // page_size),
        "records": page_df.to_dict(orient="records"),
    }


@app.get("/data/risk-analysis", tags=["Data"])
def risk_analysis():
    """Aggregated risk statistics grouped by age group and chest pain type."""
    df = _load_cleaned()
    df["target"] = (df["heart_disease"] == "Yes").astype(int)

    age_risk = (
        df.groupby("age_group", observed=True)["target"]
        .agg(count="count", disease_count="sum")
        .assign(disease_rate=lambda x: (x["disease_count"] / x["count"]).round(3))
        .reset_index()
        .to_dict(orient="records")
    )

    cp_risk = (
        df.groupby("chest_pain")["target"]
        .agg(count="count", disease_count="sum")
        .assign(disease_rate=lambda x: (x["disease_count"] / x["count"]).round(3))
        .reset_index()
        .to_dict(orient="records")
    )

    sex_risk = (
        df.assign(sex_label=df["sex"].map({1: "Male", 0: "Female"}))
        .groupby("sex_label")["target"]
        .agg(count="count", disease_count="sum")
        .assign(disease_rate=lambda x: (x["disease_count"] / x["count"]).round(3))
        .reset_index()
        .to_dict(orient="records")
    )

    return {
        "by_age_group": age_risk,
        "by_chest_pain": cp_risk,
        "by_sex": sex_risk,
    }


@app.get("/reports", tags=["Reports"])
def list_reports():
    """List all pipeline run reports."""
    REPORTS_DIR.mkdir(exist_ok=True)
    reports = sorted(REPORTS_DIR.glob("pipeline_report_*.json"), reverse=True)
    return {
        "count": len(reports),
        "reports": [r.name for r in reports],
    }


@app.get("/reports/{filename}", tags=["Reports"])
def get_report(filename: str):
    """Retrieve a specific pipeline report by filename."""
    path = REPORTS_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Report '{filename}' not found.")
    with open(path) as fh:
        return json.load(fh)
