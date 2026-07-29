"""
PA-FR-005 Embedding Validation & Diagnostics — read-only verification layer.

Inspects existing PA-FR-005 outputs only. Does not regenerate embeddings or
modify embedding algorithms, JSON schemas, or deterministic behavior.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from typing import Any, Dict, List, Optional, Tuple

from pattern_embedding import (
    ALGORITHM_NAME,
    EMBEDDING_DIMENSION,
    EMBEDDING_VERSION,
    EMBEDDINGS_FILENAME,
    FEATURE_VERSION,
    LOG_FILENAME,
    MANIFEST_FILENAME,
    PART2_DIMENSION,
)

VALIDATION_FILENAME = "PA-FR-005_embedding_validation.json"

EXPECTED_EMBEDDINGS_FIELDS: Dict[str, type] = {
    "generated_by": str,
    "embedding_version": str,
    "embedding_dimension": int,
    "algorithm": str,
    "similarity_metric": str,
    "patterns_embedded": int,
    "patterns_skipped": int,
    "embeddings": list,
}

EXPECTED_EMBEDDING_RECORD_FIELDS: Dict[str, type] = {
    "pattern_id": str,
    "embedding": list,
    "source_file": str,
    "feature_version": str,
    "created_timestamp": str,
}

MANIFEST_REQUIRED_FIELDS = (
    "embedding_version",
    "algorithm",
    "embedding_dimension",
    "feature_version",
)


def _check_status(statuses: List[str]) -> str:
    if any(status == "FAIL" for status in statuses):
        return "FAIL"
    if any(status == "WARNING" for status in statuses):
        return "WARNING"
    return "PASS"


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _append_validation_log(output_dir: str, report: Dict[str, Any]) -> None:
    log_path = os.path.join(output_dir, LOG_FILENAME)
    if not os.path.exists(log_path):
        return

    checks = report.get("checks", [])
    passed = sum(1 for item in checks if item.get("status") == "PASS")
    warnings = sum(1 for item in checks if item.get("status") == "WARNING")
    failed = sum(1 for item in checks if item.get("status") == "FAIL")

    lines = [
        "",
        "Embedding Validation",
        f"Validation Status: {report.get('validation_status', 'UNKNOWN')}",
        f"Total Checks: {len(checks)}",
        f"Passed: {passed}",
        f"Warnings: {warnings}",
        f"Failed: {failed}",
        f"SHA-256: {report.get('sha256', '')}",
    ]

    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def _validate_schema(payload: Dict[str, Any]) -> Tuple[str, str]:
    missing_top_level = [
        key for key, expected_type in EXPECTED_EMBEDDINGS_FIELDS.items()
        if key not in payload or not isinstance(payload[key], expected_type)
    ]
    if missing_top_level:
        return "FAIL", f"Missing or invalid top-level fields: {', '.join(missing_top_level)}."

    if payload.get("generated_by") != "PA-FR-005":
        return "FAIL", "generated_by must be PA-FR-005."

    embeddings = payload.get("embeddings", [])
    if not isinstance(embeddings, list):
        return "FAIL", "Embeddings collection is not a list."

    for index, record in enumerate(embeddings):
        if not isinstance(record, dict):
            return "FAIL", f"Embedding record at index {index} is not an object."
        missing_record = [
            key for key, expected_type in EXPECTED_EMBEDDING_RECORD_FIELDS.items()
            if key not in record or not isinstance(record[key], expected_type)
        ]
        if missing_record:
            return "FAIL", (
                f"Embedding record at index {index} missing or invalid fields: "
                f"{', '.join(missing_record)}."
            )

    return "PASS", "PA-FR-005_pattern_embeddings.json matches the expected schema."


def validate_pattern_embeddings(output_dir: str) -> Dict[str, Any]:
    """
    Read-only validation of existing PA-FR-005 embedding artifacts.
    Writes PA-FR-005_embedding_validation.json and appends diagnostics to the log.
    """
    os.makedirs(output_dir, exist_ok=True)

    embeddings_path = os.path.join(output_dir, EMBEDDINGS_FILENAME)
    manifest_path = os.path.join(output_dir, MANIFEST_FILENAME)
    validation_path = os.path.join(output_dir, VALIDATION_FILENAME)

    checks: List[Dict[str, str]] = []
    sha256 = ""

    if not os.path.exists(embeddings_path):
        checks.append(
            {
                "name": "Embeddings File",
                "status": "FAIL",
                "message": f"{EMBEDDINGS_FILENAME} not found.",
            }
        )
        report = {
            "generated_by": "PA-FR-005",
            "validation_status": "FAIL",
            "patterns_checked": 0,
            "dimension": EMBEDDING_DIMENSION,
            "embedding_version": EMBEDDING_VERSION,
            "algorithm": ALGORITHM_NAME,
            "sha256": sha256,
            "summary": {
                "embeddings_verified": "0 / 0",
                "dimension_check": "FAIL",
                "duplicate_pattern_ids": 0,
                "embedding_version": EMBEDDING_VERSION,
                "validation_status": "FAIL",
                "embedding_hash": "",
            },
            "checks": checks,
            "output_files": {"validation_json": validation_path},
        }
        _write_json(validation_path, report)
        _append_validation_log(output_dir, report)
        return report

    sha256 = _sha256_file(embeddings_path)
    payload = _load_json(embeddings_path)
    embeddings = payload.get("embeddings", [])
    patterns_checked = len(embeddings)

    # Rule 1 — Embedding Dimension
    invalid_lengths = [
        item.get("pattern_id", f"index_{index}")
        for index, item in enumerate(embeddings)
        if not isinstance(item.get("embedding"), list) or len(item["embedding"]) != EMBEDDING_DIMENSION
    ]
    if invalid_lengths:
        checks.append(
            {
                "name": "Embedding Dimension",
                "status": "FAIL",
                "message": (
                    f"{len(invalid_lengths)} embedding(s) do not contain exactly "
                    f"{EMBEDDING_DIMENSION} values."
                ),
            }
        )
        dimension_check = "FAIL"
    else:
        checks.append(
            {
                "name": "Embedding Dimension",
                "status": "PASS",
                "message": f"All embeddings contain {EMBEDDING_DIMENSION} values.",
            }
        )
        dimension_check = "PASS"

    # Rule 2 — Duplicate Pattern IDs
    pattern_ids = [item.get("pattern_id") for item in embeddings if isinstance(item, dict)]
    duplicates = len(pattern_ids) - len(set(pattern_ids))
    if duplicates > 0:
        checks.append(
            {
                "name": "Duplicate Pattern IDs",
                "status": "FAIL",
                "message": f"Found {duplicates} duplicate pattern_id value(s).",
            }
        )
    else:
        checks.append(
            {
                "name": "Duplicate Pattern IDs",
                "status": "PASS",
                "message": "No duplicates found.",
            }
        )

    # Rule 3 — Embedding Version Consistency
    versions = {payload.get("embedding_version")}
    if os.path.exists(manifest_path):
        manifest = _load_json(manifest_path)
        versions.add(manifest.get("embedding_version"))
    versions.discard(None)
    if len(versions) == 0:
        checks.append(
            {
                "name": "Embedding Version Consistency",
                "status": "FAIL",
                "message": "No embedding_version found.",
            }
        )
        embedding_version = EMBEDDING_VERSION
    elif len(versions) == 1 and next(iter(versions)) == EMBEDDING_VERSION:
        checks.append(
            {
                "name": "Embedding Version Consistency",
                "status": "PASS",
                "message": f"All sources report embedding_version {EMBEDDING_VERSION}.",
            }
        )
        embedding_version = next(iter(versions))
    elif len(versions) == 1:
        checks.append(
            {
                "name": "Embedding Version Consistency",
                "status": "WARNING",
                "message": f"Unexpected embedding_version {next(iter(versions))} found.",
            }
        )
        embedding_version = next(iter(versions))
    else:
        checks.append(
            {
                "name": "Embedding Version Consistency",
                "status": "WARNING",
                "message": f"Multiple embedding versions found: {', '.join(sorted(versions))}.",
            }
        )
        embedding_version = payload.get("embedding_version", EMBEDDING_VERSION)

    # Rule 4 — Embedding Dimension Consistency
    declared_dimension = payload.get("embedding_dimension")
    if declared_dimension != EMBEDDING_DIMENSION:
        checks.append(
            {
                "name": "Embedding Dimension Consistency",
                "status": "FAIL",
                "message": (
                    f"embedding_dimension is {declared_dimension}, expected {EMBEDDING_DIMENSION}."
                ),
            }
        )
    else:
        checks.append(
            {
                "name": "Embedding Dimension Consistency",
                "status": "PASS",
                "message": f"embedding_dimension equals {EMBEDDING_DIMENSION}.",
            }
        )

    # Rule 5 — Algorithm Consistency
    algorithm = payload.get("algorithm")
    manifest_algorithm: Optional[str] = None
    if os.path.exists(manifest_path):
        manifest_algorithm = _load_json(manifest_path).get("algorithm")
    algorithm_values = {value for value in (algorithm, manifest_algorithm) if value}
    if algorithm_values == {ALGORITHM_NAME}:
        checks.append(
            {
                "name": "Algorithm Consistency",
                "status": "PASS",
                "message": f"All records use {ALGORITHM_NAME}.",
            }
        )
    elif len(algorithm_values) == 0:
        checks.append(
            {
                "name": "Algorithm Consistency",
                "status": "FAIL",
                "message": "Algorithm field is missing.",
            }
        )
    else:
        checks.append(
            {
                "name": "Algorithm Consistency",
                "status": "FAIL",
                "message": f"Expected {ALGORITHM_NAME}; found {', '.join(sorted(algorithm_values))}.",
            }
        )

    # Rule 6 — Missing Embeddings
    patterns_embedded = payload.get("patterns_embedded")
    embeddings_generated = len(embeddings)
    if patterns_embedded != embeddings_generated:
        checks.append(
            {
                "name": "Missing Embeddings",
                "status": "FAIL",
                "message": (
                    f"patterns_embedded ({patterns_embedded}) does not equal "
                    f"embeddings generated ({embeddings_generated})."
                ),
            }
        )
    else:
        checks.append(
            {
                "name": "Missing Embeddings",
                "status": "PASS",
                "message": (
                    f"patterns_embedded ({patterns_embedded}) equals "
                    f"embeddings generated ({embeddings_generated})."
                ),
            }
        )

    # Rule 7 — NaN Check
    invalid_values = 0
    for item in embeddings:
        vector = item.get("embedding", [])
        if not isinstance(vector, list):
            invalid_values += 1
            continue
        for value in vector:
            if value is None or not isinstance(value, (int, float)):
                invalid_values += 1
                break
            if not math.isfinite(float(value)):
                invalid_values += 1
                break
    if invalid_values > 0:
        checks.append(
            {
                "name": "NaN Check",
                "status": "FAIL",
                "message": f"Found {invalid_values} embedding(s) with NaN, Infinity, or null values.",
            }
        )
    else:
        checks.append(
            {
                "name": "NaN Check",
                "status": "PASS",
                "message": "No invalid floating-point values.",
            }
        )

    # Rule 8 — Normalization Check (Part 2 metadata-derived values)
    out_of_range = 0
    part2_start = EMBEDDING_DIMENSION - PART2_DIMENSION
    for item in embeddings:
        vector = item.get("embedding", [])
        if not isinstance(vector, list) or len(vector) < EMBEDDING_DIMENSION:
            continue
        for value in vector[part2_start:]:
            if not isinstance(value, (int, float)):
                out_of_range += 1
                break
            if float(value) < 0.0 or float(value) > 1.0:
                out_of_range += 1
                break
    if out_of_range > 0:
        checks.append(
            {
                "name": "Normalization Check",
                "status": "WARNING",
                "message": (
                    f"{out_of_range} embedding(s) contain metadata-derived values outside 0.0–1.0."
                ),
            }
        )
    else:
        checks.append(
            {
                "name": "Normalization Check",
                "status": "PASS",
                "message": "All metadata-derived values lie within 0.0 through 1.0.",
            }
        )

    # Rule 9 — JSON Schema Validation
    schema_status, schema_message = _validate_schema(payload)
    checks.append(
        {
            "name": "JSON Schema Validation",
            "status": schema_status,
            "message": schema_message,
        }
    )

    # Rule 10 — Manifest Validation
    if not os.path.exists(manifest_path):
        checks.append(
            {
                "name": "Manifest Validation",
                "status": "FAIL",
                "message": f"{MANIFEST_FILENAME} not found.",
            }
        )
    else:
        manifest = _load_json(manifest_path)
        missing_manifest = [field for field in MANIFEST_REQUIRED_FIELDS if field not in manifest]
        if missing_manifest:
            checks.append(
                {
                    "name": "Manifest Validation",
                    "status": "FAIL",
                    "message": f"Missing manifest fields: {', '.join(missing_manifest)}.",
                }
            )
        else:
            checks.append(
                {
                    "name": "Manifest Validation",
                    "status": "PASS",
                    "message": "Metadata complete.",
                }
            )

    validation_status = _check_status([item["status"] for item in checks])
    patterns_embedded_value = patterns_embedded if isinstance(patterns_embedded, int) else patterns_checked
    verified_count = embeddings_generated if validation_status != "FAIL" else min(embeddings_generated, patterns_embedded_value)
    verified_display = f"{verified_count} / {patterns_embedded_value}"

    export_checks = [{"name": item["name"], "status": item["status"]} for item in checks]

    report = {
        "generated_by": "PA-FR-005",
        "validation_status": validation_status,
        "patterns_checked": patterns_checked,
        "dimension": EMBEDDING_DIMENSION,
        "embedding_version": embedding_version,
        "algorithm": ALGORITHM_NAME,
        "feature_version": FEATURE_VERSION,
        "sha256": sha256,
        "summary": {
            "embeddings_verified": verified_display,
            "dimension_check": dimension_check,
            "duplicate_pattern_ids": duplicates,
            "embedding_version": embedding_version,
            "validation_status": validation_status,
            "embedding_hash": f"{sha256[:8]}..." if sha256 else "",
        },
        "checks": checks,
        "export_checks": export_checks,
        "output_files": {"validation_json": validation_path},
    }

    export_payload = {
        "generated_by": report["generated_by"],
        "validation_status": report["validation_status"],
        "patterns_checked": report["patterns_checked"],
        "dimension": report["dimension"],
        "embedding_version": report["embedding_version"],
        "algorithm": report["algorithm"],
        "sha256": report["sha256"],
        "checks": export_checks,
    }
    _write_json(validation_path, export_payload)
    _append_validation_log(output_dir, report)
    return report
