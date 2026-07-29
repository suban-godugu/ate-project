"""Shared PA-FR-010 presentation projection.

This module transforms an already-built PA-FR-010.1 report model into ordered,
display-ready sections. It performs no analysis, validation, hashing, or I/O.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping, Optional, Sequence

REPORT_MODEL_FILENAME = "PA-FR-010_report_model.json"
PRESENTATION_VERSION = "1.0"
DEFAULT_TABLE_LIMIT = 10

SECTION_ORDER = (
    "metadata",
    "executive_summary",
    "coverage_summary",
    "embedding_summary",
    "cluster_summary",
    "redundancy_summary",
    "similarity_summary",
    "correlation_summary",
    "validation",
    "appendix",
)


def _number_display(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        return f"{value:,.4f}".rstrip("0").rstrip(".")
    return str(value)


def _percentage_display(value: Any) -> str:
    if value is None:
        return "—"
    return f"{_number_display(value)}%"


def _hash_display(value: Any) -> str:
    text = str(value or "")
    if not text:
        return "—"
    return text if len(text) <= 20 else f"{text[:12]}…{text[-8:]}"


def _timestamp_display(value: Any) -> str:
    text = str(value or "")
    if not text:
        return "—"
    return text.replace("T", " ").replace("Z", " UTC")


def format_cell_value(value: Any) -> str:
    """Format a raw table value consistently across export formats."""
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (list, tuple)):
        return ", ".join(format_cell_value(item) for item in value) or "—"
    if isinstance(value, Mapping):
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    return _number_display(value)


def _kpi(label: str, value: Any, *, kind: str = "number") -> Dict[str, Any]:
    if kind == "percentage":
        display = _percentage_display(value)
    elif kind == "hash":
        display = _hash_display(value)
    elif kind == "timestamp":
        display = _timestamp_display(value)
    else:
        display = _number_display(value)
    return {"label": label, "value": value, "display": display}


def _table(
    title: str,
    rows: Sequence[Mapping[str, Any]] | None,
    columns: Sequence[str],
    *,
    limit: Optional[int],
) -> Dict[str, Any]:
    source_rows = list(rows or [])
    selected = source_rows if limit is None else source_rows[:limit]
    visible = [
        {column: row.get(column) for column in columns}
        for row in selected
    ]
    return {
        "title": title,
        "columns": list(columns),
        "rows": visible,
        "total_rows": len(source_rows),
        "displayed_rows": len(visible),
        "truncated": len(source_rows) > len(visible),
    }


def _section(
    section_id: str,
    title: str,
    status: str,
    *,
    kpis: List[Dict[str, Any]] | None = None,
    tables: List[Dict[str, Any]] | None = None,
    charts: List[Dict[str, Any]] | None = None,
    messages: List[str] | None = None,
) -> Dict[str, Any]:
    return {
        "id": section_id,
        "title": title,
        "status": status,
        "kpis": kpis or [],
        "tables": tables or [],
        "charts": charts or [],
        "messages": messages or [],
    }


def _status(section: Mapping[str, Any] | None) -> str:
    return str((section or {}).get("status") or "Missing")


def _special_limit(
    table_limit: Optional[int],
    preview_limit: int,
) -> Optional[int]:
    return None if table_limit is None else preview_limit


def build_report_presentation(
    report_model: Mapping[str, Any],
    *,
    table_limit: Optional[int] = DEFAULT_TABLE_LIMIT,
) -> Dict[str, Any]:
    """Build the shared ordered presentation.

    ``table_limit=None`` includes every source row for report generation.
    A numeric limit produces the bounded PA-FR-010.2 browser preview.
    """
    metadata = report_model.get("metadata") or {}
    file_info = report_model.get("file_information") or {}
    toggle = report_model.get("toggle_summary") or {}
    embedding = report_model.get("embedding_summary") or {}
    clustering = report_model.get("clustering_summary") or {}
    redundancy = report_model.get("redundancy_summary") or {}
    similarity = report_model.get("similarity_summary") or {}
    correlation = report_model.get("correlation_summary") or {}
    statistics = report_model.get("report_statistics") or {}
    generation = report_model.get("generation_metadata") or {}

    cluster_sizes = list(clustering.get("cluster_sizes") or [])
    chart_cluster_sizes = (
        cluster_sizes if table_limit is None else cluster_sizes[:20]
    )
    sections = [
        _section(
            "metadata",
            "Metadata",
            _status(metadata),
            kpis=[
                _kpi("STIL File", metadata.get("stil_filename"), kind="text"),
                _kpi("ATE File", metadata.get("ate_filename"), kind="text"),
                _kpi("Report Version", metadata.get("report_version"), kind="text"),
                _kpi(
                    "Generated",
                    metadata.get("generated_timestamp"),
                    kind="timestamp",
                ),
            ],
        ),
        _section(
            "executive_summary",
            "Executive Summary",
            "Available",
            kpis=[
                _kpi("Patterns", statistics.get("total_patterns_analysed")),
                _kpi("Executions", statistics.get("total_executions")),
                _kpi("Available Sections", statistics.get("available_sections")),
                _kpi("Partial Sections", statistics.get("partial_sections")),
                _kpi("Missing Sections", statistics.get("missing_sections")),
                _kpi("Model Hash", generation.get("model_hash"), kind="hash"),
            ],
            tables=[
                _table(
                    "File Information",
                    [file_info],
                    (
                        "pattern_count",
                        "scan_chain_count",
                        "scan_length",
                        "compression_ratio",
                        "total_memory_cells",
                        "total_vectors",
                    ),
                    limit=1,
                )
            ],
        ),
        _section(
            "coverage_summary",
            "Coverage Summary",
            _status(toggle),
            kpis=[
                _kpi(
                    "Toggle Coverage",
                    toggle.get("toggle_coverage_pct"),
                    kind="percentage",
                ),
                _kpi(
                    "Toggle Density",
                    toggle.get("toggle_density_pct"),
                    kind="percentage",
                ),
            ],
            tables=[
                _table(
                    "Pattern Coverage",
                    toggle.get("pattern_summaries"),
                    (
                        "pattern_id",
                        "toggle_count",
                        "toggle_coverage_pct",
                        "toggle_density_pct",
                    ),
                    limit=table_limit,
                ),
                _table(
                    "Scan Chain Coverage",
                    toggle.get("chain_summaries"),
                    (
                        "pattern_id",
                        "scan_chain_id",
                        "toggle_count",
                        "toggle_coverage_pct",
                    ),
                    limit=table_limit,
                ),
            ],
            charts=[
                {
                    "type": "percentage_bars",
                    "title": "Coverage and Density",
                    "data": [
                        {
                            "label": "Toggle Coverage",
                            "value": toggle.get("toggle_coverage_pct"),
                        },
                        {
                            "label": "Toggle Density",
                            "value": toggle.get("toggle_density_pct"),
                        },
                    ],
                }
            ],
        ),
        _section(
            "embedding_summary",
            "Embedding Summary",
            _status(embedding),
            kpis=[
                _kpi("Embeddings", embedding.get("total_embeddings")),
                _kpi("Dimension", embedding.get("embedding_dimension")),
                _kpi(
                    "Embedding Version",
                    embedding.get("embedding_version"),
                    kind="text",
                ),
                _kpi(
                    "Similarity Metric",
                    embedding.get("similarity_metric"),
                    kind="text",
                ),
                _kpi("Embedding Hash", embedding.get("embedding_hash"), kind="hash"),
            ],
            tables=[
                _table(
                    "Distribution Statistics",
                    [
                        {"metric": key, "value": value}
                        for key, value in sorted(
                            (embedding.get("distribution_statistics") or {}).items()
                        )
                    ],
                    ("metric", "value"),
                    limit=table_limit,
                )
            ],
        ),
        _section(
            "cluster_summary",
            "Cluster Summary",
            _status(clustering),
            kpis=[
                _kpi("Clusters", clustering.get("total_clusters")),
                _kpi("Singletons", clustering.get("singleton_count")),
                _kpi("Largest Cluster", clustering.get("largest_cluster")),
                _kpi("Average Size", clustering.get("average_cluster_size")),
                _kpi("Threshold", clustering.get("threshold")),
                _kpi(
                    "Cluster Version", clustering.get("cluster_version"), kind="text"
                ),
            ],
            tables=[
                _table(
                    "Clusters",
                    clustering.get("clusters"),
                    (
                        "cluster_id",
                        "cluster_size",
                        "representative_pattern",
                        "average_similarity",
                    ),
                    limit=table_limit,
                )
            ],
            charts=[
                {
                    "type": "bar",
                    "title": "Cluster Sizes",
                    "data": chart_cluster_sizes,
                }
            ],
        ),
        _section(
            "redundancy_summary",
            "Redundancy Summary",
            _status(redundancy),
            kpis=[
                _kpi("Candidates", redundancy.get("total_candidates")),
                _kpi(
                    "Redundancy",
                    redundancy.get("redundancy_percentage"),
                    kind="percentage",
                ),
                _kpi("Savings", redundancy.get("savings")),
                _kpi("Threshold", redundancy.get("similarity_threshold")),
            ],
            tables=[
                _table(
                    "Redundancy Candidates",
                    redundancy.get("candidates"),
                    (
                        "pattern_a",
                        "pattern_b",
                        "cluster_id",
                        "raw_similarity",
                        "confidence_score",
                        "review_status",
                    ),
                    limit=table_limit,
                )
            ],
        ),
        _section(
            "similarity_summary",
            "Similarity Summary",
            _status(similarity),
            kpis=[
                _kpi(
                    "Metric", similarity.get("similarity_metric"), kind="text"
                ),
                _kpi(
                    "Embedding Version",
                    similarity.get("embedding_version"),
                    kind="text",
                ),
            ],
            tables=[
                _table(
                    "Most Similar Pairs",
                    similarity.get("most_similar_pairs"),
                    ("pattern_a", "pattern_b", "similarity", "rank"),
                    limit=table_limit,
                )
            ],
            charts=[
                {
                    "type": "distribution",
                    "title": "Similarity Distribution",
                    "data": similarity.get("distribution_summary") or {},
                }
            ],
        ),
        _section(
            "correlation_summary",
            "Correlation Summary",
            _status(correlation),
            kpis=[
                _kpi("PASS", correlation.get("pass_count")),
                _kpi("FAIL", correlation.get("fail_count")),
                _kpi(
                    "Pass Percentage",
                    correlation.get("pass_percentage"),
                    kind="percentage",
                ),
                _kpi(
                    "Fail Percentage",
                    correlation.get("fail_percentage"),
                    kind="percentage",
                ),
                _kpi(
                    "Validation",
                    correlation.get("validation_status"),
                    kind="text",
                ),
                _kpi(
                    "Correlation Hash",
                    correlation.get("correlation_hash"),
                    kind="hash",
                ),
            ],
            tables=[
                _table(
                    "Pattern Outcomes",
                    correlation.get("patterns"),
                    (
                        "pattern_id",
                        "scan_chain_id",
                        "latest_result",
                        "pass_count",
                        "fail_count",
                        "data_quality_flags",
                    ),
                    limit=table_limit,
                )
            ],
            charts=[
                {
                    "type": "donut",
                    "title": "PASS / FAIL",
                    "data": [
                        {"label": "PASS", "value": correlation.get("pass_count")},
                        {"label": "FAIL", "value": correlation.get("fail_count")},
                    ],
                }
            ],
        ),
        _section(
            "validation",
            "Validation",
            str(generation.get("validation_status") or "Missing"),
            kpis=[
                _kpi(
                    "Validation Status",
                    generation.get("validation_status"),
                    kind="text",
                ),
                _kpi(
                    "Warnings",
                    len(generation.get("validation_warnings") or []),
                ),
            ],
            messages=list(generation.get("validation_warnings") or []),
        ),
        _section(
            "appendix",
            "Appendix",
            "Available",
            tables=[
                _table(
                    "Artifact Provenance",
                    [
                        {
                            "artifact": artifact,
                            "status": details.get("status"),
                            "version": details.get("version"),
                            "sha256": details.get("sha256"),
                        }
                        for artifact, details in sorted(
                            (generation.get("input_artifact_versions") or {}).items()
                        )
                    ],
                    ("artifact", "status", "version", "sha256"),
                    limit=_special_limit(table_limit, 100),
                ),
                _table(
                    "Data Quality",
                    report_model.get("data_quality_appendix") or [],
                    ("pattern_id", "scan_chain_id", "data_quality_flags"),
                    limit=_special_limit(table_limit, 20),
                ),
            ],
        ),
    ]

    provenance = {
        "report_hash": generation.get("report_hash"),
        "model_hash": generation.get("model_hash"),
        "model_hash_display": _hash_display(generation.get("model_hash")),
        "generation_timestamp": generation.get("build_timestamp")
        or metadata.get("generated_timestamp"),
        "generation_timestamp_display": _timestamp_display(
            generation.get("build_timestamp") or metadata.get("generated_timestamp")
        ),
        "artifacts": generation.get("input_artifact_versions") or {},
    }
    return {
        "generated_by": "PA-FR-010.2",
        "preview_version": PRESENTATION_VERSION,
        "source_artifact": REPORT_MODEL_FILENAME,
        "section_order": list(SECTION_ORDER),
        "sections": sections,
        "validation": {
            "status": generation.get("validation_status"),
            "warnings": list(generation.get("validation_warnings") or []),
        },
        "provenance": provenance,
    }
