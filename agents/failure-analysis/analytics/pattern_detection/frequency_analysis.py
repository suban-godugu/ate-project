"""Frequency and density analysis for failure patterns."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


def compute_frequency_table(failures: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Failure counts and rates by pattern_id across scopes."""
    pattern_dies: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    pattern_lots: dict[str, set[str]] = defaultdict(set)
    pattern_wafers: dict[str, set[str]] = defaultdict(set)
    pattern_devices: dict[str, set[str]] = defaultdict(set)
    counts: Counter[str] = Counter()

    all_dies: set[tuple[str, str, str]] = set()
    for row in failures:
        pid = str(row.get("pattern_id", "UNKNOWN"))
        counts[pid] += 1
        die_key = (row.get("lot_id", ""), row.get("wafer_id", ""), row.get("die_id", ""))
        pattern_dies[pid].add(die_key)
        pattern_lots[pid].add(str(row.get("lot_id", "")))
        pattern_wafers[pid].add(str(row.get("wafer_id", "")))
        pattern_devices[pid].add(str(row.get("device_name", "")))
        all_dies.add(die_key)

    total_failures = sum(counts.values()) or 1
    total_dies = len(all_dies) or 1

    table: dict[str, dict[str, Any]] = {}
    for pid, count in counts.items():
        die_count = len(pattern_dies[pid])
        table[pid] = {
            "pattern_id": pid,
            "failure_count": count,
            "failure_frequency": round(count / total_failures, 6),
            "die_count": die_count,
            "die_failure_rate": round(die_count / total_dies, 6),
            "lot_count": len(pattern_lots[pid]),
            "wafer_count": len(pattern_wafers[pid]),
            "device_count": len(pattern_devices[pid]),
            "affected_lots": sorted(pattern_lots[pid]),
            "affected_wafers": sorted(pattern_wafers[pid]),
        }
    return table


def compute_density_by_scope(
    failures: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Pattern density per lot, wafer, and device."""
    scopes = {
        "lot": lambda r: str(r.get("lot_id", "")),
        "wafer": lambda r: f"{r.get('lot_id', '')}|{r.get('wafer_id', '')}",
        "device": lambda r: str(r.get("device_name", "")),
    }
    result: dict[str, list[dict[str, Any]]] = {}
    for scope_name, key_fn in scopes.items():
        bucket: dict[str, Counter[str]] = defaultdict(Counter)
        totals: Counter[str] = Counter()
        for row in failures:
            key = key_fn(row)
            pid = str(row.get("pattern_id", "UNKNOWN"))
            bucket[key][pid] += 1
            totals[key] += 1
        density_rows: list[dict[str, Any]] = []
        for key, counter in bucket.items():
            total = totals[key] or 1
            for pid, count in counter.most_common(5):
                density_rows.append(
                    {
                        "scope": scope_name,
                        "scope_key": key,
                        "pattern_id": pid,
                        "count": count,
                        "density": round(count / total, 6),
                    }
                )
        density_rows.sort(key=lambda item: item["density"], reverse=True)
        result[scope_name] = density_rows[:50]
    return result


def failure_distribution(failures: list[dict[str, Any]]) -> dict[str, Any]:
    freq = compute_frequency_table(failures)
    ordered = sorted(freq.values(), key=lambda r: r["failure_count"], reverse=True)
    return {
        "total_failures": len(failures),
        "unique_patterns": len(freq),
        "top_patterns": ordered[:20],
        "by_lot": _group_count(failures, "lot_id"),
        "by_wafer": _group_count(failures, "wafer_id"),
        "by_device": _group_count(failures, "device_name"),
    }


def _group_count(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter[str(row.get(field, "UNKNOWN"))] += 1
    return dict(counter.most_common(20))
