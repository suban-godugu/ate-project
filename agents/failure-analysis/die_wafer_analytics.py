"""FA-FR-007 / FA-FR-008: Die-level and wafer-level analytics with severity caveat."""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from typing import Any

from adapters.schema import TestRecord
from ingestor import DieLog, PatternResult

SEVERITY_NOT_DETERMINABLE = "Not determinable — insufficient data"
DIE_SCRAP_SEVERITY = 0.10
OUTLIER_MAD_FACTOR = 3.5


def analyze_die_level_failures(
    die_logs: list[DieLog],
    *,
    test_records: list[TestRecord] | None = None,
    recurring_failures: dict[str, Any] | None = None,
    classify_fault_type_fn: Any = None,
) -> dict[str, Any]:
    """Per-die failure profiles for dashboards and Spatial AI handoff."""
    record_index = _index_records(test_records)
    classify = classify_fault_type_fn or (lambda _p: "UNKNOWN")

    die_statistics: list[dict[str, Any]] = []
    spatial_handoff: list[dict[str, Any]] = []

    for die in die_logs:
        rec = record_index.get((die.lot_id, die.wafer_id, die.die_id))
        fault_breakdown: Counter[str] = Counter()
        chain_breakdown: Counter[str] = Counter()
        failing_patterns: list[str] = []
        failing_tests: list[str] = []

        for pattern in die.failing_patterns:
            fault_breakdown[classify(pattern)] += 1
            failing_patterns.append(pattern.pattern_id)
            if pattern.scan_chain_id:
                chain_breakdown[pattern.scan_chain_id] += 1

        if rec:
            failing_tests.extend(rec.failing_tests)
            for pid in rec.failing_patterns:
                if pid not in failing_patterns:
                    failing_patterns.append(pid)

        severity_info = _compute_die_severity(die, rec)
        recurrence_flags = _die_recurrence_flags(die, failing_patterns, recurring_failures)

        x = _coord(die, rec, "DIE_X", "x")
        y = _coord(die, rec, "DIE_Y", "y")
        bin_history = _bin_history(die, rec)

        profile = {
            "die_id": die.die_id,
            "wafer_id": die.wafer_id,
            "lot_id": die.lot_id,
            "device_name": die.device_name,
            "source_path": die.source_path,
            "x": x,
            "y": y,
            "declared_patterns": die.declared_patterns,
            "total_patterns": die.execution_count,
            "failing_pattern_count": len(die.failing_patterns),
            "passing_pattern_count": die.execution_count - len(die.failing_patterns),
            "is_failing_die": die.is_failing_die,
            "failing_patterns": sorted(set(failing_patterns)),
            "failing_tests": sorted(set(failing_tests)),
            "dominant_fault_type": fault_breakdown.most_common(1)[0][0] if fault_breakdown else None,
            "fault_breakdown": dict(fault_breakdown),
            "top_scan_chains": [c for c, _ in chain_breakdown.most_common(3)],
            "bin_history": bin_history,
            "retest_outcome": _retest_outcome(die, rec),
            "recurrence_flags": recurrence_flags,
            "severity_determinable": severity_info["determinable"],
            "severity_class": severity_info["severity_class"],
            "severity_label": severity_info["severity_label"],
            "die_failure_severity": severity_info["severity_value"],
            "severity_evidence": severity_info["evidence"],
            "disposition": severity_info["disposition"],
            "wafer_coordinates": {
                "wafer_x": _parse_numeric(die.header_fields.get("WAFER_X")),
                "wafer_y": _parse_numeric(die.header_fields.get("WAFER_Y")),
                "die_row": _parse_numeric(die.header_fields.get("DIE_ROW")),
                "die_col": _parse_numeric(die.header_fields.get("DIE_COL")),
                "x": x,
                "y": y,
            },
        }
        die_statistics.append(profile)

        spatial_handoff.append(
            {
                "die_id": die.die_id,
                "wafer_id": die.wafer_id,
                "lot_id": die.lot_id,
                "x": x,
                "y": y,
                "is_failing": die.is_failing_die,
                "intensity": profile["die_failure_severity"],
                "severity_class": profile["severity_class"],
                "dominant_fault_type": profile["dominant_fault_type"],
                "recurrence_flags": recurrence_flags,
            }
        )

    die_statistics.sort(
        key=lambda item: (item["is_failing_die"], item["die_failure_severity"] or 0),
        reverse=True,
    )

    return {
        "purpose": (
            "Per-die actionable profiles: coordinates, bins, patterns, fault types, "
            "recurrence flags, and severity (only when data supports it)."
        ),
        "differentiator_vs_fa_fr_003": (
            "FA-FR-003 = aggregate rates. FA-FR-007 = per-die drill-down records "
            "for disposition and Spatial AI handoff."
        ),
        "severity_caveat": (
            "Marginal vs catastrophic severity is computed only when parametric margins, "
            "spec limits, AI severity scores, or retest outcomes exist. Otherwise reported "
            f"as '{SEVERITY_NOT_DETERMINABLE}'."
        ),
        "total_dies": len(die_statistics),
        "failing_dies": sum(1 for d in die_statistics if d["is_failing_die"]),
        "severity_determinable_count": sum(1 for d in die_statistics if d["severity_determinable"]),
        "dashboard_feed": die_statistics,
        "spatial_ai_handoff": spatial_handoff,
    }


