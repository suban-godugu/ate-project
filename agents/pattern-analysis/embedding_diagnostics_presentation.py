"""
PA-FR-005 Embedding Diagnostics Presentation — additive UI support layer.

Reads existing embedding artifacts and validation results only.
Does not modify validation logic, embedding generation, or on-disk outputs.
"""
from __future__ import annotations

import json
import math
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from pattern_embedding import (
    ALGORITHM_NAME,
    EMBEDDINGS_FILENAME,
    MANIFEST_FILENAME,
    SIMILARITY_METRIC,
)

HISTOGRAM_BIN_COUNT = 12
ALGORITHM_DISPLAY_NAME = "Hybrid v1.0"
NORMALIZATION_METHOD = "Min-Max"
SIMILARITY_DISPLAY_NAME = "Cosine Similarity"


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _format_validation_timestamp(timestamp_utc: datetime) -> Dict[str, str]:
    display = timestamp_utc.strftime("%d-%b-%Y\n%H:%M UTC")
    return {
        "iso": timestamp_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "display": display,
    }


def _compute_embedding_statistics(embeddings: List[Dict[str, Any]]) -> Dict[str, Any]:
    values: List[float] = []
    zero_vectors = 0
    nan_count = 0
    infinity_count = 0

    for record in embeddings:
        vector = record.get("embedding", [])
        if not isinstance(vector, list):
            continue

        vector_values: List[float] = []
        vector_has_nan = False
        vector_has_infinity = False

        for raw in vector:
            if raw is None:
                nan_count += 1
                vector_has_nan = True
                continue
            if not isinstance(raw, (int, float)):
                nan_count += 1
                vector_has_nan = True
                continue
            value = float(raw)
            if math.isnan(value):
                nan_count += 1
                vector_has_nan = True
                continue
            if math.isinf(value):
                infinity_count += 1
                vector_has_infinity = True
                continue
            vector_values.append(value)
            values.append(value)

        if vector_values and all(value == 0.0 for value in vector_values):
            zero_vectors += 1
        if vector_has_nan or vector_has_infinity:
            continue

    if values:
        average_value = sum(values) / len(values)
        minimum_value = min(values)
        maximum_value = max(values)
    else:
        average_value = 0.0
        minimum_value = 0.0
        maximum_value = 0.0

    return {
        "average_value": round(average_value, 3),
        "minimum_value": round(minimum_value, 3),
        "maximum_value": round(maximum_value, 3),
        "zero_vectors": zero_vectors,
        "nan_count": nan_count,
        "infinity_count": infinity_count,
        "value_count": len(values),
    }


def _compute_distribution(embeddings: List[Dict[str, Any]], bin_count: int = HISTOGRAM_BIN_COUNT) -> Dict[str, Any]:
    values: List[float] = []
    for record in embeddings:
        vector = record.get("embedding", [])
        if not isinstance(vector, list):
            continue
        for raw in vector:
            if isinstance(raw, (int, float)) and math.isfinite(float(raw)):
                values.append(float(raw))

    if not values:
        return {
            "bin_count": bin_count,
            "bins": [],
            "counts": [],
            "max_count": 0,
        }

    minimum = min(values)
    maximum = max(values)
    if minimum == maximum:
        counts = [len(values)] + [0] * (bin_count - 1)
        return {
            "bin_count": bin_count,
            "minimum": minimum,
            "maximum": maximum,
            "bins": [minimum, maximum],
            "counts": counts,
            "max_count": len(values),
        }

    span = maximum - minimum
    step = span / bin_count
    counts = [0] * bin_count
    for value in values:
        index = min(int((value - minimum) / step), bin_count - 1)
        counts[index] += 1

    bins = [round(minimum + step * index, 3) for index in range(bin_count + 1)]
    return {
        "bin_count": bin_count,
        "minimum": round(minimum, 3),
        "maximum": round(maximum, 3),
        "bins": bins,
        "counts": counts,
        "max_count": max(counts),
    }


