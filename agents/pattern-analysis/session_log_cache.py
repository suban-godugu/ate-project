"""
E0 — shared per-log ATE parse/coverage cache for Analysis Session.

Parse each ATE log once; reuse ate_data + coverage across executions,
scan vectors, and embeddings. Session-path only; never writes FR artifacts.

PA-PERF-003: optional ProcessPoolExecutor for independent log parse+coverage.
PA-PERF-010: optional persistent ProcessPool reuse (executor lifecycle only).
workers=1 preserves the exact serial path. Parallel merge collects futures in
submission (zip) order so downstream run_id / artifact order stays deterministic.
"""
from __future__ import annotations

import atexit
import os
import threading
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ate_parser import ATEParser
from coverage_calculator import CoverageCalculator

# PA-PERF-010 — internal only (not public YAML). True only after EVG passes.
ENABLE_PERSISTENT_E0_POOL = True

_E0_POOL: Optional[ProcessPoolExecutor] = None
_E0_POOL_WORKERS: int = 0
# Monotonic lifecycle generation; incremented on create/invalidate for recovery.
_E0_POOL_GENERATION: int = 0
_E0_POOL_LOCK = threading.Lock()


@dataclass(frozen=True)
class SessionLogEntry:
    """One parsed ATE log with coverage — shared across session builders."""

    absolute_path: str
    relative_path: str
    source_name: str
    ate_data: Dict[str, Any]
    coverage: Dict[str, Any]


def _parse_one_log(absolute_path: str, relative_path: str) -> SessionLogEntry:
    """
    Process-pool worker: parse one ATE log and compute coverage.

    No STIL, session objects, embeddings, or shared mutable state.
    """
    parser = ATEParser()
    calculator = CoverageCalculator()
    ate_data = parser.parse(absolute_path)
    coverage = calculator.calculate_coverage(ate_data)
    return SessionLogEntry(
        absolute_path=absolute_path,
        relative_path=relative_path,
        source_name=os.path.basename(absolute_path),
        ate_data=ate_data,
        coverage=coverage,
    )


def _build_session_log_cache_serial(
    absolute_log_paths: Sequence[str],
    relative_log_paths: Sequence[str],
) -> List[SessionLogEntry]:
    """Exact serial E0 path (workers=1). Permanent golden reference."""
    return [
        _parse_one_log(absolute_path, relative_path)
        for absolute_path, relative_path in zip(absolute_log_paths, relative_log_paths)
    ]


def _submit_and_collect_parallel(
    executor: ProcessPoolExecutor,
    absolute_log_paths: Sequence[str],
    relative_log_paths: Sequence[str],
) -> List[SessionLogEntry]:
    """Submit in zip order; collect future.result() in submission order."""
    futures = []
    for absolute_path, relative_path in zip(absolute_log_paths, relative_log_paths):
        futures.append(
            executor.submit(_parse_one_log, absolute_path, relative_path)
        )
    # Submission order == zip order == deterministic merge.
    return [future.result() for future in futures]


def _invalidate_e0_pool_locked() -> None:
    """Discard the shared pool. Caller must hold _E0_POOL_LOCK."""
    global _E0_POOL, _E0_POOL_WORKERS, _E0_POOL_GENERATION

    if _E0_POOL is not None:
        try:
            _E0_POOL.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
    _E0_POOL = None
    _E0_POOL_WORKERS = 0
    _E0_POOL_GENERATION += 1


def shutdown_e0_process_pool(*, wait: bool = True) -> None:
    """Explicit pool teardown for tests and process shutdown."""
    global _E0_POOL, _E0_POOL_WORKERS, _E0_POOL_GENERATION

    with _E0_POOL_LOCK:
        if _E0_POOL is not None:
            try:
                _E0_POOL.shutdown(wait=wait, cancel_futures=not wait)
            except Exception:
                pass
        _E0_POOL = None
        _E0_POOL_WORKERS = 0
        _E0_POOL_GENERATION += 1


def _acquire_e0_pool(workers: int) -> Tuple[ProcessPoolExecutor, int]:
    """
    Return a live ProcessPoolExecutor and its generation token.

    Recreates the pool when worker count changes or the pool was invalidated.
    """
    global _E0_POOL, _E0_POOL_WORKERS, _E0_POOL_GENERATION

    with _E0_POOL_LOCK:
        if _E0_POOL is not None and _E0_POOL_WORKERS == workers:
            return _E0_POOL, _E0_POOL_GENERATION

        _invalidate_e0_pool_locked()
        executor = ProcessPoolExecutor(max_workers=workers)
        _E0_POOL = executor
        _E0_POOL_WORKERS = workers
        _E0_POOL_GENERATION += 1
        return executor, _E0_POOL_GENERATION


def _build_session_log_cache_ephemeral_pool(
    absolute_log_paths: Sequence[str],
    relative_log_paths: Sequence[str],
    *,
    workers: int,
) -> List[SessionLogEntry]:
    """PA-PERF-003 path: create pool per call, shutdown after merge."""
    executor = ProcessPoolExecutor(max_workers=workers)
    futures = []
    try:
        for absolute_path, relative_path in zip(absolute_log_paths, relative_log_paths):
            futures.append(
                executor.submit(_parse_one_log, absolute_path, relative_path)
            )
        return [future.result() for future in futures]
    except BaseException:
        for future in futures:
            future.cancel()
        executor.shutdown(wait=False, cancel_futures=True)
        raise
    else:
        executor.shutdown(wait=True)


def _build_session_log_cache_persistent_pool(
    absolute_log_paths: Sequence[str],
    relative_log_paths: Sequence[str],
    *,
    workers: int,
) -> List[SessionLogEntry]:
    """PA-PERF-010 path: reuse shared pool; invalidate on failure."""
    executor, generation = _acquire_e0_pool(workers)
    try:
        return _submit_and_collect_parallel(
            executor,
            absolute_log_paths,
            relative_log_paths,
        )
    except BaseException:
        with _E0_POOL_LOCK:
            if generation == _E0_POOL_GENERATION:
                _invalidate_e0_pool_locked()
        raise


def build_session_log_cache(
    absolute_log_paths: Sequence[str],
    relative_log_paths: Sequence[str],
    *,
    max_workers: int = 1,
) -> List[SessionLogEntry]:
    """
    Parse and cover each ATE log exactly once, in zip order.

    Callers must pass already-resolved path lists (same length).
    max_workers <= 1 uses the serial loop; otherwise ProcessPoolExecutor
    with results collected in submission order (never as_completed).
    """
    if len(absolute_log_paths) != len(relative_log_paths):
        raise ValueError("absolute_log_paths and relative_log_paths length mismatch.")

    log_count = len(absolute_log_paths)
    if log_count == 0:
        return []

    if max_workers <= 1:
        return _build_session_log_cache_serial(absolute_log_paths, relative_log_paths)

    workers = min(max(1, int(max_workers)), log_count)
    if workers <= 1:
        return _build_session_log_cache_serial(absolute_log_paths, relative_log_paths)

    if ENABLE_PERSISTENT_E0_POOL:
        return _build_session_log_cache_persistent_pool(
            absolute_log_paths,
            relative_log_paths,
            workers=workers,
        )

    return _build_session_log_cache_ephemeral_pool(
        absolute_log_paths,
        relative_log_paths,
        workers=workers,
    )


atexit.register(shutdown_e0_process_pool)
