"""REST API and export handlers for FA-FR-003 failure rates."""

from __future__ import annotations

import csv
import io
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.bridge import test_records_to_die_logs
from analytics.failure_rates.dashboard_service import build_dashboard_dataset
from analytics.failure_rates.rate_engine import FailureRateEngine
from analytics.failure_rates.failure_rate_repository import FailureRateRepository
from backend.config import API_PREFIX
from backend.database import get_db

router = APIRouter(prefix=f"{API_PREFIX}/failure-rates", tags=["failure-rates"])


class CalculateRequest(BaseModel):
    upload_id: str | None = None


@router.post("/calculate")
async def calculate_failure_rates(
    body: CalculateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = FailureRateRepository(db)
    engine = FailureRateEngine()

    test_records = []
    if body.upload_id:
        test_records = await repo.load_test_records(body.upload_id)
        if not test_records:
            raise HTTPException(status_code=404, detail="No records for upload_id")

    historical = await repo.historical_summaries(limit=10)
    die_logs = test_records_to_die_logs(test_records) if test_records else []
    report = engine.calculate(
        die_logs=die_logs,
        test_records=test_records or None,
        upload_id=body.upload_id,
        historical_runs=historical,
    )
    dashboard = build_dashboard_dataset(report)
    run = await repo.save_run(report, dashboard)
    await db.commit()

    return {
        "run_id": run.id,
        "upload_id": body.upload_id,
        "processing_ms": report["processing_ms"],
        "meets_performance_target": report["meets_performance_target"],
        "failure_rate_report": report,
        "yield_report": report["overall_manufacturing_yield"],
        "trend_report": report["trend_report"],
        "dashboard_dataset": dashboard,
    }


@router.get("")
async def list_failure_rate_runs(
    limit: int = Query(50, ge=1, le=200),
    format: str = Query("json"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = FailureRateRepository(db)
    runs = await repo.list_runs(limit=limit)
    payload = {
        "runs": [
            {
                "run_id": run.id,
                "upload_id": run.upload_id,
                "overall_yield_pct": run.overall_yield_pct,
                "overall_failure_rate_pct": run.overall_failure_rate_pct,
                "processing_ms": run.processing_ms,
                "created_at": run.created_at.isoformat() if run.created_at else None,
            }
            for run in runs
        ]
    }
    if format == "csv":
        return _csv_response(payload["runs"], filename="failure_rate_runs.csv")
    return payload


@router.get("/device")
async def device_failure_rates(
    run_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    run = await _get_run(db, run_id)
    return {"run_id": run.id, "device_level": run.report_json.get("device_level", {})}


@router.get("/wafer")
async def wafer_failure_rates(
    run_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    run = await _get_run(db, run_id)
    return {"run_id": run.id, "wafer_level": run.report_json.get("wafer_level", {})}


@router.get("/lot")
async def lot_failure_rates(
    run_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    run = await _get_run(db, run_id)
    return {"run_id": run.id, "lot_level": run.report_json.get("lot_level", {})}


@router.get("/dashboard")
async def failure_rate_dashboard(
    run_id: str | None = Query(None),
    format: str = Query("json"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    run = await _get_run(db, run_id)
    dashboard = run.dashboard_json
    if format == "csv":
        rows = dashboard.get("lot_failure_rate", [])
        return _csv_response(rows, filename="failure_rate_dashboard.csv")
    if format == "xlsx":
        return _excel_response(dashboard, filename="failure_rate_dashboard.xlsx")
    return {"run_id": run.id, "dashboard": dashboard}


async def _get_run(db: AsyncSession, run_id: str | None):
    repo = FailureRateRepository(db)
    if run_id:
        run = await repo.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Failure rate run not found")
        return run
    runs = await repo.list_runs(limit=1)
    if not runs:
        raise HTTPException(status_code=404, detail="No failure rate runs found")
    return runs[0]


def _csv_response(rows: list[dict[str, Any]], *, filename: str) -> Response:
    if not rows:
        rows = [{"message": "no data"}]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _excel_response(dashboard: dict[str, Any], *, filename: str) -> Response:
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover
        raise HTTPException(status_code=501, detail="Excel export requires pandas") from exc

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet, key in [
            ("Overall", "overall_yield"),
            ("Lots", "lot_failure_rate"),
            ("Wafers", "wafer_failure_rate"),
            ("Devices", "device_failure_rate"),
            ("Products", "product_failure_rate"),
            ("Testers", "tester_failure_rate"),
        ]:
            data = dashboard.get(key, [])
            if isinstance(data, dict):
                pd.DataFrame([data]).to_excel(writer, sheet_name=sheet[:31], index=False)
            else:
                pd.DataFrame(data).to_excel(writer, sheet_name=sheet[:31], index=False)
    buffer.seek(0)
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
