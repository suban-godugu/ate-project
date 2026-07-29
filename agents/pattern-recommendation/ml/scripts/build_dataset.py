"""
Build ML feature tables and labels from the existing backend services.

Usage (from project root):
  python -m ml.scripts.build_dataset
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from backend.core.config import get_settings
from backend.services.data_loader import get_data_loader, reset_data_loader
from backend.services.dataset_service import get_dataset_service, reset_dataset_service
from backend.services.ordering_service import get_ordering_service, reset_ordering_service
from backend.services.pattern_feature_builder import (
    get_pattern_feature_builder,
    reset_pattern_feature_builder,
)
from backend.services.redundancy_service import (
    get_redundancy_service,
    reset_redundancy_service,
)
from backend.services.removal_service import get_removal_service, reset_removal_service
from ml.features.schema import SEVERITY_MAP
from ml.labels.ordering_labels import build_lot_grouped_relevance, build_ordering_relevance
from ml.labels.removal_labels import build_removal_labels
from ml.labels.splits import assign_primary_lot, lot_based_split

_LOT_RE = re.compile(r"(LOT_\d+)", re.IGNORECASE)


def _lots_from_paths(paths: list[str]) -> list[str]:
    lots: list[str] = []
    for path in paths:
        match = _LOT_RE.search(str(path).replace("\\", "/"))
        if match:
            lots.append(match.group(1).upper())
    return lots


def _unique_fail_contribution(
    pattern_id: str,
    pattern_logs: set[str],
    representative_id: str,
    pattern_index: dict,
) -> int:
    rep = pattern_index.get(representative_id)
    kept = set(rep.failed_logs) if rep else set()
    return len(pattern_logs - kept)


def build_feature_frame() -> pd.DataFrame:
    settings = get_settings()
    reset_dataset_service()
    reset_data_loader()
    reset_pattern_feature_builder()
    reset_redundancy_service()
    reset_removal_service()
    reset_ordering_service()

    dataset_service = get_dataset_service(settings)
    dataset_service.discover()
    loader = get_data_loader(settings, dataset_service)
    features = get_pattern_feature_builder(loader)
    redundancy = get_redundancy_service(loader, features)
    removal = get_removal_service(settings, loader, features, redundancy)
    ordering = get_ordering_service(settings, loader, features)

    pattern_index = features.get_index()
    redundancy.ensure_built()
    removal.ensure_built()
    ordering.ensure_built()

    cluster_index = redundancy.get_cluster_index()
    red_index = redundancy.get_pattern_index()
    removal_index = {
        row.pattern_id: row for row in removal.get_recommendations().recommendations
    }
    order_index = {row.pattern_id: row for row in ordering.get_ordering().patterns}

    rows: list[dict[str, object]] = []
    for pattern_id, feature in pattern_index.items():
        red = red_index.get(pattern_id)
        rem = removal_index.get(pattern_id)
        ord_row = order_index.get(pattern_id)
        cluster = cluster_index.get(red.cluster_id) if red else None

        lots = _lots_from_paths(list(feature.failed_logs))
        if red and feature.failed_logs:
            unique = _unique_fail_contribution(
                pattern_id,
                set(feature.failed_logs),
                red.representative_pattern,
                pattern_index,
            )
        else:
            unique = 0

        # Match removal_service normalization fields when available.
        norm_unique = (
            float(rem.normalized_unique_fail_contribution) if rem else 0.0
        )
        norm_toggle = float(rem.normalized_toggle_coverage) if rem else 0.0
        heuristic_removal = float(rem.removal_priority) if rem else 0.0
        heuristic_order = float(ord_row.order_score) if ord_row else 0.0

        primary = assign_primary_lot(lots)
        rows.append(
            {
                "pattern_id": pattern_id,
                "fail_rate": float(feature.fail_rate),
                "severity": feature.severity,
                "severity_code": SEVERITY_MAP.get(str(feature.severity), 0),
                "mean_toggle_coverage": float(feature.mean_toggle_coverage),
                "mean_toggle_density": float(feature.mean_toggle_density),
                "mean_toggle_count": float(feature.mean_toggle_count),
                "coverage_percent": float(feature.coverage_percent),
                "failed_log_count": len(feature.failed_logs),
                "failed_chain_count": len(feature.failed_chains),
                "total_executions": int(feature.total_executions),
                "fail_executions": int(feature.fail_executions),
                "similarity_to_representative": float(
                    red.similarity_to_representative if red else 0.0
                ),
                "cluster_size": int(cluster.cluster_size) if cluster else 1,
                "is_representative": int(bool(red and red.is_representative)),
                "redundant_flag": int(bool(red and red.redundant_flag)),
                "unique_fail_contribution": int(
                    rem.unique_fail_contribution if rem is not None else unique
                ),
                "normalized_unique_fail_contribution": norm_unique,
                "normalized_toggle_coverage": norm_toggle,
                "heuristic_removal_priority": heuristic_removal,
                "heuristic_order_score": heuristic_order,
                "cluster_id": red.cluster_id if red else "",
                "representative_pattern": (
                    red.representative_pattern if red else pattern_id
                ),
                "affected_lots": ",".join(sorted(set(lots))),
                "primary_lot": primary,
            }
        )

    frame = pd.DataFrame(rows)
    frame = lot_based_split(frame, lot_column="primary_lot")
    return frame


def heuristic_baseline_metrics(features: pd.DataFrame, removal_labels: pd.DataFrame) -> dict:
    """Compute simple heuristic baselines for comparison reports."""
    metrics: dict[str, object] = {"n_patterns": int(len(features))}

    # Removal: precision if we take heuristic priority >= median as predicted remove
    if not removal_labels.empty:
        merged = removal_labels.merge(
            features[["pattern_id", "heuristic_removal_priority"]],
            on="pattern_id",
            how="left",
        )
        median_p = float(merged["heuristic_removal_priority"].median())
        pred = (merged["heuristic_removal_priority"] >= median_p).astype(int)
        true = merged["label"].astype(int)
        tp = int(((pred == 1) & (true == 1)).sum())
        fp = int(((pred == 1) & (true == 0)).sum())
        metrics["removal_heuristic_precision_at_median"] = (
            round(tp / (tp + fp), 6) if (tp + fp) else 0.0
        )
        metrics["removal_positive_rate"] = round(float(true.mean()), 6)

    # Ordering: early-fail mass in top-50 by heuristic_order_score
    ranked = features.sort_values(
        ["heuristic_order_score", "pattern_id"], ascending=[False, True]
    )
    top50 = ranked.head(50)
    total_fail_logs = float(features["failed_log_count"].sum()) or 1.0
    metrics["ordering_heuristic_early_fail_mass_top50"] = round(
        float(top50["failed_log_count"].sum()) / total_fail_logs, 6
    )
    return metrics


def main() -> None:
    data_dir = _PROJECT_ROOT / "ml" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    print("Building feature frame from backend services…")
    features = build_feature_frame()
    features_path = data_dir / "pattern_features.csv"
    features.to_csv(features_path, index=False)
    print(f"Wrote {features_path} rows={len(features)}")

    removal_labels = build_removal_labels(features)
    removal_path = data_dir / "removal_labels.csv"
    removal_labels.to_csv(removal_path, index=False)
    print(f"Wrote {removal_path} rows={len(removal_labels)}")

    ordering_labels = build_ordering_relevance(features)
    ordering_path = data_dir / "ordering_relevance.csv"
    ordering_labels.to_csv(ordering_path, index=False)
    print(f"Wrote {ordering_path} rows={len(ordering_labels)}")

    lot_grouped = build_lot_grouped_relevance(features)
    lot_path = data_dir / "ordering_relevance_by_lot.csv"
    lot_grouped.to_csv(lot_path, index=False)
    print(f"Wrote {lot_path} rows={len(lot_grouped)}")

    baselines = heuristic_baseline_metrics(features, removal_labels)
    split_counts = features["split"].value_counts().to_dict()
    lot_counts = features["primary_lot"].value_counts().to_dict()
    report = {
        "baselines": baselines,
        "split_counts": split_counts,
        "primary_lot_counts": lot_counts,
        "removal_label_counts": removal_labels["label"].value_counts().to_dict()
        if not removal_labels.empty
        else {},
    }
    report_path = data_dir / "dataset_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {report_path}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
