"""FA-FR-005: Multi-signature recurrence detection at die, wafer, and lot scope."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from adapters.schema import TestRecord
from adapters.yaml_config import load_adapter_configs
from ingestor import DieLog

DEFAULT_MANIFEST_PATH = (
    Path(__file__).resolve().parent / "config" / "recurrence_manifest.yaml"
)

RECURRING_DEFINITION = (
    "A signature is RECURRING when it appears across >= min_entities distinct "
    "entities in scope (default N=3 lots/wafers/shifts) OR accounts for >= "
    "failure_share_threshold of failures in the analysis window. Supported "
    "signatures: bin, die-position (X,Y), wafer slot, equipment (tester rate "
    ">= K x fleet median), pattern, and temporal shift spikes."
)


@dataclass
class RecurrenceConfig:
    min_entities: int
    failure_share_threshold: float
    equipment_rate_multiplier: float
    signatures: dict[str, dict[str, Any]]

    @classmethod
    def load(cls, path: Path | None = None) -> RecurrenceConfig:
        raw = load_adapter_configs(path or DEFAULT_MANIFEST_PATH)
        defaults = dict(raw.get("defaults", {}))
        return cls(
            min_entities=int(defaults.get("min_entities", 3)),
            failure_share_threshold=float(defaults.get("failure_share_threshold", 0.40)),
            equipment_rate_multiplier=float(defaults.get("equipment_rate_multiplier", 3.0)),
            signatures=dict(raw.get("signatures", {})),
        )

    def sig(self, name: str) -> dict[str, Any]:
        cfg = dict(self.signatures.get(name, {}))
        cfg.setdefault("enabled", True)
        cfg.setdefault("min_entities", self.min_entities)
        if name == "equipment":
            cfg.setdefault("multiplier", self.equipment_rate_multiplier)
        return cfg


def detect_recurrences(
    die_logs: list[DieLog],
    *,
    test_records: list[TestRecord] | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Detect recurring failure signatures across die, wafer, and lot scopes."""
    config = RecurrenceConfig.load(manifest_path)
    record_index = _index_records(test_records)
    total_failures = sum(len(die.failing_patterns) for die in die_logs)
    events: list[dict[str, Any]] = []

    if config.sig("pattern")["enabled"]:
        events.extend(_detect_pattern_recurrence(die_logs, config, total_failures))
    if config.sig("bin")["enabled"]:
        events.extend(
            _detect_bin_recurrence(die_logs, record_index, config, total_failures)
        )
    if config.sig("die_position")["enabled"]:
        events.extend(
            _detect_die_position_recurrence(
                die_logs, record_index, config, total_failures
            )
        )
    if config.sig("wafer_slot")["enabled"]:
        events.extend(_detect_wafer_slot_recurrence(die_logs, config, total_failures))
    if config.sig("equipment")["enabled"]:
        events.extend(_detect_equipment_recurrence(die_logs, config, total_failures))
    if config.sig("temporal")["enabled"]:
        events.extend(
            _detect_temporal_recurrence(
                die_logs, record_index, config, total_failures
            )
        )

    entity_index = _build_entity_index(events)
    pattern_events = [e for e in events if e["signature_type"] == "pattern_recurrence"]
    legacy_recurring = _legacy_pattern_rows(pattern_events)

    return {
        "manifest_source": str(manifest_path or DEFAULT_MANIFEST_PATH),
        "recurring_definition": RECURRING_DEFINITION,
        "min_entities_threshold": config.min_entities,
        "failure_share_threshold": config.failure_share_threshold,
        "equipment_rate_multiplier": config.equipment_rate_multiplier,
        "total_failure_occurrences": total_failures,
        "signature_summary": _signature_summary(events),
        "recurrence_events": events,
        "entity_index": entity_index,
        "min_lots_threshold": int(config.sig("pattern")["min_entities"]),
        "total_unique_failing_patterns": len(
            {e["entity_key"] for e in pattern_events}
        ),
        "recurring_pattern_count": len(pattern_events),
        "non_recurring_pattern_count": max(
            0,
            _unique_pattern_count(die_logs) - len(pattern_events),
        ),
        "recurring_failures": legacy_recurring,
        "recurring_scope": {
            "lot_based": True,
            "wafer_level": True,
            "die_level": True,
            "equipment_level": True,
            "temporal_level": True,
            "note": (
                "FA-FR-005 multi-signature recurrence. See recurrence_events for "
                "signature_type, confidence, and recommendations; entity_index "
                "maps flags to die, wafer, and lot keys."
            ),
        },
    }


