"""
SQLAlchemy ORM models — maps Python classes to database tables.
"""
from sqlalchemy import Column, Integer, Float, String
from api.database import Base


class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(Integer, primary_key=True, index=True)

    # Raw clinical features
    Age = Column(Integer, nullable=False)
    Sex = Column(Integer, nullable=False)           # 1=male, 0=female
    ChestPain = Column(String, nullable=False)
    RestBP = Column(Integer, nullable=False)
    Chol = Column(Integer, nullable=False)
    Fbs = Column(Integer, nullable=False)
    RestECG = Column(Integer, nullable=False)
    MaxHR = Column(Integer, nullable=False)
    ExAng = Column(Integer, nullable=False)
    Oldpeak = Column(Float, nullable=False)
    Slope = Column(Integer, nullable=False)
    Ca = Column(Integer, nullable=False)
    Thal = Column(String, nullable=False)
    AHD = Column(Integer, nullable=False)           # 1=Yes, 0=No

    # Encoded features
    ChestPain_Enc = Column(Integer)
    Thal_Enc = Column(Integer)

    # Engineered features
    AgeGroup = Column(String)
    HighChol = Column(Integer)
    HighBP = Column(Integer)
    HeartRateReserve = Column(Float)
    RiskScore = Column(Float)


class PatientStats(Base):
    __tablename__ = "patient_stats"

    AgeGroup = Column(String, primary_key=True)
    total = Column(Integer)
    ahd_positive = Column(Integer)
    avg_chol = Column(Float)
    avg_restbp = Column(Float)
    avg_maxhr = Column(Float)
    avg_risk_score = Column(Float)
    ahd_rate = Column(Float)
