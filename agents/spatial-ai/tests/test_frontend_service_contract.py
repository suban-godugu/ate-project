"""Frontend service contract tests (Node not required — pure schema checks)."""

from __future__ import annotations

from pathlib import Path


def test_wafer_vision_service_only_calls_predict_endpoints():
    service = Path("frontend/src/services/waferVisionService.ts").read_text(
        encoding="utf-8"
    )
    assert '/predict"' in service or "/predict`" in service or '("/predict"' in service
    assert "/predict/batch" in service
    # must not call invent new analysis routes
    assert "/analyze-cluster" not in service
    assert "/zones" not in service or "NEXT_PUBLIC" in service


def test_frontend_export_utilities_exist():
    export_file = Path("frontend/src/utils/export.ts")
    assert export_file.is_file()
    text = export_file.read_text(encoding="utf-8")
    assert "exportSessionCsv" in text
    assert "exportSessionJson" in text
