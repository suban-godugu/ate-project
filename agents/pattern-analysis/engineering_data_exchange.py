"""
PA-FR-011 — Engineering Data Exchange helpers.

Read-only normalization/merge utilities for pattern_analysis_master.json.
Never recalculates engineering metrics. Never reads PA-FR-* artifacts.
Never mutates Analysis Session source files.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

SCHEMA_VERSION = "1.0"
EXPORT_VERSION = "1.0"
GENERATED_BY = "Pattern Analysis Agent"
ANALYSIS_MODE = "Analysis Session"
EXPORT_TYPE = "Engineering Data Exchange"
MASTER_FILENAME = "pattern_analysis_master.json"
REPORT_MODEL_FILENAME = "PA-Analysis-Session_report_model.json"

SESSION_MANIFEST = "PA-Analysis-Session_manifest.json"
SESSION_SUMMARY = "PA-Analysis-Session_summary.json"
SESSION_EXECUTIONS = "PA-Analysis-Session_executions.json"
SESSION_SCAN_VECTORS = "PA-Analysis-Session_scan_vectors.json"
SESSION_EMBEDDINGS = "PA-Analysis-Session_embeddings.json"
SESSION_SIMILARITY = "PA-Analysis-Session_similarity.json"
SESSION_CLUSTERING = "PA-Analysis-Session_clustering.json"
SESSION_REDUNDANCY = "PA-Analysis-Session_redundancy.json"
SESSION_CORRELATION = "PA-Analysis-Session_correlation.json"

CORE_ARTIFACTS: Tuple[Tuple[str, str], ...] = (
    ("manifest", SESSION_MANIFEST),
    ("summary", SESSION_SUMMARY),
    ("executions", SESSION_EXECUTIONS),
    ("scan_vectors", SESSION_SCAN_VECTORS),
    ("embeddings", SESSION_EMBEDDINGS),
    ("similarity", SESSION_SIMILARITY),
    ("clustering", SESSION_CLUSTERING),
    ("redundancy", SESSION_REDUNDANCY),
    ("correlation", SESSION_CORRELATION),
)

OPTIONAL_ARTIFACTS: Tuple[Tuple[str, str], ...] = (
    ("report_model", REPORT_MODEL_FILENAME),
)

MASTER_TOP_LEVEL_KEYS: Tuple[str, ...] = (
    "schema_version",
    "generated_by",
    "analysis_mode",
    "analysis_session_id",
    "generated_timestamp",
    "export_information",
    "analysis_summary",
    "analysis_dataset",
    "analysis_pipeline_versions",
    "source_artifacts",
    "source_hashes",
    "pattern_metadata",
    "pattern_characteristics",
    "embeddings",
    "clusters",
    "cluster_statistics",
    "similarity_matrix",
    "structural_similarity",
    "pattern_metrics",
    "pattern_rankings",
)

CLUSTER_STAT_KEYS: Tuple[str, ...] = (
    "algorithm",
    "linkage",
    "similarity_metric",
    "similarity_threshold",
    "embedding_version",
    "embedding_strategy",
    "cluster_version",
    "session_hash",
    "lot_count",
    "lots",
    "execution_record_count",
    "patterns_clustered",
    "units_total",
    "units_clustered",
    "units_sample_size",
    "units_downsampled",
    "total_clusters",
    "largest_cluster",
    "smallest_cluster",
    "average_cluster_size",
    "singleton_clusters",
    "silhouette_score",
)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def snapshot(value: Any) -> Any:
    return copy.deepcopy(value)


def file_sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tie_key(
    pattern_id: Any = None,
    unit_id: Any = None,
    scan_chain_id: Any = None,
    run_id: Any = None,
) -> Tuple[str, str, str, str]:
    return (
        str(pattern_id or ""),
        str(unit_id or ""),
        str(scan_chain_id or ""),
        str(run_id if run_id is not None else ""),
    )


def read_session_artifact(
    output_dir: str,
    logical_name: str,
    filename: str,
    warnings: Optional[List[str]] = None,
    *,
    required: bool = True,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """Load one Analysis Session JSON file. Never opens PA-FR-* paths."""
    if filename.startswith("PA-FR-"):
        raise ValueError(f"PA-FR-* artifacts are forbidden: {filename}")

    path = os.path.join(output_dir, filename)
    provenance: Dict[str, Any] = {
        "logical_name": logical_name,
        "artifact_filename": filename,
        "status": "Missing",
        "sha256": None,
        "generated_by": None,
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
        artifact_hash = file_sha256(path)
    except OSError as exc:
        if required and warnings is not None:
            warnings.append(f"Unreadable artifact {filename}: {exc}")
        return None, provenance

    provenance.update(
        {
            "status": "Complete",
            "sha256": artifact_hash,
            "generated_by": payload.get("generated_by"),
        }
    )
    return payload, provenance


def load_exchange_sources(output_dir: str) -> Dict[str, Any]:
    """Read allowlisted Analysis Session artifacts only."""
    artifacts: Dict[str, Optional[Dict[str, Any]]] = {}
    provenance: Dict[str, Dict[str, Any]] = {}
    warnings: List[str] = []

    for logical_name, filename in CORE_ARTIFACTS:
        payload, record = read_session_artifact(
            output_dir,
            logical_name,
            filename,
            warnings,
            required=True,
        )
        artifacts[logical_name] = payload
        provenance[logical_name] = record

    for logical_name, filename in OPTIONAL_ARTIFACTS:
        payload, record = read_session_artifact(
            output_dir,
            logical_name,
            filename,
            warnings=None,
            required=False,
        )
        artifacts[logical_name] = payload
        provenance[logical_name] = record

    return {
        "artifacts": artifacts,
        "provenance": provenance,
        "warnings": warnings,
    }


def _as_mapping(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else []


def _pattern_ids_from_sources(artifacts: Mapping[str, Optional[Mapping[str, Any]]]) -> List[str]:
    ids: set[str] = set()
    executions = _as_mapping(artifacts.get("executions")).get("executions")
    for row in _as_list(executions):
        if isinstance(row, Mapping) and row.get("pattern_id") is not None:
            ids.add(str(row["pattern_id"]))

    embeddings = _as_mapping(artifacts.get("embeddings")).get("embeddings")
    for row in _as_list(embeddings):
        if isinstance(row, Mapping) and row.get("pattern_id") is not None:
            ids.add(str(row["pattern_id"]))

    vectors = _as_mapping(artifacts.get("scan_vectors")).get("vectors")
    for row in _as_list(vectors):
        if isinstance(row, Mapping) and row.get("pattern_id") is not None:
            ids.add(str(row["pattern_id"]))

    outcomes = _as_mapping(artifacts.get("correlation")).get("outcomes")
    for row in _as_list(outcomes):
        if isinstance(row, Mapping) and row.get("pattern_id") is not None:
            ids.add(str(row["pattern_id"]))

    return sorted(ids)


def _provenance_for_pattern(
    pattern_id: str,
    artifacts: Mapping[str, Optional[Mapping[str, Any]]],
) -> Dict[str, str]:
    """Lightweight filename provenance for fields contributed by each source."""
    prov: Dict[str, str] = {}
    executions = _as_list(_as_mapping(artifacts.get("executions")).get("executions"))
    if any(isinstance(r, Mapping) and str(r.get("pattern_id")) == pattern_id for r in executions):
        prov["execution_source"] = SESSION_EXECUTIONS

    vectors = _as_list(_as_mapping(artifacts.get("scan_vectors")).get("vectors"))
    if any(isinstance(r, Mapping) and str(r.get("pattern_id")) == pattern_id for r in vectors):
        prov["scan_vector_source"] = SESSION_SCAN_VECTORS

    embeddings = _as_list(_as_mapping(artifacts.get("embeddings")).get("embeddings"))
    if any(isinstance(r, Mapping) and str(r.get("pattern_id")) == pattern_id for r in embeddings):
        prov["embedding_source"] = SESSION_EMBEDDINGS

    clustering = _as_mapping(artifacts.get("clustering"))
    assignments = _as_list(clustering.get("unit_assignments"))
    clusters = _as_list(clustering.get("clusters"))
    if any(isinstance(r, Mapping) and str(r.get("pattern_id")) == pattern_id for r in assignments):
        prov["cluster_source"] = SESSION_CLUSTERING
    elif any(
        isinstance(c, Mapping)
        and any(
            isinstance(e, Mapping) and str(e.get("pattern_id")) == pattern_id
            for e in _as_list(c.get("executions"))
        )
        for c in clusters
    ):
        prov["cluster_source"] = SESSION_CLUSTERING

    similarity = _as_mapping(artifacts.get("similarity"))
    pairs = _as_list(similarity.get("similarity_pairs"))
    if any(
        isinstance(p, Mapping)
        and (
            str(p.get("pattern_a")) == pattern_id or str(p.get("pattern_b")) == pattern_id
        )
        for p in pairs
    ):
        prov["similarity_source"] = SESSION_SIMILARITY

    outcomes = _as_list(_as_mapping(artifacts.get("correlation")).get("outcomes"))
    if any(isinstance(r, Mapping) and str(r.get("pattern_id")) == pattern_id for r in outcomes):
        prov["correlation_source"] = SESSION_CORRELATION

    candidates = _as_list(_as_mapping(artifacts.get("redundancy")).get("candidates"))
    if any(
        isinstance(c, Mapping)
        and (
            str(c.get("pattern_a")) == pattern_id or str(c.get("pattern_b")) == pattern_id
        )
        for c in candidates
    ):
        prov["redundancy_source"] = SESSION_REDUNDANCY

    return prov


def _build_provenance_index(
    artifacts: Mapping[str, Optional[Mapping[str, Any]]],
) -> Dict[str, Dict[str, str]]:
    """
    Build a pattern_id -> {provenance_key: source_artifact_label} index once.

    This preserves the keys/semantics of `_provenance_for_pattern` but avoids
    O(num_patterns * num_records) repeated scans.
    """
    prov_index: Dict[str, Dict[str, str]] = {}

    def _set(pattern_id: str, key: str, value: str) -> None:
        pid = str(pattern_id or "")
        if not pid:
            return
        prov_index.setdefault(pid, {})[key] = value

    executions = _as_list(_as_mapping(artifacts.get("executions")).get("executions"))
    for r in executions:
        if not isinstance(r, Mapping):
            continue
        _set(r.get("pattern_id"), "execution_source", SESSION_EXECUTIONS)

    vectors = _as_list(_as_mapping(artifacts.get("scan_vectors")).get("vectors"))
    for r in vectors:
        if not isinstance(r, Mapping):
            continue
        _set(r.get("pattern_id"), "scan_vector_source", SESSION_SCAN_VECTORS)

    embeddings = _as_list(_as_mapping(artifacts.get("embeddings")).get("embeddings"))
    for r in embeddings:
        if not isinstance(r, Mapping):
            continue
        _set(r.get("pattern_id"), "embedding_source", SESSION_EMBEDDINGS)

    clustering = _as_mapping(artifacts.get("clustering"))
    assignments = _as_list(clustering.get("unit_assignments"))
    for r in assignments:
        if not isinstance(r, Mapping):
            continue
        _set(r.get("pattern_id"), "cluster_source", SESSION_CLUSTERING)

    clusters = _as_list(clustering.get("clusters"))
    for c in clusters:
        if not isinstance(c, Mapping):
            continue
        for e in _as_list(c.get("executions")):
            if not isinstance(e, Mapping):
                continue
            _set(e.get("pattern_id"), "cluster_source", SESSION_CLUSTERING)

    similarity = _as_mapping(artifacts.get("similarity"))
    pairs = _as_list(similarity.get("similarity_pairs"))
    for p in pairs:
        if not isinstance(p, Mapping):
            continue
        _set(p.get("pattern_a"), "similarity_source", SESSION_SIMILARITY)
        _set(p.get("pattern_b"), "similarity_source", SESSION_SIMILARITY)

    outcomes = _as_list(_as_mapping(artifacts.get("correlation")).get("outcomes"))
    for r in outcomes:
        if not isinstance(r, Mapping):
            continue
        _set(r.get("pattern_id"), "correlation_source", SESSION_CORRELATION)

    candidates = _as_list(_as_mapping(artifacts.get("redundancy")).get("candidates"))
    for c in candidates:
        if not isinstance(c, Mapping):
            continue
        _set(c.get("pattern_a"), "redundancy_source", SESSION_REDUNDANCY)
        _set(c.get("pattern_b"), "redundancy_source", SESSION_REDUNDANCY)

    return prov_index


def _provenance_for_pattern_index(
    pattern_id: str,
    prov_index: Mapping[str, Dict[str, str]],
) -> Dict[str, str]:
    """Return a per-pattern provenance dict without repeated scans."""
    return dict(prov_index.get(str(pattern_id or ""), {}) or {})


def build_export_information() -> Dict[str, Any]:
    return {
        "export_version": EXPORT_VERSION,
        "export_type": EXPORT_TYPE,
        "generated_from": ANALYSIS_MODE,
        "deterministic": True,
    }


def build_analysis_summary(artifacts: Mapping[str, Optional[Mapping[str, Any]]]) -> Dict[str, Any]:
    manifest = _as_mapping(artifacts.get("manifest"))
    summary = _as_mapping(artifacts.get("summary"))
    embeddings = _as_mapping(artifacts.get("embeddings"))
    clustering = _as_mapping(artifacts.get("clustering"))
    redundancy = _as_mapping(artifacts.get("redundancy"))
    similarity = _as_mapping(artifacts.get("similarity"))
    correlation = _as_mapping(artifacts.get("correlation"))
    sim_summary = _as_mapping(similarity.get("summary"))

    total_patterns = correlation.get("unique_patterns")
    if total_patterns is None:
        total_patterns = embeddings.get("patterns_embedded")
    if total_patterns is None:
        total_patterns = len(_pattern_ids_from_sources(artifacts))

    return {
        "total_patterns": total_patterns,
        "total_clusters": clustering.get("total_clusters"),
        "candidate_redundant_patterns": redundancy.get("total_candidates"),
        "average_similarity": sim_summary.get("average_similarity"),
        "total_similarity_pairs": sim_summary.get("total_similarity_pairs"),
        "execution_record_count": summary.get("execution_record_count"),
        "ate_log_count": manifest.get("execution_count"),
        "lot_count": clustering.get("lot_count")
        if clustering.get("lot_count") is not None
        else correlation.get("lot_count"),
        "pass_count": correlation.get("pass_count"),
        "fail_count": correlation.get("fail_count"),
    }


def build_analysis_dataset(artifacts: Mapping[str, Optional[Mapping[str, Any]]]) -> Dict[str, Any]:
    manifest = _as_mapping(artifacts.get("manifest"))
    clustering = _as_mapping(artifacts.get("clustering"))
    correlation = _as_mapping(artifacts.get("correlation"))
    lots = clustering.get("lots")
    if lots is None:
        lots = correlation.get("lots")
    lot_count = clustering.get("lot_count")
    if lot_count is None:
        lot_count = correlation.get("lot_count")
    if lot_count is None and isinstance(lots, list):
        lot_count = len(lots)

    return {
        "stil_file": manifest.get("stil_file"),
        "input_ate_logs": snapshot(manifest.get("input_ate_logs") or []),
        "ate_log_count": manifest.get("execution_count"),
        "lots": snapshot(lots) if lots is not None else [],
        "lot_count": lot_count,
        "session_hash": manifest.get("session_hash"),
    }


def build_pipeline_versions(artifacts: Mapping[str, Optional[Mapping[str, Any]]]) -> Dict[str, Any]:
    embeddings = _as_mapping(artifacts.get("embeddings"))
    similarity = _as_mapping(artifacts.get("similarity"))
    clustering = _as_mapping(artifacts.get("clustering"))
    correlation = _as_mapping(artifacts.get("correlation"))
    report_model = _as_mapping(artifacts.get("report_model"))
    generation = _as_mapping(report_model.get("generation_metadata"))

    versions: Dict[str, Any] = {}
    if embeddings:
        versions["pattern_embeddings"] = str(
            embeddings.get("embedding_version")
            if embeddings.get("embedding_version") is not None
            else "session"
        )
    if similarity:
        versions["pattern_similarity"] = str(
            similarity.get("artifact_version")
            if similarity.get("artifact_version") is not None
            else "session"
        )
    if clustering:
        versions["pattern_clustering"] = str(
            clustering.get("cluster_version")
            if clustering.get("cluster_version") is not None
            else "session"
        )
    if artifacts.get("redundancy") is not None:
        # Redundancy has no independent version; reuse cluster/embedding when present.
        versions["redundancy_analysis"] = str(
            clustering.get("cluster_version")
            if clustering.get("cluster_version") is not None
            else embeddings.get("embedding_version")
            if embeddings.get("embedding_version") is not None
            else "session"
        )
    if correlation:
        versions["pass_fail_correlation"] = str(
            correlation.get("correlation_version")
            if correlation.get("correlation_version") is not None
            else "session"
        )
    if artifacts.get("executions") is not None or artifacts.get("summary") is not None:
        versions["toggle_analysis"] = "session"
    if artifacts.get("scan_vectors") is not None or artifacts.get("manifest") is not None:
        versions["pattern_metadata"] = "session"
    if generation.get("report_version") is not None:
        versions["report_model"] = str(generation.get("report_version"))

    return versions


def build_source_artifacts(provenance: Mapping[str, Mapping[str, Any]]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for logical_name, filename in list(CORE_ARTIFACTS) + list(OPTIONAL_ARTIFACTS):
        record = provenance.get(logical_name) or {}
        records.append(
            {
                "logical_name": logical_name,
                "artifact_filename": filename,
                "status": record.get("status", "Missing"),
                "generated_by": record.get("generated_by"),
            }
        )
    return records


def build_source_hashes(provenance: Mapping[str, Mapping[str, Any]]) -> Dict[str, str]:
    hashes: Dict[str, str] = {}
    for logical_name, filename in list(CORE_ARTIFACTS) + list(OPTIONAL_ARTIFACTS):
        record = provenance.get(logical_name) or {}
        sha = record.get("sha256")
        if sha:
            hashes[filename] = str(sha)
    return dict(sorted(hashes.items()))


def build_pattern_metadata(
    artifacts: Mapping[str, Optional[Mapping[str, Any]]],
    provenance_index: Mapping[str, Dict[str, str]],
) -> List[Dict[str, Any]]:
    executions = _as_list(_as_mapping(artifacts.get("executions")).get("executions"))
    scan_vectors = _as_mapping(artifacts.get("scan_vectors"))
    symbol_map = scan_vectors.get("symbol_map")
    symbol_map_snapshot = snapshot(symbol_map) if symbol_map is not None else None

    chains_by_pattern: Dict[str, set[str]] = {}
    units_by_pattern: Dict[str, set[str]] = {}
    for row in executions:
        if not isinstance(row, Mapping):
            continue
        pattern_id = str(row.get("pattern_id") or "")
        if not pattern_id:
            continue
        chains_by_pattern.setdefault(pattern_id, set())
        if row.get("scan_chain_id") is not None:
            chains_by_pattern[pattern_id].add(str(row["scan_chain_id"]))
        unit = None
        if row.get("unit_id") is not None:
            unit = str(row["unit_id"])
        else:
            rel = row.get("source_log_relpath") or row.get("source_log") or ""
            if rel:
                unit = f"{pattern_id}::{rel}"
        if unit:
            units_by_pattern.setdefault(pattern_id, set()).add(unit)

    # Also collect from embeddings if executions absent for a pattern.
    for row in _as_list(_as_mapping(artifacts.get("embeddings")).get("embeddings")):
        if not isinstance(row, Mapping):
            continue
        pattern_id = str(row.get("pattern_id") or "")
        if not pattern_id:
            continue
        chains_by_pattern.setdefault(pattern_id, set())
        units_by_pattern.setdefault(pattern_id, set())
        rel = row.get("source_log_relpath") or row.get("source_log") or ""
        if rel:
            units_by_pattern[pattern_id].add(f"{pattern_id}::{rel}")

    result: List[Dict[str, Any]] = []
    for pattern_id in sorted(set(chains_by_pattern) | set(units_by_pattern) | set(_pattern_ids_from_sources(artifacts))):
        entry: Dict[str, Any] = {
            "pattern_id": pattern_id,
            "scan_chain_ids": sorted(chains_by_pattern.get(pattern_id) or []),
            "unit_ids": sorted(units_by_pattern.get(pattern_id) or []),
            "provenance": _provenance_for_pattern_index(pattern_id, provenance_index),
        }
        if symbol_map_snapshot is not None:
            # Reuse a single deep-copied symbol_map snapshot for performance.
            entry["symbol_map"] = symbol_map_snapshot
        result.append(entry)
    return result


def build_pattern_characteristics(
    artifacts: Mapping[str, Optional[Mapping[str, Any]]],
    provenance_index: Mapping[str, Dict[str, str]],
) -> List[Dict[str, Any]]:
    executions = _as_list(_as_mapping(artifacts.get("executions")).get("executions"))
    scan_vectors = _as_mapping(artifacts.get("scan_vectors"))
    vector_count = scan_vectors.get("vector_count")

    by_pattern: Dict[str, List[Dict[str, Any]]] = {}
    for row in executions:
        if not isinstance(row, Mapping):
            continue
        pattern_id = str(row.get("pattern_id") or "")
        if not pattern_id:
            continue
        record: Dict[str, Any] = {
            "pattern_id": pattern_id,
        }
        for key in (
            "scan_chain_id",
            "unit_id",
            "source_log",
            "source_log_relpath",
            "run_id",
            "execution_id",
            "toggle_count",
            "toggle_coverage_pct",
            "toggle_density_pct",
            "latest_result",
        ):
            if key in row and row.get(key) is not None:
                record[key] = snapshot(row.get(key))
        by_pattern.setdefault(pattern_id, []).append(record)

    result: List[Dict[str, Any]] = []
    for pattern_id in sorted(by_pattern):
        records = sorted(
            by_pattern[pattern_id],
            key=lambda r: _tie_key(
                r.get("pattern_id"),
                r.get("unit_id"),
                r.get("scan_chain_id"),
                r.get("run_id"),
            ),
        )
        entry: Dict[str, Any] = {
            "pattern_id": pattern_id,
            "executions": records,
            "provenance": _provenance_for_pattern_index(pattern_id, provenance_index),
        }
        if vector_count is not None:
            entry["vector_count"] = vector_count
        result.append(entry)

    # Patterns present only in scan_vectors.
    for row in _as_list(scan_vectors.get("vectors")):
        if not isinstance(row, Mapping):
            continue
        pattern_id = str(row.get("pattern_id") or "")
        if not pattern_id or pattern_id in by_pattern:
            continue
        entry = {
            "pattern_id": pattern_id,
            "executions": [],
            "provenance": _provenance_for_pattern_index(pattern_id, provenance_index),
        }
        if vector_count is not None:
            entry["vector_count"] = vector_count
        result.append(entry)

    return sorted(result, key=lambda item: str(item.get("pattern_id") or ""))


def build_embeddings_section(
    artifacts: Mapping[str, Optional[Mapping[str, Any]]],
) -> Dict[str, Any]:
    embeddings = _as_mapping(artifacts.get("embeddings"))
    if not embeddings:
        return {"available": False, "embeddings": []}

    rows = []
    for row in _as_list(embeddings.get("embeddings")):
        if not isinstance(row, Mapping):
            continue
        rows.append(snapshot(dict(row)))
    rows.sort(
        key=lambda r: _tie_key(
            r.get("pattern_id"),
            r.get("unit_id")
            or (
                f"{r.get('pattern_id')}::{r.get('source_log_relpath') or r.get('source_log') or ''}"
            ),
            r.get("scan_chain_id"),
            r.get("run_id"),
        )
    )
    return {
        "available": True,
        "generated_by": embeddings.get("generated_by"),
        "embedding_strategy": embeddings.get("embedding_strategy"),
        "embedding_version": embeddings.get("embedding_version"),
        "embedding_dimension": embeddings.get("embedding_dimension"),
        "algorithm": embeddings.get("algorithm"),
        "similarity_metric": embeddings.get("similarity_metric"),
        "patterns_embedded": embeddings.get("patterns_embedded"),
        "patterns_skipped": embeddings.get("patterns_skipped"),
        "skipped": snapshot(embeddings.get("skipped") or []),
        "embeddings": rows,
        "source_artifact": SESSION_EMBEDDINGS,
    }


def build_clusters_section(
    artifacts: Mapping[str, Optional[Mapping[str, Any]]],
) -> List[Dict[str, Any]]:
    clustering = _as_mapping(artifacts.get("clustering"))
    clusters = []
    for cluster in _as_list(clustering.get("clusters")):
        if not isinstance(cluster, Mapping):
            continue
        clusters.append(snapshot(dict(cluster)))
    clusters.sort(key=lambda c: str(c.get("cluster_id") or ""))
    return clusters


def build_cluster_statistics(
    artifacts: Mapping[str, Optional[Mapping[str, Any]]],
) -> Dict[str, Any]:
    clustering = _as_mapping(artifacts.get("clustering"))
    if not clustering:
        return {"available": False}
    stats: Dict[str, Any] = {"available": True, "source_artifact": SESSION_CLUSTERING}
    for key in CLUSTER_STAT_KEYS:
        if key in clustering:
            stats[key] = snapshot(clustering.get(key))
    return stats


def build_similarity_matrix(
    artifacts: Mapping[str, Optional[Mapping[str, Any]]],
) -> Dict[str, Any]:
    similarity = _as_mapping(artifacts.get("similarity"))
    if not similarity:
        return {
            "available": False,
            "note": "L1 stores top-N similarity pairs, not a dense N×N matrix.",
            "similarity_pairs": [],
        }

    pairs = []
    for pair in _as_list(similarity.get("similarity_pairs")):
        if isinstance(pair, Mapping):
            pairs.append(snapshot(dict(pair)))
    pairs.sort(
        key=lambda p: (
            -float(p.get("cosine_similarity") or 0.0),
            str(p.get("pattern_a") or ""),
            str(p.get("unit_a") or ""),
            str(p.get("pattern_b") or ""),
            str(p.get("unit_b") or ""),
            int(p.get("rank") or 0),
        )
    )
    return {
        "available": True,
        "note": "L1 stores top-N similarity pairs, not a dense N×N matrix.",
        "generated_by": similarity.get("generated_by"),
        "artifact_version": similarity.get("artifact_version"),
        "embedding_version": similarity.get("embedding_version"),
        "embedding_dimension": similarity.get("embedding_dimension"),
        "session_hash": similarity.get("session_hash"),
        "similarity_metric": similarity.get("similarity_metric"),
        "similarity_scope": similarity.get("similarity_scope"),
        "top_n": similarity.get("top_n"),
        "effective_top_n": similarity.get("effective_top_n"),
        "summary": snapshot(similarity.get("summary") or {}),
        "distribution": snapshot(similarity.get("distribution") or {}),
        "stable_patterns": snapshot(similarity.get("stable_patterns") or []),
        "divergent_patterns": snapshot(similarity.get("divergent_patterns") or []),
        "similarity_pairs": pairs,
        "source_artifact": SESSION_SIMILARITY,
    }


def build_structural_similarity(
    artifacts: Mapping[str, Optional[Mapping[str, Any]]],
    provenance_index: Mapping[str, Dict[str, str]],
) -> List[Dict[str, Any]]:
    """Join-only structural view. No new similarity calculations."""
    clustering = _as_mapping(artifacts.get("clustering"))
    similarity = _as_mapping(artifacts.get("similarity"))
    redundancy = _as_mapping(artifacts.get("redundancy"))

    assignments_by_unit: Dict[str, Dict[str, Any]] = {}
    for row in _as_list(clustering.get("unit_assignments")):
        if not isinstance(row, Mapping):
            continue
        unit_id = str(row.get("unit_id") or "")
        if unit_id:
            assignments_by_unit[unit_id] = dict(row)

    by_pattern: Dict[str, Dict[str, Any]] = {}

    def _ensure(pattern_id: str) -> Dict[str, Any]:
        if pattern_id not in by_pattern:
            by_pattern[pattern_id] = {
                "pattern_id": pattern_id,
                "cluster_assignments": [],
                "embedding_similarities": [],
                "redundancy_candidates": [],
                "provenance": _provenance_for_pattern_index(pattern_id, provenance_index),
            }
        return by_pattern[pattern_id]

    for unit_id, row in sorted(assignments_by_unit.items()):
        pattern_id = str(row.get("pattern_id") or "")
        if not pattern_id:
            continue
        entry = _ensure(pattern_id)
        assignment: Dict[str, Any] = {
            "unit_id": unit_id,
            "cluster_id": row.get("cluster_id"),
            "cluster_match": row.get("cluster_id"),
        }
        if row.get("similarity_to_centroid") is not None:
            assignment["embedding_similarity"] = row.get("similarity_to_centroid")
            assignment["similarity_to_centroid"] = row.get("similarity_to_centroid")
        for key in ("source_log", "source_log_relpath", "run_id", "source_lot"):
            if row.get(key) is not None:
                assignment[key] = row.get(key)
        entry["cluster_assignments"].append(assignment)

    for pair in _as_list(similarity.get("similarity_pairs")):
        if not isinstance(pair, Mapping):
            continue
        for side in ("a", "b"):
            pattern_id = str(pair.get(f"pattern_{side}") or "")
            if not pattern_id:
                continue
            entry = _ensure(pattern_id)
            sim_row = {
                "unit_a": pair.get("unit_a"),
                "unit_b": pair.get("unit_b"),
                "pattern_a": pair.get("pattern_a"),
                "pattern_b": pair.get("pattern_b"),
                "embedding_similarity": pair.get("cosine_similarity"),
                "cosine_similarity": pair.get("cosine_similarity"),
                "rank": pair.get("rank"),
            }
            unit_a = str(pair.get("unit_a") or "")
            unit_b = str(pair.get("unit_b") or "")
            cluster_a = (assignments_by_unit.get(unit_a) or {}).get("cluster_id")
            cluster_b = (assignments_by_unit.get(unit_b) or {}).get("cluster_id")
            if cluster_a is not None and cluster_b is not None:
                sim_row["cluster_match"] = cluster_a == cluster_b
                sim_row["cluster_id_a"] = cluster_a
                sim_row["cluster_id_b"] = cluster_b
            entry["embedding_similarities"].append(sim_row)

    for candidate in _as_list(redundancy.get("candidates")):
        if not isinstance(candidate, Mapping):
            continue
        for side in ("a", "b"):
            pattern_id = str(candidate.get(f"pattern_{side}") or "")
            if not pattern_id:
                continue
            entry = _ensure(pattern_id)
            entry["redundancy_candidates"].append(snapshot(dict(candidate)))

    result = []
    for pattern_id in sorted(by_pattern):
        entry = by_pattern[pattern_id]
        entry["cluster_assignments"].sort(
            key=lambda r: _tie_key(pattern_id, r.get("unit_id"), None, r.get("run_id"))
        )
        entry["embedding_similarities"].sort(
            key=lambda r: (
                -float(r.get("cosine_similarity") or 0.0),
                str(r.get("unit_a") or ""),
                str(r.get("unit_b") or ""),
            )
        )
        entry["redundancy_candidates"].sort(
            key=lambda r: (
                -float(r.get("confidence_score") or 0.0),
                str(r.get("unit_a") or ""),
                str(r.get("unit_b") or ""),
            )
        )
        # Deduplicate redundancy candidates that appear from both sides.
        seen = set()
        unique_candidates = []
        for cand in entry["redundancy_candidates"]:
            key = (
                str(cand.get("unit_a") or ""),
                str(cand.get("unit_b") or ""),
                str(cand.get("cluster_id") or ""),
            )
            if key in seen:
                continue
            seen.add(key)
            unique_candidates.append(cand)
        entry["redundancy_candidates"] = unique_candidates
        result.append(entry)
    return result


def build_pattern_metrics(
    artifacts: Mapping[str, Optional[Mapping[str, Any]]],
    provenance_index: Mapping[str, Dict[str, str]],
) -> List[Dict[str, Any]]:
    correlation = _as_mapping(artifacts.get("correlation"))
    summary = _as_mapping(artifacts.get("summary"))
    redundancy = _as_mapping(artifacts.get("redundancy"))
    by_pattern_chain = _as_mapping(summary.get("by_pattern_chain"))

    by_pattern: Dict[str, Dict[str, Any]] = {}

    def _ensure(pattern_id: str) -> Dict[str, Any]:
        if pattern_id not in by_pattern:
            by_pattern[pattern_id] = {
                "pattern_id": pattern_id,
                "outcomes": [],
                "summary_rollups": [],
                "redundancy": [],
                "provenance": _provenance_for_pattern_index(pattern_id, provenance_index),
            }
        return by_pattern[pattern_id]

    for outcome in _as_list(correlation.get("outcomes")):
        if not isinstance(outcome, Mapping):
            continue
        pattern_id = str(outcome.get("pattern_id") or "")
        if not pattern_id:
            continue
        entry = _ensure(pattern_id)
        row = snapshot(dict(outcome))
        exec_count = row.get("execution_count")
        pass_count = row.get("pass_count")
        fail_count = row.get("fail_count")
        if exec_count and isinstance(exec_count, (int, float)) and exec_count > 0:
            if isinstance(pass_count, (int, float)):
                row["pass_rate"] = float(pass_count) / float(exec_count)
            if isinstance(fail_count, (int, float)):
                row["fail_rate"] = float(fail_count) / float(exec_count)
        entry["outcomes"].append(row)

    for key, rollup in sorted(by_pattern_chain.items()):
        if not isinstance(rollup, Mapping):
            continue
        pattern_id = str(key).split("|", 1)[0]
        if not pattern_id:
            continue
        entry = _ensure(pattern_id)
        entry["summary_rollups"].append(
            {
                "pattern_chain_key": key,
                **snapshot(dict(rollup)),
            }
        )

    for candidate in _as_list(redundancy.get("candidates")):
        if not isinstance(candidate, Mapping):
            continue
        for side in ("a", "b"):
            pattern_id = str(candidate.get(f"pattern_{side}") or "")
            if not pattern_id:
                continue
            entry = _ensure(pattern_id)
            entry["redundancy"].append(snapshot(dict(candidate)))

    result = []
    for pattern_id in sorted(by_pattern):
        entry = by_pattern[pattern_id]
        entry["outcomes"].sort(
            key=lambda r: _tie_key(
                pattern_id,
                None,
                r.get("scan_chain_id"),
                None,
            )
        )
        entry["summary_rollups"].sort(key=lambda r: str(r.get("pattern_chain_key") or ""))
        seen = set()
        unique = []
        for cand in sorted(
            entry["redundancy"],
            key=lambda r: (
                -float(r.get("confidence_score") or 0.0),
                str(r.get("unit_a") or ""),
                str(r.get("unit_b") or ""),
            ),
        ):
            key = (str(cand.get("unit_a") or ""), str(cand.get("unit_b") or ""))
            if key in seen:
                continue
            seen.add(key)
            unique.append(cand)
        entry["redundancy"] = unique
        result.append(entry)
    return result


def build_pattern_rankings(
    artifacts: Mapping[str, Optional[Mapping[str, Any]]],
) -> Dict[str, Any]:
    executions = _as_list(_as_mapping(artifacts.get("executions")).get("executions"))
    similarity = _as_mapping(artifacts.get("similarity"))
    redundancy = _as_mapping(artifacts.get("redundancy"))
    clustering = _as_mapping(artifacts.get("clustering"))

    toggle_rows = []
    for row in executions:
        if not isinstance(row, Mapping):
            continue
        pattern_id = str(row.get("pattern_id") or "")
        if not pattern_id:
            continue
        toggle_rows.append(
            {
                "pattern_id": pattern_id,
                "scan_chain_id": row.get("scan_chain_id"),
                "unit_id": row.get("unit_id"),
                "run_id": row.get("run_id"),
                "toggle_count": row.get("toggle_count"),
                "toggle_density_pct": row.get("toggle_density_pct"),
                "toggle_coverage_pct": row.get("toggle_coverage_pct"),
            }
        )
    toggle_rows.sort(
        key=lambda r: (
            -(float(r["toggle_density_pct"]) if r.get("toggle_density_pct") is not None else -1.0),
            -(float(r["toggle_count"]) if r.get("toggle_count") is not None else -1.0),
            *_tie_key(
                r.get("pattern_id"),
                r.get("unit_id"),
                r.get("scan_chain_id"),
                r.get("run_id"),
            ),
        )
    )
    toggle_rank = []
    for index, row in enumerate(toggle_rows, start=1):
        item = dict(row)
        item["rank"] = index
        toggle_rank.append(item)

    switching_rows = []
    for candidate in _as_list(redundancy.get("candidates")):
        if not isinstance(candidate, Mapping):
            continue
        switching_rows.append(
            {
                "pattern_id": candidate.get("pattern_a"),
                "pattern_a": candidate.get("pattern_a"),
                "pattern_b": candidate.get("pattern_b"),
                "unit_a": candidate.get("unit_a"),
                "unit_b": candidate.get("unit_b"),
                "cluster_id": candidate.get("cluster_id"),
                "confidence_score": candidate.get("confidence_score"),
                "raw_similarity": candidate.get("raw_similarity"),
            }
        )
    switching_rows.sort(
        key=lambda r: (
            -(float(r["confidence_score"]) if r.get("confidence_score") is not None else -1.0),
            -(float(r["raw_similarity"]) if r.get("raw_similarity") is not None else -1.0),
            str(r.get("pattern_a") or ""),
            str(r.get("unit_a") or ""),
            str(r.get("unit_b") or ""),
        )
    )
    switching_rank = []
    for index, row in enumerate(switching_rows, start=1):
        item = dict(row)
        item["rank"] = index
        switching_rank.append(item)

    similarity_rank = []
    stable = _as_list(similarity.get("stable_patterns"))
    if stable:
        ordered = sorted(
            [dict(r) for r in stable if isinstance(r, Mapping)],
            key=lambda r: (
                -(float(r["average_similarity"]) if r.get("average_similarity") is not None else -1.0),
                str(r.get("pattern_id") or ""),
            ),
        )
        for index, row in enumerate(ordered, start=1):
            item = {
                "pattern_id": row.get("pattern_id"),
                "average_similarity": row.get("average_similarity"),
                "rank": index,
            }
            similarity_rank.append(item)
    else:
        # Fall back to centroid closeness from unit assignments.
        assignments = [
            dict(r)
            for r in _as_list(clustering.get("unit_assignments"))
            if isinstance(r, Mapping)
        ]
        assignments.sort(
            key=lambda r: (
                -(
                    float(r["similarity_to_centroid"])
                    if r.get("similarity_to_centroid") is not None
                    else -1.0
                ),
                *_tie_key(
                    r.get("pattern_id"),
                    r.get("unit_id"),
                    None,
                    r.get("run_id"),
                ),
            )
        )
        for index, row in enumerate(assignments, start=1):
            similarity_rank.append(
                {
                    "pattern_id": row.get("pattern_id"),
                    "unit_id": row.get("unit_id"),
                    "cluster_id": row.get("cluster_id"),
                    "similarity_to_centroid": row.get("similarity_to_centroid"),
                    "rank": index,
                }
            )

    return {
        "toggle_rank": toggle_rank,
        "switching_rank": switching_rank,
        "similarity_rank": similarity_rank,
    }


def validate_master_structure(payload: Mapping[str, Any]) -> List[str]:
    """Hand-rolled required-key structural checks (no runtime JSON Schema dependency)."""
    errors: List[str] = []
    for key in MASTER_TOP_LEVEL_KEYS:
        if key not in payload:
            errors.append(f"Missing top-level key: {key}")

    if payload.get("generated_by") != GENERATED_BY:
        errors.append(f"generated_by must be {GENERATED_BY!r}")
    if payload.get("analysis_mode") != ANALYSIS_MODE:
        errors.append(f"analysis_mode must be {ANALYSIS_MODE!r}")
    if "pattern_analytics" in payload:
        errors.append("pattern_analytics is forbidden; use pattern_metrics")

    export_info = payload.get("export_information")
    if not isinstance(export_info, Mapping):
        errors.append("export_information must be an object")
    else:
        for key, expected in (
            ("export_version", EXPORT_VERSION),
            ("export_type", EXPORT_TYPE),
            ("generated_from", ANALYSIS_MODE),
            ("deterministic", True),
        ):
            if export_info.get(key) != expected:
                errors.append(f"export_information.{key} must be {expected!r}")

    return errors


def build_pattern_analysis_master(
    sources: Mapping[str, Any],
    *,
    timestamp_fn: Optional[Callable[[], str]] = None,
) -> Dict[str, Any]:
    """Merge loaded session sources into the canonical master export dict."""
    artifacts = sources.get("artifacts") or {}
    provenance = sources.get("provenance") or {}
    provenance_index = _build_provenance_index(artifacts)
    stamp = (timestamp_fn or utc_timestamp)()

    manifest = _as_mapping(artifacts.get("manifest"))
    analysis_session_id = manifest.get("session_hash")

    master: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_by": GENERATED_BY,
        "analysis_mode": ANALYSIS_MODE,
        "analysis_session_id": analysis_session_id,
        "generated_timestamp": stamp,
        "export_information": build_export_information(),
        "analysis_summary": build_analysis_summary(artifacts),
        "analysis_dataset": build_analysis_dataset(artifacts),
        "analysis_pipeline_versions": build_pipeline_versions(artifacts),
        "source_artifacts": build_source_artifacts(provenance),
        "source_hashes": build_source_hashes(provenance),
        "pattern_metadata": build_pattern_metadata(artifacts, provenance_index),
        "pattern_characteristics": build_pattern_characteristics(artifacts, provenance_index),
        "embeddings": build_embeddings_section(artifacts),
        "clusters": build_clusters_section(artifacts),
        "cluster_statistics": build_cluster_statistics(artifacts),
        "similarity_matrix": build_similarity_matrix(artifacts),
        "structural_similarity": build_structural_similarity(artifacts, provenance_index),
        "pattern_metrics": build_pattern_metrics(artifacts, provenance_index),
        "pattern_rankings": build_pattern_rankings(artifacts),
    }
    return master


def write_master_json(output_dir: str, master: Mapping[str, Any]) -> str:
    path = os.path.join(output_dir, MASTER_FILENAME)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(master, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
    return path
