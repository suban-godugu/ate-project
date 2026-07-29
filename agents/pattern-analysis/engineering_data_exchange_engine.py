"""
PA-ARCH-003 — Engineering Data Exchange streaming export engine.

Orchestrates preflight hashing, per-section processors, and StreamingJsonWriter.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional, Tuple

from engineering_data_exchange import (
    MASTER_FILENAME,
    build_pattern_analysis_master,
    load_exchange_sources,
    validate_master_structure,
)
from engineering_data_exchange_catalog import ArtifactCatalog
from engineering_data_exchange_processors import (
    build_cluster_statistics_section,
    build_clusters_section_streaming,
    build_dataset_section,
    build_embeddings_section_streaming,
    build_header_entries,
    build_pattern_characteristics_section,
    build_pattern_metadata_section,
    build_pattern_metrics_section,
    build_pattern_rankings_section,
    build_pipeline_versions_section,
    build_provenance_index_streaming,
    build_similarity_matrix_section,
    build_source_sections,
    build_structural_similarity_section,
    build_summary_section,
)
from engineering_data_exchange_stream import StreamingJsonWriter


def _collect_master_entries(
    catalog: ArtifactCatalog,
    *,
    timestamp_fn: Optional[Callable[[], str]] = None,
) -> List[Tuple[str, Any]]:
    """Build all top-level master sections without holding the full dict."""
    entries: List[Tuple[str, Any]] = []
    entries.extend(build_header_entries(catalog, timestamp_fn=timestamp_fn))

    entries.append(("analysis_summary", build_summary_section(catalog)))
    entries.append(("analysis_dataset", build_dataset_section(catalog)))
    entries.append(
        ("analysis_pipeline_versions", build_pipeline_versions_section(catalog))
    )

    source_artifacts, source_hashes = build_source_sections(catalog)
    entries.append(("source_artifacts", source_artifacts))
    entries.append(("source_hashes", source_hashes))

    provenance_index = build_provenance_index_streaming(catalog)

    entries.append(
        (
            "pattern_metadata",
            build_pattern_metadata_section(catalog, provenance_index),
        )
    )
    entries.append(
        (
            "pattern_characteristics",
            build_pattern_characteristics_section(catalog, provenance_index),
        )
    )
    entries.append(("embeddings", build_embeddings_section_streaming(catalog)))
    entries.append(("clusters", build_clusters_section_streaming(catalog)))
    entries.append(
        ("cluster_statistics", build_cluster_statistics_section(catalog))
    )
    entries.append(("similarity_matrix", build_similarity_matrix_section(catalog)))
    entries.append(
        (
            "structural_similarity",
            build_structural_similarity_section(catalog, provenance_index),
        )
    )
    entries.append(
        ("pattern_metrics", build_pattern_metrics_section(catalog, provenance_index))
    )
    entries.append(("pattern_rankings", build_pattern_rankings_section(catalog)))

    return entries


def export_pattern_analysis_master_streaming(
    output_dir: str,
    *,
    write: bool = True,
    timestamp_fn: Optional[Callable[[], str]] = None,
) -> Dict[str, Any]:
    """
    Stream-export pattern_analysis_master.json with bounded peak memory.

    Returns the full master dict (loaded from disk when write=True).
    """
    catalog = ArtifactCatalog(output_dir)
    catalog.preflight()
    entries = _collect_master_entries(catalog, timestamp_fn=timestamp_fn)

    master = {key: value for key, value in entries}
    errors = validate_master_structure(master)
    if errors:
        raise ValueError("Invalid pattern_analysis_master structure: " + "; ".join(errors))

    if not write:
        return master

    writer = StreamingJsonWriter(output_dir, MASTER_FILENAME)
    writer.open()
    for key in sorted(master):
        writer.write_entry(key, master[key])
    writer.close()

    path = writer.final_path
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def export_pattern_analysis_master_legacy(
    output_dir: str,
    *,
    write: bool = True,
    timestamp_fn: Optional[Callable[[], str]] = None,
) -> Dict[str, Any]:
    """Golden-reference export path (loads all artifacts at once)."""
    from engineering_data_exchange import write_master_json

    sources = load_exchange_sources(output_dir)
    master = build_pattern_analysis_master(sources, timestamp_fn=timestamp_fn)
    errors = validate_master_structure(master)
    if errors:
        raise ValueError("Invalid pattern_analysis_master structure: " + "; ".join(errors))
    if write:
        write_master_json(output_dir, master)
    return master
