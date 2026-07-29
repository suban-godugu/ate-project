"""Service layer for FA-FR-004 classification workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adapters.bridge import test_records_to_die_logs
from backend.classification.classification_engine import ClassificationEngine
from backend.classification.classification_repository import ClassificationRepository
from backend.ingestion.record_loader import load_test_records


class ClassificationService:
    def __init__(
        self,
        repo: ClassificationRepository,
        *,
        taxonomy_path: Path | str | None = None,
        enable_ml: bool = True,
        enable_llm: bool = True,
    ) -> None:
        self.repo = repo
        self.engine = ClassificationEngine(
            taxonomy_path=taxonomy_path,
            enable_ml=enable_ml,
            enable_llm=enable_llm,
        )

    async def analyze_upload(self, upload_id: str) -> dict[str, Any]:
        test_records = await self.repo.load_test_records(upload_id)
        return await self._analyze_records(test_records, scope_id=upload_id)

    async def analyze_dataset(self, dataset_id: str) -> dict[str, Any]:
        test_records = await load_test_records(self.repo._session, dataset_id=dataset_id)
        return await self._analyze_records(test_records, scope_id=dataset_id)

    async def _analyze_records(
        self, test_records: list, *, scope_id: str
    ) -> dict[str, Any]:
        if not test_records:
            raise ValueError(f"No records found for scope={scope_id}")

        die_logs = test_records_to_die_logs(test_records)
        report = self.engine.analyze(
            die_logs=die_logs,
            test_records=test_records,
            upload_id=scope_id,
        )
        run = await self.repo.save_run(report)
        return {
            "run_id": run.id,
            "upload_id": scope_id,
            "processing_ms": report["processing_ms"],
            "meets_performance_target": report["meets_performance_target"],
            "meets_accuracy_target": report["meets_accuracy_target"],
            "estimated_accuracy_pct": report["estimated_accuracy_pct"],
            "classification_summary": report["classification_summary"],
            "category_summary": report["category_summary"],
            "classified_faults": report["classified_faults"],
            "die_classifications": report["die_classifications"],
            "taxonomy": report["taxonomy"],
        }

    async def get_statistics(self, run_id: str | None = None) -> dict[str, Any]:
        run = await self.repo.get_latest_or(run_id)
        if run is None:
            raise ValueError("No classification runs found")

        report = run.report_json
        return {
            "run_id": run.id,
            "upload_id": run.upload_id,
            "processing_ms": run.processing_ms,
            "total_classified_failures": run.total_faults,
            "unique_categories": run.unique_categories,
            "dominant_category": run.dominant_category,
            "estimated_accuracy_pct": run.estimated_accuracy_pct,
            "method_counts": report.get("method_counts", {}),
            "category_summary": report.get("category_summary", {}),
            "classification_summary": report.get("classification_summary", {}),
            "high_confidence_pct": round(
                100.0
                * report.get("classification_summary", {}).get("high_confidence_count", 0)
                / max(run.total_faults, 1),
                2,
            ),
        }
