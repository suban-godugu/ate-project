"""Shared PA-ML-003 train/inference helpers."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.contracts_003 import DEFAULT_INVESTIGATION_THRESHOLD, INVESTIGATION_DISCLAIMER
from ml.contracts import FAILURE_PREDICTIONS_BY_LOT_JSON, FAILURE_PREDICTIONS_JSON
from ml.contracts_002 import ANOMALY_SCORES_BY_LOT_JSON, ANOMALY_SCORES_JSON


def _utc_now_iso() -> str:
    from datetime import datetime, timezone

    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def build_root_cause_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=200,
                    class_weight="balanced",
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )


def feature_importances_from_model(model: Any) -> List[float]:
    clf = model
    if hasattr(model, "named_steps") and "clf" in model.named_steps:
        clf = model.named_steps["clf"]
    importances = getattr(clf, "feature_importances_", None)
    if importances is None:
        return []
    return [float(value) for value in np.asarray(importances).reshape(-1)]


def write_model_bundle(
    *,
    model_dir: str,
    pipeline: Pipeline,
    schema: Dict[str, Any],
    card: Dict[str, Any],
) -> None:
    os.makedirs(model_dir, exist_ok=True)
    joblib.dump(pipeline, os.path.join(model_dir, "model.joblib"))
    with open(
        os.path.join(model_dir, "feature_schema.json"), "w", encoding="utf-8"
    ) as handle:
        json.dump(schema, handle, indent=2, sort_keys=True)
    with open(os.path.join(model_dir, "model_card.json"), "w", encoding="utf-8") as handle:
        json.dump(card, handle, indent=2, sort_keys=True, allow_nan=False)


def _safe_metric(fn, y_true, y_score_or_pred, **kwargs):
    try:
        value = float(fn(y_true, y_score_or_pred, **kwargs))
    except Exception:
        return None
    if np.isnan(value) or np.isinf(value):
        return None
    return value


def evaluate_classifier(y_true: np.ndarray, y_score: np.ndarray) -> Dict[str, Any]:
    y_pred = (y_score >= 0.5).astype(int)
    positives = int((y_true == 1).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    fnr = (fn / positives) if positives else None
    return {
        "precision": _safe_metric(precision_score, y_true, y_pred, zero_division=0),
        "recall": _safe_metric(recall_score, y_true, y_pred, zero_division=0),
        "f1": _safe_metric(f1_score, y_true, y_pred, zero_division=0),
        "roc_auc": _safe_metric(roc_auc_score, y_true, y_score),
        "pr_auc": _safe_metric(average_precision_score, y_true, y_score),
        "fnr": fnr,
        "positive_count": positives,
        "negative_count": int((y_true == 0).sum()),
    }


def labels_and_groups(bundle: Mapping[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
    labels: List[int] = []
    groups: List[str] = []
    for row in bundle.get("rows") or []:
        if not isinstance(row, Mapping):
            continue
        labels.append(int(row["label"]))
        groups.append(str(row.get("source_lot") or "Ungrouped"))
    return np.asarray(labels, dtype=np.int64), np.asarray(groups)


def _load_json(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else None


def scan_chain_by_pattern(output_dir: str) -> Dict[str, str]:
    """Map pattern_id -> scan_chain_id from correlation outcomes."""
    path = os.path.join(output_dir, "PA-Analysis-Session_correlation.json")
    payload = _load_json(path)
    if not payload:
        return {}
    mapping: Dict[str, str] = {}
    for row in payload.get("outcomes") or []:
        if not isinstance(row, Mapping):
            continue
        pattern_id = str(row.get("pattern_id") or "")
        chain_id = str(row.get("scan_chain_id") or "")
        if pattern_id and chain_id and pattern_id not in mapping:
            mapping[pattern_id] = chain_id
    return mapping


def _index_scores(
    output_dir: str,
    *,
    failure_filename: str,
    anomaly_filename: str,
    score_key: str,
    rows_key: str,
) -> Tuple[Dict[str, float], Dict[str, int]]:
    failure_scores: Dict[str, float] = {}
    anomaly_flags: Dict[str, int] = {}

    failure_payload = _load_json(os.path.join(output_dir, failure_filename))
    if failure_payload:
        for row in failure_payload.get("predictions") or []:
            if isinstance(row, Mapping):
                uid = str(row.get("unit_id") or "")
                if uid:
                    failure_scores[uid] = float(row.get("score") or 0.0)

    anomaly_payload = _load_json(os.path.join(output_dir, anomaly_filename))
    if anomaly_payload:
        for row in anomaly_payload.get("scores") or []:
            if isinstance(row, Mapping):
                uid = str(row.get("unit_id") or "")
                if uid:
                    anomaly_flags[uid] = int(row.get("is_anomaly") or 0)

    _ = score_key
    _ = rows_key
    return failure_scores, anomaly_flags


def advisory_index_log(output_dir: str) -> Tuple[Dict[str, float], Dict[str, int]]:
    return _index_scores(
        output_dir,
        failure_filename=FAILURE_PREDICTIONS_JSON,
        anomaly_filename=ANOMALY_SCORES_JSON,
        score_key="score",
        rows_key="predictions",
    )


def advisory_index_lot(output_dir: str) -> Tuple[Dict[str, float], Dict[str, int]]:
    return _index_scores(
        output_dir,
        failure_filename=FAILURE_PREDICTIONS_BY_LOT_JSON,
        anomaly_filename=ANOMALY_SCORES_BY_LOT_JSON,
        score_key="score",
        rows_key="predictions",
    )


def investigation_score(
    *,
    model_score: float,
    failure_boost: float = 0.0,
    is_anomaly: int = 0,
    actual_fail: bool = False,
) -> float:
    score = float(model_score)
    if failure_boost > 0:
        score = min(1.0, score + 0.1 * failure_boost)
    if int(is_anomaly or 0) == 1:
        score = min(1.0, score + 0.05)
    if actual_fail:
        score = min(1.0, score + 0.15)
    return round(score, 6)


def is_candidate(
    *,
    model_score: float,
    actual_result: str,
    is_anomaly: int,
    threshold: float,
) -> bool:
    if str(actual_result or "").upper() == "FAIL":
        return True
    if float(model_score) >= threshold:
        return True
    if int(is_anomaly or 0) == 1:
        return True
    return False


def build_chain_summaries(
    rankings: Sequence[Mapping[str, Any]],
    *,
    top_n: int = 10,
) -> List[Dict[str, Any]]:
    buckets: Dict[str, Dict[str, Any]] = {}
    for row in rankings:
        chain_id = str(row.get("scan_chain_id") or "Unknown")
        bucket = buckets.setdefault(
            chain_id,
            {
                "scan_chain_id": chain_id,
                "candidate_count": 0,
                "fail_count": 0,
                "max_investigation_score": 0.0,
                "top_pattern_id": "",
            },
        )
        bucket["candidate_count"] += 1
        if str(row.get("actual_result") or "").upper() == "FAIL":
            bucket["fail_count"] += 1
        score = float(row.get("investigation_score") or 0.0)
        if score >= bucket["max_investigation_score"]:
            bucket["max_investigation_score"] = score
            bucket["top_pattern_id"] = str(row.get("pattern_id") or "")
    summaries = list(buckets.values())
    summaries.sort(
        key=lambda item: (
            -int(item.get("fail_count") or 0),
            -float(item.get("max_investigation_score") or 0.0),
            str(item.get("scan_chain_id") or ""),
        )
    )
    for item in summaries:
        item["max_investigation_score"] = round(
            float(item.get("max_investigation_score") or 0.0), 6
        )
    return summaries[:top_n]


def build_rankings_payload(
    *,
    rankings: List[Dict[str, Any]],
    generated_by: str,
    model_family: str,
    grain: str,
    model_version: str,
    feature_schema_version: str,
    session_hash: Optional[str],
    status: Optional[str],
    chain_summaries: List[Dict[str, Any]],
    investigation_threshold: float = DEFAULT_INVESTIGATION_THRESHOLD,
) -> Dict[str, Any]:
    fail_count = sum(
        1 for row in rankings if str(row.get("actual_result") or "").upper() == "FAIL"
    )
    return {
        "generated_by": generated_by,
        "model_family": model_family,
        "grain": grain,
        "model_version": model_version,
        "feature_schema_version": feature_schema_version,
        "session_hash": session_hash,
        "status": status,
        "disclaimer": INVESTIGATION_DISCLAIMER,
        "ranking_count": len(rankings),
        "candidate_count": len(rankings),
        "fail_count": fail_count,
        "investigation_threshold": float(investigation_threshold),
        "rankings": rankings,
        "chain_summaries": chain_summaries,
    }
