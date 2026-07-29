"""
PA-FR-008 Similarity Configuration — loads and validates config/similarity.yaml.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import yaml


class SimilarityConfigError(ValueError):
    """Raised when similarity configuration is invalid or incomplete."""


REQUIRED_TOP_LEVEL_KEYS = (
    "metric",
    "response_time_budget_ms",
    "default_top_n",
    "max_top_n",
    "search_scope",
    "cache_enabled",
    "ann_enabled",
    "display_precision",
    "categories",
)


@dataclass(frozen=True)
class SimilarityCategory:
    key: str
    min_threshold: float
    label: str


@dataclass(frozen=True)
class SimilarityConfig:
    metric: str
    response_time_budget_ms: int
    default_top_n: int
    max_top_n: int
    search_scope: str
    cache_enabled: bool
    ann_enabled: bool
    display_precision: int
    categories: Tuple[SimilarityCategory, ...]

    @property
    def categories_descending(self) -> Tuple[SimilarityCategory, ...]:
        return self.categories


def _parse_categories(raw: Any) -> Tuple[SimilarityCategory, ...]:
    if not isinstance(raw, dict) or not raw:
        raise SimilarityConfigError("similarity.categories must be a non-empty mapping.")
    parsed: List[SimilarityCategory] = []
    for key, value in raw.items():
        if not isinstance(value, dict):
            raise SimilarityConfigError(f"similarity.categories.{key} must be an object with min and label.")
        if "min" not in value or "label" not in value:
            raise SimilarityConfigError(f"similarity.categories.{key} requires min and label.")
        min_threshold = float(value["min"])
        if not 0.0 <= min_threshold <= 1.0:
            raise SimilarityConfigError(f"similarity.categories.{key}.min must be between 0.0 and 1.0.")
        label = str(value["label"]).strip()
        if not label:
            raise SimilarityConfigError(f"similarity.categories.{key}.label must not be empty.")
        parsed.append(SimilarityCategory(key=str(key), min_threshold=min_threshold, label=label))
    parsed.sort(key=lambda item: (-item.min_threshold, item.key))
    return tuple(parsed)


def load_similarity_config(config_path: str) -> SimilarityConfig:
    if not os.path.exists(config_path):
        raise SimilarityConfigError(f"Similarity configuration not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    similarity = payload.get("similarity", payload)
    if not isinstance(similarity, dict):
        raise SimilarityConfigError("similarity configuration root must be a mapping.")

    missing = [key for key in REQUIRED_TOP_LEVEL_KEYS if key not in similarity]
    if missing:
        raise SimilarityConfigError(
            f"Missing required similarity configuration keys: {', '.join(missing)}"
        )

    metric = str(similarity["metric"]).lower()
    if metric != "cosine":
        raise SimilarityConfigError(f"Unsupported similarity metric: {similarity['metric']}")

    default_top_n = int(similarity["default_top_n"])
    max_top_n = int(similarity["max_top_n"])
    if default_top_n < 1:
        raise SimilarityConfigError("default_top_n must be at least 1.")
    if max_top_n < 1:
        raise SimilarityConfigError("max_top_n must be at least 1.")
    if default_top_n > max_top_n:
        raise SimilarityConfigError("default_top_n cannot exceed max_top_n.")

    search_scope = str(similarity["search_scope"]).lower()
    if search_scope not in {"global", "cluster"}:
        raise SimilarityConfigError("search_scope must be 'global' or 'cluster'.")

    return SimilarityConfig(
        metric=metric,
        response_time_budget_ms=int(similarity["response_time_budget_ms"]),
        default_top_n=default_top_n,
        max_top_n=max_top_n,
        search_scope=search_scope,
        cache_enabled=bool(similarity["cache_enabled"]),
        ann_enabled=bool(similarity["ann_enabled"]),
        display_precision=int(similarity["display_precision"]),
        categories=_parse_categories(similarity["categories"]),
    )
