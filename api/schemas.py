"""
Pydantic schemas — used for FastAPI request/response validation and serialisation.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class PatientBase(BaseModel):
    Age: int = Field(..., ge=18, le=100, description="Patient age in years")
    Sex: int = Field(..., ge=0, le=1, description="1=male, 0=female")
    ChestPain: str
    RestBP: int = Field(..., ge=50, le=250)
    Chol: int = Field(..., ge=100, le=600)
    Fbs: int = Field(..., ge=0, le=1)
    RestECG: int = Field(..., ge=0, le=2)
    MaxHR: int = Field(..., ge=50, le=250)
    ExAng: int = Field(..., ge=0, le=1)
    Oldpeak: float
    Slope: int
    Ca: int = Field(..., ge=0, le=3)
    Thal: str
    AHD: int = Field(..., ge=0, le=1, description="1=heart disease, 0=none")


class PatientResponse(PatientBase):
    patient_id: int
    ChestPain_Enc: Optional[int] = None
    Thal_Enc: Optional[int] = None
    AgeGroup: Optional[str] = None
    HighChol: Optional[int] = None
    HighBP: Optional[int] = None
    HeartRateReserve: Optional[float] = None
    RiskScore: Optional[float] = None

    model_config = {"from_attributes": True}


class PaginatedPatients(BaseModel):
    total: int
    page: int
    page_size: int
    data: List[PatientResponse]


class SummaryStats(BaseModel):
    total_patients: int
    ahd_positive: int
    ahd_rate_pct: float
    avg_age: float
    avg_chol: float
    avg_restbp: float
    avg_maxhr: float
    avg_risk_score: float
    pct_male: float


class ChestPainStats(BaseModel):
    ChestPain: str
    total: int
    ahd_positive: int
    ahd_rate_pct: float


class AgeGroupStats(BaseModel):
    AgeGroup: str
    total: int
    ahd_positive: int
    ahd_rate_pct: float
    avg_risk_score: float


class RiskFactorStats(BaseModel):
    factor: str
    correlation_with_ahd: float
