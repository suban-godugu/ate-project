"""Configurable fault taxonomy management for FA-FR-004."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adapters.yaml_config import load_adapter_configs

DEFAULT_TAXONOMY_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "classification_taxonomy.yaml"
)


class TaxonomyManager:
    """Load and normalize customer-specific fault taxonomies."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.categories: list[str] = list(config.get("categories", []))
        self.definitions: dict[str, str] = dict(config.get("category_definitions", {}))
        self.unclassified: str = str(config.get("unclassified_label", "Unknown Failure"))
        self.rules: list[dict[str, Any]] = list(config.get("rules", []))
        self.thresholds: dict[str, float] = {
            k: float(v) for k, v in dict(config.get("thresholds", {})).items()
        }
        self.legacy_map: dict[str, str] = dict(config.get("legacy_category_map", {}))
        self.recommendations: dict[str, str] = dict(
            config.get("engineering_recommendations", {})
        )

    @classmethod
    def load(cls, path: Path | str | None = None) -> TaxonomyManager:
        cfg_path = Path(path) if path else DEFAULT_TAXONOMY_PATH
        return cls(load_adapter_configs(cfg_path))

    def normalize_category(self, label: str) -> str:
        if label in self.categories:
            return label
        if label in self.legacy_map:
            return self.legacy_map[label]
        return self.unclassified

    def recommendation_for(self, category: str) -> str:
        normalized = self.normalize_category(category)
        return self.recommendations.get(
            normalized,
            "Review failure signature and correlate with lot/wafer process history.",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "categories": self.categories,
            "category_definitions": self.definitions,
            "unclassified_label": self.unclassified,
            "thresholds": self.thresholds,
            "rule_count": len(self.rules),
        }
