# ATE Dashboard

Next.js 16 production UI for the Failure Analysis Agent (FA-FR-001→010).

## Docs

- [User Guide](../docs/10_USER_GUIDE.md)
- [API Specification](../docs/04_API_SPECIFICATION.md)
- [Deployment Guide](../docs/09_DEPLOYMENT_GUIDE.md)

## Run

From the **repo root** (starts API if needed, then this app):

```powershell
.\start-dashboard.ps1
# optional: free a stale :3000 listener first
.\start-dashboard.ps1 -ClearPort
```

Or from this directory (API must already be on :8000):

```powershell
npm install
npm run dev
# after a bad Turbopack cache / root inference:
npm run dev:clean
```

Open http://127.0.0.1:3000 (`/api/*` proxies to FastAPI).

### Routes 404 but sidebar still shows

If every App Router page (`/overview`, `/upload`, …) returns Next’s 404 HTML while the AppShell renders, Turbopack inferred the wrong workspace root (often because a parent `package-lock.json` exists, e.g. under `C:\Users\<you>\`). `next.config.ts` pins `turbopack.root` to this `ate-dashboard` directory — keep that absolute pin; do not set it to `"."` alone.
