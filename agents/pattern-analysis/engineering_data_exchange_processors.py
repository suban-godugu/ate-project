"""
PA-ARCH-003 — Per-section Engineering Data Exchange processors.

Each processor loads only the artifacts it needs, builds one master section,
then releases cached payloads.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Mapping, Optional

from engineering_data_exchange import (
    ANALYSIS_MODE,
    GENERATED_BY,
    SCHEMA_VERSION,
    _build_provenance_index,
    build_analysis_dataset,
    build_analysis_summary,
    build_cluster_statistics,
    build_clusters_section,
    build_embeddings_section,
    build_export_information,
    build_pattern_characteristics,
    build_pattern_metadata,
    build_pattern_metrics,
    build_pattern_rankings,
    build_pipeline_versions,
    build_similarity_matrix,
    build_source_artifacts,
    build_source_hashes,
    build_structural_similarity,
    utc_timestamp,
)
from engineering_data_exchange_catalog import ArtifactCatalog

_PROVENANCE_ARTIFACTS: List[str] = [
    "executions",
    "scan_vectors",
    "embeddings",
    "clustering",
    "similarity",
    "correlation",
    "redundancy",
]


def build_provenance_index_streaming(catalog: ArtifactCatalog) -> Dict[str, Dict[str, str]]:
    """Build provenance index loading one artifact at a time."""
    prov_index: Dict[str, Dict[str, str]] = {}
    for logical_name in _PROVENANCE_ARTIFACTS:
        payload = catalog.load(logical_name)
        if not payload:
            continue
        partial = _build_provenance_index({logical_name: payload})
        for pattern_id, prov in partial.items():
            prov_index.setdefault(pattern_id, {}).update(prov)
        catalog.release(logical_name)
    return prov_index


def _with_artifacts(
    catalog: ArtifactCatalog,
    logical_names: List[str],
    builder: Callable[[Mapping[str, Optional[Dict[str, Any]]]], Any],
) -> Any:
    catalog.load_many(logical_names)
    try:
        return builder(catalog.artifacts_view())
    finally:
        catalog.release_many(logical_names)


def build_header_entries(
    catalog: ArtifactCatalog,
    *,
    timestamp_fn: Optional[Callable[[], str]] = None,
) -> List[tuple[str, Any]]:
    """Scalar and manifest-only header sections."""
    stamp = (timestamp_fn or utc_timestamp)()
    manifest = catalog.load("manifest")
    analysis_session_id = (manifest or {}).get("session_hash")
    catalog.release("manifest")

    return [
        ("schema_version", SCHEMA_VERSION),
        ("generated_by", GENERATED_BY),
        ("analysis_mode", ANALYSIS_MODE),
        ("analysis_session_id", analysis_session_id),
        ("generated_timestamp", stamp),
        ("export_information", build_export_information()),
    ]


def build_summary_section(catalog: ArtifactCatalog) -> Dict[str, Any]:
    names = [
        "manifest",
        "summary",
        "embeddings",
        "clustering",
        "redundancy",
        "similarity",
        "correlation",
    ]
    return _with_artifacts(catalog, names, build_analysis_summary)


def build_dataset_section(catalog: ArtifactCatalog) -> Dict[str, Any]:
    return _with_artifacts(
        catalog,
        ["manifest", "clustering", "correlation"],
        build_analysis_dataset,
    )


def build_pipeline_versions_section(catalog: ArtifactCatalog) -> Dict[str, Any]:
    return _with_artifacts(
        catalog,
        [
            "embeddings",
            "similarity",
            "clustering",
            "correlation",
            "redundancy",
            "executions",
            "summary",
            "scan_vectors",
            "report_model",
        ],
        build_pipeline_versions,
    )


def build_source_sections(
    catalog: ArtifactCatalog,
) -> tuple[List[Dict[str, Any]], Dict[str, str]]:
    return (
        build_source_artifacts(catalog.provenance),
        build_source_hashes(catalog.provenance),
    )


def build_pattern_metadata_section(
    catalog: ArtifactCatalog,
    provenance_index: Mapping[str, Dict[str, str]],
) -> List[Dict[str, Any]]:
    return _with_artifacts(
        catalog,
        ["executions", "scan_vectors", "embeddings"],
        lambda artifacts: build_pattern_metadata(artifacts, provenance_index),
    )


def build_pattern_characteristics_section(
    catalog: ArtifactCatalog,
    provenance_index: Mapping[str, Dict[str, str]],
) -> List[Dict[str, Any]]:
    return _with_artifacts(
        catalog,
        ["executions", "scan_vectors"],
        lambda artifacts: build_pattern_characteristics(artifacts, provenance_index),
    )


def build_embeddings_section_streaming(catalog: ArtifactCatalog) -> Dict[str, Any]:
    return _with_artifacts(catalog, ["embeddings"], build_embeddings_section)


def build_clusters_section_streaming(catalog: ArtifactCatalog) -> List[Dict[str, Any]]:
    return _with_artifacts(catalog, ["clustering"], build_clusters_section)


def build_cluster_statistics_section(catalog: ArtifactCatalog) -> Dict[str, Any]:
    return _with_artifacts(catalog, ["clustering"], build_cluster_statistics)


def build_similarity_matrix_section(catalog: ArtifactCatalog) -> Dict[str, Any]:
    return _with_artifacts(catalog, ["similarity"], build_similarity_matrix)


def build_structural_similarity_section(
    catalog: ArtifactCatalog,
    provenance_index: Mapping[str, Dict[str, str]],
) -> List[Dict[str, Any]]:
    return _with_artifacts(
        catalog,
        ["clustering", "similarity", "redundancy"],
        lambda artifacts: build_structural_similarity(artifacts, provenance_index),
    )


def build_pattern_metrics_section(
    catalog: ArtifactCatalog,
    provenance_index: Mapping[str, Dict[str, str]],
) -> List[Dict[str, Any]]:
    return _with_artifacts(
        catalog,
        ["correlation", "summary", "redundancy"],
        lambda artifacts: build_pattern_metrics(artifacts, provenance_index),
    )


def build_pattern_rankings_section(catalog: ArtifactCatalog) -> Dict[str, Any]:
    return _with_artifacts(
        catalog,
        ["executions", "similarity", "redundancy", "clustering"],
        build_pattern_rankings,
    )
