"""
PA-FR-006 Cluster Exporter — JSON/CSV output generation and pipeline orchestration.
"""
from __future__ import annotations

import csv
import json
import logging
import os
import shutil
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from cluster_dashboard import build_cluster_dashboard_payload, build_export_rollup
from cluster_diagnostics import build_cluster_configuration, build_cluster_diagnostics
from cluster_engine import (
    EMBEDDINGS_FILENAME,
    ClusteringAbortedError,
    ClusteringConfigError,
    ClusteringRunResult,
    build_cluster_quality_metrics,
    load_clustering_config,
    load_embeddings,
    persist_similarity_threshold,
    run_clustering_engine,
)
from cluster_manifest import (
    HASH_METHOD,
    build_manifest_payload,
    compute_canonical_cluster_hash,
)
from cluster_validator import validate_clustering_result

PATTERN_CLUSTERS_JSON = "PA-FR-006_pattern_clusters.json"
CLUSTER_SUMMARY_JSON = "PA-FR-006_cluster_summary.json"
FILE_ROLLUP_JSON = "PA-FR-006_file_rollup.json"
PATTERN_CLUSTERS_CSV = "PA-FR-006_pattern_clusters.csv"
CLUSTER_SUMMARY_CSV = "PA-FR-006_cluster_summary.csv"
FILE_ROLLUP_CSV = "PA-FR-006_file_rollup.csv"
VALIDATION_REPORT_JSON = "PA-FR-006_validation_report.json"
CLUSTER_MANIFEST_JSON = "PA-FR-006_cluster_manifest.json"
LOG_FILENAME = "PA-FR-006_clustering.log"

OUTPUT_FILENAMES = (
    PATTERN_CLUSTERS_JSON,
    CLUSTER_SUMMARY_JSON,
    FILE_ROLLUP_JSON,
    PATTERN_CLUSTERS_CSV,
    CLUSTER_SUMMARY_CSV,
    FILE_ROLLUP_CSV,
    VALIDATION_REPORT_JSON,
    CLUSTER_MANIFEST_JSON,
    LOG_FILENAME,
)


def _write_json(path: str, payload: Dict[str, Any]) -> bytes:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    with open(path, "rb") as handle:
        return handle.read()


