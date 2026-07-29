"""Main FA-FR-005 recurring failure detection engine."""

from __future__ import annotations

import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from adapters.schema import TestRecord
from adapters.yaml_config import load_adapter_configs
from backend.recurring.clustering import cluster_recurring_failures
from backend.recurring.frequency_analysis import (
    aggregate_failure_statistics,
    analyze_correlations,
    build_frequency_distribution,
    impacted_lots,
)
from backend.recurring.similarity_analysis import analyze_similarity, merge_similar_events
from ingestor import DieLog
from recurrence_detection import detect_recurrences

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "recurring.yaml"
DEFAULT_MANIFEST = Path(__file__).resolve().parents[2] / "config" / "recurrence_manifest.yaml"


class RecurringEngine:
    """
    Recurring failure detection pipeline:
    failure dataset → aggregate → frequency → similarity → temporal → identify
    """

    def __init__(self, *, config_path: Path | str | None = None) -> None:
        raw = load_adapter_configs(Path(config_path) if config_path else DEFAULT_CONFIG)
        defaults = dict(raw.get("defaults", {}))
        self.min_entities = int(defaults.get("min_entities", 3))
        self.failure_share_threshold = float(defaults.get("failure_share_threshold", 0.40))
        self.similarity_threshold = float(defaults.get("similarity_threshold", 0.75))
        self.dbscan_eps = float(defaults.get("dbscan_eps", 0.45))
        self.min_cluster_size = int(defaults.get("min_cluster_size", 2))
        self.manifest_path = DEFAULT_MANIFEST

    def analyze(
        self,
        *,
        die_logs: list[DieLog],
        test_records: list[TestRecord] | None = None,
        upload_id: str | None = None,
        historical_runs: list[dict[str, Any]] | None = None,
        incremental: bool = False,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        failure_rows = _extract_failure_rows(die_logs, test_records)

        legacy = detect_recurrences(
            die_logs,
            test_records=test_records,
            manifest_path=self.manifest_path,
        )

        aggregate_stats = aggregate_failure_statistics(failure_rows)
        frequency_distribution = build_frequency_distribution(failure_rows)
        similarity_report = analyze_similarity(
            failure_rows, threshold=self.similarity_threshold
        )
        cluster_report = cluster_recurring_failures(
            failure_rows,
            eps=self.dbscan_eps,
            min_samples=self.min_cluster_size,
        )

        deduped_events = merge_similar_events(
            legacy.get("recurrence_events", []),
            similarity_report,
        )
        correlations = analyze_correlations(
            failure_rows,
            deduped_events,
            min_entities=self.min_entities,
        )
        severity_ranking = _severity_ranking(deduped_events)
        trend_analysis = _temporal_trend_analysis(failure_rows, deduped_events)
        lots_impacted = impacted_lots(deduped_events)
        alerts = _engineering_alerts(deduped_events, lots_impacted)
        recurring_list = _build_recurring_list(deduped_events)

        if incremental and historical_runs:
            recurring_list, deduped_events = _merge_historical(
                recurring_list, deduped_events, historical_runs
            )

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        dashboard = _build_dashboard(
            recurring_list=recurring_list,
            frequency_distribution=frequency_distribution,
            severity_ranking=severity_ranking,
            trend_analysis=trend_analysis,
            lots_impacted=lots_impacted,
            alerts=alerts,
            correlations=correlations,
        )

        return {
            "requirement": "FA-FR-005",
            "upload_id": upload_id,
            "processing_ms": elapsed_ms,
            "meets_performance_target": elapsed_ms < 5000,
            "incremental": incremental,
            "thresholds": {
                "min_entities": self.min_entities,
                "failure_share_threshold": self.failure_share_threshold,
                "similarity_threshold": self.similarity_threshold,
            },
            "detection_pipeline": [
                "aggregate_statistics",
                "frequency_analysis",
                "similarity_detection",
                "temporal_analysis",
                "recurring_failure_identification",
            ],
            "aggregate_statistics": aggregate_stats,
            "correlations": correlations,
            "frequency_distribution": frequency_distribution,
            "similarity_report": similarity_report,
            "cluster_report": cluster_report,
            "recurrence_events": deduped_events,
            "recurring_failure_list": recurring_list,
            "severity_ranking": severity_ranking,
            "trend_analysis": trend_analysis,
            "impacted_lots": lots_impacted,
            "engineering_alerts": alerts,
            "entity_index": legacy.get("entity_index", {}),
            "classification_summary": {
                "total_recurring_signatures": len(recurring_list),
                "total_failure_occurrences": aggregate_stats["total_failures"],
                "impacted_lot_count": len(lots_impacted),
                "alert_count": len(alerts),
                "cluster_count": cluster_report.get("cluster_count", 0),
            },
            "legacy_report": {
                "recurring_definition": legacy.get("recurring_definition"),
                "signature_summary": legacy.get("signature_summary", {}),
                "recurring_failures": legacy.get("recurring_failures", []),
            },
            "dashboard": dashboard,
        }


def _extract_failure_rows(
    die_logs: list[DieLog],
    test_records: list[TestRecord] | None,
) -> list[dict[str, Any]]:
    record_index: dict[tuple[str, str, str], TestRecord] = {}
    if test_records:
        for rec in test_records:
            record_index[(rec.lot_id, rec.wafer_id, rec.die_id)] = rec

    rows: list[dict[str, Any]] = []
    for die in die_logs:
        if not die.is_failing_die:
            continue
        rec = record_index.get((die.lot_id, die.wafer_id, die.die_id))
        time_window = _shift_bucket(die, rec)
        for pattern in die.failing_patterns:
            rows.append(
                {
                    "failure_id": str(uuid.uuid4()),
                    "lot_id": die.lot_id,
                    "wafer_id": die.wafer_id,
                    "die_id": die.die_id,
                    "pattern_id": pattern.pattern_id,
                    "device_id": die.device_name or (rec.product_id if rec else "UNKNOWN"),
                    "product_id": (rec.product_id if rec else die.device_name) or "UNKNOWN",
                    "tester_id": die.tester_name or (rec.tester_id if rec else "UNKNOWN"),
                    "hard_bin": str(rec.hard_bin) if rec and rec.hard_bin else "",
                    "time_window": time_window,
                    "timestamp": rec.timestamp if rec else die.header_fields.get("TIMESTAMP", ""),
                }
            )
    return rows


def _severity_ranking(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = []
    for event in events:
        severity_score = round(
            0.4 * float(event.get("confidence", 0))
            + 0.3 * min(1.0, int(event.get("entity_count", 0)) / 5)
            + 0.3 * min(1.0, int(event.get("failure_count", 0)) / 20),
            4,
        )
        ranked.append(
            {
                "recurrence_id": str(uuid.uuid4()),
                "signature_type": event.get("signature_type"),
                "entity_key": event.get("entity_key"),
                "severity_score": severity_score,
                "confidence": event.get("confidence"),
                "failure_count": event.get("failure_count"),
                "entity_count": event.get("entity_count"),
                "recommendation": event.get("recommendation", ""),
            }
        )
    ranked.sort(key=lambda r: r["severity_score"], reverse=True)
    for idx, row in enumerate(ranked, start=1):
        row["rank"] = idx
    return ranked


def _temporal_trend_analysis(
    failure_rows: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    windows: dict[str, int] = {}
    for row in failure_rows:
        window = row.get("time_window") or "unknown"
        windows[window] = windows.get(window, 0) + 1

    time_series = [
        {"window": w, "failure_count": c}
        for w, c in sorted(windows.items())
    ]
    temporal_events = [
        e for e in events if e.get("signature_type") == "temporal_recurrence"
    ]
    direction = "stable"
    if len(time_series) >= 2:
        first, last = time_series[0]["failure_count"], time_series[-1]["failure_count"]
        if last > first * 1.2:
            direction = "worsening"
        elif last < first * 0.8:
            direction = "improving"

    return {
        "time_series": time_series,
        "temporal_recurrence_count": len(temporal_events),
        "trend_direction": direction,
    }


def _engineering_alerts(
    events: list[dict[str, Any]],
    lots: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    for event in events[:20]:
        if float(event.get("confidence", 0)) < 0.6:
            continue
        alerts.append(
            {
                "alert_id": str(uuid.uuid4()),
                "severity": "high" if float(event.get("confidence", 0)) >= 0.85 else "medium",
                "signature_type": event.get("signature_type"),
                "entity_key": event.get("entity_key"),
                "message": (
                    f"Recurring {event.get('signature_type')} detected for "
                    f"{event.get('entity_key')} across {event.get('entity_count')} entities"
                ),
                "recommendation": event.get("recommendation", ""),
                "confidence": event.get("confidence"),
            }
        )
    for lot in lots[:5]:
        if lot["recurrence_count"] >= 2:
            alerts.append(
                {
                    "alert_id": str(uuid.uuid4()),
                    "severity": "high",
                    "signature_type": "lot_impact",
                    "entity_key": lot["lot_id"],
                    "message": (
                        f"Lot {lot['lot_id']} impacted by {lot['recurrence_count']} "
                        "recurring signatures"
                    ),
                    "recommendation": "Prioritize lot-level FA review and hold disposition.",
                    "confidence": 0.9,
                }
            )
    return alerts


def _build_recurring_list(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for event in events:
        rows.append(
            {
                "recurrence_id": str(uuid.uuid4()),
                "signature_type": event.get("signature_type"),
                "entity_key": event.get("entity_key"),
                "scope": event.get("scope"),
                "failure_count": event.get("failure_count"),
                "entity_count": event.get("entity_count"),
                "confidence": event.get("confidence"),
                "is_recurring": event.get("is_recurring", True),
                "impacted_lots": event.get("lot_keys", event.get("affected_lots", [])),
                "recommendation": event.get("recommendation", ""),
            }
        )
    return rows


def _build_dashboard(
    *,
    recurring_list: list[dict[str, Any]],
    frequency_distribution: list[dict[str, Any]],
    severity_ranking: list[dict[str, Any]],
    trend_analysis: dict[str, Any],
    lots_impacted: list[dict[str, Any]],
    alerts: list[dict[str, Any]],
    correlations: dict[str, Any],
) -> dict[str, Any]:
    return {
        "recurring_failure_list": recurring_list[:25],
        "frequency_distribution": frequency_distribution[:25],
        "severity_ranking": severity_ranking[:15],
        "trend_analysis": trend_analysis,
        "impacted_lots": lots_impacted[:15],
        "engineering_alerts": alerts[:15],
        "correlation_summary": correlations,
        "plotly_ready": {
            "frequency_bar": {
                "x": [p["pattern_id"] for p in frequency_distribution[:15]],
                "y": [p["count"] for p in frequency_distribution[:15]],
                "type": "bar",
            },
            "trend_line": {
                "x": [p["window"] for p in trend_analysis.get("time_series", [])],
                "y": [p["failure_count"] for p in trend_analysis.get("time_series", [])],
                "type": "scatter",
                "mode": "lines+markers",
            },
        },
    }


def _merge_historical(
    recurring_list: list[dict[str, Any]],
    events: list[dict[str, Any]],
    historical_runs: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    seen = {
        f"{r.get('signature_type')}::{r.get('entity_key')}" for r in recurring_list
    }
    for run in historical_runs:
        for row in run.get("recurring_failure_list", []):
            key = f"{row.get('signature_type')}::{row.get('entity_key')}"
            if key not in seen:
                recurring_list.append(row)
                seen.add(key)
    return recurring_list, events


def _shift_bucket(die: DieLog, rec: TestRecord | None) -> str:
    ts = rec.timestamp if rec and rec.timestamp else die.header_fields.get("TIMESTAMP", "")
    if not ts:
        return ""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(ts[:19], fmt)
            shift_index = dt.hour // 8
            return f"{dt.date()} shift-{shift_index}"
        except ValueError:
            continue
    return ts[:10] if len(ts) >= 10 else ""
