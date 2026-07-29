"""
PA-FR-009 Correlation Exporter — orchestrates correlation and writes output artifacts.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from analysis_session import SESSION_EXECUTIONS_JSON, SESSION_MANIFEST_JSON
from ate_log_adapter import parse_ate_log_files
from correlation_config import CorrelationConfig, load_correlation_config
from correlation_manifest import attach_correlation_hash, build_manifest_payload
from pattern_correlator import assign_run_ids, correlate

TOGGLE_COVERAGE_JSON = "PA-FR-004_toggle_coverage.json"
PATTERN_OUTCOME_JSON = "PA-FR-009_pattern_outcome_table.json"
CORRELATION_MANIFEST_JSON = "PA-FR-009_correlation_manifest.json"


class CorrelationAbortedError(RuntimeError):
    """Raised when correlation cannot proceed due to missing prerequisites."""


def _write_json(path: str, payload: Any) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _metadata_rows_from_session_executions(output_dir: str) -> Optional[List[Dict[str, Any]]]:
    """Unique (pattern_id, scan_chain_id) keys from session executions — not FR-004."""
    path = os.path.join(output_dir, SESSION_EXECUTIONS_JSON)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    executions = payload.get("executions")
    if not isinstance(executions, list) or not executions:
        return None
    seen = set()
    rows: List[Dict[str, Any]] = []
    for record in executions:
        pattern_id = str(record.get("pattern_id", ""))
        scan_chain_id = str(record.get("scan_chain_id", ""))
        key = (pattern_id, scan_chain_id)
        if not pattern_id or not scan_chain_id or key in seen:
            continue
        seen.add(key)
        rows.append({"pattern_id": pattern_id, "scan_chain_id": scan_chain_id})
    return rows or None


def load_metadata_rows(output_dir: str) -> List[Dict[str, Any]]:
    # Prefer session executions when present so multi-log does not depend on FR-004.
    session_rows = _metadata_rows_from_session_executions(output_dir)
    if session_rows is not None:
        return session_rows

    coverage_path = os.path.join(output_dir, TOGGLE_COVERAGE_JSON)
    if not os.path.exists(coverage_path):
        raise CorrelationAbortedError(
            f"Missing {TOGGLE_COVERAGE_JSON} and no session executions available. "
            "Run the pipeline through PA-FR-004 or a multi-log Analysis Session first."
        )
    with open(coverage_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    rows = payload.get("scan_chain_level")
    if not isinstance(rows, list) or not rows:
        raise CorrelationAbortedError("PA-FR-004 scan_chain_level metadata is missing or empty.")
    return rows


def _workspace_relative(path: str, workspace_dir: str) -> str:
    absolute = os.path.abspath(path)
    workspace = os.path.abspath(workspace_dir)
    try:
        return os.path.relpath(absolute, workspace).replace("\\", "/")
    except ValueError:
        return os.path.basename(absolute)


def _resolve_logs_from_session_manifest(
    workspace_dir: str,
    output_dir: str,
) -> Optional[List[str]]:
    manifest_path = os.path.join(output_dir, SESSION_MANIFEST_JSON)
    if not os.path.exists(manifest_path):
        return None
    with open(manifest_path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    logs = manifest.get("input_ate_logs")
    if not isinstance(logs, list) or not logs:
        return None
    resolved = []
    for item in logs:
        candidate = item if os.path.isabs(item) else os.path.join(workspace_dir, item)
        if not os.path.exists(candidate):
            raise CorrelationAbortedError(f"ATE log not found: {item}")
        resolved.append(os.path.abspath(candidate))
    return sorted(resolved, key=lambda path: _workspace_relative(path, workspace_dir))


def resolve_ate_log_paths(
    workspace_dir: str,
    requested_paths: Optional[List[str]] = None,
    output_dir: Optional[str] = None,
) -> List[str]:
    if requested_paths:
        resolved = []
        for item in requested_paths:
            candidate = item if os.path.isabs(item) else os.path.join(workspace_dir, item)
            if not os.path.exists(candidate):
                raise CorrelationAbortedError(f"ATE log not found: {item}")
            resolved.append(os.path.abspath(candidate))
        return sorted(resolved, key=lambda path: _workspace_relative(path, workspace_dir))

    if output_dir:
        session_logs = _resolve_logs_from_session_manifest(workspace_dir, output_dir)
        if session_logs:
            return session_logs

        cache_path = os.path.join(output_dir, "PA-FR-005_scan_vector_cache.json")
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as handle:
                cache_payload = json.load(handle)
            ate_log_used = cache_payload.get("ate_log_used")
            if ate_log_used:
                for root, _, files in os.walk(os.path.join(workspace_dir, "ate_log_files")):
                    if ate_log_used in files:
                        return [os.path.abspath(os.path.join(root, ate_log_used))]

    raise CorrelationAbortedError(
        "No ATE log paths provided and no session manifest or cached ate_log_used "
        "path could be resolved."
    )


def run_pattern_correlation(
    output_dir: str,
    workspace_dir: str,
    ate_log_paths: Optional[List[str]] = None,
    input_stil: str = "",
    generated_timestamp: str | None = None,
    config: Optional[CorrelationConfig] = None,
) -> Dict[str, Any]:
    config_path = os.path.join(workspace_dir, "config", "correlation.yaml")
    config = config or load_correlation_config(config_path)

    metadata_rows = load_metadata_rows(output_dir)
    resolved_logs = resolve_ate_log_paths(workspace_dir, ate_log_paths, output_dir=output_dir)
    sorted_rel_logs = sorted(_workspace_relative(path, workspace_dir) for path in resolved_logs)

    adapter_result = parse_ate_log_files(resolved_logs, workspace_dir=workspace_dir)
    normalized_rows = assign_run_ids(adapter_result.rows, sorted_rel_logs)

    result = correlate(metadata_rows, normalized_rows, config)

    patterns = list(result.patterns)

    outcome_payload = {
        "generated_by": "PA-FR-009",
        "correlation_version": 1,
        "patterns": patterns,
    }
    if config.strict_join and result.orphan_ate_rows:
        outcome_payload["orphan_ate_diagnostics"] = result.orphan_ate_rows

    validation_status = "PASSED"
    if config.strict_join and result.unmatched_ate > 0:
        validation_status = "FAILED"

    manifest = build_manifest_payload(
        input_stil=input_stil,
        input_ate_logs=[os.path.basename(path) for path in resolved_logs],
        metadata_rows=result.metadata_rows,
        ate_rows=result.ate_rows,
        matched_rows=result.matched_rows,
        unmatched_metadata=result.unmatched_metadata,
        unmatched_ate=result.unmatched_ate,
        duplicate_histories=result.duplicate_histories,
        validation_status=validation_status,
        generated_timestamp=generated_timestamp,
    )
    manifest = attach_correlation_hash(manifest)

    os.makedirs(output_dir, exist_ok=True)
    _write_json(os.path.join(output_dir, PATTERN_OUTCOME_JSON), outcome_payload)
    if config.export_manifest:
        _write_json(os.path.join(output_dir, CORRELATION_MANIFEST_JSON), manifest)

    return {
        "pattern_outcomes": outcome_payload,
        "manifest": manifest,
        "malformed_row_count": adapter_result.malformed_row_count,
    }


def handle_correlate_pattern_outcomes(
    workspace_dir: str,
    output_dir: str,
    ate_log_paths: Optional[List[str]] = None,
    input_stil: str = "",
) -> Dict[str, Any]:
    return run_pattern_correlation(
        output_dir=output_dir,
        workspace_dir=workspace_dir,
        ate_log_paths=ate_log_paths,
        input_stil=input_stil,
    )