def identify_recurring_failures(
    die_logs: list[DieLog],
    *,
    min_lots: int | None = None,
    test_records: list[TestRecord] | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Backward-compatible wrapper used by analyzer and dashboards."""
    result = detect_recurrences(
        die_logs, test_records=test_records, manifest_path=manifest_path
    )
    if min_lots is not None:
        pattern_events = [
            e
            for e in result["recurrence_events"]
            if e["signature_type"] == "pattern_recurrence"
            and e["entity_count"] >= min_lots
        ]
        result["min_lots_threshold"] = min_lots
        result["recurring_failures"] = _legacy_pattern_rows(pattern_events)
        result["recurring_pattern_count"] = len(pattern_events)
        result["non_recurring_pattern_count"] = max(
            0, _unique_pattern_count(die_logs) - len(pattern_events)
        )
    return result


def _detect_pattern_recurrence(
    die_logs: list[DieLog],
    config: RecurrenceConfig,
    total_failures: int,
) -> list[dict[str, Any]]:
    sig = config.sig("pattern")
    min_entities = int(sig["min_entities"])
    stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "lots": set(),
            "wafers": set(),
            "dies": set(),
            "failure_count": 0,
            "scan_chain_ids": set(),
        }
    )
    for die in die_logs:
        for pattern in die.failing_patterns:
            row = stats[pattern.pattern_id]
            row["lots"].add(die.lot_id)
            row["wafers"].add(die.wafer_id)
            row["dies"].add((die.lot_id, die.wafer_id, die.die_id))
            row["failure_count"] += 1
            if pattern.scan_chain_id:
                row["scan_chain_ids"].add(pattern.scan_chain_id)

    events: list[dict[str, Any]] = []
    for pattern_id, row in stats.items():
        entity_count = len(row["lots"])
        failure_count = row["failure_count"]
        if not _is_recurring(
            entity_count, failure_count, total_failures, min_entities, config
        ):
            continue
        confidence = _confidence(entity_count, failure_count, total_failures, min_entities)
        events.append(
            {
                "signature_type": "pattern_recurrence",
                "scope": str(sig.get("scope", "lot")),
                "entity_key": pattern_id,
                "entity_count": entity_count,
                "failure_count": failure_count,
                "confidence": confidence,
                "affected_lots": sorted(row["lots"]),
                "affected_wafers": len(row["wafers"]),
                "affected_dies": len(row["dies"]),
                "scan_chain_ids": sorted(row["scan_chain_ids"])[:5],
                "recommendation": str(sig.get("recommendation", "")),
                "is_recurring": True,
                "die_keys": [
                    f"{lot}|{wafer}|{die}" for lot, wafer, die in sorted(row["dies"])
                ],
                "wafer_keys": sorted(
                    {f"{lot}|{wafer}" for lot, wafer, _ in row["dies"]}
                ),
                "lot_keys": sorted(row["lots"]),
            }
        )
    events.sort(key=lambda e: (e["entity_count"], e["failure_count"]), reverse=True)
    return events


def _detect_bin_recurrence(
    die_logs: list[DieLog],
    record_index: dict[tuple[str, str, str], TestRecord],
    config: RecurrenceConfig,
    total_failures: int,
) -> list[dict[str, Any]]:
    sig = config.sig("bin")
    min_entities = int(sig["min_entities"])
    stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"lots": set(), "wafers": set(), "dies": set(), "failure_count": 0}
    )
    for die in die_logs:
        if not die.is_failing_die:
            continue
        rec = record_index.get((die.lot_id, die.wafer_id, die.die_id))
        hard_bin = _hard_bin(die, rec)
        if not hard_bin:
            continue
        row = stats[hard_bin]
        row["lots"].add(die.lot_id)
        row["wafers"].add(f"{die.lot_id}|{die.wafer_id}")
        row["dies"].add((die.lot_id, die.wafer_id, die.die_id))
        row["failure_count"] += len(die.failing_patterns) or 1

    return _build_scope_events(
        stats,
        signature_type="bin_recurrence",
        scope=str(sig.get("scope", "lot")),
        entity_label="hard_bin",
        min_entities=min_entities,
        config=config,
        total_failures=total_failures,
        recommendation=str(sig.get("recommendation", "")),
        entity_counter=lambda row: len(row["lots"]),
    )


def _detect_die_position_recurrence(
    die_logs: list[DieLog],
    record_index: dict[tuple[str, str, str], TestRecord],
    config: RecurrenceConfig,
    total_failures: int,
) -> list[dict[str, Any]]:
    sig = config.sig("die_position")
    min_entities = int(sig["min_entities"])
    stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"wafers": set(), "dies": set(), "failure_count": 0}
    )
    for die in die_logs:
        if not die.is_failing_die:
            continue
        x, y = _die_xy(die, record_index.get((die.lot_id, die.wafer_id, die.die_id)))
        if x is None or y is None:
            continue
        key = f"({x},{y})"
        row = stats[key]
        row["wafers"].add(f"{die.lot_id}|{die.wafer_id}")
        row["dies"].add((die.lot_id, die.wafer_id, die.die_id))
        row["failure_count"] += len(die.failing_patterns) or 1

    return _build_scope_events(
        stats,
        signature_type="die_position_recurrence",
        scope=str(sig.get("scope", "wafer")),
        entity_label="die_xy",
        min_entities=min_entities,
        config=config,
        total_failures=total_failures,
        recommendation=str(sig.get("recommendation", "")),
        entity_counter=lambda row: len(row["wafers"]),
    )


def _detect_wafer_slot_recurrence(
    die_logs: list[DieLog],
    config: RecurrenceConfig,
    total_failures: int,
) -> list[dict[str, Any]]:
    sig = config.sig("wafer_slot")
    min_entities = int(sig["min_entities"])
    stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"lots": set(), "wafers": set(), "dies": set(), "failure_count": 0}
    )
    for die in die_logs:
        if not die.is_failing_die:
            continue
        slot = _wafer_slot(die)
        if slot is None:
            continue
        row = stats[str(slot)]
        row["lots"].add(die.lot_id)
        row["wafers"].add(f"{die.lot_id}|{die.wafer_id}")
        row["dies"].add((die.lot_id, die.wafer_id, die.die_id))
        row["failure_count"] += len(die.failing_patterns) or 1

    return _build_scope_events(
        stats,
        signature_type="wafer_slot_recurrence",
        scope=str(sig.get("scope", "lot")),
        entity_label="wafer_slot",
        min_entities=min_entities,
        config=config,
        total_failures=total_failures,
        recommendation=str(sig.get("recommendation", "")),
        entity_counter=lambda row: len(row["lots"]),
    )


def _detect_equipment_recurrence(
    die_logs: list[DieLog],
    config: RecurrenceConfig,
    total_failures: int,
) -> list[dict[str, Any]]:
    sig = config.sig("equipment")
    multiplier = float(sig.get("multiplier", config.equipment_rate_multiplier))
    tester_stats: dict[str, dict[str, int]] = defaultdict(
        lambda: {"tested": 0, "failing": 0}
    )
    for die in die_logs:
        tester = die.tester_name or "UNKNOWN"
        tester_stats[tester]["tested"] += 1
        if die.is_failing_die:
            tester_stats[tester]["failing"] += 1

    rates = {
        tester: (row["failing"] / row["tested"] if row["tested"] else 0.0)
        for tester, row in tester_stats.items()
    }
    if not rates:
        return []

    sorted_rates = sorted(rates.values())
    median_rate = sorted_rates[len(sorted_rates) // 2]
    threshold = max(median_rate * multiplier, 0.01)

    events: list[dict[str, Any]] = []
    for tester, row in tester_stats.items():
        rate = rates[tester]
        if rate < threshold or row["failing"] == 0:
            continue
        confidence = min(1.0, round(rate / threshold, 4)) if threshold else 1.0
        events.append(
            {
                "signature_type": "equipment_recurrence",
                "scope": str(sig.get("scope", "fleet")),
                "entity_key": tester,
                "entity_count": row["failing"],
                "failure_count": row["failing"],
                "failure_rate": round(rate, 6),
                "fleet_median_rate": round(median_rate, 6),
                "rate_threshold": round(threshold, 6),
                "confidence": confidence,
                "recommendation": str(sig.get("recommendation", "")),
                "is_recurring": True,
                "die_keys": [
                    f"{die.lot_id}|{die.wafer_id}|{die.die_id}"
                    for die in die_logs
                    if (die.tester_name or "UNKNOWN") == tester and die.is_failing_die
                ],
                "lot_keys": sorted(
                    {
                        die.lot_id
                        for die in die_logs
                        if (die.tester_name or "UNKNOWN") == tester and die.is_failing_die
                    }
                ),
            }
        )
    events.sort(key=lambda e: e["failure_rate"], reverse=True)
    return events


def _detect_temporal_recurrence(
    die_logs: list[DieLog],
    record_index: dict[tuple[str, str, str], TestRecord],
    config: RecurrenceConfig,
    total_failures: int,
) -> list[dict[str, Any]]:
    sig = config.sig("temporal")
    min_entities = int(sig["min_entities"])
    shift_hours = int(sig.get("shift_hours", 8))
    stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"lots": set(), "dies": set(), "failure_count": 0}
    )
    for die in die_logs:
        if not die.is_failing_die:
            continue
        rec = record_index.get((die.lot_id, die.wafer_id, die.die_id))
        shift = _shift_bucket(die, rec, shift_hours)
        if not shift:
            continue
        row = stats[shift]
        row["lots"].add(die.lot_id)
        row["dies"].add((die.lot_id, die.wafer_id, die.die_id))
        row["failure_count"] += len(die.failing_patterns) or 1

    return _build_scope_events(
        stats,
        signature_type="temporal_recurrence",
        scope=str(sig.get("scope", "shift")),
        entity_label="shift_window",
        min_entities=min_entities,
        config=config,
        total_failures=total_failures,
        recommendation=str(sig.get("recommendation", "")),
        entity_counter=lambda row: row["failure_count"],
        recurring_predicate=lambda entity_count, failure_count: entity_count >= min_entities
        and failure_count >= min_entities,
    )


def _build_scope_events(
    stats: dict[str, dict[str, Any]],
    *,
    signature_type: str,
    scope: str,
    entity_label: str,
    min_entities: int,
    config: RecurrenceConfig,
    total_failures: int,
    recommendation: str,
    entity_counter,
    recurring_predicate=None,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for entity_key, row in stats.items():
        entity_count = entity_counter(row)
        failure_count = row["failure_count"]
        recurring = (
            recurring_predicate(entity_count, failure_count)
            if recurring_predicate
            else _is_recurring(
                entity_count, failure_count, total_failures, min_entities, config
            )
        )
        if not recurring:
            continue
        die_keys = [
            f"{lot}|{wafer}|{die}" for lot, wafer, die in sorted(row.get("dies", set()))
        ]
        wafer_keys = sorted(
            {
                f"{lot}|{wafer}"
                for lot, wafer, _ in row.get("dies", set())
            }
        ) or sorted(row.get("wafers", set()))
        lot_keys = sorted(row.get("lots", set()))
        events.append(
            {
                "signature_type": signature_type,
                "scope": scope,
                "entity_label": entity_label,
                "entity_key": entity_key,
                "entity_count": entity_count,
                "failure_count": failure_count,
                "confidence": _confidence(
                    entity_count, failure_count, total_failures, min_entities
                ),
                "recommendation": recommendation,
                "is_recurring": True,
                "die_keys": die_keys,
                "wafer_keys": wafer_keys,
                "lot_keys": lot_keys,
            }
        )
    events.sort(key=lambda e: (e["entity_count"], e["failure_count"]), reverse=True)
    return events


def _build_entity_index(events: list[dict[str, Any]]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    index: dict[str, dict[str, list[dict[str, Any]]]] = {
        "dies": defaultdict(list),
        "wafers": defaultdict(list),
        "lots": defaultdict(list),
    }
    for event in events:
        summary = {
            "signature_type": event["signature_type"],
            "entity_key": event["entity_key"],
            "confidence": event["confidence"],
            "recommendation": event.get("recommendation", ""),
        }
        for die_key in event.get("die_keys", []):
            index["dies"][die_key].append(summary)
        for wafer_key in event.get("wafer_keys", []):
            index["wafers"][wafer_key].append(summary)
        for lot_key in event.get("lot_keys", []):
            index["lots"][lot_key].append(summary)
    return {scope: dict(values) for scope, values in index.items()}


def _legacy_pattern_rows(pattern_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in pattern_events:
        rows.append(
            {
                "pattern_id": event["entity_key"],
                "affected_lots": event.get("affected_lots", event.get("lot_keys", [])),
                "lot_count": event["entity_count"],
                "affected_wafers": event.get("affected_wafers", len(event.get("wafer_keys", []))),
                "affected_dies": event.get("affected_dies", len(event.get("die_keys", []))),
                "failure_count": event["failure_count"],
                "primary_fault_category": "Unclassified",
                "scan_chain_ids": event.get("scan_chain_ids", []),
                "is_recurring": True,
                "signature_type": "pattern_recurrence",
                "confidence": event["confidence"],
                "recommendation": event.get("recommendation", ""),
            }
        )
    return rows


def _signature_summary(events: list[dict[str, Any]]) -> dict[str, int]:
    summary = Counter(event["signature_type"] for event in events)
    return dict(summary)


def _unique_pattern_count(die_logs: list[DieLog]) -> int:
    patterns: set[str] = set()
    for die in die_logs:
        for pattern in die.failing_patterns:
            patterns.add(pattern.pattern_id)
    return len(patterns)


def _is_recurring(
    entity_count: int,
    failure_count: int,
    total_failures: int,
    min_entities: int,
    config: RecurrenceConfig,
) -> bool:
    if entity_count >= min_entities:
        return True
    if total_failures <= 0:
        return False
    share = failure_count / total_failures
    return share >= config.failure_share_threshold


def _confidence(
    entity_count: int,
    failure_count: int,
    total_failures: int,
    min_entities: int,
) -> float:
    entity_score = min(1.0, entity_count / max(min_entities, 1))
    share_score = (failure_count / total_failures) if total_failures else 0.0
    return round(min(1.0, 0.6 * entity_score + 0.4 * share_score), 4)


def _index_records(
    test_records: list[TestRecord] | None,
) -> dict[tuple[str, str, str], TestRecord]:
    index: dict[tuple[str, str, str], TestRecord] = {}
    if not test_records:
        return index
    for rec in test_records:
        index[(rec.lot_id, rec.wafer_id, rec.die_id)] = rec
    return index


def _hard_bin(die: DieLog, rec: TestRecord | None) -> str:
    if rec and rec.hard_bin:
        return str(rec.hard_bin)
    for key in ("HARD_BIN", "hard_bin", "BIN"):
        value = die.header_fields.get(key)
        if value:
            return str(value)
    return ""


def _die_xy(die: DieLog, rec: TestRecord | None) -> tuple[int | None, int | None]:
    if rec and rec.x is not None and rec.y is not None:
        return rec.x, rec.y
    x_raw = die.header_fields.get("DIE_X") or die.header_fields.get("X")
    y_raw = die.header_fields.get("DIE_Y") or die.header_fields.get("Y")
    try:
        x = int(x_raw) if x_raw not in (None, "") else None
        y = int(y_raw) if y_raw not in (None, "") else None
        return x, y
    except (TypeError, ValueError):
        return None, None


def _wafer_slot(die: DieLog) -> int | None:
    slot_raw = die.header_fields.get("WAFER_SLOT") or die.header_fields.get("SLOT")
    if slot_raw:
        try:
            return int(slot_raw)
        except ValueError:
            pass
    match = re.search(r"(\d+)$", die.wafer_id or "")
    if match:
        return int(match.group(1))
    return None


def _shift_bucket(die: DieLog, rec: TestRecord | None, shift_hours: int) -> str:
    ts = ""
    if rec and rec.timestamp:
        ts = rec.timestamp
    else:
        ts = die.header_fields.get("TIMESTAMP", "")
    if not ts:
        return ""
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(ts[:19], fmt)
            shift_index = dt.hour // max(shift_hours, 1)
            return f"{dt.date()} shift-{shift_index}"
        except ValueError:
            continue
    return ""
