"""Upload metadata generation."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from adapters.schema import TestRecord
from backend.ingestion.normalization import dataset_summary


def build_upload_metadata(
    *,
    upload_id: str,
    original_filename: str,
    stored_path: Path,
    parser_id: str | None,
    checksum: str,
    records: list[TestRecord],
    validation_report: dict[str, Any],
    processing_stats: dict[str, Any],
) -> dict[str, Any]:
    return {
        "upload_id": upload_id,
        "original_filename": original_filename,
        "stored_path": str(stored_path),
        "parser_id": parser_id,
        "checksum_sha256": checksum,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": dataset_summary(records),
        "validation_report": validation_report,
        "processing_stats": processing_stats,
        "audit": {
            "raw_file_preserved": True,
            "processed_separately": True,
        },
    }
