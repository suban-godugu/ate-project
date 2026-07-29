"""
Analysis Session configuration loader.

Separate from completed FR configs; used only by the session orchestration pathway.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, List, Union

import yaml

DEFAULT_SUMMARY_METRICS = [
    "execution_count",
    "pass_count",
    "fail_count",
    "toggle_coverage_pct_avg",
    "toggle_coverage_pct_max",
    "toggle_coverage_pct_min",
    "toggle_density_pct_avg",
]

DEFAULT_EMBEDDING_STRATEGY = "per_execution"
# Phase C: projection intentionally unset — finalize in a dedicated design phase.
DEFAULT_DOWNSTREAM_EMBEDDING_PROJECTION = "deferred"
DEFAULT_E0_PARALLEL_WORKERS: Union[str, int] = "auto"
DEFAULT_SESSION_WARM_CACHE = True


@dataclass(frozen=True)
class SessionConfig:
    pattern_chain_summary_metrics: List[str] = field(
        default_factory=lambda: list(DEFAULT_SUMMARY_METRICS)
    )
    embedding_strategy: str = DEFAULT_EMBEDDING_STRATEGY
    downstream_embedding_projection: str = DEFAULT_DOWNSTREAM_EMBEDDING_PROJECTION
    e0_parallel_workers: Union[str, int] = DEFAULT_E0_PARALLEL_WORKERS
    session_warm_cache: bool = DEFAULT_SESSION_WARM_CACHE


def resolve_e0_parallel_workers(value: Any, *, log_count: int) -> int:
    """
    Resolve e0_parallel_workers for ProcessPool sizing.

    - None / "auto" → min(cpu_count(), log_count), at least 1 when logs exist
    - positive int → that count, capped at log_count
    - invalid → ValueError (no silent recovery)
    """
    if log_count < 0:
        raise ValueError(f"log_count must be >= 0, got {log_count}")

    effective_logs = max(log_count, 1)

    if value is None:
        value = "auto"

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "auto":
            cpu = os.cpu_count() or 1
            return max(1, min(int(cpu), effective_logs if log_count > 0 else 1))
        if normalized.isdigit():
            workers = int(normalized)
        else:
            raise ValueError(
                f"Invalid e0_parallel_workers value: {value!r}. "
                "Expected 'auto' or a positive integer."
            )
    elif isinstance(value, bool):
        raise ValueError(
            f"Invalid e0_parallel_workers value: {value!r}. "
            "Expected 'auto' or a positive integer."
        )
    elif isinstance(value, int):
        workers = value
    else:
        raise ValueError(
            f"Invalid e0_parallel_workers value: {value!r}. "
            "Expected 'auto' or a positive integer."
        )

    if workers < 1:
        raise ValueError(
            f"Invalid e0_parallel_workers value: {value!r}. "
            "Expected 'auto' or a positive integer."
        )
    if log_count == 0:
        return workers
    return max(1, min(workers, log_count))


def load_session_config(config_path: str) -> SessionConfig:
    if not os.path.exists(config_path):
        return SessionConfig()
    with open(config_path, "r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    section = payload.get("analysis_session") or {}
    metrics = section.get("pattern_chain_summary_metrics") or list(DEFAULT_SUMMARY_METRICS)
    strategy = section.get("embedding_strategy") or DEFAULT_EMBEDDING_STRATEGY
    projection = (
        section.get("downstream_embedding_projection")
        or DEFAULT_DOWNSTREAM_EMBEDDING_PROJECTION
    )
    e0_workers = section.get("e0_parallel_workers", DEFAULT_E0_PARALLEL_WORKERS)
    warm_cache = section.get("session_warm_cache", DEFAULT_SESSION_WARM_CACHE)
    if isinstance(warm_cache, str):
        warm_cache = warm_cache.strip().lower() in {"1", "true", "yes", "on"}
    else:
        warm_cache = bool(warm_cache)
    return SessionConfig(
        pattern_chain_summary_metrics=list(metrics),
        embedding_strategy=str(strategy),
        downstream_embedding_projection=str(projection),
        e0_parallel_workers=e0_workers if e0_workers is not None else DEFAULT_E0_PARALLEL_WORKERS,
        session_warm_cache=warm_cache,
    )
