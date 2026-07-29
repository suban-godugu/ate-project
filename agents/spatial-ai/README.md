# WaferVision-AI

Enterprise semiconductor wafer defect analytics platform — ResNet50 classification,
Grad-CAM explainability, die-level yield, overlay / density visualization, spatial
cluster detection, engineering zone analysis, batch LOT workflows, FastAPI backend,
and a Next.js production dashboard.

**Version:** `v1.0.0`

---

## Project overview

WaferVision-AI turns wafer map images into engineering-ready analytics:

| Capability | Module |
|---|---|
| Defect classification (ResNet50) | `src/predict.py`, `src/model.py` |
| Explainable AI | `src/gradcam.py` |
| Die extraction + yield | `src/dice_analysis.py` |
| Overlay / density | pipeline helpers + visualization modules |
| Spatial clusters | `src/cluster_analysis.py` |
| Engineering zones | `src/zone_analysis.py` |
| Orchestration | `src/wafer_pipeline.py` |
| REST API | `src/api.py` |
| Dashboard | `frontend/` |

---

## Architecture

```
Next.js Dashboard (visualization only)
        ↓  POST /predict | POST /predict/batch
FastAPI (validation + ops endpoints)
        ↓
run_wafer_analysis()
        ↓
Predict → Grad-CAM → Die/Yield → Overlay → Density → Clusters → Zones
        ↓
JSON (unchanged fields + optional spatial_analysis)
```

No module bypasses this order. The backend is the single source of truth.

---

## Folder structure

```
├── src/                     Backend package
│   ├── api.py               FastAPI routes
│   ├── config.py            Env-driven configuration
│   ├── logging_config.py    Rotating logs
│   ├── health.py            Health / metrics helpers
│   ├── errors.py            Structured API errors
│   ├── wafer_pipeline.py    Master orchestrator
│   ├── predict.py / model.py / preprocess.py / …
│   ├── cluster_analysis.py / zone_analysis.py
│   └── …
├── frontend/                Next.js dashboard
├── tests/                   pytest suite
├── scripts/                 Ops utilities (profiling)
├── models/                  resnet50_layer4_ft.pth (default)
├── logs/                    application.log / error.log / batch.log
├── docs/                    Architecture notes
├── Dockerfile / docker-compose.yml
├── .github/workflows/ci.yml
├── requirements.txt
├── pyproject.toml
└── .env.example
```

---

## Installation

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # or cp .env.example .env

cd frontend
npm install
```

Place trained weights at `models/resnet50_layer4_ft.pth` (or set `WAFERVISION_MODEL_PATH`).

---

## Dataset structure

Use **only** the bundled dataset:

```
wafer dataset/data/
  train/{Center,Donut,...,Scratch}/
  valid/...
  test/...
```

Do not download or replace this dataset.

---

## Training / evaluation / prediction

```bash
# Train (writes config.MODEL_PATH — default models/resnet50_layer4_ft.pth)
python -m src.train

# Evaluate
python -m src.evaluate

# Single prediction helper
python -m src.predict path/to/wafer.jpg

# Full pipeline (includes spatial_analysis)
python -m src.wafer_pipeline path/to/wafer.jpg
```

---

## FastAPI

```bash
python -m src.api
# → http://127.0.0.1:8000/docs
```

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Root liveness |
| GET | `/health` | Model loaded + readiness |
| GET | `/version` | Semantic version |
| GET | `/metrics` | Process metrics |
| POST | `/predict` | Single wafer analysis |
| POST | `/analyze` | Alias of `/predict` |
| POST | `/predict/batch` | Batch analysis |

### Example — single wafer

```bash
curl -X POST http://127.0.0.1:8000/predict ^
  -F "image=@wafer.jpg" ^
  -F "grid_mode=automatic"
```

Manual grid:

```bash
curl -X POST http://127.0.0.1:8000/predict ^
  -F "image=@wafer.jpg" ^
  -F "grid_mode=manual" ^
  -F "grid_size=52"
```

Error shape (ops):

```json
{ "status": "error", "message": "…", "code": 415, "detail": "…" }
```

Analysis success responses remain the **exact** pipeline JSON (no envelope).

---

## Dashboard

```bash
cd frontend
npm run dev
# → http://localhost:3000
```

Tabs: Overview · Wafer Analysis · Batch Analysis · Reports · Spatial Analytics · Engineering Zones.

Exports: CSV / JSON (PDF placeholder). Session **Clear All** resets cached results.

---

## Configuration

All runtime knobs live in `src/config.py` and are overridable via `.env`
(see `.env.example`): host, port, workers, model path, upload limits, CORS,
log directories, timeouts, version strings.

---

## Logging

`src/logging_config.py` writes rotating files under `logs/`:

- `application.log`
- `error.log`
- `batch.log`

Never logs base64 images or large JSON payloads.

---

## Testing & quality

```bash
pytest
black src tests scripts
isort src tests scripts
flake8 src tests scripts
mypy src
```

---

## Docker / deployment

```bash
# Requires models/resnet50_layer4_ft.pth on the host (mounted read-only)
docker compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

---

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`) installs dependencies, lints Python,
runs unit/contract tests, builds the frontend, and builds the backend image.

---

## Profiling

```bash
python -m scripts.profile_pipeline
```

Reports wall-clock timing for ops awareness. Does **not** change prediction math.

---

## Troubleshooting

| Symptom | Check |
|---|---|
| API offline | `python -m src.api`, confirm port / CORS |
| Model not loaded | `models/resnet50_layer4_ft.pth` exists (or `WAFERVISION_MODEL_PATH`); see `GET /health` |
| 415 on upload | Only jpg/jpeg/png/bmp; no exe/archives |
| Batch too large | `WAFERVISION_MAX_BATCH_FILES` |
| Frontend empty | Analyze wafers first; check `NEXT_PUBLIC_API_BASE_URL` |

---

## Future work

- Stronger per-die CNN classifiers (replace heuristic GOOD/FAIL)
- Auth / RBAC / multi-tenant lots
- PDF report generation
- Kubernetes manifests & horizontal scaling
- Real-time streaming analysis

---

## Production checklist

- [x] Backend starts (`python -m src.api`)
- [x] Frontend builds (`cd frontend && npm run build`)
- [x] Model singleton load
- [x] `/predict` + `/predict/batch`
- [x] Spatial clusters + zones in JSON
- [x] Logging + health/version/metrics
- [x] Tests + lint tooling
- [x] Docker + Compose + CI
- [x] Enterprise README

This project preserves complete AI backward compatibility — Prompt 15 hardens
operations only.
