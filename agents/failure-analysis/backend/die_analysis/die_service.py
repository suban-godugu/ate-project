"""Service layer for FA-FR-007 die-level analytics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adapters.bridge import test_records_to_die_logs
from backend.die_analysis.die_engine import DieAnalysisEngine
from backend.die_analysis.die_repository import DieAnalysisRepository
from backend.ingestion.record_loader import load_test_records


class DieAnalysisService:
    def __init__(
        self,
        repo: DieAnalysisRepository,
        *,
        config_path: Path | str | None = None,
    ) -> None:
        self.repo = repo
        self.engine = DieAnalysisEngine(config_path=config_path)

    async def analyze_upload(self, upload_id: str) -> dict[str, Any]:
        test_records = await self.repo.load_test_records(upload_id)
        return await self._analyze_records(test_records, scope_id=upload_id)

    async def analyze_dataset(self, dataset_id: str) -> dict[str, Any]:
        test_records = await load_test_records(self.repo._session, dataset_id=dataset_id)
        return await self._analyze_records(test_records, scope_id=dataset_id)

    async def _analyze_records(self, test_records: list, *, scope_id: str) -> dict[str, Any]:
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
            "total_dies": report["total_dies"],
            "failing_dies": report["failing_dies"],
            "die_heatmap": report["die_heatmap"],
            "hotspot_analysis": report["hotspot_analysis"],
            "cluster_report": report["cluster_report"],
            "yield_distribution": report["yield_distribution"],
            "engineering_dashboard": report["engineering_dashboard"],
            "die_profiles": report.get("die_profiles", []),
            "spatial_ai_handoff": report.get("spatial_ai_handoff", []),
        }

    async def get_heatmap(self, run_id: str | None = None) -> dict[str, Any]:
        run = await self.repo.get_latest_or(run_id)
        if run is None:
            raise ValueError("No die analysis runs found")
        return {"run_id": run.id, "heatmap": run.heatmap_json}

    async def get_hotspots(self, run_id: str | None = None) -> dict[str, Any]:
        run = await self.repo.get_latest_or(run_id)
        if run is None:
            raise ValueError("No die analysis runs found")
        return {
            "run_id": run.id,
            "hotspot_analysis": run.report_json.get("hotspot_analysis", {}),
            "ai_hotspot_analysis": run.report_json.get("ai_hotspot_analysis", {}),
        }

    async def get_statistics(self, run_id: str | None = None) -> dict[str, Any]:
        run = await self.repo.get_latest_or(run_id)
        if run is None:
            raise ValueError("No die analysis runs found")
        return {
            "run_id": run.id,
            "total_dies": run.total_dies,
            "failing_dies": run.failing_dies,
            "overall_yield_pct": run.overall_yield_pct,
            "hotspot_count": run.hotspot_count,
            "cluster_count": run.cluster_count,
            "yield_distribution": run.report_json.get("yield_distribution", {}),
            "neighbor_analysis": run.report_json.get("neighbor_analysis", {}),
            "pattern_density": run.report_json.get("pattern_density", {}),
            "coordinate_mapping": {
                "edge_failures": run.report_json.get("coordinate_mapping", {}).get("edge_failures"),
                "center_failures": run.report_json.get("coordinate_mapping", {}).get("center_failures"),
            },
        }
