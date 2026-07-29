# Folder Structure

```
Failure-Analysis-Agent/
├── backend/
│   ├── auth/                 # JWT auth, users, audit, settings, health APIs
│   ├── ingestion/            # FA-FR-001 upload pipeline
│   ├── main.py               # FastAPI entry + routers
│   └── settings.py           # Env-backed configuration
├── ate-dashboard/
│   ├── src/
│   │   ├── app/              # Routes (overview, login, users, settings, …)
│   │   ├── components/       # UI + AuthGuard + AppShell + workbench
│   │   ├── hooks/
│   │   ├── lib/              # api, config, http, logger, rbac
│   │   ├── services/
│   │   ├── stores/           # Zustand (analysis, auth, settings, …)
│   │   └── middleware.ts     # Auth redirect edge middleware
│   ├── .env.development
│   ├── .env.production
│   └── Dockerfile
├── deploy/nginx.conf
├── docker-compose.yml
├── Dockerfile                # API image
└── docs/                     # Architecture, API, deploy, env docs
```