def analyze_wafer_level_failures(
    die_logs: list[DieLog],
    *,
    test_records: list[TestRecord] | None = None,
    failure_rates_engine: dict[str, Any] | None = None,
    classify_fault_type_fn: Any = None,
) -> dict[str, Any]:
    """Normalized wafer statistics, pareto charts, outlier detection, and trends."""
    classify = classify_fault_type_fn or (lambda _p: "UNKNOWN")
    record_index = _index_records(test_records)
    engine_wafer = (failure_rates_engine or {}).get("wafer_level", {})

    by_wafer: dict[str, list[DieLog]] = defaultdict(list)
    for die in die_logs:
        by_wafer[die.wafer_id].append(die)

    by_lot: dict[str, list[str]] = defaultdict(list)
    wafer_statistics: list[dict[str, Any]] = []
    heatmap_data: list[dict[str, Any]] = []
    spatial_map: list[dict[str, Any]] = []
    alerts: list[dict[str, Any]] = []

    for wafer_id, dies in sorted(by_wafer.items()):
        lot_id = dies[0].lot_id
        by_lot[lot_id].append(wafer_id)

        failing_dies = sum(1 for d in dies if d.is_failing_die)
        total = len(dies)
        engine_stats = engine_wafer.get(wafer_id, {})
        failure_rate_pct = engine_stats.get(
            "failure_rate_pct",
            round(100.0 * failing_dies / total, 6) if total else 0.0,
        )
        yield_pct = engine_stats.get("yield_pct", round(100.0 - failure_rate_pct, 6))

        bin_pareto: Counter[str] = Counter()
        fault_pareto: Counter[str] = Counter()
        pattern_pareto: Counter[str] = Counter()

        for die in dies:
            rec = record_index.get((die.lot_id, die.wafer_id, die.die_id))
            bin_key = _bin_label(die, rec)
            bin_pareto[bin_key] += 1
            for pattern in die.failing_patterns:
                fault_pareto[classify(pattern)] += 1
                pattern_pareto[pattern.pattern_id] += 1

            spatial_map.append(
                {
                    "wafer_id": wafer_id,
                    "die_id": die.die_id,
                    "lot_id": lot_id,
                    "wafer_x": _parse_numeric(die.header_fields.get("WAFER_X")),
                    "wafer_y": _parse_numeric(die.header_fields.get("WAFER_Y")),
                    "x": _coord(die, rec, "DIE_X", "x"),
                    "y": _coord(die, rec, "DIE_Y", "y"),
                    "is_failing": die.is_failing_die,
                    "failing_count": len(die.failing_patterns),
                    "intensity": _safe_rate(len(die.failing_patterns), die.execution_count),
                }
            )

        signature = _wafer_spatial_signature(dies)
        wafer_statistics.append(
            {
                "wafer_id": wafer_id,
                "lot_id": lot_id,
                "wafer_slot": _wafer_slot(wafer_id),
                "total_dies_tested": total,
                "failing_dies": failing_dies,
                "passing_dies": total - failing_dies,
                "yield_pct": yield_pct,
                "failure_rate": failure_rate_pct / 100.0,
                "failure_rate_pct": failure_rate_pct,
                "spatial_signature": signature,
                "bin_pareto": _pareto_list(bin_pareto),
                "dominant_fault_types": _pareto_list(fault_pareto),
                "failing_pattern_pareto": _pareto_list(pattern_pareto, limit=10),
                "die_ids": [d.die_id for d in dies],
                "is_outlier": False,
                "outlier_reason": "",
            }
        )

        heatmap_data.append(
            {
                "wafer_id": wafer_id,
                "lot_id": lot_id,
                "failure_rate": failure_rate_pct / 100.0,
                "failure_rate_pct": failure_rate_pct,
                "die_count": total,
                "spatial_signature": signature,
                "intensity": failure_rate_pct / 100.0,
            }
        )

    _flag_outlier_wafers(wafer_statistics, by_lot)
    alerts.extend(_build_wafer_alerts(wafer_statistics, failure_rates_engine))

    wafer_statistics.sort(key=lambda item: item["failure_rate_pct"], reverse=True)
    heatmap_data.sort(key=lambda item: item["failure_rate_pct"], reverse=True)
    lot_trends = _lot_sequence_trends(wafer_statistics)

    return {
        "purpose": (
            "Normalized cross-customer wafer statistics with pareto breakdowns, "
            "outlier detection vs lot siblings, and lot-sequence trends."
        ),
        "differentiator_vs_fa_fr_003": (
            "FA-FR-003 = single failure rate number. FA-FR-008 = spatial signature, "
            "bin/fault/pattern pareto, outlier flags, and equipment-style alerts."
        ),
        "total_wafers": len(wafer_statistics),
        "outlier_wafer_count": sum(1 for w in wafer_statistics if w["is_outlier"]),
        "wafer_ranking": [
            {
                "rank": idx + 1,
                "wafer_id": item["wafer_id"],
                "lot_id": item["lot_id"],
                "failure_rate": item["failure_rate"],
                "failure_rate_pct": item["failure_rate_pct"],
                "spatial_signature": item["spatial_signature"],
                "is_outlier": item["is_outlier"],
            }
            for idx, item in enumerate(wafer_statistics[:20])
        ],
        "dashboard_feed": wafer_statistics,
        "heatmap_data": heatmap_data,
        "spatial_map": spatial_map,
        "alerts": alerts,
        "lot_sequence_trends": lot_trends,
    }


