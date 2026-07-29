"""Pattern Analysis Agent — run API.

Inputs (STIL/logs) are read only from:
  C:\\personal\\input all file\\<job_id>\\
Outputs (reports) are written only to:
  C:\\personal\\agent and parser output\\<job_id>\\pattern\\
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from pipeline.consume_api import map_dataset_to_pattern_metrics
from pipeline.dataset_loader import load_dataset

router = APIRouter(tags=["pattern-run"])

SERVICE_KEY = os.environ.get("VERILUMEN_SERVICE_KEY", "dev-service-key-change-me")
AGENT_OUTPUT_ROOT = Path(
    os.environ.get("AGENT_OUTPUT_ROOT", r"C:\personal\agent and parser output")
)
UPLOAD_INPUT_ROOT = Path(
    os.environ.get("UPLOAD_INPUT_ROOT", r"C:\personal\input all file")
)
PATTERN_ROOT = Path(__file__).resolve().parent.parent
STIL_UPLOAD_DIR = PATTERN_ROOT / "uploads" / "stil"
ATE_UPLOAD_DIR = PATTERN_ROOT / "uploads" / "ate_logs"

_JOBS: dict[str, dict[str, Any]] = {}
_LATEST_JOB_ID: str | None = None


class PatternRunRequest(BaseModel):
    job_id: str
    dataset_path: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    upload_id: str | None = None
    dataset_uri: str | None = None
    # dataset_kpis = fast platform path (no STIL/ATE re-parse). full_agent = Validate session.
    # auto = full_agent when input root has STIL, else dataset_kpis.
    mode: Literal["auto", "full_agent", "dataset_kpis"] = "auto"


def _check_key(key: str | None) -> None:
    if SERVICE_KEY and key != SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Invalid service key")


def _place_ref(src: Path, dest: Path) -> None:
    """Hardlink/symlink input into Pattern workspace view (no byte copy)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() or dest.is_symlink():
        try:
            dest.unlink()
        except OSError:
            pass
    try:
        os.link(src, dest)
    except OSError:
        os.symlink(src, dest)


