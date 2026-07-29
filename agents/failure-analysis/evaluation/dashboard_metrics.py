"""Normalize dashboard KPI metrics and chart payloads from pipeline module outputs."""

from __future__ import annotations

from collections import Counter
from typing import Any


def _num(value: Any, fallback: float = 0.0) -> float:
    try:
        n = float(value)
        return n if n == n else fallback
    except (TypeError, ValueError):
        return fallback


def _int(value: Any, fallback: int = 0) -> int:
    return int(_num(value, fallback))


def _category_count(payload: Any) -> int:
    if isinstance(payload, dict):
        return _int(payload.get("count"))
    return _int(payload)


def _append_spatial_cell(
    cells: list[dict[str, Any]],
    cell: dict[str, Any],
    *,
    id_key: str,
    limit: int = 500,
) -> None:
    if len(cells) >= limit:
        return
    x = cell.get("x")
    y = cell.get("y")
    if x is None or y is None:
        return
    cells.append(
        {
            "x": _num(x),
            "y": _num(y),
            "intensity": _num(
                cell.get("intensity")
                or cell.get("failure_density")
                or cell.get("density")
                or cell.get("failure_rate")
                or cell.get("value")
                or (1 if cell.get("is_failing") or cell.get("is_failing_die") else 0)
            ),
            id_key: str(cell.get(id_key) or cell.get("die_id") or cell.get("wafer_id") or ""),
        }
    )


def _extract_die_cells(die: dict[str, Any]) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []

    die_feed = die.get("die_heatmap") or die.get("heatmap")
    if isinstance(die_feed, dict):
        inner = die_feed.get("die_heatmap")
        if isinstance(inner, dict):
            for bucket in (inner.get("failing_dies") or [], inner.get("passing_dies") or []):
                for cell in bucket:
                    _append_spatial_cell(cells, cell, id_key="die_id")
        grid = die_feed.get("failure_density_map", {}).get("grid") or []
        for cell in grid:
            _append_spatial_cell(cells, cell, id_key="die_id")
    elif isinstance(die_feed, list):
        for cell in die_feed:
            _append_spatial_cell(cells, cell, id_key="die_id")

    for profile in die.get("die_profiles") or die.get("dashboard_feed") or []:
        _append_spatial_cell(cells, profile, id_key="die_id")

    for handoff in die.get("spatial_ai_handoff") or []:
        _append_spatial_cell(cells, handoff, id_key="die_id")

    for cell in die.get("dies") or []:
        _append_spatial_cell(cells, cell, id_key="die_id")

    return cells


def _extract_wafer_cells(wafer: dict[str, Any]) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []

    spatial = (
        wafer.get("spatial_map")
        or (wafer.get("legacy_report") or {}).get("spatial_map")
        or wafer.get("dashboard_feed")
        or []
    )
    if isinstance(spatial, list):
        for cell in spatial:
            _append_spatial_cell(cells, cell, id_key="wafer_id")

    wafer_feed = wafer.get("wafer_heatmap") or wafer.get("heatmap")
    if isinstance(wafer_feed, dict):
        for wafer_map in wafer_feed.get("wafer_maps") or []:
            wafer_id = wafer_map.get("wafer_id", "")
            for bucket in (wafer_map.get("fail_dies") or [], wafer_map.get("pass_dies") or []):
                for cell in bucket:
                    enriched = {**cell, "wafer_id": cell.get("wafer_id") or wafer_id}
                    _append_spatial_cell(cells, enriched, id_key="wafer_id")
            for cell in wafer_map.get("density_grid") or []:
                enriched = {**cell, "wafer_id": wafer_id}
                _append_spatial_cell(cells, enriched, id_key="wafer_id")
    elif isinstance(wafer_feed, list):
        for cell in wafer_feed:
            _append_spatial_cell(cells, cell, id_key="wafer_id")

    return cells


def _build_category_distribution(
    classification: dict[str, Any],
    detection: dict[str, Any],
) -> list[dict[str, Any]]:
    category_distribution: list[dict[str, Any]] = []
    summary = classification.get("category_summary") or {}
    if isinstance(summary, dict):
        for category, payload in summary.items():
            count = _category_count(payload)
            if count > 0:
                category_distribution.append({"category": str(category), "count": count})

    if category_distribution:
        return category_distribution

    pattern_counts: Counter[str] = Counter()
    for pattern in detection.get("patterns") or []:
        label = (
            pattern.get("pattern_category")
            or pattern.get("fault_category")
            or pattern.get("pattern_name")
            or pattern.get("pattern_id")
        )
        if not label:
            continue
        pattern_counts[str(label)] += _int(
            pattern.get("failure_count") or pattern.get("pattern_frequency") or 1
        )

    return [
        {"category": category, "count": count}
        for category, count in pattern_counts.most_common(20)
        if count > 0
    ]


