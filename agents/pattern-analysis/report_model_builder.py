"""
PA-FR-010.1 Pattern Quality Report Model Builder.

Collects read-only outputs from PA-FR-001 through PA-FR-009 and assembles the
deterministic single-log report model without invoking analysis engines.

Artifact helpers read upstream files and write only PA-FR-010_report_model.json.
The pure builder never mutates its inputs.
"""
from __future__ import annotations

import copy
import csv
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Tuple


@dataclass(frozen=True)
class ReportModelSources:
    """Immutable container for upstream FR outputs consumed by the report builder."""

    fr001_cpm_report: Optional[Mapping[str, Any]] = None
    fr002_pattern_vectors: Optional[Mapping[str, Any]] = None
    fr003_metadata: Optional[Mapping[str, Any]] = None
    fr004_toggle_coverage: Optional[Mapping[str, Any]] = None
    fr005_embeddings: Optional[Mapping[str, Any]] = None
    fr006_cluster_summary: Optional[Mapping[str, Any]] = None
    fr006_pattern_clusters: Optional[Mapping[str, Any]] = None
    fr006_file_rollup: Optional[Mapping[str, Any]] = None
    fr007_redundancy_candidates: Optional[Mapping[str, Any]] = None
    fr007_file_rollup: Optional[Mapping[str, Any]] = None
    fr008_similarity_metadata: Optional[Mapping[str, Any]] = None
    fr009_pattern_outcomes: Optional[Mapping[str, Any]] = None
    fr009_correlation_manifest: Optional[Mapping[str, Any]] = None
    artifact_metadata: Optional[Mapping[str, Any]] = None
    validation_warnings: Tuple[str, ...] = ()


REPORT_MODEL_FILENAME = "PA-FR-010_report_model.json"
REPORT_VERSION = "10.1"
REPORT_GENERATOR_VERSION = "1.0.0"


REDUNDANCY_CANDIDATE_FIELDS = (
    "pattern_a",
    "pattern_b",
    "cluster_id",
    "raw_similarity",
    "confidence_score",
    "confidence_source",
    "review_status",
    "label",
)

PATTERN_STATISTICS_FIELDS = (
    "pattern_id",
    "scan_chain_id",
    "toggle_count",
    "toggle_coverage_pct",
    "toggle_density_pct",
    "cluster_id",
    "similarity_to_centroid",
    "chain_count",
    "compression_ratio",
    "max_chain_length",
)

TOGGLE_SUMMARY_FIELDS = (
    "file_name",
    "total_toggle_count",
    "toggle_coverage_pct",
    "toggle_density_pct",
    "patterns_analyzed",
    "scan_chains_analyzed",
)

CORRELATION_SUMMARY_SCALAR_FIELDS = (
    "correlation_version",
    "matched_rows",
    "unmatched_metadata",
    "unmatched_ate",
    "duplicate_histories",
    "validation_status",
    "correlation_hash",
)


def _snapshot(value: Any) -> Any:
    """Return a deep copy so upstream objects are never mutated."""
    return copy.deepcopy(value)


def _sort_key_pattern_chain(row: Mapping[str, Any]) -> Tuple[str, str]:
    return (str(row.get("pattern_id", "")), str(row.get("scan_chain_id", "")))


def _build_source_versions(sources: ReportModelSources) -> Dict[str, Any]:
    embedding_version = None
    cluster_version = None
    correlation_version = None

    if sources.fr005_embeddings is not None:
        embedding_version = sources.fr005_embeddings.get("embedding_version")
    if embedding_version is None and sources.fr006_cluster_summary is not None:
        clusters = sources.fr006_cluster_summary.get("clusters") or []
        if clusters:
            embedding_version = clusters[0].get("embedding_version")
    if embedding_version is None and sources.fr006_pattern_clusters is not None:
        embedding_version = sources.fr006_pattern_clusters.get("embedding_version")
    if embedding_version is None and sources.fr007_redundancy_candidates is not None:
        embedding_version = sources.fr007_redundancy_candidates.get("embedding_version")

    if sources.fr006_cluster_summary is not None:
        cluster_version = sources.fr006_cluster_summary.get("cluster_version")
    if cluster_version is None and sources.fr006_file_rollup is not None:
        cluster_version = sources.fr006_file_rollup.get("cluster_version")
    if cluster_version is None and sources.fr007_redundancy_candidates is not None:
        cluster_version = sources.fr007_redundancy_candidates.get("cluster_version")

    if sources.fr009_correlation_manifest is not None:
        correlation_version = sources.fr009_correlation_manifest.get("correlation_version")
    if correlation_version is None and sources.fr009_pattern_outcomes is not None:
        correlation_version = sources.fr009_pattern_outcomes.get("correlation_version")

    return {
        "embedding_version": embedding_version,
        "cluster_version": cluster_version,
        "correlation_version": correlation_version,
    }


