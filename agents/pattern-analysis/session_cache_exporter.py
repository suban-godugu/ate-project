"""
Session scan-vector exporter — writes PA-Analysis-Session_scan_vectors.json only.

Calls locked build_scan_vector_cache() / from-ate_data helpers in-memory per log.
Never writes PA-FR-005_scan_vector_cache.json.

E0: when SessionLogEntry cache is provided, vectors are built without re-parsing.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from analysis_session import SESSION_GENERATED_BY
from scan_vector_cache import SYMBOL_MAP, build_scan_vector_cache, build_scan_vector_cache_from_ate_data
from session_log_cache import SessionLogEntry


def _vector_sort_key(record: Dict[str, Any]) -> tuple:
    return (
        str(record.get("pattern_id", "")),
        str(record.get("source_log", "")),
        int(record.get("run_id", 0)),
    )


def build_session_scan_vectors(
    *,
    stil_file: str,
    absolute_log_paths: Sequence[str],
    relative_log_paths: Sequence[str],
    log_entries: Optional[Sequence[SessionLogEntry]] = None,
) -> Dict[str, Any]:
    """
    Build per-execution scan vectors for every (pattern_id, source_log).

    One vector record is emitted per pattern per log. run_id values are assigned
    deterministically in sorted-log then pattern encounter order.
    """
    if log_entries is None and len(absolute_log_paths) != len(relative_log_paths):
        raise ValueError("absolute_log_paths and relative_log_paths length mismatch.")

    vectors: List[Dict[str, Any]] = []
    run_id = 1

    if log_entries is not None:
        iterable = [
            (entry.ate_data, entry.relative_path, entry.source_name)
            for entry in log_entries
        ]
        for ate_data, relative_path, source_name in iterable:
            cache = build_scan_vector_cache_from_ate_data(
                ate_data,
                source_file=stil_file,
                ate_log_used=source_name,
            )
            patterns = sorted(
                cache.get("patterns") or [],
                key=lambda item: str(item.get("pattern_id", "")),
            )
            for pattern_entry in patterns:
                vectors.append(
                    {
                        "pattern_id": str(pattern_entry.get("pattern_id", "")),
                        "source_log": source_name,
                        "source_log_relpath": relative_path,
                        "run_id": run_id,
                        "chains": pattern_entry.get("chains") or [],
                        "concatenated_sequence": pattern_entry.get("concatenated_sequence", ""),
                    }
                )
                run_id += 1
    else:
        for absolute_path, relative_path in zip(absolute_log_paths, relative_log_paths):
            cache = build_scan_vector_cache(absolute_path, stil_file)
            source_name = cache.get("ate_log_used") or relative_path.rsplit("/", 1)[-1]
            patterns = sorted(
                cache.get("patterns") or [],
                key=lambda item: str(item.get("pattern_id", "")),
            )
            for pattern_entry in patterns:
                vectors.append(
                    {
                        "pattern_id": str(pattern_entry.get("pattern_id", "")),
                        "source_log": source_name,
                        "source_log_relpath": relative_path,
                        "run_id": run_id,
                        "chains": pattern_entry.get("chains") or [],
                        "concatenated_sequence": pattern_entry.get("concatenated_sequence", ""),
                    }
                )
                run_id += 1

    vectors.sort(key=_vector_sort_key)
    return {
        "generated_by": SESSION_GENERATED_BY,
        "symbol_map": dict(SYMBOL_MAP),
        "vector_count": len(vectors),
        "vectors": vectors,
    }
