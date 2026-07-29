"""Deterministic die-level spatial engine for FA-FR-007."""

from __future__ import annotations

import hashlib
import math
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class DieComputationError(ValueError):
    pass


@dataclass(frozen=True)
class DieAnalysisConfig:
    version: str
    algorithm: str
    hotspot_density: float
    hotspot_min_dies: int
    cluster_eps: float
    cluster_min_samples: int
    grid_cell_size: float
    neighbor_radius: float
    isolated_neighbor_max: int
    min_confidence: float
    health_critical: float
    health_high: float
    health_medium: float
    trend_delta: float
    min_sample_size: int
    batch_size: int
    max_coordinate_export: int
    compatible_formula_prefix: str
    require_same_tenant: bool
    require_product_overlap: bool
    require_test_stage_overlap: bool

    @classmethod
    def load(cls, path: str | Path | None = None) -> "DieAnalysisConfig":
        target = (
            Path(path)
            if path
            else Path(__file__).resolve().parents[2]
            / "config"
            / "die_analysis_production.yaml"
        )
        raw = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
        thresholds = raw.get("thresholds", {})
        cohort = raw.get("cohort", {})
        performance = raw.get("performance", {})
        return cls(
            version=str(raw.get("config_version", "die-analysis-v2.0")),
            algorithm=str(raw.get("algorithm", "grid_union_find")),
            hotspot_density=float(thresholds.get("hotspot_density", 0.15)),
            hotspot_min_dies=int(thresholds.get("hotspot_min_dies", 3)),
            cluster_eps=float(thresholds.get("cluster_eps", 2.5)),
            cluster_min_samples=int(thresholds.get("cluster_min_samples", 3)),
            grid_cell_size=float(thresholds.get("grid_cell_size", 1.0)),
            neighbor_radius=float(thresholds.get("neighbor_radius", 1.5)),
            isolated_neighbor_max=int(thresholds.get("isolated_neighbor_max", 0)),
            min_confidence=float(thresholds.get("minimum_confidence", 0.55)),
            health_critical=float(thresholds.get("health_critical", 0.35)),
            health_high=float(thresholds.get("health_high", 0.55)),
            health_medium=float(thresholds.get("health_medium", 0.75)),
            trend_delta=float(thresholds.get("trend_delta", 0.05)),
            min_sample_size=int(thresholds.get("minimum_sample_size", 1)),
            batch_size=int(raw.get("batch_size", 10_000)),
            max_coordinate_export=int(performance.get("max_coordinate_export", 500)),
            compatible_formula_prefix=str(
                cohort.get("compatible_formula_prefix", "failure-rate-v1")
            ),
            require_same_tenant=bool(cohort.get("require_same_tenant", True)),
            require_product_overlap=bool(cohort.get("require_product_overlap", True)),
            require_test_stage_overlap=bool(
                cohort.get("require_test_stage_overlap", True)
            ),
        )


