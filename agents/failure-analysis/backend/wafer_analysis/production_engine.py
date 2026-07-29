"""Deterministic wafer-level spatial engine for FA-FR-008."""

from __future__ import annotations

import hashlib
import math
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class WaferComputationError(ValueError):
    pass


@dataclass(frozen=True)
class WaferAnalysisConfig:
    version: str
    algorithm: str
    hotspot_density: float
    hotspot_min_dies: int
    grid_cell_size: float
    edge_radius_fraction: float
    center_radius_fraction: float
    radial_bins: int
    min_confidence: float
    health_critical: float
    health_high: float
    health_medium: float
    trend_delta: float
    yield_outlier_delta: float
    min_sample_size: int
    batch_size: int
    max_grid_export: int
    compatible_formula_prefix: str
    require_same_tenant: bool
    require_product_overlap: bool
    require_test_stage_overlap: bool

    @classmethod
    def load(cls, path: str | Path | None = None) -> "WaferAnalysisConfig":
        target = (
            Path(path)
            if path
            else Path(__file__).resolve().parents[2]
            / "config"
            / "wafer_analysis_production.yaml"
        )
        raw = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
        thresholds = raw.get("thresholds", {})
        cohort = raw.get("cohort", {})
        performance = raw.get("performance", {})
        return cls(
            version=str(raw.get("config_version", "wafer-analysis-v2.0")),
            algorithm=str(raw.get("algorithm", "deterministic_grid_aggregate")),
            hotspot_density=float(thresholds.get("hotspot_density", 0.15)),
            hotspot_min_dies=int(thresholds.get("hotspot_min_dies", 3)),
            grid_cell_size=float(thresholds.get("grid_cell_size", 1.0)),
            edge_radius_fraction=float(thresholds.get("edge_radius_fraction", 0.67)),
            center_radius_fraction=float(thresholds.get("center_radius_fraction", 0.34)),
            radial_bins=int(thresholds.get("radial_bins", 8)),
            min_confidence=float(thresholds.get("minimum_confidence", 0.55)),
            health_critical=float(thresholds.get("health_critical", 0.35)),
            health_high=float(thresholds.get("health_high", 0.55)),
            health_medium=float(thresholds.get("health_medium", 0.75)),
            trend_delta=float(thresholds.get("trend_delta", 0.05)),
            yield_outlier_delta=float(thresholds.get("yield_outlier_delta", 10.0)),
            min_sample_size=int(thresholds.get("minimum_sample_size", 1)),
            batch_size=int(raw.get("batch_size", 10_000)),
            max_grid_export=int(performance.get("max_grid_export", 500)),
            compatible_formula_prefix=str(
                cohort.get("compatible_formula_prefix", "failure-rate-v1")
            ),
            require_same_tenant=bool(cohort.get("require_same_tenant", True)),
            require_product_overlap=bool(cohort.get("require_product_overlap", True)),
            require_test_stage_overlap=bool(
                cohort.get("require_test_stage_overlap", True)
            ),
        )


