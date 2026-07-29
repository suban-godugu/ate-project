# Test Optimization Recommendation Agent v1.1

Owner: akhila@verilumen.ai (akhila-vai)

Final enterprise decision layer for semiconductor ATE Scan Test platforms.

This agent does **not** perform pattern analysis, ATPG, scan debug, or failure diagnosis.
It consumes upstream Pattern Recommendation + Scan Debug outputs plus production telemetry
and returns an Adaptive Test Strategy as structured JSON.

## Stack

- Python 3.11+
- FastAPI (async)
- Pydantic / pydantic-settings
- LangChain OpenAI-compatible LLM
- Deterministic heuristic fallback (no invented metrics)

## Layout

```
backend/
  app/
    api/             Routes
    core/            Config, logging, DI
    domain/          Models & schemas
    infrastructure/  LLM client, repositories
    prompts/         System prompts
    services/        Optimization + heuristic engines
  tests/
  requirements.txt
samples/
```

## Run

```bash
cd backend
python -m pip install -r requirements.txt
copy .env.example .env   # optional: set OPENAI_API_KEY
python -m uvicorn app.main:app --reload --port 8000
```

- API docs: http://127.0.0.1:8000/docs
- Health: `GET /api/v1/health`
- Sample: `POST /api/v1/optimize/sample/low_risk`

```bash
cd backend
python run_samples.py
python -m pytest -q
```

## Output

JSON with `summary`, `recommended_strategy`, `risk_level`, `confidence`,
adaptive/test-stop/risk blocks, yield/cost/coverage/production recommendations,
time/cost/yield impact, `business_impact`, and `assumptions`.