class ProductionDieAnalysisEngine:
    def __init__(self, config: DieAnalysisConfig) -> None:
        self.config = config

    def analyze(
        self,
        *,
        observations: list[dict[str, Any]],
        source_record_counts: dict[str, int],
        correlations: list[dict[str, Any]],
        recurrences: list[dict[str, Any]],
        failure_rates: dict[str, float],
        analysis_id: str,
        current_execution_id: str,
    ) -> dict[str, Any]:
        if not observations:
            raise DieComputationError("Die analysis requires traceable observations")
        if any(value <= 0 for value in source_record_counts.values()):
            raise DieComputationError("Every source execution requires a positive record count")

        current = [
            row
            for row in observations
            if str(row.get("execution_id", "")) == current_execution_id
        ]
        if not current:
            raise DieComputationError("Current FA-FR-002 execution has no die observations")

        dies = _aggregate_dies(current, analysis_id)
        if not dies:
            raise DieComputationError("No deterministic die identities could be formed")

        _assign_neighbors(dies, self.config)
        historical = _historical_densities(observations, current_execution_id)
        correlation_index = {
            (str(item["pattern_id"]), str(item["fault_type"])): item
            for item in correlations
        }
        recurrence_index = {
            (str(item["pattern_id"]), str(item["fault_type"])): item
            for item in recurrences
        }
        lot_stats = _scope_stats(dies, "lot_id")
        wafer_stats = _scope_stats(dies, "wafer_id")

        for die in dies:
            key = (die["dominant_pattern_id"], die["dominant_fault_type"])
            correlation = correlation_index.get(key, {})
            recurrence = recurrence_index.get(key, {})
            current_density = die["failure_density"]
            historical_density = historical.get(die["canonical_die_key"], 0.0)
            trend = _trend(current_density, historical_density, self.config.trend_delta)
            confidence = _confidence(die, correlation, recurrence, self.config)
            health = _health_score(die, self.config)
            severity = _severity_from_health(health, self.config)
            recommendations = _recommendations(
                die_result_id=die["die_result_id"],
                die=die,
                severity=severity,
                trend=trend,
                health=health,
            )
            die.update(
                {
                    "trend_status": trend,
                    "confidence_score": round(confidence, 6),
                    "health_score": round(health, 6),
                    "severity": severity,
                    "historical_density": round(historical_density, 6),
                    "lot_comparison": _comparison(die, lot_stats[die["lot_id"]]),
                    "wafer_comparison": _comparison(die, wafer_stats[die["wafer_id"]]),
                    "engineering_recommendation": recommendations[0]["action"],
                    "recommendations": recommendations,
                    "upstream_correlation_id": correlation.get("correlation_id"),
                    "upstream_recurrence_id": recurrence.get("recurrence_id"),
                    "failure_rate_pct": float(
                        failure_rates.get(die["dominant_pattern_id"], 0.0)
                    ),
                }
            )

        failing = [die for die in dies if die["is_failing"]]
        clusters = _cluster_union_find(failing, analysis_id, self.config)
        hotspots = _detect_hotspots(failing, analysis_id, self.config)
        _link_membership(dies, clusters, hotspots)

        dies.sort(
            key=lambda item: (
                item["severity"] != "critical",
                item["health_score"],
                item["canonical_die_key"],
            )
        )
        return {
            "dies": dies,
            "hotspots": hotspots,
            "clusters": clusters,
            "statistics": _statistics(dies, hotspots, clusters),
            "scoped_statistics": _scoped_statistics(dies, hotspots, clusters),
        }


