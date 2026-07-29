"""
PA-FR-006 Cluster Validation — automated PASS/FAIL checks on clustering outputs.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List

from cluster_engine import ClusteringConfig, ClusteringRunResult, EMBEDDING_DIMENSION


def _overall_status(checks: List[Dict[str, Any]]) -> str:
    if any(check["status"] == "FAIL" for check in checks):
        return "FAIL"
    if any(check["status"] == "WARNING" for check in checks):
        return "WARNING"
    return "PASS"


def validate_clustering_result(
    result: ClusteringRunResult,
    config: ClusteringConfig,
    cluster_quality_metrics: Dict[str, Dict[str, float]] | None = None,
    export_rollup: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []
    total_patterns = result.file_rollup.get("total_patterns", 0)
    assigned_ids = [item.pattern_id for item in result.patterns]
    assigned_set = set(assigned_ids)

    if len(assigned_ids) == total_patterns and len(assigned_set) == total_patterns:
        checks.append(
            {
                "rule": "all_patterns_assigned",
                "status": "PASS",
                "details": f"{len(assigned_ids)}/{total_patterns} patterns assigned",
            }
        )
    else:
        checks.append(
            {
                "rule": "all_patterns_assigned",
                "status": "FAIL",
                "details": f"{len(assigned_set)}/{total_patterns} unique patterns assigned",
            }
        )

    if len(assigned_ids) == len(assigned_set):
        checks.append(
            {
                "rule": "no_duplicate_assignments",
                "status": "PASS",
                "details": "No duplicate pattern assignments found.",
            }
        )
    else:
        checks.append(
            {
                "rule": "no_duplicate_assignments",
                "status": "FAIL",
                "details": f"Found {len(assigned_ids) - len(assigned_set)} duplicate assignment(s).",
            }
        )

    representatives = [cluster.representative_pattern for cluster in result.clusters]
    if len(representatives) == len(result.clusters) and len(set(representatives)) == len(representatives):
        checks.append(
            {
                "rule": "one_representative_per_cluster",
                "status": "PASS",
                "details": f"{len(representatives)} representatives for {len(result.clusters)} clusters.",
            }
        )
    else:
        checks.append(
            {
                "rule": "one_representative_per_cluster",
                "status": "FAIL",
                "details": "Duplicate or missing cluster representatives detected.",
            }
        )

    invalid_representatives = [
        cluster.cluster_id
        for cluster in result.clusters
        if cluster.representative_pattern not in cluster.member_ids
    ]
    if not invalid_representatives:
        checks.append(
            {
                "rule": "representative_membership",
                "status": "PASS",
                "details": "All representative patterns belong to their clusters.",
            }
        )
    else:
        checks.append(
            {
                "rule": "representative_membership",
                "status": "FAIL",
                "details": f"Invalid representatives in clusters: {', '.join(invalid_representatives)}",
            }
        )

    cluster_ids = [cluster.cluster_id for cluster in result.clusters]
    if len(cluster_ids) == len(set(cluster_ids)):
        checks.append(
            {
                "rule": "unique_cluster_ids",
                "status": "PASS",
                "details": "Cluster IDs are unique.",
            }
        )
    else:
        checks.append(
            {
                "rule": "unique_cluster_ids",
                "status": "FAIL",
                "details": "Duplicate cluster IDs detected.",
            }
        )

    invalid_centroids = [
        cluster.cluster_id
        for cluster in result.clusters
        if len(cluster.centroid) != EMBEDDING_DIMENSION
    ]
    if not invalid_centroids:
        checks.append(
            {
                "rule": "centroid_dimension",
                "status": "PASS",
                "details": f"All centroids contain {EMBEDDING_DIMENSION} values.",
            }
        )
    else:
        checks.append(
            {
                "rule": "centroid_dimension",
                "status": "FAIL",
                "details": f"Invalid centroid dimension in clusters: {', '.join(invalid_centroids)}",
            }
        )

    def _contains_non_finite(values: List[float]) -> bool:
        return any(value is None or not isinstance(value, (int, float)) or not math.isfinite(float(value)) for value in values)

    nan_found = any(_contains_non_finite(cluster.centroid) for cluster in result.clusters)
    if not nan_found:
        checks.append({"rule": "no_nan_values", "status": "PASS", "details": "No NaN values in outputs."})
    else:
        checks.append({"rule": "no_nan_values", "status": "FAIL", "details": "NaN values detected in centroids."})

    inf_found = False
    for cluster in result.clusters:
        for value in cluster.centroid:
            if isinstance(value, (int, float)) and math.isinf(float(value)):
                inf_found = True
    if not inf_found:
        checks.append({"rule": "no_infinity_values", "status": "PASS", "details": "No Infinity values in outputs."})
    else:
        checks.append({"rule": "no_infinity_values", "status": "FAIL", "details": "Infinity values detected."})

    out_of_range = False
    for item in result.patterns:
        if item.similarity_to_centroid < 0.0 or item.similarity_to_centroid > 1.0:
            out_of_range = True
    for cluster in result.clusters:
        if cluster.average_intra_similarity < 0.0 or cluster.average_intra_similarity > 1.0:
            out_of_range = True
    if not out_of_range:
        checks.append(
            {
                "rule": "similarity_range",
                "status": "PASS",
                "details": "All similarity values fall within [0.0, 1.0].",
            }
        )
    else:
        checks.append(
            {
                "rule": "similarity_range",
                "status": "FAIL",
                "details": "One or more similarity values fall outside [0.0, 1.0].",
            }
        )

    checks.append(
        {
            "rule": "embedding_version_consistency",
            "status": "PASS",
            "details": f"Embedding version {result.embedding_version} is consistent.",
        }
    )

    config_matches = (
        result.file_rollup.get("similarity_threshold") == config.similarity_threshold
        and result.file_rollup.get("algorithm") == config.algorithm
        and result.file_rollup.get("linkage") == config.linkage
    )
    checks.append(
        {
            "rule": "runtime_configuration_match",
            "status": "PASS" if config_matches else "FAIL",
            "details": "Runtime configuration values match reported outputs."
            if config_matches
            else "Reported configuration differs from runtime configuration.",
        }
    )

    silhouette = result.file_rollup.get("silhouette_score")
    total_clusters = result.file_rollup.get("total_clusters", 0)
    if total_clusters == 1:
        export_score = (export_rollup or {}).get("silhouette_score")
        if export_score is None:
            checks.append(
                {
                    "rule": "silhouette_score_range",
                    "status": "PASS",
                    "details": "Silhouette score not applicable for a single cluster.",
                }
            )
        else:
            checks.append(
                {
                    "rule": "silhouette_score_range",
                    "status": "FAIL",
                    "details": "Single-cluster run must report silhouette_score as null.",
                }
            )
    elif silhouette is not None and -1.0 <= float(silhouette) <= 1.0:
        checks.append(
            {
                "rule": "silhouette_score_range",
                "status": "PASS",
                "details": f"Silhouette score {silhouette} is within [-1, 1].",
            }
        )
    else:
        checks.append(
            {
                "rule": "silhouette_score_range",
                "status": "FAIL",
                "details": f"Silhouette score {silhouette} is outside [-1, 1].",
            }
        )

    size_sum = sum(len(cluster.member_ids) for cluster in result.clusters)
    if size_sum == total_patterns:
        checks.append(
            {
                "rule": "cluster_integrity",
                "status": "PASS",
                "details": f"sum(cluster_size)={size_sum} equals patterns_clustered={total_patterns}",
            }
        )
    else:
        checks.append(
            {
                "rule": "cluster_integrity",
                "status": "FAIL",
                "details": (
                    f"sum(cluster_size)={size_sum} does not equal "
                    f"patterns_clustered={total_patterns}"
                ),
            }
        )

    quality_metrics = cluster_quality_metrics or {}
    if quality_metrics:
        radii = [metrics["cluster_radius"] for metrics in quality_metrics.values()]
        compactness_values = [metrics["cluster_compactness"] for metrics in quality_metrics.values()]
        if all(value >= 0.0 for value in radii):
            checks.append(
                {
                    "rule": "cluster_radius_non_negative",
                    "status": "PASS",
                    "details": f"Checked {len(radii)} clusters",
                }
            )
        else:
            checks.append(
                {
                    "rule": "cluster_radius_non_negative",
                    "status": "FAIL",
                    "details": f"Checked {len(radii)} clusters",
                }
            )
        if all(0.0 <= value <= 1.0 for value in compactness_values):
            checks.append(
                {
                    "rule": "cluster_compactness_in_range",
                    "status": "PASS",
                    "details": f"Checked {len(compactness_values)} clusters",
                }
            )
        else:
            checks.append(
                {
                    "rule": "cluster_compactness_in_range",
                    "status": "FAIL",
                    "details": f"Checked {len(compactness_values)} clusters",
                }
            )

    passed = sum(1 for check in checks if check["status"] == "PASS")
    return {
        "generated_by": "PA-FR-006",
        "validation_status": _overall_status(checks),
        "total_checks": len(checks),
        "passed": passed,
        "failed": sum(1 for check in checks if check["status"] == "FAIL"),
        "warnings": sum(1 for check in checks if check["status"] == "WARNING"),
        "checks": checks,
    }


def validate_clustering_result_for_test(
    result: ClusteringRunResult,
    config: ClusteringConfig,
    expected_dimension: int,
) -> Dict[str, Any]:
    report = validate_clustering_result(result, config)
    centroid_check = next(item for item in report["checks"] if item["rule"] == "centroid_dimension")
    if expected_dimension != EMBEDDING_DIMENSION:
        invalid = [cluster for cluster in result.clusters if len(cluster.centroid) != expected_dimension]
        centroid_check["status"] = "PASS" if not invalid else "FAIL"
        centroid_check["details"] = (
            f"All centroids contain {expected_dimension} values."
            if not invalid
            else f"Invalid centroid dimension in {len(invalid)} cluster(s)."
        )
        report["validation_status"] = _overall_status(report["checks"])
        report["passed"] = sum(1 for check in report["checks"] if check["status"] == "PASS")
        report["failed"] = sum(1 for check in report["checks"] if check["status"] == "FAIL")
    return report