def _load_latest_from_disk() -> dict[str, Any] | None:
    if not AGENT_OUTPUT_ROOT.exists():
        return None
    jobs = sorted(
        [p for p in AGENT_OUTPUT_ROOT.iterdir() if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for job_dir in jobs:
        report_path = job_dir / "pattern" / "report.json"
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


def _discover_inputs(job_id: str) -> tuple[Path | None, list[Path]]:
    """Read STIL/logs only from input all file/<job_id>/."""
    inputs = UPLOAD_INPUT_ROOT / job_id
    if not inputs.is_dir():
        return None, []
    stil_files = sorted(
        [
            p
            for p in inputs.iterdir()
            if p.is_file() and not p.name.startswith("_original_") and p.suffix.lower() == ".stil"
        ],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    log_files = sorted(
        [
            p
            for p in inputs.iterdir()
            if p.is_file()
            and not p.name.startswith("_original_")
            and p.suffix.lower() in {".log", ".txt"}
        ],
        key=lambda p: p.name.lower(),
    )
    stil = stil_files[0] if stil_files else None
    return stil, log_files


def _materialize_into_workspace(stil: Path, logs: list[Path]) -> tuple[str, list[str]]:
    """Link (not copy) inputs into Pattern uploads/ for workspace-relative paths."""
    STIL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ATE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stil_dest = STIL_UPLOAD_DIR / stil.name
    _place_ref(stil, stil_dest)
    stil_rel = f"uploads/stil/{stil.name}".replace("\\", "/")
    log_rels: list[str] = []
    for log_path in logs:
        dest = ATE_UPLOAD_DIR / log_path.name
        _place_ref(log_path, dest)
        log_rels.append(f"uploads/ate_logs/{log_path.name}".replace("\\", "/"))
    return stil_rel, log_rels


def _kpis_from_full_report(report: dict[str, Any]) -> dict[str, Any]:
    meta = report.get("metadata") or {}
    cycles = report.get("cycles_count") or len(report.get("cycles") or [])
    chains = report.get("scan_chains_count") or meta.get("chain_count") or 0
    patterns = meta.get("pattern_count") or 0
    return {
        "pattern_count": patterns,
        "chain_count": chains,
        "fail_count": 0,
        "failing_chains": 0,
        "coverage_score": (meta.get("toggle_coverage_pct") or 0) / 100.0
        if meta.get("toggle_coverage_pct") is not None
        else 1.0,
        "compression_ratio": float(meta.get("compression_ratio") or 0),
        "record_count": cycles,
    }


def _try_full_agent_run(job_id: str, metadata: dict[str, Any]) -> dict[str, Any] | None:
    """Run full Pattern Validate when platform saved STIL under input all file."""
    stil, logs = _discover_inputs(job_id)
    if stil is None:
        return None

    stil_rel, log_rels = _materialize_into_workspace(stil, logs)

    # Lazy import avoids circular import at module load (server imports this router).
    from server import WorkspaceFileRequest, _execute_parse_workspace  # noqa: WPS433
    import server as pattern_server  # noqa: WPS433

    # Redirect session/output artifacts into agent and parser output/<job>/pattern/
    out_dir = AGENT_OUTPUT_ROOT / job_id / "pattern"
    out_dir.mkdir(parents=True, exist_ok=True)
    prev_out = getattr(pattern_server, "OUTPUT_DIR", None)
    pattern_server.OUTPUT_DIR = str(out_dir)
    os.environ["PATTERN_OUTPUT_DIR"] = str(out_dir)

    req_kwargs: dict[str, Any] = {"filename": stil_rel}
    if len(log_rels) == 1:
        req_kwargs["ate_log_filename"] = log_rels[0]
    elif len(log_rels) > 1:
        req_kwargs["ate_log_filenames"] = log_rels

    try:
        report = _execute_parse_workspace(WorkspaceFileRequest(**req_kwargs))
    finally:
        if prev_out is not None:
            pattern_server.OUTPUT_DIR = prev_out

    if not isinstance(report, dict):
        report = {"raw": report}

    dataset_metrics: dict[str, Any] = {}
    try:
        # Prefer dataset KPIs when available; full report still returned as `report`.
        ds_path = AGENT_OUTPUT_ROOT / job_id / "parser" / "unified_dataset.json"
        if ds_path.exists():
            dataset_metrics = map_dataset_to_pattern_metrics(load_dataset(str(ds_path)))
    except Exception:  # noqa: BLE001
        dataset_metrics = {}

    kpis = dataset_metrics.get("kpis") or _kpis_from_full_report(report)
    coverage = dataset_metrics.get("coverage_report") or {
        "record_count": kpis.get("record_count") or report.get("cycles_count") or 0,
        "pattern_count": kpis.get("pattern_count"),
        "chain_count": kpis.get("chain_count"),
    }

    return {
        "job_id": job_id,
        "upload_id": job_id,
        "status": "completed",
        "mode": "full_agent",
        "metadata": {
            **(metadata or {}),
            "stil_file": stil.name,
            "log_files": [p.name for p in logs],
            "input_root": str(UPLOAD_INPUT_ROOT / job_id),
            "workspace_stil": stil_rel,
            "workspace_logs": log_rels,
        },
        "kpis": kpis,
        "coverage_report": coverage,
        "chain_metrics": dataset_metrics.get("chain_metrics") or {},
        "report": report,
        "full_analysis": True,
    }


def _write_pattern_report(job_id: str, payload: dict[str, Any]) -> None:
    try:
        out = AGENT_OUTPUT_ROOT / job_id / "pattern"
        out.mkdir(parents=True, exist_ok=True)
        # Avoid writing multi‑MB session blobs for platform KPI mode.
        to_store = dict(payload)
        report = to_store.get("report")
        if isinstance(report, dict) and (
            to_store.get("mode") == "dataset_kpis"
            or len(json.dumps(report, default=str)) > 2_000_000
        ):
            to_store["report"] = {
                "summary": True,
                "cycles_count": report.get("cycles_count"),
                "scan_chains_count": report.get("scan_chains_count"),
                "metadata": report.get("metadata") or {},
            }
        (out / "report.json").write_text(
            json.dumps(to_store, indent=2, default=str), encoding="utf-8"
        )
    except Exception:  # noqa: BLE001
        pass


@router.post("/api/v1/pattern/run")
def pattern_run(
    body: PatternRunRequest,
    x_verilumen_service_key: str | None = Header(default=None, alias="X-Verilumen-Service-Key"),
):
    global _LATEST_JOB_ID
    _check_key(x_verilumen_service_key)
    job_id = body.job_id or body.upload_id or str(uuid.uuid4())
    path = body.dataset_path or body.dataset_uri or ""
    mode = body.mode or "auto"
    try:
        if mode != "dataset_kpis":
            # auto / full_agent: try Validate session when STIL inputs exist
            full = _try_full_agent_run(job_id, body.metadata or {})
            if full is not None:
                _JOBS[job_id] = {"status": "completed", "percent": 100, "result": full}
                _LATEST_JOB_ID = job_id
                _write_pattern_report(job_id, full)
                return full
            if mode == "full_agent":
                raise HTTPException(
                    status_code=400,
                    detail="full_agent requires STIL under parser/inputs for this job",
                )

        dataset = load_dataset(path)
        result = map_dataset_to_pattern_metrics(dataset)
        payload = {
            "job_id": job_id,
            "upload_id": job_id,
            "status": "completed",
            "mode": "dataset_kpis",
            "metadata": body.metadata,
            "full_analysis": False,
            **result,
        }
        _JOBS[job_id] = {"status": "completed", "percent": 100, "result": payload}
        _LATEST_JOB_ID = job_id
        _write_pattern_report(job_id, payload)
        return payload
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        _JOBS[job_id] = {"status": "failed", "error": str(exc)}
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/api/v1/pattern/jobs/{job_id}")
def pattern_job(job_id: str):
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@router.get("/api/v1/pattern/latest")
def pattern_latest():
    """Embed poll — last platform /pattern/run, with disk artifact fallback."""
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
    raise HTTPException(status_code=404, detail="no platform pattern job yet")
