"""Shared upload-pipeline helpers for integration tests and verify_parser_e2e.py."""

from __future__ import annotations

import hashlib
import asyncio
import os
import time
from pathlib import Path

import httpx
import redis.asyncio as aioredis
from minio import Minio
from sqlalchemy import create_engine, text

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
API_BASE = os.environ.get("VERILUMEN_API_BASE", "http://localhost:8000/api/v1")
TEST_LOGIN = {"email": "alex@verilumen.ai", "password": "changeme123"}


def sync_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://verilumen:verilumen@localhost:5432/verilumen")
    return url.replace("postgresql+asyncpg://", "postgresql://")


def db_scalar(sql: str, params: dict | None = None):
    engine = create_engine(sync_db_url())
    with engine.connect() as conn:
        return conn.execute(text(sql), params or {}).scalar()


def db_query(sql: str, params: dict | None = None) -> list:
    engine = create_engine(sync_db_url())
    with engine.connect() as conn:
        return conn.execute(text(sql), params or {}).fetchall()


async def api_reachable() -> bool:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get("http://localhost:8000/live")
            return r.status_code == 200
    except Exception:
        return False


async def postgres_reachable() -> bool:
    try:
        db_scalar("SELECT 1")
        return True
    except Exception:
        return False


async def stack_available() -> bool:
    return await api_reachable() and await postgres_reachable()


async def login(client: httpx.AsyncClient) -> str:
    r = await client.post(f"{API_BASE}/auth/login", json=TEST_LOGIN)
    r.raise_for_status()
    return r.json()["access_token"]


async def wait_job(client: httpx.AsyncClient, job_id: str, token: str, timeout: int = 180) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    deadline = time.time() + timeout
    last: dict = {}
    while time.time() < deadline:
        r = await client.get(f"{API_BASE}/uploads/{job_id}", headers=headers)
        r.raise_for_status()
        data = r.json()
        job = data.get("job", {})
        last = job
        if job.get("status") in ("Completed", "Failed"):
            return data
        await asyncio.sleep(2)
    return {"job": last, "timeout": True}


async def upload_file(
    client: httpx.AsyncClient,
    token: str,
    file_path: Path,
    kind: str,
    module: str = "scan-chain",
) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    raw = file_path.read_bytes()
    checksum = hashlib.sha256(raw).hexdigest()

    presign = await client.post(
        f"{API_BASE}/uploads/presign",
        headers=headers,
        json={"file_name": file_path.name, "size": len(raw), "kind": kind, "module": module},
    )
    presign.raise_for_status()
    meta = presign.json()
    job_id = meta["job_id"]
    upload_url = meta["upload_url"]

    put = await client.put(upload_url, content=raw, headers={"Content-Type": "application/octet-stream"})
    put.raise_for_status()

    complete = await client.post(
        f"{API_BASE}/uploads/{job_id}/complete",
        headers=headers,
        json={"checksum_sha256": checksum},
    )
    complete.raise_for_status()
    return {"job_id": job_id, "file_name": file_path.name}


async def check_redis_job_status(job_id: str) -> bool:
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    prefix = os.environ.get("REDIS_PREFIX", "verilumen:")
    r = aioredis.from_url(redis_url, decode_responses=True)
    try:
        return await r.get(f"{prefix}job:{job_id}:status") is not None
    finally:
        await r.aclose()


def check_minio_parsed(job_id: str, raw_key: str | None) -> tuple[bool, bool]:
    client = Minio(
        os.environ.get("MINIO_ENDPOINT", "localhost:9000"),
        access_key=os.environ.get("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.environ.get("MINIO_SECRET_KEY", "minioadmin123"),
        secure=False,
    )
    raw_bucket = os.environ.get("MINIO_BUCKET_RAW", "verilumen-raw-uploads")
    parsed_bucket = os.environ.get("MINIO_BUCKET_PARSED", "verilumen-parsed")

    has_raw = False
    if raw_key:
        try:
            client.stat_object(raw_bucket, raw_key)
            has_raw = True
        except Exception:
            pass

    has_parsed = False
    for suffix in (f"{job_id}/summary.json", f"{job_id}/scan-chains.json"):
        try:
            client.stat_object(parsed_bucket, suffix)
            has_parsed = True
        except Exception:
            pass
    return has_raw, has_parsed
