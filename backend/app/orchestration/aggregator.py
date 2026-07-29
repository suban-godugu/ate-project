"""Merge agent reports into one enterprise Scan Chain result."""

from __future__ import annotations

from typing import Any


class ResultAggregator:
    def merge(
        self,
        *,
        upload_id: str,
        pattern: dict[str, Any] | None,
        failure: dict[str, Any] | None,
        diagnosis: dict[str, Any] | None,
    ) -> dict[str, Any]:
        pattern = pattern or {}
        failure = failure or {}
        diagnosis = diagnosis or {}
        return {
            "upload_id": upload_id,
            "schema_version": "2.0.0",
            "pattern_report": pattern.get("report") or pattern.get("pattern_report") or pattern,
            "coverage_report": pattern.get("coverage_report") or (pattern.get("report") or {}).get("coverage"),
            "chain_metrics": pattern.get("chain_metrics") or (pattern.get("report") or {}).get("chain_metrics"),
            "pattern_kpis": pattern.get("kpis") or {},
            "failure_report": failure.get("report") or failure.get("failure_report") or failure,
            "yield_report": failure.get("yield_report") or (failure.get("report") or {}).get("yield"),
            "failure_kpis": failure.get("kpis") or {},
            "diagnosis_report": diagnosis.get("report") or diagnosis.get("diagnosis_report") or diagnosis,
            "diagnosis_kpis": diagnosis.get("kpis") or {},
            "diagnosis_confidence": diagnosis.get("confidence"),
            "agent_recommendations": diagnosis.get("recommendations") or [],
        }
