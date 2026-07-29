"""
PA-FR-010.AS.2 — Analysis Session report preview builder.

The sole input is PA-Analysis-Session_report_model.json. This presentation-only
module writes no files, invokes no analysis, and is independent from the
Single Log preview implementation.
"""
from __future__ import annotations

import copy
import json
import os
from typing import Any, Dict, List, Mapping, Optional, Sequence


REPORT_MODEL_FILENAME = "PA-Analysis-Session_report_model.json"
PREVIEW_GENERATED_BY = "PA-FR-010.AS.2"
PREVIEW_VERSION = "1.0"
DEFAULT_TABLE_LIMIT = 10
APPENDIX_TABLE_LIMIT = 100


class AnalysisSessionReportPreviewError(RuntimeError):
    """Raised when the Analysis Session report model cannot be loaded."""


def _snapshot(value: Any) -> Any:
    return copy.deepcopy(value)


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
        display = _number_display(value)
    return {"label": label, "value": _snapshot(value), "display": display}


def _table(
    title: str,
    rows: Sequence[Mapping[str, Any]] | None,
    columns: Sequence[str],
    *,
    limit: Optional[int] = DEFAULT_TABLE_LIMIT,
) -> Dict[str, Any]:
    source_rows = [row for row in (rows or []) if isinstance(row, Mapping)]
    selected = source_rows if limit is None else source_rows[:limit]
    visible = [
        {column: _snapshot(row.get(column)) for column in columns}
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


def _section_tables(
    section_id: str,
    data: Any,
    provenance: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    payload = data if isinstance(data, Mapping) else {}
    if section_id == "toggle_coverage":
        summary = payload.get("summary")
        executions = payload.get("executions")
        summary_payload = summary if isinstance(summary, Mapping) else {}
        executions_payload = executions if isinstance(executions, Mapping) else {}
        return [
            _table(
                "Pattern / Chain Coverage",
                _mapping_rows(
                    summary_payload.get("by_pattern_chain"),
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
                "Executions",
                executions_payload.get("executions"),
                (
                    "pattern_id",
                    "scan_chain_id",
                    "source_log",
                    "run_id",
                    "toggle_count",
                    "toggle_coverage_pct",
                    "toggle_density_pct",
                    "latest_result",
                ),
            ),
        ]
    if section_id == "scan_vectors":
        return [
            _table(
                "Scan Vectors",
                payload.get("vectors"),
                (
                    "pattern_id",
                    "source_log",
                    "source_log_relpath",
                    "run_id",
                ),
            )
        ]
    if section_id == "embeddings":
        return [
            _table(
                "Embeddings",
                payload.get("embeddings"),
                (
                    "pattern_id",
                    "source_log",
                    "source_log_relpath",
                    "run_id",
                    "feature_version",
                    "created_timestamp",
                ),
            )
        ]
    if section_id == "clustering":
        return [
            _table(
                "Clusters",
                payload.get("clusters"),
                (
                    "cluster_id",
                    "representative_pattern",
                    "pattern_count",
                    "execution_count",
                    "average_similarity",
                ),
            ),
            _table(
                "Unit Assignments",
                payload.get("unit_assignments"),
                (
                    "unit_id",
                    "pattern_id",
                    "source_lot",
                    "cluster_id",
                    "similarity_to_centroid",
                ),
            ),
        ]
    if section_id == "redundancy":
        return [
            _table(
                "Redundancy Candidates",
                payload.get("candidates"),
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
        ]
    if section_id == "similarity":
        return [
            _table(
                "Top Similarity Pairs",
                payload.get("similarity_pairs"),
                (
                    "unit_a",
                    "unit_b",
                    "pattern_a",
                    "pattern_b",
                    "rank",
                    "cosine_similarity",
                ),
            )
        ]
    if section_id == "pattern_outcomes":
        return [
            _table(
                "Pattern Outcomes",
                payload.get("outcomes"),
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
        ]
    if section_id == "anomaly_by_lot":
        return [
            _table(
                "Anomaly Scores by LOT (advisory)",
                payload.get("scores"),
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
        ]
    if section_id == "anomaly":
        return [
            _table(
                "Anomaly Scores by Log (advisory)",
                payload.get("scores"),
                (
                    "unit_id",
                    "pattern_id",
                    "source_log",
                    "anomaly_score",
                    "is_anomaly",
                    "top_contributors",
                ),
            )
        ]
    if section_id == "failure_risk_by_lot":
        return [
            _table(
                "Failure Risk by LOT (advisory)",
                payload.get("predictions"),
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
        ]
    if section_id == "failure_risk":
        return [
            _table(
                "Failure Risk by Log (advisory)",
                payload.get("predictions"),
                (
                    "unit_id",
                    "pattern_id",
                    "source_log",
                    "score",
                    "label_pred",
                    "top_contributors",
                ),
            )
        ]
    if section_id == "root_cause_by_lot":
        return [
            _table(
                "Root Cause Rankings by LOT (advisory)",
                payload.get("rankings"),
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
        ]
    if section_id == "root_cause":
        return [
            _table(
                "Root Cause Rankings by Log (advisory)",
                payload.get("rankings"),
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
        ]
    if section_id == "recommendations_by_lot":
        return [
            _table(
                "Pattern Recommendations by LOT (advisory)",
                payload.get("recommendations"),
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
        ]
    if section_id == "recommendations":
        return [
            _table(
                "Pattern Recommendations by Log (advisory)",
                payload.get("recommendations"),
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
        ]
    if section_id == "appendix":
        records = provenance.get("artifacts")
        return [
            _table(
                "Artifact Provenance",
                records if isinstance(records, list) else [],
                (
                    "logical_name",
                    "artifact_filename",
                    "status",
                    "generated_by",
                    "version",
                    "sha256",
                    "generation_timestamp",
                ),
                limit=APPENDIX_TABLE_LIMIT,
            )
        ]
    return []


def _section_kpis(
    section_id: str,
    data: Any,
    metadata: Mapping[str, Any],
    hashes: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    payload = data if isinstance(data, Mapping) else {}
    if section_id == "session_overview":
        return [
            _kpi("STIL File", metadata.get("stil_filename")),
            _kpi("Session Hash", metadata.get("session_hash"), kind="hash"),
            _kpi(
                "Generated",
                metadata.get("generated_timestamp"),
                kind="timestamp",
            ),
            _kpi("LOTs", metadata.get("lot_count")),
            _kpi("ATE Logs", metadata.get("ate_log_count")),
            _kpi("Executions", metadata.get("execution_record_count")),
        ]
    if section_id == "scan_vectors":
        return [_kpi("Vectors", payload.get("vector_count"))]
    if section_id == "embeddings":
        return [
            _kpi("Embeddings", payload.get("patterns_embedded")),
            _kpi("Skipped", payload.get("patterns_skipped")),
            _kpi("Dimension", payload.get("embedding_dimension")),
            _kpi("Embedding Version", payload.get("embedding_version")),
            _kpi("Metric", payload.get("similarity_metric")),
        ]
    if section_id == "clustering":
        return [
            _kpi("Clusters", payload.get("total_clusters")),
            _kpi("Units", payload.get("units_total")),
            _kpi("Singletons", payload.get("singleton_clusters")),
            _kpi("Largest Cluster", payload.get("largest_cluster")),
            _kpi("Average Size", payload.get("average_cluster_size")),
        ]
    if section_id == "redundancy":
        return [
            _kpi("Candidates", payload.get("total_candidates")),
            _kpi("Units Represented", payload.get("units_represented")),
            _kpi("Clusters Evaluated", payload.get("clusters_evaluated")),
            _kpi("Threshold", payload.get("similarity_threshold")),
        ]
    if section_id == "similarity":
        summary = payload.get("summary")
        summary = summary if isinstance(summary, Mapping) else {}
        return [
            _kpi("Metric", payload.get("similarity_metric")),
            _kpi("Embedding Version", payload.get("embedding_version")),
            _kpi("Units", summary.get("total_units")),
            _kpi("Pairs", summary.get("total_similarity_pairs")),
            _kpi("Average Similarity", summary.get("average_similarity")),
        ]
    if section_id == "pattern_outcomes":
        return [
            _kpi("PASS", payload.get("pass_count")),
            _kpi("FAIL", payload.get("fail_count")),
            _kpi("Unknown", payload.get("unknown_count")),
            _kpi("Outcomes", payload.get("outcome_count")),
            _kpi("Validation", payload.get("validation_status")),
        ]
    if section_id == "anomaly_by_lot":
        return [
            _kpi("Model", payload.get("model_version")),
            _kpi("Grain", payload.get("grain") or "pattern_x_lot"),
            _kpi("Scores", payload.get("score_count")),
            _kpi("Displayed", payload.get("display_count")),
            _kpi("Anomalies", payload.get("anomaly_count")),
            _kpi("Advisory", "Yes" if payload.get("advisory") else "No"),
        ]
    if section_id == "anomaly":
        return [
            _kpi("Model", payload.get("model_version")),
            _kpi("Grain", payload.get("grain") or "pattern_x_source_log"),
            _kpi("Scores", payload.get("score_count")),
            _kpi("Displayed", payload.get("display_count")),
            _kpi("Anomalies", payload.get("anomaly_count")),
            _kpi("Advisory", "Yes" if payload.get("advisory") else "No"),
        ]
    if section_id == "failure_risk_by_lot":
        return [
            _kpi("Model", payload.get("model_version")),
            _kpi("Grain", payload.get("grain") or "pattern_x_lot"),
            _kpi("Predictions", payload.get("prediction_count")),
            _kpi("Displayed", payload.get("display_count")),
            _kpi("Predicted FAIL", payload.get("predicted_fail_count")),
            _kpi("Advisory", "Yes" if payload.get("advisory") else "No"),
        ]
    if section_id == "failure_risk":
        return [
            _kpi("Model", payload.get("model_version")),
            _kpi("Grain", payload.get("grain") or "pattern_x_source_log"),
            _kpi("Predictions", payload.get("prediction_count")),
            _kpi("Displayed", payload.get("display_count")),
            _kpi("Predicted FAIL", payload.get("predicted_fail_count")),
            _kpi("Advisory", "Yes" if payload.get("advisory") else "No"),
        ]
    if section_id == "root_cause_by_lot":
        return [
            _kpi("Model", payload.get("model_version")),
            _kpi("Grain", payload.get("grain") or "pattern_x_lot"),
            _kpi("Rankings", payload.get("ranking_count")),
            _kpi("Displayed", payload.get("display_count")),
            _kpi("Observed FAIL", payload.get("fail_count")),
            _kpi("Advisory", "Yes" if payload.get("advisory") else "No"),
        ]
    if section_id == "root_cause":
        return [
            _kpi("Model", payload.get("model_version")),
            _kpi("Grain", payload.get("grain") or "pattern_x_source_log"),
            _kpi("Rankings", payload.get("ranking_count")),
            _kpi("Displayed", payload.get("display_count")),
            _kpi("Observed FAIL", payload.get("fail_count")),
            _kpi("Advisory", "Yes" if payload.get("advisory") else "No"),
        ]
    if section_id == "recommendations_by_lot":
        return [
            _kpi("Model", payload.get("model_version")),
            _kpi("Grain", payload.get("grain") or "pattern_x_lot"),
            _kpi("Recommendations", payload.get("recommendation_count")),
            _kpi("Displayed", payload.get("display_count")),
            _kpi("High Priority", payload.get("high_priority_count")),
            _kpi("Advisory", "Yes" if payload.get("advisory") else "No"),
        ]
    if section_id == "recommendations":
        return [
            _kpi("Model", payload.get("model_version")),
            _kpi("Grain", payload.get("grain") or "pattern_x_source_log"),
            _kpi("Recommendations", payload.get("recommendation_count")),
            _kpi("Displayed", payload.get("display_count")),
            _kpi("High Priority", payload.get("high_priority_count")),
            _kpi("Advisory", "Yes" if payload.get("advisory") else "No"),
        ]
    if section_id == "validation":
        warnings = payload.get("warnings")
        return [
            _kpi("Validation Status", payload.get("status")),
            _kpi("Warnings", len(warnings) if isinstance(warnings, list) else 0),
            _kpi("Model Hash", hashes.get("model_hash"), kind="hash"),
        ]
    return []


def build_analysis_session_report_preview(
    report_model: Mapping[str, Any],
) -> Dict[str, Any]:
    """Build a bounded, deterministic preview without mutating the model."""
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
    appendix = report_model.get("appendix")
    appendix = appendix if isinstance(appendix, Mapping) else {}
    model_sections = report_model.get("sections")
    model_sections = model_sections if isinstance(model_sections, list) else []

    sections: List[Dict[str, Any]] = []
    for source_section in model_sections:
        if not isinstance(source_section, Mapping):
            continue
        section_id = str(source_section.get("id") or "")
        section_data = source_section.get("data")
        messages = source_section.get("warnings")
        sections.append(
            {
                "id": section_id,
                "title": str(source_section.get("title") or section_id),
                "status": str(source_section.get("status") or "Missing"),
                "kpis": _section_kpis(
                    section_id,
                    section_data,
                    metadata,
                    hashes,
                ),
                "tables": _section_tables(section_id, section_data, provenance),
                "charts": [],
                "messages": (
                    _snapshot(messages) if isinstance(messages, list) else []
                ),
            }
        )

    warnings = report_model.get("warnings")
    warnings = _snapshot(warnings) if isinstance(warnings, list) else []
    model_hash = hashes.get("model_hash")
    generated_timestamp = metadata.get("generated_timestamp")
    provenance_preview = _snapshot(dict(provenance))
    provenance_preview.update(
        {
            "model_hash": model_hash,
            "model_hash_display": _hash_display(model_hash),
            "generation_timestamp": generated_timestamp,
            "generation_timestamp_display": _timestamp_display(
                generated_timestamp
            ),
        }
    )

    return {
        "generated_by": PREVIEW_GENERATED_BY,
        "preview_version": PREVIEW_VERSION,
        "source_artifact": REPORT_MODEL_FILENAME,
        "metadata": _snapshot(dict(metadata)),
        "section_order": [section["id"] for section in sections],
        "section_summaries": [
            {
                "id": section["id"],
                "title": section["title"],
                "status": section["status"],
            }
            for section in sections
        ],
        "sections": sections,
        "validation": _snapshot(dict(validation)),
        "warnings": warnings,
        "provenance": provenance_preview,
        "hashes": _snapshot(dict(hashes)),
        "summary": _snapshot(dict(summary)),
        "appendix": _snapshot(dict(appendix)),
    }


def load_analysis_session_report_model(output_dir: str) -> Dict[str, Any]:
    """Read only PA-Analysis-Session_report_model.json."""
    path = os.path.join(output_dir, REPORT_MODEL_FILENAME)
    if not os.path.exists(path):
        raise AnalysisSessionReportPreviewError(
            f"Missing {REPORT_MODEL_FILENAME}."
        )
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise AnalysisSessionReportPreviewError(
            f"Unable to read {REPORT_MODEL_FILENAME}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise AnalysisSessionReportPreviewError(
            f"{REPORT_MODEL_FILENAME} must contain an object."
        )
    return payload


def build_analysis_session_report_preview_from_output(
    output_dir: str,
) -> Dict[str, Any]:
    """Load the existing session model and return a preview object only."""
    return build_analysis_session_report_preview(
        load_analysis_session_report_model(output_dir)
    )


def preview_analysis_session_report_from_output(
    output_dir: str,
) -> Dict[str, Any]:
    """Endpoint adapter retaining the isolated public builder contract."""
    return build_analysis_session_report_preview_from_output(output_dir)
