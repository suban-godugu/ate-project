"""
PA-FR-007 Redundancy Exporter — JSON/CSV output generation and pipeline orchestration.
"""
from __future__ import annotations

import csv
import json
import logging
import os
import shutil
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from cluster_engine import ClusteringAbortedError
from redundancy_audit import build_redundancy_audit_entries
from redundancy_engine import (
    RedundancyAbortedError,
    load_redundancy_config,
    run_redundancy_engine,
)
from redundancy_manifest import build_redundancy_manifest_payload
from redundancy_validator import validate_redundancy_result

REDUNDANCY_CANDIDATES_JSON = "PA-FR-007_redundancy_candidates.json"
REDUNDANCY_CANDIDATES_CSV = "PA-FR-007_redundancy_candidates.csv"
FILE_ROLLUP_JSON = "PA-FR-007_file_rollup.json"
VALIDATION_REPORT_JSON = "PA-FR-007_validation_report.json"
REDUNDANCY_MANIFEST_JSON = "PA-FR-007_redundancy_manifest.json"
AUDIT_LOG_JSON = "PA-FR-007_audit_log.json"
LOG_FILENAME = "PA-FR-007.log"

OUTPUT_FILENAMES = (
    REDUNDANCY_CANDIDATES_JSON,
    REDUNDANCY_CANDIDATES_CSV,
    FILE_ROLLUP_JSON,
    VALIDATION_REPORT_JSON,
    REDUNDANCY_MANIFEST_JSON,
    AUDIT_LOG_JSON,
    LOG_FILENAME,
)


