from contextlib import asynccontextmanager

import logging



from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware



from app.core.config import get_settings

from app.core.exception_handlers import register_exception_handlers

from app.core.logging_config import configure_logging

from app.core.startup_validation import validate_settings

from app.middleware.logging_middleware import LoggingMiddleware

from app.middleware.rate_limit import RateLimitMiddleware

from app.middleware.request_id import RequestIdMiddleware

from app.middleware.security_headers import SecurityHeadersMiddleware

from app.routers import actions, audit, auth, dashboard, jobs, notifications, operations, uploads, users, wafer_predict



settings = get_settings()

logger = logging.getLogger("verilumen")





@asynccontextmanager

async def lifespan(app: FastAPI):

    validate_settings(settings)

    logger.info("VERILUMEN API started", extra={"structured_extra": {"version": settings.app_version}})

    yield





configure_logging(json_logs=settings.json_logs, level=getattr(logging, settings.log_level.upper(), logging.INFO))



app = FastAPI(title="VERILUMEN API", version=settings.app_version, lifespan=lifespan)



register_exception_handlers(app)



# Outermost middleware is added last (runs first on request).

app.add_middleware(

    CORSMiddleware,

    allow_origins=settings.cors_origins,

    allow_credentials=True,

    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],

    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],

)

app.add_middleware(RateLimitMiddleware)

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(LoggingMiddleware)

app.add_middleware(RequestIdMiddleware)



app.include_router(operations.router)

api = settings.api_prefix

app.include_router(auth.router, prefix=api)

app.include_router(users.router, prefix=api)
app.include_router(audit.router, prefix=api)

app.include_router(dashboard.router, prefix=api)

app.include_router(dashboard.search_router, prefix=api)

app.include_router(dashboard.filters_router, prefix=api)

app.include_router(operations.integration_router, prefix=api)

app.include_router(uploads.router, prefix=api)

app.include_router(jobs.router, prefix=api)

app.include_router(wafer_predict.router, prefix=api)

app.include_router(actions.router, prefix=api)

app.include_router(notifications.router, prefix=api)

app.include_router(notifications.rec_router, prefix=api)

app.include_router(notifications.export_router, prefix=api)


