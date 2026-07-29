"""Versioned, data-driven engineering rule execution for FA-FR-002."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from adapters.schema import SCHEMA_VERSION, TestRecord
from adapters.yaml_config import load_adapter_configs

DEFAULT_RULES = Path(__file__).resolve().parents[2] / "config" / "pattern_rules.yaml"
SUPPORTED_OPERATORS = {
    "equals",
    "not_equals",
    "contains",
    "in",
    "not_in",
    "not_empty",
    "empty",
    "greater_than",
    "less_than",
    "differs_from",
}


class RuleConfigurationError(ValueError):
    """Raised when a rule definition cannot be executed safely."""


@dataclass(frozen=True)
class RuleSet:
    schema_version: str
    version: str
    confidence_threshold: float
    recurrence_threshold: int
    rules: tuple[dict[str, Any], ...]

    @classmethod
    def load(cls, path: Path | None = None) -> "RuleSet":
        raw = load_adapter_configs(path or DEFAULT_RULES)
        schema = str(raw.get("schema_version", ""))
        if schema != SCHEMA_VERSION.rsplit(".", 1)[0]:
            raise RuleConfigurationError(
                f"Unsupported rule schema '{schema}'; expected 1.0"
            )
        rules = tuple(raw.get("rules") or ())
        keys: set[str] = set()
        for rule in rules:
            key = str(rule.get("rule_key", "")).strip()
            if not key or key in keys:
                raise RuleConfigurationError("Rule keys must be non-empty and unique")
            keys.add(key)
            _validate_expression(rule.get("match", {}))
            confidence = float(rule.get("confidence", 0.0))
            if not 0.0 <= confidence <= 1.0:
                raise RuleConfigurationError(f"Rule {key}: confidence must be 0..1")
        return cls(
            schema_version=schema,
            version=str(raw.get("rule_set_version", "unversioned")),
            confidence_threshold=float(raw.get("confidence_threshold", 0.55)),
            recurrence_threshold=max(2, int(raw.get("recurrence_threshold", 2))),
            rules=rules,
        )


class EngineeringRuleEngine:
    """Evaluate normalized records without executing arbitrary customer code."""

    def __init__(self, rule_set: RuleSet | None = None) -> None:
        self.rule_set = rule_set or RuleSet.load()

    def detect(self, records: list[TestRecord]) -> list[dict[str, Any]]:
        detections: list[dict[str, Any]] = []
        matched_records: set[str] = set()
        for rule in sorted(self.rule_set.rules, key=lambda r: int(r.get("priority", 100))):
            groups: dict[str, list[tuple[TestRecord, dict[str, Any]]]] = {}
            for record in records:
                data = record.to_dict()
                if not _evaluate(rule["match"], data):
                    continue
                source_key = record.record_key or record.build_record_key()
                matched_records.add(source_key)
                group_values = _group_values(data, str(rule.get("group_by", "")))
                for group_value in group_values:
                    groups.setdefault(group_value, []).append((record, data))
            for group, rows in groups.items():
                detections.append(
                    _build_detection(
                        rule=rule,
                        signature=f"rule:{rule['rule_key']}:{group}",
                        rows=rows,
                        method="engineering_rule",
                    )
                )

        # Preserve every unexplained failure as an engineering-review candidate.
        unknown_groups: dict[str, list[tuple[TestRecord, dict[str, Any]]]] = {}
        for record in records:
            key = record.record_key or record.build_record_key()
            if record.pass_fail.upper() != "FAIL" or key in matched_records:
                continue
            data = record.to_dict()
            signature = _unknown_signature(data)
            unknown_groups.setdefault(signature, []).append((record, data))
        for signature, rows in unknown_groups.items():
            count = len(rows)
            recurring = count >= self.rule_set.recurrence_threshold
            confidence = min(0.85, 0.45 + (0.08 * min(count, 5)))
            detections.append(
                _build_detection(
                    rule={
                        "rule_key": "unknown_signature",
                        "name": "Recurring Unknown Failure" if recurring else "Unknown Failure",
                        "category": "unknown",
                        "severity_level": "high" if recurring else "medium",
                        "confidence": confidence,
                        "explanation": (
                            "Previously unseen signature repeated across source records; "
                            "engineering review required."
                            if recurring
                            else "No active engineering rule matched this failed record."
                        ),
                    },
                    signature=signature,
                    rows=rows,
                    method="unknown_recurring" if recurring else "unknown",
                )
            )
        return detections


def _validate_expression(expression: dict[str, Any]) -> None:
    clauses = expression.get("all") or expression.get("any")
    if not isinstance(clauses, list) or not clauses:
        raise RuleConfigurationError("Each rule match requires a non-empty all/any list")
    for clause in clauses:
        operator = clause.get("operator")
        if operator not in SUPPORTED_OPERATORS:
            raise RuleConfigurationError(f"Unsupported rule operator: {operator}")
        if not str(clause.get("field", "")).strip():
            raise RuleConfigurationError("Rule clause field is required")


def _evaluate(expression: dict[str, Any], data: dict[str, Any]) -> bool:
    clauses = expression.get("all") or expression.get("any") or []
    results = [_evaluate_clause(clause, data) for clause in clauses]
    return all(results) if "all" in expression else any(results)


def _evaluate_clause(clause: dict[str, Any], data: dict[str, Any]) -> bool:
    actual = _get(data, str(clause["field"]))
    operator = clause["operator"]
    expected = clause.get("value")
    if operator == "equals":
        return str(actual).upper() == str(expected).upper()
    if operator == "not_equals":
        return str(actual).upper() != str(expected).upper()
    if operator == "contains":
        return expected in actual if isinstance(actual, (list, str, dict)) else False
    if operator == "in":
        return actual in (expected or [])
    if operator == "not_in":
        return str(actual).upper() not in {str(v).upper() for v in (expected or [])}
    if operator == "not_empty":
        return actual not in (None, "", [], {})
    if operator == "empty":
        return actual in (None, "", [], {})
    if operator == "greater_than":
        return float(actual) > float(expected)
    if operator == "less_than":
        return float(actual) < float(expected)
    if operator == "differs_from":
        return actual != _get(data, str(clause.get("other_field", "")))
    return False


def _get(data: dict[str, Any], dotted: str) -> Any:
    value: Any = data
    for part in dotted.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _group_values(data: dict[str, Any], field: str) -> list[str]:
    value = _get(data, field) if field else None
    if isinstance(value, list):
        return [str(v) for v in value if str(v)] or ["UNSPECIFIED"]
    return [str(value or "UNSPECIFIED")]


def _unknown_signature(data: dict[str, Any]) -> str:
    fields = [
        data.get("test_stage"),
        data.get("hard_bin"),
        data.get("soft_bin"),
        ",".join(sorted(map(str, data.get("failing_tests") or []))),
        str((data.get("scan_fail_data") or {}).get("scan_chain_id", "")),
    ]
    digest = hashlib.sha256("|".join(map(str, fields)).encode()).hexdigest()[:16]
    return f"unknown:{digest}"


def _build_detection(
    *,
    rule: dict[str, Any],
    signature: str,
    rows: list[tuple[TestRecord, dict[str, Any]]],
    method: str,
) -> dict[str, Any]:
    records = [record for record, _ in rows]
    confidence = round(float(rule.get("confidence", 0.0)), 4)
    return {
        "signature": signature,
        "pattern_id": signature.split(":")[-1] or signature,
        "pattern_name": str(rule.get("name", signature)),
        "pattern_category": str(rule.get("category", "unknown")),
        "detection_method": method,
        "severity_level": str(rule.get("severity_level", "medium")),
        "confidence": confidence,
        "rule_key": str(rule.get("rule_key", "")),
        "rule_version": str(rule.get("version", "")),
        "explanation": str(rule.get("explanation", "")),
        "occurrence_count": len(rows),
        "affected_lots": sorted({r.lot_id for r in records if r.lot_id}),
        "affected_wafers": sorted({r.wafer_id for r in records if r.wafer_id}),
        "affected_dies": sorted({r.die_id for r in records if r.die_id}),
        "affected_devices": sorted({r.product_id for r in records if r.product_id}),
        "occurrences": [
            {
                "source_record_id": record.record_key or record.build_record_key(),
                "lot_id": record.lot_id,
                "wafer_id": record.wafer_id,
                "die_id": record.die_id,
                "device_id": record.product_id,
                "x": record.x,
                "y": record.y,
                "evidence": data,
            }
            for record, data in rows
        ],
    }
