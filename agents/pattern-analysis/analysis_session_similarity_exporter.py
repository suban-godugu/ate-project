"""
PA-FR-008.AS — deterministic Analysis Session similarity artifact.

The exporter consumes an already-built Analysis Session embeddings payload and
manifest. It does not invoke an analysis engine, rebuild embeddings, or mutate
any deterministic source artifact.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from similarity_config import SimilarityConfig, load_similarity_config
from robustness_config import load_robustness_config, lot_from_relpath


GENERATED_BY = "PA-FR-008.AS"
ARTIFACT_VERSION = "1.0"
DEFAULT_TOP_N = 10
DEFAULT_BLOCK_SIZE = 256
DEFAULT_SIMILARITY_THRESHOLD = 0.98
EMBEDDINGS_FILENAME = "PA-Analysis-Session_embeddings.json"


class AnalysisSessionSimilarityError(ValueError):
    """Raised when deterministic session similarity cannot be exported."""


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _model_hash(payload: Mapping[str, Any]) -> str:
    canonical = copy.deepcopy(dict(payload))
    canonical.pop("model_hash", None)
    return _canonical_sha256(canonical)


def _unit_id(row: Mapping[str, Any]) -> str:
    pattern_id = str(row.get("pattern_id") or "").strip()
    source = str(
        row.get("source_log_relpath") or row.get("source_log") or ""
    ).strip()
    return f"{pattern_id}::{source}"


def _source_lot(
    row: Mapping[str, Any],
    robustness_cfg: Optional[object] = None,
) -> str:
    source = str(
        row.get("source_log_relpath") or row.get("source_log") or ""
    ).replace("\\", "/")
    return lot_from_relpath(source, config=robustness_cfg)


def _resolve_config_path(
    workspace_dir: Optional[str],
    config_path: Optional[str],
) -> str:
    if config_path:
        return config_path
    if workspace_dir:
        candidate = os.path.join(workspace_dir, "config", "similarity.yaml")
        if os.path.exists(candidate):
            return candidate
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "config",
        "similarity.yaml",
    )


def _high_similarity_threshold(config: SimilarityConfig) -> float:
    for category in config.categories_descending:
        if category.key == "very_high":
            return float(category.min_threshold)
    positive = [
        float(category.min_threshold)
        for category in config.categories_descending
        if 0.0 < float(category.min_threshold) < 1.0
    ]
    return max(positive) if positive else DEFAULT_SIMILARITY_THRESHOLD


def _validate_inputs(
    embeddings_payload: Mapping[str, Any],
    manifest: Mapping[str, Any],
) -> Tuple[List[Dict[str, Any]], np.ndarray, str, int]:
    if not isinstance(embeddings_payload, Mapping):
        raise AnalysisSessionSimilarityError(
            "Analysis Session embeddings payload is missing or invalid."
        )
    if not isinstance(manifest, Mapping):
        raise AnalysisSessionSimilarityError(
            "Analysis Session manifest is missing or invalid."
        )

    raw_rows = embeddings_payload.get("embeddings")
    if not isinstance(raw_rows, list) or not raw_rows:
        raise AnalysisSessionSimilarityError(
            "Analysis Session embeddings contain no usable rows."
        )

    embedding_version = str(
        embeddings_payload.get("embedding_version") or ""
    ).strip()
    try:
        embedding_dimension = int(
            embeddings_payload.get("embedding_dimension")
        )
    except (TypeError, ValueError) as exc:
        raise AnalysisSessionSimilarityError(
            "Analysis Session embedding_dimension is invalid."
        ) from exc
    if not embedding_version or embedding_dimension < 1:
        raise AnalysisSessionSimilarityError(
            "Analysis Session embedding metadata is incomplete."
        )
    if str(embeddings_payload.get("similarity_metric") or "").lower() != "cosine":
        raise AnalysisSessionSimilarityError(
            "Analysis Session similarity requires cosine embeddings."
        )
    if not str(manifest.get("session_hash") or "").strip():
        raise AnalysisSessionSimilarityError(
            "Analysis Session manifest session_hash is required."
        )
    if not str(manifest.get("generated_timestamp") or "").strip():
        raise AnalysisSessionSimilarityError(
            "Analysis Session manifest generated_timestamp is required."
        )

    rows: List[Dict[str, Any]] = []
    seen_units = set()
    for raw_row in raw_rows:
        if not isinstance(raw_row, Mapping):
            raise AnalysisSessionSimilarityError(
                "Analysis Session embedding row must be an object."
            )
        row = dict(raw_row)
        pattern_id = str(row.get("pattern_id") or "").strip()
        uid = _unit_id(row)
        if not pattern_id or uid.endswith("::"):
            raise AnalysisSessionSimilarityError(
                "Analysis Session embedding row has no deterministic unit ID."
            )
        if uid in seen_units:
            raise AnalysisSessionSimilarityError(
                f"Duplicate Analysis Session embedding unit ID: {uid}"
            )
        seen_units.add(uid)

        vector = row.get("embedding")
        if not isinstance(vector, list) or len(vector) != embedding_dimension:
            raise AnalysisSessionSimilarityError(
                f"Embedding unit '{uid}' has an invalid vector dimension."
            )
        try:
            numeric = [float(value) for value in vector]
        except (TypeError, ValueError) as exc:
            raise AnalysisSessionSimilarityError(
                f"Embedding unit '{uid}' contains non-numeric values."
            ) from exc
        if not all(math.isfinite(value) for value in numeric):
            raise AnalysisSessionSimilarityError(
                f"Embedding unit '{uid}' contains non-finite values."
            )

        row["_unit_id"] = uid
        row["_numeric_embedding"] = numeric
        rows.append(row)

    rows.sort(key=lambda row: str(row["_unit_id"]))
    matrix = np.asarray(
        [row["_numeric_embedding"] for row in rows],
        dtype=np.float64,
    )
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    normalized = np.divide(
        matrix,
        norms,
        out=np.zeros_like(matrix),
        where=norms != 0.0,
    )
    return rows, normalized, embedding_version, embedding_dimension


def _select_top_indices(
    scores: np.ndarray,
    count: int,
) -> List[int]:
    """Return exact top indices, breaking rounded-score ties by unit order."""
    if count <= 0:
        return []
    if count >= scores.size:
        candidates = np.flatnonzero(np.isfinite(scores))
        return sorted(
            (int(index) for index in candidates),
            key=lambda index: (-float(scores[index]), index),
        )

    finite = np.flatnonzero(np.isfinite(scores))
    if finite.size <= count:
        return sorted(
            (int(index) for index in finite),
            key=lambda index: (-float(scores[index]), index),
        )

    finite_scores = scores[finite]
    boundary = float(
        np.partition(finite_scores, finite_scores.size - count)[
            finite_scores.size - count
        ]
    )
    higher = finite[finite_scores > boundary]
    higher_ordered = sorted(
        (int(index) for index in higher),
        key=lambda index: (-float(scores[index]), index),
    )
    remaining = count - len(higher_ordered)
    equals = finite[finite_scores == boundary]
    equal_ordered = sorted(int(index) for index in equals)
    return higher_ordered + equal_ordered[:remaining]


def _distribution(similarities: Sequence[float]) -> Dict[str, int]:
    buckets = {
        "-1.00-0.00": 0,
        "0.00-0.90": 0,
        "0.90-0.95": 0,
        "0.95-0.98": 0,
        "0.98-1.00": 0,
    }
    for score in similarities:
        if score < 0.0:
            buckets["-1.00-0.00"] += 1
        elif score < 0.90:
            buckets["0.00-0.90"] += 1
        elif score < 0.95:
            buckets["0.90-0.95"] += 1
        elif score < 0.98:
            buckets["0.95-0.98"] += 1
        else:
            buckets["0.98-1.00"] += 1
    return buckets


def _pattern_averages(
    rows: Sequence[Mapping[str, Any]],
    pairs: Sequence[Mapping[str, Any]],
) -> Dict[str, float]:
    scores: Dict[str, List[float]] = {}
    pattern_by_unit = {
        str(row["_unit_id"]): str(row.get("pattern_id") or "")
        for row in rows
    }
    for pair in pairs:
        pattern_id = pattern_by_unit.get(str(pair.get("unit_a")), "")
        if pattern_id:
            scores.setdefault(pattern_id, []).append(
                float(pair["cosine_similarity"])
            )
    return {
        pattern_id: round(sum(values) / len(values), 6)
        for pattern_id, values in sorted(scores.items())
        if values
    }


def build_analysis_session_similarity(
    *,
    embeddings_payload: Mapping[str, Any],
    manifest: Mapping[str, Any],
    workspace_dir: Optional[str] = None,
    config_path: Optional[str] = None,
    block_size: int = DEFAULT_BLOCK_SIZE,
) -> Dict[str, Any]:
    """Build an exact, deterministic, bounded session similarity artifact."""
    if block_size < 1:
        raise AnalysisSessionSimilarityError("block_size must be at least 1.")

    config = load_similarity_config(
        _resolve_config_path(workspace_dir, config_path)
    )
    robustness_cfg = (
        load_robustness_config(workspace_dir) if workspace_dir else None
    )
    if config.metric != "cosine":
        raise AnalysisSessionSimilarityError(
            "Analysis Session similarity supports cosine only."
        )
    rows, normalized, embedding_version, embedding_dimension = _validate_inputs(
        embeddings_payload,
        manifest,
    )

    unit_count = len(rows)
    requested_top_n = int(config.default_top_n or DEFAULT_TOP_N)
    effective_top_n = min(requested_top_n, max(0, unit_count - 1))
    precision = int(config.display_precision)
    threshold = _high_similarity_threshold(config)
    pairs: List[Dict[str, Any]] = []

    for block_start in range(0, unit_count, block_size):
        block_end = min(block_start + block_size, unit_count)
        score_block = normalized[block_start:block_end] @ normalized.T
        score_block = np.clip(score_block, -1.0, 1.0)
        score_block = np.round(score_block, precision)
        for local_index in range(block_end - block_start):
            row_index = block_start + local_index
            scores = score_block[local_index]
            scores[row_index] = -np.inf
            selected = _select_top_indices(scores, effective_top_n)
            left = rows[row_index]
            for rank, right_index in enumerate(selected, start=1):
                right = rows[right_index]
                pairs.append(
                    {
                        "unit_a": left["_unit_id"],
                        "unit_b": right["_unit_id"],
                        "pattern_a": str(left.get("pattern_id") or ""),
                        "pattern_b": str(right.get("pattern_id") or ""),
                        "source_log_a": str(left.get("source_log") or ""),
                        "source_log_b": str(right.get("source_log") or ""),
                        "source_log_relpath_a": str(
                            left.get("source_log_relpath") or ""
                        ),
                        "source_log_relpath_b": str(
                            right.get("source_log_relpath") or ""
                        ),
                        "source_lot_a": _source_lot(left, robustness_cfg=robustness_cfg),
                        "source_lot_b": _source_lot(right, robustness_cfg=robustness_cfg),
                        "rank": rank,
                        "cosine_similarity": float(scores[right_index]),
                    }
                )

    pairs.sort(
        key=lambda pair: (
            str(pair["unit_a"]),
            int(pair["rank"]),
            str(pair["unit_b"]),
        )
    )
    similarities = [float(pair["cosine_similarity"]) for pair in pairs]
    pattern_averages = _pattern_averages(rows, pairs)
    stable_patterns = sorted(
        (
            {
                "pattern_id": pattern_id,
                "average_similarity": average,
            }
            for pattern_id, average in pattern_averages.items()
            if average >= threshold
        ),
        key=lambda item: (
            -float(item["average_similarity"]),
            str(item["pattern_id"]),
        ),
    )
    divergent_patterns = sorted(
        (
            {
                "pattern_id": pattern_id,
                "average_similarity": average,
            }
            for pattern_id, average in pattern_averages.items()
            if average < threshold
        ),
        key=lambda item: (
            float(item["average_similarity"]),
            str(item["pattern_id"]),
        ),
    )

    warnings: List[str] = []
    if unit_count < 2:
        warnings.append(
            "Fewer than two embedding units; no similarity pairs were produced."
        )
    validation_status = "Complete" if not warnings else "Partial"
    embedding_rows = embeddings_payload.get("embeddings") or []
    provenance_timestamp = embeddings_payload.get("generated_timestamp")
    if provenance_timestamp is None and embedding_rows:
        first = embedding_rows[0]
        if isinstance(first, Mapping):
            provenance_timestamp = first.get("created_timestamp")

    artifact: Dict[str, Any] = {
        "generated_by": GENERATED_BY,
        "artifact_version": ARTIFACT_VERSION,
        "embedding_version": embedding_version,
        "embedding_dimension": embedding_dimension,
        "session_hash": str(manifest.get("session_hash") or ""),
        "generated_timestamp": str(
            manifest.get("generated_timestamp") or ""
        ),
        "model_hash": None,
        "similarity_metric": "cosine",
        "similarity_scope": "exact_global_top_n",
        "top_n": requested_top_n,
        "effective_top_n": effective_top_n,
        "summary": {
            "total_patterns": len(
                {str(row.get("pattern_id") or "") for row in rows}
            ),
            "total_units": unit_count,
            "total_similarity_pairs": len(pairs),
            "average_similarity": (
                round(sum(similarities) / len(similarities), 6)
                if similarities
                else None
            ),
            "minimum_similarity": min(similarities) if similarities else None,
            "maximum_similarity": max(similarities) if similarities else None,
            "similarity_threshold": threshold,
            "highly_similar_pair_count": sum(
                score >= threshold for score in similarities
            ),
        },
        "similarity_pairs": pairs,
        "distribution": _distribution(similarities),
        "stable_patterns": stable_patterns,
        "divergent_patterns": divergent_patterns,
        "validation": {
            "status": validation_status,
            "warnings": warnings,
        },
        "provenance": {
            "filename": EMBEDDINGS_FILENAME,
            "sha256": _canonical_sha256(embeddings_payload),
            "timestamp": provenance_timestamp,
        },
    }
    artifact["model_hash"] = _model_hash(artifact)
    return artifact