def _write_csv(path: str, headers: List[str], rows: List[List[Any]]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def resolve_cluster_version(output_dir: str, config_value: str) -> int:
    history_dir = os.path.join(output_dir, "history")
    existing_versions: List[int] = []
    if os.path.isdir(history_dir):
        for name in os.listdir(history_dir):
            if name.startswith("v") and name[1:].isdigit():
                existing_versions.append(int(name[1:]))
    if config_value != "auto":
        requested = int(config_value)
        if requested in existing_versions:
            return max(existing_versions) + 1
        return requested
    return max(existing_versions, default=0) + 1


def build_export_payloads(
    result: ClusteringRunResult,
    export_rollup: Dict[str, Any],
    cluster_quality_metrics: Dict[str, Dict[str, float]],
) -> Dict[str, Any]:
    pattern_clusters = {
        "generated_by": "PA-FR-006",
        "cluster_version": result.cluster_version,
        "embedding_version": result.embedding_version,
        "similarity_threshold": result.config.similarity_threshold,
        "patterns": [
            {
                "pattern_id": item.pattern_id,
                "cluster_id": item.cluster_id,
                "similarity_to_centroid": item.similarity_to_centroid,
            }
            for item in result.patterns
        ],
    }
    cluster_summary = {
        "generated_by": "PA-FR-006",
        "cluster_version": result.cluster_version,
        "clusters": [
            {
                "cluster_id": cluster.cluster_id,
                "cluster_size": len(cluster.member_ids),
                "representative_pattern": cluster.representative_pattern,
                "centroid_dimension": len(cluster.centroid),
                "average_similarity": cluster.average_intra_similarity,
                "embedding_version": result.embedding_version,
                "cluster_radius": cluster_quality_metrics.get(cluster.cluster_id, {}).get("cluster_radius", 0.0),
                "cluster_compactness": cluster_quality_metrics.get(cluster.cluster_id, {}).get("cluster_compactness", 1.0),
            }
            for cluster in result.clusters
        ],
    }
    return {
        PATTERN_CLUSTERS_JSON: pattern_clusters,
        CLUSTER_SUMMARY_JSON: cluster_summary,
        FILE_ROLLUP_JSON: dict(export_rollup),
    }


def build_csv_rows(
    result: ClusteringRunResult,
    export_rollup: Dict[str, Any],
    cluster_quality_metrics: Dict[str, Dict[str, float]],
) -> Dict[str, Tuple[List[str], List[List[Any]]]]:
    pattern_rows = [
        [item.pattern_id, item.cluster_id, item.similarity_to_centroid]
        for item in result.patterns
    ]
    summary_rows = [
        [
            cluster.cluster_id,
            cluster.representative_pattern,
            len(cluster.member_ids),
            cluster.average_intra_similarity,
            len(cluster.centroid),
            result.embedding_version,
            cluster_quality_metrics.get(cluster.cluster_id, {}).get("cluster_radius", 0.0),
            cluster_quality_metrics.get(cluster.cluster_id, {}).get("cluster_compactness", 1.0),
        ]
        for cluster in result.clusters
    ]
    rollup = export_rollup
    rollup_rows = [[
        rollup.get("algorithm"),
        rollup.get("similarity_threshold"),
        rollup.get("total_clusters"),
        rollup.get("largest_cluster"),
        rollup.get("singleton_clusters"),
        rollup.get("silhouette_score"),
    ]]
    return {
        PATTERN_CLUSTERS_CSV: (
            ["pattern_id", "cluster_id", "similarity_to_centroid"],
            pattern_rows,
        ),
        CLUSTER_SUMMARY_CSV: (
            [
                "cluster_id",
                "representative_pattern",
                "cluster_size",
                "average_similarity",
                "centroid_dimension",
                "embedding_version",
                "cluster_radius",
                "cluster_compactness",
            ],
            summary_rows,
        ),
        FILE_ROLLUP_CSV: (
            ["algorithm", "threshold", "total_clusters", "largest_cluster", "singleton_clusters", "silhouette_score"],
            rollup_rows,
        ),
    }


def write_outputs_to_directory(
    target_dir: str,
    json_payloads: Dict[str, Dict[str, Any]],
    csv_payloads: Dict[str, Tuple[List[str], List[List[Any]]]],
    validation_report: Dict[str, Any],
    manifest_payload: Dict[str, Any],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Tuple[List[str], List[List[Any]]]]]:
    os.makedirs(target_dir, exist_ok=True)

    for filename, payload in json_payloads.items():
        _write_json(os.path.join(target_dir, filename), payload)

    for filename, (headers, rows) in csv_payloads.items():
        _write_csv(os.path.join(target_dir, filename), headers, rows)

    _write_json(os.path.join(target_dir, VALIDATION_REPORT_JSON), validation_report)
    _write_json(os.path.join(target_dir, CLUSTER_MANIFEST_JSON), manifest_payload)
    return json_payloads, csv_payloads


def _configure_logger(log_path: str) -> logging.Logger:
    logger = logging.getLogger("pa_fr_006_clustering")
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(levelname)s  %(message)s"))
    logger.addHandler(handler)
    return logger


def get_clustering_configuration(
    workspace_dir: str,
    output_dir: str | None = None,
) -> Dict[str, Any]:
    """Return current clustering settings and whether PA-FR-005 embeddings are available."""
    workspace = workspace_dir or os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(workspace, "config", "clustering.yaml")
    config = load_clustering_config(config_path)
    resolved_output = output_dir or os.path.join(workspace, "output")
    embeddings_path = os.path.join(resolved_output, EMBEDDINGS_FILENAME)
    return {
        "algorithm": config.algorithm,
        "linkage": config.linkage,
        "similarity_metric": config.similarity_metric,
        "similarity_threshold": config.similarity_threshold,
        "singleton_clusters": config.singleton_clusters,
        "cluster_version": config.cluster_version,
        "embeddings_available": os.path.exists(embeddings_path),
        "config_path": config_path,
    }


