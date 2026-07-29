# WaferVision-AI (integrated)

The WaferVision workflow now lives **inside** VERILUMEN at:

`/dashboard/wafer-analysis`

Source: `dashboard/src/wafervision/`

API (same FastAPI as the rest of the platform):

- `POST /api/v1/predict`
- `POST /api/v1/predict/batch`

Requires login (Bearer token). Restart FastAPI after pulling so the new router is loaded.

The standalone `frontend/` app on port 3001 is optional/legacy; use the main dashboard on `:3000`.
