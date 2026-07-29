"""Main FA-FR-007 die-level failure analytics engine."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from adapters.schema import TestRecord
from adapters.yaml_config import load_adapter_configs
from backend.die_analysis.clustering import cluster_die_failures
from backend.die_analysis.heatmap_generator import (
    build_engineering_dashboard,
    generate_die_heatmap,
)
from backend.die_analysis.hotspot_detection import detect_ai_hotspots, detect_hotspots
from backend.die_analysis.spatial_statistics import (
    compute_failure_density,
    map_coordinates,
    neighbor_analysis,
    pattern_density_by_zone,
    yield_distribution,
)
from die_wafer_analytics import analyze_die_level_failures
from ingestor import DieLog

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "die_analysis.yaml"


class DieAnalysisEngine:
    """
    Die-level spatial analytics pipeline:
    coordinates → spatial stats → hotspots → clusters → heatmap → dashboard
    """

    def __init__(self, *, config_path: Path | str | None = None) -> None:
        raw = load_adapter_configs(Path(config_path) if config_path else DEFAULT_CONFIG)
        self.hotspot_threshold = float(raw.get("hotspot_density_threshold", 0.15))
        self.hotspot_min_dies = int(raw.get("hotspot_min_dies", 3))
        self.dbscan_eps = float(raw.get("dbscan_eps", 2.5))
        self.dbscan_min_samples = int(raw.get("dbscan_min_samples", 3))
        self.grid_resolution = int(raw.get("grid_resolution", 20))
        self.anomaly_contamination = float(raw.get("anomaly_contamination", 0.05))

    def analyze(
        self,
        *,
        die_logs: list[DieLog],
        test_records: list[TestRecord] | None = None,
        upload_id: str | None = None,
        recurring_failures: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        start = time.perf_counter()

        legacy = analyze_die_level_failures(
            die_logs,
            test_records=test_records,
            recurring_failures=recurring_failures,
        )
        die_profiles = legacy.get("dashboard_feed", [])
        die_points = _to_die_points(die_profiles, legacy.get("spatial_ai_handoff", []))

        coordinate_map = map_coordinates(die_points)
        density_report = compute_failure_density(
            die_points,
            grid_resolution=self.grid_resolution,
        )
        neighbor_report = neighbor_analysis(die_points)
        yield_dist = yield_distribution(die_profiles)
        pattern_density = pattern_density_by_zone(die_profiles, coordinate_map)

        hotspot_start = time.perf_counter()
        hotspot_report = detect_hotspots(
            density_report,
            threshold=self.hotspot_threshold,
            min_dies=self.hotspot_min_dies,
        )
        ai_hotspots = detect_ai_hotspots(
            die_points,
            contamination=self.anomaly_contamination,
        )
        hotspot_ms = round((time.perf_counter() - hotspot_start) * 1000, 2)

        cluster_report = cluster_die_failures(
            die_points,
            eps=self.dbscan_eps,
            min_samples=self.dbscan_min_samples,
        )

        heatmap_start = time.perf_counter()
        heatmap = generate_die_heatmap(
            coordinate_map,
            density_report,
            hotspots=hotspot_report.get("hotspots", []),
        )
        heatmap_ms = round((time.perf_counter() - heatmap_start) * 1000, 2)

        dashboard = build_engineering_dashboard(
            heatmap=heatmap,
            hotspots=hotspot_report,
            clusters=cluster_report,
            yield_dist=yield_dist,
            spatial_stats=coordinate_map,
            neighbor_report=neighbor_report,
        )

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "requirement": "FA-FR-007",
            "upload_id": upload_id,
            "processing_ms": elapsed_ms,
            "heatmap_ms": heatmap_ms,
            "hotspot_ms": hotspot_ms,
            "meets_performance_target": elapsed_ms < 5000 and heatmap_ms < 3000 and hotspot_ms < 5000,
            "detection_pipeline": [
                "coordinate_mapping",
                "spatial_statistics",
                "hotspot_detection",
                "cluster_analysis",
                "heatmap_generation",
                "engineering_dashboard",
            ],
            "total_dies": legacy.get("total_dies", 0),
            "failing_dies": legacy.get("failing_dies", 0),
            "die_profiles": die_profiles,
            "spatial_ai_handoff": legacy.get("spatial_ai_handoff", []),
            "coordinate_mapping": coordinate_map,
            "failure_density": density_report,
            "neighbor_analysis": neighbor_report,
            "pattern_density": pattern_density,
            "yield_distribution": yield_dist,
            "hotspot_analysis": hotspot_report,
            "ai_hotspot_analysis": ai_hotspots,
            "cluster_report": cluster_report,
            "die_heatmap": heatmap,
            "engineering_dashboard": dashboard,
            "legacy_report": {
                "severity_caveat": legacy.get("severity_caveat"),
                "severity_determinable_count": legacy.get("severity_determinable_count"),
            },
        }


def _to_die_points(
    profiles: list[dict[str, Any]],
    handoff: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    intensity_lookup = {
        (h.get("die_id"), h.get("wafer_id")): h.get("intensity", 0.0) for h in handoff
    }
    points = []
    for profile in profiles:
        key = (profile.get("die_id"), profile.get("wafer_id"))
        points.append(
            {
                "die_id": profile.get("die_id"),
                "wafer_id": profile.get("wafer_id"),
                "lot_id": profile.get("lot_id"),
                "x": profile.get("x"),
                "y": profile.get("y"),
                "is_failing": profile.get("is_failing_die", False),
                "intensity": intensity_lookup.get(key, 0.0),
            }
        )
    return points