def run_pattern_clustering(
    output_dir: str,
    workspace_dir: str | None = None,
) -> Dict[str, Any]:
    workspace = workspace_dir or os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(workspace, "config", "clustering.yaml")
    embeddings_path = os.path.join(output_dir, EMBEDDINGS_FILENAME)

    config = load_clustering_config(config_path)
    _, records = load_embeddings(embeddings_path)
    cluster_version = resolve_cluster_version(output_dir, config.cluster_version)
    generated_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    os.makedirs(output_dir, exist_ok=True)
    log_path = os.path.join(output_dir, LOG_FILENAME)
    logger = _configure_logger(log_path)

    logger.info(f"Loaded {len(records)} embeddings.")
    embedding_version = records[0].feature_version if records else "1.0"
    logger.info(f"Embedding version verified: {embedding_version} (consistent across all patterns)")
    logger.info(f"Similarity Threshold = {config.similarity_threshold}")

    result = run_clustering_engine(
        records,
        config,
        embedding_version=embedding_version,
        cluster_version=cluster_version,
    )

    embeddings_map = {record.pattern_id: record.embedding for record in records}
    cluster_quality_metrics = build_cluster_quality_metrics(result.clusters, embeddings_map)
    export_rollup = build_export_rollup(result)
    cluster_sizes = [len(cluster.member_ids) for cluster in result.clusters]
    configuration = build_cluster_configuration(
        {
            "algorithm": config.algorithm,
            "linkage": config.linkage,
            "similarity_metric": config.similarity_metric,
            "similarity_threshold": config.similarity_threshold,
        }
    )

    logger.info("Agglomerative Clustering Complete.")
    logger.info(f"Generated {result.file_rollup['total_clusters']} clusters.")
    logger.info(f"Largest Cluster = {result.file_rollup['largest_cluster']} patterns.")
    logger.info(f"Singleton Clusters = {result.file_rollup['singleton_clusters']}")
    if export_rollup.get("total_clusters", 0) == 1:
        logger.info("Silhouette Score = Not Applicable")
    else:
        logger.info(f"Silhouette Score = {export_rollup.get('silhouette_score')}")

    validation_report = validate_clustering_result(
        result,
        config,
        cluster_quality_metrics=cluster_quality_metrics,
        export_rollup=export_rollup,
    )
    passed = validation_report.get("passed", 0)
    total = validation_report.get("total_checks", 0)
    logger.info(
        f"Validation {'Passed' if validation_report['validation_status'] == 'PASS' else validation_report['validation_status']}. "
        f"({passed}/{total} rules)"
    )

    json_payloads = build_export_payloads(result, export_rollup, cluster_quality_metrics)
    csv_payloads = build_csv_rows(result, export_rollup, cluster_quality_metrics)

    history_dir = os.path.join(output_dir, "history", f"v{cluster_version}")
    pattern_clusters_payload = json_payloads[PATTERN_CLUSTERS_JSON]
    manifest_stub = build_manifest_payload(result, canonical_cluster_hash="", generated_timestamp=generated_timestamp)
    manifest_stub.pop("canonical_cluster_hash", None)
    canonical_cluster_hash = compute_canonical_cluster_hash(manifest_stub, pattern_clusters_payload)
    manifest_payload = build_manifest_payload(
        result,
        canonical_cluster_hash,
        generated_timestamp=generated_timestamp,
    )

    write_outputs_to_directory(
        history_dir,
        json_payloads,
        csv_payloads,
        validation_report,
        manifest_payload,
    )

    for filename in OUTPUT_FILENAMES:
        if filename == LOG_FILENAME:
            continue
        source = os.path.join(history_dir, filename)
        if os.path.exists(source):
            shutil.copy2(source, os.path.join(output_dir, filename))

    shutil.copy2(log_path, os.path.join(history_dir, LOG_FILENAME))
    logger.info(f"canonical_cluster_hash = {canonical_cluster_hash[:8]}...")
    logger.info(f"hash_method = {HASH_METHOD}")
    logger.info("Export Complete.")

    diagnostics = build_cluster_diagnostics(
        validation_report,
        canonical_cluster_hash,
        export_rollup,
        cluster_quality_metrics,
        cluster_sizes,
        configuration,
    )
    dashboard = build_cluster_dashboard_payload(
        result,
        diagnostics,
        canonical_cluster_hash,
        cluster_quality_metrics,
        export_rollup,
    )

    return {
        **dashboard,
        "output_files": {
            filename: os.path.join(output_dir, filename)
            for filename in OUTPUT_FILENAMES
            if filename != LOG_FILENAME
        },
        "history_directory": history_dir,
        "validation_report": validation_report,
        "manifest": manifest_payload,
    }
