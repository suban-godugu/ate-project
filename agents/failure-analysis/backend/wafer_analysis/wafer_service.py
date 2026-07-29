"""Service layer for FA-FR-008 wafer-level analytics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adapters.bridge import test_records_to_die_logs
from backend.ingestion.record_loader import load_test_records
from backend.wafer_analysis.wafer_engine import WaferAnalysisEngine
from backend.wafer_analysis.wafer_repository import WaferAnalysisRepository


class WaferAnalysisService:
    def __init__(
        self,
        repo: WaferAnalysisRepository,
        *,
        config_path: Path | str | None = None,
    ) -> None:
        self.repo = repo
        self.engine = WaferAnalysisEngine(config_path=config_path)

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
            "total_wafers": report["total_wafers"],
            "overall_yield_pct": report["overall_yield_pct"],
            "wafer_heatmap": report["wafer_heatmap"],
            "hotspot_analysis": report["hotspot_analysis"],
            "cluster_report": report["cluster_report"],
            "radial_failure_analysis": report["radial_failure_analysis"],
            "engineering_dashboard": report["engineering_dashboard"],
            "legacy_report": report.get("legacy_report", {}),
        }

    async def get_map(self, run_id: str | None = None) -> dict[str, Any]:
        run = await self.repo.get_latest_or(run_id)
        if run is None:
            raise ValueError("No wafer analysis runs found")
        return {"run_id": run.id, "wafer_map": run.map_json}

    async def get_hotspots(self, run_id: str | None = None) -> dict[str, Any]:
        run = await self.repo.get_latest_or(run_id)
        if run is None:
            raise ValueError("No wafer analysis runs found")
        return {
            "run_id": run.id,
            "hotspot_analysis": run.report_json.get("hotspot_analysis", {}),
            "radial_defects": run.report_json.get("radial_defects", []),
        }

    async def get_statistics(self, run_id: str | None = None) -> dict[str, Any]:
        run = await self.repo.get_latest_or(run_id)
        if run is None:
            raise ValueError("No wafer analysis runs found")
        return {
            "run_id": run.id,
            "total_wafers": run.total_wafers,
            "overall_yield_pct": run.overall_yield_pct,
            "outlier_wafer_count": run.outlier_wafer_count,
            "hotspot_count": run.hotspot_count,
            "cluster_count": run.cluster_count,
            "wafer_statistics": run.report_json.get("wafer_statistics", []),
            "yield_distribution": run.report_json.get("yield_distribution", []),
            "bin_distribution": run.report_json.get("bin_distribution", {}),
            "edge_center_analysis": run.report_json.get("edge_center_analysis", {}),
            "pass_fail_distribution": run.report_json.get("pass_fail_distribution", []),
        }
