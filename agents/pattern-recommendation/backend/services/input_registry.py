"""
Required Pattern Recommendation Agent inputs.

Inputs live under:
  C:\\personal\\input all file\\pattern-recommendation
Outputs (including generated failure_summary.json) live under:
  C:\\personal\\agent and parser output\\pattern-recommendation

Required input roles (filename markers):
  1. executions  → PA-Analysis-Session_executions.json  (marker: execution)
  2. clustering  → PA-Analysis-Session_clustering.json  (marker: clustering)
  3. embeddings  → PA-Analysis-Session_embeddings.json  (marker: embedding)
  4. cpm         → PA-FR-*_cpm_report.json              (marker: cpm_report)
  5. cvm         → PA-FR-*_cvm_cycles.csv               (marker: cvm_cycles)
  6. metadata    → PA-FR-*_metadata_metrics.json        (marker: metadata_metrics)

Generated output:
  failure_summary.json  (built from executions on connect if missing)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import ijson

from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.services.coverage_service import reset_coverage_service
from backend.services.data_loader import get_data_loader, reset_data_loader
from backend.services.dataset_service import get_dataset_service, reset_dataset_service
from backend.services.failure_service import get_failure_service, reset_failure_service
from backend.services.gap_analysis_service import reset_gap_analysis_service
from backend.services.low_power_service import reset_low_power_service
from backend.services.ordering_service import reset_ordering_service
from backend.services.pattern_feature_builder import (
    get_pattern_feature_builder,
    reset_pattern_feature_builder,
)
from backend.services.recommendation_orchestrator import (
    get_recommendation_orchestrator,
    reset_recommendation_orchestrator,
)
from backend.services.redundancy_service import reset_redundancy_service
from backend.services.removal_service import reset_removal_service

# role_id -> (label, filename marker substring, required)
REQUIRED_ROLES: list[tuple[str, str, str, bool]] = [
    ("executions", "Executions", "execution", True),
    ("clustering", "Clustering", "clustering", True),
    ("embeddings", "Embeddings", "embedding", True),
    ("cpm", "CPM report", "cpm_report", True),
    ("cvm", "CVM cycles", "cvm_cycles", True),
    ("metadata", "Metadata metrics", "metadata_metrics", True),
]


def _file_meta(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"path": None, "exists": False, "size_bytes": 0, "mtime": None}
    exists = path.is_file()
    return {
        "path": str(path),
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else 0,
        "mtime": path.stat().st_mtime if exists else None,
    }


def _find_by_marker(root: Path, marker: str) -> Path | None:
    if not root.is_dir():
        return None
    marker_l = marker.lower()
    candidates = [
        p for p in root.iterdir() if p.is_file() and marker_l in p.name.lower()
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda p: (0 if marker_l in p.stem.lower() else 1, p.name))
    return candidates[0]


def input_inventory(settings: Settings | None = None) -> dict[str, Any]:
    cfg = settings or get_settings()
    data_dir = Path(cfg.data_dir)
    output_dir = Path(cfg.output_dir)

    inputs: list[dict[str, Any]] = []
    for role_id, label, marker, required in REQUIRED_ROLES:
        path = _find_by_marker(data_dir, marker)
        meta = _file_meta(path)
        inputs.append(
            {
                "id": role_id,
                "label": label,
                "pattern": f"*{marker}*",
                "required": required,
                **meta,
            }
        )

    failure_summary = output_dir / "failure_summary.json"
    missing = [item["id"] for item in inputs if item["required"] and not item["exists"]]
    ready = len(missing) == 0

    return {
        "data_dir": str(data_dir),
        "output_dir": str(output_dir),
        "ready": ready,
        "missing": missing,
        "inputs": inputs,
        "failure_summary": {
            "id": "failure_summary",
            "label": "Failure summary (generated)",
            "pattern": "failure_summary.json",
            "required": False,
            **_file_meta(failure_summary),
        },
    }


def _severity(coverage_percent: float) -> str:
    if coverage_percent >= 70.0:
        return "HIGH"
    if coverage_percent >= 30.0:
        return "MEDIUM"
    return "LOW"


def build_failure_summary_from_executions(
    executions_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    """
    Aggregate FAIL executions into failure_summary.json so recommendation
    engines have the expected contract when raw ATE logs are absent.
    """
    logger = get_logger()
    logger.info("Building failure_summary from executions path=%s", executions_path)

    by_pattern: dict[str, dict[str, Any]] = {}
    total_logs: set[str] = set()
    failed_logs: set[str] = set()
    total_lots: set[str] = set()

    with executions_path.open("rb") as handle:
        for item in ijson.items(handle, "executions.item"):
            if not isinstance(item, dict):
                continue
            pattern_id = str(item.get("pattern_id") or "").strip()
            source_log = str(
                item.get("source_log") or item.get("source_log_relpath") or ""
            )
            lot = ""
            rel = str(item.get("source_log_relpath") or "")
            if "/" in rel or "\\" in rel:
                parts = rel.replace("\\", "/").split("/")
                if len(parts) >= 2:
                    lot = parts[-2]
            result = str(item.get("latest_result") or "").upper()
            if source_log:
                total_logs.add(source_log)
            if lot:
                total_lots.add(lot)
            if result != "FAIL" or not pattern_id:
                continue
            if source_log:
                failed_logs.add(source_log)
            bucket = by_pattern.setdefault(
                pattern_id,
                {"fail_count": 0, "logs": set(), "lots": set()},
            )
            bucket["fail_count"] += 1
            if source_log:
                bucket["logs"].add(source_log)
            if lot:
                bucket["lots"].add(lot)

    failed_log_count = max(len(failed_logs), 1)
    patterns: list[dict[str, Any]] = []
    for pattern_id, bucket in by_pattern.items():
        coverage = (len(bucket["logs"]) / failed_log_count) * 100.0
        patterns.append(
            {
                "pattern_id": pattern_id,
                "failed_logs": int(bucket["fail_count"]),
                "coverage_percent": round(coverage, 4),
                "severity": _severity(coverage),
                "affected_lots": sorted(bucket["lots"]),
                "failing_logs": sorted(bucket["logs"]),
            }
        )

    patterns.sort(
        key=lambda p: (-p["coverage_percent"], -p["failed_logs"], p["pattern_id"])
    )
    for rank, row in enumerate(patterns, start=1):
        row["rank"] = rank

    payload = {
        "summary": {
            "total_logs": len(total_logs),
            "failed_logs": len(failed_logs),
            "good_logs": max(len(total_logs) - len(failed_logs), 0),
            "unique_patterns": len(patterns),
            "total_pattern_occurrences": sum(p["failed_logs"] for p in patterns),
            "total_lots": len(total_lots) if total_lots else None,
            "source": "derived_from_executions",
        },
        "patterns": patterns,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    logger.info(
        "Wrote failure_summary patterns=%d path=%s",
        len(patterns),
        output_path,
    )
    return payload


def _reset_all_services() -> None:
    reset_recommendation_orchestrator()
    reset_coverage_service()
    reset_low_power_service()
    reset_gap_analysis_service()
    reset_ordering_service()
    reset_removal_service()
    reset_redundancy_service()
    reset_pattern_feature_builder()
    reset_failure_service()
    reset_data_loader()
    reset_dataset_service()


def connect_inputs(settings: Settings | None = None) -> dict[str, Any]:
    """Validate inputs, build failure_summary if needed, refresh registries."""
    cfg = settings or get_settings()
    inventory = input_inventory(cfg)
    if not inventory["ready"]:
        return {
            "status": "missing_inputs",
            "message": (
                "Required Pattern Recommendation inputs are missing — place "
                "PA-Analysis-Session_* / PA-FR-* files under "
                f"{inventory['data_dir']}"
            ),
            **inventory,
        }

    data_dir = Path(cfg.data_dir)
    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    executions = _find_by_marker(data_dir, "execution")
    failure_path = output_dir / "failure_summary.json"
    built_summary = False
    if executions and (not failure_path.is_file() or failure_path.stat().st_size < 32):
        build_failure_summary_from_executions(executions, failure_path)
        built_summary = True

    _reset_all_services()

    dataset_service = get_dataset_service(cfg)
    dataset_list = dataset_service.refresh()
    data_loader = get_data_loader(cfg, dataset_service)
    data_loader.clear_cache()

    failure_service = get_failure_service(data_loader)
    failure_payload = failure_service.refresh()

    feature_builder = get_pattern_feature_builder(data_loader)
    feature_stats = feature_builder.refresh()

    orchestrator = get_recommendation_orchestrator(settings=cfg)
    dashboard = orchestrator.refresh()

    refreshed = input_inventory(cfg)
    return {
        "status": "connected",
        "message": "Pattern Recommendation inputs connected",
        "built_failure_summary": built_summary,
        "datasets_available": sum(
            1 for d in dataset_list.datasets if d.status == "available"
        ),
        "datasets_total": dataset_list.total,
        "failure_patterns": len(getattr(failure_payload, "patterns", []) or []),
        "pattern_features": getattr(feature_stats, "total", None),
        "dashboard_ready": bool(dashboard),
        **refreshed,
    }
