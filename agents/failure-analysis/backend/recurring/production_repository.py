"""PostgreSQL handoff and append-only persistence for FA-FR-005."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ingestion.models_ingestion import IngestionDataset, NormalizedRecord
from backend.models import (
    ClassifiedFault,
    ClassificationRun,
    ComputationHistory,
    EngineeringRecommendation,
    DetectedPattern,
    DetectionHistory,
    FailureRateMetric,
    HotspotAnalysis,
    PatternOccurrence,
    RecurrenceAuditLog,
    RecurrenceHistory,
    RecurrenceStatistic,
    RecurrenceTrend,
    RecurringFailure,
    Upload,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _compatible_cohort(
    current: list[dict[str, Any]],
    historical: list[dict[str, Any]],
    *,
    require_same_tenant: bool,
    require_product_overlap: bool,
    require_test_stage_overlap: bool,
) -> bool:
    def values(rows: list[dict[str, Any]], key: str) -> set[str]:
        return {str(row.get(key, "")).strip() for row in rows if row.get(key)}

    if require_same_tenant:
        current_tenants = values(current, "tenant_id")
        historical_tenants = values(historical, "tenant_id")
        if current_tenants != historical_tenants:
            return False
    if require_product_overlap:
        current_products = values(current, "product_id")
        historical_products = values(historical, "product_id")
        if current_products and historical_products and not (
            current_products & historical_products
        ):
            return False
    if require_test_stage_overlap:
        current_stages = values(current, "test_stage")
        historical_stages = values(historical, "test_stage")
        if current_stages and historical_stages and not (
            current_stages & historical_stages
        ):
            return False
    return True


class ProductionRecurrenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def load_analysis_source(
        self,
        *,
        dataset_id: str | None,
        upload_id: str | None,
        detection_execution_id: str | None,
        computation_id: str | None,
        historical_window: int,
        compatible_formula_prefix: str,
        require_same_tenant: bool,
        require_product_overlap: bool,
        require_test_stage_overlap: bool,
    ) -> dict[str, Any]:
        if dataset_id:
            source = await self.session.get(IngestionDataset, dataset_id)
            if source is None:
                raise LookupError("Dataset not found")
            if source.status != "completed":
                raise ValueError(f"FA-FR-001 dataset status is {source.status}")
        else:
            source = await self.session.get(Upload, upload_id)
            if source is None:
                raise LookupError("Upload not found")
            if source.status != "completed":
                raise ValueError(f"FA-FR-001 upload status is {source.status}")

        current_stmt = select(ComputationHistory).where(
            ComputationHistory.status == "completed"
        )
        if computation_id:
            current_stmt = current_stmt.where(
                ComputationHistory.computation_id == computation_id
            )
        elif dataset_id:
            current_stmt = current_stmt.where(ComputationHistory.dataset_id == dataset_id)
        else:
            current_stmt = current_stmt.where(ComputationHistory.upload_id == upload_id)
        current_stmt = current_stmt.order_by(ComputationHistory.completed_at.desc())
        current = (await self.session.execute(current_stmt)).scalars().first()
        if current is None:
            raise ValueError("A completed FA-FR-003 computation is required")
        if dataset_id and current.dataset_id != dataset_id:
            raise ValueError("FA-FR-003 computation does not belong to this dataset")
        if upload_id and current.upload_id != upload_id:
            raise ValueError("FA-FR-003 computation does not belong to this upload")
        if detection_execution_id and current.detection_execution_id != detection_execution_id:
            raise ValueError("FA-FR-003 computation and FA-FR-002 execution do not match")

        detection = (
            await self.session.execute(
                select(DetectionHistory).where(
                    DetectionHistory.analysis_id == current.detection_execution_id,
                    DetectionHistory.execution_status == "completed",
                )
            )
        ).scalars().first()
        if detection is None or detection.completed_at is None or detection.errors:
            raise ValueError("A successful FA-FR-002 detection execution is required")
        if not current.formula_version.startswith(compatible_formula_prefix):
            raise ValueError(
                f"FA-FR-003 formula {current.formula_version} is not compatible "
                f"with {compatible_formula_prefix}"
            )

        histories = list(
            (
                await self.session.execute(
                    select(ComputationHistory)
                    .where(
                        ComputationHistory.status == "completed",
                        ComputationHistory.formula_version.like(
                            f"{compatible_formula_prefix}%"
                        ),
                    )
                    .order_by(ComputationHistory.completed_at.desc())
                    .limit(historical_window)
                )
            )
            .scalars()
            .all()
        )
        if all(row.computation_id != current.computation_id for row in histories):
            histories.insert(0, current)

        selected: list[ComputationHistory] = []
        seen_detections: set[str] = set()
        for row in histories:
            if row.detection_execution_id in seen_detections:
                continue
            seen_detections.add(row.detection_execution_id)
            selected.append(row)

        current_observations, current_count, current_warnings = (
            await self._load_execution(current)
        )
        if not current_observations:
            raise ValueError(
                "A completed FA-FR-004 classification matching the current "
                f"source is required: {current_warnings}"
            )
        observations: list[dict[str, Any]] = list(current_observations)
        source_record_counts: dict[str, int] = {
            current.detection_execution_id: current_count
        }
        warnings: list[str] = list(current_warnings)
        for history in selected:
            if history.computation_id == current.computation_id:
                continue
            loaded, record_count, execution_warnings = await self._load_execution(history)
            warnings.extend(execution_warnings)
            if not loaded:
                continue
            if not _compatible_cohort(
                current_observations,
                loaded,
                require_same_tenant=require_same_tenant,
                require_product_overlap=require_product_overlap,
                require_test_stage_overlap=require_test_stage_overlap,
            ):
                warnings.append(
                    f"Excluded incompatible historical execution "
                    f"{history.detection_execution_id}"
                )
                continue
            observations.extend(loaded)
            source_record_counts[history.detection_execution_id] = record_count

        source_ids = {str(row["source_id"]) for row in observations}
        if len(source_ids) < 2:
            raise ValueError(
                "At least two compatible completed FA-FR-001 through FA-FR-004 "
                "source executions are required"
            )

        rate_rows = list(
            (
                await self.session.execute(
                    select(FailureRateMetric).where(
                        FailureRateMetric.computation_id == current.computation_id,
                        FailureRateMetric.aggregation_level == "pattern",
                    )
                )
            )
            .scalars()
            .all()
        )
        failure_rates: dict[str, float] = {}
        for row in rate_rows:
            failure_rates[row.pattern_id] = max(
                failure_rates.get(row.pattern_id, 0.0), float(row.failure_percentage)
            )
        return {
            "current": current,
            "detection": detection,
            "classification_execution_ids": sorted(
                {
                    str(row["classification_execution_id"])
                    for row in current_observations
                }
            ),
            "observations": observations,
            "source_record_counts": source_record_counts,
            "failure_rates": failure_rates,
            "warnings": warnings,
        }

    async def _load_execution(
        self, history: ComputationHistory
    ) -> tuple[list[dict[str, Any]], int, list[str]]:
        if history.dataset_id:
            record_stmt = select(NormalizedRecord).where(
                NormalizedRecord.dataset_id == history.dataset_id
            )
            source_id = history.dataset_id
        elif history.upload_id:
            record_stmt = select(NormalizedRecord).where(
                NormalizedRecord.upload_id == history.upload_id
            )
            source_id = history.upload_id
        else:
            return [], 0, ["Skipped historical computation without a source identifier"]
        records = list((await self.session.execute(record_stmt)).scalars().all())
        by_key: dict[str, NormalizedRecord] = {}
        duplicates: set[str] = set()
        for row in records:
            if row.record_key in by_key:
                duplicates.add(row.record_key)
            by_key[row.record_key] = row
        if duplicates:
            raise ValueError(
                f"Duplicate normalized record keys prevent traceability: {sorted(duplicates)[:10]}"
            )

        upload_ids = sorted({row.upload_id for row in records})
        classification_rows = list(
            (
                await self.session.execute(
                    select(ClassificationRun)
                    .where(
                        ClassificationRun.upload_id.in_(upload_ids),
                        ClassificationRun.status == "completed",
                    )
                    .order_by(ClassificationRun.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        latest_classification: dict[str, ClassificationRun] = {}
        for row in classification_rows:
            if row.upload_id and row.upload_id not in latest_classification:
                latest_classification[row.upload_id] = row
        missing_classification = [
            item for item in upload_ids if item not in latest_classification
        ]
        if missing_classification:
            return [], len(records), [
                "Skipped execution "
                f"{history.detection_execution_id}: FA-FR-004 classification is "
                f"missing for uploads {missing_classification[:10]}"
            ]
        classification_ids = [row.id for row in latest_classification.values()]
        faults = list(
            (
                await self.session.execute(
                    select(ClassifiedFault).where(
                        ClassifiedFault.run_id.in_(classification_ids)
                    )
                )
            )
            .scalars()
            .all()
        )
        fault_by_scope = {
            (row.lot_id, row.wafer_id, row.die_id, row.pattern_id): row
            for row in faults
        }
        fault_by_die: dict[tuple[str, str, str], ClassifiedFault] = {}
        for row in sorted(
            faults,
            key=lambda item: item.classification_confidence,
            reverse=True,
        ):
            fault_by_die.setdefault((row.lot_id, row.wafer_id, row.die_id), row)
        source_tenant = ""
        if history.dataset_id:
            dataset = await self.session.get(IngestionDataset, history.dataset_id)
            source_tenant = str(dataset.tenant_id or "") if dataset else ""
        elif history.upload_id:
            upload = await self.session.get(Upload, history.upload_id)
            source_tenant = str(upload.tenant_id or "") if upload else ""

        patterns = list(
            (
                await self.session.execute(
                    select(DetectedPattern).where(
                        DetectedPattern.analysis_id == history.detection_execution_id
                    )
                )
            )
            .scalars()
            .all()
        )
        pattern_by_id = {row.id: row for row in patterns}
        if not pattern_by_id:
            return [], len(records), [
                f"Skipped execution {history.detection_execution_id}: no detected patterns"
            ]
        occurrences = list(
            (
                await self.session.execute(
                    select(PatternOccurrence).where(
                        PatternOccurrence.analysis_id == history.detection_execution_id
                    )
                )
            )
            .scalars()
            .all()
        )
        observations: list[dict[str, Any]] = []
        orphan_count = 0
        for occurrence in occurrences:
            pattern = pattern_by_id.get(occurrence.detected_pattern_id)
            record = by_key.get(occurrence.source_record_id)
            if pattern is None or record is None:
                orphan_count += 1
                continue
            payload = dict(record.payload or {})
            evidence = dict(occurrence.evidence or {})
            fault = fault_by_scope.get(
                (
                    occurrence.lot_id or record.lot_id,
                    occurrence.wafer_id or record.wafer_id,
                    occurrence.die_id or record.die_id,
                    pattern.pattern_id,
                )
            )
            if fault is None:
                fault = fault_by_die.get(
                    (
                        occurrence.lot_id or record.lot_id,
                        occurrence.wafer_id or record.wafer_id,
                        occurrence.die_id or record.die_id,
                    )
                )
            observations.append(
                {
                    "execution_id": history.detection_execution_id,
                    "computation_id": history.computation_id,
                    "source_id": source_id,
                    "occurrence_id": occurrence.id,
                    "dataset_id": history.dataset_id,
                    "upload_id": history.upload_id,
                    "source_record_id": record.record_key,
                    "normalized_record_id": record.id,
                    "detected_pattern_id": pattern.id,
                    "pattern_id": pattern.pattern_id,
                    "pattern_name": pattern.pattern_name,
                    "pattern_confidence": pattern.confidence,
                    "classification_execution_id": (
                        latest_classification[record.upload_id].id
                    ),
                    "fault_type": fault.fault_category if fault else "",
                    "classification_confidence": (
                        fault.classification_confidence if fault else 0.0
                    ),
                    "classification_pattern_id": fault.pattern_id if fault else "",
                    "failure_category": pattern.pattern_category,
                    "failure_code": evidence.get("failure_code")
                    or payload.get("failure_code")
                    or payload.get("hard_bin")
                    or "",
                    "device_id": occurrence.device_id
                    or payload.get("product_id")
                    or record.tester_id,
                    "batch_id": payload.get("batch_id")
                    or payload.get("production_batch")
                    or "",
                    "product_id": payload.get("product_id") or "",
                    "tenant_id": source_tenant,
                    "die_id": occurrence.die_id or record.die_id,
                    "wafer_id": occurrence.wafer_id or record.wafer_id,
                    "lot_id": occurrence.lot_id or record.lot_id,
                    "test_program": payload.get("test_program") or record.test_stage,
                    "test_stage": record.test_stage,
                    "x": occurrence.x if occurrence.x is not None else payload.get("x"),
                    "y": occurrence.y if occurrence.y is not None else payload.get("y"),
                    "timestamp": record.timestamp,
                }
            )
        warnings = []
        if orphan_count:
            warnings.append(
                f"Excluded {orphan_count} orphaned occurrences from "
                f"{history.detection_execution_id}"
            )
        unclassified = sum(1 for row in observations if not row["fault_type"])
        if unclassified:
            warnings.append(
                f"{unclassified} pattern occurrences in {history.detection_execution_id} "
                "could not be matched to FA-FR-004 classified faults"
            )
        return observations, len(records), warnings

    async def get_audit(self, analysis_id: str) -> RecurrenceAuditLog | None:
        return (
            await self.session.execute(
                select(RecurrenceAuditLog)
                .where(RecurrenceAuditLog.analysis_id == analysis_id)
                .order_by(RecurrenceAuditLog.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

    async def create_audit(
        self,
        *,
        analysis_id: str,
        dataset_id: str | None,
        upload_id: str | None,
        detection_execution_id: str | None,
        computation_id: str | None,
        status: str,
        config_version: str,
        actor: str | None,
        details: dict[str, Any] | None = None,
    ) -> RecurrenceAuditLog:
        row = RecurrenceAuditLog(
            analysis_id=analysis_id,
            dataset_id=dataset_id,
            upload_id=upload_id,
            detection_execution_id=detection_execution_id,
            computation_id=computation_id,
            action="recurrence_analysis",
            status=status,
            config_version=config_version,
            actor=actor,
            details=details or {},
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def persist(
        self,
        *,
        analysis_id: str,
        dataset_id: str | None,
        upload_id: str | None,
        detection_execution_id: str,
        computation_id: str,
        classification_execution_id: str,
        config_version: str,
        incremental: bool,
        result: dict[str, Any],
        audit: RecurrenceAuditLog,
        source_record_count: int,
        processing_ms: float,
        benchmark_metrics: dict[str, Any],
        warnings: list[str],
    ) -> list[RecurringFailure]:
        persisted: list[RecurringFailure] = []
        dependents: list[Any] = []
        for item in result["recurrences"]:
            row = RecurringFailure(
                recurrence_id=item["recurrence_id"],
                analysis_id=analysis_id,
                dataset_id=dataset_id,
                upload_id=upload_id,
                detection_execution_id=detection_execution_id,
                computation_id=computation_id,
                classification_execution_id=item.get(
                    "classification_execution_id", classification_execution_id
                ),
                detected_pattern_id=item["detected_pattern_id"],
                pattern_id=item["pattern_id"],
                pattern_name=item["pattern_name"],
                fault_type=item["fault_type"],
                canonical_recurrence_key=item["canonical_recurrence_key"],
                signature_hash=item["signature_hash"],
                similarity_group=item["similarity_group"],
                recurrence_count=item["recurrence_count"],
                recurrence_frequency=item["recurrence_frequency"],
                recurrence_percentage=item["recurrence_percentage"],
                confidence_score=item["confidence_score"],
                severity=item["severity"],
                trend_direction=item["trend_direction"],
                first_occurrence=item["first_occurrence"],
                latest_occurrence=item["latest_occurrence"],
                historical_frequency=item["historical_frequency"],
                hotspot_location=item["hotspot_location"],
                engineering_recommendation=item["engineering_recommendation"],
                config_version=config_version,
                incremental=incremental,
                metadata_json={
                    "source_ids": item["source_ids"],
                    "affected_devices": item["affected_devices"],
                    "affected_dies": item["affected_dies"],
                    "affected_wafers": item["affected_wafers"],
                    "affected_lots": item["affected_lots"],
                    "affected_batches": item["affected_batches"],
                    "feature_tokens": item["feature_tokens"],
                    "current_occurrence_count": item["current_occurrence_count"],
                },
            )
            self.session.add(row)
            persisted.append(row)
            dependents.append(
                RecurrenceHistory(
                    recurrence_id=row.recurrence_id,
                    analysis_id=analysis_id,
                    pattern_id=row.pattern_id,
                    dataset_id=dataset_id,
                    upload_id=upload_id,
                    occurrence_count=row.recurrence_count,
                    frequency=row.recurrence_frequency,
                    confidence_score=row.confidence_score,
                    source_execution_ids=item["source_execution_ids"],
                    details={
                        "signature_hash": row.signature_hash,
                        "canonical_recurrence_key": row.canonical_recurrence_key,
                        "fault_type": row.fault_type,
                        "recurrence_percentage": row.recurrence_percentage,
                    },
                )
            )
            historical = float(item["historical_frequency"])
            current = float(item["recurrence_frequency"])
            dependents.append(
                RecurrenceTrend(
                    recurrence_id=row.recurrence_id,
                    analysis_id=analysis_id,
                    pattern_id=row.pattern_id,
                    trend_direction=row.trend_direction,
                    current_frequency=current,
                    historical_frequency=historical,
                    absolute_change=current - historical,
                    relative_change=(
                        ((current - historical) / historical) * 100
                        if historical
                        else None
                    ),
                    newly_emerging=bool(item["newly_emerging"]),
                    time_series=item["time_series"],
                )
            )
            for hotspot in item["hotspots"]:
                dependents.append(
                    HotspotAnalysis(
                        hotspot_id=hotspot["hotspot_id"],
                        recurrence_id=row.recurrence_id,
                        analysis_id=analysis_id,
                        pattern_id=row.pattern_id,
                        lot_id=hotspot["lot_id"],
                        wafer_id=hotspot["wafer_id"],
                        x=hotspot["x"],
                        y=hotspot["y"],
                        radius=hotspot["radius"],
                        occurrence_count=hotspot["occurrence_count"],
                        density=hotspot["density"],
                        confidence_score=hotspot["confidence_score"],
                        severity=hotspot["severity"],
                        coordinates=hotspot["coordinates"],
                        details={},
                    )
                )
            for recommendation in item["recommendations"]:
                dependents.append(
                    EngineeringRecommendation(
                        recommendation_id=recommendation["recommendation_id"],
                        recurrence_id=row.recurrence_id,
                        analysis_id=analysis_id,
                        pattern_id=row.pattern_id,
                        fault_type=row.fault_type,
                        recommendation_code=recommendation["recommendation_code"],
                        priority=recommendation["priority"],
                        action=recommendation["action"],
                        rationale=recommendation["rationale"],
                        evidence=recommendation["evidence"],
                        config_version=config_version,
                    )
                )
        # Flush all parent rows in one batch before foreign-key dependents.
        await self.session.flush()
        self.session.add_all(dependents)
        for item in result["statistics"]:
            self.session.add(
                RecurrenceStatistic(
                    analysis_id=analysis_id,
                    scope_type=item["scope_type"],
                    scope_key=item["scope_key"],
                    pattern_count=item["pattern_count"],
                    recurrence_count=item["recurrence_count"],
                    mean_frequency=item["mean_frequency"],
                    mean_confidence=item["mean_confidence"],
                    hotspot_count=item["hotspot_count"],
                    details={},
                )
            )
        audit.status = "completed"
        audit.detection_execution_id = detection_execution_id
        audit.computation_id = computation_id
        audit.source_record_count = source_record_count
        audit.pattern_count = len(
            {str(row["pattern_id"]) for row in result["recurrences"]}
        )
        audit.recurrence_count = len(persisted)
        audit.processing_ms = processing_ms
        audit.benchmark_metrics = benchmark_metrics
        audit.warnings = warnings
        audit.details = {
            **dict(audit.details or {}),
            "requirement": "FA-FR-005",
            "classification_execution_id": classification_execution_id,
        }
        audit.completed_at = _now()
        await self.session.flush()
        return persisted

    async def mark_failed(self, audit: RecurrenceAuditLog, message: str) -> None:
        audit.status = "failed"
        audit.errors = [message]
        audit.completed_at = _now()
        await self.session.flush()

    async def list_recurrences(
        self,
        *,
        limit: int,
        offset: int,
        pattern_id: str | None,
        fault_type: str | None,
        severity: str | None,
        trend: str | None,
        analysis_id: str | None,
    ) -> list[RecurringFailure]:
        stmt = select(RecurringFailure).order_by(
            RecurringFailure.created_at.desc(),
            RecurringFailure.confidence_score.desc(),
        )
        if pattern_id:
            stmt = stmt.where(RecurringFailure.pattern_id == pattern_id)
        if fault_type:
            stmt = stmt.where(RecurringFailure.fault_type == fault_type)
        if severity:
            stmt = stmt.where(RecurringFailure.severity == severity)
        if trend:
            stmt = stmt.where(RecurringFailure.trend_direction == trend)
        if analysis_id:
            stmt = stmt.where(RecurringFailure.analysis_id == analysis_id)
        return list(
            (await self.session.execute(stmt.offset(offset).limit(limit))).scalars().all()
        )

    async def get_recurrence(self, recurrence_id: str) -> RecurringFailure | None:
        return (
            await self.session.execute(
                select(RecurringFailure).where(
                    RecurringFailure.recurrence_id == recurrence_id
                )
            )
        ).scalar_one_or_none()

    async def recommendations(
        self, recurrence_id: str
    ) -> list[EngineeringRecommendation]:
        return list(
            (
                await self.session.execute(
                    select(EngineeringRecommendation)
                    .where(EngineeringRecommendation.recurrence_id == recurrence_id)
                    .order_by(EngineeringRecommendation.priority)
                )
            )
            .scalars()
            .all()
        )

    async def trends(self, limit: int) -> list[RecurrenceTrend]:
        return list(
            (
                await self.session.execute(
                    select(RecurrenceTrend)
                    .order_by(RecurrenceTrend.created_at.desc())
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )

    async def trends_for_recurrence(
        self, recurrence_id: str
    ) -> list[RecurrenceTrend]:
        return list(
            (
                await self.session.execute(
                    select(RecurrenceTrend).where(
                        RecurrenceTrend.recurrence_id == recurrence_id
                    )
                )
            )
            .scalars()
            .all()
        )

    async def hotspots(self, limit: int) -> list[HotspotAnalysis]:
        return list(
            (
                await self.session.execute(
                    select(HotspotAnalysis)
                    .order_by(
                        HotspotAnalysis.severity.desc(),
                        HotspotAnalysis.occurrence_count.desc(),
                    )
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )

    async def hotspots_for_recurrence(
        self, recurrence_id: str
    ) -> list[HotspotAnalysis]:
        return list(
            (
                await self.session.execute(
                    select(HotspotAnalysis).where(
                        HotspotAnalysis.recurrence_id == recurrence_id
                    )
                )
            )
            .scalars()
            .all()
        )

    async def history(self, limit: int) -> list[RecurrenceAuditLog]:
        return list(
            (
                await self.session.execute(
                    select(RecurrenceAuditLog)
                    .order_by(RecurrenceAuditLog.created_at.desc())
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )

    async def statistics(self) -> dict[str, Any]:
        total = await self.session.scalar(select(func.count(RecurringFailure.id))) or 0
        avg_confidence = (
            await self.session.scalar(select(func.avg(RecurringFailure.confidence_score)))
            or 0.0
        )
        hotspots = await self.session.scalar(select(func.count(HotspotAnalysis.id))) or 0
        critical = (
            await self.session.scalar(
                select(func.count(RecurringFailure.id)).where(
                    RecurringFailure.severity == "critical"
                )
            )
            or 0
        )
        latest = (
            await self.session.execute(
                select(RecurrenceAuditLog)
                .where(RecurrenceAuditLog.status == "completed")
                .order_by(RecurrenceAuditLog.completed_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        by_fault_type = (
            await self.session.execute(
                select(
                    RecurringFailure.fault_type,
                    func.count(RecurringFailure.id),
                    func.avg(RecurringFailure.recurrence_percentage),
                    func.avg(RecurringFailure.confidence_score),
                ).group_by(RecurringFailure.fault_type)
            )
        ).all()
        return {
            "total_recurrences": int(total),
            "average_confidence": round(float(avg_confidence), 6),
            "hotspot_count": int(hotspots),
            "critical_count": int(critical),
            "latest_analysis_id": latest.analysis_id if latest else None,
            "latest_benchmark_metrics": latest.benchmark_metrics if latest else {},
            "by_fault_type": [
                {
                    "fault_type": fault_type,
                    "recurrence_count": count,
                    "average_recurrence_percentage": round(float(percentage or 0), 6),
                    "average_confidence": round(float(confidence or 0), 6),
                }
                for fault_type, count, percentage, confidence in by_fault_type
            ],
        }
