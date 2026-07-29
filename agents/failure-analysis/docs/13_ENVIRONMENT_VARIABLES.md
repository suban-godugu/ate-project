# Environment Variables

## Backend (repo root `.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_HOST` | localhost | PostgreSQL host |
| `DATABASE_PORT` | 5432 | PostgreSQL port |
| `DATABASE_NAME` | failure_analysis_db | Database name |
| `DATABASE_USER` | postgres | DB user |
| `DATABASE_PASSWORD` | *(required)* | DB password |
| `DATABASE_URL` | — | Optional full asyncpg URL |
| `REDIS_URL` | redis://localhost:6379/0 | Redis |
| `JWT_SECRET` | dev-only… | HS256 signing secret |
| `JWT_ACCESS_MINUTES` | 30 | Access token lifetime |
| `JWT_REFRESH_DAYS` | 7 | Refresh token lifetime |
| `AUTH_REQUIRED` | false | Enforce Bearer JWT on protected deps |
| `CORS_ORIGINS` | localhost:3000 | Comma-separated origins |
| `BOOTSTRAP_ADMIN_EMAIL` | admin@verilumen.local | First admin email |
| `BOOTSTRAP_ADMIN_PASSWORD` | ChangeMe123! | First admin password |
| `API_PREFIX` | /api/v1 | API path prefix |
| `UPLOAD_DIR` | backend/storage/raw | Upload storage |

## Dashboard (`ate-dashboard/.env.*`)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | /api/v1 | Axios base URL |
| `NEXT_PUBLIC_AUTH_ENABLED` | false (dev) / true (prod) | Enable login + route guards |
| `NEXT_PUBLIC_POLLING_INTERVAL_MS` | 2000 | Default poll interval |
| `NEXT_PUBLIC_LOG_LEVEL` | info | Client logger level |
| `NEXT_PUBLIC_APP_NAME` | ATE Dashboard | Display name |
| `ATE_API_PROXY` | http://127.0.0.1:8000 | Next.js rewrite target for `/api/*` |

Never commit real secrets. Use `.env.local` for machine overrides.
