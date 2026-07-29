"""Main FA-FR-008 wafer-level failure analytics engine."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from adapters.schema import TestRecord
from adapters.yaml_config import load_adapter_configs
from backend.wafer_analysis.cluster_detection import detect_wafer_clusters
from backend.wafer_analysis.edge_center_analysis import (
    analyze_edge_center,
    detect_radial_defects,
)
from backend.wafer_analysis.hotspot_detection import (
    detect_ai_wafer_anomalies,
    detect_wafer_hotspots,
)
from backend.wafer_analysis.radial_analysis import analyze_radial_distribution
from backend.wafer_analysis.wafer_map_generator import (
    build_engineering_dashboard,
    generate_wafer_maps,
)
from backend.wafer_analysis.wafer_statistics import (
    aggregate_wafer_data,
    compute_bin_distribution,
    compute_failure_density_per_wafer,
)
from die_wafer_analytics import analyze_wafer_level_failures
from failure_rate_engine import compute_failure_rates
from ingestor import DieLog

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "wafer_analysis.yaml"


class WaferAnalysisEngine:
    """
    Wafer-level spatial analytics pipeline:
    aggregation → coordinates → stats → clusters → hotspots → maps → dashboard
    """

    def __init__(self, *, config_path: Path | str | None = None) -> None:
        raw = load_adapter_configs(Path(config_path) if config_path else DEFAULT_CONFIG)
        self.grid_resolution = int(raw.get("grid_resolution", 25))
        self.hotspot_threshold = float(raw.get("hotspot_density_threshold", 0.15))
        self.hotspot_min_dies = int(raw.get("hotspot_min_dies", 3))
        self.dbscan_eps = float(raw.get("dbscan_eps", 2.5))
        self.dbscan_min_samples = int(raw.get("dbscan_min_samples", 3))
        self.edge_radius_ratio = float(raw.get("edge_radius_ratio", 0.67))
        self.center_radius_ratio = float(raw.get("center_radius_ratio", 0.34))
        self.radial_bins = int(raw.get("radial_bins", 8))
        self.anomaly_contamination = float(raw.get("anomaly_contamination", 0.05))
        self.coordinate_system = str(raw.get("coordinate_system", "die_xy"))

    def analyze(
        self,
        *,
        die_logs: list[DieLog],
        test_records: list[TestRecord] | None = None,
        upload_id: str | None = None,
    ) -> dict[str, Any]:
        start = time.perf_counter()

        failure_rates = compute_failure_rates(die_logs, test_records=test_records)
        legacy = analyze_wafer_level_failures(
            die_logs,
            test_records=test_records,
            failure_rates_engine=failure_rates,
        )

        spatial_map = legacy.get("spatial_map", [])
        wafer_stats = legacy.get("dashboard_feed", [])

        aggregation = aggregate_wafer_data(spatial_map, wafer_stats)
        density_by_wafer = compute_failure_density_per_wafer(
            spatial_map,
            grid_resolution=self.grid_resolution,
        )
        bin_dist = compute_bin_distribution(wafer_stats)
        edge_center = analyze_edge_center(
            spatial_map,
            edge_radius_ratio=self.edge_radius_ratio,
            center_radius_ratio=self.center_radius_ratio,
        )
        radial = analyze_radial_distribution(
            spatial_map,
            radial_bins=self.radial_bins,
        )
        radial_defects = detect_radial_defects(edge_center)

        cluster_report = detect_wafer_clusters(
            spatial_map,
            eps=self.dbscan_eps,
            min_samples=self.dbscan_min_samples,
        )

        hotspot_start = time.perf_counter()
        hotspot_report = detect_wafer_hotspots(
            density_by_wafer,
            threshold=self.hotspot_threshold,
            min_dies=self.hotspot_min_dies,
        )
        anomalies = detect_ai_wafer_anomalies(
            spatial_map,
            wafer_stats,
            contamination=self.anomaly_contamination,
        )
        hotspot_ms = round((time.perf_counter() - hotspot_start) * 1000, 2)

        map_start = time.perf_counter()
        wafer_maps = generate_wafer_maps(
            spatial_map,
            density_by_wafer,
            hotspots=hotspot_report,
        )
        map_ms = round((time.perf_counter() - map_start) * 1000, 2)

        dashboard = build_engineering_dashboard(
            aggregation=aggregation,
            edge_center=edge_center,
            radial=radial,
            hotspots=hotspot_report,
            clusters=cluster_report,
            bin_dist=bin_dist,
            anomalies=anomalies,
            legacy_alerts=legacy.get("alerts", []),
        )

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "requirement": "FA-FR-008",
            "upload_id": upload_id,
            "processing_ms": elapsed_ms,
            "heatmap_ms": map_ms,
            "hotspot_ms": hotspot_ms,
            "meets_performance_target": elapsed_ms < 10000 and map_ms < 5000,
            "coordinate_system": self.coordinate_system,
            "detection_pipeline": [
                "wafer_data_aggregation",
                "coordinate_mapping",
                "spatial_statistics",
                "cluster_detection",
                "hotspot_detection",
                "wafer_map_generation",
                "engineering_dashboard",
            ],
            "total_wafers": legacy.get("total_wafers", 0),
            "outlier_wafer_count": legacy.get("outlier_wafer_count", 0),
            "wafer_statistics": aggregation.get("wafer_statistics", []),
            "yield_distribution": aggregation.get("yield_distribution", []),
            "overall_yield_pct": aggregation.get("overall_yield_pct", 100.0),
            "failure_density": density_by_wafer,
            "bin_distribution": bin_dist,
            "pass_fail_distribution": [
                w.get("pass_fail_distribution", {}) for w in aggregation.get("wafer_statistics", [])
            ],
            "edge_center_analysis": edge_center,
            "radial_failure_analysis": radial,
            "radial_defects": radial_defects,
            "hotspot_analysis": hotspot_report,
            "ai_anomaly_analysis": anomalies,
            "cluster_report": cluster_report,
            "wafer_heatmap": wafer_maps,
            "engineering_dashboard": dashboard,
            "legacy_report": {
                "wafer_ranking": legacy.get("wafer_ranking", []),
                "lot_sequence_trends": legacy.get("lot_sequence_trends", []),
                "spatial_map": spatial_map,
                "alerts": legacy.get("alerts", []),
            },
        }
