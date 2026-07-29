"""Statistical correlation methods for FA-FR-006."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from itertools import combinations
from typing import Any

import numpy as np

try:
    from scipy import stats as scipy_stats

    SCIPY_AVAILABLE = True
except ImportError:  # pragma: no cover
    SCIPY_AVAILABLE = False


def build_feature_table(failure_rows: list[dict[str, Any]]) -> dict[str, list[Any]]:
    """Engineer tabular features from normalized failure rows."""
    table: dict[str, list[Any]] = defaultdict(list)
    for row in failure_rows:
        table["failure_indicator"].append(1)
        table["pattern_id"].append(str(row.get("pattern_id", "UNKNOWN")))
        table["tester"].append(str(row.get("tester_id", "UNKNOWN")))
        table["product"].append(str(row.get("product_id", "UNKNOWN")))
        table["wafer"].append(str(row.get("wafer_id", "UNKNOWN")))
        table["die"].append(str(row.get("die_id", "UNKNOWN")))
        table["lot"].append(str(row.get("lot_id", "UNKNOWN")))
        table["equipment"].append(str(row.get("equipment_id", "UNKNOWN")))
        table["machine"].append(str(row.get("machine_id", "UNKNOWN")))
        table["operator"].append(str(row.get("operator_id", "UNKNOWN")))
        table["temperature"].append(_to_float(row.get("temperature")))
        table["voltage"].append(_to_float(row.get("voltage")))
        table["process_step"].append(str(row.get("process_step", "UNKNOWN")))
        table["shift"].append(str(row.get("shift", "UNKNOWN")))
    return dict(table)


def compute_correlation_matrix(
    feature_table: dict[str, list[Any]],
    *,
    threshold: float = 0.35,
) -> dict[str, Any]:
    """Pearson + Spearman matrix for numeric columns; chi-square for categoricals."""
    numeric_cols = ["failure_indicator", "temperature", "voltage"]
    categorical_cols = [
        c
        for c in (
            "tester",
            "product",
            "wafer",
            "die",
            "lot",
            "equipment",
            "machine",
            "operator",
            "process_step",
            "shift",
            "pattern_id",
        )
        if c in feature_table
    ]

    pearson: dict[str, dict[str, float]] = {}
    spearman: dict[str, dict[str, float]] = {}
    chi_square: list[dict[str, Any]] = []

    for col in numeric_cols:
        if col not in feature_table:
            continue
        pearson[col] = {}
        spearman[col] = {}
        values = np.array([_to_float(v) for v in feature_table[col]], dtype=float)
        for other in numeric_cols:
            if other not in feature_table:
                continue
            other_values = np.array(
                [_to_float(v) for v in feature_table[other]], dtype=float
            )
            pearson[col][other] = _pearson(values, other_values)
            spearman[col][other] = _spearman(values, other_values)

    for col in categorical_cols:
        chi = _chi_square_vs_failure(feature_table, col)
        if chi["p_value"] is not None and chi["correlation_score"] >= threshold:
            chi_square.append(chi)

    chi_square.sort(key=lambda r: r["correlation_score"], reverse=True)
    significant_pairs = _significant_pairs(pearson, spearman, threshold)

    return {
        "pearson": pearson,
        "spearman": spearman,
        "chi_square": chi_square[:50],
        "significant_pairs": significant_pairs[:100],
        "correlation_threshold": threshold,
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
    }


def mine_association_rules(
    feature_table: dict[str, list[Any]],
    *,
    min_support: float = 0.05,
    min_confidence: float = 0.60,
) -> list[dict[str, Any]]:
    """Simple association-rule mining across categorical manufacturing variables."""
    n = len(feature_table.get("failure_indicator", []))
    if n == 0:
        return []

    categorical_cols = [
        "tester",
        "product",
        "lot",
        "equipment",
        "machine",
        "operator",
        "process_step",
        "shift",
        "pattern_id",
    ]
    transactions: list[set[str]] = []
    for idx in range(n):
        itemset = set()
        for col in categorical_cols:
            if col not in feature_table:
                continue
            value = str(feature_table[col][idx])
            itemset.add(f"{col}={value}")
        transactions.append(itemset)

    rules: list[dict[str, Any]] = []
    item_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str]] = Counter()

    for txn in transactions:
        for item in txn:
            item_counts[item] += 1
        for a, b in combinations(sorted(txn), 2):
            pair_counts[(a, b)] += 1

    for (antecedent, consequent), pair_count in pair_counts.items():
        support = pair_count / n
        if support < min_support:
            continue
        ant_count = item_counts[antecedent]
        confidence = pair_count / ant_count if ant_count else 0.0
        if confidence < min_confidence:
            continue
        lift = confidence / (item_counts[consequent] / n) if item_counts[consequent] else 0.0
        rules.append(
            {
                "antecedent": antecedent,
                "consequent": consequent,
                "support": round(support, 4),
                "confidence": round(confidence, 4),
                "lift": round(lift, 4),
            }
        )

    rules.sort(key=lambda r: (r["lift"], r["confidence"]), reverse=True)
    return rules[:50]


def dimension_correlations(
    feature_table: dict[str, list[Any]],
    *,
    threshold: float = 0.35,
) -> dict[str, Any]:
    """Per-dimension correlation strength with failure indicator."""
    results: dict[str, Any] = {}
    n = len(feature_table.get("failure_indicator", []))
    if n == 0:
        return results

    for dim in (
        "tester",
        "product",
        "wafer",
        "die",
        "lot",
        "equipment",
        "machine",
        "operator",
        "temperature",
        "voltage",
        "process_step",
        "shift",
    ):
        if dim not in feature_table:
            continue
        if dim in ("temperature", "voltage"):
            values = np.array([_to_float(v) for v in feature_table[dim]], dtype=float)
            failures = np.ones(n, dtype=float)
            score = abs(_pearson(values, failures))
            method = "pearson"
        else:
            chi = _chi_square_vs_failure(feature_table, dim)
            score = chi["correlation_score"]
            method = "chi_square"

        if score >= threshold:
            results[dim] = {
                "dimension": dim,
                "method": method,
                "correlation_score": round(score, 4),
                "significant": True,
            }
    return results


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 2 or np.std(a) == 0 or np.std(b) == 0:
        return 0.0
    if SCIPY_AVAILABLE:
        coef, _ = scipy_stats.pearsonr(a, b)
        return round(float(coef), 4) if not math.isnan(coef) else 0.0
    return round(float(np.corrcoef(a, b)[0, 1]), 4)


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 2:
        return 0.0
    if SCIPY_AVAILABLE:
        coef, _ = scipy_stats.spearmanr(a, b)
        return round(float(coef), 4) if not math.isnan(coef) else 0.0
    rank_a = np.argsort(np.argsort(a))
    rank_b = np.argsort(np.argsort(b))
    return _pearson(rank_a.astype(float), rank_b.astype(float))


def _chi_square_vs_failure(
    feature_table: dict[str, list[Any]],
    column: str,
) -> dict[str, Any]:
    values = feature_table.get(column, [])
    n = len(values)
    if n == 0:
        return {"column": column, "correlation_score": 0.0, "p_value": None}

    counts: Counter[str] = Counter(str(v) for v in values)
    total = sum(counts.values())
    expected = total / max(len(counts), 1)
    chi_stat = sum(((c - expected) ** 2) / max(expected, 1e-6) for c in counts.values())
    dof = max(len(counts) - 1, 1)
    p_value = None
    if SCIPY_AVAILABLE:
        p_value = float(scipy_stats.chi2.sf(chi_stat, dof))

    score = min(1.0, chi_stat / (chi_stat + dof))
    return {
        "column": column,
        "chi_square": round(chi_stat, 4),
        "degrees_of_freedom": dof,
        "p_value": round(p_value, 6) if p_value is not None else None,
        "correlation_score": round(score, 4),
        "top_values": counts.most_common(5),
    }


def _significant_pairs(
    pearson: dict[str, dict[str, float]],
    spearman: dict[str, dict[str, float]],
    threshold: float,
) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for method_name, matrix in (("pearson", pearson), ("spearman", spearman)):
        for a, row in matrix.items():
            for b, score in row.items():
                if a >= b:
                    continue
                key = (a, b)
                if key in seen:
                    continue
                if abs(score) >= threshold:
                    seen.add(key)
                    pairs.append(
                        {
                            "left": a,
                            "right": b,
                            "method": method_name,
                            "correlation_score": score,
                        }
                    )
    pairs.sort(key=lambda p: abs(p["correlation_score"]), reverse=True)
    return pairs


def _to_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
