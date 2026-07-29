# VERILUMEN ΓÇö How Everything Connects

One place that explains how the **dashboard (frontend)**, **platform backend**, **database / cache / storage**, and **AI agents** work together, what each piece is built with, and how to run the stack.

---

## Big picture

```text
 Browser (:3000 only for users)
        Γöé
        Γû╝
 ΓöîΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÉ
 Γöé  Next.js Dashboard  (dashboard/)                             Γöé
 Γöé  ΓÇó Main ATE Intelligence UI                                  Γöé
 Γöé  ΓÇó Proxies agent UIs under /embed/*                          Γöé
 Γöé  ΓÇó Calls platform API at /api/v1 (live mode)                 Γöé
 ΓööΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓö¼ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓö¼ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÿ
                 Γöé HTTP + JWT + SSE             Γöé iframe / rewrite
                 Γû╝                              Γû╝
 ΓöîΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÉ     ΓöîΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÉ
 Γöé  FastAPI Platform API     Γöé     Γöé  Agent services + UIs      Γöé
 Γöé  backend/  (:8000)        Γöé     Γöé  agents/*                  Γöé
 Γöé  + ARQ worker (Redis)     Γöé     Γöé  Pattern / Failure / Scan  Γöé
 ΓööΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓö¼ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÿ     Γöé  Diagnosis / Recs / Opt    Γöé
             Γöé                     ΓööΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÿ
   ΓöîΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓö╝ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÉ
   Γû╝         Γû╝         Γû╝
 Postgres  Redis     MinIO
 :5432     :6379     :9000
 (data)    (jobs/    (files)
           cache)
```

**User rule:** open **http://localhost:3000/dashboard** ΓÇö do not browse raw agent ports. The dashboard rewrites `/embed/...` to each agent UI/API.

---

## Folder map

| Folder | Role | Default ports |
|--------|------|----------------|
| `dashboard/` | Main Next.js UI | `:3000` |
| `backend/` | Platform FastAPI + ARQ worker | `:8000` |
| `agents/pattern-analysis/` | Pattern Analysis agent | `:8011` |
| `agents/failure-analysis/` | Failure Analysis API + UI | `:8021` / `:3020` |
| `agents/scan-diagnosis/` | Scan Diagnosis API + UI | `:8031` / `:3030` |
| `agents/pattern-recommendation/` | Pattern Recommendation | `:8041` / `:3041` |
| `agents/scan-debug-recommendation/` | Scan Debug Recommendation | `:8042` / `:3042` |
| `agents/test-optimization/` | Test Optimization | `:8043` / `:3043` |
| `agents/spatial-ai/` | WaferVision / spatial AI (optional) | own ports |
| `runtime/` | Local input / output / MinIO data / logs | ΓÇö |

---

## How the layers connect

### 1. Frontend ΓåÆ Platform backend

| Mode | Behavior |
|------|----------|
| `NEXT_PUBLIC_API_MODE=mock` | UI uses local mock data in `dashboard/src/lib/*` ΓÇö no backend needed |
| `NEXT_PUBLIC_API_MODE=live` | React Query calls `NEXT_PUBLIC_API_URL` ΓåÆ `http://localhost:8000/api/v1` |

Flow in live mode:

1. Login ΓåÆ JWT from FastAPI  
2. Dashboards / search / notifications ΓåÆ REST  
3. Uploads ΓåÆ presigned URL ΓåÆ **MinIO** PUT ΓåÆ job status over **SSE** (Redis-backed)  
4. Primary AI actions ΓåÆ ARQ worker jobs  

