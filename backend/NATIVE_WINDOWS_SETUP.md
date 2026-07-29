# VERILUMEN Native Windows Setup

This guide runs VERILUMEN without Docker by using native Windows installs and local processes.

## Required software

- PostgreSQL 16
- Redis for Windows
- MinIO Server
- Python 3.12
- Node.js 22+ or current LTS

## Service layout

- Dashboard: `http://localhost:3000`
- FastAPI: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- MinIO API: `http://localhost:9000`
- MinIO Console: `http://localhost:9001`

## 1. Backend environment

From `Backend-and-DP-s-main`:

```powershell
Copy-Item .env.example .env
```

Set these values in `.env`:

```env
DATABASE_URL=postgresql+asyncpg://verilumen:CHANGE_ME@localhost:5432/verilumen
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=CHANGE_ME
MINIO_USE_SSL=false
JWT_SECRET=CHANGE_ME
```

## 2. PostgreSQL

Install PostgreSQL 16 as a Windows service, then create the application user and database.

```sql
CREATE USER verilumen WITH PASSWORD 'CHANGE_ME';
CREATE DATABASE verilumen OWNER verilumen;
```

If PostgreSQL was installed with an unknown superuser password, reset it first from an elevated shell before continuing.

Run migrations:

```powershell
cd C:\office\Backend-and-DP-s-main
pip install -r requirements.txt
alembic upgrade head
python scripts/seed.py
```

Seed login:

- `alex@verilumen.ai`
- `changeme123`

## 3. Redis

Start Redis locally and confirm it listens on `6379`.

Example:

```powershell
redis-server
```

## 4. MinIO

Create a local data folder:

```powershell
New-Item -ItemType Directory -Force C:\VERILUMEN\data
```

Start MinIO:

```powershell
$env:MINIO_ROOT_USER = "minioadmin"
$env:MINIO_ROOT_PASSWORD = "CHANGE_ME"
minio server C:\VERILUMEN\data --console-address ":9001"
```

Then create the required buckets:

- `verilumen-raw-uploads`
- `verilumen-parsed`
- `verilumen-wafer-images`
- `verilumen-exports`
- `verilumen-ai-artifacts`

You can create them from the MinIO console at `http://localhost:9001`.

## 5. FastAPI backend

Run the API in one terminal:

```powershell
cd C:\office\Backend-and-DP-s-main
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Verify:

- `http://localhost:8000/health`
- `http://localhost:8000/docs`

## 6. ARQ worker

Run the worker in a second terminal:

```powershell
cd C:\office\Backend-and-DP-s-main
arq app.workers.WorkerSettings
```

## 7. Dashboard

In `dashboard-main/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_API_MODE=live
```

Then run:

```powershell
cd C:\office\dashboard-main
npm install
npm run dev
```

Open:

- `http://localhost:3000/login`
- `http://localhost:3000/dashboard`

## 8. Validation checklist

The stack is connected when:

- PostgreSQL is reachable on `5432`
- Redis is reachable on `6379`
- MinIO is reachable on `9000` and `9001`
- FastAPI returns `200` at `/health`
- Dashboard loads in live mode
- Login works with the seeded user
- Uploads, alerts, notifications, and actions hit backend endpoints

## Notes

- The backend code already defaults to localhost for `DATABASE_URL`, `REDIS_URL`, and `MINIO_ENDPOINT`.
- `docker-compose.yml` can remain in the repo as an optional deployment path, but it is not required for native Windows development.
