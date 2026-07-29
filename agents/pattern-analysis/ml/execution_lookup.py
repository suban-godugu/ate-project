"""Shared execution outcome lookup by log or LOT grain."""
from __future__ import annotations

import json
import os
from typing import Dict, Mapping

from ml.feature_builder_001_lot import lot_unit_id

from robustness_config import (
    load_robustness_config,
    lot_from_relpath,
    normalize_execution_result,
)


def load_execution_results_by_log(output_dir: str) -> Dict[str, str]:
    workspace_dir = os.path.dirname(output_dir)
    robustness_cfg = load_robustness_config(workspace_dir)
    path = os.path.join(output_dir, "PA-Analysis-Session_executions.json")
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    results: Dict[str, str] = {}
    for row in payload.get("executions") or []:
        if not isinstance(row, Mapping):
            continue
        pattern_id = str(row.get("pattern_id") or "")
        relpath = str(row.get("source_log_relpath") or "")
        source_log = str(row.get("source_log") or "")
        uid = f"{pattern_id}::{relpath or source_log}"
        results[uid] = normalize_execution_result(
            row.get("latest_result"), config=robustness_cfg
        )
    return results


def load_execution_results_by_lot(output_dir: str) -> Dict[str, str]:
    """Aggregate executions to pattern×LOT; any FAIL in the LOT wins."""
    workspace_dir = os.path.dirname(output_dir)
    robustness_cfg = load_robustness_config(workspace_dir)
    path = os.path.join(output_dir, "PA-Analysis-Session_executions.json")
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    has_fail: Dict[str, bool] = {}
    has_pass: Dict[str, bool] = {}
    for row in payload.get("executions") or []:
        if not isinstance(row, Mapping):
            continue
        pattern_id = str(row.get("pattern_id") or "")
        relpath = str(row.get("source_log_relpath") or "")
        source_log = str(row.get("source_log") or "")
        source_lot = str(
            row.get("source_lot")
            or lot_from_relpath(relpath or source_log, config=robustness_cfg)
        )
        uid = lot_unit_id(pattern_id, source_lot)
        if uid not in has_fail:
            has_fail[uid] = False
            has_pass[uid] = False

        canonical = normalize_execution_result(
            row.get("latest_result"), config=robustness_cfg
        )
        if canonical == "FAIL":
            has_fail[uid] = True
        elif canonical == "PASS":
            has_pass[uid] = True

    return {
        uid: ("FAIL" if failed else ("PASS" if has_pass.get(uid) else "UNKNOWN"))
        for uid, failed in has_fail.items()
    }
