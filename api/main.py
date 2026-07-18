"""
FastAPI application — serves heart disease data via REST endpoints.
"""
import os
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from api.database import get_db, engine, Base
from api import models, schemas

# ──────────────────────────────────────────────
# App initialisation
# ──────────────────────────────────────────────
app = FastAPI(
    title="Heart Disease Data API",
    description=(
        "REST API serving the Heart Disease dataset with cleaned features, "
        "engineered risk scores, and aggregate statistics."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# Startup
# ──────────────────────────────────────────────
@app.on_event("startup")
def startup_event():
    """Ensure tables exist on startup (safe if ETL already ran)."""
    Base.metadata.create_all(bind=engine)


# ──────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Heart Disease Pipeline API is running 🫀"}


# ──────────────────────────────────────────────
# Patients
# ──────────────────────────────────────────────
@app.get(
    "/api/v1/patients",
    response_model=schemas.PaginatedPatients,
    tags=["Patients"],
    summary="List all patients (paginated)",
)
def list_patients(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Records per page"),
    ahd: Optional[int] = Query(None, ge=0, le=1, description="Filter by AHD (0 or 1)"),
    sex: Optional[int] = Query(None, ge=0, le=1, description="Filter by Sex (0 or 1)"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Patient)

    if ahd is not None:
        query = query.filter(models.Patient.AHD == ahd)
    if sex is not None:
        query = query.filter(models.Patient.Sex == sex)

    total = query.count()
    patients = query.offset((page - 1) * page_size).limit(page_size).all()

    return schemas.PaginatedPatients(
        total=total,
        page=page,
        page_size=page_size,
        data=patients,
    )


@app.get(
    "/api/v1/patients/{patient_id}",
    response_model=schemas.PatientResponse,
    tags=["Patients"],
    summary="Get a single patient by ID",
)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    return patient


# ──────────────────────────────────────────────
# Statistics
# ──────────────────────────────────────────────
@app.get(
    "/api/v1/stats/summary",
    response_model=schemas.SummaryStats,
    tags=["Statistics"],
    summary="Overall dataset summary",
)
def get_summary(db: Session = Depends(get_db)):
    total = db.query(func.count(models.Patient.patient_id)).scalar()
    if total == 0:
        raise HTTPException(status_code=503, detail="Database is empty — run the ETL pipeline first.")

    ahd_pos = db.query(func.sum(models.Patient.AHD)).scalar() or 0
    avg_age = db.query(func.avg(models.Patient.Age)).scalar()
    avg_chol = db.query(func.avg(models.Patient.Chol)).scalar()
    avg_restbp = db.query(func.avg(models.Patient.RestBP)).scalar()
    avg_maxhr = db.query(func.avg(models.Patient.MaxHR)).scalar()
    avg_risk = db.query(func.avg(models.Patient.RiskScore)).scalar()
    male_count = db.query(func.count(models.Patient.patient_id)).filter(models.Patient.Sex == 1).scalar()

    return schemas.SummaryStats(
        total_patients=total,
        ahd_positive=int(ahd_pos),
        ahd_rate_pct=round(ahd_pos / total * 100, 2),
        avg_age=round(avg_age, 1),
        avg_chol=round(avg_chol, 1),
        avg_restbp=round(avg_restbp, 1),
        avg_maxhr=round(avg_maxhr, 1),
        avg_risk_score=round(avg_risk, 2),
        pct_male=round(male_count / total * 100, 1),
    )


@app.get(
    "/api/v1/stats/by-chest-pain",
    response_model=List[schemas.ChestPainStats],
    tags=["Statistics"],
    summary="AHD rate by chest pain type",
)
def stats_by_chest_pain(db: Session = Depends(get_db)):
    rows = (
        db.query(
            models.Patient.ChestPain,
            func.count(models.Patient.patient_id).label("total"),
            func.sum(models.Patient.AHD).label("ahd_positive"),
        )
        .group_by(models.Patient.ChestPain)
        .all()
    )
    return [
        schemas.ChestPainStats(
            ChestPain=r.ChestPain,
            total=r.total,
            ahd_positive=int(r.ahd_positive),
            ahd_rate_pct=round(r.ahd_positive / r.total * 100, 2),
        )
        for r in rows
    ]


@app.get(
    "/api/v1/stats/by-age-group",
    response_model=List[schemas.AgeGroupStats],
    tags=["Statistics"],
    summary="AHD rate and risk score by age group",
)
def stats_by_age_group(db: Session = Depends(get_db)):
    rows = (
        db.query(
            models.Patient.AgeGroup,
            func.count(models.Patient.patient_id).label("total"),
            func.sum(models.Patient.AHD).label("ahd_positive"),
            func.avg(models.Patient.RiskScore).label("avg_risk_score"),
        )
        .group_by(models.Patient.AgeGroup)
        .all()
    )
    return [
        schemas.AgeGroupStats(
            AgeGroup=r.AgeGroup,
            total=r.total,
            ahd_positive=int(r.ahd_positive or 0),
            ahd_rate_pct=round((r.ahd_positive or 0) / r.total * 100, 2),
            avg_risk_score=round(r.avg_risk_score or 0, 2),
        )
        for r in rows
    ]


@app.get(
    "/api/v1/stats/risk-factors",
    response_model=List[schemas.RiskFactorStats],
    tags=["Statistics"],
    summary="Correlation of numeric features with AHD",
)
def risk_factors(db: Session = Depends(get_db)):
    """
    Returns Pearson correlation of each numeric feature with the AHD target.
    Computed in-memory from the full table (303 rows, very fast).
    """
    import pandas as pd

    patients = db.query(models.Patient).all()
    if not patients:
        return []

    records = [
        {
            "Age": p.Age, "RestBP": p.RestBP, "Chol": p.Chol,
            "MaxHR": p.MaxHR, "Oldpeak": p.Oldpeak, "Ca": p.Ca,
            "ExAng": p.ExAng, "RiskScore": p.RiskScore,
            "HeartRateReserve": p.HeartRateReserve, "AHD": p.AHD,
        }
        for p in patients
    ]
    df = pd.DataFrame(records)
    corr = df.corr(numeric_only=True)["AHD"].drop("AHD").sort_values(ascending=False)

    return [
        schemas.RiskFactorStats(factor=col, correlation_with_ahd=round(val, 4))
        for col, val in corr.items()
    ]