Config: `dashboard/.env.local`

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_API_MODE=live
```

### 2. Platform backend ΓåÆ DB / Redis / MinIO

| Store | Port | Used for |
|-------|------|----------|
| **PostgreSQL** | `5432` | Users, uploads metadata, analytics tables, audit |
| **Redis** | `6379` | Sessions, cache, ARQ job queue, SSE job status |
| **MinIO** | `9000` (console `9001`) | STDF/logs/images/PDFs ΓÇö Postgres keeps only object keys |

Backend env: `backend/.env` (from `.env.example`).

### 3. Platform backend ΓåÆ Agents

Backend can call agents over HTTP using service key + base URLs (see `backend/.env.example`):

- `PATTERN_AGENT_BASE_URL`
- `FAILURE_AGENT_API_URL` / dashboard URL  
- `SCAN_DIAGNOSIS_AGENT_API_URL` / dashboard URL  
- `VERILUMEN_SERVICE_KEY`  
- Shared folders: `UPLOAD_INPUT_ROOT`, `AGENT_OUTPUT_ROOT` ΓåÆ under `runtime/` in this package  

Agents read inputs from `runtime/input/` and write results under `runtime/output/`.

### 4. Frontend ΓåÆ Agents (embeds)

`dashboard/next.config.ts` rewrites same-origin paths so the browser stays on `:3000`:

| Dashboard path | Proxies to |
|----------------|------------|
| `/embed/pattern` | Pattern agent `:8011` |
| `/embed/failure` | Failure UI `:3020` |
| `/embed/scan` | Scan Diagnosis UI `:3030` |
| `/embed/pattern-rec` (+ `/api-proxy`) | Pattern Rec UI `:3041` / API `:8041` |
| `/embed/scan-debug-rec` | Scan Debug Rec UI `:3042` |
| `/embed/test-opt` (+ `/api-proxy`) | Test Opt UI `:3043` / API `:8043` |

Scan Chain / Recommendation pages embed those UIs in iframes (`AgentEmbedFrame`).

---

## What each piece is built with

### Frontend (`dashboard/`)

| Tech | Purpose |
|------|---------|
| **Next.js 16** (App Router) | Framework & routing |
| **React 19** + **TypeScript** | UI |
| **Tailwind CSS v4** + **shadcn/ui** | Styling / components |
| **Zustand** | Client state (filters, uploads, theme) |
| **TanStack React Query** | Live API data |
| **Recharts** | Charts |
| **Framer Motion** | Motion |
| **Lucide** | Icons |

Run alone (mock):

```powershell
cd dashboard
npm install
npm run dev
```

### Platform backend (`backend/`)

| Tech | Purpose |
|------|---------|
| **Python 3.11+** | Runtime |
| **FastAPI** + **Uvicorn** | REST + SSE API |
| **SQLAlchemy (async)** + **asyncpg** | PostgreSQL ORM |
| **Alembic** | Migrations |
| **ARQ** | Background workers (parse, AI actions) |
| **Redis** | Queue + cache |
| **MinIO** (S3-compatible) | Object storage |
| **python-jose / passlib** | JWT + passwords |
| **stdf-tamer** | STDF parsing support |
| **ReportLab** | PDF export |

Run:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # edit DATABASE_URL, secrets
alembic upgrade head
python scripts/seed.py

# Terminal A
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal B
arq app.workers.WorkerSettings
```

Seed login: `alex@verilumen.ai` / `changeme123`

### Database & infra

| Service | Role |
|---------|------|
| **PostgreSQL** | Structured platform data |
| **Redis** | Jobs, cache, SSE |
| **MinIO** | File blobs |

Start Postgres as a Windows service (or local install). Redis/MinIO are started by `start-stack.ps1` if not already listening.

---

## Agents ΓÇö what they do and what they use

Each agent is its own FastAPI (and often its own UI). Together they cover analysis ΓåÆ diagnosis ΓåÆ recommendation ΓåÆ optimization.

```text
 ATE logs / STIL / wafer images
        Γöé
        Γö£ΓöÇΓû║ Pattern Analysis          (patterns, coverage, redundancy)
        Γö£ΓöÇΓû║ Failure Analysis          (failures, rates, fault prediction)
        Γö£ΓöÇΓû║ Scan Diagnosis            (chain breaks, cell localization, ML)
        Γö£ΓöÇΓû║ Pattern Recommendation    (remove / reorder patterns ΓÇö LightGBM)
        Γö£ΓöÇΓû║ Scan Debug Recommendation (debug ranking ΓÇö sklearn + DQN)
        Γö£ΓöÇΓû║ Test Optimization         (adaptive strategy ΓÇö heuristics + LLM)
        ΓööΓöÇΓû║ Spatial AI / WaferVision  (ResNet50 + Grad-CAM) [optional]
```

