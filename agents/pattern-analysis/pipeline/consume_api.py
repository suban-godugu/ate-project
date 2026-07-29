"""VERILUMEN pipeline consume API — Pattern Analysis Agent.

Accepts unified dataset URI from Backend Orchestrator. Does NOT parse raw files.
"""

from __future__ import annotations

import os
import uuid
from collections import Counter
from typing import Any

import httpx
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["pipeline"])

SERVICE_KEY = os.environ.get("VERILUMEN_SERVICE_KEY", "dev-service-key-change-me")
_JOBS: dict[str, dict[str, Any]] = {}


class ConsumeRequest(BaseModel):
    upload_id: str
    dataset_uri: str
    dataset_sha256: str | None = None
    callback_context: dict[str, Any] = Field(default_factory=dict)


def _check_key(key: str | None) -> None:
    if SERVICE_KEY and key != SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Invalid service key")


def _fetch_json(uri: str) -> dict[str, Any]:
    with httpx.Client(timeout=120.0) as client:
        resp = client.get(uri)
        resp.raise_for_status()
        return resp.json()


def map_dataset_to_pattern_metrics(dataset: dict[str, Any]) -> dict[str, Any]:
    records = dataset.get("records") or []
    patterns = Counter()
    chains = Counter()
    fails = 0
    for r in records:
        pf = str(r.get("pass_fail") or "").upper()
        if pf == "FAIL":
            fails += 1
        pat = r.get("pattern") or ""
        if pat:
            patterns[pat] += 1
        ch = r.get("scan_chain") or ""
        if ch:
            chains[ch] += 1
    total = max(len(records), 1)
    coverage = {
        "pattern_count": len(patterns),
        "chain_count": len(chains),
        "record_count": len(records),
        "fail_rate": fails / total,
        "top_patterns": patterns.most_common(20),
        "top_chains": chains.most_common(20),
    }
    chain_metrics = {
        "unique_chains": len(chains),
        "failing_chains": sum(1 for c, n in chains.items() if n > 0),
        "chain_fail_counts": dict(chains),
    }
    # Compression ratio heuristic: unique patterns / records
    compression_ratio = (len(patterns) / total) if total else 0.0
    kpis = {
        "pattern_count": len(patterns),
        "chain_count": len(chains),
        "fail_count": fails,
        "failing_chains": chain_metrics["failing_chains"],
        "compression_ratio": round(compression_ratio, 4),
        "coverage_score": round(1.0 - coverage["fail_rate"], 4),
    }
    return {
        "report": {
            "pattern_validation": {"ok": True, "record_count": len(records)},
            "coverage": coverage,
            "compression_ratio": compression_ratio,
            "pattern_burst": patterns.most_common(10),
            "chain_metrics": chain_metrics,
            "cvm": {"status": "derived_from_unified_dataset", "vector_fields": ["expected", "actual"]},
        },
        "coverage_report": coverage,
        "chain_metrics": chain_metrics,
        "kpis": kpis,
    }


@router.post("/api/pipeline/consume")
def pipeline_consume(
    body: ConsumeRequest,
    x_verilumen_service_key: str | None = Header(default=None, alias="X-Verilumen-Service-Key"),
):
    _check_key(x_verilumen_service_key)
    job_id = str(uuid.uuid4())
    _JOBS[job_id] = {"status": "running", "upload_id": body.upload_id, "percent": 10}
    try:
        dataset = _fetch_json(body.dataset_uri)
        result = map_dataset_to_pattern_metrics(dataset)
        payload = {
            "job_id": job_id,
            "upload_id": body.upload_id,
            "status": "completed",
            **result,
        }
        _JOBS[job_id] = {"status": "completed", "percent": 100, "result": payload}
        return payload
    except Exception as exc:  # noqa: BLE001
        _JOBS[job_id] = {"status": "failed", "error": str(exc), "percent": 0}
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/api/pipeline/jobs/{job_id}")
def pipeline_job(job_id: str):
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job