class ProductionWaferAnalysisEngine:
    def __init__(self, config: WaferAnalysisConfig) -> None:
        self.config = config

    def analyze(
        self,
        *,
        dies: list[dict[str, Any]],
        die_hotspots: list[dict[str, Any]],
        historical_wafer_yields: dict[str, float],
        analysis_id: str,
        die_analysis_id: str,
    ) -> dict[str, Any]:
        if not dies:
            raise WaferComputationError("Wafer analysis requires traceable die results")

        wafers = _aggregate_wafers(dies, analysis_id)
        if not wafers:
            raise WaferComputationError("No deterministic wafer identities could be formed")

        lot_stats = _scope_stats(wafers, "lot_id")
        for wafer in wafers:
            spatial = _spatial_metrics(wafer["dies"], self.config)
            radial = _radial_distribution(wafer["dies"], self.config)
            edge_rate, center_rate = _edge_center_rates(wafer["dies"], self.config)
            historical_yield = historical_wafer_yields.get(wafer["canonical_wafer_key"])
            trend = _yield_trend(wafer["yield_pct"], historical_yield, self.config)
            confidence = _confidence(wafer, self.config)
            health = _health_score(wafer, edge_rate, center_rate, self.config)
            severity = _severity_from_health(health, self.config)
            recommendations = _recommendations(
                wafer_result_id=wafer["wafer_result_id"],
                wafer=wafer,
                severity=severity,
                trend=trend,
                edge_rate=edge_rate,
                center_rate=center_rate,
            )
            wafer.update(
                {
                    "failure_density": round(
                        wafer["failing_dies"] / max(1, wafer["total_dies"]), 6
                    ),
                    "edge_failure_rate": round(edge_rate, 6),
                    "center_failure_rate": round(center_rate, 6),
                    "radial_distribution": radial,
                    "spatial": spatial,
                    "trend_status": trend,
                    "confidence_score": round(confidence, 6),
                    "health_score": round(health, 6),
                    "severity": severity,
                    "historical_yield_pct": historical_yield,
                    "yield_delta": (
                        round(wafer["yield_pct"] - historical_yield, 6)
                        if historical_yield is not None
                        else None
                    ),
                    "lot_comparison": _comparison(wafer, lot_stats[wafer["lot_id"]]),
                    "engineering_recommendation": recommendations[0]["action"],
                    "recommendations": recommendations,
                    "die_analysis_id": die_analysis_id,
                }
            )

        hotspots = _detect_wafer_hotspots(
            wafers, die_hotspots, analysis_id, self.config
        )
        yield_metrics = _yield_metrics(wafers)

        wafers.sort(
            key=lambda item: (
                item["severity"] != "critical",
                item["health_score"],
                item["canonical_wafer_key"],
            )
        )
        for wafer in wafers:
            wafer["dies"] = sorted(
                wafer["dies"],
                key=lambda item: (
                    str(item.get("canonical_die_key", "")),
                    str(item.get("die_id", "")),
                ),
            )
        return {
            "wafers": wafers,
            "hotspots": hotspots,
            "yield_metrics": yield_metrics,
            "statistics": _statistics(wafers, hotspots),
            "scoped_statistics": _scoped_statistics(wafers, hotspots),
        }


def _aggregate_wafers(
    dies: list[dict[str, Any]], analysis_id: str
) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for die in dies:
        lot_id = str(die.get("lot_id", "")).strip()
        wafer_id = str(die.get("wafer_id", "")).strip()
        if not all((lot_id, wafer_id)):
            raise WaferComputationError(
                "Every die result requires deterministic lot_id and wafer_id"
            )
        canonical = hashlib.sha256(
            f"{lot_id.lower()}|{wafer_id.lower()}".encode()
        ).hexdigest()
        bucket = buckets.get(canonical)
        if bucket is None:
            wafer_result_id = str(
                uuid.uuid5(uuid.NAMESPACE_URL, f"{analysis_id}:{canonical}")
            )
            bucket = {
                "wafer_result_id": wafer_result_id,
                "canonical_wafer_key": canonical,
                "lot_id": lot_id,
                "wafer_id": wafer_id,
                "dies": [],
                "total_dies": 0,
                "failing_dies": 0,
                "die_ids": set(),
            }
            buckets[canonical] = bucket
        die_id = str(die.get("die_id", "")).strip()
        if die_id and die_id in bucket["die_ids"]:
            continue
        if die_id:
            bucket["die_ids"].add(die_id)
        bucket["dies"].append(die)
        bucket["total_dies"] += 1
        if die.get("is_failing"):
            bucket["failing_dies"] += 1

    wafers: list[dict[str, Any]] = []
    for canonical, bucket in sorted(buckets.items()):
        total = max(1, bucket["total_dies"])
        failing = bucket["failing_dies"]
        yield_pct = round((1.0 - failing / total) * 100.0, 4)
        wafers.append(
            {
                "wafer_result_id": bucket["wafer_result_id"],
                "canonical_wafer_key": canonical,
                "lot_id": bucket["lot_id"],
                "wafer_id": bucket["wafer_id"],
                "dies": bucket["dies"],
                "total_dies": bucket["total_dies"],
                "failing_dies": failing,
                "yield_pct": yield_pct,
            }
        )
    return wafers