def normalize_dashboard_metrics(
    raw: dict[str, Any],
    *,
    imported_files: int = 0,
    processing_ms: float = 0.0,
    rates: dict[str, Any] | None = None,
    detection: dict[str, Any] | None = None,
) -> dict[str, float | int]:
    """Map internal pipeline keys to dashboard API contract."""
    total_tests = 0
    total_passed = 0
    total_failed = 0

    rows = (rates or {}).get("metrics") or (rates or {}).get("rates") or []
    for row in rows:
        level = str(row.get("aggregation_level") or "").lower()
        if "device" in level or "overall" in level or not total_tests:
            total_tests = _int(row.get("total_tests"), total_tests)
            total_passed = _int(row.get("pass_count"), total_passed)
            total_failed = _int(row.get("fail_count"), total_failed)

    if not total_tests and detection:
        total_tests = _int(detection.get("source_record_count"))

    return {
        "imported_test_files": _int(
            raw.get("imported_test_files") or raw.get("imported_files") or imported_files
        ),
        "overall_failure_rate": _num(raw.get("overall_failure_rate")),
        "ai_detection_accuracy": _num(raw.get("ai_detection_accuracy")),
        "failing_test_patterns": _int(
            raw.get("failing_test_patterns") or raw.get("failing_patterns")
        ),
        "die_failure_rate": _num(raw.get("die_failure_rate")),
        "wafer_failure_rate": _num(raw.get("wafer_failure_rate")),
        "lot_failure_rate": _num(raw.get("lot_failure_rate")),
        "fault_categories": _int(raw.get("fault_categories")),
        "root_cause_confidence": _num(raw.get("root_cause_confidence")),
        "recurring_failures": _int(raw.get("recurring_failures")),
        "failure_correlations": _int(raw.get("failure_correlations")),
        "failure_reports": _int(
            raw.get("failure_reports") or raw.get("reports_generated")
        ),
        "processing_time": round(_num(raw.get("processing_time") or processing_ms), 2),
        "total_tests": total_tests,
        "total_failed": total_failed,
        "total_passed": total_passed,
    }


def extract_dashboard_charts(module_outputs: dict[str, Any]) -> dict[str, Any]:
    """Build Recharts-ready chart datasets from FA-FR module responses."""
    detection = module_outputs.get("FA-FR-002") or {}
    rates = module_outputs.get("FA-FR-003") or {}
    classification = module_outputs.get("FA-FR-004") or {}
    correlation = module_outputs.get("FA-FR-006") or {}
    die = module_outputs.get("FA-FR-007") or {}
    wafer = module_outputs.get("FA-FR-008") or {}

    failure_trend: list[dict[str, Any]] = []
    for row in (rates.get("metrics") or rates.get("rates") or [])[:24]:
        label = (
            row.get("aggregation_key")
            or row.get("pattern_id")
            or row.get("aggregation_level")
            or "—"
        )
        failure_trend.append(
            {
                "label": str(label),
                "rate": round(_num(row.get("failure_percentage")), 4),
                "level": str(row.get("aggregation_level") or ""),
            }
        )

    failure_distribution: list[dict[str, Any]] = []
    for pattern in (detection.get("patterns") or [])[:20]:
        failure_distribution.append(
            {
                "name": str(
                    pattern.get("pattern_name") or pattern.get("pattern_id") or "unknown"
                ),
                "count": _int(pattern.get("failure_count") or pattern.get("pattern_frequency")),
            }
        )

    category_distribution = _build_category_distribution(classification, detection)

    pass_vs_fail: list[dict[str, Any]] = []
    for row in rows if (rows := (rates.get("metrics") or rates.get("rates") or [])) else []:
        level = str(row.get("aggregation_level") or "").lower()
        if "device" in level or "overall" in level or len(pass_vs_fail) == 0:
            pass_vs_fail = [
                {"name": "Passed", "value": _int(row.get("pass_count"))},
                {"name": "Failed", "value": _int(row.get("fail_count"))},
            ]
            if "device" in level or "overall" in level:
                break

    die_cells = _extract_die_cells(die)
    wafer_cells = _extract_wafer_cells(wafer)

    correlation_graph: dict[str, Any] = {}
    if correlation.get("relationship_graph"):
        correlation_graph = correlation["relationship_graph"]
    elif correlation.get("matrix"):
        correlation_graph = correlation["matrix"]
    elif correlation.get("correlations"):
        correlation_graph = {
            "nodes": [
                {
                    "id": f"{c.get('pattern_id')}|{c.get('fault_type')}",
                    "label": str(c.get("pattern_id") or ""),
                    "weight": _num(c.get("correlation_coefficient")),
                }
                for c in correlation.get("correlations", [])[:40]
            ],
            "edges": [],
        }

    return {
        "failure_trend": failure_trend,
        "failure_distribution": failure_distribution,
        "category_distribution": category_distribution,
        "pass_vs_fail": pass_vs_fail,
        "wafer_heatmap": wafer_cells,
        "die_heatmap": die_cells,
        "correlation_graph": correlation_graph,
    }
