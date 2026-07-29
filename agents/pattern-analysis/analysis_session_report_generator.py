"""PA-FR-010.AS.3 Analysis Session report generation orchestrator."""
from __future__ import annotations

import copy
import json
import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Mapping, Sequence

from analysis_session_report_export_excel import export_analysis_session_excel
from analysis_session_report_export_html import export_analysis_session_html
from analysis_session_report_export_pdf import export_analysis_session_pdf


REPORT_MODEL_FILENAME = "PA-Analysis-Session_report_model.json"


class AnalysisSessionReportGenerationError(ValueError):
    """Raised for unsupported Analysis Session report generation requests."""


class AnalysisSessionReportModelError(RuntimeError):
    """Raised when the Analysis Session report model cannot be loaded."""


@dataclass(frozen=True)
class GeneratedAnalysisSessionReport:
    content: bytes
    media_type: str
    filename: str
    model_hash: str


Exporter = Callable[[Mapping[str, Any]], bytes]

EXPORTERS: Dict[str, tuple[Exporter, str, str]] = {
    "html": (
        export_analysis_session_html,
        "text/html; charset=utf-8",
        "PA-Analysis-Session_quality_report.html",
    ),
    "pdf": (
        export_analysis_session_pdf,
        "application/pdf",
        "PA-Analysis-Session_quality_report.pdf",
    ),
    "excel": (
        export_analysis_session_excel,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "PA-Analysis-Session_quality_report.xlsx",
    ),
}

EXPORT_SECTION_ORDER = (
    "overview",
    "session_summary",
    "requirement_1_ingestion",
    "requirement_2_vectors",
    "requirement_3_metadata",
    "requirement_4_toggle",
    "embeddings",
    "clustering",
    "redundancy",
    "similarity",
    "pattern_outcomes",
    "anomaly_by_lot",
    "anomaly",
    "root_cause_by_lot",
    "root_cause",
    "recommendations_by_lot",
    "recommendations",
    "failure_risk_by_lot",
    "failure_risk",
    "validation",
    "appendix",
)


def _snapshot(value: Any) -> Any:
    return copy.deepcopy(value)


def _display(value: Any) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        return f"{value:,.4f}".rstrip("0").rstrip(".")
    if isinstance(value, (list, tuple)):
        return ", ".join(_display(item) for item in value) or "—"
    if isinstance(value, Mapping):
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    return str(value)


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


def _kpi(label: str, value: Any, *, kind: str = "number") -> Dict[str, Any]:
    if kind == "hash":
        display = _hash_display(value)
    elif kind == "timestamp":
        display = _timestamp_display(value)
    else:
        display = _display(value)
    return {"label": label, "value": _snapshot(value), "display": display}


def _table(
    title: str,
    rows: Sequence[Mapping[str, Any]] | None,
    columns: Sequence[str],
) -> Dict[str, Any]:
    source_rows = [row for row in (rows or []) if isinstance(row, Mapping)]
    visible = [
        {column: _snapshot(row.get(column)) for column in columns}
        for row in source_rows
    ]
    return {
        "title": title,
        "columns": list(columns),
        "rows": visible,
        "total_rows": len(visible),
        "displayed_rows": len(visible),
        "truncated": False,
    }


