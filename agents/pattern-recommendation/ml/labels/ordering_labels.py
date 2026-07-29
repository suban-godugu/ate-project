"""Ordering relevance label construction."""

from __future__ import annotations

import pandas as pd


def build_ordering_relevance(features: pd.DataFrame) -> pd.DataFrame:
    """
    Build per-pattern relevance for learning-to-rank.

    Relevance (0-4):
      4: high failed_log_count + HIGH/MEDIUM severity
      3: high failed_log_count
      2: fail_rate above median or severity MEDIUM+
      1: any fail_executions
      0: no failure signal
    """
    rows = features.copy()
    if rows.empty:
        return pd.DataFrame(
            columns=[
                "pattern_id",
                "relevance",
                "failed_log_count",
                "fail_rate",
                "severity_code",
                "primary_lot",
                "group_id",
                "split",
            ]
        )

    fail_log_median = float(rows["failed_log_count"].median())
    fail_rate_median = float(rows["fail_rate"].median())

    def _relevance(row: pd.Series) -> int:
        failed_logs = int(row["failed_log_count"])
        severity = int(row["severity_code"])
        fail_rate = float(row["fail_rate"])
        fail_exec = int(row["fail_executions"])
        high_logs = failed_logs >= max(1, fail_log_median)
        if high_logs and severity >= 2:
            return 4
        if high_logs:
            return 3
        if fail_rate >= fail_rate_median or severity >= 2:
            return 2
        if fail_exec > 0 or failed_logs > 0:
            return 1
        return 0

    rows["relevance"] = rows.apply(_relevance, axis=1)
    # Single global group for overall ranking; lot used for splits.
    rows["group_id"] = 0
    return rows[
        [
            "pattern_id",
            "relevance",
            "failed_log_count",
            "fail_rate",
            "severity_code",
            "primary_lot",
            "group_id",
            "split",
        ]
    ].reset_index(drop=True)


def build_lot_grouped_relevance(features: pd.DataFrame) -> pd.DataFrame:
    """
    Expand to lot-query groups: one row per (lot, pattern) with lot-local relevance.

    Patterns with no lot membership appear once under group 'GLOBAL'.
    """
    records: list[dict[str, object]] = []
    for _, row in features.iterrows():
        lots_raw = str(row.get("affected_lots") or "")
        lots = [part.strip() for part in lots_raw.split(",") if part.strip()]
        if not lots:
            lots = ["GLOBAL"]
        for lot in lots:
            failed_in_lot = 1 if lot in lots and int(row["failed_log_count"]) > 0 else 0
            relevance = 0
            if failed_in_lot and int(row["severity_code"]) >= 2:
                relevance = 4
            elif failed_in_lot:
                relevance = 3
            elif float(row["fail_rate"]) > 0:
                relevance = 2
            elif int(row["fail_executions"]) > 0:
                relevance = 1
            records.append(
                {
                    "pattern_id": row["pattern_id"],
                    "lot_id": lot,
                    "group_id": lot,
                    "relevance": relevance,
                    "primary_lot": row.get("primary_lot", lot),
                    "split": row.get("split", "train"),
                }
            )
    return pd.DataFrame(records)