def _spatial_metrics(
    dies: list[dict[str, Any]], config: WaferAnalysisConfig
) -> dict[str, Any]:
    coords = [
        (float(d["x"]), float(d["y"]))
        for d in dies
        if d.get("x") is not None and d.get("y") is not None
    ]
    if not coords:
        return {"coordinate_count": 0, "centroid": None, "max_radius": 0.0}
    cx = sum(x for x, _ in coords) / len(coords)
    cy = sum(y for _, y in coords) / len(coords)
    max_r = max(math.sqrt((x - cx) ** 2 + (y - cy) ** 2) for x, y in coords) or 1.0
    return {
        "coordinate_count": len(coords),
        "centroid": {"x": round(cx, 4), "y": round(cy, 4)},
        "max_radius": round(max_r, 4),
        "grid_cell_size": config.grid_cell_size,
    }


def _radial_distribution(
    dies: list[dict[str, Any]], config: WaferAnalysisConfig
) -> dict[str, Any]:
    coords = [
        d
        for d in dies
        if d.get("x") is not None
        and d.get("y") is not None
        and d.get("is_failing")
    ]
    if not coords:
        return {"radial_bins": config.radial_bins, "profile": [], "pattern": "none"}
    cx = sum(float(d["x"]) for d in coords) / len(coords)
    cy = sum(float(d["y"]) for d in coords) / len(coords)
    all_coords = [
        (float(d["x"]), float(d["y"]))
        for d in dies
        if d.get("x") is not None and d.get("y") is not None
    ]
    max_r = max(math.sqrt((x - cx) ** 2 + (y - cy) ** 2) for x, y in all_coords) or 1.0
    bins = [0] * config.radial_bins
    for d in coords:
        r_norm = math.sqrt(
            (float(d["x"]) - cx) ** 2 + (float(d["y"]) - cy) ** 2
        ) / max_r
        bin_idx = min(int(r_norm * config.radial_bins), config.radial_bins - 1)
        bins[bin_idx] += 1
    total_failing = sum(bins)
    profile = [
        {
            "ring": i,
            "radius_min": round(i / config.radial_bins, 4),
            "radius_max": round((i + 1) / config.radial_bins, 4),
            "failure_count": bins[i],
            "failure_pct": round(100.0 * bins[i] / total_failing, 2)
            if total_failing
            else 0.0,
        }
        for i in range(config.radial_bins)
    ]
    return {
        "radial_bins": config.radial_bins,
        "centroid": {"x": round(cx, 4), "y": round(cy, 4)},
        "profile": profile,
        "pattern": _radial_pattern(profile),
        "total_failing": total_failing,
    }


def _radial_pattern(profile: list[dict[str, Any]]) -> str:
    if not profile:
        return "unknown"
    outer = sum(p["failure_count"] for p in profile[-2:])
    inner = sum(p["failure_count"] for p in profile[:2])
    total = sum(p["failure_count"] for p in profile)
    if total == 0:
        return "none"
    if outer > inner * 2:
        return "edge_ring"
    if inner > outer * 2:
        return "center_ring"
    return "uniform"


