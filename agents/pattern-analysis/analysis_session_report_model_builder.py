"""
PA-FR-010.AS.1 — deterministic Analysis Session report model builder.

Presentation-oriented model: KPIs, chart series, top-N tables, and artifact
references. Does not duplicate full Analysis Session datasets.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from analysis_session import AnalysisSession, SESSION_GENERATED_BY


REPORT_MODEL_FILENAME = "PA-Analysis-Session_report_model.json"
REPORT_GENERATED_BY = "PA-FR-010.AS.1"
REPORT_VERSION = "2.0"
REPORT_GENERATOR_VERSION = "2.0"
PRESENTATION_SCHEMA_VERSION = "2.0"
TOP_N = 50

SESSION_ARTIFACTS: Tuple[Tuple[str, str], ...] = (
    ("manifest", "PA-Analysis-Session_manifest.json"),
    ("summary", "PA-Analysis-Session_summary.json"),
    ("executions", "PA-Analysis-Session_executions.json"),
    ("scan_vectors", "PA-Analysis-Session_scan_vectors.json"),
    ("embeddings", "PA-Analysis-Session_embeddings.json"),
    ("similarity", "PA-Analysis-Session_similarity.json"),
    ("clustering", "PA-Analysis-Session_clustering.json"),
    ("redundancy", "PA-Analysis-Session_redundancy.json"),
    ("pattern_outcomes", "PA-Analysis-Session_correlation.json"),
)

# Optional Layer-3 advisory artifacts — never counted toward L1 Completeness.
OPTIONAL_SESSION_ARTIFACTS: Tuple[Tuple[str, str], ...] = (
    ("pattern_recommendations_by_lot", "PA-Analysis-Session_pattern_recommendations_by_lot.json"),
    ("pattern_recommendations", "PA-Analysis-Session_pattern_recommendations.json"),
    ("root_cause_rankings_by_lot", "PA-Analysis-Session_root_cause_rankings_by_lot.json"),
    ("root_cause_rankings", "PA-Analysis-Session_root_cause_rankings.json"),
    ("anomaly_scores_by_lot", "PA-Analysis-Session_anomaly_scores_by_lot.json"),
    ("anomaly_scores", "PA-Analysis-Session_anomaly_scores.json"),
    ("failure_predictions_by_lot", "PA-Analysis-Session_failure_predictions_by_lot.json"),
    ("failure_predictions", "PA-Analysis-Session_failure_predictions.json"),
)

SECTION_ORDER: Tuple[Tuple[str, str], ...] = (
    ("session_overview", "Session Overview"),
    ("toggle_coverage", "Toggle Coverage"),
    ("scan_vectors", "Scan Vectors"),
    ("embeddings", "Embeddings"),
    ("clustering", "Clustering"),
    ("redundancy", "Redundancy"),
    ("similarity", "Similarity"),
    ("pattern_outcomes", "Pattern Outcomes"),
    ("validation", "Validation"),
    ("appendix", "Appendix"),
)

_VERSION_FIELDS = (
    "version",
    "artifact_version",
    "embedding_version",
    "cluster_version",
    "correlation_version",
)

_VECTOR_DROP_KEYS = frozenset(
    {
        "embedding",
        "concatenated_sequence",
        "chains",
        "centroids",
    }
)


@dataclass(frozen=True)
class AnalysisSessionReportSources:
    artifacts: Mapping[str, Optional[Mapping[str, Any]]] = field(default_factory=dict)
    provenance: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    optional_artifacts: Mapping[str, Optional[Mapping[str, Any]]] = field(
        default_factory=dict
    )
    optional_provenance: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    validation_warnings: Tuple[str, ...] = ()


def _snapshot(value: Any) -> Any:
    return copy.deepcopy(value)


def _file_sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _model_hash(model: Mapping[str, Any]) -> str:
    canonical = _snapshot(dict(model))
    hashes = canonical.get("hashes")
    if isinstance(hashes, dict):
        hashes.pop("model_hash", None)
    generation = canonical.get("generation_metadata")
    if isinstance(generation, dict):
        generation.pop("model_hash", None)
    return _canonical_sha256(canonical)


def _source_timestamp(payload: Mapping[str, Any]) -> Optional[Any]:
    for field_name in ("generated_timestamp", "created_timestamp", "build_timestamp"):
        if payload.get(field_name) is not None:
            return payload.get(field_name)
    return None


def _source_version(payload: Mapping[str, Any]) -> Optional[Any]:
    for field_name in _VERSION_FIELDS:
        if payload.get(field_name) is not None:
            return payload.get(field_name)
    return None


def _read_artifact(
    output_dir: str,
    logical_name: str,
    filename: str,
    warnings: Optional[List[str]] = None,
    *,
    required: bool = True,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    path = os.path.join(output_dir, filename)
    provenance: Dict[str, Any] = {
        "logical_name": logical_name,
        "artifact_filename": filename,
        "status": "Missing",
        "sha256": None,
        "generation_timestamp": None,
        "generated_by": None,
        "version": None,
    }
    if not os.path.exists(path):
        if required and warnings is not None:
            warnings.append(f"Missing artifact: {filename}")
        return None, provenance

    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        if required and warnings is not None:
            warnings.append(f"Unreadable artifact {filename}: {exc}")
        return None, provenance

    if not isinstance(payload, dict):
        if required and warnings is not None:
            warnings.append(f"Invalid artifact object: {filename}")
        return None, provenance

    try:
        artifact_hash = _file_sha256(path)
    except OSError as exc:
        if required and warnings is not None:
            warnings.append(f"Unreadable artifact {filename}: {exc}")
        return None, provenance

    provenance.update(
        {
            "status": "Complete",
            "sha256": artifact_hash,
            "generation_timestamp": _source_timestamp(payload),
            "generated_by": payload.get("generated_by"),
            "version": _source_version(payload),
        }
    )
    return payload, provenance


def load_analysis_session_report_sources(
    output_dir: str,
) -> AnalysisSessionReportSources:
    artifacts: Dict[str, Optional[Mapping[str, Any]]] = {}
    provenance: Dict[str, Mapping[str, Any]] = {}
    optional_artifacts: Dict[str, Optional[Mapping[str, Any]]] = {}
    optional_provenance: Dict[str, Mapping[str, Any]] = {}
    warnings: List[str] = []
    for logical_name, filename in SESSION_ARTIFACTS:
        payload, artifact_provenance = _read_artifact(
            output_dir,
            logical_name,
            filename,
            warnings,
            required=True,
        )
        artifacts[logical_name] = payload
        provenance[logical_name] = artifact_provenance
    for logical_name, filename in OPTIONAL_SESSION_ARTIFACTS:
        payload, artifact_provenance = _read_artifact(
            output_dir,
            logical_name,
            filename,
            warnings=None,
            required=False,
        )
        optional_artifacts[logical_name] = payload
        optional_provenance[logical_name] = artifact_provenance
    return AnalysisSessionReportSources(
        artifacts=artifacts,
        provenance=provenance,
        optional_artifacts=optional_artifacts,
        optional_provenance=optional_provenance,
        validation_warnings=tuple(sorted(set(warnings))),
    )


def session_executions_artifact_payload(
    executions: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    """On-disk / report-source envelope for session executions (shared write+report)."""
    return {
        "generated_by": SESSION_GENERATED_BY,
        "executions": executions,
    }


def _provenance_from_payload(
    logical_name: str,
    filename: str,
    payload: Optional[Mapping[str, Any]],
    sha256: Optional[str],
    *,
    required: bool = True,
    warnings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    provenance: Dict[str, Any] = {
        "logical_name": logical_name,
        "artifact_filename": filename,
        "status": "Missing",
        "sha256": None,
        "generation_timestamp": None,
        "generated_by": None,
        "version": None,
    }
    if payload is None:
        if required and warnings is not None:
            warnings.append(f"Missing artifact: {filename}")
        return provenance
    if not isinstance(payload, Mapping):
        if required and warnings is not None:
            warnings.append(f"Invalid artifact object: {filename}")
        return provenance
    provenance.update(
        {
            "status": "Complete",
            "sha256": sha256,
            "generation_timestamp": _source_timestamp(payload),
            "generated_by": payload.get("generated_by"),
            "version": _source_version(payload),
        }
    )
    return provenance


def build_analysis_session_report_sources_from_session(
    session: AnalysisSession,
    *,
    artifact_hashes: Optional[Mapping[str, str]] = None,
    output_dir: Optional[str] = None,
) -> AnalysisSessionReportSources:
    """
    Build report sources from an in-memory AnalysisSession (PA-PERF-002).

    Core artifacts are referenced from session memory — no json.load of L1 files.
    Provenance SHA-256 comes from write-phase hashes (on-disk byte identity).
    Optional ML sidecars are still loaded from disk when output_dir is set.
    """
    hashes = dict(artifact_hashes or {})
    warnings: List[str] = []

    executions_payload = session_executions_artifact_payload(session.executions)
    payload_by_logical: Dict[str, Optional[Mapping[str, Any]]] = {
        "manifest": session.manifest,
        "summary": session.summary,
        "executions": executions_payload,
        "scan_vectors": session.scan_vectors,
        "embeddings": session.embeddings,
        "similarity": session.similarity,
        "clustering": session.clustering,
        "redundancy": session.redundancy,
        "pattern_outcomes": session.correlation,
    }

    artifacts: Dict[str, Optional[Mapping[str, Any]]] = {}
    provenance: Dict[str, Mapping[str, Any]] = {}
    for logical_name, filename in SESSION_ARTIFACTS:
        payload = payload_by_logical.get(logical_name)
        artifacts[logical_name] = payload
        provenance[logical_name] = _provenance_from_payload(
            logical_name,
            filename,
            payload,
            hashes.get(filename),
            required=True,
            warnings=warnings,
        )

    optional_artifacts: Dict[str, Optional[Mapping[str, Any]]] = {}
    optional_provenance: Dict[str, Mapping[str, Any]] = {}
    if output_dir:
        for logical_name, filename in OPTIONAL_SESSION_ARTIFACTS:
            payload, artifact_provenance = _read_artifact(
                output_dir,
                logical_name,
                filename,
                warnings=None,
                required=False,
            )
            optional_artifacts[logical_name] = payload
            optional_provenance[logical_name] = artifact_provenance
    else:
        for logical_name, filename in OPTIONAL_SESSION_ARTIFACTS:
            optional_artifacts[logical_name] = None
            optional_provenance[logical_name] = _provenance_from_payload(
                logical_name,
                filename,
                None,
                None,
                required=False,
            )

    return AnalysisSessionReportSources(
        artifacts=artifacts,
        provenance=provenance,
        optional_artifacts=optional_artifacts,
        optional_provenance=optional_provenance,
        validation_warnings=tuple(sorted(set(warnings))),
    )


def build_analysis_session_report_model_from_session(
    session: AnalysisSession,
    *,
    artifact_hashes: Optional[Mapping[str, str]] = None,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    return build_analysis_session_report_model(
        build_analysis_session_report_sources_from_session(
            session,
            artifact_hashes=artifact_hashes,
            output_dir=output_dir,
        )
    )


def _presence_status(*values: Optional[Mapping[str, Any]]) -> str:
    present = sum(value is not None for value in values)
    if present == 0:
        return "Missing"
    if present < len(values):
        return "Partial"
    return "Complete"


def _first_present(
    sources: Sequence[Optional[Mapping[str, Any]]],
    field_name: str,
) -> Optional[Any]:
    for source in sources:
        if source is not None and source.get(field_name) is not None:
            return source.get(field_name)
    return None


def _section(
    section_id: str,
    title: str,
    status: str,
    data: Any,
    warnings: Sequence[str] = (),
) -> Dict[str, Any]:
    return {
        "id": section_id,
        "title": title,
        "status": status,
        "data": _snapshot(data),
        "warnings": sorted(set(str(item) for item in warnings)),
    }


def _source_ref(
    provenance: Mapping[str, Any],
    *,
    row_count: Optional[int] = None,
    display_records: int = TOP_N,
) -> Dict[str, Any]:
    return {
        "artifact_filename": provenance.get("artifact_filename"),
        "sha256": provenance.get("sha256"),
        "status": provenance.get("status"),
        "row_count": row_count,
        "display_records": display_records,
    }


def _strip_row(row: Mapping[str, Any], drop: Sequence[str] = ()) -> Dict[str, Any]:
    banned = set(drop) | _VECTOR_DROP_KEYS
    return {
        key: _snapshot(value)
        for key, value in row.items()
        if key not in banned
    }


def _top_rows(
    rows: Sequence[Any],
    *,
    limit: int = TOP_N,
    sort_key=None,
    drop: Sequence[str] = (),
) -> List[Dict[str, Any]]:
    cleaned = [row for row in rows if isinstance(row, Mapping)]
    if sort_key is not None:
        cleaned = sorted(cleaned, key=sort_key)
    return [_strip_row(row, drop=drop) for row in cleaned[: max(0, int(limit))]]


def _chart_from_buckets(
    title: str,
    buckets: Any,
    *,
    chart_type: str = "percentage_bars",
) -> Optional[Dict[str, Any]]:
    if isinstance(buckets, Mapping):
        data = [
            {"label": str(key), "value": value}
            for key, value in sorted(buckets.items(), key=lambda item: str(item[0]))
        ]
    elif isinstance(buckets, list):
        data = []
        for item in buckets:
            if not isinstance(item, Mapping):
                continue
            label = item.get("label")
            if label is None:
                label = item.get("name") or item.get("bucket") or item.get("cluster_id")
            value = item.get("value")
            if value is None:
                value = item.get("count") or item.get("size") or item.get("execution_count")
            data.append({"label": str(label), "value": value})
    else:
        return None
    if not data:
        return None
    return {"title": title, "type": chart_type, "data": data}


def _top_pattern_chains(summary: Mapping[str, Any], limit: int = TOP_N) -> Dict[str, Any]:
    chains = summary.get("by_pattern_chain")
    if not isinstance(chains, Mapping):
        return {}
    ranked = sorted(
        (
            (str(key), value)
            for key, value in chains.items()
            if isinstance(value, Mapping)
        ),
        key=lambda item: (
            -int(item[1].get("fail_count") or 0),
            -int(item[1].get("execution_count") or 0),
            item[0],
        ),
    )
    return {
        key: _snapshot(dict(value))
        for key, value in ranked[:limit]
    }


def _slim_overview(
    manifest: Optional[Mapping[str, Any]],
    summary: Optional[Mapping[str, Any]],
    provenance: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    slim_summary = None
    if isinstance(summary, Mapping):
        slim_summary = {
            "generated_by": summary.get("generated_by"),
            "execution_record_count": summary.get("execution_record_count"),
            "by_pattern_chain": _top_pattern_chains(summary),
            "by_pattern_chain_total": len(summary.get("by_pattern_chain") or {}),
        }
    return {
        "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
        "manifest": _snapshot(manifest) if isinstance(manifest, Mapping) else None,
        "summary": slim_summary,
        "source": {
            "manifest": _source_ref(provenance.get("manifest") or {}),
            "summary": _source_ref(
                provenance.get("summary") or {},
                row_count=(
                    len(summary.get("by_pattern_chain") or {})
                    if isinstance(summary, Mapping)
                    else None
                ),
            ),
        },
    }


def _slim_toggle(
    summary: Optional[Mapping[str, Any]],
    executions: Optional[Mapping[str, Any]],
    provenance: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    exec_rows = []
    if isinstance(executions, Mapping):
        exec_rows = [
            row
            for row in (executions.get("executions") or [])
            if isinstance(row, Mapping)
        ]
    top_executions = _top_rows(
        exec_rows,
        sort_key=lambda row: (
            -float(row.get("toggle_coverage_pct") or 0.0),
            -float(row.get("toggle_density_pct") or 0.0),
            str(row.get("pattern_id") or ""),
            str(row.get("source_log") or ""),
        ),
    )
    fail_rows = _top_rows(
        [row for row in exec_rows if str(row.get("latest_result") or "").upper() == "FAIL"],
        sort_key=lambda row: (
            -float(row.get("toggle_coverage_pct") or 0.0),
            str(row.get("pattern_id") or ""),
        ),
        limit=min(TOP_N, 20),
    )
    slim_summary = None
    if isinstance(summary, Mapping):
        slim_summary = {
            "generated_by": summary.get("generated_by"),
            "execution_record_count": summary.get("execution_record_count"),
            "by_pattern_chain": _top_pattern_chains(summary),
            "by_pattern_chain_total": len(summary.get("by_pattern_chain") or {}),
        }
    pass_count = sum(
        1 for row in exec_rows if str(row.get("latest_result") or "").upper() == "PASS"
    )
    fail_count = sum(
        1 for row in exec_rows if str(row.get("latest_result") or "").upper() == "FAIL"
    )
    coverages = [
        float(row.get("toggle_coverage_pct"))
        for row in exec_rows
        if row.get("toggle_coverage_pct") is not None
    ]
    densities = [
        float(row.get("toggle_density_pct"))
        for row in exec_rows
        if row.get("toggle_density_pct") is not None
    ]
    return {
        "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
        "summary": slim_summary,
        "executions": {
            "generated_by": (
                executions.get("generated_by") if isinstance(executions, Mapping) else None
            ),
            "total_records": len(exec_rows),
            "executions": top_executions,
        },
        "kpis": {
            "execution_records": len(exec_rows),
            "pass_count": pass_count,
            "fail_count": fail_count,
            "toggle_coverage_pct_avg": (
                round(sum(coverages) / len(coverages), 4) if coverages else None
            ),
            "toggle_coverage_pct_max": (
                round(max(coverages), 4) if coverages else None
            ),
            "toggle_coverage_pct_min": (
                round(min(coverages), 4) if coverages else None
            ),
            "toggle_density_pct_avg": (
                round(sum(densities) / len(densities), 4) if densities else None
            ),
        },
        "charts": [
            chart
            for chart in (
                _chart_from_buckets(
                    "Top Pattern/Chain Failures",
                    [
                        {
                            "label": key,
                            "count": int((value or {}).get("fail_count") or 0),
                        }
                        for key, value in list(
                            (
                                (slim_summary or {}).get("by_pattern_chain") or {}
                            ).items()
                        )[:20]
                    ],
                ),
            )
            if chart is not None
        ],
        "top_failures": fail_rows,
        "source": {
            "summary": _source_ref(provenance.get("summary") or {}),
            "executions": _source_ref(
                provenance.get("executions") or {},
                row_count=len(exec_rows),
            ),
        },
    }


def _slim_scan_vectors(
    scan_vectors: Optional[Mapping[str, Any]],
    provenance: Mapping[str, Any],
) -> Dict[str, Any]:
    if not isinstance(scan_vectors, Mapping):
        return {
            "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
            "source": _source_ref(provenance),
        }
    vectors = [
        row for row in (scan_vectors.get("vectors") or []) if isinstance(row, Mapping)
    ]
    return {
        "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
        "generated_by": scan_vectors.get("generated_by"),
        "vector_count": scan_vectors.get("vector_count", len(vectors)),
        "vectors": _top_rows(
            vectors,
            sort_key=lambda row: (
                str(row.get("pattern_id") or ""),
                str(row.get("source_log_relpath") or row.get("source_log") or ""),
            ),
            drop=("concatenated_sequence", "chains"),
        ),
        "source": _source_ref(provenance, row_count=len(vectors)),
    }


def _slim_embeddings(
    embeddings: Optional[Mapping[str, Any]],
    provenance: Mapping[str, Any],
) -> Dict[str, Any]:
    if not isinstance(embeddings, Mapping):
        return {
            "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
            "source": _source_ref(provenance),
        }
    rows = [
        row for row in (embeddings.get("embeddings") or []) if isinstance(row, Mapping)
    ]
    return {
        "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
        "generated_by": embeddings.get("generated_by"),
        "algorithm": embeddings.get("algorithm"),
        "embedding_strategy": embeddings.get("embedding_strategy"),
        "embedding_version": embeddings.get("embedding_version"),
        "embedding_dimension": embeddings.get("embedding_dimension"),
        "similarity_metric": embeddings.get("similarity_metric"),
        "patterns_embedded": embeddings.get("patterns_embedded", len(rows)),
        "patterns_skipped": embeddings.get("patterns_skipped"),
        "embeddings": _top_rows(
            rows,
            sort_key=lambda row: (
                str(row.get("pattern_id") or ""),
                str(row.get("source_log") or ""),
            ),
            drop=("embedding",),
        ),
        "source": _source_ref(provenance, row_count=len(rows)),
    }


def _slim_clustering(
    clustering: Optional[Mapping[str, Any]],
    provenance: Mapping[str, Any],
) -> Dict[str, Any]:
    if not isinstance(clustering, Mapping):
        return {
            "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
            "source": _source_ref(provenance),
        }
    clusters = [
        row for row in (clustering.get("clusters") or []) if isinstance(row, Mapping)
    ]
    assignments = [
        row
        for row in (clustering.get("unit_assignments") or [])
        if isinstance(row, Mapping)
    ]
    charts_payload = clustering.get("charts")
    charts: List[Dict[str, Any]] = []
    if isinstance(charts_payload, Mapping):
        for key, title in (
            ("size_distribution", "Cluster Size Distribution"),
            ("lot_contribution", "LOT Contribution per Cluster"),
            ("execution_distribution", "Execution Distribution"),
        ):
            chart = _chart_from_buckets(title, charts_payload.get(key))
            if chart is not None:
                charts.append(chart)
    return {
        "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
        "generated_by": clustering.get("generated_by"),
        "available": clustering.get("available"),
        "algorithm": clustering.get("algorithm"),
        "linkage": clustering.get("linkage"),
        "similarity_metric": clustering.get("similarity_metric"),
        "similarity_threshold": clustering.get("similarity_threshold"),
        "embedding_version": clustering.get("embedding_version"),
        "embedding_strategy": clustering.get("embedding_strategy"),
        "cluster_version": clustering.get("cluster_version"),
        "session_hash": clustering.get("session_hash"),
        "lot_count": clustering.get("lot_count"),
        "lots": _snapshot(clustering.get("lots") or []),
        "total_clusters": clustering.get("total_clusters"),
        "largest_cluster": clustering.get("largest_cluster"),
        "smallest_cluster": clustering.get("smallest_cluster"),
        "average_cluster_size": clustering.get("average_cluster_size"),
        "singleton_clusters": clustering.get("singleton_clusters"),
        "patterns_clustered": clustering.get("patterns_clustered"),
        "units_total": clustering.get("units_total"),
        "units_clustered": clustering.get("units_clustered"),
        "units_downsampled": clustering.get("units_downsampled"),
        "units_sample_size": clustering.get("units_sample_size"),
        "clusters": _top_rows(
            clusters,
            sort_key=lambda row: (
                -int(row.get("execution_count") or 0),
                str(row.get("cluster_id") or ""),
            ),
            drop=("executions",),
        ),
        "unit_assignments": _top_rows(
            assignments,
            sort_key=lambda row: (
                -float(row.get("similarity_to_centroid") or 0.0),
                str(row.get("unit_id") or ""),
            ),
        ),
        "charts": charts,
        "source": _source_ref(
            provenance,
            row_count=len(assignments) or clustering.get("units_total"),
        ),
    }


def _slim_redundancy(
    redundancy: Optional[Mapping[str, Any]],
    provenance: Mapping[str, Any],
) -> Dict[str, Any]:
    if not isinstance(redundancy, Mapping):
        return {
            "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
            "source": _source_ref(provenance),
        }
    candidates = [
        row for row in (redundancy.get("candidates") or []) if isinstance(row, Mapping)
    ]
    charts: List[Dict[str, Any]] = []
    charts_payload = redundancy.get("charts")
    if isinstance(charts_payload, Mapping):
        for key, title in (
            ("confidence_distribution", "Confidence Distribution"),
            ("lot_pair_contribution", "LOT Pair Contribution"),
        ):
            chart = _chart_from_buckets(title, charts_payload.get(key))
            if chart is not None:
                charts.append(chart)
    confidences = [
        float(row.get("confidence_score"))
        for row in candidates
        if row.get("confidence_score") is not None
    ]
    return {
        "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
        "generated_by": redundancy.get("generated_by"),
        "available": redundancy.get("available"),
        "session_hash": redundancy.get("session_hash"),
        "embedding_version": redundancy.get("embedding_version"),
        "cluster_version": redundancy.get("cluster_version"),
        "similarity_threshold": redundancy.get("similarity_threshold"),
        "confidence_source": redundancy.get("confidence_source"),
        "lot_count": redundancy.get("lot_count"),
        "units_total": redundancy.get("units_total"),
        "units_represented": redundancy.get("units_represented"),
        "clusters_evaluated": redundancy.get("clusters_evaluated"),
        "total_candidates": redundancy.get("total_candidates", len(candidates)),
        "candidates_per_cluster_avg": redundancy.get("candidates_per_cluster_avg"),
        "neighbors_per_unit": redundancy.get("neighbors_per_unit"),
        "candidates_per_cluster_cap": redundancy.get("candidates_per_cluster_cap"),
        "validation_status": redundancy.get("validation_status"),
        "average_confidence": (
            round(sum(confidences) / len(confidences), 4) if confidences else None
        ),
        "highest_confidence": (
            round(max(confidences), 4) if confidences else None
        ),
        "candidates": _top_rows(
            candidates,
            sort_key=lambda row: (
                -float(row.get("confidence_score") or 0.0),
                -float(row.get("raw_similarity") or 0.0),
                str(row.get("pattern_a") or ""),
                str(row.get("pattern_b") or ""),
            ),
        ),
        "charts": charts,
        "source": _source_ref(provenance, row_count=len(candidates)),
    }


def _slim_similarity(
    similarity: Optional[Mapping[str, Any]],
    provenance: Mapping[str, Any],
) -> Dict[str, Any]:
    if not isinstance(similarity, Mapping):
        return {
            "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
            "source": _source_ref(provenance),
        }
    pairs = [
        row
        for row in (similarity.get("similarity_pairs") or [])
        if isinstance(row, Mapping)
    ]
    distribution = similarity.get("distribution")
    charts = []
    chart = _chart_from_buckets("Similarity Distribution", distribution)
    if chart is not None:
        charts.append(chart)
    summary = similarity.get("summary")
    summary = summary if isinstance(summary, Mapping) else {}
    return {
        "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
        "generated_by": similarity.get("generated_by"),
        "artifact_version": similarity.get("artifact_version"),
        "embedding_version": similarity.get("embedding_version"),
        "embedding_dimension": similarity.get("embedding_dimension"),
        "session_hash": similarity.get("session_hash"),
        "generated_timestamp": similarity.get("generated_timestamp"),
        "similarity_metric": similarity.get("similarity_metric"),
        "top_n": similarity.get("top_n"),
        "effective_top_n": similarity.get("effective_top_n"),
        "summary": _snapshot(summary),
        "distribution": _snapshot(distribution),
        "stable_patterns": _top_rows(
            similarity.get("stable_patterns") or [],
            limit=20,
        ),
        "divergent_patterns": _top_rows(
            similarity.get("divergent_patterns") or [],
            limit=20,
        ),
        "similarity_pairs": _top_rows(
            pairs,
            sort_key=lambda row: (
                -float(row.get("cosine_similarity") or 0.0),
                str(row.get("unit_a") or ""),
                str(row.get("unit_b") or ""),
            ),
        ),
        "validation": _snapshot(similarity.get("validation")),
        "charts": charts,
        "source": _source_ref(provenance, row_count=len(pairs)),
    }


def _slim_outcomes(
    correlation: Optional[Mapping[str, Any]],
    provenance: Mapping[str, Any],
) -> Dict[str, Any]:
    if not isinstance(correlation, Mapping):
        return {
            "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
            "source": _source_ref(provenance),
        }
    outcomes = [
        row for row in (correlation.get("outcomes") or []) if isinstance(row, Mapping)
    ]
    pass_count = int(correlation.get("pass_count") or 0)
    fail_count = int(correlation.get("fail_count") or 0)
    unknown_count = int(correlation.get("unknown_count") or 0)
    charts = [
        chart
        for chart in (
            _chart_from_buckets(
                "PASS vs FAIL",
                [
                    {"label": "PASS", "count": pass_count},
                    {"label": "FAIL", "count": fail_count},
                    {"label": "Unknown", "count": unknown_count},
                ],
            ),
        )
        if chart is not None
    ]
    return {
        "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
        "generated_by": correlation.get("generated_by"),
        "available": correlation.get("available"),
        "correlation_version": correlation.get("correlation_version"),
        "session_hash": correlation.get("session_hash"),
        "execution_count": correlation.get("execution_count"),
        "outcome_count": correlation.get("outcome_count", len(outcomes)),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "unknown_count": unknown_count,
        "lot_count": correlation.get("lot_count"),
        "lots": _snapshot(correlation.get("lots") or []),
        "unique_patterns": correlation.get("unique_patterns"),
        "cross_lot_outcomes": correlation.get("cross_lot_outcomes"),
        "validation_status": correlation.get("validation_status"),
        "outcomes": _top_rows(
            outcomes,
            sort_key=lambda row: (
                -int(row.get("fail_count") or 0),
                -int(row.get("execution_count") or 0),
                str(row.get("pattern_id") or ""),
            ),
        ),
        "charts": charts,
        "source": _source_ref(provenance, row_count=len(outcomes)),
    }


def _format_top_contributors(contributors: Any) -> str:
    if not isinstance(contributors, list):
        return ""
    parts: List[str] = []
    for item in contributors[:5]:
        if isinstance(item, Mapping):
            name = item.get("feature") or item.get("name") or item.get("feature_name")
            weight = item.get("contribution")
            if weight is None:
                weight = item.get("weight")
            if name is None:
                continue
            if weight is None:
                parts.append(str(name))
            else:
                try:
                    parts.append(f"{name}:{float(weight):.4f}")
                except (TypeError, ValueError):
                    parts.append(f"{name}:{weight}")
        else:
            parts.append(str(item))
    return "; ".join(parts)


def _slim_failure_predictions(
    predictions_payload: Optional[Mapping[str, Any]],
    provenance: Mapping[str, Any],
) -> Dict[str, Any]:
    if not isinstance(predictions_payload, Mapping):
        return {
            "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
            "advisory": True,
            "source": _source_ref(provenance),
        }
    raw_predictions = [
        row
        for row in (predictions_payload.get("predictions") or [])
        if isinstance(row, Mapping)
    ]
    slim_rows: List[Dict[str, Any]] = []
    for row in raw_predictions:
        slim_rows.append(
            {
                "unit_id": row.get("unit_id"),
                "pattern_id": row.get("pattern_id"),
                "source_log": row.get("source_log"),
                "score": row.get("score"),
                "label_pred": row.get("label_pred"),
                "top_contributors": _format_top_contributors(
                    row.get("top_contributors")
                ),
            }
        )
    slim_rows = _top_rows(
        slim_rows,
        sort_key=lambda row: (
            -float(row.get("score") or 0.0),
            str(row.get("unit_id") or ""),
        ),
    )
    predicted_fail = sum(
        1 for row in slim_rows if int(row.get("label_pred") or 0) == 1
    )
    return {
        "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
        "advisory": True,
        "generated_by": predictions_payload.get("generated_by"),
        "model_version": predictions_payload.get("model_version"),
        "feature_schema_version": predictions_payload.get("feature_schema_version"),
        "session_hash": predictions_payload.get("session_hash"),
        "prediction_count": int(
            predictions_payload.get("prediction_count") or len(raw_predictions)
        ),
        "display_count": len(slim_rows),
        "predicted_fail_count": predicted_fail,
        "predictions": slim_rows,
        "source": _source_ref(provenance, row_count=len(raw_predictions)),
    }


def _slim_failure_predictions_by_lot(
    predictions_payload: Optional[Mapping[str, Any]],
    provenance: Mapping[str, Any],
) -> Dict[str, Any]:
    if not isinstance(predictions_payload, Mapping):
        return {
            "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
            "advisory": True,
            "grain": "pattern_x_lot",
            "source": _source_ref(provenance),
        }
    raw_predictions = [
        row
        for row in (predictions_payload.get("predictions") or [])
        if isinstance(row, Mapping)
    ]
    slim_rows: List[Dict[str, Any]] = []
    for row in raw_predictions:
        slim_rows.append(
            {
                "unit_id": row.get("unit_id"),
                "pattern_id": row.get("pattern_id"),
                "source_lot": row.get("source_lot"),
                "log_count_in_lot": row.get("log_count_in_lot"),
                "score": row.get("score"),
                "label_pred": row.get("label_pred"),
                "top_contributors": _format_top_contributors(
                    row.get("top_contributors")
                ),
            }
        )
    slim_rows = _top_rows(
        slim_rows,
        sort_key=lambda row: (
            -float(row.get("score") or 0.0),
            str(row.get("unit_id") or ""),
        ),
    )
    predicted_fail = sum(
        1 for row in slim_rows if int(row.get("label_pred") or 0) == 1
    )
    return {
        "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
        "advisory": True,
        "grain": "pattern_x_lot",
        "generated_by": predictions_payload.get("generated_by"),
        "model_version": predictions_payload.get("model_version"),
        "feature_schema_version": predictions_payload.get("feature_schema_version"),
        "session_hash": predictions_payload.get("session_hash"),
        "prediction_count": int(
            predictions_payload.get("prediction_count") or len(raw_predictions)
        ),
        "display_count": len(slim_rows),
        "predicted_fail_count": predicted_fail,
        "predictions": slim_rows,
        "source": _source_ref(provenance, row_count=len(raw_predictions)),
    }


def _slim_anomaly_scores(
    scores_payload: Optional[Mapping[str, Any]],
    provenance: Mapping[str, Any],
    *,
    grain: str,
) -> Dict[str, Any]:
    if not isinstance(scores_payload, Mapping):
        return {
            "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
            "advisory": True,
            "grain": grain,
            "source": _source_ref(provenance),
        }
    raw_scores = [
        row for row in (scores_payload.get("scores") or []) if isinstance(row, Mapping)
    ]
    slim_rows: List[Dict[str, Any]] = []
    for row in raw_scores:
        slim_rows.append(
            {
                "unit_id": row.get("unit_id"),
                "pattern_id": row.get("pattern_id"),
                "source_log": row.get("source_log"),
                "source_lot": row.get("source_lot"),
                "log_count_in_lot": row.get("log_count_in_lot"),
                "anomaly_score": row.get("anomaly_score"),
                "is_anomaly": row.get("is_anomaly"),
                "top_contributors": _format_top_contributors(
                    row.get("top_contributors")
                ),
            }
        )
    slim_rows = _top_rows(
        slim_rows,
        sort_key=lambda row: (
            -float(row.get("anomaly_score") or 0.0),
            str(row.get("unit_id") or ""),
        ),
    )
    anomaly_count = sum(int(row.get("is_anomaly") or 0) for row in slim_rows)
    return {
        "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
        "advisory": True,
        "grain": grain,
        "generated_by": scores_payload.get("generated_by"),
        "model_version": scores_payload.get("model_version"),
        "feature_schema_version": scores_payload.get("feature_schema_version"),
        "session_hash": scores_payload.get("session_hash"),
        "score_count": int(scores_payload.get("score_count") or len(raw_scores)),
        "display_count": len(slim_rows),
        "anomaly_count": int(scores_payload.get("anomaly_count") or anomaly_count),
        "scores": slim_rows,
        "source": _source_ref(provenance, row_count=len(raw_scores)),
    }


def _slim_root_cause_rankings(
    rankings_payload: Optional[Mapping[str, Any]],
    provenance: Mapping[str, Any],
    *,
    grain: str,
) -> Dict[str, Any]:
    if not isinstance(rankings_payload, Mapping):
        return {
            "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
            "advisory": True,
            "grain": grain,
            "source": _source_ref(provenance),
        }
    raw_rankings = [
        row for row in (rankings_payload.get("rankings") or []) if isinstance(row, Mapping)
    ]
    slim_rows: List[Dict[str, Any]] = []
    for row in raw_rankings:
        slim_rows.append(
            {
                "investigation_rank": row.get("investigation_rank"),
                "investigation_score": row.get("investigation_score"),
                "unit_id": row.get("unit_id"),
                "pattern_id": row.get("pattern_id"),
                "scan_chain_id": row.get("scan_chain_id"),
                "source_log": row.get("source_log"),
                "source_lot": row.get("source_lot"),
                "log_count_in_lot": row.get("log_count_in_lot"),
                "actual_result": row.get("actual_result"),
                "hypothesis_tags": row.get("hypothesis_tags"),
                "top_contributors": _format_top_contributors(
                    row.get("top_contributors")
                ),
            }
        )
    slim_rows = _top_rows(
        slim_rows,
        sort_key=lambda row: (
            int(row.get("investigation_rank") or 999999),
            str(row.get("unit_id") or ""),
        ),
    )
    fail_count = sum(
        1
        for row in slim_rows
        if str(row.get("actual_result") or "").upper() == "FAIL"
    )
    chain_summaries = [
        row
        for row in (rankings_payload.get("chain_summaries") or [])
        if isinstance(row, Mapping)
    ][:TOP_N]
    return {
        "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
        "advisory": True,
        "grain": grain,
        "disclaimer": rankings_payload.get("disclaimer"),
        "generated_by": rankings_payload.get("generated_by"),
        "model_version": rankings_payload.get("model_version"),
        "feature_schema_version": rankings_payload.get("feature_schema_version"),
        "session_hash": rankings_payload.get("session_hash"),
        "ranking_count": int(
            rankings_payload.get("ranking_count") or len(raw_rankings)
        ),
        "display_count": len(slim_rows),
        "fail_count": int(rankings_payload.get("fail_count") or fail_count),
        "rankings": slim_rows,
        "chain_summaries": chain_summaries,
        "source": _source_ref(provenance, row_count=len(raw_rankings)),
    }


def _slim_pattern_recommendations(
    recommendations_payload: Optional[Mapping[str, Any]],
    provenance: Mapping[str, Any],
    *,
    grain: str,
) -> Dict[str, Any]:
    if not isinstance(recommendations_payload, Mapping):
        return {
            "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
            "advisory": True,
            "grain": grain,
            "source": _source_ref(provenance),
        }
    raw_rows = [
        row
        for row in (recommendations_payload.get("recommendations") or [])
        if isinstance(row, Mapping)
    ]
    slim_rows: List[Dict[str, Any]] = []
    for row in raw_rows:
        signals = row.get("signals") if isinstance(row.get("signals"), Mapping) else {}
        slim_rows.append(
            {
                "recommendation_rank": row.get("recommendation_rank"),
                "priority_score": row.get("priority_score"),
                "priority_tier": row.get("priority_tier"),
                "recommended_action": row.get("recommended_action"),
                "unit_id": row.get("unit_id"),
                "pattern_id": row.get("pattern_id"),
                "scan_chain_id": row.get("scan_chain_id"),
                "source_log": row.get("source_log"),
                "source_lot": row.get("source_lot"),
                "log_count_in_lot": row.get("log_count_in_lot"),
                "actual_result": row.get("actual_result"),
                "rationale": row.get("rationale"),
                "failure_score": signals.get("failure_score"),
                "anomaly_score": signals.get("anomaly_score"),
                "investigation_score": signals.get("investigation_score"),
            }
        )
    slim_rows = _top_rows(
        slim_rows,
        sort_key=lambda row: (
            int(row.get("recommendation_rank") or 999999),
            str(row.get("unit_id") or ""),
        ),
    )
    high_count = sum(
        1 for row in slim_rows if str(row.get("priority_tier") or "") == "HIGH"
    )
    return {
        "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
        "advisory": True,
        "grain": grain,
        "disclaimer": recommendations_payload.get("disclaimer"),
        "generated_by": recommendations_payload.get("generated_by"),
        "model_version": recommendations_payload.get("model_version"),
        "policy_version": recommendations_payload.get("policy_version"),
        "session_hash": recommendations_payload.get("session_hash"),
        "recommendation_count": int(
            recommendations_payload.get("recommendation_count") or len(raw_rows)
        ),
        "display_count": len(slim_rows),
        "high_priority_count": int(
            recommendations_payload.get("high_priority_count") or high_count
        ),
        "recommendations": slim_rows,
        "source": _source_ref(provenance, row_count=len(raw_rows)),
    }


def build_analysis_session_report_model(
    sources: AnalysisSessionReportSources,
) -> Dict[str, Any]:
    artifacts = dict(sources.artifacts)
    manifest = artifacts.get("manifest")
    summary_source = artifacts.get("summary")
    executions = artifacts.get("executions")
    scan_vectors = artifacts.get("scan_vectors")
    embeddings = artifacts.get("embeddings")
    similarity = artifacts.get("similarity")
    clustering = artifacts.get("clustering")
    redundancy = artifacts.get("redundancy")
    correlation = artifacts.get("pattern_outcomes")
    provenance_map = sources.provenance
    optional_artifacts = dict(sources.optional_artifacts)
    optional_provenance = dict(sources.optional_provenance)
    failure_predictions_by_lot = optional_artifacts.get("failure_predictions_by_lot")
    failure_predictions = optional_artifacts.get("failure_predictions")
    anomaly_scores_by_lot = optional_artifacts.get("anomaly_scores_by_lot")
    anomaly_scores = optional_artifacts.get("anomaly_scores")
    root_cause_rankings_by_lot = optional_artifacts.get("root_cause_rankings_by_lot")
    root_cause_rankings = optional_artifacts.get("root_cause_rankings")
    pattern_recommendations_by_lot = optional_artifacts.get("pattern_recommendations_by_lot")
    pattern_recommendations = optional_artifacts.get("pattern_recommendations")

    warnings = sorted(set(str(item) for item in sources.validation_warnings))

    metadata = {
        "workflow": "analysis_session",
        "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
        "stil_filename": manifest.get("stil_file") if manifest else None,
        "session_hash": _first_present(
            (manifest, similarity, clustering, redundancy, correlation),
            "session_hash",
        ),
        "generated_timestamp": (
            manifest.get("generated_timestamp") if manifest else None
        ),
        "lot_count": _first_present(
            (clustering, redundancy, correlation),
            "lot_count",
        ),
        "ate_log_count": manifest.get("execution_count") if manifest else None,
        "execution_count": (
            correlation.get("execution_count") if correlation else None
        ),
        "execution_record_count": (
            summary_source.get("execution_record_count") if summary_source else None
        ),
        "embedding_version": (
            embeddings.get("embedding_version") if embeddings else None
        ),
        "embedding_dimension": (
            embeddings.get("embedding_dimension") if embeddings else None
        ),
        "pattern_count": (
            correlation.get("unique_patterns")
            if correlation
            else (embeddings.get("patterns_embedded") if embeddings else None)
        ),
    }

    section_warnings: Dict[str, List[str]] = {
        section_id: [] for section_id, _ in SECTION_ORDER
    }
    artifact_to_section = {
        "manifest": "session_overview",
        "summary": "session_overview",
        "executions": "toggle_coverage",
        "scan_vectors": "scan_vectors",
        "embeddings": "embeddings",
        "similarity": "similarity",
        "clustering": "clustering",
        "redundancy": "redundancy",
        "pattern_outcomes": "pattern_outcomes",
    }
    for logical_name, provenance in provenance_map.items():
        if provenance.get("status") != "Complete":
            section_id = artifact_to_section.get(logical_name)
            if section_id:
                section_warnings[section_id].append(
                    f"{provenance.get('artifact_filename')} is missing or unreadable."
                )
    if summary_source is None:
        section_warnings["toggle_coverage"].append(
            "PA-Analysis-Session_summary.json is missing or unreadable."
        )
    loaded_count = sum(artifact is not None for artifact in artifacts.values())
    expected_count = len(SESSION_ARTIFACTS)
    appendix_status = (
        "Missing"
        if loaded_count == 0
        else ("Complete" if loaded_count == expected_count else "Partial")
    )

    sections = [
        _section(
            "session_overview",
            "Session Overview",
            _presence_status(manifest, summary_source),
            _slim_overview(manifest, summary_source, provenance_map),
            section_warnings["session_overview"],
        ),
        _section(
            "toggle_coverage",
            "Toggle Coverage",
            _presence_status(summary_source, executions),
            _slim_toggle(summary_source, executions, provenance_map),
            section_warnings["toggle_coverage"],
        ),
        _section(
            "scan_vectors",
            "Scan Vectors",
            _presence_status(scan_vectors),
            _slim_scan_vectors(scan_vectors, provenance_map.get("scan_vectors") or {}),
            section_warnings["scan_vectors"],
        ),
        _section(
            "embeddings",
            "Embeddings",
            _presence_status(embeddings),
            _slim_embeddings(embeddings, provenance_map.get("embeddings") or {}),
            section_warnings["embeddings"],
        ),
        _section(
            "clustering",
            "Clustering",
            _presence_status(clustering),
            _slim_clustering(clustering, provenance_map.get("clustering") or {}),
            section_warnings["clustering"],
        ),
        _section(
            "redundancy",
            "Redundancy",
            _presence_status(redundancy),
            _slim_redundancy(redundancy, provenance_map.get("redundancy") or {}),
            section_warnings["redundancy"],
        ),
        _section(
            "similarity",
            "Similarity",
            _presence_status(similarity),
            _slim_similarity(similarity, provenance_map.get("similarity") or {}),
            section_warnings["similarity"],
        ),
        _section(
            "pattern_outcomes",
            "Pattern Outcomes",
            _presence_status(correlation),
            _slim_outcomes(correlation, provenance_map.get("pattern_outcomes") or {}),
            section_warnings["pattern_outcomes"],
        ),
    ]

    if anomaly_scores_by_lot is not None:
        sections.append(
            _section(
                "anomaly_by_lot",
                "Anomaly by LOT (PA-ML-002)",
                "Complete",
                _slim_anomaly_scores(
                    anomaly_scores_by_lot,
                    optional_provenance.get("anomaly_scores_by_lot") or {},
                    grain="pattern_x_lot",
                ),
                (),
            )
        )

    if anomaly_scores is not None:
        sections.append(
            _section(
                "anomaly",
                "Anomaly by Log (PA-ML-002)",
                "Complete",
                _slim_anomaly_scores(
                    anomaly_scores,
                    optional_provenance.get("anomaly_scores") or {},
                    grain="pattern_x_source_log",
                ),
                (),
            )
        )

    if failure_predictions_by_lot is not None:
        sections.append(
            _section(
                "failure_risk_by_lot",
                "Failure Risk by LOT (PA-ML-001)",
                "Complete",
                _slim_failure_predictions_by_lot(
                    failure_predictions_by_lot,
                    optional_provenance.get("failure_predictions_by_lot") or {},
                ),
                (),
            )
        )

    if failure_predictions is not None:
        sections.append(
            _section(
                "failure_risk",
                "Failure Risk by Log (PA-ML-001)",
                "Complete",
                _slim_failure_predictions(
                    failure_predictions,
                    optional_provenance.get("failure_predictions") or {},
                ),
                (),
            )
        )

    if root_cause_rankings_by_lot is not None:
        sections.append(
            _section(
                "root_cause_by_lot",
                "Root Cause by LOT (PA-ML-003)",
                "Complete",
                _slim_root_cause_rankings(
                    root_cause_rankings_by_lot,
                    optional_provenance.get("root_cause_rankings_by_lot") or {},
                    grain="pattern_x_lot",
                ),
                (),
            )
        )

    if root_cause_rankings is not None:
        sections.append(
            _section(
                "root_cause",
                "Root Cause by Log (PA-ML-003)",
                "Complete",
                _slim_root_cause_rankings(
                    root_cause_rankings,
                    optional_provenance.get("root_cause_rankings") or {},
                    grain="pattern_x_source_log",
                ),
                (),
            )
        )

    if pattern_recommendations_by_lot is not None:
        sections.append(
            _section(
                "recommendations_by_lot",
                "Recommendations by LOT (PA-ML-004)",
                "Complete",
                _slim_pattern_recommendations(
                    pattern_recommendations_by_lot,
                    optional_provenance.get("pattern_recommendations_by_lot") or {},
                    grain="pattern_x_lot",
                ),
                (),
            )
        )

    if pattern_recommendations is not None:
        sections.append(
            _section(
                "recommendations",
                "Recommendations by Log (PA-ML-004)",
                "Complete",
                _slim_pattern_recommendations(
                    pattern_recommendations,
                    optional_provenance.get("pattern_recommendations") or {},
                    grain="pattern_x_source_log",
                ),
                (),
            )
        )

    validation_status = "Partial" if warnings else "Complete"
    provenance_records = [
        _snapshot(provenance_map.get(logical_name, {}))
        for logical_name, _ in SESSION_ARTIFACTS
    ]
    source_hashes = {
        str(record.get("artifact_filename")): record.get("sha256")
        for record in provenance_records
        if record.get("sha256") is not None
    }

    phase_completion = {
        "phase_1_ingestion": _presence_status(manifest),
        "phase_2_scan_vectors": _presence_status(scan_vectors),
        "phase_3_metadata": _presence_status(manifest, summary_source),
        "phase_4_toggle": _presence_status(summary_source, executions),
        "phase_5_embeddings": _presence_status(embeddings),
        "phase_6_clustering": _presence_status(clustering),
        "phase_7_redundancy": _presence_status(redundancy),
        "phase_8_similarity": _presence_status(similarity),
        "phase_9_correlation": _presence_status(correlation),
    }
    complete_phases = sum(status == "Complete" for status in phase_completion.values())
    completion_pct = round(100.0 * complete_phases / max(1, len(phase_completion)), 1)

    sections.extend(
        [
            _section(
                "validation",
                "Validation",
                validation_status,
                {
                    "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
                    "status": validation_status,
                    "warnings": warnings,
                    "phase_completion": phase_completion,
                    "completion_pct": completion_pct,
                },
                warnings,
            ),
            _section(
                "appendix",
                "Appendix",
                appendix_status,
                {
                    "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
                    "artifacts": provenance_records,
                },
                (),
            ),
        ]
    )

    section_counts = {
        status: sum(section["status"] == status for section in sections)
        for status in ("Complete", "Partial", "Missing")
    }
    provenance = {
        "artifacts": provenance_records,
        "loaded_artifact_count": loaded_count,
        "expected_artifact_count": expected_count,
    }
    engineering_status = (
        "ENGINEERING ANALYSIS COMPLETE"
        if complete_phases == len(phase_completion) and not warnings
        else "ENGINEERING ANALYSIS PARTIAL"
    )
    model: Dict[str, Any] = {
        "generated_by": REPORT_GENERATED_BY,
        "metadata": metadata,
        "provenance": provenance,
        "validation": {
            "status": validation_status,
            "warnings": warnings,
            "phase_completion": phase_completion,
            "completion_pct": completion_pct,
        },
        "sections": sections,
        "warnings": warnings,
        "hashes": {
            "source_artifacts": dict(sorted(source_hashes.items())),
            "model_hash": None,
        },
        "summary": {
            "section_counts": section_counts,
            "lot_count": metadata["lot_count"],
            "ate_log_count": metadata["ate_log_count"],
            "execution_count": metadata["execution_count"],
            "execution_record_count": metadata["execution_record_count"],
            "pattern_count": metadata.get("pattern_count"),
            "completion_pct": completion_pct,
            "engineering_status": engineering_status,
        },
        "appendix": {
            "artifact_inventory": provenance_records,
            "source_versions": {
                str(record.get("logical_name")): record.get("version")
                for record in provenance_records
            },
        },
        "generation_metadata": {
            "generated_by": REPORT_GENERATED_BY,
            "report_version": REPORT_VERSION,
            "report_generator_version": REPORT_GENERATOR_VERSION,
            "presentation_schema_version": PRESENTATION_SCHEMA_VERSION,
            "build_timestamp": metadata["generated_timestamp"],
            "validation_status": validation_status,
            "model_hash": None,
        },
    }
    model_hash = _model_hash(model)
    model["hashes"]["model_hash"] = model_hash
    model["generation_metadata"]["model_hash"] = model_hash
    return model


def build_analysis_session_report_model_from_artifacts(
    output_dir: str,
) -> Dict[str, Any]:
    return build_analysis_session_report_model(
        load_analysis_session_report_sources(output_dir)
    )


def write_analysis_session_report_model(
    output_dir: str,
    *,
    session: Optional[AnalysisSession] = None,
    artifact_hashes: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """
    Write PA-Analysis-Session_report_model.json.

    When session is provided (pipeline hot path), builds from in-memory
    AnalysisSession and write-phase hashes — no core artifact json.load.
    When session is None, falls back to disk reload (standalone re-run).
    """
    if session is not None:
        model = build_analysis_session_report_model_from_session(
            session,
            artifact_hashes=artifact_hashes,
            output_dir=output_dir,
        )
    else:
        model = build_analysis_session_report_model_from_artifacts(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, REPORT_MODEL_FILENAME)
    temporary_path = f"{path}.tmp"
    try:
        with open(temporary_path, "w", encoding="utf-8") as handle:
            json.dump(
                model,
                handle,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
        os.replace(temporary_path, path)
    except Exception:
        try:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)
        except OSError:
            pass
        raise
    return model
