"""Failure aggregation service — reads agent outputs via DataLoader."""

from __future__ import annotations

from threading import RLock
from typing import Any

from backend.core.exceptions import AppException
from backend.core.logging import get_logger
from backend.schemas.failures import (
    FailureDashboardRowsResponse,
    FailurePatternRow,
    FailureSummaryResponse,
    FailureSummaryStats,
)
from backend.services.data_loader import DataLoader, get_data_loader


class FailureService:
    """Expose failure_summary.json as a stable dashboard contract."""

    def __init__(self, data_loader: DataLoader) -> None:
        self._data_loader = data_loader
        self._lock = RLock()
        self._payload: FailureSummaryResponse | None = None

    def is_ready(self) -> bool:
        with self._lock:
            return self._payload is not None

    def ensure_built(self) -> FailureSummaryResponse:
        if not self.is_ready():
            return self.build()
        with self._lock:
            assert self._payload is not None
            return self._payload

    def build(self) -> FailureSummaryResponse:
        logger = get_logger()
        logger.info("Failure summary load started")
        try:
            raw = self._data_loader.get_failure_summary()
        except AppException:
            raise
        except Exception as exc:  # noqa: BLE001 — surface as 503 for dashboard
            raise AppException(
                "Failure summary is unavailable",
                status_code=503,
                details={"error": str(exc)},
            ) from exc

        if not isinstance(raw, dict):
            raise AppException(
                "Failure summary payload is invalid",
                status_code=503,
                details={"type": type(raw).__name__},
            )

        summary_raw = raw.get("summary") or {}
        patterns_raw = raw.get("patterns") or []
        if not isinstance(summary_raw, dict):
            summary_raw = {}
        if not isinstance(patterns_raw, list):
            patterns_raw = []

        rows: list[FailurePatternRow] = []
        severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for item in patterns_raw:
            if not isinstance(item, dict):
                continue
            row = _to_pattern_row(item)
            rows.append(row)
            key = str(row.severity).upper()
            if key in severity_counts:
                severity_counts[key] += 1

        payload = FailureSummaryResponse(
            success=True,
            message="Failure summary ready",
            summary=FailureSummaryStats(
                total_logs=int(summary_raw.get("total_logs") or 0),
                failed_logs=int(summary_raw.get("failed_logs") or 0),
                good_logs=int(summary_raw.get("good_logs") or 0),
                unique_patterns=int(summary_raw.get("unique_patterns") or 0),
                total_pattern_occurrences=int(
                    summary_raw.get("total_pattern_occurrences") or 0
                ),
                total_lots=int(summary_raw.get("total_lots") or 0),
                severity_high=severity_counts["HIGH"],
                severity_medium=severity_counts["MEDIUM"],
                severity_low=severity_counts["LOW"],
            ),
            patterns=rows,
            total_patterns=len(rows),
        )

        with self._lock:
            self._payload = payload

        logger.info(
            "Failure summary loaded patterns=%d failed_logs=%d",
            payload.total_patterns,
            payload.summary.failed_logs,
        )
        return payload

    def refresh(self) -> FailureSummaryResponse:
        get_logger().info("Failure summary refresh requested")
        self._data_loader.invalidate_role("failure_summary")
        with self._lock:
            self._payload = None
        return self.build()

    def get_summary(self) -> FailureSummaryResponse:
        return self.ensure_built()

    def get_dashboard_rows(self) -> FailureDashboardRowsResponse:
        payload = self.ensure_built()
        rows = [_to_dashboard_row(row) for row in payload.patterns]
        return FailureDashboardRowsResponse(
            success=True,
            message="Failure dashboard rows ready",
            rows=rows,
            total=len(rows),
        )


def _to_pattern_row(item: dict[str, Any]) -> FailurePatternRow:
    failing_logs = item.get("failing_logs") or []
    if not isinstance(failing_logs, list):
        failing_logs = []
    affected_lots = item.get("affected_lots") or []
    if not isinstance(affected_lots, list):
        affected_lots = []
    failed_logs = int(item.get("failed_logs") or 0)
    return FailurePatternRow(
        rank=int(item.get("rank") or 0),
        pattern_id=str(item.get("pattern_id") or ""),
        failed_logs=failed_logs,
        coverage_percent=float(item.get("coverage_percent") or 0.0),
        severity=str(item.get("severity") or "LOW").upper(),
        affected_lots=[str(lot) for lot in affected_lots],
        failing_logs=[str(path) for path in failing_logs],
        failing_log_count=len(failing_logs) if failing_logs else failed_logs,
    )


def _to_dashboard_row(row: FailurePatternRow) -> dict[str, Any]:
    return {
        "Rank": row.rank,
        "Pattern ID": row.pattern_id,
        "Failed Logs": row.failed_logs,
        "Coverage %": row.coverage_percent,
        "Severity": row.severity,
        "Affected Lots": row.affected_lots,
        "Failing Log Count": row.failing_log_count,
        "Failing Logs": row.failing_logs,
    }


_failure_service: FailureService | None = None
_failure_lock = RLock()


def get_failure_service(data_loader: DataLoader | None = None) -> FailureService:
    global _failure_service
    with _failure_lock:
        if _failure_service is None:
            loader = data_loader or get_data_loader()
            _failure_service = FailureService(loader)
        return _failure_service


def reset_failure_service() -> None:
    global _failure_service
    with _failure_lock:
        _failure_service = None