### Pattern Analysis (`agents/pattern-analysis/`) ΓÇö `:8011`

- **Role:** Pattern KPIs, clustering, similarity, optimization scoring for scan patterns  
- **Stack:** Python, **FastAPI/Uvicorn**, pandas/numpy style analytics, optional GPU/report extras  
- **UI:** Served from the same agent process; embedded at `/embed/pattern`

### Failure Analysis (`agents/failure-analysis/`) ΓÇö API `:8021`, UI `:3020`

- **Role:** Ingest STIL/logs ΓåÆ patterns ΓåÆ rates ΓåÆ classification ΓåÆ die/wafer ΓåÆ fault prediction ΓåÆ reports (FA-FR-001ΓÇª010)  
- **Stack:**
  - **FastAPI**, SQLAlchemy/asyncpg, Alembic, Redis, Celery (optional)
  - **pandas / numpy / scipy / scikit-learn / XGBoost / LightGBM / NetworkX**
  - Optional AI: **OpenAI**, **LangChain**, **FAISS**, **sentence-transformers**
- **UI:** Next.js (`ate-dashboard`) embedded at `/embed/failure`

### Scan Diagnosis (`agents/scan-diagnosis/`) ΓÇö API `:8031`, UI `:3030`

- **Role:** Parse ATE logs + STIL ΓåÆ localize scan cells ΓåÆ break detection ΓåÆ root-cause ML  
- **Stack:**
  - **FastAPI**, pandas, numpy, **scikit-learn** (KNN / K-Means), Parquet cache (**pyarrow**)
  - Multiprocess ingestion (`ProcessPoolExecutor`)
- **UI:** Next.js embedded at `/embed/scan`

### Pattern Recommendation (`agents/pattern-recommendation/`) ΓÇö API `:8041`, UI `:3041`

- **Role:** Redundant pattern detection, removal/ordering recommendations, coverage proxies  
- **Stack:**
  - **FastAPI**, ijson, pandas  
  - **ML:** **LightGBM** (removal classifier + LambdaMART ranker), scikit-learn  
- **UI:** **React + Vite + TypeScript + Tailwind + Zustand + Recharts**  
- Embedded at `/embed/pattern-rec` (API via `/embed/pattern-rec/api-proxy`)

### Scan Debug Recommendation (`agents/scan-debug-recommendation/`) ΓÇö API `:8042`, UI `:3042`

- **Role:** KPI engines + ranked debug recommendations; optional RL self-learning  
- **Stack:**
  - **FastAPI**, scikit-learn, joblib  
  - **PyTorch** + **Gymnasium** (DQN agent)  
- **UI:** Next.js embedded at `/embed/scan-debug-rec`

### Test Optimization (`agents/test-optimization/`) ΓÇö API `:8043`, UI `:3043`

- **Role:** Final decision layer ΓÇö consumes upstream recs + telemetry ΓåÆ Adaptive Test Strategy JSON  
- **Stack:**
  - **FastAPI**, Pydantic  
  - **LangChain** + OpenAI-compatible LLM (with deterministic heuristic fallback)  
- **UI:** Vite/React embedded at `/embed/test-opt`

### Spatial AI / WaferVision (`agents/spatial-ai/`) ΓÇö optional

- **Role:** Wafer defect classification, Grad-CAM explainability, die yield, clusters, zones  
- **Stack:**
  - **PyTorch / torchvision**, **ResNet50**, OpenCV, scikit-learn  
  - **pytorch-grad-cam**, FastAPI, Next.js frontend  

---

## Run commands (full stack)

### Prerequisites (Windows)

1. Python **3.11+**  
2. Node.js **20+** + npm  
3. PostgreSQL on `127.0.0.1:5432`  
4. `redis-server` and `minio` on PATH  
5. Copy `.env.example` ΓåÆ `.env` / `.env.local` and set DB passwords / JWT / MinIO secrets  

