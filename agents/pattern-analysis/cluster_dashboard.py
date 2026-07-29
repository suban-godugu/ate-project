"""
PA-FR-006 Cluster Dashboard — additive API payload for Phase 6 UI.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from cluster_diagnostics import build_cluster_configuration, silhouette_band
from cluster_engine import ClusteringRunResult


def compactness_quality_label(compactness: float) -> str:
    if compactness >= 0.99:
        return "Excellent"
    if compactness >= 0.97:
        return "Very Good"
    if compactness >= 0.95:
        return "Good"
    if compactness >= 0.90:
        return "Moderate"
    return "Weak"


def build_export_rollup(result: ClusteringRunResult) -> Dict[str, Any]:
    rollup = dict(result.file_rollup)
    if rollup.get("total_clusters", 0) == 1:
        rollup["silhouette_score"] = None
        rollup["silhouette_status"] = "Not Applicable"
    else:
        rollup["silhouette_status"] = "Computed"
    return rollup


def build_threshold_banner_text(threshold: float) -> str:
    return (
        f"All patterns satisfied the current similarity threshold ({threshold:.2f}). "
        f"Increase the threshold (for example 0.98–0.995) to generate finer-grained clusters."
    )


def build_cluster_dashboard_payload(
    result: ClusteringRunResult,
    diagnostics: Dict[str, Any],
    canonical_cluster_hash: str,
    cluster_quality_metrics: Dict[str, Dict[str, float]],
    export_rollup: Dict[str, Any],
) -> Dict[str, Any]:
    rollup = export_rollup
    total_clusters = int(rollup.get("total_clusters", 0))
    silhouette_score: Optional[float] = rollup.get("silhouette_score")
    configuration = build_cluster_configuration(
        {
            "algorithm": rollup.get("algorithm"),
            "linkage": rollup.get("linkage"),
            "similarity_metric": rollup.get("similarity_metric"),
            "similarity_threshold": rollup.get("similarity_threshold"),
        }
    )

    summary_cards = {
        "patterns_clustered": rollup.get("total_patterns", 0),
        "total_clusters": total_clusters,
        "largest_cluster": rollup.get("largest_cluster", 0),
        "singleton_clusters": rollup.get("singleton_clusters", 0),
        "average_cluster_size": rollup.get("average_cluster_size", 0),
        "similarity_threshold": rollup.get("similarity_threshold", 0),
        "algorithm": rollup.get("algorithm", "Agglomerative"),
        "cluster_version": rollup.get("cluster_version", 1),
        "silhouette_score": silhouette_score,
        "silhouette_status": rollup.get("silhouette_status", "Computed"),
        "silhouette_band": silhouette_band(silhouette_score if total_clusters > 1 else None),
        "embedding_version": rollup.get("embedding_version", "1.0"),
        "threshold_configurable": True,
        "threshold_banner": build_threshold_banner_text(float(rollup.get("similarity_threshold", 0.90)))
        if total_clusters == 1
        else None,
    }

    cluster_summary_records: List[Dict[str, Any]] = []
    for cluster in result.clusters:
        quality = cluster_quality_metrics.get(cluster.cluster_id, {})
        compactness = quality.get("cluster_compactness", 0.0)
        cluster_summary_records.append(
            {
                "cluster_id": cluster.cluster_id,
                "representative_pattern": cluster.representative_pattern,
                "cluster_size": len(cluster.member_ids),
                "average_similarity": cluster.average_intra_similarity,
                "centroid_dimension": len(cluster.centroid),
                "embedding_version": result.embedding_version,
                "cluster_radius": quality.get("cluster_radius", 0.0),
                "cluster_compactness": compactness,
                "quality_badge": compactness_quality_label(compactness),
            }
        )

    pattern_assignment_records: List[Dict[str, Any]] = [
        {
            "pattern_id": item.pattern_id,
            "cluster_id": item.cluster_id,
            "similarity_to_centroid": item.similarity_to_centroid,
        }
        for item in result.patterns
    ]

    return {
        "generated_by": "PA-FR-006",
        "cluster_version": result.cluster_version,
        "summary": summary_cards,
        "cluster_summary": cluster_summary_records,
        "pattern_assignments": pattern_assignment_records,
        "diagnostics": diagnostics,
        "configuration": configuration,
        "canonical_cluster_hash": canonical_cluster_hash,
        "file_rollup": rollup,
    }