def _write_json(path: str, payload: Any) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _write_csv(path: str, headers: List[str], rows: List[List[Any]]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def _configure_logger(log_path: str) -> logging.Logger:
    logger = logging.getLogger("pa_fr_007_redundancy")
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(levelname)s  %(message)s"))
    logger.addHandler(handler)
    return logger


def build_file_rollup(result, config) -> Dict[str, Any]:
    clusters_evaluated = result.clusters_evaluated
    total_candidates = len(result.candidates)
    if clusters_evaluated > 0:
        candidates_per_cluster_avg = round(total_candidates / clusters_evaluated, 2)
    else:
        candidates_per_cluster_avg = 0
    return {
        "generated_by": "PA-FR-007",
        "embedding_version": result.embedding_version,
        "cluster_version": result.cluster_version,
        "similarity_threshold": config.similarity_threshold,
        "total_candidates": total_candidates,
        "clusters_evaluated": clusters_evaluated,
        "candidates_per_cluster_avg": candidates_per_cluster_avg,
    }


def build_export_payloads(result, config) -> Dict[str, Any]:
    candidates = [candidate.to_dict() for candidate in result.candidates]
    return {
        REDUNDANCY_CANDIDATES_JSON: {
            "generated_by": "PA-FR-007",
            "embedding_version": result.embedding_version,
            "cluster_version": result.cluster_version,
            "similarity_threshold": config.similarity_threshold,
            "candidates": candidates,
        },
        FILE_ROLLUP_JSON: build_file_rollup(result, config),
    }


def build_csv_rows(result) -> Tuple[List[str], List[List[Any]]]:
    headers = [
        "pattern_a",
        "pattern_b",
        "cluster_id",
        "raw_similarity",
        "confidence_score",
        "confidence_source",
        "review_status",
    ]
    rows = [
        [
            candidate.pattern_a,
            candidate.pattern_b,
            candidate.cluster_id,
            candidate.raw_similarity,
            candidate.confidence_score,
            candidate.confidence_source,
            candidate.review_status,
        ]
        for candidate in result.candidates
    ]
    return headers, rows


def write_outputs_to_directory(
    target_dir: str,
    json_payloads: Dict[str, Any],
    csv_headers: List[str],
    csv_rows: List[List[Any]],
    validation_report: Dict[str, Any],
    manifest_payload: Dict[str, Any],
    audit_entries: List[Dict[str, Any]],
) -> None:
    os.makedirs(target_dir, exist_ok=True)
    for filename, payload in json_payloads.items():
        _write_json(os.path.join(target_dir, filename), payload)
    _write_csv(os.path.join(target_dir, REDUNDANCY_CANDIDATES_CSV), csv_headers, csv_rows)
    _write_json(os.path.join(target_dir, VALIDATION_REPORT_JSON), validation_report)
    _write_json(os.path.join(target_dir, REDUNDANCY_MANIFEST_JSON), manifest_payload)
    _write_json(os.path.join(target_dir, AUDIT_LOG_JSON), audit_entries)


def run_pattern_redundancy(
    output_dir: str,
    workspace_dir: str | None = None,
) -> Dict[str, Any]:
    workspace = workspace_dir or os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(workspace, "config", "redundancy.yaml")
    config = load_redundancy_config(config_path)
    generated_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    os.makedirs(output_dir, exist_ok=True)
    log_path = os.path.join(output_dir, LOG_FILENAME)
    logger = _configure_logger(log_path)
    logger.info("PA-FR-007 pipeline started")

    try:
        result = run_redundancy_engine(output_dir, workspace_dir=workspace)
    except ClusteringAbortedError as exc:
        logger.error(str(exc))
        raise RedundancyAbortedError(str(exc)) from exc

    logger.info(f"Loaded embeddings (embedding_version={result.embedding_version})")
    logger.info(f"Loaded clusters (cluster_version={result.cluster_version})")
    logger.info(f"Similarity threshold = {config.similarity_threshold}")
    logger.info(f"Generating candidates within {result.clusters_evaluated} clusters...")
    logger.info(f"Generated {len(result.candidates)} candidates")

    if result.skipped_patterns_missing_embedding:
        logger.warning(
            "Missing embeddings for patterns: "
            + ", ".join(result.skipped_patterns_missing_embedding)
        )
    if result.skipped_patterns_missing_cluster:
        logger.warning(
            "Missing cluster assignments for patterns: "
            + ", ".join(result.skipped_patterns_missing_cluster)
        )
    if result.duplicate_pattern_ids:
        logger.warning(
            "Duplicate pattern IDs in input: "
            + ", ".join(sorted(set(result.duplicate_pattern_ids)))
        )

    audit_entries = build_redundancy_audit_entries(result.candidates, config, generated_timestamp)
    json_payloads = build_export_payloads(result, config)
    csv_headers, csv_rows = build_csv_rows(result)
    manifest_payload = build_redundancy_manifest_payload(
        embedding_version=result.embedding_version,
        cluster_version=result.cluster_version,
        similarity_threshold=config.similarity_threshold,
        total_candidates=len(result.candidates),
        validation_status="PENDING",
        generated_timestamp=generated_timestamp,
    )

    validation_report = validate_redundancy_result(
        result,
        config,
        audit_entries=audit_entries,
        manifest_generated=True,
    )
    manifest_payload["validation_status"] = validation_report["validation_status"]
    passed = validation_report.get("passed", 0)
    total = validation_report.get("total_checks", 0)
    logger.info(f"Validation: {passed}/{total} rules PASS")

    history_dir = os.path.join(output_dir, "history", f"v{result.cluster_version}")
    if config.enable_history:
        write_outputs_to_directory(
            history_dir,
            json_payloads,
            csv_headers,
            csv_rows,
            validation_report,
            manifest_payload,
            audit_entries,
        )
        for filename in OUTPUT_FILENAMES:
            if filename == LOG_FILENAME:
                continue
            source = os.path.join(history_dir, filename)
            if os.path.exists(source):
                shutil.copy2(source, os.path.join(output_dir, filename))
        shutil.copy2(log_path, os.path.join(history_dir, LOG_FILENAME))
    else:
        write_outputs_to_directory(
            output_dir,
            json_payloads,
            csv_headers,
            csv_rows,
            validation_report,
            manifest_payload,
            audit_entries,
        )

    logger.info(f"Audit log written: {len(audit_entries)} entries")
    logger.info("Export complete")
    logger.info("PA-FR-007 pipeline complete")

    return {
        "generated_by": "PA-FR-007",
        "embedding_version": result.embedding_version,
        "cluster_version": result.cluster_version,
        "similarity_threshold": config.similarity_threshold,
        "total_candidates": len(result.candidates),
        "clusters_evaluated": result.clusters_evaluated,
        "validation_status": validation_report["validation_status"],
        "candidates": [candidate.to_dict() for candidate in result.candidates],
        "file_rollup": json_payloads[FILE_ROLLUP_JSON],
        "validation_report": validation_report,
        "manifest": manifest_payload,
        "output_files": {
            filename: os.path.join(output_dir, filename)
            for filename in OUTPUT_FILENAMES
            if filename != LOG_FILENAME
        },
        "history_directory": history_dir if config.enable_history else None,
    }
