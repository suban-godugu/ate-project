"""Unified ingestion orchestrator (FA-FR-001 Phase 1)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterable

from adapters.base import IngestionReport
from adapters.bridge import test_records_to_die_logs
from adapters.registry import AdapterRegistry, default_registry
from adapters.schema import TestRecord
from adapters.validation import dedupe_records, partition_records
from ingestor import DieLog, ingest_logs as legacy_ingest_logs

logger = logging.getLogger(__name__)

SUPPORTED_GLOBS = ("*.log", "*.txt", "*.dat", "*.csv", "*.stdf", "*.std")


def discover_files(root_dir: Path, *, recursive: bool = True) -> list[Path]:
    root = Path(root_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"Ingestion directory does not exist: {root}")

    finder = root.rglob if recursive else root.glob
    files: list[Path] = []
    for pattern in SUPPORTED_GLOBS:
        files.extend(finder(pattern))
    return sorted(set(files))


def ingest_path(
    path: Path,
    registry: AdapterRegistry,
) -> tuple[list[TestRecord], list[dict[str, str]], str | None]:
    adapter = registry.resolve(path)
    if adapter is None:
        return [], [{"file": str(path), "error": "No adapter matched"}], None

    result = adapter.parse(path)
    accepted, quarantined = adapter.validate(result.records)
    errors = list(result.errors)
    for item in quarantined:
        errors.append(
            {
                "file": str(path),
                "error": item.get("reason", "quarantined"),
                "record": json.dumps(item.get("record", {}))[:500],
            }
        )
    return accepted, errors, adapter.adapter_id


def ingest_directory(
    root_dir: str | Path,
    *,
    recursive: bool = True,
    registry: AdapterRegistry | None = None,
    use_legacy_fallback: bool = True,
) -> tuple[list[TestRecord], list[DieLog], IngestionReport]:
    """
    Ingest all supported files under *root_dir* using the adapter plugin architecture.

    Returns canonical test records, DieLog objects (for backward-compatible analytics),
    and an ingestion report with quarantine details.
    """
    root = Path(root_dir)
    reg = registry or default_registry()
    report = IngestionReport()

    files = discover_files(root, recursive=recursive)
    report.files_discovered = len(files)

    all_records: list[TestRecord] = []
    file_errors: list[dict[str, str]] = []

    for file_path in files:
        accepted, errors, adapter_id = ingest_path(file_path, reg)
        if errors and not accepted:
            report.files_failed += 1
            file_errors.extend(errors)
            continue
        if accepted:
            report.files_parsed += 1
            report.adapters_used[adapter_id or "unknown"] = (
                report.adapters_used.get(adapter_id or "unknown", 0) + 1
            )
            all_records.extend(accepted)
        if errors:
            file_errors.extend(errors)
            report.quarantine.extend(
                {"file": str(file_path), **err} for err in errors if "quarantined" in err.get("error", "")
            )

    all_records, dupes = dedupe_records(all_records)
    accepted, quarantined = partition_records(all_records)
    report.records_accepted = len(accepted)
    report.records_quarantined = len(quarantined) + dupes
    report.quarantine.extend(quarantined)
    report.errors = file_errors

    total = report.records_accepted + report.records_quarantined
    if total:
        report.integrity_pct = round(100.0 * report.records_accepted / total, 4)

    die_logs = test_records_to_die_logs(accepted)

    if use_legacy_fallback and not die_logs:
        logger.info("Adapter ingestion produced no die logs; falling back to legacy ingestor.")
        legacy_logs, legacy_errors = legacy_ingest_logs(root, recursive=recursive)
        die_logs = legacy_logs
        report.errors.extend(legacy_errors)
        report.files_parsed = len(legacy_logs)
        report.files_failed = len(legacy_errors)

    return accepted, die_logs, report


def export_ingestion_report(report: IngestionReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(report.to_dict(), handle, indent=2)
