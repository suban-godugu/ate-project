"""Background ingestion tasks — never block the FastAPI event loop incorrectly."""

from __future__ import annotations

import asyncio
import logging
import threading

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.celery_app import CELERY_ENABLED, celery_app
from backend.database import create_engine
from backend.ingestion.upload_service import UploadService

logger = logging.getLogger(__name__)


async def _process_upload_async(upload_id: str) -> dict:
    """
    Process on a dedicated engine bound to this thread's event loop.

    The process-global async engine cannot be shared across asyncio loops (asyncpg).
    """
    worker_engine = create_engine()
    local_sessions = async_sessionmaker(
        worker_engine, expire_on_commit=False, class_=AsyncSession
    )
    try:
        async with local_sessions() as session:
            service = UploadService(session)
            return await service.process_existing_upload(upload_id)
    finally:
        await worker_engine.dispose()


def _run_in_background_thread(upload_id: str) -> None:
    try:
        asyncio.run(_process_upload_async(upload_id))
    except Exception:  # noqa: BLE001
        logger.exception("Background processing failed for upload %s", upload_id)


def enqueue_upload_processing(upload_id: str) -> str | None:
    """
    Queue upload processing.

    Returns Celery task id when available; otherwise starts a daemon thread
    so FastAPI's running event loop is never blocked by asyncio.run().
    """
    if CELERY_ENABLED and celery_app is not None:
        async_result = process_upload_task.delay(upload_id)
        return str(async_result.id)

    logger.info("Celery disabled — processing upload %s in background thread", upload_id)
    worker = threading.Thread(
        target=_run_in_background_thread,
        args=(upload_id,),
        name=f"ingest-{upload_id[:8]}",
        daemon=True,
    )
    worker.start()
    return None


if CELERY_ENABLED and celery_app is not None:

    @celery_app.task(name="backend.ingestion.tasks.process_upload_task")
    def process_upload_task(upload_id: str) -> dict:
        return asyncio.run(_process_upload_async(upload_id))