def _edge_center_rates(
    dies: list[dict[str, Any]], config: WaferAnalysisConfig
) -> tuple[float, float]:
    coords = [
        d
        for d in dies
        if d.get("x") is not None and d.get("y") is not None
    ]
    if not coords:
        return 0.0, 0.0
    cx = sum(float(d["x"]) for d in coords) / len(coords)
    cy = sum(float(d["y"]) for d in coords) / len(coords)
    max_r = (
        max(
            math.sqrt((float(d["x"]) - cx) ** 2 + (float(d["y"]) - cy) ** 2)
            for d in coords
        )
        or 1.0
    )
    edge_fail = 0
    center_fail = 0
    edge_total = 0
    center_total = 0
    for d in coords:
        r = math.sqrt((float(d["x"]) - cx) ** 2 + (float(d["y"]) - cy) ** 2) / max_r
        if r >= config.edge_radius_fraction:
            edge_total += 1
            if d.get("is_failing"):
                edge_fail += 1
        if r < config.center_radius_fraction:
            center_total += 1
            if d.get("is_failing"):
                center_fail += 1
    edge_rate = edge_fail / max(1, edge_total)
    center_rate = center_fail / max(1, center_total)
    return edge_rate, center_rate


def _detect_wafer_hotspots(
    wafers: list[dict[str, Any]],
    die_hotspots: list[dict[str, Any]],
    analysis_id: str,
    config: WaferAnalysisConfig,
) -> list[dict[str, Any]]:
    die_hotspot_by_wafer: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in die_hotspots:
        key = (str(item.get("lot_id", "")), str(item.get("wafer_id", "")))
        die_hotspot_by_wafer[key].append(item)

    hotspots: list[dict[str, Any]] = []
    for wafer in wafers:
        key = (wafer["lot_id"], wafer["wafer_id"])
        grid = _density_grid(wafer["dies"], config)
        merged_cells: list[dict[str, Any]] = []
        for cell in grid:
            if cell["failure_count"] < config.hotspot_min_dies:
                continue
            if cell["density"] < config.hotspot_density:
                continue
            merged_cells.append(cell)
        if not merged_cells and not die_hotspot_by_wafer.get(key):
            continue
        if merged_cells:
            best = max(merged_cells, key=lambda c: (c["density"], c["failure_count"]))
            member_ids = [
                str(d.get("die_id", ""))
                for d in wafer["dies"]
                if d.get("x") is not None
                and d.get("y") is not None
                and abs(float(d["x"]) - best["x"]) <= config.grid_cell_size
                and abs(float(d["y"]) - best["y"]) <= config.grid_cell_size
                and d.get("is_failing")
            ]
            hotspot_id = str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"{analysis_id}:{wafer['canonical_wafer_key']}:hotspot:{best['x']}:{best['y']}",
                )
            )
            density = best["density"]
            severity = (
                "critical"
                if density >= config.hotspot_density * 2
                else "high"
                if density >= config.hotspot_density * 1.5
                else "medium"
            )
            hotspots.append(
                {
                    "hotspot_id": hotspot_id,
                    "lot_id": wafer["lot_id"],
                    "wafer_id": wafer["wafer_id"],
                    "center_x": best["x"],
                    "center_y": best["y"],
                    "radius": config.grid_cell_size,
                    "die_count": best["die_count"],
                    "failure_count": best["failure_count"],
                    "density": round(density, 6),
                    "severity": severity,
                    "confidence_score": round(min(1.0, density + 0.25), 6),
                    "member_die_ids": sorted(set(member_ids))[:200],
                    "density_grid": grid[: config.max_grid_export],
                    "details": {
                        "source": "density_grid",
                        "die_hotspot_count": len(die_hotspot_by_wafer.get(key, [])),
                    },
                }
            )
        for die_hotspot in die_hotspot_by_wafer.get(key, [])[:5]:
            hotspot_id = str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"{analysis_id}:{wafer['canonical_wafer_key']}:die-hotspot:{die_hotspot.get('hotspot_id', '')}",
                )
            )
            if any(h["hotspot_id"] == hotspot_id for h in hotspots):
                continue
            hotspots.append(
                {
                    "hotspot_id": hotspot_id,
                    "lot_id": wafer["lot_id"],
                    "wafer_id": wafer["wafer_id"],
                    "center_x": die_hotspot.get("center_x"),
                    "center_y": die_hotspot.get("center_y"),
                    "radius": die_hotspot.get("radius", config.grid_cell_size),
                    "die_count": die_hotspot.get("die_count", 0),
                    "failure_count": die_hotspot.get("failure_count", 0),
                    "density": round(float(die_hotspot.get("density", 0.0)), 6),
                    "severity": die_hotspot.get("severity", "medium"),
                    "confidence_score": round(
                        float(die_hotspot.get("confidence_score", 0.5)), 6
                    ),
                    "member_die_ids": list(die_hotspot.get("member_die_ids", []))[:200],
                    "density_grid": grid[: config.max_grid_export],
                    "details": {"source": "die_hotspot_aggregate"},
                }
            )
    hotspots.sort(
        key=lambda item: (-item["density"], -item["failure_count"], item["hotspot_id"])
    )
    return hotspots


