# 🫀 Heart Disease Data Engineering Pipeline

A production-grade data engineering project built on the [Heart Disease dataset](https://www.kaggle.com/datasets/cherngs/heart-disease-cleveland-uci).  
It features a full **Extract → Transform → Load (ETL)** pipeline, a **REST API** for data access, and an interactive **analytics dashboard** — all deployable to [Render](https://render.com) in one click.

---

## 📐 Architecture

```
heart-pipeline/
├── data/
│   ├── raw/                  # Source CSV (tracked in git)
│   ├── processed/            # ETL outputs: CSV + Parquet (generated)
│   └── reports/              # JSON run reports (generated)
├── etl/
│   ├── extract.py            # Stage 1: load & validate raw CSV
│   ├── transform.py          # Stage 2: clean, engineer features, encode
│   ├── load.py               # Stage 3: persist outputs & write report
│   └── pipeline.py           # Orchestrator: runs E→T→L end-to-end
├── api/
│   └── app.py                # FastAPI REST API (6 endpoints)
├── dashboard/
│   └── app.py                # Streamlit analytics dashboard
├── tests/
│   └── test_etl.py           # Pytest unit tests (14 tests)
├── scripts/
│   └── run_pipeline.sh       # Convenience shell runner
├── Procfile                  # Render / Heroku process file
├── render.yaml               # Render multi-service deployment config
└── requirements.txt
```

---

## 🚀 Quickstart (Local)

### 1. Clone & install

```bash
git clone https://github.com/<your-username>/heart-pipeline.git
cd heart-pipeline
pip install -r requirements.txt
```

### 2. Run the ETL pipeline

```bash
python -m etl.pipeline
# or
bash scripts/run_pipeline.sh
```

Outputs written to `data/processed/` and `data/reports/`.

### 3. Start the API

```bash
uvicorn api.app:app --reload
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

### 4. Start the Dashboard

```bash
streamlit run dashboard/app.py
```

Open **http://localhost:8501**

### 5. Run tests

```bash
pytest tests/ -v --cov=etl
```

---

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/pipeline/run` | Trigger full ETL pipeline |
| `GET` | `/data/summary` | Descriptive statistics |
| `GET` | `/data/records` | Paginated records (filterable) |
| `GET` | `/data/risk-analysis` | Disease rate by age group, chest pain, sex |
| `GET` | `/reports` | List all pipeline run reports |
| `GET` | `/reports/{filename}` | Retrieve a specific report |

---

## ☁️ Deploy to Render

### Option A — One-click via `render.yaml` (recommended)

1. Fork this repo on GitHub.
2. Go to [Render Dashboard](https://dashboard.render.com) → **New → Blueprint**.
3. Connect your GitHub repo — Render auto-reads `render.yaml`.
4. Click **Apply** — both the API and Dashboard services are deployed automatically.

### Option B — Manual service setup

#### Deploy the API

1. **New Web Service** → connect your repo.
2. **Build Command:** `pip install -r requirements.txt && python -m etl.pipeline`
3. **Start Command:** `uvicorn api.app:app --host 0.0.0.0 --port $PORT`
4. **Environment:** Python 3.11

#### Deploy the Dashboard

1. **New Web Service** → connect your repo.
2. **Build Command:** `pip install -r requirements.txt && python -m etl.pipeline`
3. **Start Command:** `streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
4. **Environment:** Python 3.11

---

## 🔬 Dataset

| Column | Description |
|--------|-------------|
| `age` | Patient age in years |
| `sex` | 1 = male, 0 = female |
| `chest_pain` | Type: typical, atypical, nonanginal, asymptomatic |
| `rest_bp` | Resting blood pressure (mm Hg) |
| `cholesterol` | Serum cholesterol (mg/dL) |
| `fasting_blood_sugar` | FBS > 120 mg/dL → 1, else 0 |
| `rest_ecg` | Resting ECG results |
| `max_hr` | Maximum heart rate achieved |
| `exercise_angina` | Exercise-induced angina (1 = yes) |
| `st_depression` | ST depression induced by exercise |
| `slope` | Slope of peak exercise ST segment |
| `ca_vessels` | Number of major vessels colored by fluoroscopy |
| `thal` | Thalassemia type |
| `heart_disease` | Diagnosis: **Yes / No** (target) |

**Engineered features:** `age_group`, `chol_risk`, `hr_reserve`, `target`

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| ETL | Python · Pandas · NumPy · PyArrow |
| API | FastAPI · Uvicorn |
| Dashboard | Streamlit · Plotly |
| Testing | Pytest · pytest-cov |
| Deployment | Render (render.yaml) |

---

## 📄 License

MIT
