"""VERILUMEN pipeline consume API — Failure Analysis Agent.

Ingests unified dataset without running file parsers.
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
    callback_context: dict[str, Any] = Field(default_factory=dict)


def _check_key(key: str | None) -> None:
    if SERVICE_KEY and key != SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Invalid service key")


def _fetch_json(uri: str) -> dict[str, Any]:
    with httpx.Client(timeout=120.0) as client:
        resp = client.get(uri)
        resp.raise_for_status()
        return resp.json()


def analyze_failures(dataset: dict[str, Any]) -> dict[str, Any]:
    records = dataset.get("records") or []
    soft = Counter()
    hard = Counter()
    signatures = Counter()
    testers = Counter()
    patterns = Counter()
    chains = Counter()
    wafers: dict[str, dict[str, int]] = {}
    fails = 0
    passes = 0
    others = 0
    for r in records:
        pf = str(r.get("pass_fail") or "").upper()
        if pf == "FAIL":
            fails += 1
        elif pf == "PASS":
            passes += 1
        else:
            others += 1
        if r.get("soft_bin"):
            soft[str(r["soft_bin"])] += 1
        if r.get("hard_bin"):
            hard[str(r["hard_bin"])] += 1
        if r.get("pattern"):
            patterns[str(r["pattern"])] += 1
        if r.get("scan_chain"):
            chains[str(r["scan_chain"])] += 1
        sig = f"{r.get('expected','')}|{r.get('actual','')}"[:128]
        if pf == "FAIL" and sig.strip("|"):
            signatures[sig] += 1
        if r.get("tester"):
            testers[str(r["tester"])] += 1
        wid = str(r.get("wafer_id") or "UNKNOWN")
        bucket = wafers.setdefault(wid, {"fail": 0, "pass": 0, "other": 0, "total": 0})
        bucket["total"] += 1
        if pf == "FAIL":
            bucket["fail"] += 1
        elif pf == "PASS":
            bucket["pass"] += 1
        else:
            bucket["other"] += 1

    record_count = len(records)
    classified = max(fails + passes, 1)
    yield_pct = round(100.0 * passes / classified, 2)
    fail_rate = round(100.0 * fails / max(record_count, 1), 2)
    clusters = [{"signature": s, "count": c} for s, c in signatures.most_common(25)]
    yield_report = {
        "yield_pct": yield_pct,
        "pass_count": passes,
        "fail_count": fails,
        "other_count": others,
        "record_count": record_count,
        "wafer_stats": wafers,
    }
    report = {
        "yield": yield_report,
        "soft_bins": dict(soft),
        "hard_bins": dict(hard),
        "failure_clusters": clusters,
        "fail_signatures": clusters,
        "tester_analysis": dict(testers),
        "wafer_statistics": wafers,
        "pattern_analysis": dict(patterns.most_common(25)),
        "chain_analysis": dict(chains.most_common(25)),
    }
    kpis = {
        "yield_pct": yield_pct,
        "fail_count": fails,
        "pass_count": passes,
        "other_count": others,
        "record_count": record_count,
        "fail_rate": fail_rate,
        "cluster_count": len(clusters),
        "soft_bin_count": len(soft),
        "hard_bin_count": len(hard),
        "pattern_count": len(patterns),
        "chain_count": len(chains),
        "tester_count": len(testers),
        "wafer_count": len(wafers),
    }
    return {"report": report, "yield_report": yield_report, "kpis": kpis}


@router.post("/pipeline/consume")
def pipeline_consume(
    body: ConsumeRequest,
    x_verilumen_service_key: str | None = Header(default=None, alias="X-Verilumen-Service-Key"),
):
    _check_key(x_verilumen_service_key)
    job_id = str(uuid.uuid4())
    try:
        dataset = _fetch_json(body.dataset_uri)
        result = analyze_failures(dataset)
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
