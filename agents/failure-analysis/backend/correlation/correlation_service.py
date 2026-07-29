"""Service layer for FA-FR-006 correlation analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adapters.bridge import test_records_to_die_logs
from backend.correlation.correlation_engine import CorrelationEngine
from backend.correlation.correlation_repository import CorrelationRepository


class CorrelationService:
    def __init__(
        self,
        repo: CorrelationRepository,
        *,
        config_path: Path | str | None = None,
    ) -> None:
        self.repo = repo
        self.engine = CorrelationEngine(config_path=config_path)

    async def analyze_upload(self, upload_id: str, *, top_n: int = 50) -> dict[str, Any]:
        test_records = await self.repo.load_test_records(upload_id)
        if not test_records:
            raise ValueError(f"No records found for upload_id={upload_id}")

        die_logs = test_records_to_die_logs(test_records)
        report = self.engine.analyze(
            die_logs=die_logs,
            test_records=test_records,
            upload_id=upload_id,
            top_n=top_n,
        )
        run = await self.repo.save_run(report)
        return {
            "run_id": run.id,
            "upload_id": upload_id,
            "processing_ms": report["processing_ms"],
            "meets_performance_target": report["meets_performance_target"],
            "correlation_matrix": report["correlation_matrix"],
            "correlation_report": report["correlation_report"],
            "pattern_relationships": report["pattern_relationships"],
            "failure_dependency_graph": report["failure_dependency_graph"],
            "engineering_insights": report["engineering_insights"],
            "visualization": report["visualization"],
            "downstream_export": report["downstream_export"],
        }

    async def get_matrix(self, run_id: str | None = None) -> dict[str, Any]:
        run = await self.repo.get_latest_or(run_id)
        if run is None:
            raise ValueError("No correlation runs found")
        return {
            "run_id": run.id,
            "correlation_matrix": run.report_json.get("correlation_matrix", {}),
            "dimension_correlations": run.report_json.get("dimension_correlations", {}),
            "statistical_methods": run.report_json.get("statistical_methods", {}),
        }

    async def get_network(self, run_id: str | None = None) -> dict[str, Any]:
        run = await self.repo.get_latest_or(run_id)
        if run is None:
            raise ValueError("No correlation runs found")
        return {
            "run_id": run.id,
            "failure_dependency_graph": run.report_json.get("failure_dependency_graph", {}),
            "pattern_relationships": run.report_json.get("pattern_relationships", []),
            "visualization": run.report_json.get("visualization", {}),
        }
