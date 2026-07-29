"""PA-FR-010.2 single-log report preview builder.

The sole input is PA-FR-010_report_model.json. This frozen adapter delegates
presentation shaping to the additive shared builder and writes no files.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Mapping

from report_presentation_builder import (
    DEFAULT_TABLE_LIMIT,
    PRESENTATION_VERSION,
    REPORT_MODEL_FILENAME,
    SECTION_ORDER,
    build_report_presentation,
)

PREVIEW_VERSION = PRESENTATION_VERSION


class ReportPreviewError(RuntimeError):
    """Raised when the PA-FR-010.1 model cannot be loaded."""


def build_report_preview(report_model: Mapping[str, Any]) -> Dict[str, Any]:
    """Transform PA-FR-010.1 into the bounded PA-FR-010.2 preview."""
    return build_report_presentation(
        report_model,
        table_limit=DEFAULT_TABLE_LIMIT,
    )


def load_report_model(output_dir: str) -> Dict[str, Any]:
    """Read only the PA-FR-010.1 model from the output directory."""
    path = os.path.join(output_dir, REPORT_MODEL_FILENAME)
    if not os.path.exists(path):
        raise ReportPreviewError(f"Missing {REPORT_MODEL_FILENAME}.")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ReportPreviewError(
            f"Unable to read {REPORT_MODEL_FILENAME}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ReportPreviewError(f"{REPORT_MODEL_FILENAME} must contain an object.")
    return payload


def build_report_preview_from_output(output_dir: str) -> Dict[str, Any]:
    """Load PA-FR-010.1 and return the presentation-only preview model."""
    return build_report_preview(load_report_model(output_dir))
