"""
PA-FR-006 Cluster Diagnostics — dashboard-facing diagnostics derived from validation output.
"""
from __future__ import annotations

import statistics
from typing import Any, Dict, List, Optional


def silhouette_band(score: Optional[float]) -> str:
    if score is None:
        return "Single Cluster"
    if score > 0.8:
        return "Excellent"
    if score >= 0.6:
        return "Good"
    if score >= 0.4:
        return "Acceptable"
    return "Poor"


def _median_value(values: List[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return float(ordered[mid])
    return round((ordered[mid - 1] + ordered[mid]) / 2.0, 2)


def build_cluster_statistics(
    file_rollup: Dict[str, Any],
    cluster_quality_metrics: Dict[str, Dict[str, float]],
    cluster_sizes: List[int],
) -> Dict[str, Any]:
    radii = [metrics["cluster_radius"] for metrics in cluster_quality_metrics.values()]
    compactness_values = [metrics["cluster_compactness"] for metrics in cluster_quality_metrics.values()]
    singleton_count = int(file_rollup.get("singleton_clusters", 0))
    total_clusters = int(file_rollup.get("total_clusters", 0))

    return {
        "largest_cluster": file_rollup.get("largest_cluster", 0),
        "smallest_cluster": file_rollup.get("smallest_cluster", 0),
        "average_cluster_size": file_rollup.get("average_cluster_size", 0),
        "median_cluster_size": _median_value([float(size) for size in cluster_sizes]),
        "largest_radius": max(radii) if radii else 0.0,
        "smallest_radius": min(radii) if radii else 0.0,
        "average_radius": round(statistics.mean(radii), 8) if radii else 0.0,
        "average_compactness": round(statistics.mean(compactness_values), 8) if compactness_values else 0.0,
        "singleton_count": singleton_count,
        "multi_member_count": max(total_clusters - singleton_count, 0),
    }


def build_cluster_configuration(result_config: Dict[str, Any]) -> Dict[str, Any]:
    similarity_metric = result_config.get("similarity_metric", "Cosine")
    metric_display = "Cosine Similarity"
    if str(similarity_metric).lower() != "cosine":
        metric_display = str(similarity_metric).replace("_", " ").title()
    return {
        "algorithm": result_config.get("algorithm", "Agglomerative"),
        "linkage": result_config.get("linkage", "Average"),
        "similarity_metric": metric_display,
        "threshold": result_config.get("similarity_threshold", 0.90),
    }


def build_cluster_diagnostics(
    validation_report: Dict[str, Any],
    canonical_cluster_hash: str,
    file_rollup: Dict[str, Any],
    cluster_quality_metrics: Dict[str, Dict[str, float]],
    cluster_sizes: List[int],
    configuration: Dict[str, Any],
) -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = validation_report.get("checks", [])
    diagnostics_checks = [
        {
            "rule": check.get("rule", ""),
            "status": check.get("status", "FAIL"),
            "message": check.get("details", ""),
        }
        for check in checks
    ]
    export_score = file_rollup.get("silhouette_score")
    silhouette_status = file_rollup.get("silhouette_status", "Computed")
    statistics_summary = build_cluster_statistics(file_rollup, cluster_quality_metrics, cluster_sizes)

    return {
        "validation_status": validation_report.get("validation_status", "FAIL"),
        "total_checks": validation_report.get("total_checks", len(checks)),
        "passed": validation_report.get("passed", 0),
        "warnings": validation_report.get("warnings", 0),
        "failed": validation_report.get("failed", 0),
        "canonical_cluster_hash": canonical_cluster_hash,
        "canonical_cluster_hash_display": f"{canonical_cluster_hash[:8]}..." if canonical_cluster_hash else "",
        "hash_method": "Canonical SHA-256",
        "silhouette_score": export_score,
        "silhouette_status": silhouette_status,
        "silhouette_band": silhouette_band(export_score if file_rollup.get("total_clusters", 0) > 1 else None),
        "configuration": configuration,
        "statistics": statistics_summary,
        "checks": diagnostics_checks,
    }
