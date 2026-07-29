"""Celery application for async ingestion."""

from __future__ import annotations

from backend.config import CELERY_ENABLED, REDIS_URL

if CELERY_ENABLED:
    from celery import Celery

    celery_app = Celery("fa_ingestion", broker=REDIS_URL, backend=REDIS_URL)
    celery_app.conf.task_routes = {"backend.ingestion.tasks.process_upload_task": {"queue": "ingestion"}}
else:
    celery_app = None