def _aggregate_dies(rows: list[dict[str, Any]], analysis_id: str) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for row in rows:
        lot_id = str(row.get("lot_id", "")).strip()
        wafer_id = str(row.get("wafer_id", "")).strip()
        die_id = str(row.get("die_id", "")).strip()
        if not all((lot_id, wafer_id, die_id)):
            raise DieComputationError(
                "Every observation requires deterministic lot_id, wafer_id, and die_id"
            )
        canonical = hashlib.sha256(
            f"{lot_id.lower()}|{wafer_id.lower()}|{die_id.lower()}".encode()
        ).hexdigest()
        bucket = buckets.get(canonical)
        if bucket is None:
            die_result_id = str(
                uuid.uuid5(uuid.NAMESPACE_URL, f"{analysis_id}:{canonical}")
            )
            bucket = {
                "die_result_id": die_result_id,
                "canonical_die_key": canonical,
                "lot_id": lot_id,
                "wafer_id": wafer_id,
                "die_id": die_id,
                "x_values": [],
                "y_values": [],
                "failure_count": 0,
                "total_tests": 0,
                "source_record_ids": set(),
                "occurrence_ids": [],
                "pattern_counts": Counter(),
                "fault_counts": Counter(),
                "pattern_confidence": [],
                "classification_confidence": [],
                "correlation_scores": [],
            }
            buckets[canonical] = bucket
        source_record_id = str(row.get("source_record_id", "")).strip()
        if source_record_id and source_record_id not in bucket["source_record_ids"]:
            bucket["source_record_ids"].add(source_record_id)
            bucket["total_tests"] += 1
            bucket["failure_count"] += 1
        bucket["occurrence_ids"].append(str(row.get("occurrence_id", "")))
        pattern_id = str(row.get("pattern_id", "")).strip()
        fault_type = str(row.get("fault_type", "")).strip()
        if pattern_id:
            bucket["pattern_counts"][pattern_id] += 1
        if fault_type:
            bucket["fault_counts"][fault_type] += 1
        if row.get("x") is not None:
            bucket["x_values"].append(float(row["x"]))
        if row.get("y") is not None:
            bucket["y_values"].append(float(row["y"]))
        bucket["pattern_confidence"].append(float(row.get("pattern_confidence", 0.0)))
        bucket["classification_confidence"].append(
            float(row.get("classification_confidence", 0.0))
        )

    dies: list[dict[str, Any]] = []
    for canonical, bucket in sorted(buckets.items()):
        total = max(1, int(bucket["total_tests"]))
        density = bucket["failure_count"] / total
        x = _mean(bucket["x_values"])
        y = _mean(bucket["y_values"])
        dominant_pattern = (
            bucket["pattern_counts"].most_common(1)[0][0]
            if bucket["pattern_counts"]
            else ""
        )
        dominant_fault = (
            bucket["fault_counts"].most_common(1)[0][0]
            if bucket["fault_counts"]
            else ""
        )
        dies.append(
            {
                "die_result_id": bucket["die_result_id"],
                "canonical_die_key": canonical,
                "lot_id": bucket["lot_id"],
                "wafer_id": bucket["wafer_id"],
                "die_id": bucket["die_id"],
                "x": None if x is None else round(x, 4),
                "y": None if y is None else round(y, 4),
                "failure_count": int(bucket["failure_count"]),
                "total_tests": int(bucket["total_tests"]),
                "failure_density": round(density, 6),
                "is_failing": bucket["failure_count"] > 0,
                "dominant_pattern_id": dominant_pattern,
                "dominant_fault_type": dominant_fault,
                "pattern_breakdown": dict(bucket["pattern_counts"]),
                "fault_breakdown": dict(bucket["fault_counts"]),
                "occurrence_ids": bucket["occurrence_ids"][:500],
                "source_record_ids": sorted(bucket["source_record_ids"])[:500],
                "mean_pattern_confidence": round(
                    _mean(bucket["pattern_confidence"]) or 0.0, 6
                ),
                "mean_classification_confidence": round(
                    _mean(bucket["classification_confidence"]) or 0.0, 6
                ),
                "neighbor_failure_count": 0,
                "is_isolated": False,
                "hotspot_id": None,
                "cluster_id": None,
            }
        )
    return dies


