"""Scan Diagnosis — POST /api/v1/scan/run (dataset + pattern + failure results)."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from api.pipeline.consume_api import diagnose

router = APIRouter(prefix="/api/v1", tags=["scan-run"])

SERVICE_KEY = os.environ.get("VERILUMEN_SERVICE_KEY", "dev-service-key-change-me")
AGENT_OUTPUT_ROOT = Path(
    os.environ.get("AGENT_OUTPUT_ROOT", r"C:\personal\agent and parser output")
)
_JOBS: dict[str, dict[str, Any]] = {}
_LATEST_JOB_ID: str | None = None


class ScanRunRequest(BaseModel):
    job_id: str
    dataset_path: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    pattern_result_path: str | None = None
    failure_result_path: str | None = None
    upload_id: str | None = None
    dataset_uri: str | None = None
    pattern_result_uri: str | None = None
    failure_result_uri: str | None = None


def _check_key(key: str | None) -> None:
    if SERVICE_KEY and key != SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Invalid service key")


def _load(path_or_uri: str | None) -> dict[str, Any] | None:
    if not path_or_uri:
        return None
    p = Path(path_or_uri)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    with httpx.Client(timeout=120.0) as client:
        r = client.get(path_or_uri)
        r.raise_for_status()
        return r.json()


def _load_latest_from_disk() -> dict[str, Any] | None:
    if not AGENT_OUTPUT_ROOT.exists():
        return None
    jobs = sorted(
        [p for p in AGENT_OUTPUT_ROOT.iterdir() if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for job_dir in jobs:
        report_path = job_dir / "scan" / "report.json"
        if not report_path.exists():
            continue
        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(data, dict):
            continue
        data.setdefault("job_id", job_dir.name)
        data.setdefault("upload_id", job_dir.name)
        data.setdefault("status", "completed")
        return data
    return None


@router.post("/scan/run")
def scan_run(
    body: ScanRunRequest,
    x_verilumen_service_key: str | None = Header(default=None, alias="X-Verilumen-Service-Key"),
):
    global _LATEST_JOB_ID
    _check_key(x_verilumen_service_key)
    job_id = body.job_id or body.upload_id or str(uuid.uuid4())
    try:
        dataset = _load(body.dataset_path or body.dataset_uri) or {}
        pattern = _load(body.pattern_result_path or body.pattern_result_uri)
        failure = _load(body.failure_result_path or body.failure_result_uri)
        result = diagnose(dataset, pattern, failure)
        payload = {
            "job_id": job_id,
            "upload_id": job_id,
            "status": "completed",
            "metadata": body.metadata,
            **result,
        }
        _JOBS[job_id] = {"status": "completed", "percent": 100, "result": payload}
        _LATEST_JOB_ID = job_id
        # Persist under agent and parser output/<job>/scan/ only
        try:
            from api.adapters.paths import job_scan_output_dir

            out = job_scan_output_dir(job_id)
            (out / "report.json").write_text(
                json.dumps(payload, indent=2, default=str), encoding="utf-8"
            )
        except Exception:  # noqa: BLE001
            pass
        return payload
    except Exception as exc:  # noqa: BLE001
        _JOBS[job_id] = {"status": "failed", "error": str(exc)}
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/scan/jobs/{job_id}")
def scan_job(job_id: str):
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@router.get("/scan/latest")
def scan_latest():
    """Embed poll — last platform /scan/run, with disk artifact fallback."""
    global _LATEST_JOB_ID
    if _LATEST_JOB_ID and _LATEST_JOB_ID in _JOBS:
        job = _JOBS[_LATEST_JOB_ID]
        if job.get("status") == "completed" and job.get("result"):
            return job["result"]
    disk = _load_latest_from_disk()
    if disk:
        jid = str(disk.get("job_id") or disk.get("upload_id") or "disk-latest")
        _JOBS[jid] = {"status": "completed", "percent": 100, "result": disk}
        _LATEST_JOB_ID = jid
        return disk
    raise HTTPException(status_code=404, detail="no platform scan job yet")


@router.post("/scan/reload-live")
def scan_reload_live(
    request: Request,
    x_verilumen_service_key: str | None = Header(default=None, alias="X-Verilumen-Service-Key"),
):
    """Clear in-memory + parquet caches so newly published data/stil + data/logs are picked up."""
    _check_key(x_verilumen_service_key)
    from api.adapters import data_loader, diagnosis_service
    from api.adapters.diagnosis_service import validate_live_path
    from api.adapters.paths import CACHE_DIR, DATA_DIR, LOG_DIR

    # Disk parquet cache
    if CACHE_DIR.exists():
        for p in CACHE_DIR.glob("*"):
            try:
                if p.is_file():
                    p.unlink()
            except OSError:
                pass

    # In-process caches
    try:
        data_loader.list_filter_options_cached.cache_clear()
    except Exception:  # noqa: BLE001
        pass
    try:
        diagnosis_service._DASHBOARD_CACHE.clear()  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass

    live = validate_live_path()
    try:
        request.app.state.live_validation = live
    except Exception:  # noqa: BLE001
        pass

    stil_count = len(list((DATA_DIR / "stil").glob("*.stil"))) if (DATA_DIR / "stil").exists() else 0
    from api.adapters.data_loader import select_logs

    log_count = len(select_logs(max_per_lot=None))
    return {
        "ok": True,
        "data_dir": str(DATA_DIR),
        "log_dir": str(LOG_DIR),
        "stil_count": stil_count,
        "log_count": log_count,
        "live_path_ok": bool(live.get("ok")),
        "failure_records": live.get("failure_records"),
        "live_errors": live.get("errors") or [],
    }
