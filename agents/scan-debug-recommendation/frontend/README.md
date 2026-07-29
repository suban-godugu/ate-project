# COMPTY Scan Debug Recommendation Agent — Frontend

Enterprise AI Decision Workspace for semiconductor Test Engineers.

## Setup

```bash
cd frontend
cp .env.example .env.local
# edit hosts/ports/API URL as needed
npm install
npm run dev
```

`PORT`, `NEXT_PUBLIC_API_BASE_URL`, and `API_PROXY_TARGET` come from `.env.local` — nothing is hard-coded in `next.config` or the API client.

## Modes

- `NEXT_PUBLIC_API_MODE=live` — FastAPI via same-origin `/scan-debug-api` proxy (or `NEXT_PUBLIC_API_BASE_URL` server-side)
- `NEXT_PUBLIC_API_MODE=mock` — local mock dashboard data for UI-only work

Backend env lives in the project-root `.env` (see `.env.example`).
