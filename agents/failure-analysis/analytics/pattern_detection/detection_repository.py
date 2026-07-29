"""PostgreSQL repository for production FA-FR-002 detections."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.schema import TestRecord
from backend.ingestion.models_ingestion import IngestionDataset, NormalizedRecord
from backend.models import (
    DetectedPattern,
    DetectionHistory,
    PatternAnalysisRun,
    PatternConfidence,
    PatternOccurrence,
    PatternStatistic,
    RuleLibrary,
    Upload,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class DetectionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def load_source(
        self, *, dataset_id: str | None, upload_id: str | None
    ) -> tuple[list[TestRecord], list[dict[str, Any]]]:
        if dataset_id:
            dataset = await self.session.get(IngestionDataset, dataset_id)
            if dataset is None:
                raise LookupError("Dataset not found")
            if dataset.status != "completed":
                raise ValueError(
                    f"Dataset is not eligible for detection (status={dataset.status})"
                )
            stmt = select(NormalizedRecord).where(
                NormalizedRecord.dataset_id == dataset_id
            )
        else:
            upload = await self.session.get(Upload, upload_id)
            if upload is None:
                raise LookupError("Upload not found")
            if upload.status != "completed":
                raise ValueError(
                    f"Upload is not eligible for detection (status={upload.status})"
                )
            stmt = select(NormalizedRecord).where(
                NormalizedRecord.upload_id == upload_id
            )

        rows = list((await self.session.execute(stmt)).scalars().all())
        records: list[TestRecord] = []
        source_rows: list[dict[str, Any]] = []
        for row in rows:
            payload = dict(row.payload or {})
            payload.update(
                {
                    "record_key": row.record_key,
                    "lot_id": row.lot_id,
                    "wafer_id": row.wafer_id,
                    "die_id": row.die_id,
                    "test_stage": row.test_stage,
                    "pass_fail": row.pass_fail,
                    "adapter_id": row.adapter_id,
                }
            )
            payload.setdefault("tester_id", "")
            payload.setdefault("timestamp", "")
            payload.setdefault("source_file", "")
            records.append(TestRecord.from_dict(payload))
            source_rows.append(
                {
                    "id": row.id,
                    "upload_id": row.upload_id,
                    "record_key": row.record_key,
                    "payload": payload,
                }
            )
        return records, source_rows

    async def prior_record_keys(
        self, *, dataset_id: str | None, upload_id: str | None
    ) -> set[str]:
        stmt = select(PatternOccurrence.source_record_id)
        if dataset_id:
            stmt = stmt.where(PatternOccurrence.dataset_id == dataset_id)
        if upload_id:
            stmt = stmt.where(PatternOccurrence.upload_id == upload_id)
        return set((await self.session.execute(stmt)).scalars().all())

    async def begin_history(
        self,
        *,
        analysis_id: str,
        dataset_id: str | None,
        upload_id: str | None,
        rule_set_version: str,
        actor: str | None,
    ) -> DetectionHistory:
        history = DetectionHistory(
            analysis_id=analysis_id,
            dataset_id=dataset_id,
            upload_id=upload_id,
            execution_status="processing",
            rule_set_version=rule_set_version,
            actor=actor,
        )
        self.session.add(history)
        await self.session.flush()
        return history

    async def persist_detection(
        self,
        *,
        analysis_id: str,
        dataset_id: str | None,
        upload_id: str | None,
        detections: list[dict[str, Any]],
        total_records: int,
        threshold: float,
        processing_ms: float,
        report: dict[str, Any],
        history: DetectionHistory,
    ) -> list[DetectedPattern]:
        run = PatternAnalysisRun(
            id=analysis_id,
            upload_id=upload_id,
            status="completed",
            failure_count=sum(int(d["occurrence_count"]) for d in detections),
            unique_patterns=len(detections),
            processing_ms=processing_ms,
            report_json=report,
        )
        self.session.add(run)
        persisted: list[DetectedPattern] = []
        for rank, detection in enumerate(
            sorted(detections, key=lambda d: d["occurrence_count"], reverse=True), 1
        ):
            frequency = detection["occurrence_count"] / max(total_records, 1)
            pattern = DetectedPattern(
                analysis_id=analysis_id,
                dataset_id=dataset_id,
                pattern_id=detection["pattern_id"],
                pattern_name=detection["pattern_name"],
                pattern_category=detection["pattern_category"],
                pattern_frequency=frequency,
                rank=rank,
                rank_score=frequency * detection["confidence"],
                confidence=detection["confidence"],
                failure_count=detection["occurrence_count"],
                detection_method=detection["detection_method"],
                severity_level=detection["severity_level"],
                affected_devices=detection["affected_devices"],
                affected_dies=detection["affected_dies"],
                affected_wafers=detection["affected_wafers"],
                affected_lots=detection["affected_lots"],
                engineering_explanation=detection["explanation"],
                source_signature=detection["signature"],
                is_anomaly=1 if detection["pattern_category"] == "unknown" else 0,
                payload=detection,
            )
            self.session.add(pattern)
            await self.session.flush()
            persisted.append(pattern)
            for occurrence in detection["occurrences"]:
                self.session.add(
                    PatternOccurrence(
                        detected_pattern_id=pattern.id,
                        analysis_id=analysis_id,
                        dataset_id=dataset_id,
                        upload_id=upload_id,
                        **occurrence,
                    )
                )
            self.session.add(
                PatternConfidence(
                    detected_pattern_id=pattern.id,
                    analysis_id=analysis_id,
                    composite_score=detection["confidence"],
                    rule_score=(
                        detection["confidence"]
                        if detection["detection_method"] == "engineering_rule"
                        else 0.0
                    ),
                    statistical_score=frequency,
                    similarity_score=0.0,
                    threshold=threshold,
                    passed_threshold=detection["confidence"] >= threshold,
                    breakdown={
                        "frequency": frequency,
                        "method": detection["detection_method"],
                    },
                )
            )
            for scope, values in (
                ("lot", detection["affected_lots"]),
                ("wafer", detection["affected_wafers"]),
                ("die", detection["affected_dies"]),
                ("device", detection["affected_devices"]),
            ):
                for key in values:
                    count = sum(
                        1
                        for occurrence in detection["occurrences"]
                        if str(occurrence.get(f"{scope}_id", "")) == str(key)
                    )
                    self.session.add(
                        PatternStatistic(
                            detected_pattern_id=pattern.id,
                            analysis_id=analysis_id,
                            scope_type=scope,
                            scope_key=str(key),
                            occurrence_count=count,
                            total_records=total_records,
                            frequency=count / max(total_records, 1),
                        )
                    )

        history.execution_status = "completed"
        history.pattern_count = len(persisted)
        history.source_record_count = total_records
        history.processing_ms = processing_ms
        history.confidence_distribution = report["confidence_distribution"]
        history.benchmark_metrics = report["benchmark_metrics"]
        history.warnings = report.get("warnings", [])
        history.details = report
        history.completed_at = _now()
        await self.session.flush()
        return persisted

    async def mark_failed(self, history: DetectionHistory, message: str) -> None:
        history.execution_status = "failed"
        history.errors = [message]
        history.completed_at = _now()
        await self.session.flush()

    async def list_patterns(
        self,
        *,
        limit: int,
        offset: int,
        category: str | None,
        severity: str | None,
        query: str | None,
    ) -> list[DetectedPattern]:
        stmt = select(DetectedPattern).order_by(DetectedPattern.created_at.desc())
        if category:
            stmt = stmt.where(DetectedPattern.pattern_category == category)
        if severity:
            stmt = stmt.where(DetectedPattern.severity_level == severity)
        if query:
            stmt = stmt.where(
                DetectedPattern.pattern_name.ilike(f"%{query[:128]}%")
                | DetectedPattern.pattern_id.ilike(f"%{query[:128]}%")
            )
        result = await self.session.execute(stmt.offset(offset).limit(limit))
        return list(result.scalars().all())

    async def statistics(self) -> dict[str, Any]:
        total = await self.session.scalar(select(func.count(DetectedPattern.id))) or 0
        by_category = (
            await self.session.execute(
                select(
                    DetectedPattern.pattern_category,
                    func.count(DetectedPattern.id),
                ).group_by(DetectedPattern.pattern_category)
            )
        ).all()
        by_severity = (
            await self.session.execute(
                select(
                    DetectedPattern.severity_level,
                    func.count(DetectedPattern.id),
                ).group_by(DetectedPattern.severity_level)
            )
        ).all()
        confidence = (
            await self.session.scalar(select(func.avg(DetectedPattern.confidence)))
            or 0.0
        )
        return {
            "total_patterns": total,
            "average_confidence": round(float(confidence), 4),
            "by_category": {key: count for key, count in by_category},
            "by_severity": {key: count for key, count in by_severity},
        }

    async def histories(self, limit: int) -> list[DetectionHistory]:
        stmt = (
            select(DetectionHistory)
            .order_by(DetectionHistory.created_at.desc())
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_pattern_bundle(self, pattern_id: str) -> dict[str, Any] | None:
        pattern = await self.session.get(DetectedPattern, pattern_id)
        if pattern is None:
            return None
        occurrences = list(
            (
                await self.session.execute(
                    select(PatternOccurrence).where(
                        PatternOccurrence.detected_pattern_id == pattern_id
                    )
                )
            )
            .scalars()
            .all()
        )
        confidence = (
            await self.session.execute(
                select(PatternConfidence).where(
                    PatternConfidence.detected_pattern_id == pattern_id
                )
            )
        ).scalar_one_or_none()
        return {
            "pattern": pattern,
            "occurrences": occurrences,
            "confidence": confidence,
        }

    async def upsert_config_rules(
        self, rules: tuple[dict[str, Any], ...], actor: str | None = None
    ) -> None:
        for rule in rules:
            stmt = select(RuleLibrary).where(
                RuleLibrary.rule_key == rule["rule_key"],
                RuleLibrary.version == str(rule.get("version", "1.0")),
            )
            if (await self.session.execute(stmt)).scalar_one_or_none():
                continue
            self.session.add(
                RuleLibrary(
                    id=str(uuid.uuid4()),
                    rule_key=rule["rule_key"],
                    name=rule["name"],
                    category=rule["category"],
                    version=str(rule.get("version", "1.0")),
                    priority=int(rule.get("priority", 100)),
                    severity_level=rule.get("severity_level", "medium"),
                    confidence_weight=float(rule.get("confidence", 1.0)),
                    definition=rule,
                    explanation_template=rule.get("explanation", ""),
                    created_by=actor,
                )
            )
