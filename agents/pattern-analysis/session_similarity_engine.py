"""Analysis Session similarity over execution units.

This module is additive: it never reads or writes PA-FR-008 artifacts and does
not change the legacy pattern-keyed SimilarityEngine.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from cluster_engine import cosine_similarity, pattern_sort_key
from similarity_config import SimilarityConfig, load_similarity_config
from similarity_validator import (
    SimilarityAbortError,
    SimilarityValidationError,
    validate_metric_supported,
    validate_top_n,
)

from robustness_config import lot_from_relpath, load_robustness_config


def session_unit_id(row: Dict[str, Any]) -> str:
    pattern_id = str(row.get("pattern_id") or "").strip()
    source = str(
        row.get("source_log_relpath") or row.get("source_log") or ""
    ).strip()
    return f"{pattern_id}::{source}"


def source_lot(
    row: Dict[str, Any],
    robustness_cfg: Optional[object] = None,
) -> str:
    explicit = str(row.get("source_lot") or "").strip()
    if explicit:
        return explicit
    source = str(
        row.get("source_log_relpath") or row.get("source_log") or ""
    ).replace("\\", "/")
    return lot_from_relpath(source, config=robustness_cfg)


@dataclass(frozen=True)
class SessionSimilarityUnit:
    unit_id: str
    pattern_id: str
    source_log: str
    source_log_relpath: str
    source_lot: str
    run_id: Any
    embedding: Tuple[float, ...]
    embedding_version: str
    cluster_id: Optional[str] = None

    def provenance_dict(self) -> Dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "pattern_id": self.pattern_id,
            "source_log": self.source_log,
            "source_log_relpath": self.source_log_relpath,
            "source_lot": self.source_lot,
            "run_id": self.run_id,
            "cluster_id": self.cluster_id,
            "embedding_version": self.embedding_version,
        }


class SessionSimilarityEngine:
    """Pairwise and Top-N similarity for pattern + execution-source units."""

    def __init__(
        self,
        *,
        config: SimilarityConfig,
        units: Sequence[SessionSimilarityUnit],
        embedding_version: str,
    ) -> None:
        validate_metric_supported(config)
        self.config = config
        self.embedding_version = str(embedding_version or "1.0")
        ordered = sorted(units, key=lambda unit: pattern_sort_key(unit.unit_id))
        self.units = tuple(ordered)
        self.units_map = {unit.unit_id: unit for unit in ordered}
        self.unit_index = {
            unit.unit_id: index for index, unit in enumerate(self.units)
        }
        if len(self.units_map) != len(self.units):
            raise SimilarityAbortError("Duplicate Analysis Session unit IDs detected.")
        versions = {unit.embedding_version for unit in ordered}
        if len(versions) > 1:
            raise SimilarityAbortError(
                f"Mixed session embedding versions detected: {sorted(versions)}"
            )
        dimensions = {len(unit.embedding) for unit in ordered}
        if len(dimensions) > 1:
            raise SimilarityAbortError(
                f"Mixed session embedding dimensions detected: {sorted(dimensions)}"
            )
        if ordered:
            matrix = np.asarray([unit.embedding for unit in ordered], dtype=np.float64)
            norms = np.linalg.norm(matrix, axis=1, keepdims=True)
            self.normalized_matrix = np.divide(
                matrix,
                norms,
                out=np.zeros_like(matrix),
                where=norms != 0.0,
            )
        else:
            self.normalized_matrix = np.empty((0, 0), dtype=np.float64)

    @classmethod
    def from_rows(
        cls,
        *,
        rows: Sequence[Dict[str, Any]],
        workspace_dir: str,
        embedding_version: str = "1.0",
        cluster_by_unit: Optional[Dict[str, str]] = None,
        config_path: Optional[str] = None,
    ) -> "SessionSimilarityEngine":
        config_file = config_path or os.path.join(
            workspace_dir, "config", "similarity.yaml"
        )
        config = load_similarity_config(config_file)
        cluster_by_unit = cluster_by_unit or {}
        robustness_cfg = load_robustness_config(workspace_dir)
        units: List[SessionSimilarityUnit] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            vector = row.get("embedding")
            pattern_id = str(row.get("pattern_id") or "").strip()
            if not pattern_id or not isinstance(vector, list) or not vector:
                continue
            uid = session_unit_id(row)
            version = str(
                row.get("embedding_version")
                or row.get("feature_version")
                or embedding_version
            )
            try:
                embedding = tuple(float(value) for value in vector)
            except (TypeError, ValueError) as exc:
                raise SimilarityAbortError(
                    f"Session unit '{uid}' contains invalid embedding values."
                ) from exc
            units.append(
                SessionSimilarityUnit(
                    unit_id=uid,
                    pattern_id=pattern_id,
                    source_log=str(row.get("source_log") or ""),
                    source_log_relpath=str(row.get("source_log_relpath") or ""),
                    source_lot=source_lot(row, robustness_cfg=robustness_cfg),
                    run_id=row.get("run_id"),
                    embedding=embedding,
                    embedding_version=version,
                    cluster_id=cluster_by_unit.get(uid),
                )
            )
        return cls(
            config=config,
            units=units,
            embedding_version=embedding_version,
        )

    def classify_similarity(self, score: float) -> str:
        for category in self.config.categories_descending:
            if score >= category.min_threshold:
                return category.label
        return self.config.categories_descending[-1].label

    def _round_score(self, score: float) -> float:
        return round(float(score), self.config.display_precision)

    def _require_unit(self, unit_id: str) -> SessionSimilarityUnit:
        normalized = str(unit_id or "").strip()
        if not normalized:
            raise SimilarityValidationError("unit_id is required.")
        unit = self.units_map.get(normalized)
        if unit is None:
            raise SimilarityValidationError(
                f"Session unit '{normalized}' was not found in the embedding index."
            )
        return unit

    def compute_pair(self, unit_a: str, unit_b: str) -> Dict[str, Any]:
        left_id = str(unit_a or "").strip()
        right_id = str(unit_b or "").strip()
        if not left_id or not right_id:
            raise SimilarityValidationError("unit_a and unit_b are required.")
        if left_id == right_id:
            raise SimilarityValidationError(
                "Unit A and Unit B must be different execution units."
            )
        start = time.perf_counter()
        left = self._require_unit(left_id)
        right = self._require_unit(right_id)
        if left.embedding_version != right.embedding_version:
            raise SimilarityAbortError(
                "Mixed session embedding versions detected; comparison not permitted."
            )
        score = self._round_score(cosine_similarity(left.embedding, right.embedding))
        latency = round((time.perf_counter() - start) * 1000)
        return {
            "unit_a": left.provenance_dict(),
            "unit_b": right.provenance_dict(),
            "similarity_score": score,
            "category": self.classify_similarity(score),
            "engine_latency_ms": latency,
            "budget_exceeded": latency > self.config.response_time_budget_ms,
            "embedding_version": left.embedding_version,
            "similarity_metric": self.config.metric,
            "cross_lot": left.source_lot != right.source_lot,
            "pass_fail_context": None,
        }

    def compute_top_n(
        self, reference_unit: str, requested_top_n: Optional[int]
    ) -> Dict[str, Any]:
        reference = self._require_unit(reference_unit)
        top_n = validate_top_n(
            self.config.default_top_n
            if requested_top_n is None
            else int(requested_top_n),
            self.config,
        )
        start = time.perf_counter()
        reference_index = self.unit_index[reference.unit_id]
        all_scores = self.normalized_matrix @ self.normalized_matrix[reference_index]
        candidates = [
            unit for unit in self.units if unit.unit_id != reference.unit_id
        ]
        scores = np.delete(all_scores, reference_index)

        ranked: List[Tuple[float, SessionSimilarityUnit]] = [
            (self._round_score(float(score)), unit)
            for score, unit in zip(scores, candidates)
        ]
        ranked.sort(
            key=lambda item: (-item[0], pattern_sort_key(item[1].unit_id))
        )
        selected = ranked[:top_n]
        rows = []
        for index, (score, unit) in enumerate(selected):
            row = unit.provenance_dict()
            row.update(
                {
                    "rank": index + 1,
                    "similarity": score,
                    "category": self.classify_similarity(score),
                    "cross_lot": unit.source_lot != reference.source_lot,
                }
            )
            rows.append(row)
        latency = round((time.perf_counter() - start) * 1000)
        return {
            "reference_unit": reference.provenance_dict(),
            "requested_top_n": top_n,
            "returned_count": len(rows),
            "available_count": len(candidates),
            "partial_result": len(rows) < top_n,
            "results": rows,
            "engine_latency_ms": latency,
            "budget_exceeded": latency > self.config.response_time_budget_ms,
            "embedding_version": reference.embedding_version,
            "similarity_metric": self.config.metric,
            "pass_fail_context": None,
        }

    def option_rows(self) -> List[Dict[str, Any]]:
        return [
            {
                **unit.provenance_dict(),
                "label": (
                    f"{unit.pattern_id} — {unit.source_lot} / "
                    f"{unit.source_log_relpath or unit.source_log}"
                ),
            }
            for unit in self.units
        ]
