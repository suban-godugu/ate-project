"""Feature engineering for root cause prediction."""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from typing import Any

from adapters.schema import TestRecord
from fault_classifier import classify_fault_type
from ingestor import DieLog


FEATURE_NAMES = [
    "failure_count",
    "affected_dies",
    "affected_lots",
    "affected_wafers",
    "pattern_count",
    "avg_setup_slack",
    "avg_hold_slack",
    "avg_ir_drop",
    "avg_thermal",
    "avg_severity",
    "transition_faults",
    "recurring_lot_boost",
    "correlation_score",
    "hint_entropy",
    "fault_category_entropy",
]


def build_record_index(
    test_records: list[TestRecord] | None,
) -> dict[tuple[str, str, str], TestRecord]:
    index: dict[tuple[str, str, str], TestRecord] = {}
    for rec in test_records or []:
        index[(rec.lot_id, rec.wafer_id, rec.die_id)] = rec
    return index


def extract_cluster_contexts(
    die_logs: list[DieLog],
    *,
    test_records: list[TestRecord] | None = None,
    recurring: dict[str, Any] | None = None,
    correlation: dict[str, Any] | None = None,
    recurring_min_lots: int = 2,
) -> list[dict[str, Any]]:
    """Build per-scan-chain prediction contexts from failure data."""
    record_index = build_record_index(test_records)
    correlation_by_chain = _correlation_by_chain(correlation)
    recurring_patterns = _recurring_pattern_set(recurring)

    clusters: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "patterns": set(),
            "lots": set(),
            "wafers": set(),
            "dies": set(),
            "failure_count": 0,
            "hints": Counter(),
            "fault_categories": Counter(),
            "ir_drop_values": [],
            "thermal_values": [],
            "severity_scores": [],
            "setup_slack_values": [],
            "hold_slack_values": [],
            "transition_faults": 0,
            "evidence": [],
            "sample_patterns": [],
        }
    )

    for die in die_logs:
        for pattern in die.failing_patterns:
            chain_key = pattern.scan_chain_id or "UNKNOWN_CHAIN"
            cluster = clusters[chain_key]
            cluster["failure_count"] += 1
            cluster["patterns"].add(pattern.pattern_id)
            cluster["lots"].add(die.lot_id)
            cluster["wafers"].add(die.wafer_id)
            cluster["dies"].add(die.die_id)

            fields = pattern.raw_fields
            hint = str(fields.get("ROOT_CAUSE_HINT", "")).strip()
            if hint:
                cluster["hints"][hint] += 1
            cluster["fault_categories"][classify_fault_type(pattern, die=die)] += 1

            for key, bucket in (
                ("IR_DROP_MV", "ir_drop_values"),
                ("THERMAL_C", "thermal_values"),
                ("AI_SEVERITY_SCORE", "severity_scores"),
                ("SETUP_SLACK_PS", "setup_slack_values"),
                ("HOLD_SLACK_PS", "hold_slack_values"),
            ):
                val = _parse_numeric(fields.get(key))
                if val is not None:
                    cluster[bucket].append(val)

            transition = _parse_numeric(fields.get("TRANSITION_FAULTS"))
            if transition is not None:
                cluster["transition_faults"] += int(transition)

            if len(cluster["sample_patterns"]) < 3:
                rec = record_index.get((die.lot_id, die.wafer_id, die.die_id))
                cluster["sample_patterns"].append(
                    {
                        "lot_id": die.lot_id,
                        "wafer_id": die.wafer_id,
                        "die_id": die.die_id,
                        "pattern_id": pattern.pattern_id,
                        "FAIL_TYPE": fields.get("FAIL_TYPE", ""),
                        "ROOT_CAUSE_HINT": hint,
                        "failing_test": fields.get("failing_test", ""),
                        "hard_bin": rec.hard_bin if rec else "",
                    }
                )

    contexts: list[dict[str, Any]] = []
    for chain_id, cluster in clusters.items():
        lot_count = len(cluster["lots"])
        is_recurring = lot_count >= recurring_min_lots or any(
            p in recurring_patterns for p in cluster["patterns"]
        )
        corr_score = correlation_by_chain.get(chain_id, 0.0)

        primary_hint = (
            cluster["hints"].most_common(1)[0][0] if cluster["hints"] else ""
        )
        primary_fault = (
            cluster["fault_categories"].most_common(1)[0][0]
            if cluster["fault_categories"]
            else "Unknown Failure"
        )

        ctx = {
            "scan_chain_id": chain_id,
            "failure_count": cluster["failure_count"],
            "affected_dies": len(cluster["dies"]),
            "affected_lots": lot_count,
            "affected_wafers": len(cluster["wafers"]),
            "pattern_count": len(cluster["patterns"]),
            "patterns": sorted(cluster["patterns"]),
            "primary_hint": primary_hint,
            "primary_fault_category": primary_fault,
            "hints": dict(cluster["hints"]),
            "fault_categories": dict(cluster["fault_categories"]),
            "is_recurring": is_recurring,
            "correlation_score": corr_score,
            "sample_patterns": cluster["sample_patterns"],
            "semantic_query": _build_semantic_query(chain_id, cluster),
            "features": feature_vector_from_cluster(cluster, is_recurring, corr_score),
            "feature_names": FEATURE_NAMES,
        }
        contexts.append(ctx)

    contexts.sort(key=lambda c: (c["failure_count"], c["correlation_score"]), reverse=True)
    return contexts