def _build_manifest_panel(manifest: Optional[Dict[str, Any]], payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    source = manifest or payload or {}
    similarity = source.get("similarity_metric", SIMILARITY_METRIC)
    similarity_display = SIMILARITY_DISPLAY_NAME
    if isinstance(similarity, str) and similarity.lower() != "cosine":
        similarity_display = similarity.replace("_", " ").title()

    return {
        "algorithm": source.get("algorithm", ALGORITHM_NAME),
        "algorithm_display_name": ALGORITHM_DISPLAY_NAME,
        "embedding_version": source.get("embedding_version", "1.0"),
        "embedding_dimension": source.get("embedding_dimension", 128),
        "similarity_metric": similarity,
        "similarity_metric_display": similarity_display,
        "normalization": NORMALIZATION_METHOD,
        "generated_by": (payload or {}).get("generated_by", "PA-FR-005"),
        "feature_version": source.get("feature_version", "1.0"),
    }


def _derive_check_details(
    check: Dict[str, str],
    patterns_checked: int,
    summary: Dict[str, Any],
    statistics: Dict[str, Any],
) -> Dict[str, Any]:
    name = check.get("name", "")
    status = check.get("status", "")
    failures = 0
    checked = patterns_checked

    if name == "Embedding Dimension":
        failures = 0 if status == "PASS" else max(patterns_checked, 0)
        if status == "FAIL" and "embedding(s)" in check.get("message", ""):
            try:
                failures = int(check["message"].split(" ")[0])
            except (ValueError, IndexError):
                failures = patterns_checked
    elif name == "Duplicate Pattern IDs":
        failures = int(summary.get("duplicate_pattern_ids", 0) or 0)
        checked = patterns_checked
    elif name == "Missing Embeddings":
        failures = 0 if status == "PASS" else 1
    elif name == "NaN Check":
        failures = int(statistics.get("nan_count", 0) or 0) + int(statistics.get("infinity_count", 0) or 0)
        if status == "FAIL" and failures == 0:
            try:
                failures = int(check.get("message", "").split(" ")[1])
            except (ValueError, IndexError):
                failures = 1
    elif name == "Normalization Check":
        failures = 0 if status == "PASS" else 1
        if status == "WARNING" and "embedding(s)" in check.get("message", ""):
            try:
                failures = int(check["message"].split(" ")[0])
            except (ValueError, IndexError):
                failures = 1
    elif name in ("JSON Schema Validation", "Manifest Validation", "Embeddings File"):
        failures = 0 if status == "PASS" else 1
        checked = 1
    else:
        failures = 0 if status == "PASS" else 1

    execution_time = "Not Available"

    return {
        "checked": checked,
        "checked_label": f"{checked} embeddings" if checked != 1 else "1 embedding",
        "failures": failures,
        "execution_time": execution_time,
    }


def enrich_validation_presentation(
    validation_report: Dict[str, Any],
    output_dir: str,
    validation_started_at: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Append presentation-only diagnostics to an existing validation report.
    The original validation report fields remain unchanged.
    """
    enriched = dict(validation_report)
    validation_completed_at = time.time()
    timestamp_utc = datetime.fromtimestamp(
        validation_started_at or validation_completed_at,
        tz=timezone.utc,
    )
    validation_duration_ms = None
    if validation_started_at is not None:
        validation_duration_ms = (validation_completed_at - validation_started_at) * 1000.0

    embeddings_path = os.path.join(output_dir, EMBEDDINGS_FILENAME)
    manifest_path = os.path.join(output_dir, MANIFEST_FILENAME)

    payload: Optional[Dict[str, Any]] = None
    manifest: Optional[Dict[str, Any]] = None
    embeddings: List[Dict[str, Any]] = []

    if os.path.exists(embeddings_path):
        payload = _load_json(embeddings_path)
        embeddings = payload.get("embeddings", []) if isinstance(payload.get("embeddings"), list) else []

    if os.path.exists(manifest_path):
        manifest = _load_json(manifest_path)

    statistics = _compute_embedding_statistics(embeddings)
    distribution = _compute_distribution(embeddings)
    manifest_panel = _build_manifest_panel(manifest, payload)
    summary = validation_report.get("summary", {})
    patterns_checked = int(validation_report.get("patterns_checked", 0) or 0)

    check_details: Dict[str, Dict[str, Any]] = {}
    for check in validation_report.get("checks", []):
        if not isinstance(check, dict):
            continue
        check_name = check.get("name", "")
        check_details[check_name] = _derive_check_details(
            check,
            patterns_checked,
            summary,
            statistics,
        )

    statistics_panel = {
        **statistics,
        "dimension": validation_report.get("dimension", manifest_panel.get("embedding_dimension", 128)),
        "embedding_version": validation_report.get("embedding_version", manifest_panel.get("embedding_version")),
        "algorithm": validation_report.get("algorithm", manifest_panel.get("algorithm")),
        "similarity_metric": manifest_panel.get("similarity_metric_display"),
        "normalization_method": NORMALIZATION_METHOD,
        "generated_by": manifest_panel.get("generated_by", "PA-FR-005"),
    }

    enriched["presentation"] = {
        "validation_timestamp": _format_validation_timestamp(timestamp_utc),
        "validation_duration_ms": round(validation_duration_ms, 1) if validation_duration_ms is not None else None,
        "statistics": statistics_panel,
        "statistics_summary": {
            "average_value": statistics_panel["average_value"],
            "minimum_value": statistics_panel["minimum_value"],
            "maximum_value": statistics_panel["maximum_value"],
            "zero_vectors": statistics_panel["zero_vectors"],
            "nan_count": statistics_panel["nan_count"],
            "infinity_count": statistics_panel["infinity_count"],
        },
        "distribution": distribution,
        "manifest_panel": manifest_panel,
        "manifest_summary": manifest_panel,
        "check_details": check_details,
    }
    return enriched