def _mapping_rows(
    values: Mapping[str, Any] | None,
    key_name: str,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for key, value in sorted((values or {}).items(), key=lambda item: str(item[0])):
        row = {key_name: key}
        if isinstance(value, Mapping):
            row.update(_snapshot(dict(value)))
        else:
            row["value"] = _snapshot(value)
        rows.append(row)
    return rows


def _section(
    section_id: str,
    title: str,
    status: str,
    *,
    kpis: Sequence[Mapping[str, Any]] = (),
    tables: Sequence[Mapping[str, Any]] = (),
    charts: Sequence[Mapping[str, Any]] = (),
    messages: Sequence[str] = (),
    purpose: str = "",
    summary: str = "",
    findings: Sequence[str] = (),
) -> Dict[str, Any]:
    return {
        "id": section_id,
        "title": title,
        "status": status,
        "purpose": purpose,
        "summary": summary,
        "findings": _snapshot(list(findings)),
        "kpis": _snapshot(list(kpis)),
        "tables": _snapshot(list(tables)),
        "charts": _snapshot(list(charts)),
        "messages": _snapshot(list(messages)),
    }


def _charts_from_data(data: Mapping[str, Any]) -> List[Dict[str, Any]]:
    charts = data.get("charts")
    if not isinstance(charts, list):
        return []
    return [dict(chart) for chart in charts if isinstance(chart, Mapping)]


def _manifest_display_row(manifest: Mapping[str, Any] | None) -> List[Dict[str, Any]]:
    """Compact manifest row for HTML — never dump the full ATE log list into one cell."""
    if not isinstance(manifest, Mapping):
        return []
    logs = manifest.get("input_ate_logs")
    if isinstance(logs, list):
        log_count = len(logs)
        preview_parts = [str(item) for item in logs[:5]]
        preview = ", ".join(preview_parts)
        if log_count > 5:
            preview = f"{preview} … (+{log_count - 5} more)"
    elif logs is None:
        log_count = manifest.get("execution_count")
        preview = "—"
    else:
        log_count = 1
        preview = str(logs)
    return [
        {
            "stil_file": manifest.get("stil_file"),
            "session_hash": manifest.get("session_hash"),
            "generated_timestamp": manifest.get("generated_timestamp"),
            "ate_log_count": log_count,
            "ate_logs_preview": preview,
        }
    ]


def _ranked_similarity_pattern_rows(
    rows: Sequence[Any] | None,
) -> List[Dict[str, Any]]:
    """Map stable/divergent artifact fields to display columns (rank, pattern_id, average)."""
    cleaned = [row for row in (rows or []) if isinstance(row, Mapping)]
    ranked: List[Dict[str, Any]] = []
    for index, row in enumerate(cleaned, start=1):
        ranked.append(
            {
                "rank": index,
                "pattern_id": row.get("pattern_id"),
                "average_similarity": row.get("average_similarity"),
            }
        )
    return ranked


def _model_sections(report_model: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    return {
        str(section.get("id")): section
        for section in (report_model.get("sections") or [])
        if isinstance(section, Mapping)
    }


def _section_data(
    sections: Mapping[str, Mapping[str, Any]],
    section_id: str,
) -> Mapping[str, Any]:
    data = (sections.get(section_id) or {}).get("data")
    return data if isinstance(data, Mapping) else {}


def _section_status(
    sections: Mapping[str, Mapping[str, Any]],
    section_id: str,
) -> str:
    return str((sections.get(section_id) or {}).get("status") or "Missing")


def _section_messages(
    sections: Mapping[str, Mapping[str, Any]],
    section_id: str,
) -> List[str]:
    warnings = (sections.get(section_id) or {}).get("warnings")
    return list(warnings) if isinstance(warnings, list) else []


def _combined_status(first: str, second: str) -> str:
    if first == "Complete" and second == "Complete":
        return "Complete"
    if first == "Missing" and second == "Missing":
        return "Missing"
    return "Partial"


def _build_export_projection(
    report_model: Mapping[str, Any],
) -> Dict[str, Any]:
    metadata = report_model.get("metadata")
    metadata = metadata if isinstance(metadata, Mapping) else {}
    validation = report_model.get("validation")
    validation = validation if isinstance(validation, Mapping) else {}
    provenance = report_model.get("provenance")
    provenance = provenance if isinstance(provenance, Mapping) else {}
    hashes = report_model.get("hashes")
    hashes = hashes if isinstance(hashes, Mapping) else {}
    summary = report_model.get("summary")
    summary = summary if isinstance(summary, Mapping) else {}
    sections = _model_sections(report_model)

    overview_status = _section_status(sections, "session_overview")
    overview_data = _section_data(sections, "session_overview")
    coverage_data = _section_data(sections, "toggle_coverage")
    scan_data = _section_data(sections, "scan_vectors")
    embedding_data = _section_data(sections, "embeddings")
    clustering_data = _section_data(sections, "clustering")
    redundancy_data = _section_data(sections, "redundancy")
    similarity_data = _section_data(sections, "similarity")
    outcomes_data = _section_data(sections, "pattern_outcomes")
    failure_risk_by_lot_data = _section_data(sections, "failure_risk_by_lot")
    failure_risk_data = _section_data(sections, "failure_risk")
    anomaly_by_lot_data = _section_data(sections, "anomaly_by_lot")
    anomaly_data = _section_data(sections, "anomaly")
    root_cause_by_lot_data = _section_data(sections, "root_cause_by_lot")
    root_cause_data = _section_data(sections, "root_cause")
    recommendations_by_lot_data = _section_data(sections, "recommendations_by_lot")
    recommendations_data = _section_data(sections, "recommendations")
    has_anomaly_by_lot = any(
        isinstance(section, Mapping) and section.get("id") == "anomaly_by_lot"
        for section in (report_model.get("sections") or [])
    )
    has_anomaly = any(
        isinstance(section, Mapping) and section.get("id") == "anomaly"
        for section in (report_model.get("sections") or [])
    )
    has_failure_risk_by_lot = any(
        isinstance(section, Mapping) and section.get("id") == "failure_risk_by_lot"
        for section in (report_model.get("sections") or [])
    )
    has_failure_risk = any(
        isinstance(section, Mapping) and section.get("id") == "failure_risk"
        for section in (report_model.get("sections") or [])
    )
    has_root_cause_by_lot = any(
        isinstance(section, Mapping) and section.get("id") == "root_cause_by_lot"
        for section in (report_model.get("sections") or [])
    )
    has_root_cause = any(
        isinstance(section, Mapping) and section.get("id") == "root_cause"
        for section in (report_model.get("sections") or [])
    )
    has_recommendations_by_lot = any(
        isinstance(section, Mapping) and section.get("id") == "recommendations_by_lot"
        for section in (report_model.get("sections") or [])
    )
    has_recommendations = any(
        isinstance(section, Mapping) and section.get("id") == "recommendations"
        for section in (report_model.get("sections") or [])
    )

    coverage_summary = coverage_data.get("summary")
    coverage_summary = (
        coverage_summary if isinstance(coverage_summary, Mapping) else {}
    )
    execution_payload = coverage_data.get("executions")
    execution_payload = (
        execution_payload if isinstance(execution_payload, Mapping) else {}
    )
    provenance_records = provenance.get("artifacts")
    provenance_records = (
        provenance_records if isinstance(provenance_records, list) else []
    )
    warnings = validation.get("warnings")
    warnings = list(warnings) if isinstance(warnings, list) else []

    coverage_kpis = coverage_data.get("kpis")
    coverage_kpis = coverage_kpis if isinstance(coverage_kpis, Mapping) else {}
    validation_data = _section_data(sections, "validation")
    completion_pct = (
        validation_data.get("completion_pct")
        if validation_data.get("completion_pct") is not None
        else summary.get("completion_pct")
    )
    engineering_status = summary.get("engineering_status") or (
        "ENGINEERING ANALYSIS COMPLETE"
        if str(validation.get("status")) == "Complete"
        else "ENGINEERING ANALYSIS PARTIAL"
    )

    export_sections = [
        _section(
            "overview",
            "Cover — Session Identity",
            overview_status,
            purpose="Identify the Analysis Session under review.",
            summary="STIL, session hash, LOT/ATE scale, and engineering completion badge.",
            kpis=[
                _kpi("STIL File", metadata.get("stil_filename")),
                _kpi("Session Hash", metadata.get("session_hash"), kind="hash"),
                _kpi(
                    "Generated",
                    metadata.get("generated_timestamp"),
                    kind="timestamp",
                ),
                _kpi("LOTs", metadata.get("lot_count")),
                _kpi("ATE Logs", metadata.get("ate_log_count")),
                _kpi("Patterns", metadata.get("pattern_count") or summary.get("pattern_count")),
                _kpi("Execution Records", metadata.get("execution_record_count")),
                _kpi("Completion %", completion_pct),
                _kpi("Engineering Status", engineering_status),
                _kpi("Report Version", "2.0"),
                _kpi("Model Hash", hashes.get("model_hash"), kind="hash"),
            ],
            findings=[
                "This report is a presentation of deterministic Analysis Session artifacts.",
                "Full detail remains in PA-Analysis-Session_*.json; tables below show Top-N only.",
            ],
        ),
        _section(
            "session_summary",
            "Executive Summary & Engineering Dashboard",
            overview_status,
            purpose="One-page view of dataset scale and pipeline completion.",
            summary="Key session counts and requirement readiness for engineering review.",
            kpis=[
                _kpi("LOTs", summary.get("lot_count")),
                _kpi("ATE Logs", summary.get("ate_log_count")),
                _kpi("Executions", summary.get("execution_count")),
                _kpi("Execution Records", summary.get("execution_record_count")),
                _kpi("Patterns", summary.get("pattern_count") or metadata.get("pattern_count")),
                _kpi("Completion %", completion_pct),
                _kpi("Toggle Coverage Avg %", coverage_kpis.get("toggle_coverage_pct_avg")),
                _kpi("Embeddings", embedding_data.get("patterns_embedded")),
                _kpi("Clusters", clustering_data.get("total_clusters")),
                _kpi("Redundancy Candidates", redundancy_data.get("total_candidates")),
                _kpi(
                    "Similarity Pairs",
                    (similarity_data.get("summary") or {}).get("total_similarity_pairs")
                    if isinstance(similarity_data.get("summary"), Mapping)
                    else None,
                ),
                _kpi("FAIL Outcomes", outcomes_data.get("fail_count")),
            ],
            tables=[
                _table(
                    "Manifest",
                    _manifest_display_row(
                        overview_data.get("manifest")
                        if isinstance(overview_data.get("manifest"), Mapping)
                        else None
                    ),
                    (
                        "stil_file",
                        "session_hash",
                        "generated_timestamp",
                        "ate_log_count",
                        "ate_logs_preview",
                    ),
                )
            ],
            messages=_section_messages(sections, "session_overview"),
            findings=[
                f"Engineering status: {engineering_status}",
                f"Validation: {validation.get('status') or '—'}",
            ],
        ),
        _section(
            "requirement_1_ingestion",
            "Requirement 1 — Ingest pattern files",
            _section_status(sections, "session_overview"),
            purpose="STIL structural ingest and session manifest for the Analysis Session.",
            summary="Authoritative STIL source, session identity, and ATE log inventory from PA-FR-001.",
            kpis=[
                _kpi("STIL File", metadata.get("stil_filename")),
                _kpi("Session Hash", metadata.get("session_hash"), kind="hash"),
                _kpi(
                    "Generated",
                    metadata.get("generated_timestamp"),
                    kind="timestamp",
                ),
                _kpi("LOTs", metadata.get("lot_count")),
                _kpi("ATE Logs", metadata.get("ate_log_count")),
            ],
            tables=[
                _table(
                    "Manifest",
                    _manifest_display_row(
                        overview_data.get("manifest")
                        if isinstance(overview_data.get("manifest"), Mapping)
                        else None
                    ),
                    (
                        "stil_file",
                        "session_hash",
                        "generated_timestamp",
                        "ate_log_count",
                        "ate_logs_preview",
                    ),
                )
            ],
            messages=_section_messages(sections, "session_overview"),
            findings=[
                "Requirement 1 confirms the STIL stimulus and session manifest are present and readable.",
            ],
        ),
        _section(
            "requirement_2_vectors",
            "Requirement 2 — Parse patterns and vectors",
            _section_status(sections, "scan_vectors"),
            purpose="Scan vector materialization (CVM) for pattern×log execution units.",
            summary="Reconstructed scan vectors from the session pipeline (PA-FR-002).",
            kpis=[
                _kpi("Scan Vectors", scan_data.get("vector_count")),
            ],
            tables=[
                _table(
                    "Top Scan Vectors",
                    scan_data.get("vectors"),
                    (
                        "pattern_id",
                        "source_log",
                        "source_log_relpath",
                        "run_id",
                    ),
                ),
            ],
            charts=_charts_from_data(scan_data),
            messages=_section_messages(sections, "scan_vectors"),
            findings=[
                "Full vector rows remain in session artifacts; HTML shows Top-N only.",
            ],
        ),
        _section(
            "requirement_3_metadata",
            "Requirement 3 — Extract metadata features",
            _combined_status(
                _section_status(sections, "session_overview"),
                _section_status(sections, "toggle_coverage"),
            ),
            purpose="Session-scale metadata and pattern×chain inventory derived from ingest and summary artifacts.",
            summary="Pattern counts, execution inventory, and summary rollups (PA-FR-003 context).",
            kpis=[
                _kpi("Patterns", metadata.get("pattern_count") or summary.get("pattern_count")),
                _kpi(
                    "Execution Records",
                    metadata.get("execution_record_count")
                    or summary.get("execution_record_count"),
                ),
                _kpi(
                    "Pattern×Chain Keys",
                    (
                        (overview_data.get("summary") or {}).get("by_pattern_chain_total")
                        if isinstance(overview_data.get("summary"), Mapping)
                        else None
                    ),
                ),
                _kpi("Executions", summary.get("execution_count")),
            ],
            tables=[
                _table(
                    "Top Pattern / Chain Summary",
                    _mapping_rows(
                        (
                            (overview_data.get("summary") or {}).get("by_pattern_chain")
                            if isinstance(overview_data.get("summary"), Mapping)
                            else coverage_summary.get("by_pattern_chain")
                        ),
                        "pattern_chain",
                    ),
                    (
                        "pattern_chain",
                        "execution_count",
                        "pass_count",
                        "fail_count",
                    ),
                ),
            ],
            messages=_section_messages(sections, "session_overview"),
            findings=[
                "Metadata is presented from existing session summary artifacts without recomputation.",
            ],
        ),
        _section(
            "requirement_4_toggle",
            "Requirement 4 — Pattern toggle coverage",
            _section_status(sections, "toggle_coverage"),
            purpose="Toggle coverage and density across ATE execution records.",
            summary="Per-execution toggle metrics and PASS/FAIL outcomes from PA-FR-004.",
            kpis=[
                _kpi("Execution Records", coverage_kpis.get("execution_records")),
                _kpi("PASS", coverage_kpis.get("pass_count")),
                _kpi("FAIL", coverage_kpis.get("fail_count")),
                _kpi("Coverage Avg %", coverage_kpis.get("toggle_coverage_pct_avg")),
                _kpi("Coverage Max %", coverage_kpis.get("toggle_coverage_pct_max")),
                _kpi("Coverage Min %", coverage_kpis.get("toggle_coverage_pct_min")),
                _kpi("Density Avg %", coverage_kpis.get("toggle_density_pct_avg")),
            ],
            tables=[
                _table(
                    "Top Pattern / Chain Coverage",
                    _mapping_rows(
                        coverage_summary.get("by_pattern_chain"),
                        "pattern_chain",
                    ),
                    (
                        "pattern_chain",
                        "execution_count",
                        "pass_count",
                        "fail_count",
                        "toggle_coverage_pct_avg",
                        "toggle_coverage_pct_max",
                        "toggle_coverage_pct_min",
                        "toggle_density_pct_avg",
                    ),
                ),
                _table(
                    "Top Executions",
                    execution_payload.get("executions"),
                    (
                        "pattern_id",
                        "scan_chain_id",
                        "source_log",
                        "source_log_relpath",
                        "run_id",
                        "toggle_count",
                        "toggle_coverage_pct",
                        "toggle_density_pct",
                        "latest_result",
                    ),
                ),
            ],
            charts=_charts_from_data(coverage_data),
            messages=_section_messages(sections, "toggle_coverage"),
            findings=[
                "Full execution rows remain in session artifacts; HTML shows Top-N only.",
            ],
        ),
        _section(
            "embeddings",
            "Requirement 5 — Pattern Embeddings",
            _section_status(sections, "embeddings"),
            purpose="Convert pattern×log units into fixed-dimension vectors for clustering and similarity.",
            summary="Deterministic per-execution embeddings with vectors omitted from the presentation model.",
            kpis=[
                _kpi("Embeddings", embedding_data.get("patterns_embedded")),
                _kpi("Skipped", embedding_data.get("patterns_skipped")),
                _kpi("Dimension", embedding_data.get("embedding_dimension")),
                _kpi("Version", embedding_data.get("embedding_version")),
                _kpi("Metric", embedding_data.get("similarity_metric")),
            ],
            tables=[
                _table(
                    "Top Embeddings (metadata)",
                    embedding_data.get("embeddings"),
                    (
                        "pattern_id",
                        "source_log",
                        "source_log_relpath",
                        "run_id",
                        "feature_version",
                        "created_timestamp",
                    ),
                )
            ],
            charts=_charts_from_data(embedding_data),
            messages=_section_messages(sections, "embeddings"),
            findings=[
                f"Source artifact: {(embedding_data.get('source') or {}).get('artifact_filename') or 'PA-Analysis-Session_embeddings.json'}",
            ],
        ),
        _section(
            "clustering",
            "Requirement 6 — Pattern Clustering",
            _section_status(sections, "clustering"),
            purpose="Group similar pattern×log units into clusters for redundancy and review focus.",
            summary="Clusters learned from a capped sample; all units assigned to nearest centroid.",
            kpis=[
                _kpi("Clusters", clustering_data.get("total_clusters")),
                _kpi("Units", clustering_data.get("units_total")),
                _kpi("Singletons", clustering_data.get("singleton_clusters")),
                _kpi("Largest Cluster", clustering_data.get("largest_cluster")),
                _kpi("Average Size", clustering_data.get("average_cluster_size")),
                _kpi("Threshold", clustering_data.get("similarity_threshold")),
            ],
            tables=[
                _table(
                    "Largest Clusters",
                    clustering_data.get("clusters"),
                    (
                        "cluster_id",
                        "representative_pattern",
                        "pattern_count",
                        "execution_count",
                        "average_similarity",
                    ),
                ),
                _table(
                    "Top Unit Assignments",
                    clustering_data.get("unit_assignments"),
                    (
                        "unit_id",
                        "pattern_id",
                        "source_lot",
                        "source_log",
                        "run_id",
                        "cluster_id",
                        "similarity_to_centroid",
                    ),
                ),
            ],
            charts=_charts_from_data(clustering_data),
            messages=_section_messages(sections, "clustering"),
        ),
        _section(
            "redundancy",
            "Requirement 7 — Redundancy",
            _section_status(sections, "redundancy"),
            purpose="Flag near-duplicate units within clusters for engineering review.",
            summary="Bounded nearest-neighbor candidates with embedding-only confidence scores.",
            kpis=[
                _kpi("Candidates", redundancy_data.get("total_candidates")),
                _kpi("Units Represented", redundancy_data.get("units_represented")),
                _kpi("Clusters Evaluated", redundancy_data.get("clusters_evaluated")),
                _kpi("Threshold", redundancy_data.get("similarity_threshold")),
                _kpi("Avg Confidence", redundancy_data.get("average_confidence")),
                _kpi("Highest Confidence", redundancy_data.get("highest_confidence")),
            ],
            tables=[
                _table(
                    "Top Redundancy Candidates",
                    redundancy_data.get("candidates"),
                    (
                        "pattern_a",
                        "pattern_b",
                        "source_lot_a",
                        "source_lot_b",
                        "cluster_id",
                        "raw_similarity",
                        "confidence_score",
                        "review_status",
                    ),
                )
            ],
            charts=_charts_from_data(redundancy_data),
            messages=_section_messages(sections, "redundancy"),
        ),
        _section(
            "similarity",
            "Requirement 8 — Similarity",
            _section_status(sections, "similarity"),
            purpose="Exact top-N cosine neighbors for every pattern×source-log unit.",
            summary="Deterministic similarity artifact with bounded top neighbors (no ANN).",
            kpis=[
                _kpi("Metric", similarity_data.get("similarity_metric")),
                _kpi("Embedding Version", similarity_data.get("embedding_version")),
                _kpi(
                    "Units",
                    (similarity_data.get("summary") or {}).get("total_units")
                    if isinstance(similarity_data.get("summary"), Mapping)
                    else None,
                ),
                _kpi(
                    "Pairs",
                    (similarity_data.get("summary") or {}).get("total_similarity_pairs")
                    if isinstance(similarity_data.get("summary"), Mapping)
                    else None,
                ),
                _kpi(
                    "Average Similarity",
                    (similarity_data.get("summary") or {}).get("average_similarity")
                    if isinstance(similarity_data.get("summary"), Mapping)
                    else None,
                ),
                _kpi(
                    "Max Similarity",
                    (similarity_data.get("summary") or {}).get("maximum_similarity")
                    if isinstance(similarity_data.get("summary"), Mapping)
                    else None,
                ),
            ],
            tables=[
                _table(
                    "Top Similarity Pairs",
                    similarity_data.get("similarity_pairs"),
                    (
                        "unit_a",
                        "unit_b",
                        "pattern_a",
                        "pattern_b",
                        "rank",
                        "cosine_similarity",
                    ),
                ),
                _table(
                    "Stable Patterns",
                    _ranked_similarity_pattern_rows(
                        similarity_data.get("stable_patterns")
                    ),
                    ("rank", "pattern_id", "average_similarity"),
                ),
                _table(
                    "Divergent Patterns",
                    _ranked_similarity_pattern_rows(
                        similarity_data.get("divergent_patterns")
                    ),
                    ("rank", "pattern_id", "average_similarity"),
                ),
            ],
            charts=_charts_from_data(similarity_data),
            messages=_section_messages(sections, "similarity"),
        ),
        _section(
            "pattern_outcomes",
            "Requirement 9 — Pattern Outcome Correlation",
            _section_status(sections, "pattern_outcomes"),
            purpose="Correlate pattern outcomes across LOTs and executions.",
            summary="PASS/FAIL outcome aggregation for multi-LOT session review.",
            kpis=[
                _kpi("PASS", outcomes_data.get("pass_count")),
                _kpi("FAIL", outcomes_data.get("fail_count")),
                _kpi("Unknown", outcomes_data.get("unknown_count")),
                _kpi("Outcomes", outcomes_data.get("outcome_count")),
                _kpi("Cross-LOT Outcomes", outcomes_data.get("cross_lot_outcomes")),
                _kpi("Validation", outcomes_data.get("validation_status")),
            ],
            tables=[
                _table(
                    "Top Failing Pattern Outcomes",
                    outcomes_data.get("outcomes"),
                    (
                        "pattern_id",
                        "scan_chain_id",
                        "latest_result",
                        "pass_count",
                        "fail_count",
                        "execution_count",
                        "lot_count",
                        "cross_lot",
                        "data_quality_flags",
                    ),
                )
            ],
            charts=_charts_from_data(outcomes_data),
            messages=_section_messages(sections, "pattern_outcomes"),
        ),
    ]

    if has_anomaly_by_lot:
        export_sections.append(
            _section(
                "anomaly_by_lot",
                "Layer 3 — Anomaly by LOT (PA-ML-002)",
                _section_status(sections, "anomaly_by_lot"),
                purpose="Advisory unsupervised anomaly scores at pattern × LOT grain.",
                summary="Primary LOT-scoped anomaly view; aggregates ATE logs within each LOT.",
                kpis=[
                    _kpi("Model", anomaly_by_lot_data.get("model_version")),
                    _kpi("Grain", anomaly_by_lot_data.get("grain") or "pattern_x_lot"),
                    _kpi("Scores", anomaly_by_lot_data.get("score_count")),
                    _kpi("Displayed", anomaly_by_lot_data.get("display_count")),
                    _kpi("Anomalies", anomaly_by_lot_data.get("anomaly_count")),
                    _kpi("Advisory", "Yes" if anomaly_by_lot_data.get("advisory") else "No"),
                ],
                tables=[
                    _table(
                        "Top Anomalies by LOT",
                        anomaly_by_lot_data.get("scores"),
                        (
                            "unit_id",
                            "pattern_id",
                            "source_lot",
                            "log_count_in_lot",
                            "anomaly_score",
                            "is_anomaly",
                            "top_contributors",
                        ),
                    )
                ],
                messages=_section_messages(sections, "anomaly_by_lot"),
            )
        )

    if has_anomaly:
        export_sections.append(
            _section(
                "anomaly",
                "Layer 3 — Anomaly by Log (PA-ML-002)",
                _section_status(sections, "anomaly"),
                purpose="Advisory unsupervised anomaly scores at pattern × source_log grain.",
                summary="Log-level drill-down for unusual executions.",
                kpis=[
                    _kpi("Model", anomaly_data.get("model_version")),
                    _kpi("Grain", anomaly_data.get("grain") or "pattern_x_source_log"),
                    _kpi("Scores", anomaly_data.get("score_count")),
                    _kpi("Displayed", anomaly_data.get("display_count")),
                    _kpi("Anomalies", anomaly_data.get("anomaly_count")),
                    _kpi("Advisory", "Yes" if anomaly_data.get("advisory") else "No"),
                ],
                tables=[
                    _table(
                        "Top Anomalies by Log",
                        anomaly_data.get("scores"),
                        (
                            "unit_id",
                            "pattern_id",
                            "source_log",
                            "anomaly_score",
                            "is_anomaly",
                            "top_contributors",
                        ),
                    )
                ],
                messages=_section_messages(sections, "anomaly"),
            )
        )

    if has_failure_risk_by_lot:
        export_sections.append(
            _section(
                "failure_risk_by_lot",
                "Layer 3 — Failure Risk by LOT (PA-ML-001)",
                _section_status(sections, "failure_risk_by_lot"),
                purpose="Advisory failure-risk scores at pattern × LOT grain.",
                summary="Primary LOT-scoped view; aggregates ATE logs within each LOT.",
                kpis=[
                    _kpi("Model", failure_risk_by_lot_data.get("model_version")),
                    _kpi("Grain", failure_risk_by_lot_data.get("grain") or "pattern_x_lot"),
                    _kpi("Predictions", failure_risk_by_lot_data.get("prediction_count")),
                    _kpi("Displayed", failure_risk_by_lot_data.get("display_count")),
                    _kpi("Predicted FAIL", failure_risk_by_lot_data.get("predicted_fail_count")),
                    _kpi("Advisory", "Yes" if failure_risk_by_lot_data.get("advisory") else "No"),
                ],
                tables=[
                    _table(
                        "Top Failure Risk by LOT",
                        failure_risk_by_lot_data.get("predictions"),
                        (
                            "unit_id",
                            "pattern_id",
                            "source_lot",
                            "log_count_in_lot",
                            "score",
                            "label_pred",
                            "top_contributors",
                        ),
                    )
                ],
                messages=_section_messages(sections, "failure_risk_by_lot"),
                findings=[
                    "LOT grain aggregates log executions; L1 PASS/FAIL outcomes remain authoritative.",
                ],
            )
        )

    if has_failure_risk:
        export_sections.append(
            _section(
                "failure_risk",
                "Layer 3 — Failure Risk by Log (PA-ML-001)",
                _section_status(sections, "failure_risk"),
                purpose="Advisory failure-risk scores at pattern × source_log grain.",
                summary="Log-level drill-down; does not mutate L1 Analysis Session artifacts.",
                kpis=[
                    _kpi("Model", failure_risk_data.get("model_version")),
                    _kpi("Grain", failure_risk_data.get("grain") or "pattern_x_source_log"),
                    _kpi("Predictions", failure_risk_data.get("prediction_count")),
                    _kpi("Displayed", failure_risk_data.get("display_count")),
                    _kpi("Predicted FAIL", failure_risk_data.get("predicted_fail_count")),
                    _kpi("Advisory", "Yes" if failure_risk_data.get("advisory") else "No"),
                ],
                tables=[
                    _table(
                        "Top Failure Risk by Log",
                        failure_risk_data.get("predictions"),
                        (
                            "unit_id",
                            "pattern_id",
                            "source_log",
                            "score",
                            "label_pred",
                            "top_contributors",
                        ),
                    )
                ],
                messages=_section_messages(sections, "failure_risk"),
                findings=[
                    "Scores are advisory; L1 PASS/FAIL outcomes remain authoritative.",
                ],
            )
        )

    if has_root_cause_by_lot:
        export_sections.append(
            _section(
                "root_cause_by_lot",
                "Layer 3 — Root Cause by LOT (PA-ML-003)",
                _section_status(sections, "root_cause_by_lot"),
                purpose="Advisory investigation priority at pattern × LOT grain.",
                summary="Ranked candidates for engineering investigation; not a causal diagnosis.",
                kpis=[
                    _kpi("Model", root_cause_by_lot_data.get("model_version")),
                    _kpi("Grain", root_cause_by_lot_data.get("grain") or "pattern_x_lot"),
                    _kpi("Rankings", root_cause_by_lot_data.get("ranking_count")),
                    _kpi("Displayed", root_cause_by_lot_data.get("display_count")),
                    _kpi("Observed FAIL", root_cause_by_lot_data.get("fail_count")),
                    _kpi("Advisory", "Yes" if root_cause_by_lot_data.get("advisory") else "No"),
                ],
                tables=[
                    _table(
                        "Top Investigation Priorities by LOT",
                        root_cause_by_lot_data.get("rankings"),
                        (
                            "investigation_rank",
                            "investigation_score",
                            "unit_id",
                            "pattern_id",
                            "scan_chain_id",
                            "source_lot",
                            "log_count_in_lot",
                            "actual_result",
                            "hypothesis_tags",
                            "top_contributors",
                        ),
                    )
                ],
                messages=_section_messages(sections, "root_cause_by_lot"),
            )
        )

    if has_root_cause:
        export_sections.append(
            _section(
                "root_cause",
                "Layer 3 — Root Cause by Log (PA-ML-003)",
                _section_status(sections, "root_cause"),
                purpose="Advisory investigation priority at pattern × source_log grain.",
                summary="Log-level drill-down for ranked investigation candidates.",
                kpis=[
                    _kpi("Model", root_cause_data.get("model_version")),
                    _kpi("Grain", root_cause_data.get("grain") or "pattern_x_source_log"),
                    _kpi("Rankings", root_cause_data.get("ranking_count")),
                    _kpi("Displayed", root_cause_data.get("display_count")),
                    _kpi("Observed FAIL", root_cause_data.get("fail_count")),
                    _kpi("Advisory", "Yes" if root_cause_data.get("advisory") else "No"),
                ],
                tables=[
                    _table(
                        "Top Investigation Priorities by Log",
                        root_cause_data.get("rankings"),
                        (
                            "investigation_rank",
                            "investigation_score",
                            "unit_id",
                            "pattern_id",
                            "scan_chain_id",
                            "source_log",
                            "actual_result",
                            "hypothesis_tags",
                            "top_contributors",
                        ),
                    )
                ],
                messages=_section_messages(sections, "root_cause"),
            )
        )

    if has_recommendations_by_lot:
        export_sections.append(
            _section(
                "recommendations_by_lot",
                "Layer 3 — Recommendations by LOT (PA-ML-004)",
                _section_status(sections, "recommendations_by_lot"),
                purpose="Advisory pattern prioritization at pattern × LOT grain.",
                summary="Fuses failure risk, anomaly, and root-cause signals into ranked actions.",
                kpis=[
                    _kpi("Model", recommendations_by_lot_data.get("model_version")),
                    _kpi("Grain", recommendations_by_lot_data.get("grain") or "pattern_x_lot"),
                    _kpi("Recommendations", recommendations_by_lot_data.get("recommendation_count")),
                    _kpi("Displayed", recommendations_by_lot_data.get("display_count")),
                    _kpi("High Priority", recommendations_by_lot_data.get("high_priority_count")),
                    _kpi("Advisory", "Yes" if recommendations_by_lot_data.get("advisory") else "No"),
                ],
                tables=[
                    _table(
                        "Top Recommendations by LOT",
                        recommendations_by_lot_data.get("recommendations"),
                        (
                            "recommendation_rank",
                            "priority_score",
                            "priority_tier",
                            "recommended_action",
                            "unit_id",
                            "pattern_id",
                            "scan_chain_id",
                            "source_lot",
                            "log_count_in_lot",
                            "actual_result",
                            "rationale",
                            "failure_score",
                            "anomaly_score",
                            "investigation_score",
                        ),
                    )
                ],
                messages=_section_messages(sections, "recommendations_by_lot"),
            )
        )

    if has_recommendations:
        export_sections.append(
            _section(
                "recommendations",
                "Layer 3 — Recommendations by Log (PA-ML-004)",
                _section_status(sections, "recommendations"),
                purpose="Advisory pattern prioritization at pattern × source_log grain.",
                summary="Log-level drill-down for fused ML recommendations.",
                kpis=[
                    _kpi("Model", recommendations_data.get("model_version")),
                    _kpi("Grain", recommendations_data.get("grain") or "pattern_x_source_log"),
                    _kpi("Recommendations", recommendations_data.get("recommendation_count")),
                    _kpi("Displayed", recommendations_data.get("display_count")),
                    _kpi("High Priority", recommendations_data.get("high_priority_count")),
                    _kpi("Advisory", "Yes" if recommendations_data.get("advisory") else "No"),
                ],
                tables=[
                    _table(
                        "Top Recommendations by Log",
                        recommendations_data.get("recommendations"),
                        (
                            "recommendation_rank",
                            "priority_score",
                            "priority_tier",
                            "recommended_action",
                            "unit_id",
                            "pattern_id",
                            "scan_chain_id",
                            "source_log",
                            "actual_result",
                            "rationale",
                            "failure_score",
                            "anomaly_score",
                            "investigation_score",
                        ),
                    )
                ],
                messages=_section_messages(sections, "recommendations"),
            )
        )

    export_sections.extend(
        [
        _section(
            "validation",
            "Validation Summary",
            str(validation.get("status") or "Missing"),
            purpose="Deterministic phase completion checklist for the Analysis Session.",
            summary="Overall validation status derived from artifact presence and warnings.",
            kpis=[
                _kpi("Validation Status", validation.get("status")),
                _kpi("Warnings", len(warnings)),
                _kpi("Completion %", completion_pct),
                _kpi("Model Hash", hashes.get("model_hash"), kind="hash"),
            ],
            tables=[
                _table(
                    "Requirement Completion",
                    [
                        {"phase": key, "status": value}
                        for key, value in sorted(
                            (
                                (validation.get("phase_completion") or validation_data.get("phase_completion") or {})
                                if isinstance(
                                    validation.get("phase_completion")
                                    or validation_data.get("phase_completion"),
                                    Mapping,
                                )
                                else {}
                            ).items()
                        )
                    ],
                    ("phase", "status"),
                )
            ],
            messages=warnings,
            findings=[
                "Complete = artifact present and readable; Missing/Partial require engineering follow-up.",
            ],
        ),
        _section(
            "appendix",
            "Audit Appendix",
            _section_status(sections, "appendix"),
            purpose="Technical inventory: hashes, versions, and provenance.",
            summary="All cryptographic and generation metadata for audit.",
            tables=[
                _table(
                    "Artifact Provenance",
                    provenance_records,
                    (
                        "logical_name",
                        "artifact_filename",
                        "status",
                        "generated_by",
                        "version",
                        "sha256",
                        "generation_timestamp",
                    ),
                )
            ],
        ),
        ]
    )

    section_order = [
        section_id
        for section_id in EXPORT_SECTION_ORDER
        if (section_id != "anomaly_by_lot" or has_anomaly_by_lot)
        and (section_id != "anomaly" or has_anomaly)
        and (section_id != "root_cause_by_lot" or has_root_cause_by_lot)
        and (section_id != "root_cause" or has_root_cause)
        and (section_id != "recommendations_by_lot" or has_recommendations_by_lot)
        and (section_id != "recommendations" or has_recommendations)
        and (section_id != "failure_risk_by_lot" or has_failure_risk_by_lot)
        and (section_id != "failure_risk" or has_failure_risk)
    ]

    return {
        "generated_by": "PA-FR-010.AS.3",
        "report_title": "Semiconductor Pattern Analysis Engineering Report",
        "report_subtitle": "Deterministic Engineering Analysis · Analysis Session Report",
        "engineering_status": engineering_status,
        "source_artifact": REPORT_MODEL_FILENAME,
        "section_order": section_order,
        "sections": export_sections,
        "metadata": _snapshot(dict(metadata)),
        "validation": _snapshot(dict(validation)),
        "provenance": {
            **_snapshot(dict(provenance)),
            "model_hash": hashes.get("model_hash"),
            "generation_timestamp": metadata.get("generated_timestamp"),
        },
        "hashes": _snapshot(dict(hashes)),
        "summary": _snapshot(dict(summary)),
    }


def _load_analysis_session_report_model(output_dir: str) -> Dict[str, Any]:
    path = os.path.join(output_dir, REPORT_MODEL_FILENAME)
    if not os.path.exists(path):
        raise AnalysisSessionReportModelError(f"Missing {REPORT_MODEL_FILENAME}.")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise AnalysisSessionReportModelError(
            f"Unable to read {REPORT_MODEL_FILENAME}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise AnalysisSessionReportModelError(
            f"{REPORT_MODEL_FILENAME} must contain an object."
        )
    return payload


def generate_analysis_session_report(
    report_model: Mapping[str, Any],
    requested_format: str,
) -> GeneratedAnalysisSessionReport:
    """Generate bytes directly from an already-loaded Analysis Session model."""
    normalized_format = str(requested_format or "").strip().lower()
    export_config = EXPORTERS.get(normalized_format)
    if export_config is None:
        raise AnalysisSessionReportGenerationError(
            "Unsupported report format. Expected html, pdf, or excel."
        )
    projection = _build_export_projection(report_model)
    exporter, media_type, filename = export_config
    content = exporter(projection)
    hashes = report_model.get("hashes")
    hashes = hashes if isinstance(hashes, Mapping) else {}
    return GeneratedAnalysisSessionReport(
        content=content,
        media_type=media_type,
        filename=filename,
        model_hash=str(hashes.get("model_hash") or ""),
    )


def generate_analysis_session_report_from_output(
    output_dir: str,
    requested_format: str,
) -> GeneratedAnalysisSessionReport:
    """Load only the session report model and generate the requested format."""
    return generate_analysis_session_report(
        _load_analysis_session_report_model(output_dir),
        requested_format,
    )