def feature_vector_from_cluster(
    cluster: dict[str, Any],
    is_recurring: bool,
    correlation_score: float,
) -> list[float]:
    def avg(key: str) -> float:
        vals = cluster.get(key, [])
        return sum(vals) / len(vals) if vals else 0.0

    return [
        float(cluster["failure_count"]),
        float(len(cluster["dies"])),
        float(len(cluster["lots"])),
        float(len(cluster["wafers"])),
        float(len(cluster["patterns"])),
        avg("setup_slack_values"),
        avg("hold_slack_values"),
        avg("ir_drop_values"),
        avg("thermal_values"),
        avg("severity_scores"),
        float(cluster["transition_faults"]),
        1.0 if is_recurring else 0.0,
        float(correlation_score),
        _entropy(cluster["hints"]),
        _entropy(cluster["fault_categories"]),
    ]


def labeled_training_samples(
    contexts: list[dict[str, Any]],
) -> list[tuple[list[float], str, dict[str, Any]]]:
    """Build ML training labels from hint/fault category consensus."""
    labeled: list[tuple[list[float], str, dict[str, Any]]] = []
    for ctx in contexts:
        label = ctx["primary_hint"] or ctx["primary_fault_category"]
        if label and label not in ("UNKNOWN", "Unknown Failure"):
            labeled.append((ctx["features"], label, ctx))
    return labeled


def _build_semantic_query(chain_id: str, cluster: dict[str, Any]) -> str:
    parts = [
        f"scan_chain {chain_id}",
        f"failures {cluster['failure_count']}",
    ]
    if cluster["hints"]:
        parts.append("hints " + " ".join(cluster["hints"].keys()))
    if cluster["fault_categories"]:
        parts.append("categories " + " ".join(cluster["fault_categories"].keys()))
    if cluster["setup_slack_values"]:
        parts.append("setup_slack")
    if cluster["ir_drop_values"]:
        parts.append("IR_DROP")
    if cluster["thermal_values"]:
        parts.append("THERMAL")
    if cluster["transition_faults"]:
        parts.append("transition_faults")
    return " ".join(parts)


def _correlation_by_chain(correlation: dict[str, Any] | None) -> dict[str, float]:
    scores: dict[str, float] = {}
    for row in (correlation or {}).get("correlation_report", []):
        chain = str(row.get("scan_chain_id", row.get("pattern_id", "")))
        if chain:
            scores[chain] = max(scores.get(chain, 0.0), float(row.get("correlation_score", 0.0)))
    return scores


def _recurring_pattern_set(recurring: dict[str, Any] | None) -> set[str]:
    patterns: set[str] = set()
    for row in (recurring or {}).get("recurring_failures", []):
        pid = row.get("pattern_id")
        if pid:
            patterns.add(str(pid))
    return patterns


def _entropy(counter: Counter) -> float:
    total = sum(counter.values())
    if total == 0:
        return 0.0
    import math

    ent = 0.0
    for count in counter.values():
        p = count / total
        ent -= p * math.log2(p)
    return round(ent, 6)


def _parse_numeric(value: str | float | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def signature_hash(ctx: dict[str, Any]) -> str:
    raw = ctx.get("semantic_query", "") + str(ctx.get("primary_hint", ""))
    return hashlib.md5(raw.encode()).hexdigest()[:12]
