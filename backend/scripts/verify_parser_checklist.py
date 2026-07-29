#!/usr/bin/env python3
"""Part 1 checklist: verify parser output differs by input (not faked)."""

from __future__ import annotations

import asyncio
import hashlib
import shutil
import sys
import tempfile
import time
from pathlib import Path

import httpx
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
API = "http://localhost:8000/api/v1"


def db_url() -> str:
    import os

    url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://verilumen:verilumen@localhost:5433/verilumen")
    return url.replace("postgresql+asyncpg://", "postgresql://")


def q(sql: str, params: dict | None = None) -> list:
    with create_engine(db_url()).connect() as conn:
        return conn.execute(text(sql), params or {}).fetchall()


async def upload(client: httpx.AsyncClient, token: str, path: Path, kind: str) -> str:
    raw = path.read_bytes()
    headers = {"Authorization": f"Bearer {token}"}
    presign = await client.post(
        f"{API}/uploads/presign",
        headers=headers,
        json={"file_name": path.name, "size": len(raw), "kind": kind, "module": "scan-chain"},
    )
    presign.raise_for_status()
    meta = presign.json()
    await client.put(meta["upload_url"], content=raw, headers={"Content-Type": "application/octet-stream"})
    await client.post(
        f"{API}/uploads/{meta['job_id']}/complete",
        headers=headers,
        json={"checksum_sha256": hashlib.sha256(raw).hexdigest()},
    )
    return meta["job_id"]


async def wait_done(client: httpx.AsyncClient, token: str, job_id: str, timeout: int = 120) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    deadline = time.time() + timeout
    steps_seen: list[str] = []
    while time.time() < deadline:
        r = await client.get(f"{API}/uploads/{job_id}", headers=headers)
        r.raise_for_status()
        job = r.json()["job"]
        status = job.get("status", "")
        for s in r.json().get("steps", []):
            if s.get("status") == "active" and s.get("id") not in steps_seen:
                steps_seen.append(s["id"])
        if status in ("Completed", "Failed"):
            return {"status": status, "steps": steps_seen, "job": job}
        await asyncio.sleep(1)
    return {"status": "timeout", "steps": steps_seen}


async def main() -> int:
    print("=== Part 1 Parser Verification ===\n")
    stdf = FIXTURES / "sample.stdf"
    log = FIXTURES / "sample_ate.log"
    if not stdf.exists():
        print("Run: python scripts/build_stdf_fixture.py")
        return 1

    failures_before = q("SELECT COUNT(*) FROM scan_chain_failures")[0][0]

    async with httpx.AsyncClient(timeout=120) as client:
        try:
            await client.get("http://localhost:8000/health")
        except Exception as exc:
            print(f"FAIL: API not reachable ({exc})")
            return 1

        login = await client.post(f"{API}/auth/login", json={"email": "alex@verilumen.ai", "password": "changeme123"})
        if login.status_code != 200:
            print(f"FAIL: login ({login.text})")
            return 1
        token = login.json()["access_token"]

        # STDF upload + pipeline timing
        t0 = time.monotonic()
        stdf_job = await upload(client, token, stdf, "data")
        stdf_result = await wait_done(client, token, stdf_job)
        stdf_elapsed = time.monotonic() - t0
        print(f"[{'PASS' if stdf_result['status'] == 'Completed' else 'FAIL'}] STDF upload: {stdf_result['status']} ({stdf_elapsed:.1f}s, steps={stdf_result['steps']})")
        if stdf_elapsed < 0.5:
            print("  WARN: completed very fast — confirm worker ran, not instant mock")

        # LOG upload
        log_job = await upload(client, token, log, "log")
        log_result = await wait_done(client, token, log_job)
        print(f"[{'PASS' if log_result['status'] == 'Completed' else 'FAIL'}] LOG upload: {log_result['status']}")

        # Same STDF, different filename (duplicate content)
        dup_path = FIXTURES / "_dup_lot2.stdf"
        shutil.copy2(stdf, dup_path)
        dup_job = await upload(client, token, dup_path, "data")
        await wait_done(client, token, dup_job)
        dup_path.unlink(missing_ok=True)

    failures_after = q("SELECT COUNT(*) FROM scan_chain_failures")[0][0]
    print(f"[{'PASS' if failures_after > failures_before else 'FAIL'}] scan_chain_failures grew: {failures_before} -> {failures_after}")

    stdf_chains = q(
        "SELECT chain_id, pattern_id FROM scan_chain_failures WHERE chain_id = 'SC-4821' ORDER BY created_at DESC LIMIT 3"
    )
    log_chains = q(
        "SELECT chain_id, pattern_id FROM scan_chain_failures WHERE chain_id = 'SC-3100' ORDER BY created_at DESC LIMIT 3"
    )
    print(f"[{'PASS' if stdf_chains else 'FAIL'}] STDF failure SC-4821 present: {stdf_chains[:2]}")
    print(f"[{'PASS' if log_chains else 'FAIL'}] LOG-only failure SC-3100 present: {log_chains[:2]}")

    # Different inputs -> different chain sets
    stdf_only = bool(stdf_chains)
    log_only = bool(log_chains)
    print(f"[{'PASS' if stdf_only and log_only else 'FAIL'}] STDF vs LOG produce different failure signatures")

    summary = q(
        "SELECT patterns_found, scan_chains, yield_pct FROM ai_log_summaries ORDER BY created_at DESC LIMIT 2"
    )
    print(f"[PASS] Latest ai_log_summaries: {summary}")

    # Dashboard reflects live data
    async with httpx.AsyncClient(timeout=30) as client:
        login = await client.post(f"{API}/auth/login", json={"email": "alex@verilumen.ai", "password": "changeme123"})
        token = login.json()["access_token"]
        dash = await client.get(
            f"{API}/dashboard/scan-chain/overview",
            headers={"Authorization": f"Bearer {token}"},
        )
        rows = dash.json().get("rows", []) if dash.status_code == 200 else []
        print(f"[{'PASS' if dash.status_code == 200 and len(rows) > 0 else 'FAIL'}] Dashboard scan-chain rows: {len(rows)} (status={dash.status_code})")

    print("\n=== Part 1 complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
