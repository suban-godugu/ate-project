# Backend — Test Optimization Recommendation Agent

Clean-architecture FastAPI service.

## Run

```bash
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

## Key endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health + LLM status |
| POST | `/api/v1/optimize` | Optimize from context |
| POST | `/api/v1/optimize/sample/{name}` | `low_risk` \| `high_risk` |
| POST | `/api/v1/upload` | Upload OptimizationContext JSON |
| GET | `/api/v1/recommendations` | History list |
| GET | `/api/v1/recommendations/{id}` | Details |
| POST | `/api/v1/recommendations/compare` | Compare IDs |
| GET | `/api/v1/analytics/summary` | Analytics |

## LLM

Set `OPENAI_API_KEY` (and optional `OPENAI_BASE_URL`) for LangChain OpenAI-compatible mode.
Without a key, the deterministic heuristic engine is used.