def _compute_die_severity(die: DieLog, rec: TestRecord | None) -> dict[str, Any]:
    if not die.is_failing_die:
        return {
            "determinable": True,
            "severity_class": "PASS",
            "severity_label": "PASS",
            "severity_value": 0.0,
            "disposition": "RELEASE",
            "evidence": ["die passed all tests"],
        }

    evidence: list[str] = []
    scores: list[float] = []

    retest = _retest_outcome(die, rec)
    if retest:
        evidence.append(f"retest_outcome={retest}")
        if retest.upper() in {"PASS", "RETEST_PASS"}:
            return {
                "determinable": True,
                "severity_class": "MARGINAL_FAIL",
                "severity_label": "MARGINAL_FAIL",
                "severity_value": _safe_rate(len(die.failing_patterns), die.execution_count),
                "disposition": "RETEST",
                "evidence": evidence + ["retest passed — marginal"],
            }
        if retest.upper() in {"FAIL", "RETEST_FAIL"}:
            return {
                "determinable": True,
                "severity_class": "CATASTROPHIC_FAIL",
                "severity_label": "CATASTROPHIC_FAIL",
                "severity_value": 1.0,
                "disposition": "SCRAP",
                "evidence": evidence + ["retest failed — catastrophic"],
            }

    for pattern in die.failing_patterns[:5]:
        fields = pattern.raw_fields
        ai_score = _parse_numeric(fields.get("AI_SEVERITY_SCORE"))
        if ai_score is not None:
            scores.append(min(max(ai_score, 0.0), 1.0))
            evidence.append(f"AI_SEVERITY_SCORE={ai_score}")

        setup = _parse_numeric(fields.get("SETUP_SLACK_PS"))
        hold = _parse_numeric(fields.get("HOLD_SLACK_PS"))
        if setup is not None and setup < 0:
            scores.append(min(abs(setup) / 100.0, 1.0))
            evidence.append(f"SETUP_SLACK_PS={setup}")
        if hold is not None and hold < 0:
            scores.append(min(abs(hold) / 100.0, 1.0))
            evidence.append(f"HOLD_SLACK_PS={hold}")

        if rec and rec.parametric:
            for key, val in rec.parametric.items():
                if "slack" in key and isinstance(val, (int, float)) and val < 0:
                    scores.append(min(abs(float(val)) / 100.0, 1.0))
                    evidence.append(f"parametric {key}={val}")

    if scores:
        severity_value = round(sum(scores) / len(scores), 6)
        if severity_value >= DIE_SCRAP_SEVERITY:
            sev_class = "CATASTROPHIC_FAIL"
            disposition = "SCRAP"
        else:
            sev_class = "MARGINAL_FAIL"
            disposition = "RETEST"
        return {
            "determinable": True,
            "severity_class": sev_class,
            "severity_label": sev_class,
            "severity_value": severity_value,
            "disposition": disposition,
            "evidence": evidence,
        }

    return {
        "determinable": False,
        "severity_class": "UNKNOWN",
        "severity_label": SEVERITY_NOT_DETERMINABLE,
        "severity_value": None,
        "disposition": "RETEST" if die.is_failing_die else "RELEASE",
        "evidence": ["insufficient parametric margins, spec limits, or retest data"],
    }


