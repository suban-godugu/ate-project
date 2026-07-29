"""
PA-FR-011 — Pattern Analysis Master Exporter.

Explicit, read-only Engineering Data Exchange Interface for Analysis Session
artifacts. Produces pattern_analysis_master.json when invoked.

Isolation rules:
- Never hooked into run_analysis_session_pipeline / server / UI / report paths.
- Never reads PA-FR-* Single Log artifacts.
- Never mutates Analysis Session source artifacts.
- Never recalculates embeddings, clustering, similarity, or redundancy.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from engineering_data_exchange import (
    MASTER_FILENAME,
    MASTER_TOP_LEVEL_KEYS,
    SCHEMA_VERSION,
    build_pattern_analysis_master,
    load_exchange_sources,
    validate_master_structure,
    write_master_json,
)
from engineering_data_exchange_engine import (
    export_pattern_analysis_master_legacy,
    export_pattern_analysis_master_streaming,
)

__all__ = [
    "MASTER_FILENAME",
    "MASTER_TOP_LEVEL_KEYS",
    "SCHEMA_VERSION",
    "build_pattern_analysis_master",
    "export_pattern_analysis_master",
    "load_exchange_sources",
    "validate_master_structure",
]


def export_pattern_analysis_master(
    output_dir: str,
    *,
    write: bool = True,
    timestamp_fn: Optional[Callable[[], str]] = None,
) -> Dict[str, Any]:
    """
    Read Analysis Session L1 artifacts from ``output_dir`` and build the
    canonical Engineering Data Exchange document.

    Parameters
    ----------
    output_dir:
        Directory containing PA-Analysis-Session_*.json artifacts.
    write:
        When True, write ``pattern_analysis_master.json`` beside the sources.
    timestamp_fn:
        Optional UTC timestamp supplier for deterministic tests.

    Returns
    -------
    dict
        The master export payload. Source session artifacts are never modified.
    """
    return export_pattern_analysis_master_streaming(
        output_dir,
        write=write,
        timestamp_fn=timestamp_fn,
    )


def export_pattern_analysis_master_reference(
    output_dir: str,
    *,
    write: bool = True,
    timestamp_fn: Optional[Callable[[], str]] = None,
) -> Dict[str, Any]:
    """Legacy all-at-once export path retained for golden parity tests."""
    return export_pattern_analysis_master_legacy(
        output_dir,
        write=write,
        timestamp_fn=timestamp_fn,
    )
