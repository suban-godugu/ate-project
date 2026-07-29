# WaferVision-AI Dashboard

Next.js visualization layer for the WaferVision-AI FastAPI backend.

## Run

```bash
# terminal 1 — API
python -m src.api

# terminal 2 — dashboard
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## API contract

Uses only:

- `POST /predict`
- `POST /predict/batch`

Form fields:

- `grid_mode`: `automatic` | `manual`
- `grid_size`: required for manual (square rows=cols)

No client-side engineering calculations. All metrics/images come from the API JSON.

## Structure

App Router entry: `src/app/`. Dashboard composition: `src/components/pages/`
(avoid `src/pages/` — Next.js treats that as the Pages Router).
Hooks, services, types, and utils live under `src/` as specified.