# API Integration Guide — Auth & Operations

## Base URL

Use `NEXT_PUBLIC_API_BASE_URL` (default `/api/v1`). In Docker/NGINX, `/api/` is proxied to the FastAPI service.

## Auth headers

```
Authorization: Bearer <access_token>
X-User-Id: <user_uuid>          # optional; set by dashboard interceptor
X-Role: administrator|engineer|operator|viewer
```

## Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{"email":"admin@verilumen.local","password":"ChangeMe123!"}
```

Response:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {"id":"...","email":"...","role":"administrator","status":"active"}
}
```

## Refresh

```http
POST /api/v1/auth/refresh
{"refresh_token":"..."}
```

## Error codes

| HTTP | Meaning |
|------|---------|
| 401 | Missing/expired/invalid token — client refreshes or redirects to `/login` |
| 403 | Role insufficient |
| 404 | Resource missing |
| 422 | Validation error |
| 500 | Server error |

The dashboard Axios interceptor (`src/lib/http.ts`) maps these to toast notifications and auto-refresh on 401.

## Admin endpoints

| Method | Path | Role |
|--------|------|------|
| GET/POST | `/users` | administrator |
| PATCH/DELETE | `/users/{id}` | administrator |
| GET | `/audit` | administrator |
| GET/PUT | `/settings` | get: any auth; put: administrator |
| GET | `/system/health` | operator+ |
| GET | `/storage/files` | engineer+ |
| GET | `/notifications` | authenticated |
