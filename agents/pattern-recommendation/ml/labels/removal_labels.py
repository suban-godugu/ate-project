"""Removal label construction rules."""

from __future__ import annotations

import pandas as pd


def build_removal_labels(features: pd.DataFrame) -> pd.DataFrame:
    """
    Build removal labels for redundant non-representative candidates.

    Stronger rule:
      unique_fail_contribution == 0 → label 1 (safe remove)
      unique_fail_contribution > 0  → label 0 (keep)

    Weak bootstrap:
      heuristic_removal_priority >= median among candidates → weak_label 1
    """
    candidates = features[
        (features["redundant_flag"] == 1) & (features["is_representative"] == 0)
    ].copy()
    if candidates.empty:
        return pd.DataFrame(
            columns=[
                "pattern_id",
                "label",
                "weak_label",
                "unique_fail_contribution",
                "primary_lot",
                "split",
            ]
        )

    candidates["label"] = (candidates["unique_fail_contribution"] <= 0).astype(int)
    median_priority = float(candidates["heuristic_removal_priority"].median())
    candidates["weak_label"] = (
        candidates["heuristic_removal_priority"] >= median_priority
    ).astype(int)

    return candidates[
        [
            "pattern_id",
            "label",
            "weak_label",
            "unique_fail_contribution",
            "primary_lot",
            "split",
        ]
    ].reset_index(drop=True)
