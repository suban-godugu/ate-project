"""Classification / prediction metric computation for AI evaluation."""

from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np


def compute_classification_metrics(
    y_true: list[str],
    y_pred: list[str],
    *,
    confidences: list[float] | None = None,
) -> dict[str, Any]:
    """Compute accuracy, precision, recall, F1, confusion matrix, ROC-AUC (binary/OVR)."""
    if not y_true or not y_pred or len(y_true) != len(y_pred):
        return {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "roc_auc": None,
            "confusion_matrix": {},
            "sample_count": 0,
            "prediction_confidence_mean": 0.0,
        }

    labels = sorted(set(y_true) | set(y_pred))
    label_index = {label: idx for idx, label in enumerate(labels)}
    matrix = np.zeros((len(labels), len(labels)), dtype=int)
    for truth, pred in zip(y_true, y_pred):
        matrix[label_index[truth], label_index[pred]] += 1

    accuracy = float(np.mean([t == p for t, p in zip(y_true, y_pred)]))
    per_class_precision: list[float] = []
    per_class_recall: list[float] = []
    per_class_f1: list[float] = []

    for idx, _label in enumerate(labels):
        tp = float(matrix[idx, idx])
        fp = float(matrix[:, idx].sum() - tp)
        fn = float(matrix[idx, :].sum() - tp)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall)
            else 0.0
        )
        per_class_precision.append(precision)
        per_class_recall.append(recall)
        per_class_f1.append(f1)

    roc_auc = _ovr_roc_auc(y_true, y_pred, labels, confidences)
    conf_mean = float(np.mean(confidences)) if confidences else 0.0

    return {
        "accuracy": round(accuracy, 6),
        "precision": round(float(np.mean(per_class_precision)), 6),
        "recall": round(float(np.mean(per_class_recall)), 6),
        "f1_score": round(float(np.mean(per_class_f1)), 6),
        "roc_auc": None if roc_auc is None else round(roc_auc, 6),
        "confusion_matrix": {
            "labels": labels,
            "matrix": matrix.tolist(),
        },
        "sample_count": len(y_true),
        "prediction_confidence_mean": round(conf_mean, 6),
        "label_distribution": dict(Counter(y_true)),
    }


def engineering_score(metrics: dict[str, Any], *, weights: dict[str, float] | None = None) -> float:
    """Composite engineering score in [0, 1]."""
    weights = weights or {
        "accuracy": 0.30,
        "f1_score": 0.30,
        "precision": 0.15,
        "recall": 0.15,
        "prediction_confidence_mean": 0.10,
    }
    score = 0.0
    total_w = 0.0
    for key, weight in weights.items():
        value = metrics.get(key)
        if value is None:
            continue
        score += weight * float(value)
        total_w += weight
    if total_w <= 0:
        return 0.0
    return round(score / total_w, 6)


def similarity_accuracy(
    retrieved_relevant: int,
    retrieved_total: int,
) -> float:
    if retrieved_total <= 0:
        return 0.0
    return round(retrieved_relevant / retrieved_total, 6)


def recommendation_accuracy(
    recommendations: list[dict[str, Any]],
    *,
    min_priority: str = "MEDIUM",
) -> float:
    if not recommendations:
        return 0.0
    order = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "LOW": 0}
    threshold = order.get(min_priority, 1)
    actionable = [
        r
        for r in recommendations
        if order.get(str(r.get("priority", "LOW")).upper(), 0) >= threshold
        and r.get("action")
    ]
    return round(len(actionable) / len(recommendations), 6)


def _ovr_roc_auc(
    y_true: list[str],
    y_pred: list[str],
    labels: list[str],
    confidences: list[float] | None,
) -> float | None:
    if confidences is None or len(set(y_true)) < 2:
        return None
    try:
        from sklearn.metrics import roc_auc_score
        from sklearn.preprocessing import label_binarize
    except ImportError:
        return None

    y_bin = label_binarize(y_true, classes=labels)
    # Approximate score matrix from predicted class + confidence
    scores = np.zeros((len(y_true), len(labels)), dtype=float)
    label_index = {label: idx for idx, label in enumerate(labels)}
    for i, (pred, conf) in enumerate(zip(y_pred, confidences)):
        idx = label_index.get(pred)
        if idx is None:
            continue
        scores[i, idx] = float(conf)
        remainder = max(0.0, 1.0 - float(conf))
        others = [j for j in range(len(labels)) if j != idx]
        if others:
            share = remainder / len(others)
            for j in others:
                scores[i, j] = share

    try:
        if y_bin.shape[1] == 1:
            return float(roc_auc_score(y_bin.ravel(), scores.ravel()))
        return float(roc_auc_score(y_bin, scores, multi_class="ovr", average="macro"))
    except ValueError:
        return None
