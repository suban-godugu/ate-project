"""Lot-based train/val/test split helpers."""

from __future__ import annotations

from collections import Counter

import pandas as pd


def assign_primary_lot(affected_lots: list[str] | str | None) -> str:
    if affected_lots is None:
        return "UNKNOWN"
    if isinstance(affected_lots, str):
        lots = [part.strip() for part in affected_lots.split(",") if part.strip()]
    else:
        lots = [str(lot).strip() for lot in affected_lots if str(lot).strip()]
    if not lots:
        return "UNKNOWN"
    # Prefer the most frequent lot token; stable tie-break by name.
    counts = Counter(lots)
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def lot_based_split(
    frame: pd.DataFrame,
    *,
    lot_column: str = "primary_lot",
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
) -> pd.DataFrame:
    """
    Assign split by unique lots (not random rows).

    Sorted lot names determine deterministic assignment.
    """
    out = frame.copy()
    lots = sorted({str(lot) for lot in out[lot_column].fillna("UNKNOWN").unique()})
    n = len(lots)
    if n == 0:
        out["split"] = "train"
        return out

    n_train = max(1, int(round(n * train_ratio)))
    n_val = max(0, int(round(n * val_ratio)))
    if n_train + n_val >= n:
        n_val = max(0, n - n_train - 1) if n > n_train else 0
    n_test = n - n_train - n_val

    # Ensure at least one test lot when possible.
    if n_test == 0 and n_val > 0 and n > 2:
        n_val -= 1
        n_test = 1
    if n_test == 0 and n_train > 1 and n > 1:
        n_train -= 1
        n_test = 1

    train_lots = set(lots[:n_train])
    val_lots = set(lots[n_train : n_train + n_val])
    test_lots = set(lots[n_train + n_val :])

    def _split_for(lot: object) -> str:
        name = str(lot)
        if name in train_lots:
            return "train"
        if name in val_lots:
            return "val"
        return "test"

    out["split"] = out[lot_column].map(_split_for)
    return out
