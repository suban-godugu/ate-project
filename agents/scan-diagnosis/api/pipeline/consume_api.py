"""VERILUMEN pipeline consume API — Scan Diagnosis Agent.

Consumes unified dataset + Pattern/Failure result URIs. Does not parse raw logs.
"""

from __future__ import annotations

import os
import uuid
from collections import Counter
from typing import Any

import httpx
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1", tags=["pipeline"])

SERVICE_KEY = os.environ.get("VERILUMEN_SERVICE_KEY", "dev-service-key-change-me")
_JOBS: dict[str, dict[str, Any]] = {}


class ConsumeRequest(BaseModel):
    upload_id: str
    dataset_uri: str
    dataset_sha256: str | None = None
    pattern_result_uri: str | None = None
    failure_result_uri: str | None = None
    callback_context: dict[str, Any] = Field(default_factory=dict)


def _check_key(key: str | None) -> None:
    if SERVICE_KEY and key != SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Invalid service key")


def _fetch_json(uri: str) -> dict[str, Any]:
    with httpx.Client(timeout=120.0) as client:
        resp = client.get(uri)
        resp.raise_for_status()
        return resp.json()


def diagnose(
    dataset: dict[str, Any],
    pattern: dict[str, Any] | None,
    failure: dict[str, Any] | None,
) -> dict[str, Any]:
    records = dataset.get("records") or []
    flop_hits: Counter[str] = Counter()
    chain_hits: Counter[str] = Counter()
    fail_types: Counter[str] = Counter()
    for r in records:
        if str(r.get("pass_fail") or "").upper() != "FAIL":
            continue
        meta = r.get("metadata") or {}
        flop = meta.get("fail_flop_id") or ""
        if flop:
            flop_hits[str(flop)] += 1
        chain = r.get("scan_chain") or ""
        if chain:
            chain_hits[str(chain)] += 1
        ft = meta.get("fail_type") or "unknown"
        fail_types[str(ft)] += 1

    top_flop = flop_hits.most_common(1)
    top_chain = chain_hits.most_common(1)
    root_cause = "unknown"
    if top_flop:
        root_cause = f"fail_flop:{top_flop[0][0]}"
    elif top_chain:
        root_cause = f"scan_chain:{top_chain[0][0]}"

    fail_count = sum(1 for r in records if str(r.get("pass_fail") or "").upper() == "FAIL")
    confidence = 0.85 if top_flop else (0.65 if top_chain else 0.4)
    if failure and (failure.get("kpis") or {}).get("yield_pct") is not None:
        # Blend with failure yield signal
        yp = float(failure["kpis"]["yield_pct"])
        confidence = min(0.95, confidence + (0.05 if yp < 95 else 0))

    recommendations = []
    if top_chain:
        recommendations.append(
            {
                "code": "RETEST_CHAIN",
                "severity": "high",
                "message": f"Retest / isolate scan chain {top_chain[0][0]} ({top_chain[0][1]} fails)",
            }
        )
    if top_flop:
        recommendations.append(
            {
                "code": "LOCALIZE_FLOP",
                "severity": "medium",
                "message": f"Investigate fail flop {top_flop[0][0]}",
            }
        )
    if pattern and (pattern.get("kpis") or {}).get("compression_ratio"):
        recommendations.append(
            {
                "code": "PATTERN_COVERAGE",
                "severity": "info",
                "message": "Cross-check Pattern Analysis coverage against diagnosis hotspots",
            }
        )

    report = {
        "chain_diagnosis": dict(chain_hits),
        "fail_flop_localization": dict(flop_hits),
        "fail_types": dict(fail_types),
        "root_cause": root_cause,
        "diagnosis_confidence": confidence,
        "repair_suggestions": recommendations,
        "inputs": {
            "pattern_kpis": (pattern or {}).get("kpis"),
            "failure_kpis": (failure or {}).get("kpis"),
        },
    }
    kpis = {
        "fail_count": fail_count,
        "localized_flops": len(flop_hits),
        "affected_chains": len(chain_hits),
        "confidence": confidence,
    }
    return {
        "report": report,
        "kpis": kpis,
        "recommendations": recommendations,
        "confidence": confidence,
    }


@router.post("/pipeline/consume")
def pipeline_consume(
    body: ConsumeRequest,
    x_verilumen_service_key: str | None = Header(default=None, alias="X-Verilumen-Service-Key"),
):
    _check_key(x_verilumen_service_key)
    job_id = str(uuid.uuid4())
    try:
        dataset = _fetch_json(body.dataset_uri)
        pattern = _fetch_json(body.pattern_result_uri) if body.pattern_result_uri else None
        failure = _fetch_json(body.failure_result_uri) if body.failure_result_uri else None
        result = diagnose(dataset, pattern, failure)
        payload = {"job_id": job_id, "upload_id": body.upload_id, "status": "completed", **result}
        _JOBS[job_id] = {"status": "completed", "percent": 100, "result": payload}
        return payload
    except Exception as exc:  # noqa: BLE001
        _JOBS[job_id] = {"status": "failed", "error": str(exc)}
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/pipeline/jobs/{job_id}")
def pipeline_job(job_id: str):
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job
