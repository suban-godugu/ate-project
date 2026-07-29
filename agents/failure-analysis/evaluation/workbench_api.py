"""Workbench API — aggregated endpoints for the evaluation UI."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import API_PREFIX
from backend.database import get_db
from evaluation.evaluation_repository import EvaluationRepository
from evaluation.evaluation_service import EvaluationService
from evaluation.pipeline_orchestrator import EvaluationOrchestrator
from evaluation.workbench_analyzer import (
    compute_ai_health_score,
    generate_improvement_recommendations,
    production_readiness,
)

router = APIRouter(prefix=f"{API_PREFIX}/workbench", tags=["workbench"])


def _system_metrics() -> dict[str, Any]:
    try:
        import psutil

        proc = psutil.Process()
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.05),
            "memory_mb": round(proc.memory_info().rss / (1024 * 1024), 2),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage("/").percent
            if hasattr(psutil, "disk_usage")
            else None,
        }
    except ImportError:
        return {
            "cpu_percent": None,
            "memory_mb": None,
            "memory_percent": None,
            "disk_usage_percent": None,
        }


@router.get("/overview")
async def workbench_overview(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Landing dashboard aggregate: datasets, latest run, health, AI score."""
    repo = EvaluationRepository(db)
    service = EvaluationService(repo)
    orch = EvaluationOrchestrator()

    inventory = orch.discover()
    runs = await repo.list_runs(limit=1)
    latest = runs[0] if runs else None

    ai_health = {"score": 0, "rating": "N/A", "factors": {}}
    readiness = {"production_ready": False, "blockers": ["No evaluation run yet"]}
    overall_accuracy = 0.0
    overall_confidence = 0.0

    if latest and latest.report_json:
        ai_health = compute_ai_health_score(latest.report_json)
        readiness = production_readiness(latest.report_json)
        ds_results = latest.report_json.get("dataset_results", [])
        if ds_results:
            ai = ds_results[0].get("ai_evaluation", {})
            overall_accuracy = float(ai.get("accuracy") or 0)
            overall_confidence = float(ai.get("prediction_confidence") or 0)

    return {
        "total_datasets": len(inventory.get("bundles", [])),
        "stil_count": inventory.get("stil_count", 0),
        "log_count": inventory.get("log_count", 0),
        "tabular_count": inventory.get("tabular_count", 0),
        "current_dataset": (
            latest.report_json.get("dataset_results", [{}])[0]
            .get("dataset", {})
            .get("dataset_id")
            if latest and latest.report_json.get("dataset_results")
            else None
        ),
        "agent_status": "ready" if readiness.get("production_ready") else "needs_review",
        "ai_health_score": ai_health,
        "overall_accuracy": round(overall_accuracy, 4),
        "overall_confidence": round(overall_confidence, 4),
        "production_readiness": readiness,
        "latest_execution": {
            "execution_id": latest.id if latest else None,
            "processing_ms": latest.processing_ms if latest else None,
            "pass_count": latest.pass_count if latest else 0,
            "fail_count": latest.fail_count if latest else 0,
            "warning_count": latest.warning_count if latest else 0,
            "model_version": latest.model_version if latest else "",
            "created_at": latest.created_at.isoformat() if latest and latest.created_at else None,
        },
        "system_metrics": _system_metrics(),
        "database_health": "ok",
        "inventory_warnings": inventory.get("warnings", [])[:5],
    }


@router.get("/improvements")
async def workbench_improvements(
    execution_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = EvaluationRepository(db)
    run = await repo.get_latest_or(execution_id)
    if run is None:
        raise HTTPException(status_code=404, detail="No evaluation run found")
    report = run.report_json or {}
    return {
        "execution_id": run.id,
        "recommendations": generate_improvement_recommendations(report),
        "production_readiness": production_readiness(report),
        "ai_health_score": compute_ai_health_score(report),
    }


@router.get("/logs")
async def workbench_logs(
    execution_id: str | None = Query(None),
    module: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(500, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = EvaluationRepository(db)
    run = await repo.get_latest_or(execution_id)
    if run is None:
        raise HTTPException(status_code=404, detail="No evaluation run found")

    logs: list[dict[str, Any]] = []
    for ds in (run.report_json or {}).get("dataset_results", []):
        logs.extend(ds.get("execution_logs", []))

    if module:
        logs = [l for l in logs if l.get("module") == module]
    if status:
        logs = [l for l in logs if l.get("status") == status]
    return {"execution_id": run.id, "logs": logs[-limit:], "total": len(logs)}


@router.get("/visualizations")
async def workbench_visualizations(
    execution_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Extract visualization payloads from latest evaluation report."""
    repo = EvaluationRepository(db)
    run = await repo.get_latest_or(execution_id)
    if run is None:
        raise HTTPException(status_code=404, detail="No evaluation run found")

    report = run.report_json or {}
    viz: dict[str, Any] = {
        "charts": run.dashboard_json.get("charts", {}) if run.dashboard_json else {},
        "ai_metrics": run.dashboard_json.get("ai_metrics", []) if run.dashboard_json else [],
        "benchmark_stages": run.dashboard_json.get("benchmark_stages", []) if run.dashboard_json else [],
        "die_heatmap": None,
        "wafer_map": None,
        "correlation_matrix": None,
        "root_cause_predictions": [],
        "pattern_frequency": [],
    }

    for ds in report.get("dataset_results", []):
        modules = ds.get("module_outputs", {})
        raw = report.get("dataset_results", [{}])
        # Pull from nested reports stored during evaluation
        for key, mod_key, field in (
            ("die_heatmap", "FA-FR-007", "die_heatmap"),
            ("wafer_map", "FA-FR-008", "wafer_heatmap"),
        ):
            pass  # module_outputs strips full reports; use report_json paths below

    # Full reports are in dataset_results module_outputs stripped; re-read from report
    for ds in report.get("dataset_results", []):
        # Reports stored at orchestrator level aren't persisted separately;
        # use dashboard charts + validation metrics
        ai = ds.get("ai_evaluation", {})
        if ai.get("confusion_matrix"):
            viz["confusion_matrix"] = ai["confusion_matrix"]

    fr009 = None
    for ds in report.get("dataset_results", []):
        mod = ds.get("module_outputs", {}).get("FA-FR-009", {})
        if mod.get("total_predictions"):
            viz["root_cause_predictions"] = mod

    return {"execution_id": run.id, "visualizations": viz}


@router.get("/health")
async def workbench_health() -> dict[str, Any]:
    start = time.perf_counter()
    metrics = _system_metrics()
    return {
        "status": "ok",
        "service": "evaluation-workbench",
        "response_ms": round((time.perf_counter() - start) * 1000, 2),
        **metrics,
    }
