# Scan Debug Recommendation Agent v1.1

AI-assisted scan debug recommendations: live KPI engines, supervised ML ranking, and RL training for future self-learning.

Owner: mohith@verilumen.ai (mohith1805)

## Requirements

- Python 3.11+
- Node.js 20+ (frontend)
- Scan dataset in `scan debug data/` (included)

## Quick start (local)

### 1. Backend API

```bash
cp .env.example .env
pip install -r requirements.txt

# Windows PowerShell
$env:PYTHONPATH="."
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8005
```

API: `http://127.0.0.1:8005` · Health: `http://127.0.0.1:8005/health`

### 2. Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

UI: `http://localhost:3001/dashboard/recommendation-analysis`

Set `API_KEY` in both `.env` and `frontend/.env.local` if `REQUIRE_API_KEY=true`.

## Docker

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
# Edit API_KEY in both files

docker compose up --build
```

See [PRODUCTION.md](PRODUCTION.md) for deployment hardening.

## Project layout

| Path | Purpose |
|------|---------|
| `src/api/` | FastAPI app, dashboard, health, middleware |
| `src/data/` | KPI engines, recommendation builders, dataset |
| `src/models/` | ML recommender, KPI ML, DQN agent |
| `scan debug data/` | STIL, diagnosis HTML, failure logs, compiled dataset |
| `frontend/` | Next.js dashboard |
| `tests/` | Pytest suite |

## Key environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RECOMMENDATION_SOURCE` | `ml` | Top recs: `ml`, `kpi`, or `hybrid` |
| `KPI_ML_ENABLED` | `true` | Blend ML into KPI confidence/ranking |
| `ML_AUTO_TRAIN` | `true` | Retrain sklearn recommender on startup |
| `AUTO_TRAIN_ON_STARTUP` | `true` | Background DQN training (set `false` for dev) |

## Tests

```bash
$env:PYTHONPATH="."
pytest tests/ -q
```
