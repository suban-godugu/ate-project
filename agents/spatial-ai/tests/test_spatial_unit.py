"""Unit tests for cluster and zone analysis (no network / no model)."""

from __future__ import annotations

from src.cluster_analysis import detect_defect_clusters, severity_label
from src.dice_analysis import calculate_yield
from src.zone_analysis import analyze_engineering_zones, assign_die_zone


def test_calculate_yield_from_dies(sample_dies):
    summary = calculate_yield(sample_dies)
    assert summary["total_dies"] == len(sample_dies)
    assert summary["good_dies"] + summary["fail_dies"] == summary["total_dies"]
    assert 0.0 <= summary["yield_percent"] <= 100.0


def test_cluster_detection_finds_fail_component(sample_dies, sample_yield):
    payload = detect_defect_clusters(sample_dies, sample_yield)
    summary = payload["cluster_summary"]
    clusters = payload["clusters"]
    assert summary["total_clusters_detected"] >= 1
    assert summary["displayed_clusters"] == len(clusters)
    assert clusters[0]["rank"] == 1
    assert clusters[0]["cluster_id"].startswith("C")
    assert clusters[0]["fail_dies"] >= 1
    assert "severity" in clusters[0]
    assert "bounding_box" in clusters[0]


def test_severity_label_thresholds():
    assert severity_label(0.2) == "Very Low"
    assert severity_label(1.0) == "Low"
    assert severity_label(2.0) == "Medium"
    assert severity_label(4.0) == "High"
    assert severity_label(7.0) == "Critical"


def test_zone_assignment_center(sample_geometry):
    die = {"x": 112, "y": 112, "status": "GOOD"}
    assert assign_die_zone(die, sample_geometry) == "Center"


def test_zone_analysis_returns_six_zones(sample_dies, sample_geometry):
    zones = analyze_engineering_zones(sample_dies, sample_geometry)
    assert len(zones) == 6
    names = {z["zone"] for z in zones}
    assert "Center" in names
    assert "Edge" in names
    assert zones[0]["rank"] == 1
    for zone in zones:
        assert "status" in zone
        assert isinstance(zone["zone_boundary"], list)