def _flag_outlier_wafers(
    wafer_statistics: list[dict[str, Any]],
    by_lot: dict[str, list[str]],
) -> None:
    rates_by_lot: dict[str, list[float]] = defaultdict(list)
    wafer_lookup = {w["wafer_id"]: w for w in wafer_statistics}

    for wafer in wafer_statistics:
        rates_by_lot[wafer["lot_id"]].append(wafer["failure_rate_pct"])

    for lot_id, wafer_ids in by_lot.items():
        rates = rates_by_lot.get(lot_id, [])
        if len(rates) < 2:
            continue
        median = statistics.median(rates)
        deviations = [abs(r - median) for r in rates]
        mad = statistics.median(deviations) or 0.0001

        for wid in wafer_ids:
            wafer = wafer_lookup[wid]
            rate = wafer["failure_rate_pct"]
            delta = rate - median
            mad_threshold = OUTLIER_MAD_FACTOR * mad
            ratio_outlier = (
                delta > 0
                and delta >= max(5.0, median * 2)
                and rate >= median + 5.0
            )
            mad_outlier = mad > 0 and abs(rate - median) > mad_threshold
            if ratio_outlier or mad_outlier:
                wafer["is_outlier"] = True
                wafer["outlier_reason"] = (
                    f"Rate {rate:.2f}% vs lot median {median:.2f}% "
                    f"(delta {delta:.2f} pct pts)"
                )


