"""FA-FR-002: Failing pattern detection with deterministic + inference fallback."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from adapters.schema import TestRecord
from adapters.yaml_config import load_adapter_configs
from ingestor import DieLog, PatternResult

logger = logging.getLogger(__name__)

INFERENCE_CONFIDENCE_THRESHOLD = 0.95
DETERMINISTIC_CONFIDENCE = 1.0


@dataclass
class PatternManifest:
    """Maps failing test numbers/names to ATPG pattern IDs (Pattern Analysis Agent handoff)."""

    test_to_pattern: dict[str, str] = field(default_factory=dict)
    pattern_ids: set[str] = field(default_factory=set)
    source: str = "unknown"

    @classmethod
    def from_yaml(cls, path: Path) -> PatternManifest:
        data = load_adapter_configs(path)
        mappings = data.get("test_to_pattern", {})
        if isinstance(mappings, dict):
            test_to_pattern = {str(k): str(v) for k, v in mappings.items()}
        else:
            test_to_pattern = {}
        pattern_ids = set(data.get("pattern_ids", [])) | set(test_to_pattern.values())
        return cls(
            test_to_pattern=test_to_pattern,
            pattern_ids=pattern_ids,
            source=str(path),
        )

    @classmethod
    def from_stil_metadata(cls, pattern_begin: int, pattern_end: int) -> PatternManifest:
        """Build identity mapping test_num → pattern_id from STIL pattern range."""
        test_to_pattern = {
            str(num): str(num).zfill(6) if num < 1000000 else str(num)
            for num in range(pattern_begin, pattern_end + 1)
        }
        return cls(
            test_to_pattern=test_to_pattern,
            pattern_ids=set(test_to_pattern.values()),
            source="stil_pattern_range",
        )

    def infer_pattern(self, test_key: str) -> tuple[str | None, float, list[str]]:
        key = test_key.strip()
        evidence: list[str] = []
        if not key:
            return None, 0.0, ["empty test key"]

        if key in self.test_to_pattern:
            pattern = self.test_to_pattern[key]
            evidence.append(f"manifest exact match: {key} → {pattern}")
            return pattern, 1.0, evidence

        upper = key.upper()
        for test_name, pattern in self.test_to_pattern.items():
            if test_name.upper() == upper:
                evidence.append(f"manifest case-insensitive match: {key} → {pattern}")
                return pattern, 0.98, evidence

        digits = re.sub(r"\D", "", key)
        if digits and digits in self.test_to_pattern:
            pattern = self.test_to_pattern[digits]
            evidence.append(f"manifest numeric extract: {key} → {digits} → {pattern}")
            return pattern, 0.96, evidence

        if digits and digits.zfill(6) in self.pattern_ids:
            pattern = digits.zfill(6)
            evidence.append(f"pattern_id set membership: {pattern}")
            return pattern, 0.95, evidence

        return None, 0.0, [f"no manifest mapping for test key '{key}'"]


def load_pattern_manifest(
    manifest_path: Path | None = None,
    *,
    stil_pattern_begin: int | None = None,
    stil_pattern_end: int | None = None,
) -> PatternManifest | None:
    if manifest_path and manifest_path.is_file():
        return PatternManifest.from_yaml(manifest_path)
    if stil_pattern_begin is not None and stil_pattern_end is not None:
        return PatternManifest.from_stil_metadata(stil_pattern_begin, stil_pattern_end)
    default = Path(__file__).resolve().parent / "config" / "pattern_manifest.yaml"
    if default.is_file():
        return PatternManifest.from_yaml(default)
    return None


def detect_failing_patterns(
    die_logs: list[DieLog],
    *,
    manifest: PatternManifest | None = None,
    test_records: list[TestRecord] | None = None,
) -> list[dict[str, Any]]:
    """
    Detect all failing patterns per die.

    Deterministic: pattern_id explicitly present in log (confidence 1.0).
    Inferred: map failing_tests / test numbers via pattern manifest when pattern_id absent.
    """
    failures: list[dict[str, Any]] = []
    records_by_die = _index_test_records(test_records)

    for die in die_logs:
        die_key = (die.lot_id, die.wafer_id, die.die_id)
        extra_tests = records_by_die.get(die_key, [])

        if die.failing_patterns:
            for pattern in die.failing_patterns:
                failures.append(
                    _build_failure_record(
                        die,
                        pattern,
                        detection_method="deterministic",
                        confidence=DETERMINISTIC_CONFIDENCE,
                        inference_evidence=["explicit pattern_id in tester log"],
                    )
                )
            continue

        if extra_tests:
            for test_name in extra_tests:
                failures.extend(
                    _infer_failures_from_test(die, test_name, manifest, source="test_record")
                )

    if test_records:
        for record in test_records:
            if record.pass_fail.upper() != "FAIL":
                continue
            die_key = (record.lot_id, record.wafer_id, record.die_id)
            if any(
                f["lot_id"] == record.lot_id
                and f["wafer_id"] == record.wafer_id
                and f["die_id"] == record.die_id
                for f in failures
            ):
                continue
            for pattern_id in record.failing_patterns:
                failures.append(
                    _synthetic_failure_from_pattern(record, pattern_id, "deterministic", 1.0)
                )
            for test_name in record.failing_tests:
                if not record.failing_patterns:
                    die_stub = _die_stub_from_record(record)
                    failures.extend(
                        _infer_failures_from_test(die_stub, test_name, manifest, source="test_record")
                    )

    return failures


def measure_detection_accuracy(
    die_logs: list[DieLog],
    detected_failures: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """FA-FR-002 accuracy: 100% deterministic completeness + inferred precision stats."""
    detected = detected_failures or detect_failing_patterns(die_logs)
    parsed = sum(die.execution_count for die in die_logs)
    expected = sum(die.expected_executions for die in die_logs)
    malformed = sum(die.malformed_blocks for die in die_logs)

    deterministic = [f for f in detected if f.get("detection_method") == "deterministic"]
    inferred = [f for f in detected if f.get("detection_method") == "inferred"]
    inferred_high_conf = [
        f for f in inferred if f.get("confidence", 0) >= INFERENCE_CONFIDENCE_THRESHOLD
    ]

    raw_accuracy = (parsed / expected) if expected else 1.0
    completeness = round(min(raw_accuracy, 1.0), 6)
    inferred_precision = (
        len(inferred_high_conf) / len(inferred) if inferred else 1.0
    )

    return {
        "method": (
            "Deterministic: 100% of explicit FAIL/pattern_id in logs. "
            "Inferred: test→pattern via manifest when pattern_id absent; "
            f"precision target ≥{INFERENCE_CONFIDENCE_THRESHOLD * 100:.0f}% on validation."
        ),
        "parsed_executions": parsed,
        "expected_executions": expected,
        "malformed_blocks": malformed,
        "accuracy": completeness,
        "accuracy_pct": round(completeness * 100, 4),
        "deterministic_failures": len(deterministic),
        "inferred_failures": len(inferred),
        "inferred_high_confidence": len(inferred_high_conf),
        "inferred_precision": round(inferred_precision, 4),
        "inferred_precision_pct": round(inferred_precision * 100, 2),
        "inference_threshold": INFERENCE_CONFIDENCE_THRESHOLD,
        "meets_deterministic_threshold": completeness >= 1.0,
        "meets_inferred_precision": inferred_precision >= INFERENCE_CONFIDENCE_THRESHOLD
        if inferred
        else True,
        "meets_threshold": completeness >= 1.0,
        "threshold": 1.0,
    }


def _index_test_records(
    test_records: list[TestRecord] | None,
) -> dict[tuple[str, str, str], list[str]]:
    index: dict[tuple[str, str, str], list[str]] = {}
    if not test_records:
        return index
    for rec in test_records:
        if rec.pass_fail.upper() != "FAIL":
            continue
        key = (rec.lot_id, rec.wafer_id, rec.die_id)
        index.setdefault(key, []).extend(rec.failing_tests)
    return index


def _build_failure_record(
    die: DieLog,
    pattern: PatternResult,
    *,
    detection_method: Literal["deterministic", "inferred"],
    confidence: float,
    inference_evidence: list[str],
) -> dict[str, Any]:
    return {
        "source_path": die.source_path,
        "device_name": die.device_name,
        "lot_id": die.lot_id,
        "wafer_id": die.wafer_id,
        "die_id": die.die_id,
        "pattern_id": pattern.pattern_id,
        "scan_chain_id": pattern.scan_chain_id,
        "expected_signature": pattern.expected_signature,
        "actual_signature": pattern.actual_signature,
        "status": pattern.status,
        "detection_method": detection_method,
        "confidence": round(confidence, 4),
        "inference_evidence": inference_evidence,
        "is_inferred": detection_method == "inferred",
    }


def _infer_failures_from_test(
    die: DieLog,
    test_name: str,
    manifest: PatternManifest | None,
    *,
    source: str,
) -> list[dict[str, Any]]:
    if manifest is None:
        return [
            _build_failure_record(
                die,
                PatternResult(
                    pattern_id="UNMAPPED",
                    scan_chain_id="",
                    expected_signature="",
                    actual_signature="",
                    status="FAIL",
                    raw_fields={"failing_test": test_name},
                ),
                detection_method="inferred",
                confidence=0.0,
                inference_evidence=[f"no pattern manifest loaded; failing_test={test_name}"],
            )
        ]

    pattern_id, confidence, evidence = manifest.infer_pattern(test_name)
    if pattern_id is None:
        pattern_id = "UNMAPPED"

    return [
        _build_failure_record(
            die,
            PatternResult(
                pattern_id=pattern_id,
                scan_chain_id="",
                expected_signature="",
                actual_signature="",
                status="FAIL",
                raw_fields={"failing_test": test_name, "inference_source": source},
            ),
            detection_method="inferred",
            confidence=confidence,
            inference_evidence=evidence,
        )
    ]


def _synthetic_failure_from_pattern(
    record: TestRecord,
    pattern_id: str,
    method: Literal["deterministic", "inferred"],
    confidence: float,
) -> dict[str, Any]:
    return {
        "source_path": record.source_file,
        "device_name": record.product_id,
        "lot_id": record.lot_id,
        "wafer_id": record.wafer_id,
        "die_id": record.die_id,
        "pattern_id": pattern_id,
        "scan_chain_id": record.scan_fail_data.get("scan_chain_id", ""),
        "expected_signature": str(record.scan_fail_data.get("expected", "")),
        "actual_signature": str(record.scan_fail_data.get("actual", "")),
        "status": "FAIL",
        "detection_method": method,
        "confidence": confidence,
        "inference_evidence": ["explicit failing_patterns in test_record"],
        "is_inferred": method == "inferred",
    }


def _die_stub_from_record(record: TestRecord) -> DieLog:
    return DieLog(
        source_path=record.source_file,
        tester_name=record.tester_id,
        device_name=record.product_id,
        lot_id=record.lot_id,
        wafer_id=record.wafer_id,
        die_id=record.die_id,
        header_fields=record.raw_fields,
    )


def export_detection_report(failures: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump({"failures": failures, "count": len(failures)}, handle, indent=2)
