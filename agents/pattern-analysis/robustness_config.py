"""Central robustness rules — LOT mapping, result normalization, embedding projection."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Sequence

import yaml

DEFAULT_PASS_VALUES = ("PASS", "P", "OK", "GOOD")
DEFAULT_FAIL_VALUES = ("FAIL", "F", "NG", "BAD", "ERROR")
DEFAULT_LOT_STRATEGY = "parent_dir"
DEFAULT_UNGROUPED = "Ungrouped"
DEFAULT_UNKNOWN = "UNKNOWN"
DEFAULT_EMBEDDING_DIM = 128
DEFAULT_MAX_CHAIN_SLOTS = 23
DEFAULT_WINDOW_COUNT = 64
DEFAULT_WAVEFORM_TABLE_MODE = "auto"


@dataclass(frozen=True)
class StilValidationConfig:
    waveform_table_mode: str = DEFAULT_WAVEFORM_TABLE_MODE


@dataclass(frozen=True)
class LotMappingConfig:
    strategy: str = DEFAULT_LOT_STRATEGY
    ungrouped_label: str = DEFAULT_UNGROUPED
    explicit_map: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ResultMappingConfig:
    pass_values: tuple[str, ...] = DEFAULT_PASS_VALUES
    fail_values: tuple[str, ...] = DEFAULT_FAIL_VALUES
    unknown_label: str = DEFAULT_UNKNOWN


@dataclass(frozen=True)
class EmbeddingProjectionConfig:
    target_dimension: int = DEFAULT_EMBEDDING_DIM
    max_chain_slots: int = DEFAULT_MAX_CHAIN_SLOTS
    window_count: int = DEFAULT_WINDOW_COUNT
    overflow_chain_strategy: str = "aggregate"


@dataclass(frozen=True)
class RobustnessConfig:
    lot_mapping: LotMappingConfig = field(default_factory=LotMappingConfig)
    result_mapping: ResultMappingConfig = field(default_factory=ResultMappingConfig)
    embedding: EmbeddingProjectionConfig = field(default_factory=EmbeddingProjectionConfig)
    stil_validation: StilValidationConfig = field(default_factory=StilValidationConfig)


def _normalize_list(values: Optional[Sequence[str]], default: tuple[str, ...]) -> tuple[str, ...]:
    if not values:
        return default
    return tuple(str(item).strip().upper() for item in values if str(item).strip())


def resolve_robustness_config_path(workspace_dir: str, config_path: Optional[str] = None) -> str:
    if config_path:
        return config_path
    candidate = os.path.join(workspace_dir, "config", "robustness.yaml")
    if os.path.exists(candidate):
        return candidate
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "robustness.yaml")


def load_robustness_config(
    workspace_dir: str = ".",
    *,
    config_path: Optional[str] = None,
) -> RobustnessConfig:
    path = resolve_robustness_config_path(workspace_dir, config_path)
    if not os.path.exists(path):
        return RobustnessConfig()
    with open(path, encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    section = payload.get("robustness") or {}
    lot_section = section.get("lot_mapping") or {}
    result_section = section.get("result_mapping") or {}
    embedding_section = section.get("embedding") or {}
    stil_section = section.get("stil_validation") or {}
    explicit = lot_section.get("explicit_map") or {}
    explicit_map = {
        str(key).replace("\\", "/"): str(value)
        for key, value in explicit.items()
        if str(key).strip()
    }
    return RobustnessConfig(
        lot_mapping=LotMappingConfig(
            strategy=str(lot_section.get("strategy") or DEFAULT_LOT_STRATEGY),
            ungrouped_label=str(lot_section.get("ungrouped_label") or DEFAULT_UNGROUPED),
            explicit_map=explicit_map,
        ),
        result_mapping=ResultMappingConfig(
            pass_values=_normalize_list(
                result_section.get("pass_values"), DEFAULT_PASS_VALUES
            ),
            fail_values=_normalize_list(
                result_section.get("fail_values"), DEFAULT_FAIL_VALUES
            ),
            unknown_label=str(result_section.get("unknown_label") or DEFAULT_UNKNOWN),
        ),
        embedding=EmbeddingProjectionConfig(
            target_dimension=int(
                embedding_section.get("target_dimension") or DEFAULT_EMBEDDING_DIM
            ),
            max_chain_slots=int(
                embedding_section.get("max_chain_slots") or DEFAULT_MAX_CHAIN_SLOTS
            ),
            window_count=int(
                embedding_section.get("window_count") or DEFAULT_WINDOW_COUNT
            ),
            overflow_chain_strategy=str(
                embedding_section.get("overflow_chain_strategy") or "aggregate"
            ),
        ),
        stil_validation=StilValidationConfig(
            waveform_table_mode=str(
                stil_section.get("waveform_table_mode") or DEFAULT_WAVEFORM_TABLE_MODE
            ).lower(),
        ),
    )


def normalize_path(path: str) -> str:
    return str(path or "").replace("\\", "/").strip("/")


def lot_from_relpath(
    relpath: str,
    *,
    config: Optional[RobustnessConfig] = None,
    source_lot: Optional[str] = None,
) -> str:
    """Resolve canonical source_lot from metadata, explicit map, or strategy."""
    if source_lot and str(source_lot).strip():
        return str(source_lot).strip()
    cfg = config or RobustnessConfig()
    normalized = normalize_path(relpath)
    if normalized in cfg.lot_mapping.explicit_map:
        return cfg.lot_mapping.explicit_map[normalized]
    parts = [part for part in normalized.split("/") if part]
    if not parts:
        return cfg.lot_mapping.ungrouped_label
    strategy = cfg.lot_mapping.strategy.lower()
    if strategy == "basename":
        return os.path.splitext(parts[-1])[0] or cfg.lot_mapping.ungrouped_label
    if len(parts) >= 2:
        return parts[-2]
    return parts[0] if parts else cfg.lot_mapping.ungrouped_label


def normalize_execution_result(
    raw_result: object,
    *,
    config: Optional[RobustnessConfig] = None,
) -> str:
    """Map arbitrary ATE result strings to PASS, FAIL, or UNKNOWN."""
    cfg = config or RobustnessConfig()
    text = str(raw_result or "").strip().upper()
    if not text:
        return cfg.result_mapping.unknown_label
    if text in cfg.result_mapping.pass_values:
        return "PASS"
    if text in cfg.result_mapping.fail_values:
        return "FAIL"
    return cfg.result_mapping.unknown_label


def label_from_result(
    raw_result: object,
    *,
    config: Optional[RobustnessConfig] = None,
) -> Optional[int]:
    """Binary ML label: 1=FAIL, 0=PASS, None=unknown."""
    canonical = normalize_execution_result(raw_result, config=config)
    if canonical == "FAIL":
        return 1
    if canonical == "PASS":
        return 0
    return None


def project_vector_to_dimension(
    values: Sequence[float],
    target_dim: int,
) -> List[float]:
    """Deterministically pad or truncate a vector to target_dim."""
    dim = max(0, int(target_dim))
    if dim == 0:
        return []
    source = [float(value) for value in values]
    if len(source) >= dim:
        return source[:dim]
    return source + [0.0] * (dim - len(source))


def infer_chain_geometry(
    chains: Sequence[Mapping[str, object]],
) -> Dict[str, int]:
    """Infer chain count and max bit length from scan vector rows."""
    max_length = 0
    for row in chains:
        if not isinstance(row, Mapping):
            continue
        sequence = str(row.get("bit_sequence") or "")
        if len(sequence) > max_length:
            max_length = len(sequence)
    return {
        "chain_count": len(chains),
        "max_chain_length": max_length,
    }