def _build_wafer_alerts(
    wafer_statistics: list[dict[str, Any]],
    failure_rates_engine: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    for wafer in wafer_statistics:
        if wafer["is_outlier"]:
            alerts.append(
                {
                    "wafer_id": wafer["wafer_id"],
                    "lot_id": wafer["lot_id"],
                    "alert_type": "OUTLIER_VS_LOT_SIBLINGS",
                    "current_failure_rate_pct": wafer["failure_rate_pct"],
                    "message": wafer["outlier_reason"],
                    "spatial_signature": wafer["spatial_signature"],
                }
            )

    if failure_rates_engine:
        for alert in failure_rates_engine.get("alerts", []):
            if alert.get("level") == "wafer":
                alerts.append(alert)
    return alerts


def _lot_sequence_trends(wafer_statistics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_lot: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for wafer in wafer_statistics:
        by_lot[wafer["lot_id"]].append(wafer)

    trends: list[dict[str, Any]] = []
    for lot_id, wafers in sorted(by_lot.items()):
        ordered = sorted(wafers, key=lambda w: w.get("wafer_slot", 0))
        rates = [w["failure_rate_pct"] for w in ordered]
        if len(rates) < 2:
            direction = "STABLE"
        elif rates[-1] > rates[0] * 1.1:
            direction = "WORSENING"
        elif rates[-1] < rates[0] * 0.9:
            direction = "IMPROVING"
        else:
            direction = "STABLE"
        trends.append(
            {
                "lot_id": lot_id,
                "wafer_count": len(ordered),
                "sequence": [
                    {"wafer_id": w["wafer_id"], "slot": w.get("wafer_slot"), "failure_rate_pct": w["failure_rate_pct"]}
                    for w in ordered
                ],
                "trend_direction": direction,
            }
        )
    return trends


def _wafer_spatial_signature(dies: list[DieLog]) -> str:
    failing = [d for d in dies if d.is_failing_die]
    if not failing:
        return "NONE"

    defect_types = Counter(
        d.header_fields.get("DEFECT_TYPE", "").strip().upper()
        for d in failing
        if d.header_fields.get("DEFECT_TYPE")
    )
    if defect_types:
        return defect_types.most_common(1)[0][0]

    pts = [
        (_parse_numeric(d.header_fields.get("WAFER_X")), _parse_numeric(d.header_fields.get("WAFER_Y")))
        for d in dies
    ]
    pts = [(x, y) for x, y in pts if x is not None and y is not None]
    fail_pts = [
        (_parse_numeric(d.header_fields.get("WAFER_X")), _parse_numeric(d.header_fields.get("WAFER_Y")))
        for d in failing
    ]
    fail_pts = [(x, y) for x, y in fail_pts if x is not None and y is not None]
    if not pts or not fail_pts:
        return "UNCLASSIFIED"

    cx = sum(x for x, _ in pts) / len(pts)
    cy = sum(y for _, y in pts) / len(pts)
    max_r = max(((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 for x, y in pts) or 1.0
    avg_fail_r = sum(((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 for x, y in fail_pts) / len(fail_pts)
    ratio = avg_fail_r / max_r
    if ratio < 0.34:
        return "CENTER"
    if ratio < 0.67:
        return "MID_RADIUS"
    return "EDGE"


def _index_records(test_records: list[TestRecord] | None) -> dict[tuple[str, str, str], TestRecord]:
    index: dict[tuple[str, str, str], TestRecord] = {}
    if not test_records:
        return index
    for rec in test_records:
        index[(rec.lot_id, rec.wafer_id, rec.die_id)] = rec
    return index


def _recurring_pattern_set(recurring_failures: dict[str, Any] | None) -> set[str]:
    if not recurring_failures:
        return set()
    return {
        item["pattern_id"]
        for item in recurring_failures.get("recurring_failures", [])
        if item.get("is_recurring", True)
    }


def _die_recurrence_flags(
    die: DieLog,
    failing_patterns: list[str],
    recurring_failures: dict[str, Any] | None,
) -> list[str]:
    recurring_patterns = _recurring_pattern_set(recurring_failures)
    flags = [f"pattern:{pid}" for pid in failing_patterns if pid in recurring_patterns]
    if recurring_failures:
        die_key = f"{die.lot_id}|{die.wafer_id}|{die.die_id}"
        for event in recurring_failures.get("entity_index", {}).get("dies", {}).get(die_key, []):
            flags.append(f"{event['signature_type']}:{event['entity_key']}")
    return sorted(set(flags))


def _bin_history(die: DieLog, rec: TestRecord | None) -> dict[str, str]:
    history: dict[str, str] = {}
    if rec:
        if rec.hard_bin:
            history["hard_bin"] = rec.hard_bin
        if rec.soft_bin:
            history["soft_bin"] = rec.soft_bin
    for key in ("HARD_BIN", "SOFT_BIN", "BIN"):
        if die.header_fields.get(key):
            history[key.lower()] = die.header_fields[key]
    return history


def _bin_label(die: DieLog, rec: TestRecord | None) -> str:
    if rec and rec.hard_bin:
        return f"H{rec.hard_bin}"
    if die.header_fields.get("HARD_BIN"):
        return f"H{die.header_fields['HARD_BIN']}"
    return "PASS" if not die.is_failing_die else "FAIL"


def _retest_outcome(die: DieLog, rec: TestRecord | None) -> str:
    for key in ("RETEST_OUTCOME", "RETEST_RESULT", "RETEST_STATUS"):
        if die.header_fields.get(key):
            return str(die.header_fields[key])
    if rec and rec.raw_fields.get("retest_outcome"):
        return str(rec.raw_fields["retest_outcome"])
    return ""


def _coord(die: DieLog, rec: TestRecord | None, header_key: str, rec_key: str) -> int | None:
    """Resolve die grid coordinates from common ATE header aliases."""
    header_aliases = {
        "DIE_X": ("DIE_X", "DIE_COL", "WAFER_X", "X1"),
        "DIE_Y": ("DIE_Y", "DIE_ROW", "WAFER_Y", "Y1"),
    }
    for key in header_aliases.get(header_key, (header_key,)):
        val = die.header_fields.get(key)
        if val is not None:
            parsed = _parse_int(val)
            if parsed is not None:
                return parsed
    if rec is not None:
        direct = getattr(rec, rec_key, None)
        if direct is not None:
            return direct
        raw = rec.raw_fields or {}
        for key in header_aliases.get(header_key, (header_key,)):
            parsed = _parse_int(raw.get(key))
            if parsed is not None:
                return parsed
    return None


def _wafer_slot(wafer_id: str) -> int:
    digits = "".join(c for c in wafer_id if c.isdigit())
    try:
        return int(digits) if digits else 0
    except ValueError:
        return 0


def _pareto_list(counter: Counter[str], limit: int = 5) -> list[dict[str, Any]]:
    total = sum(counter.values()) or 1
    return [
        {"name": name, "count": count, "share_pct": round(100.0 * count / total, 2)}
        for name, count in counter.most_common(limit)
    ]


def _parse_numeric(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _parse_int(value: str | int | None) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def _safe_rate(failing: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(failing / total, 6)
