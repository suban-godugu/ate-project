"""PA-ML-004 fusion helpers — merge 001/002/003 into ranked recommendations."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Mapping, Optional, Tuple

from ml.contracts import FAILURE_PREDICTIONS_BY_LOT_JSON, FAILURE_PREDICTIONS_JSON
from ml.contracts_002 import ANOMALY_SCORES_BY_LOT_JSON, ANOMALY_SCORES_JSON
from ml.contracts_003 import (
    ROOT_CAUSE_RANKINGS_BY_LOT_JSON,
    ROOT_CAUSE_RANKINGS_JSON,
)
from ml.contracts_004 import (
    DEFAULT_WEIGHTS,
    RECOMMENDATION_DISCLAIMER,
    TIER_HIGH,
    TIER_MEDIUM,
)
from ml.root_cause_common import scan_chain_by_pattern


def _load_json(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else None


def _session_hash_from_artifacts(
    *payloads: Optional[Mapping[str, Any]],
) -> Optional[str]:
    for payload in payloads:
        if isinstance(payload, Mapping) and payload.get("session_hash"):
            return str(payload.get("session_hash"))
    return None


def artifact_filenames_for_grain(
    grain: str,
) -> Tuple[str, str, str]:
    if grain == "pattern_x_lot":
        return (
            FAILURE_PREDICTIONS_BY_LOT_JSON,
            ANOMALY_SCORES_BY_LOT_JSON,
            ROOT_CAUSE_RANKINGS_BY_LOT_JSON,
        )
    return (
        FAILURE_PREDICTIONS_JSON,
        ANOMALY_SCORES_JSON,
        ROOT_CAUSE_RANKINGS_JSON,
    )


def load_upstream_artifacts(
    output_dir: str,
    *,
    grain: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    failure_name, anomaly_name, root_cause_name = artifact_filenames_for_grain(grain)
    return (
        _load_json(os.path.join(output_dir, failure_name)),
        _load_json(os.path.join(output_dir, anomaly_name)),
        _load_json(os.path.join(output_dir, root_cause_name)),
    )


def _index_predictions(payload: Optional[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    indexed: Dict[str, Dict[str, Any]] = {}
    if not isinstance(payload, Mapping):
        return indexed
    for row in payload.get("predictions") or []:
        if isinstance(row, Mapping):
            uid = str(row.get("unit_id") or "")
            if uid:
                indexed[uid] = dict(row)
    return indexed


def _index_scores(payload: Optional[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    indexed: Dict[str, Dict[str, Any]] = {}
    if not isinstance(payload, Mapping):
        return indexed
    for row in payload.get("scores") or []:
        if isinstance(row, Mapping):
            uid = str(row.get("unit_id") or "")
            if uid:
                indexed[uid] = dict(row)
    return indexed


def _index_rankings(payload: Optional[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    indexed: Dict[str, Dict[str, Any]] = {}
    if not isinstance(payload, Mapping):
        return indexed
    for row in payload.get("rankings") or []:
        if isinstance(row, Mapping):
            uid = str(row.get("unit_id") or "")
            if uid:
                indexed[uid] = dict(row)
    return indexed


def merge_unit_ids(
    failure: Mapping[str, Mapping[str, Any]],
    anomaly: Mapping[str, Mapping[str, Any]],
    root_cause: Mapping[str, Mapping[str, Any]],
) -> List[str]:
    unit_ids = set(failure) | set(anomaly) | set(root_cause)
    return sorted(unit_ids)


def priority_tier(
    score: float,
    *,
    tier_thresholds: Optional[Mapping[str, float]] = None,
) -> str:
    high = float((tier_thresholds or {}).get("high", TIER_HIGH))
    medium = float((tier_thresholds or {}).get("medium", TIER_MEDIUM))
    if score >= high:
        return "HIGH"
    if score >= medium:
        return "MEDIUM"
    return "LOW"


def compute_priority_score(
    *,
    failure_score: float,
    anomaly_score: float,
    investigation_score: float,
    actual_result: str,
    weights: Mapping[str, float],
) -> float:
    fail_obs = 1.0 if str(actual_result or "").upper() == "FAIL" else 0.0
    score = (
        float(weights.get("w_failure", DEFAULT_WEIGHTS["w_failure"])) * failure_score
        + float(weights.get("w_anomaly", DEFAULT_WEIGHTS["w_anomaly"])) * anomaly_score
        + float(weights.get("w_rootcause", DEFAULT_WEIGHTS["w_rootcause"]))
        * investigation_score
        + float(weights.get("w_fail_obs", DEFAULT_WEIGHTS["w_fail_obs"])) * fail_obs
    )
    return round(min(1.0, max(0.0, score)), 6)


def recommended_action(
    *,
    failure_score: float,
    anomaly_score: float,
    investigation_score: float,
    is_anomaly: int,
    actual_result: str,
) -> str:
    if str(actual_result or "").upper() == "FAIL":
        return "INVESTIGATE_FAIL"
    weighted = {
        "INVESTIGATE_FAIL": failure_score,
        "REVIEW_ANOMALY": anomaly_score + (0.25 if int(is_anomaly or 0) == 1 else 0.0),
        "PRIORITIZE_ROOT_CAUSE": investigation_score,
    }
    top_action = max(weighted.items(), key=lambda item: (item[1], item[0]))[0]
    if weighted[top_action] < 0.35:
        return "MONITOR"
    return top_action


def build_rationale(
    *,
    failure_score: float,
    anomaly_score: float,
    investigation_score: float,
    investigation_rank: Optional[int],
    is_anomaly: int,
    actual_result: str,
    hypothesis_tags: Optional[List[str]],
    recommended: str,
) -> List[str]:
    rationale: List[str] = []
    if str(actual_result or "").upper() == "FAIL":
        rationale.append("Observed FAIL")
    if failure_score >= 0.5:
        rationale.append("High failure risk")
    if int(is_anomaly or 0) == 1:
        rationale.append("Anomaly flagged")
    elif anomaly_score >= 0.5:
        rationale.append("Elevated anomaly score")
    if investigation_score >= 0.5:
        rationale.append("Top root-cause candidate")
    if investigation_rank is not None and int(investigation_rank) <= 10:
        rationale.append(f"Root-cause rank #{int(investigation_rank)}")
    for tag in hypothesis_tags or []:
        text = str(tag).replace("_", " ").strip()
        if text and text not in rationale:
            rationale.append(text.title())
    if recommended == "MONITOR" and not rationale:
        rationale.append("Elevated composite priority")
    return rationale[:8]


def build_recommendations(
    *,
    output_dir: str,
    grain: str,
    execution_results: Mapping[str, str],
    policy: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    failure_payload, anomaly_payload, root_cause_payload = load_upstream_artifacts(
        output_dir, grain=grain
    )
    failure_index = _index_predictions(failure_payload)
    anomaly_index = _index_scores(anomaly_payload)
    root_cause_index = _index_rankings(root_cause_payload)
    unit_ids = merge_unit_ids(failure_index, anomaly_index, root_cause_index)
    if not unit_ids:
        return []

    weights = policy.get("weights") if isinstance(policy.get("weights"), Mapping) else {}
    tier_thresholds = (
        policy.get("tier_thresholds")
        if isinstance(policy.get("tier_thresholds"), Mapping)
        else {}
    )
    chain_map = scan_chain_by_pattern(output_dir)
    recommendations: List[Dict[str, Any]] = []

    for uid in unit_ids:
        failure_row = failure_index.get(uid) or {}
        anomaly_row = anomaly_index.get(uid) or {}
        root_row = root_cause_index.get(uid) or {}

        failure_score = float(failure_row.get("score") or 0.0)
        anomaly_score = float(anomaly_row.get("anomaly_score") or 0.0)
        is_anomaly = int(anomaly_row.get("is_anomaly") or 0)
        investigation_score = float(root_row.get("investigation_score") or 0.0)
        investigation_rank = root_row.get("investigation_rank")
        actual_result = str(
            root_row.get("actual_result")
            or execution_results.get(uid)
            or ""
        )
        pattern_id = str(
            root_row.get("pattern_id")
            or failure_row.get("pattern_id")
            or anomaly_row.get("pattern_id")
            or ""
        )

        priority_score = compute_priority_score(
            failure_score=failure_score,
            anomaly_score=anomaly_score,
            investigation_score=investigation_score,
            actual_result=actual_result,
            weights=weights,
        )
        action = recommended_action(
            failure_score=failure_score,
            anomaly_score=anomaly_score,
            investigation_score=investigation_score,
            is_anomaly=is_anomaly,
            actual_result=actual_result,
        )
        tags = root_row.get("hypothesis_tags")
        hypothesis_tags = tags if isinstance(tags, list) else []

        entry: Dict[str, Any] = {
            "unit_id": uid,
            "pattern_id": pattern_id,
            "scan_chain_id": chain_map.get(pattern_id, ""),
            "priority_score": priority_score,
            "priority_tier": priority_tier(
                priority_score, tier_thresholds=tier_thresholds
            ),
            "recommended_action": action,
            "actual_result": actual_result,
            "signals": {
                "failure_score": round(failure_score, 6),
                "anomaly_score": round(anomaly_score, 6),
                "is_anomaly": is_anomaly,
                "investigation_score": round(investigation_score, 6),
                "investigation_rank": investigation_rank,
            },
            "rationale": build_rationale(
                failure_score=failure_score,
                anomaly_score=anomaly_score,
                investigation_score=investigation_score,
                investigation_rank=(
                    int(investigation_rank) if investigation_rank is not None else None
                ),
                is_anomaly=is_anomaly,
                actual_result=actual_result,
                hypothesis_tags=hypothesis_tags,
                recommended=action,
            ),
        }
        for key in (
            "source_log",
            "source_log_relpath",
            "source_lot",
            "log_count_in_lot",
        ):
            value = root_row.get(key) or failure_row.get(key) or anomaly_row.get(key)
            if value is not None:
                entry[key] = value
        recommendations.append(entry)

    recommendations.sort(
        key=lambda item: (
            -float(item.get("priority_score") or 0.0),
            str(item.get("unit_id") or ""),
        )
    )
    for rank, entry in enumerate(recommendations, start=1):
        entry["recommendation_rank"] = rank
    return recommendations


def build_recommendations_payload(
    *,
    recommendations: List[Dict[str, Any]],
    generated_by: str,
    model_family: str,
    grain: str,
    model_version: str,
    policy_version: str,
    session_hash: Optional[str],
    status: Optional[str],
) -> Dict[str, Any]:
    high_count = sum(
        1 for row in recommendations if str(row.get("priority_tier") or "") == "HIGH"
    )
    return {
        "generated_by": generated_by,
        "model_family": model_family,
        "grain": grain,
        "model_version": model_version,
        "policy_version": policy_version,
        "session_hash": session_hash,
        "status": status,
        "disclaimer": RECOMMENDATION_DISCLAIMER,
        "recommendation_count": len(recommendations),
        "high_priority_count": high_count,
        "recommendations": recommendations,
    }
