"""
dashboard/app.py — Streamlit analytics dashboard for the Heart Disease pipeline.

Run:
    streamlit run dashboard/app.py
"""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[1]
CLEANED_CSV = BASE_DIR / "data" / "processed" / "heart_cleaned.csv"
REPORTS_DIR = BASE_DIR / "data" / "reports"

st.set_page_config(
    page_title="Heart Disease Pipeline Dashboard",
    page_icon="🫀",
    layout="wide",
)

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🫀 Heart Disease — Data Engineering Dashboard")
st.caption("ETL pipeline analytics & exploratory data insights")
st.divider()


# ── Load data ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    if not CLEANED_CSV.exists():
        return None
    return pd.read_csv(CLEANED_CSV)


df = load_data()

if df is None:
    st.warning("⚠️  Processed dataset not found. Trigger the pipeline first.")
    if st.button("▶ Run ETL Pipeline Now"):
        with st.spinner("Running pipeline…"):
            import sys
            sys.path.insert(0, str(BASE_DIR))
            from etl.pipeline import run_pipeline
            outputs = run_pipeline()
            st.success("Pipeline complete!")
            st.json(outputs)
            st.rerun()
    st.stop()

df["target"] = (df["heart_disease"] == "Yes").astype(int)

# ── KPI Row ────────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Patients", len(df))
col2.metric("With Heart Disease", int(df["target"].sum()))
col3.metric("Disease Rate", f"{df['target'].mean():.1%}")
col4.metric("Mean Age", f"{df['age'].mean():.1f} yrs")

st.divider()

# ── Charts Row 1 ───────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.subheader("Disease Distribution")
    vc = df["heart_disease"].value_counts().reset_index()
    vc.columns = ["Outcome", "Count"]
    fig = px.pie(vc, names="Outcome", values="Count",
                 color_discrete_sequence=["#ef4444", "#22c55e"],
                 hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Age Distribution by Outcome")
    fig = px.histogram(df, x="age", color="heart_disease",
                       barmode="overlay", nbins=20,
                       color_discrete_map={"Yes": "#ef4444", "No": "#22c55e"},
                       labels={"age": "Age", "heart_disease": "Heart Disease"})
    st.plotly_chart(fig, use_container_width=True)

# ── Charts Row 2 ───────────────────────────────────────────────────────────────
c3, c4 = st.columns(2)

with c3:
    st.subheader("Disease Rate by Chest Pain Type")
    cp = (df.groupby("chest_pain")["target"]
            .agg(["mean", "count"])
            .reset_index()
            .rename(columns={"mean": "rate", "count": "patients", "chest_pain": "Chest Pain"}))
    fig = px.bar(cp, x="Chest Pain", y="rate",
                 color="rate",
                 color_continuous_scale="Reds",
                 labels={"rate": "Disease Rate"})
    fig.update_layout(yaxis_tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)

with c4:
    st.subheader("Cholesterol vs. Max Heart Rate")
    fig = px.scatter(df, x="cholesterol", y="max_hr",
                     color="heart_disease",
                     color_discrete_map={"Yes": "#ef4444", "No": "#22c55e"},
                     opacity=0.7,
                     labels={"cholesterol": "Cholesterol (mg/dL)",
                             "max_hr": "Max Heart Rate",
                             "heart_disease": "Heart Disease"})
    st.plotly_chart(fig, use_container_width=True)

# ── Charts Row 3 ───────────────────────────────────────────────────────────────
c5, c6 = st.columns(2)

with c5:
    st.subheader("Disease Rate by Age Group")
    ag = (df.groupby("age_group", observed=True)["target"]
            .agg(["mean", "count"])
            .reset_index()
            .rename(columns={"mean": "rate", "count": "patients", "age_group": "Age Group"}))
    fig = px.bar(ag, x="Age Group", y="rate",
                 color="rate",
                 color_continuous_scale="Oranges",
                 labels={"rate": "Disease Rate"})
    fig.update_layout(yaxis_tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)

with c6:
    st.subheader("Thal Type Distribution")
    fig = px.histogram(df, x="thal", color="heart_disease",
                       barmode="group",
                       color_discrete_map={"Yes": "#ef4444", "No": "#22c55e"},
                       labels={"thal": "Thal Type", "heart_disease": "Heart Disease"})
    st.plotly_chart(fig, use_container_width=True)

# ── Data Table ─────────────────────────────────────────────────────────────────
st.divider()
st.subheader("📋 Cleaned Dataset Preview")
st.dataframe(df.head(50), use_container_width=True)

# ── Pipeline Reports ───────────────────────────────────────────────────────────
st.divider()
st.subheader("📊 Pipeline Run Reports")
reports = sorted(REPORTS_DIR.glob("pipeline_report_*.json"), reverse=True) if REPORTS_DIR.exists() else []

if reports:
    selected = st.selectbox("Select report", [r.name for r in reports])
    with open(REPORTS_DIR / selected) as fh:
        report_data = json.load(fh)
    st.json(report_data)
else:
    st.info("No reports yet — run the pipeline to generate one.")