def _build_summary(sources: ReportModelSources) -> Dict[str, int]:
    total_patterns = 0
    if sources.fr003_metadata is not None:
        total_patterns = int(sources.fr003_metadata.get("pattern_count") or 0)
    elif sources.fr006_file_rollup is not None:
        total_patterns = int(sources.fr006_file_rollup.get("total_patterns") or 0)

    total_clusters = 0
    if sources.fr006_file_rollup is not None:
        total_clusters = int(sources.fr006_file_rollup.get("total_clusters") or 0)

    total_redundancy_candidates = 0
    if sources.fr007_file_rollup is not None:
        total_redundancy_candidates = int(sources.fr007_file_rollup.get("total_candidates") or 0)

    total_correlated_patterns = 0
    if sources.fr009_correlation_manifest is not None:
        total_correlated_patterns = int(sources.fr009_correlation_manifest.get("matched_rows") or 0)

    return {
        "total_patterns": total_patterns,
        "total_clusters": total_clusters,
        "total_redundancy_candidates": total_redundancy_candidates,
        "total_correlated_patterns": total_correlated_patterns,
    }


def _index_pattern_clusters(
    pattern_clusters: Optional[Mapping[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    if pattern_clusters is None:
        return {}
    indexed: Dict[str, Dict[str, Any]] = {}
    for entry in pattern_clusters.get("patterns") or []:
        pattern_id = entry.get("pattern_id")
        if pattern_id is None:
            continue
        indexed[str(pattern_id)] = _snapshot(entry)
    return indexed


def _build_pattern_statistics(sources: ReportModelSources) -> List[Dict[str, Any]]:
    """
    Build pattern_statistics rows at grain (pattern_id, scan_chain_id).

    Structural/toggle fields come from PA-FR-004 scan_chain_level. Cluster fields
    are joined from PA-FR-006 pattern_clusters by pattern_id. File-level PA-FR-003
    metrics (chain_count, compression_ratio, max_chain_length) are broadcast onto
    every row because PA-FR-003 has no pattern_id.
    """
    toggle_coverage = sources.fr004_toggle_coverage
    if toggle_coverage is None:
        return []

    scan_chain_rows = toggle_coverage.get("scan_chain_level") or []
    cluster_by_pattern = _index_pattern_clusters(sources.fr006_pattern_clusters)

    file_level: Dict[str, Any] = {}
    if sources.fr003_metadata is not None:
        for field in ("chain_count", "compression_ratio", "max_chain_length"):
            if field in sources.fr003_metadata:
                file_level[field] = sources.fr003_metadata[field]

    rows: List[Dict[str, Any]] = []
    for scan_row in scan_chain_rows:
        row: Dict[str, Any] = {
            "pattern_id": scan_row.get("pattern_id"),
            "scan_chain_id": scan_row.get("scan_chain_id"),
        }
        for field in ("toggle_count", "toggle_coverage_pct", "toggle_density_pct"):
            if field in scan_row:
                row[field] = scan_row[field]

        pattern_id = row.get("pattern_id")
        if pattern_id is not None:
            cluster_entry = cluster_by_pattern.get(str(pattern_id))
            if cluster_entry is not None:
                if "cluster_id" in cluster_entry:
                    row["cluster_id"] = cluster_entry["cluster_id"]
                if "similarity_to_centroid" in cluster_entry:
                    row["similarity_to_centroid"] = cluster_entry["similarity_to_centroid"]

        row.update(file_level)
        rows.append(row)

    rows.sort(key=_sort_key_pattern_chain)
    return rows


def _build_cluster_summary(sources: ReportModelSources) -> List[Dict[str, Any]]:
    if sources.fr006_cluster_summary is None:
        return []
    clusters = sources.fr006_cluster_summary.get("clusters") or []
    copied = [_snapshot(cluster) for cluster in clusters]
    copied.sort(key=lambda item: str(item.get("cluster_id", "")))
    return copied


def _build_redundancy_summary(sources: ReportModelSources) -> List[Dict[str, Any]]:
    if sources.fr007_redundancy_candidates is None:
        return []
    candidates = sources.fr007_redundancy_candidates.get("candidates") or []
    rows: List[Dict[str, Any]] = []
    for candidate in candidates:
        row = {field: candidate[field] for field in REDUNDANCY_CANDIDATE_FIELDS if field in candidate}
        rows.append(row)
    rows.sort(
        key=lambda item: (
            str(item.get("pattern_a", "")),
            str(item.get("pattern_b", "")),
            str(item.get("cluster_id", "")),
            str(item.get("raw_similarity", "")),
        )
    )
    return rows


def _build_similarity_summary(sources: ReportModelSources) -> Dict[str, Any]:
    if sources.fr008_similarity_metadata is not None:
        return _snapshot(dict(sources.fr008_similarity_metadata))

    summary: Dict[str, Any] = {}
    if sources.fr005_embeddings is not None:
        for field in ("embedding_version", "similarity_metric"):
            if field in sources.fr005_embeddings:
                summary[field] = sources.fr005_embeddings[field]
    return summary


def _build_toggle_summary(sources: ReportModelSources) -> Dict[str, Any]:
    if sources.fr004_toggle_coverage is None:
        return {}
    file_rollup = sources.fr004_toggle_coverage.get("file_rollup") or {}
    return {
        field: file_rollup[field]
        for field in TOGGLE_SUMMARY_FIELDS
        if field in file_rollup
    }


def _build_correlation_summary(sources: ReportModelSources) -> Dict[str, Any]:
    summary: Dict[str, Any] = {field: None for field in CORRELATION_SUMMARY_SCALAR_FIELDS}
    summary["patterns"] = []

    manifest = sources.fr009_correlation_manifest
    if manifest is not None:
        for field in CORRELATION_SUMMARY_SCALAR_FIELDS:
            if field in manifest:
                summary[field] = manifest[field]

    outcomes = sources.fr009_pattern_outcomes
    if outcomes is not None:
        if summary["correlation_version"] is None and "correlation_version" in outcomes:
            summary["correlation_version"] = outcomes["correlation_version"]
        patterns = [_snapshot(pattern) for pattern in (outcomes.get("patterns") or [])]
        patterns.sort(key=_sort_key_pattern_chain)
        summary["patterns"] = patterns

    return summary


def _build_data_quality_appendix(sources: ReportModelSources) -> List[Dict[str, Any]]:
    outcomes = sources.fr009_pattern_outcomes
    if outcomes is None:
        return []

    appendix: List[Dict[str, Any]] = []
    for pattern in outcomes.get("patterns") or []:
        flags = pattern.get("data_quality_flags") or []
        if not flags:
            continue
        appendix.append(
            {
                "pattern_id": pattern.get("pattern_id"),
                "scan_chain_id": pattern.get("scan_chain_id"),
                "data_quality_flags": _snapshot(flags),
            }
        )
    appendix.sort(key=_sort_key_pattern_chain)
    return appendix


def _section_status(*values: Optional[Mapping[str, Any]]) -> str:
    available = sum(value is not None for value in values)
    if available == 0:
        return "Missing"
    if available < len(values):
        return "Partial"
    return "Available"


def _sorted_rows(
    rows: Any,
    *keys: str,
) -> List[Dict[str, Any]]:
    copied = [_snapshot(row) for row in (rows or []) if isinstance(row, Mapping)]
    copied.sort(key=lambda row: tuple(str(row.get(key, "")) for key in keys))
    return copied


def _build_metadata_section(
    sources: ReportModelSources,
    generated_timestamp: str,
    tool_version: str,
) -> Dict[str, Any]:
    fr001 = sources.fr001_cpm_report or {}
    manifest = sources.fr009_correlation_manifest or {}
    ate_logs = list(manifest.get("input_ate_logs") or [])
    return {
        "status": _section_status(sources.fr001_cpm_report),
        "workflow": "single_log",
        "stil_filename": fr001.get("file_name") or manifest.get("input_stil"),
        "ate_filename": ate_logs[0] if ate_logs else None,
        "generated_timestamp": generated_timestamp,
        "tool_version": tool_version,
        "report_version": REPORT_VERSION,
        "processing_duration_seconds": fr001.get("processing_duration_seconds"),
    }


def _build_file_information(sources: ReportModelSources) -> Dict[str, Any]:
    fr001 = sources.fr001_cpm_report or {}
    fr002 = sources.fr002_pattern_vectors or {}
    fr003 = sources.fr003_metadata or {}
    scan_chains = fr001.get("scan_chains") or {}
    scan_lengths = []
    for row in scan_chains.values() if isinstance(scan_chains, Mapping) else []:
        try:
            scan_lengths.append(int(row.get("ScanLength") or 0))
        except (TypeError, ValueError):
            continue
    return {
        "status": _section_status(
            sources.fr001_cpm_report,
            sources.fr002_pattern_vectors,
            sources.fr003_metadata,
        ),
        "pattern_count": fr003.get("pattern_count", fr001.get("patterns_count")),
        "scan_chain_count": fr003.get("chain_count", fr001.get("scan_chains_count")),
        "scan_length": fr003.get("max_chain_length")
        or (max(scan_lengths) if scan_lengths else None),
        "compression_ratio": fr003.get("compression_ratio"),
        "total_memory_cells": fr003.get("total_flip_flops"),
        "total_vectors": fr003.get("vector_count", fr002.get("row_count")),
        "file_size_bytes": fr001.get("file_size_bytes"),
        "line_count": fr001.get("line_count"),
        "structural_validation_pass_ratio": fr001.get(
            "structural_validation_pass_ratio"
        ),
        "pattern_vector_artifact": _snapshot(dict(fr002)) if fr002 else {},
    }


def _pattern_ids(sources: ReportModelSources) -> List[str]:
    identifiers = set()
    if sources.fr004_toggle_coverage is not None:
        for row in sources.fr004_toggle_coverage.get("pattern_level") or []:
            if row.get("pattern_id") is not None:
                identifiers.add(str(row["pattern_id"]))
    if sources.fr005_embeddings is not None:
        for row in sources.fr005_embeddings.get("embeddings") or []:
            if row.get("pattern_id") is not None:
                identifiers.add(str(row["pattern_id"]))
    return sorted(identifiers)


def _build_pattern_summary(sources: ReportModelSources) -> Dict[str, Any]:
    fr001 = sources.fr001_cpm_report or {}
    fr003 = sources.fr003_metadata or {}
    pattern_ids = _pattern_ids(sources)
    total = int(
        fr003.get("pattern_count")
        or fr001.get("patterns_count")
        or len(pattern_ids)
        or 0
    )
    structural_ok = fr001.get("status") == "PASS"
    errors = list(fr001.get("errors") or [])
    return {
        "status": _section_status(
            sources.fr001_cpm_report,
            sources.fr003_metadata,
            sources.fr004_toggle_coverage,
        ),
        "total_patterns": total,
        "valid_patterns": total if structural_ok else max(total - len(errors), 0),
        "invalid_patterns": 0 if structural_ok else len(errors),
        "pattern_ids": pattern_ids,
        "pattern_metadata": _sorted_rows(
            (sources.fr004_toggle_coverage or {}).get("pattern_level"),
            "pattern_id",
        ),
    }


def _build_complete_toggle_summary(sources: ReportModelSources) -> Dict[str, Any]:
    payload = sources.fr004_toggle_coverage or {}
    file_rollup = _snapshot(payload.get("file_rollup") or {})
    return {
        "status": _section_status(sources.fr004_toggle_coverage),
        "toggle_coverage_pct": file_rollup.get("toggle_coverage_pct"),
        "toggle_density_pct": file_rollup.get("toggle_density_pct"),
        "coverage_statistics": file_rollup,
        "chain_summaries": _sorted_rows(
            payload.get("scan_chain_level"), "pattern_id", "scan_chain_id"
        ),
        "pattern_summaries": _sorted_rows(payload.get("pattern_level"), "pattern_id"),
    }


def _build_embedding_summary(sources: ReportModelSources) -> Dict[str, Any]:
    payload = sources.fr005_embeddings or {}
    artifact = (sources.artifact_metadata or {}).get("PA-FR-005") or {}
    return {
        "status": _section_status(sources.fr005_embeddings),
        "embedding_version": payload.get("embedding_version"),
        "embedding_dimension": payload.get("embedding_dimension"),
        "similarity_metric": payload.get("similarity_metric"),
        "algorithm": payload.get("algorithm"),
        "total_embeddings": payload.get(
            "patterns_embedded", len(payload.get("embeddings") or [])
        ),
        "patterns_skipped": payload.get("patterns_skipped"),
        "embedding_hash": artifact.get("sha256"),
        "distribution_statistics": _snapshot(
            payload.get("distribution_statistics") or {}
        ),
    }


def _build_complete_clustering_summary(sources: ReportModelSources) -> Dict[str, Any]:
    rollup = sources.fr006_file_rollup or {}
    cluster_payload = sources.fr006_cluster_summary or {}
    assignment_payload = sources.fr006_pattern_clusters or {}
    clusters = _sorted_rows(cluster_payload.get("clusters"), "cluster_id")
    return {
        "status": _section_status(
            sources.fr006_cluster_summary,
            sources.fr006_pattern_clusters,
            sources.fr006_file_rollup,
        ),
        "total_clusters": rollup.get("total_clusters", len(clusters)),
        "cluster_sizes": [
            {
                "cluster_id": row.get("cluster_id"),
                "cluster_size": row.get("cluster_size"),
            }
            for row in clusters
        ],
        "singleton_count": rollup.get("singleton_clusters"),
        "largest_cluster": rollup.get("largest_cluster"),
        "average_cluster_size": rollup.get("average_cluster_size"),
        "threshold": rollup.get(
            "similarity_threshold", assignment_payload.get("similarity_threshold")
        ),
        "cluster_version": rollup.get(
            "cluster_version", cluster_payload.get("cluster_version")
        ),
        "clusters": clusters,
        "pattern_assignments": _sorted_rows(
            assignment_payload.get("patterns"), "pattern_id"
        ),
    }


def _build_complete_redundancy_summary(sources: ReportModelSources) -> Dict[str, Any]:
    payload = sources.fr007_redundancy_candidates or {}
    rollup = sources.fr007_file_rollup or {}
    candidates = _build_redundancy_summary(sources)
    return {
        "status": _section_status(
            sources.fr007_redundancy_candidates,
            sources.fr007_file_rollup,
        ),
        "duplicate_patterns": _snapshot(rollup.get("duplicate_patterns") or []),
        "redundant_patterns": _snapshot(rollup.get("redundant_patterns") or []),
        "total_candidates": rollup.get("total_candidates", len(candidates)),
        "reduction_statistics": _snapshot(
            rollup.get("reduction_statistics") or {}
        ),
        "savings": rollup.get("savings"),
        "redundancy_percentage": rollup.get("redundancy_percentage"),
        "similarity_threshold": payload.get("similarity_threshold"),
        "candidates": candidates,
    }


def _build_complete_similarity_summary(sources: ReportModelSources) -> Dict[str, Any]:
    if sources.fr008_similarity_metadata is not None:
        summary = _snapshot(dict(sources.fr008_similarity_metadata))
        summary.setdefault("status", "Available")
        if isinstance(summary.get("most_similar_pairs"), list):
            summary["most_similar_pairs"] = _sorted_rows(
                summary["most_similar_pairs"],
                "reference_pattern",
                "pattern_a",
                "pattern_b",
                "rank",
            )
        return summary
    embeddings = sources.fr005_embeddings or {}
    return {
        "status": "Partial" if embeddings else "Missing",
        "similarity_metric": embeddings.get("similarity_metric"),
        "embedding_version": embeddings.get("embedding_version"),
        "thresholds": {},
        "similarity_statistics": {},
        "most_similar_pairs": [],
        "distribution_summary": {},
    }


def _build_complete_correlation_summary(sources: ReportModelSources) -> Dict[str, Any]:
    base = _build_correlation_summary(sources)
    patterns = base["patterns"]
    pass_count = sum(int(row.get("pass_count") or 0) for row in patterns)
    fail_count = sum(int(row.get("fail_count") or 0) for row in patterns)
    total = pass_count + fail_count
    base.update(
        {
            "status": _section_status(
                sources.fr009_pattern_outcomes,
                sources.fr009_correlation_manifest,
            ),
            "pass_count": pass_count,
            "fail_count": fail_count,
            "pass_percentage": round(pass_count / total * 100, 4) if total else 0,
            "fail_percentage": round(fail_count / total * 100, 4) if total else 0,
            "pattern_outcome_statistics": {
                "total_patterns": len(patterns),
                "patterns_with_failures": sum(
                    int(row.get("fail_count") or 0) > 0 for row in patterns
                ),
            },
        }
    )
    return base


def _artifact_versions(sources: ReportModelSources) -> Dict[str, Any]:
    versions = {}
    for fr_name, metadata in sorted((sources.artifact_metadata or {}).items()):
        versions[fr_name] = {
            "generated_by": metadata.get("generated_by"),
            "version": metadata.get("version"),
            "sha256": metadata.get("sha256"),
            "status": metadata.get("status"),
        }
    return versions


def _model_hash(model: Mapping[str, Any]) -> str:
    canonical = _snapshot(dict(model))
    metadata = canonical.get("metadata") or {}
    metadata.pop("generated_timestamp", None)
    generation = canonical.get("generation_metadata") or {}
    generation.pop("build_timestamp", None)
    generation.pop("model_hash", None)
    legacy_metadata = canonical.get("report_metadata") or {}
    legacy_metadata.pop("generated_timestamp", None)
    encoded = json.dumps(
        canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_pattern_quality_report_model(
    sources: ReportModelSources,
    *,
    generated_timestamp: str,
    tool_version: str = REPORT_GENERATOR_VERSION,
) -> Dict[str, Any]:
    """
    Assemble and return the canonical Pattern Quality Report model.

    Parameters
    ----------
    sources:
        Read-only upstream FR outputs. Missing optional inputs yield empty sections.
    generated_timestamp:
        ISO-8601 timestamp recorded in report_metadata (caller-supplied for determinism).
    """
    metadata = _build_metadata_section(sources, generated_timestamp, tool_version)
    file_information = _build_file_information(sources)
    pattern_summary = _build_pattern_summary(sources)
    toggle_summary = _build_complete_toggle_summary(sources)
    embedding_summary = _build_embedding_summary(sources)
    clustering_summary = _build_complete_clustering_summary(sources)
    redundancy_summary = _build_complete_redundancy_summary(sources)
    similarity_summary = _build_complete_similarity_summary(sources)
    correlation_summary = _build_complete_correlation_summary(sources)
    section_map = {
        "file_information": file_information,
        "pattern_summary": pattern_summary,
        "toggle_summary": toggle_summary,
        "embedding_summary": embedding_summary,
        "clustering_summary": clustering_summary,
        "redundancy_summary": redundancy_summary,
        "similarity_summary": similarity_summary,
        "correlation_summary": correlation_summary,
    }
    warnings = list(str(item) for item in sources.validation_warnings)
    for section_name, section in section_map.items():
        if section.get("status") != "Available":
            warnings.append(
                f"{section_name} is {str(section.get('status')).lower()}."
            )
    warnings = sorted(set(warnings))
    content_sections = (
        file_information,
        pattern_summary,
        toggle_summary,
        embedding_summary,
        clustering_summary,
        redundancy_summary,
        similarity_summary,
        correlation_summary,
    )
    report_statistics = {
        "total_sections": len(content_sections),
        "available_sections": sum(
            section.get("status") == "Available" for section in content_sections
        ),
        "partial_sections": sum(
            section.get("status") == "Partial" for section in content_sections
        ),
        "missing_sections": sum(
            section.get("status") == "Missing" for section in content_sections
        ),
        "total_tables": sum(
            bool(rows)
            for rows in (
                pattern_summary["pattern_metadata"],
                toggle_summary["pattern_summaries"],
                toggle_summary["chain_summaries"],
                clustering_summary["clusters"],
                clustering_summary["pattern_assignments"],
                redundancy_summary["candidates"],
                similarity_summary.get("most_similar_pairs") or [],
                correlation_summary["patterns"],
                _build_data_quality_appendix(sources),
            )
        ),
        "total_charts_available": 0,
        "total_patterns_analysed": pattern_summary["total_patterns"],
        "total_executions": 1 if metadata.get("ate_filename") else 0,
    }
    generation_metadata = {
        "generated_by": "PA-FR-010.1",
        "report_version": REPORT_VERSION,
        "report_generator_version": tool_version,
        "build_timestamp": generated_timestamp,
        "input_artifact_versions": _artifact_versions(sources),
        "validation_status": "WARNING" if warnings else "PASSED",
        "validation_warnings": warnings,
    }
    model = {
        "generated_by": "PA-FR-010.1",
        "metadata": metadata,
        "file_information": file_information,
        "pattern_summary": pattern_summary,
        "toggle_summary": toggle_summary,
        "embedding_summary": embedding_summary,
        "clustering_summary": clustering_summary,
        "redundancy_summary": redundancy_summary,
        "similarity_summary": similarity_summary,
        "correlation_summary": correlation_summary,
        "report_statistics": report_statistics,
        "generation_metadata": generation_metadata,
        # PA-FR-010.1 pre-release aliases retained for backward compatibility.
        "report_metadata": {
            "generated_timestamp": generated_timestamp,
            "source_versions": _build_source_versions(sources),
        },
        "summary": _build_summary(sources),
        "pattern_statistics": _build_pattern_statistics(sources),
        "cluster_summary": _build_cluster_summary(sources),
        "data_quality_appendix": _build_data_quality_appendix(sources),
    }
    generation_metadata["model_hash"] = _model_hash(model)
    return model


def empty_report_model(generated_timestamp: str = "1970-01-01T00:00:00Z") -> Dict[str, Any]:
    """Return the canonical empty report model shape (all sections present)."""
    return build_pattern_quality_report_model(ReportModelSources(), generated_timestamp=generated_timestamp)


ARTIFACT_FILES = {
    "PA-FR-001": ("PA-FR-001_cpm_report.json",),
    "PA-FR-002": ("PA-FR-002_cvm_cycles.csv",),
    "PA-FR-003": ("PA-FR-003_metadata_metrics.json",),
    "PA-FR-004": ("PA-FR-004_toggle_coverage.json",),
    "PA-FR-005": ("PA-FR-005_pattern_embeddings.json",),
    "PA-FR-006": (
        "PA-FR-006_cluster_summary.json",
        "PA-FR-006_pattern_clusters.json",
        "PA-FR-006_file_rollup.json",
    ),
    "PA-FR-007": (
        "PA-FR-007_redundancy_candidates.json",
        "PA-FR-007_file_rollup.json",
    ),
    "PA-FR-008": ("PA-FR-008_similarity_summary.json",),
    "PA-FR-009": (
        "PA-FR-009_pattern_outcome_table.json",
        "PA-FR-009_correlation_manifest.json",
    ),
}


def _file_sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: str, warnings: List[str]) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        warnings.append(f"Missing artifact: {os.path.basename(path)}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            warnings.append(f"Invalid artifact object: {os.path.basename(path)}")
            return None
        return payload
    except (OSError, json.JSONDecodeError) as exc:
        warnings.append(f"Unreadable artifact {os.path.basename(path)}: {exc}")
        return None


def _read_vector_summary(
    path: str, warnings: List[str]
) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        warnings.append(f"Missing artifact: {os.path.basename(path)}")
        return None
    try:
        with open(path, "r", encoding="utf-8", newline="") as handle:
            rows = (line for line in handle if not line.startswith("#"))
            reader = csv.DictReader(rows)
            row_count = sum(1 for _ in reader)
            return {
                "generated_by": "PA-FR-002",
                "row_count": row_count,
                "columns": list(reader.fieldnames or []),
            }
    except (OSError, csv.Error) as exc:
        warnings.append(f"Unreadable artifact {os.path.basename(path)}: {exc}")
        return None


def _artifact_metadata(
    output_dir: str,
    loaded: Mapping[str, Optional[Mapping[str, Any]]],
) -> Dict[str, Dict[str, Any]]:
    metadata: Dict[str, Dict[str, Any]] = {}
    for fr_name, filenames in ARTIFACT_FILES.items():
        existing = [
            filename
            for filename in filenames
            if os.path.exists(os.path.join(output_dir, filename))
        ]
        hashes = {
            filename: _file_sha256(os.path.join(output_dir, filename))
            for filename in existing
        }
        if not existing:
            status = "Missing"
        elif len(existing) < len(filenames):
            status = "Partial"
        else:
            status = "Available"
        payload = loaded.get(fr_name) or {}
        version = (
            payload.get("correlation_version")
            or payload.get("cluster_version")
            or payload.get("embedding_version")
            or payload.get("version")
        )
        combined = hashlib.sha256(
            json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        metadata[fr_name] = {
            "status": status,
            "generated_by": payload.get("generated_by", fr_name),
            "version": version,
            "sha256": combined,
            "files": hashes,
        }
    return metadata


def load_report_model_sources(output_dir: str) -> ReportModelSources:
    """Load existing single-log FR artifacts without invoking any analysis engine."""
    warnings: List[str] = []
    fr001 = _read_json(os.path.join(output_dir, ARTIFACT_FILES["PA-FR-001"][0]), warnings)
    fr002 = _read_vector_summary(
        os.path.join(output_dir, ARTIFACT_FILES["PA-FR-002"][0]), warnings
    )
    fr003 = _read_json(os.path.join(output_dir, ARTIFACT_FILES["PA-FR-003"][0]), warnings)
    fr004 = _read_json(os.path.join(output_dir, ARTIFACT_FILES["PA-FR-004"][0]), warnings)
    fr005 = _read_json(os.path.join(output_dir, ARTIFACT_FILES["PA-FR-005"][0]), warnings)
    fr006_summary = _read_json(
        os.path.join(output_dir, ARTIFACT_FILES["PA-FR-006"][0]), warnings
    )
    fr006_patterns = _read_json(
        os.path.join(output_dir, ARTIFACT_FILES["PA-FR-006"][1]), warnings
    )
    fr006_rollup = _read_json(
        os.path.join(output_dir, ARTIFACT_FILES["PA-FR-006"][2]), warnings
    )
    fr007_candidates = _read_json(
        os.path.join(output_dir, ARTIFACT_FILES["PA-FR-007"][0]), warnings
    )
    fr007_rollup = _read_json(
        os.path.join(output_dir, ARTIFACT_FILES["PA-FR-007"][1]), warnings
    )
    fr008 = _read_json(os.path.join(output_dir, ARTIFACT_FILES["PA-FR-008"][0]), warnings)
    fr009_outcomes = _read_json(
        os.path.join(output_dir, ARTIFACT_FILES["PA-FR-009"][0]), warnings
    )
    fr009_manifest = _read_json(
        os.path.join(output_dir, ARTIFACT_FILES["PA-FR-009"][1]), warnings
    )
    representative = {
        "PA-FR-001": fr001,
        "PA-FR-002": fr002,
        "PA-FR-003": fr003,
        "PA-FR-004": fr004,
        "PA-FR-005": fr005,
        "PA-FR-006": fr006_rollup or fr006_summary or fr006_patterns,
        "PA-FR-007": fr007_rollup or fr007_candidates,
        "PA-FR-008": fr008,
        "PA-FR-009": fr009_manifest or fr009_outcomes,
    }
    return ReportModelSources(
        fr001_cpm_report=fr001,
        fr002_pattern_vectors=fr002,
        fr003_metadata=fr003,
        fr004_toggle_coverage=fr004,
        fr005_embeddings=fr005,
        fr006_cluster_summary=fr006_summary,
        fr006_pattern_clusters=fr006_patterns,
        fr006_file_rollup=fr006_rollup,
        fr007_redundancy_candidates=fr007_candidates,
        fr007_file_rollup=fr007_rollup,
        fr008_similarity_metadata=fr008,
        fr009_pattern_outcomes=fr009_outcomes,
        fr009_correlation_manifest=fr009_manifest,
        artifact_metadata=_artifact_metadata(output_dir, representative),
        validation_warnings=tuple(warnings),
    )


def build_report_model_from_artifacts(
    output_dir: str,
    *,
    generated_timestamp: Optional[str] = None,
    tool_version: str = REPORT_GENERATOR_VERSION,
) -> Dict[str, Any]:
    """Build PA-FR-010.1 from persisted single-log outputs only."""
    timestamp = generated_timestamp or datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    sources = load_report_model_sources(output_dir)
    return build_pattern_quality_report_model(
        sources,
        generated_timestamp=timestamp,
        tool_version=tool_version,
    )


def write_pattern_quality_report_model(
    output_dir: str,
    *,
    generated_timestamp: Optional[str] = None,
    tool_version: str = REPORT_GENERATOR_VERSION,
) -> Dict[str, Any]:
    """Atomically persist the PA-FR-010.1 model without modifying FR-001..009."""
    model = build_report_model_from_artifacts(
        output_dir,
        generated_timestamp=generated_timestamp,
        tool_version=tool_version,
    )
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, REPORT_MODEL_FILENAME)
    temp_path = f"{path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(model, handle, indent=2, sort_keys=True, ensure_ascii=False)
    os.replace(temp_path, path)
    return model
