# Pattern Recommendation Agent v1.1
A production-style pattern analysis platform for semiconductor test optimization.
It includes:
- **FastAPI backend** for recommendation services
- **React + Vite dashboard** for KPI cards, failure views, and recommendation tables
- **Failure aggregation agent** for parsing ATE logs and generating summaries
- **Supervised ML layer (v1.1)** for removal and ordering scoring (with safe shadow rollout)
---
## Features
### Core recommendation services
- Redundant pattern detection
- Pattern removal recommendations
- Pattern ordering for early failure detection
- Gap analysis request generation
- Low-power proxy pattern set
- Coverage proxy recommendations
- Unified orchestrator payload for dashboards
### Failure analytics
- Aggregate failed logs by pattern
- Coverage % and severity tagging
- Dashboard-ready rows and summaries
### ML v1.1 (supervised)
- LightGBM **removal classifier**
- LightGBM LambdaMART **ordering ranker**
- Shadow mode + blended rollout support
- Operator feedback capture via API
---
## Project structure
agents/      # Offline agents (e.g., failure aggregation)
backend/     # FastAPI app, schemas, services, routes
dashboard/   # Legacy Streamlit dashboard (optional)
frontend/    # React + TypeScript + Vite dashboard
ml/          # ML data builders, labels, training, artifacts
data/        # Input datasets (ignored in git)
outputs/     # Generated outputs/artifacts (ignored in git)
Tech stack
Backend
FastAPI
Pydantic Settings
Uvicorn
ijson (streaming large JSON)
Frontend
React
Vite
TypeScript
Tailwind CSS
Axios
Recharts
Zustand
React Router
ML
LightGBM
scikit-learn
pandas
numpy
Prerequisites
Python 3.11+ (3.13 works)
Node.js 20+
npm
Installation
1) Backend dependencies
pip install -r requirements.txt
2) Frontend dependencies
cd frontend
npm install
Run the application
Start FastAPI backend
python -m backend.app
Backend default URL:

http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/docs
Start React dashboard
cd frontend
npm run dev
Frontend default URL:

http://localhost:5173
Vite is configured to proxy API calls to http://127.0.0.1:8000.

Key API endpoints
System
GET /health
GET /version
GET /
Datasets
GET /datasets
GET /datasets/status
GET /datasets/summary
POST /datasets/refresh
Pattern services
GET /patterns/statistics
GET /redundancy/statistics
GET /recommendations/removal
GET /recommendations/ordering
GET /recommendations/gap-analysis
GET /recommendations/low-power
GET /recommendations/coverage
Unified dashboard payload
GET /recommendations/dashboard
GET /recommendations/summary
POST /recommendations/refresh
Failure aggregation API
GET /failures/summary
GET /failures/dashboard-rows
POST /failures/refresh
ML API
GET /ml/status
POST /ml/feedback
GET /ml/feedback/recent
ML workflow (v1.1)
From project root:

python -m ml.scripts.build_dataset
python -m ml.scripts.train_removal
python -m ml.scripts.train_ordering
python -m ml.scripts.evaluate
Artifacts are written to:

ml/artifacts/
Generated ML datasets are written to:

ml/data/
ML rollout modes
Runtime flags (env variables via BACKEND_ prefix):

BACKEND_ML_ENABLED (default: false)
BACKEND_ML_SHADOW_MODE (default: true)
BACKEND_ML_REMOVAL_BLEND (default: 0.7)
BACKEND_ML_ORDERING_BLEND (default: 0.7)
Behavior
ml_enabled=false, ml_shadow_mode=true
Models load and shadow-log only; heuristics remain final.

ml_enabled=true, ml_shadow_mode=false
ML scores are blended into removal/ordering outputs.

Safety rule
Removal with unique_fail_contribution > 0 is forced toward keep.

Failure aggregation agent (offline)
Run the agent to generate failure summaries:

python -m agents.failure_aggregation_agent
It produces outputs under outputs/, including:

failure_summary.json
failure_summary.csv
dashboard_data.json
failure_report.md
Git policy (source-only)
This repo is configured to avoid committing input/output artifacts.

Ignored by root .gitignore:

data/
outputs/
ml/data/
ml/artifacts/
caches, logs, env/local runtime files
This keeps Git focused on source code and configs only.

Frontend build
cd frontend
npm run build
