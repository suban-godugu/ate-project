"""Service layer for FA-FR-005 recurring failure detection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adapters.bridge import test_records_to_die_logs
from backend.recurring.recurring_engine import RecurringEngine
from backend.recurring.recurring_repository import RecurringRepository


class RecurringService:
    def __init__(
        self,
        repo: RecurringRepository,
        *,
        config_path: Path | str | None = None,
    ) -> None:
        self.repo = repo
        self.engine = RecurringEngine(config_path=config_path)

    async def analyze_upload(
        self,
        upload_id: str,
        *,
        incremental: bool = False,
    ) -> dict[str, Any]:
        test_records = await self.repo.load_test_records(upload_id)
        if not test_records:
            raise ValueError(f"No records found for upload_id={upload_id}")

        historical = await self.repo.historical_summaries(limit=10) if incremental else []
        die_logs = test_records_to_die_logs(test_records)
        report = self.engine.analyze(
            die_logs=die_logs,
            test_records=test_records,
            upload_id=upload_id,
            historical_runs=historical,
            incremental=incremental,
        )
        run = await self.repo.save_run(report)
        return {
            "run_id": run.id,
            "upload_id": upload_id,
            "processing_ms": report["processing_ms"],
            "meets_performance_target": report["meets_performance_target"],
            "recurring_failure_list": report["recurring_failure_list"],
            "frequency_distribution": report["frequency_distribution"],
            "severity_ranking": report["severity_ranking"],
            "trend_analysis": report["trend_analysis"],
            "impacted_lots": report["impacted_lots"],
            "engineering_alerts": report["engineering_alerts"],
            "classification_summary": report["classification_summary"],
            "dashboard": report["dashboard"],
        }
