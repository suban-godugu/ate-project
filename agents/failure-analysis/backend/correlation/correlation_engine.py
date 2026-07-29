"""Main FA-FR-006 failure pattern correlation engine."""

from __future__ import annotations

import time
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from adapters.schema import TestRecord
from adapters.yaml_config import load_adapter_configs
from backend.correlation.graph_builder import build_relationship_graph
from backend.correlation.statistical_analysis import (
    build_feature_table,
    compute_correlation_matrix,
    dimension_correlations,
    mine_association_rules,
)
from backend.correlation.visualization import build_visualization
from ingestor import DieLog
from pattern_correlation import (
    calculate_pattern_level_failure_rates,
    correlate_failures_with_patterns,
)
from recurrence_detection import detect_recurrences

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "correlation.yaml"
WEIGHTS_PATH = Path(__file__).resolve().parents[2] / "config" / "correlation_weights.yaml"


class CorrelationEngine:
    """
    Failure pattern correlation pipeline:
    dataset → feature engineering → statistics → matrix → graph → insights
    """

    def __init__(self, *, config_path: Path | str | None = None) -> None:
        raw = load_adapter_configs(Path(config_path) if config_path else DEFAULT_CONFIG)
        self.correlation_threshold = float(raw.get("correlation_threshold", 0.35))
        self.high_risk_threshold = float(raw.get("high_risk_threshold", 0.75))
        self.min_support = float(raw.get("min_support", 0.05))
        self.min_confidence = float(raw.get("min_confidence", 0.60))
        self.dimensions = list(raw.get("dimensions", []))

    def analyze(
        self,
        *,
        die_logs: list[DieLog],
        test_records: list[TestRecord] | None = None,
        upload_id: str | None = None,
        top_n: int = 50,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        failure_rows = _extract_failure_rows(die_logs, test_records)
        feature_table = build_feature_table(failure_rows)

        recurring = detect_recurrences(die_logs, test_records=test_records)
        pattern_rates = calculate_pattern_level_failure_rates(die_logs)
        legacy = correlate_failures_with_patterns(
            die_logs,
            pattern_rates,
            test_records=test_records,
            recurring_failures=recurring,
            weights_path=WEIGHTS_PATH,
            top_n=top_n,
        )

        correlation_matrix = compute_correlation_matrix(
            feature_table,
            threshold=self.correlation_threshold,
        )
        dim_corr = dimension_correlations(
            feature_table,
            threshold=self.correlation_threshold,
        )
        correlation_matrix["dimension_scores"] = dim_corr

        association_rules = mine_association_rules(
            feature_table,
            min_support=self.min_support,
            min_confidence=self.min_confidence,
        )

        pattern_relationships = _pattern_relationships(
            legacy.get("correlation_report", []),
            failure_rows,
        )

        network = build_relationship_graph(
            correlation_matrix=correlation_matrix,
            association_rules=association_rules,
            pattern_relationships=pattern_relationships,
            dimension_correlations=dim_corr,
            threshold=self.correlation_threshold,
        )

        insights = _engineering_insights(
            legacy=legacy,
            dim_corr=dim_corr,
            association_rules=association_rules,
            pattern_relationships=pattern_relationships,
        )

        visualization = build_visualization(
            correlation_matrix=correlation_matrix,
            network=network,
            engineering_insights=insights,
        )

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "requirement": "FA-FR-006",
            "upload_id": upload_id,
            "processing_ms": elapsed_ms,
            "meets_performance_target": elapsed_ms < 10000,
            "correlation_threshold": self.correlation_threshold,
            "high_risk_threshold": self.high_risk_threshold,
            "dimensions_analyzed": self.dimensions,
            "detection_pipeline": [
                "feature_engineering",
                "statistical_analysis",
                "correlation_matrix",
                "relationship_graph",
                "engineering_insights",
            ],
            "statistical_methods": {
                "pearson": correlation_matrix.get("pearson", {}),
                "spearman": correlation_matrix.get("spearman", {}),
                "chi_square": correlation_matrix.get("chi_square", []),
                "association_rules": association_rules,
            },
            "correlation_matrix": correlation_matrix,
            "dimension_correlations": dim_corr,
            "correlation_report": legacy.get("correlation_report", []),
            "correlation_report_total": legacy.get("correlation_report_total", 0),
            "top_failing_patterns": legacy.get("top_failing_patterns", []),
            "pattern_relationships": pattern_relationships,
            "failure_dependency_graph": network,
            "engineering_insights": insights,
            "engineering_recommendations": legacy.get("engineering_recommendations", [])
            + insights,
            "downstream_export": legacy.get("downstream_export", {}),
            "visualization": visualization,
            "legacy_report": {
                "baseline_failure_rate": legacy.get("baseline_failure_rate"),
                "weights": legacy.get("weights"),
                "ranking_method": legacy.get("ranking_method"),
            },
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
        shift = _shift_bucket(die, rec)
        temperature = _param(rec, die, "THERMAL_C", "temperature")
        voltage = _param(rec, die, "IR_DROP_MV", "voltage")

        for pattern in die.failing_patterns:
            rows.append(
                {
                    "failure_id": str(uuid.uuid4()),
                    "pattern_id": pattern.pattern_id,
                    "lot_id": die.lot_id,
                    "wafer_id": die.wafer_id,
                    "die_id": die.die_id,
                    "tester_id": die.tester_name or (rec.tester_id if rec else "UNKNOWN"),
                    "product_id": (rec.product_id if rec else die.device_name) or "UNKNOWN",
                    "equipment_id": die.tester_name or (rec.tester_id if rec else "UNKNOWN"),
                    "machine_id": die.header_fields.get("MACHINE_ID", die.tester_name or "UNKNOWN"),
                    "operator_id": die.header_fields.get("OPERATOR_ID", "UNKNOWN"),
                    "process_step": (rec.test_stage if rec else die.header_fields.get("TEST_STAGE", "UNKNOWN")),
                    "shift": shift or "UNKNOWN",
                    "temperature": temperature,
                    "voltage": voltage,
                    "hard_bin": str(rec.hard_bin) if rec and rec.hard_bin else "",
                }
            )
    return rows


def _pattern_relationships(
    correlation_report: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_pattern: dict[str, list[dict[str, Any]]] = {}
    for row in failure_rows:
        by_pattern.setdefault(row["pattern_id"], []).append(row)

    relationships = []
    for item in correlation_report:
        pid = item["pattern_id"]
        rows = by_pattern.get(pid, [])
        testers = Counter(r["tester_id"] for r in rows)
        lots = Counter(r["lot_id"] for r in rows)
        products = Counter(r["product_id"] for r in rows)
        relationships.append(
            {
                "relationship_id": str(uuid.uuid4()),
                "pattern_id": pid,
                "correlation_score": item.get("correlation_score", 0.0),
                "status": item.get("status", "NORMAL"),
                "top_tester": testers.most_common(1)[0][0] if testers else None,
                "top_lot": lots.most_common(1)[0][0] if lots else None,
                "top_product": products.most_common(1)[0][0] if products else None,
                "related_patterns": [
                    other
                    for other in by_pattern
                    if other != pid and _patterns_co_occur(rows, by_pattern.get(other, []))
                ][:5],
            }
        )
    return relationships


def _patterns_co_occur(
    rows_a: list[dict[str, Any]],
    rows_b: list[dict[str, Any]],
) -> bool:
    dies_a = {(r["lot_id"], r["wafer_id"], r["die_id"]) for r in rows_a}
    dies_b = {(r["lot_id"], r["wafer_id"], r["die_id"]) for r in rows_b}
    return bool(dies_a & dies_b)


def _engineering_insights(
    *,
    legacy: dict[str, Any],
    dim_corr: dict[str, Any],
    association_rules: list[dict[str, Any]],
    pattern_relationships: list[dict[str, Any]],
) -> list[str]:
    insights = list(legacy.get("engineering_recommendations", []))
    if dim_corr:
        top_dim = max(dim_corr, key=lambda d: dim_corr[d]["correlation_score"])
        insights.append(
            f"Strongest manufacturing correlation: {top_dim} "
            f"(score={dim_corr[top_dim]['correlation_score']:.2f}, "
            f"method={dim_corr[top_dim]['method']})."
        )
    if association_rules:
        rule = association_rules[0]
        insights.append(
            f"Association rule: {rule['antecedent']} → {rule['consequent']} "
            f"(confidence={rule['confidence']:.2f}, lift={rule['lift']:.2f})."
        )
    high_risk = [p for p in pattern_relationships if p.get("status") == "HIGH_RISK"]
    if high_risk:
        insights.append(
            f"{len(high_risk)} pattern(s) show HIGH_RISK correlation with manufacturing variables."
        )
    return insights


def _shift_bucket(die: DieLog, rec: TestRecord | None) -> str:
    ts = rec.timestamp if rec and rec.timestamp else die.header_fields.get("TIMESTAMP", "")
    if not ts:
        return ""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(ts[:19], fmt)
            return f"{dt.date()} shift-{dt.hour // 8}"
        except ValueError:
            continue
    return ts[:10] if len(ts) >= 10 else ""


def _param(rec: TestRecord | None, die: DieLog, field: str, key: str) -> float:
    if rec:
        val = rec.parametric.get(key) or rec.parametric.get(field)
        if val is not None:
            try:
                return float(val)
            except (TypeError, ValueError):
                pass
    raw = die.header_fields.get(field, "")
    try:
        return float(raw or 0)
    except (TypeError, ValueError):
        return 0.0