def _assign_neighbors(dies: list[dict[str, Any]], config: DieAnalysisConfig) -> None:
    by_wafer: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for die in dies:
        if die["x"] is None or die["y"] is None:
            continue
        by_wafer[(die["lot_id"], die["wafer_id"])].append(die)

    radius = config.neighbor_radius
    radius_sq = radius * radius
    cell = max(config.grid_cell_size, 0.0001)
    for group in by_wafer.values():
        grid: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
        for die in group:
            grid[(int(die["x"] // cell), int(die["y"] // cell))].append(die)
        for die in group:
            cx, cy = int(die["x"] // cell), int(die["y"] // cell)
            neighbor_failures = 0
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for other in grid.get((cx + dx, cy + dy), []):
                        if other["die_result_id"] == die["die_result_id"]:
                            continue
                        dist_sq = (die["x"] - other["x"]) ** 2 + (
                            die["y"] - other["y"]
                        ) ** 2
                        if dist_sq <= radius_sq and other["is_failing"]:
                            neighbor_failures += 1
            die["neighbor_failure_count"] = neighbor_failures
            die["is_isolated"] = (
                die["is_failing"]
                and neighbor_failures <= config.isolated_neighbor_max
            )


def _historical_densities(
    observations: list[dict[str, Any]], current_execution_id: str
) -> dict[str, float]:
    buckets: dict[str, dict[str, Any]] = {}
    for row in observations:
        if str(row.get("execution_id", "")) == current_execution_id:
            continue
        lot_id = str(row.get("lot_id", "")).strip()
        wafer_id = str(row.get("wafer_id", "")).strip()
        die_id = str(row.get("die_id", "")).strip()
        if not all((lot_id, wafer_id, die_id)):
            continue
        canonical = hashlib.sha256(
            f"{lot_id.lower()}|{wafer_id.lower()}|{die_id.lower()}".encode()
        ).hexdigest()
        bucket = buckets.setdefault(
            canonical, {"failures": 0, "records": set()}
        )
        source_record_id = str(row.get("source_record_id", "")).strip()
        if source_record_id and source_record_id not in bucket["records"]:
            bucket["records"].add(source_record_id)
            bucket["failures"] += 1
    return {
        key: value["failures"] / max(1, len(value["records"]))
        for key, value in buckets.items()
    }


def _cluster_union_find(
    failing: list[dict[str, Any]],
    analysis_id: str,
    config: DieAnalysisConfig,
) -> list[dict[str, Any]]:
    points = [
        die
        for die in failing
        if die["x"] is not None and die["y"] is not None
    ]
    if not points:
        return []
    parent = {die["die_result_id"]: die["die_result_id"] for die in points}
    rank = {die["die_result_id"]: 0 for die in points}

    def find(node: str) -> str:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(left: str, right: str) -> None:
        root_l, root_r = find(left), find(right)
        if root_l == root_r:
            return
        if rank[root_l] < rank[root_r]:
            parent[root_l] = root_r
        elif rank[root_l] > rank[root_r]:
            parent[root_r] = root_l
        else:
            parent[root_r] = root_l
            rank[root_l] += 1

    cell = max(config.cluster_eps, 0.0001)
    grid: dict[tuple[str, str, int, int], list[dict[str, Any]]] = defaultdict(list)
    for die in points:
        key = (
            die["lot_id"],
            die["wafer_id"],
            int(die["x"] // cell),
            int(die["y"] // cell),
        )
        grid[key].append(die)

    eps_sq = config.cluster_eps * config.cluster_eps
    for die in points:
        cx, cy = int(die["x"] // cell), int(die["y"] // cell)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                neighbors = grid.get(
                    (die["lot_id"], die["wafer_id"], cx + dx, cy + dy), []
                )
                for other in neighbors:
                    if other["die_result_id"] <= die["die_result_id"]:
                        continue
                    dist_sq = (die["x"] - other["x"]) ** 2 + (die["y"] - other["y"]) ** 2
                    if dist_sq <= eps_sq:
                        union(die["die_result_id"], other["die_result_id"])

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for die in points:
        groups[find(die["die_result_id"])].append(die)

    clusters: list[dict[str, Any]] = []
    for root, members in sorted(groups.items()):
        if len(members) < config.cluster_min_samples:
            continue
        members = sorted(members, key=lambda item: item["canonical_die_key"])
        xs = [item["x"] for item in members]
        ys = [item["y"] for item in members]
        failures = sum(item["failure_count"] for item in members)
        density = failures / max(1, len(members))
        cluster_id = str(
            uuid.uuid5(uuid.NAMESPACE_URL, f"{analysis_id}:cluster:{root}")
        )
        lots = {item["lot_id"] for item in members}
        wafers = {item["wafer_id"] for item in members}
        severity = _severity_from_density(density, len(members), config)
        clusters.append(
            {
                "cluster_id": cluster_id,
                "lot_id": next(iter(lots)) if len(lots) == 1 else "MULTI",
                "wafer_id": next(iter(wafers)) if len(wafers) == 1 else "MULTI",
                "algorithm": config.algorithm,
                "die_count": len(members),
                "failure_count": failures,
                "density": round(density, 6),
                "centroid_x": round(_mean(xs) or 0.0, 4),
                "centroid_y": round(_mean(ys) or 0.0, 4),
                "severity": severity,
                "member_die_ids": [item["die_id"] for item in members],
                "member_result_ids": [item["die_result_id"] for item in members],
                "coordinates": [
                    {
                        "die_id": item["die_id"],
                        "x": item["x"],
                        "y": item["y"],
                        "failure_count": item["failure_count"],
                    }
                    for item in members[: config.max_coordinate_export]
                ],
                "details": {"root": root},
            }
        )
    clusters.sort(key=lambda item: (item["density"], item["die_count"]), reverse=True)
    return clusters


def _detect_hotspots(
    failing: list[dict[str, Any]],
    analysis_id: str,
    config: DieAnalysisConfig,
) -> list[dict[str, Any]]:
    """Detect spatial hotspots via neighbor-connected failing dies.

    Single grid cells alone are insufficient when ``grid_cell_size`` places each
    die in its own cell (common for integer coordinates). Neighbor linking with
    ``neighbor_radius`` groups adjacent failing dies, then density / min-die
    thresholds decide hotspot membership.
    """
    points = [
        die
        for die in failing
        if die["x"] is not None and die["y"] is not None
    ]
    if not points:
        return []

    parent = {die["die_result_id"]: die["die_result_id"] for die in points}
    rank = {die["die_result_id"]: 0 for die in points}

    def find(node: str) -> str:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(left: str, right: str) -> None:
        root_l, root_r = find(left), find(right)
        if root_l == root_r:
            return
        if rank[root_l] < rank[root_r]:
            parent[root_l] = root_r
        elif rank[root_l] > rank[root_r]:
            parent[root_r] = root_l
        else:
            parent[root_r] = root_l
            rank[root_l] += 1

    cell = max(config.grid_cell_size, 0.0001)
    radius = max(float(config.neighbor_radius), cell)
    radius_sq = radius * radius
    grid: dict[tuple[str, str, int, int], list[dict[str, Any]]] = defaultdict(list)
    for die in points:
        key = (
            die["lot_id"],
            die["wafer_id"],
            int(die["x"] // cell),
            int(die["y"] // cell),
        )
        grid[key].append(die)

    for die in points:
        cx, cy = int(die["x"] // cell), int(die["y"] // cell)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                neighbors = grid.get(
                    (die["lot_id"], die["wafer_id"], cx + dx, cy + dy), []
                )
                for other in neighbors:
                    if other["die_result_id"] <= die["die_result_id"]:
                        continue
                    dist_sq = (die["x"] - other["x"]) ** 2 + (
                        die["y"] - other["y"]
                    ) ** 2
                    if dist_sq <= radius_sq:
                        union(die["die_result_id"], other["die_result_id"])

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for die in points:
        groups[find(die["die_result_id"])].append(die)

    wafer_totals: dict[tuple[str, str], int] = Counter(
        (die["lot_id"], die["wafer_id"]) for die in points
    )
    hotspots: list[dict[str, Any]] = []
    for root, members in sorted(groups.items()):
        if len(members) < config.hotspot_min_dies:
            continue
        lots = {item["lot_id"] for item in members}
        wafers = {item["wafer_id"] for item in members}
        lot_id = next(iter(lots)) if len(lots) == 1 else "MULTI"
        wafer_id = next(iter(wafers)) if len(wafers) == 1 else "MULTI"
        if lot_id == "MULTI" or wafer_id == "MULTI":
            density = len(members) / max(1, len(points))
        else:
            density = len(members) / max(1, wafer_totals[(lot_id, wafer_id)])
        if density < config.hotspot_density:
            continue
        members = sorted(members, key=lambda item: item["canonical_die_key"])
        failures = sum(item["failure_count"] for item in members)
        xs = [item["x"] for item in members]
        ys = [item["y"] for item in members]
        hotspot_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"{analysis_id}:hotspot:{lot_id}:{wafer_id}:{root}",
            )
        )
        severity = _severity_from_density(density, len(members), config)
        confidence = min(
            1.0,
            0.4
            + min(0.4, density)
            + min(0.2, len(members) / max(1, config.hotspot_min_dies * 4)),
        )
        hotspots.append(
            {
                "hotspot_id": hotspot_id,
                "lot_id": lot_id,
                "wafer_id": wafer_id,
                "center_x": round(_mean(xs) or 0.0, 4),
                "center_y": round(_mean(ys) or 0.0, 4),
                "radius": round(radius * math.sqrt(2), 4),
                "die_count": len(members),
                "failure_count": failures,
                "density": round(density, 6),
                "severity": severity,
                "confidence_score": round(confidence, 6),
                "member_die_ids": [item["die_id"] for item in members],
                "member_result_ids": [item["die_result_id"] for item in members],
                "coordinates": [
                    {
                        "die_id": item["die_id"],
                        "x": item["x"],
                        "y": item["y"],
                        "failure_count": item["failure_count"],
                    }
                    for item in members[: config.max_coordinate_export]
                ],
                "details": {"root": root, "algorithm": "neighbor_union_find"},
            }
        )
    hotspots.sort(key=lambda item: (item["density"], item["die_count"]), reverse=True)
    return hotspots


def _link_membership(
    dies: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    hotspots: list[dict[str, Any]],
) -> None:
    cluster_map = {
        result_id: cluster["cluster_id"]
        for cluster in clusters
        for result_id in cluster["member_result_ids"]
    }
    hotspot_map = {
        result_id: hotspot["hotspot_id"]
        for hotspot in hotspots
        for result_id in hotspot["member_result_ids"]
    }
    for die in dies:
        die["cluster_id"] = cluster_map.get(die["die_result_id"])
        die["hotspot_id"] = hotspot_map.get(die["die_result_id"])


def _scope_stats(
    dies: list[dict[str, Any]], key: str
) -> dict[str, dict[str, float]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for die in dies:
        groups[str(die[key])].append(die)
    stats: dict[str, dict[str, float]] = {}
    for scope, members in groups.items():
        densities = [item["failure_density"] for item in members]
        health = [
            item.get("health_score", 1.0 - item["failure_density"]) for item in members
        ]
        stats[scope] = {
            "mean_density": _mean(densities) or 0.0,
            "mean_health": _mean(health) or 0.0,
            "die_count": float(len(members)),
            "failing_dies": float(sum(1 for item in members if item["is_failing"])),
        }
    return stats


def _comparison(die: dict[str, Any], scope: dict[str, float]) -> dict[str, Any]:
    return {
        "scope_mean_density": round(scope["mean_density"], 6),
        "scope_mean_health": round(scope["mean_health"], 6),
        "density_delta": round(die["failure_density"] - scope["mean_density"], 6),
        "scope_die_count": int(scope["die_count"]),
        "scope_failing_dies": int(scope["failing_dies"]),
        "relative_rank": (
            "above_average"
            if die["failure_density"] > scope["mean_density"] + 1e-9
            else "at_or_below_average"
        ),
    }


def _confidence(
    die: dict[str, Any],
    correlation: dict[str, Any],
    recurrence: dict[str, Any],
    config: DieAnalysisConfig,
) -> float:
    sample = min(1.0, math.log1p(die["total_tests"]) / math.log1p(50))
    upstream = (
        float(correlation.get("confidence_score", 0.0)) * 0.35
        + float(recurrence.get("confidence_score", 0.0)) * 0.25
        + die["mean_pattern_confidence"] * 0.2
        + die["mean_classification_confidence"] * 0.2
    )
    coordinate_bonus = 0.05 if die["x"] is not None and die["y"] is not None else 0.0
    score = min(1.0, upstream * 0.7 + sample * 0.25 + coordinate_bonus)
    if die["total_tests"] < config.min_sample_size:
        return min(score, config.min_confidence)
    return score


def _health_score(die: dict[str, Any], config: DieAnalysisConfig) -> float:
    density_penalty = die["failure_density"]
    neighbor_penalty = min(0.35, die["neighbor_failure_count"] * 0.05)
    isolated_penalty = 0.1 if die["is_isolated"] else 0.0
    health = 1.0 - min(1.0, density_penalty * 0.7 + neighbor_penalty + isolated_penalty)
    return max(0.0, min(1.0, health))


def _severity_from_health(health: float, config: DieAnalysisConfig) -> str:
    if health < config.health_critical:
        return "critical"
    if health < config.health_high:
        return "high"
    if health < config.health_medium:
        return "medium"
    return "low"


def _severity_from_density(
    density: float, count: int, config: DieAnalysisConfig
) -> str:
    if density >= config.hotspot_density * 2 or count >= config.hotspot_min_dies * 3:
        return "critical"
    if density >= config.hotspot_density * 1.5 or count >= config.hotspot_min_dies * 2:
        return "high"
    if density >= config.hotspot_density:
        return "medium"
    return "low"


def _trend(current: float, historical: float, delta: float) -> str:
    change = current - historical
    if change >= delta:
        return "increasing"
    if change <= -delta:
        return "decreasing"
    return "stable"


def _recommendations(
    *,
    die_result_id: str,
    die: dict[str, Any],
    severity: str,
    trend: str,
    health: float,
) -> list[dict[str, Any]]:
    actions = [
        (
            "DIE_HEALTH_REVIEW",
            "critical" if severity == "critical" else "high",
            f"Review die {die['die_id']} on wafer {die['wafer_id']} (health {health:.3f}).",
            f"Failure density {die['failure_density']:.3f} with severity {severity}.",
        )
    ]
    if die["is_isolated"]:
        actions.append(
            (
                "ISOLATED_FAILURE_REVIEW",
                "medium",
                "Inspect isolated failing die for random defect or probe mark issues.",
                "No failing spatial neighbors within configured radius.",
            )
        )
    if die.get("hotspot_id"):
        actions.append(
            (
                "HOTSPOT_CONTAINMENT",
                "high",
                f"Contain process window around hotspot including die {die['die_id']}.",
                "Die participates in a spatial hotspot.",
            )
        )
    if die.get("cluster_id"):
        actions.append(
            (
                "CLUSTER_PROCESS_DRIFT",
                "high",
                "Investigate clustered die failures for tool/process drift.",
                "Die participates in a deterministic spatial cluster.",
            )
        )
    if trend == "increasing":
        actions.append(
            (
                "ESCALATING_DIE_FAILURE",
                "high",
                "Escalate historical density trend for this die identity.",
                "Current failure density exceeds the historical compatible baseline.",
            )
        )
    return [
        {
            "recommendation_id": str(
                uuid.uuid5(uuid.NAMESPACE_URL, f"{die_result_id}:{code}")
            ),
            "recommendation_code": code,
            "priority": priority,
            "action": action,
            "rationale": rationale,
            "evidence": {
                "die_id": die["die_id"],
                "wafer_id": die["wafer_id"],
                "lot_id": die["lot_id"],
                "health_score": round(health, 6),
                "severity": severity,
                "trend": trend,
            },
        }
        for code, priority, action, rationale in actions
    ]


def _statistics(
    dies: list[dict[str, Any]],
    hotspots: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
) -> dict[str, Any]:
    failing = [die for die in dies if die["is_failing"]]
    return {
        "total_dies": len(dies),
        "failing_dies": len(failing),
        "isolated_failures": sum(1 for die in dies if die["is_isolated"]),
        "mean_failure_density": round(
            _mean([die["failure_density"] for die in dies]) or 0.0, 6
        ),
        "mean_health_score": round(
            _mean([die["health_score"] for die in dies]) or 0.0, 6
        ),
        "mean_confidence": round(
            _mean([die["confidence_score"] for die in dies]) or 0.0, 6
        ),
        "hotspot_count": len(hotspots),
        "cluster_count": len(clusters),
        "critical_count": sum(1 for die in dies if die["severity"] == "critical"),
        "high_count": sum(1 for die in dies if die["severity"] == "high"),
    }


def _scoped_statistics(
    dies: list[dict[str, Any]],
    hotspots: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = [
        {
            "scope_type": "analysis",
            "scope_key": "all",
            **_statistics(dies, hotspots, clusters),
            "details": {},
        }
    ]
    for dimension in ("lot_id", "wafer_id"):
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for die in dies:
            groups[str(die[dimension])].append(die)
        for scope_key, members in sorted(groups.items()):
            scoped_hotspots = [
                item
                for item in hotspots
                if scope_key
                in {
                    item["lot_id"] if dimension == "lot_id" else item["wafer_id"],
                }
            ]
            scoped_clusters = [
                item
                for item in clusters
                if scope_key
                in {
                    item["lot_id"] if dimension == "lot_id" else item["wafer_id"],
                }
            ]
            rows.append(
                {
                    "scope_type": dimension.removesuffix("_id"),
                    "scope_key": scope_key,
                    **_statistics(members, scoped_hotspots, scoped_clusters),
                    "details": {
                        "die_result_ids": [item["die_result_id"] for item in members]
                    },
                }
            )
    return rows


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)
