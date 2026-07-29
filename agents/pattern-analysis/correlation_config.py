"""
PA-FR-009 Correlation Configuration — loads and validates config/correlation.yaml.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, List, Tuple

import yaml


class CorrelationConfigError(ValueError):
    """Raised when correlation configuration is invalid or incomplete."""


REQUIRED_TOP_LEVEL_KEYS = (
    "join_key",
    "strict_join",
    "flag_missing_rows",
    "export_history",
    "export_manifest",
)

EXPECTED_JOIN_KEY: Tuple[str, str] = ("pattern_id", "scan_chain_id")


@dataclass(frozen=True)
class CorrelationConfig:
    join_key: Tuple[str, str]
    strict_join: bool
    flag_missing_rows: bool
    export_history: bool
    export_manifest: bool


def load_correlation_config(config_path: str) -> CorrelationConfig:
    if not os.path.exists(config_path):
        raise CorrelationConfigError(f"Correlation configuration not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    correlation = payload.get("correlation", payload)
    if not isinstance(correlation, dict):
        raise CorrelationConfigError("correlation configuration root must be a mapping.")

    missing = [key for key in REQUIRED_TOP_LEVEL_KEYS if key not in correlation]
    if missing:
        raise CorrelationConfigError(
            f"Missing required correlation configuration keys: {', '.join(missing)}"
        )

    join_key_raw = correlation["join_key"]
    if not isinstance(join_key_raw, list):
        raise CorrelationConfigError("correlation.join_key must be a list.")
    join_key = tuple(str(item) for item in join_key_raw)
    if join_key != EXPECTED_JOIN_KEY:
        raise CorrelationConfigError(
            f"correlation.join_key must be {list(EXPECTED_JOIN_KEY)}, got {list(join_key)}"
        )

    return CorrelationConfig(
        join_key=join_key,
        strict_join=bool(correlation["strict_join"]),
        flag_missing_rows=bool(correlation["flag_missing_rows"]),
        export_history=bool(correlation["export_history"]),
        export_manifest=bool(correlation["export_manifest"]),
    )
