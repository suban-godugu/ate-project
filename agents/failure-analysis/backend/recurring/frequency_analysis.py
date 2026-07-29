"""Frequency analysis and multi-dimensional correlation for recurring failures."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


def aggregate_failure_statistics(
    failure_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate failure counts across production hierarchy."""
    lot_counts: Counter[str] = Counter()
    wafer_counts: Counter[str] = Counter()
    die_counts: Counter[str] = Counter()
    device_counts: Counter[str] = Counter()
    product_counts: Counter[str] = Counter()
    tester_counts: Counter[str] = Counter()
    time_counts: Counter[str] = Counter()
    pattern_counts: Counter[str] = Counter()

    for row in failure_rows:
        lot_counts[row.get("lot_id", "UNKNOWN")] += 1
        wafer_counts[f"{row.get('lot_id')}|{row.get('wafer_id')}"] += 1
        die_counts[
            f"{row.get('lot_id')}|{row.get('wafer_id')}|{row.get('die_id')}"
        ] += 1
        device_counts[row.get("device_id", "UNKNOWN")] += 1
        product_counts[row.get("product_id", "UNKNOWN")] += 1
        tester_counts[row.get("tester_id", "UNKNOWN")] += 1
        if row.get("time_window"):
            time_counts[row["time_window"]] += 1
        pattern_counts[row.get("pattern_id", "UNKNOWN")] += 1

    total = len(failure_rows) or 1
    return {
        "total_failures": len(failure_rows),
        "unique_patterns": len(pattern_counts),
        "unique_lots": len(lot_counts),
        "unique_wafers": len(wafer_counts),
        "unique_dies": len(die_counts),
        "by_lot": _top_distribution(lot_counts, total),
        "by_wafer": _top_distribution(wafer_counts, total, limit=25),
        "by_die": _top_distribution(die_counts, total, limit=25),
        "by_device": _top_distribution(device_counts, total),
        "by_product": _top_distribution(product_counts, total),
        "by_tester": _top_distribution(tester_counts, total),
        "by_time": _top_distribution(time_counts, total),
        "by_pattern": _top_distribution(pattern_counts, total),
    }


def analyze_correlations(
    failure_rows: list[dict[str, Any]],
    recurrence_events: list[dict[str, Any]],
    *,
    min_entities: int = 3,
) -> dict[str, Any]:
    """Compute correlation strength across lot, wafer, die, device, product, tester, time."""
    stats = aggregate_failure_statistics(failure_rows)
    total = max(stats["total_failures"], 1)

    def _correlation(items: list[dict[str, Any]], label: str) -> dict[str, Any]:
        recurring = [i for i in items if i["count"] >= min_entities]
        return {
            "dimension": label,
            "recurring_entities": len(recurring),
            "top_entity": recurring[0]["entity"] if recurring else None,
            "max_share_pct": round(100.0 * recurring[0]["share"], 2) if recurring else 0.0,
            "entities": recurring[:10],
        }

    return {
        "failure_frequency": {
            "total_failures": stats["total_failures"],
            "recurring_event_count": len(recurrence_events),
            "recurrence_rate_pct": round(
                100.0 * len(recurrence_events) / max(len(stats["by_pattern"]), 1), 2
            ),
        },
        "lot_correlation": _correlation(stats["by_lot"], "lot"),
        "wafer_correlation": _correlation(stats["by_wafer"], "wafer"),
        "die_correlation": _correlation(stats["by_die"], "die"),
        "device_correlation": _correlation(stats["by_device"], "device"),
        "product_correlation": _correlation(stats["by_product"], "product"),
        "tester_correlation": _correlation(stats["by_tester"], "tester"),
        "time_correlation": _correlation(stats["by_time"], "time_window"),
    }


def build_frequency_distribution(
    failure_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Frequency distribution for dashboard charts."""
    pattern_counts: Counter[str] = Counter()
    for row in failure_rows:
        pattern_counts[row.get("pattern_id", "UNKNOWN")] += 1

    total = sum(pattern_counts.values()) or 1
    return [
        {
            "pattern_id": pattern,
            "count": count,
            "frequency_pct": round(100.0 * count / total, 4),
        }
        for pattern, count in pattern_counts.most_common(50)
    ]


def impacted_lots(recurrence_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Lots impacted by recurring failures."""
    lot_map: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"lot_id": "", "recurrence_count": 0, "failure_count": 0, "signatures": set()}
    )
    for event in recurrence_events:
        lots = event.get("lot_keys") or event.get("affected_lots", [])
        for lot in lots:
            row = lot_map[lot]
            row["lot_id"] = lot
            row["recurrence_count"] += 1
            row["failure_count"] += int(event.get("failure_count", 0))
            row["signatures"].add(event.get("entity_key", ""))

    results = []
    for lot, row in lot_map.items():
        results.append(
            {
                "lot_id": lot,
                "recurrence_count": row["recurrence_count"],
                "failure_count": row["failure_count"],
                "signature_count": len(row["signatures"]),
                "signatures": sorted(row["signatures"])[:10],
            }
        )
    results.sort(key=lambda r: (r["recurrence_count"], r["failure_count"]), reverse=True)
    return results


def _top_distribution(
    counter: Counter[str],
    total: int,
    *,
    limit: int = 15,
) -> list[dict[str, Any]]:
    return [
        {
            "entity": entity,
            "count": count,
            "share": round(count / total, 6),
        }
        for entity, count in counter.most_common(limit)
    ]