def _density_grid(
    dies: list[dict[str, Any]], config: WaferAnalysisConfig
) -> list[dict[str, Any]]:
    cells: dict[tuple[int, int], dict[str, Any]] = {}
    size = config.grid_cell_size
    for die in dies:
        if die.get("x") is None or die.get("y") is None:
            continue
        gx = int(math.floor(float(die["x"]) / size))
        gy = int(math.floor(float(die["y"]) / size))
        cell = cells.get((gx, gy))
        if cell is None:
            cell = {
                "x": round((gx + 0.5) * size, 4),
                "y": round((gy + 0.5) * size, 4),
                "die_count": 0,
                "failure_count": 0,
                "density": 0.0,
            }
            cells[(gx, gy)] = cell
        cell["die_count"] += 1
        if die.get("is_failing"):
            cell["failure_count"] += 1
    for cell in cells.values():
        cell["density"] = round(cell["failure_count"] / max(1, cell["die_count"]), 6)
    return sorted(
        cells.values(),
        key=lambda item: (-item["density"], -item["failure_count"], item["x"], item["y"]),
    )


def _scope_stats(
    wafers: list[dict[str, Any]], field: str
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for wafer in wafers:
        grouped[str(wafer[field])].append(wafer)
    stats: dict[str, dict[str, Any]] = {}
    for key, rows in grouped.items():
        total_dies = sum(row["total_dies"] for row in rows)
        failing_dies = sum(row["failing_dies"] for row in rows)
        stats[key] = {
            "total_wafers": len(rows),
            "failing_wafers": sum(1 for row in rows if row["failing_dies"] > 0),
            "total_dies": total_dies,
            "failing_dies": failing_dies,
            "mean_yield_pct": round(
                sum(row["yield_pct"] for row in rows) / max(1, len(rows)), 4
            ),
            "mean_failure_density": round(
                failing_dies / max(1, total_dies), 6
            ),
            "mean_health_score": round(
                sum(row.get("health_score", 1.0) for row in rows) / max(1, len(rows)),
                6,
            ),
        }
    return stats


def _comparison(
    wafer: dict[str, Any], scope: dict[str, Any]
) -> dict[str, Any]:
    return {
        "scope_yield_pct": scope.get("mean_yield_pct"),
        "wafer_yield_pct": wafer.get("yield_pct"),
        "yield_delta": round(
            wafer.get("yield_pct", 0.0) - scope.get("mean_yield_pct", 0.0), 4
        ),
        "scope_failure_density": scope.get("mean_failure_density"),
        "wafer_failure_density": wafer.get("failure_density"),
        "relative_health": round(
            wafer.get("health_score", 1.0) - scope.get("mean_health_score", 1.0), 4
        ),
    }


def _yield_trend(
    current_yield: float,
    historical: float | None,
    config: WaferAnalysisConfig,
) -> str:
    if historical is None:
        return "unknown"
    delta = current_yield - historical
    if delta <= -config.trend_delta * 100:
        return "decreasing"
    if delta >= config.trend_delta * 100:
        return "increasing"
    return "stable"


def _confidence(wafer: dict[str, Any], config: WaferAnalysisConfig) -> float:
    sample_factor = min(1.0, wafer["total_dies"] / max(1, config.min_sample_size * 10))
    density = wafer["failing_dies"] / max(1, wafer["total_dies"])
    die_confidences = [
        float(d.get("confidence_score", 0.0))
        for d in wafer["dies"]
        if d.get("confidence_score") is not None
    ]
    mean_die_conf = (
        sum(die_confidences) / len(die_confidences) if die_confidences else 0.5
    )
    return max(config.min_confidence, min(1.0, (density + mean_die_conf) * sample_factor))


def _health_score(
    wafer: dict[str, Any],
    edge_rate: float,
    center_rate: float,
    config: WaferAnalysisConfig,
) -> float:
    yield_factor = wafer["yield_pct"] / 100.0
    die_health = [
        float(d.get("health_score", 1.0)) for d in wafer["dies"] if d.get("is_failing")
    ]
    mean_die_health = sum(die_health) / len(die_health) if die_health else 1.0
    spatial_penalty = max(edge_rate, center_rate) * 0.15
    return max(0.0, min(1.0, yield_factor * 0.5 + mean_die_health * 0.4 - spatial_penalty))


def _severity_from_health(health: float, config: WaferAnalysisConfig) -> str:
    if health <= config.health_critical:
        return "critical"
    if health <= config.health_high:
        return "high"
    if health <= config.health_medium:
        return "medium"
    return "low"


def _recommendations(
    *,
    wafer_result_id: str,
    wafer: dict[str, Any],
    severity: str,
    trend: str,
    edge_rate: float,
    center_rate: float,
) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    if severity in {"critical", "high"}:
        recs.append(
            {
                "recommendation_id": str(
                    uuid.uuid5(uuid.NAMESPACE_URL, f"{wafer_result_id}:inspect")
                ),
                "recommendation_code": "WAFER_PRIORITY_INSPECTION",
                "priority": "high" if severity == "critical" else "medium",
                "action": "Schedule priority wafer inspection and retest failing dies",
                "rationale": (
                    f"Wafer {wafer['wafer_id']} health={wafer.get('health_score', 0):.2f} "
                    f"with {wafer['failing_dies']}/{wafer['total_dies']} failing dies"
                ),
                "evidence": {
                    "wafer_result_id": wafer_result_id,
                    "lot_id": wafer["lot_id"],
                    "wafer_id": wafer["wafer_id"],
                    "severity": severity,
                },
            }
        )
    if edge_rate >= 0.5:
        recs.append(
            {
                "recommendation_id": str(
                    uuid.uuid5(uuid.NAMESPACE_URL, f"{wafer_result_id}:edge")
                ),
                "recommendation_code": "EDGE_RING_INVESTIGATION",
                "priority": "medium",
                "action": "Investigate edge-ring process or handling defects",
                "rationale": f"Edge failure rate {edge_rate * 100:.1f}% exceeds threshold",
                "evidence": {"edge_failure_rate": edge_rate},
            }
        )
    if center_rate >= 0.5:
        recs.append(
            {
                "recommendation_id": str(
                    uuid.uuid5(uuid.NAMESPACE_URL, f"{wafer_result_id}:center")
                ),
                "recommendation_code": "CENTER_CLUSTER_REVIEW",
                "priority": "medium",
                "action": "Review center-cluster equipment or reticle alignment",
                "rationale": f"Center failure rate {center_rate * 100:.1f}% exceeds threshold",
                "evidence": {"center_failure_rate": center_rate},
            }
        )
    if trend == "decreasing":
        recs.append(
            {
                "recommendation_id": str(
                    uuid.uuid5(uuid.NAMESPACE_URL, f"{wafer_result_id}:trend")
                ),
                "recommendation_code": "YIELD_REGRESSION_ALERT",
                "priority": "high",
                "action": "Compare against historical wafer yield and lot siblings",
                "rationale": "Wafer yield decreased versus compatible historical executions",
                "evidence": {
                    "trend_status": trend,
                    "historical_yield_pct": wafer.get("historical_yield_pct"),
                    "current_yield_pct": wafer.get("yield_pct"),
                },
            }
        )
    if not recs:
        recs.append(
            {
                "recommendation_id": str(
                    uuid.uuid5(uuid.NAMESPACE_URL, f"{wafer_result_id}:monitor")
                ),
                "recommendation_code": "CONTINUE_MONITORING",
                "priority": "low",
                "action": "Continue monitoring wafer yield within lot baseline",
                "rationale": "No critical wafer-level anomalies detected",
                "evidence": {"wafer_result_id": wafer_result_id},
            }
        )
    return recs


def _yield_metrics(wafers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    metrics: list[dict[str, Any]] = []
    for wafer in wafers:
        metrics.append(
            {
                "wafer_result_id": wafer["wafer_result_id"],
                "lot_id": wafer["lot_id"],
                "wafer_id": wafer["wafer_id"],
                "yield_pct": wafer["yield_pct"],
                "historical_yield_pct": wafer.get("historical_yield_pct"),
                "yield_delta": wafer.get("yield_delta"),
                "trend_status": wafer.get("trend_status", "unknown"),
                "lot_yield_pct": (wafer.get("lot_comparison") or {}).get(
                    "scope_yield_pct"
                ),
                "details": {
                    "total_dies": wafer["total_dies"],
                    "failing_dies": wafer["failing_dies"],
                    "failure_density": wafer.get("failure_density"),
                },
            }
        )
    return metrics


def _statistics(
    wafers: list[dict[str, Any]], hotspots: list[dict[str, Any]]
) -> dict[str, Any]:
    total_dies = sum(w["total_dies"] for w in wafers)
    failing_dies = sum(w["failing_dies"] for w in wafers)
    failing_wafers = sum(1 for w in wafers if w["failing_dies"] > 0)
    return {
        "total_wafers": len(wafers),
        "failing_wafers": failing_wafers,
        "total_dies": total_dies,
        "failing_dies": failing_dies,
        "overall_yield_pct": round(
            (1.0 - failing_dies / max(1, total_dies)) * 100.0, 4
        ),
        "mean_failure_density": round(failing_dies / max(1, total_dies), 6),
        "mean_health_score": round(
            sum(w.get("health_score", 1.0) for w in wafers) / max(1, len(wafers)), 6
        ),
        "mean_confidence": round(
            sum(w.get("confidence_score", 0.0) for w in wafers) / max(1, len(wafers)),
            6,
        ),
        "hotspot_count": len(hotspots),
        "outlier_wafer_count": sum(
            1
            for w in wafers
            if w.get("yield_delta") is not None and abs(w["yield_delta"]) >= 10.0
        ),
    }


def _scoped_statistics(
    wafers: list[dict[str, Any]], hotspots: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rows.append(
        {
            "scope_type": "analysis",
            "scope_key": "all",
            **_statistics(wafers, hotspots),
        }
    )
    by_lot: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for wafer in wafers:
        by_lot[wafer["lot_id"]].append(wafer)
    for lot_id, lot_wafers in sorted(by_lot.items()):
        lot_hotspots = [h for h in hotspots if h["lot_id"] == lot_id]
        stat = _statistics(lot_wafers, lot_hotspots)
        rows.append(
            {
                "scope_type": "lot",
                "scope_key": lot_id,
                "total_wafers": stat["total_wafers"],
                "failing_wafers": stat["failing_wafers"],
                "total_dies": stat["total_dies"],
                "failing_dies": stat["failing_dies"],
                "mean_yield_pct": round(
                    sum(w["yield_pct"] for w in lot_wafers) / max(1, len(lot_wafers)),
                    4,
                ),
                "mean_failure_density": stat["mean_failure_density"],
                "mean_health_score": stat["mean_health_score"],
                "mean_confidence": stat["mean_confidence"],
                "hotspot_count": len(lot_hotspots),
                "details": stat,
            }
        )
    return rows
