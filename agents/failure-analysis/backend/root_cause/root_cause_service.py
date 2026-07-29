"""Service layer for FA-FR-009 root cause prediction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adapters.bridge import test_records_to_die_logs
from backend.ingestion.record_loader import load_test_records
from backend.root_cause.root_cause_engine import RootCauseEngine
from backend.root_cause.root_cause_repository import RootCauseRepository


class RootCauseService:
    def __init__(
        self,
        repo: RootCauseRepository,
        *,
        config_path: Path | str | None = None,
    ) -> None:
        self.repo = repo
        self.engine = RootCauseEngine(config_path=config_path)

    async def predict_upload(self, upload_id: str) -> dict[str, Any]:
        test_records = await self.repo.load_test_records(upload_id)
        return await self._predict_records(test_records, scope_id=upload_id)

    async def predict_dataset(self, dataset_id: str) -> dict[str, Any]:
        test_records = await load_test_records(self.repo._session, dataset_id=dataset_id)
        return await self._predict_records(test_records, scope_id=dataset_id)

    async def _predict_records(self, test_records: list, *, scope_id: str) -> dict[str, Any]:
        if not test_records:
            raise ValueError(f"No records found for scope={scope_id}")

        die_logs = test_records_to_die_logs(test_records)
        report = self.engine.predict(
            die_logs=die_logs,
            test_records=test_records,
            upload_id=scope_id,
        )
        run = await self.repo.save_run(report)
        return {
            "run_id": run.id,
            "upload_id": scope_id,
            "processing_ms": report["processing_ms"],
            "semantic_search_ms": report["semantic_search_ms"],
            "meets_performance_target": report["meets_performance_target"],
            "total_predictions": report["total_predictions"],
            "average_confidence": report["average_confidence"],
            "predictions": report["predictions"],
            "similar_historical_cases": report["similar_historical_cases"],
            "engineering_recommendations": report["engineering_recommendations"],
            "root_cause_report": report["root_cause_report"],
            "engineering_dashboard": report["engineering_dashboard"],
        }

    async def get_history(self, run_id: str | None = None) -> dict[str, Any]:
        run = await self.repo.get_latest_or(run_id)
        if run is None:
            raise ValueError("No root cause prediction runs found")
        return {
            "run_id": run.id,
            "upload_id": run.upload_id,
            "total_predictions": run.total_predictions,
            "average_confidence": run.average_confidence,
            "similar_historical_cases": run.report_json.get("similar_historical_cases", []),
            "predictions": run.report_json.get("predictions", []),
            "ranked_hypothesis_queue": run.report_json.get("ranked_hypothesis_queue", []),
        }

    async def get_recommendations(self, run_id: str | None = None) -> dict[str, Any]:
        run = await self.repo.get_latest_or(run_id)
        if run is None:
            raise ValueError("No root cause prediction runs found")
        return {
            "run_id": run.id,
            "engineering_recommendations": run.report_json.get(
                "engineering_recommendations", []
            ),
            "ai_explanations": run.report_json.get("ai_explanations", []),
            "root_cause_report": run.report_json.get("root_cause_report", {}),
        }