### First-time setup

```powershell
# From VERILUMEN-E2E folder

# Backend
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
python scripts/seed.py
cd ..

# Dashboard
cd dashboard
copy .env.example .env.local   # if present; else create .env.local
npm install
cd ..

# Agent UIs (each folder with package.json)
# failure-analysis\ate-dashboard
# scan-diagnosis\frontend
# pattern-recommendation\frontend
# scan-debug-recommendation\frontend
# test-optimization\frontend
# ΓåÆ npm install in each

# Agent Python deps
# pip install -r requirements.txt in each agents\* (venv recommended)
```

### Start everything

```powershell
powershell -ExecutionPolicy Bypass -File .\start-stack.ps1
```

This starts (if not already up):

- Redis `:6379`, MinIO `:9000`  
- Platform API `:8000` + ARQ worker  
- Dashboard `:3000`  
- All agents via `start-agents.ps1`  

Open: **http://localhost:3000/dashboard**  
API docs: **http://127.0.0.1:8000/docs**  
MinIO console: **http://127.0.0.1:9001** (`minioadmin` / as in env)

### Agents only

```powershell
powershell -ExecutionPolicy Bypass -File .\start-agents.ps1
```

### Stop

```powershell
powershell -ExecutionPolicy Bypass -File .\stop-stack.ps1
# or agents only:
powershell -ExecutionPolicy Bypass -File .\stop-agents.ps1
```

### Manual ports cheat sheet

| Process | Port |
|---------|------|
| Dashboard | 3000 |
| Platform API | 8000 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| MinIO | 9000 / 9001 |
| Pattern Analysis | 8011 |
| Failure API / UI | 8021 / 3020 |
| Scan Diagnosis API / UI | 8031 / 3030 |
| Pattern Rec API / UI | 8041 / 3041 |
| Scan Debug Rec API / UI | 8042 / 3042 |
| Test Opt API / UI | 8043 / 3043 |

---

## Request path examples

**Live dashboard KPI (platform):**

```text
Browser ΓåÆ :3000 ΓåÆ Next.js ΓåÆ http://localhost:8000/api/v1/... ΓåÆ Postgres / Redis
```

**Upload file:**

```text
Browser ΓåÆ FastAPI (presign) ΓåÆ MinIO PUT ΓåÆ ARQ worker (parse) ΓåÆ Postgres rows + Redis status ΓåÆ SSE back to UI
```

**Scan Chain ΓåÆ Failure Analysis tab (embed):**

```text
Browser ΓåÆ :3000/embed/failure/... ΓåÆ Next rewrite ΓåÆ Failure UI :3020 ΓåÆ Failure API :8021
```

**Recommendation ΓåÆ Pattern Rec (embed + API proxy):**

```text
Browser ΓåÆ :3000/embed/pattern-rec/ ΓåÆ UI :3041
Browser ΓåÆ :3000/embed/pattern-rec/api-proxy/... ΓåÆ API :8041 (LightGBM services)
```

---

## Runtime data

| Path | Purpose |
|------|---------|
| `runtime/input/` | Sample / uploaded agent inputs |
| `runtime/output/` | Agent outputs / artifacts |
| `runtime/minio-data/` | Local MinIO bucket storage |
| `runtime/logs/` | Agent/stack logs |

Large sample datasets are not shipped in the share zip ΓÇö add files under `runtime/input/` after unzip.

---

## Security notes (local / demo)

Change before any shared environment:

- `JWT_SECRET`, DB password  
- MinIO root password  
- `VERILUMEN_SERVICE_KEY` (`dev-service-key-change-me`)  

---

## More detail

| Doc | Focus |
|-----|--------|
| `dashboard/README.md` | UI pages, mock vs live, prompt history |
| `backend/README.md` | API schema, workers, data placement |
| `backend/NATIVE_WINDOWS_SETUP.md` | Postgres / Redis / MinIO on Windows |
| `agents/*/README.md` | Per-agent architecture and FR coverage |

Share-package short guide (setup only): [`README-SHARE.md`](./README-SHARE.md)
