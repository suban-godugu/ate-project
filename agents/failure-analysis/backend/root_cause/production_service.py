"""Validated, benchmarked FA-FR-009 orchestration."""

from __future__ import annotations

import time
import uuid
from collections import Counter
from dataclasses import replace
from typing import Any

import psutil
from sqlalchemy.ext.asyncio import AsyncSession

from backend.root_cause.production_engine import (
    FaultPredictionComputationError,
    FaultPredictionConfig,
    ProductionFaultPredictionEngine,
)
from backend.root_cause.production_repository import ProductionFaultPredictionRepository
from backend.root_cause.schemas import PredictFaultRequest


class FaultPredictionValidationError(ValueError):
    def __init__(self, issues: list[dict[str, Any]]) -> None:
        self.issues = issues
        super().__init__("Fault prediction input validation failed")


class ProductionFaultPredictionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProductionFaultPredictionRepository(session)

    async def execute(
        self,
        request: PredictFaultRequest,
        *,
        execution_id: str | None = None,
    ) -> dict[str, Any]:
        run_id = execution_id or str(uuid.uuid4())
        config = FaultPredictionConfig.load()
        updates: dict[str, Any] = {}
        if request.confidence_threshold is not None:
            updates["min_confidence"] = request.confidence_threshold
        if request.minimum_probability is not None:
            updates["min_probability"] = request.minimum_probability
        if updates:
            config = replace(config, **updates)
        if request.model_version and request.model_version != config.model_version:
            raise ValueError(f"Unsupported model version: {request.model_version}")

        await self.repo.ensure_model(
            model_version=config.model_version,
            config_version=config.version,
        )
        audit = await self.repo.get_audit(run_id)
        if audit is None:
            audit = await self.repo.create_audit(
                execution_id=run_id,
                dataset_id=request.dataset_id,
                upload_id=request.upload_id,
                config_version=config.version,
                model_version=config.model_version,
                status="processing",
                actor=request.actor,
                details={"incremental": request.incremental, "requirement": "FA-FR-009"},
            )
        else:
            audit.status = "processing"
        await self.session.commit()

        started = time.perf_counter()
        cpu_started = time.process_time()
        process = psutil.Process()
        memory_started = process.memory_info().rss
        try:
            load_started = time.perf_counter()
            source = await self.repo.load_analysis_source(
                dataset_id=request.dataset_id,
                upload_id=request.upload_id,
                detection_execution_id=request.detection_execution_id,
                computation_id=request.computation_id,
                recurrence_analysis_id=request.recurrence_analysis_id,
                correlation_analysis_id=request.correlation_analysis_id,
                die_analysis_id=request.die_analysis_id,
                wafer_analysis_id=request.wafer_analysis_id,
                historical_window=request.historical_window,
                compatible_formula_prefix=config.compatible_formula_prefix,
                require_same_tenant=config.require_same_tenant,
                require_product_overlap=config.require_product_overlap,
                require_test_stage_overlap=config.require_test_stage_overlap,
            )
            load_ms = (time.perf_counter() - load_started) * 1000
            issues, warnings = validate_prediction_source(source, config)
            warnings.extend(source.get("warnings", []))
            if issues:
                raise FaultPredictionValidationError(issues)

            compute_started = time.perf_counter()
            result = ProductionFaultPredictionEngine(config).predict(
                patterns=source["patterns"],
                correlations=source.get("correlations", []),
                recurrences=source.get("recurrences", []),
                classifications=source.get("classifications", []),
                failure_rates=source.get("failure_rates", {}),
                dies=source["dies"],
                wafers=source["wafers"],
                feedback_signals=source.get("feedback_signals", []),
                execution_id=run_id,
                wafer_analysis_id=source["wafer_audit"].analysis_id,
            )
            compute_ms = (time.perf_counter() - compute_started) * 1000
            processing_ms = round((time.perf_counter() - started) * 1000, 3)
            benchmarks = prediction_benchmarks(
                result["predictions"],
                request.expected_fault_types,
            )
            memory_current = process.memory_info().rss
            benchmarks.update(
                {
                    "prediction_latency_ms": processing_ms,
                    "throughput_patterns_per_second": round(
                        len(source["patterns"]) / max(processing_ms / 1000, 0.000001),
                        3,
                    ),
                    "cpu_time_ms": round((time.process_time() - cpu_started) * 1000, 3),
                    "process_memory_mb": round(memory_current / (1024 * 1024), 3),
                    "memory_delta_mb": round(
                        (memory_current - memory_started) / (1024 * 1024), 3
                    ),
                    "database_load_ms": round(load_ms, 3),
                    "computation_ms": round(compute_ms, 3),
                    "api_sla_met": processing_ms < 2000,
                }
            )
            persist_started = time.perf_counter()
            persisted = await self.repo.persist(
                execution_id=run_id,
                dataset_id=request.dataset_id,
                upload_id=request.upload_id,
                source=source,
                result=result,
                audit=audit,
                processing_ms=processing_ms,
                benchmarks=benchmarks,
                warnings=warnings,
                config_version=config.version,
                model_version=config.model_version,
            )
            benchmarks["database_persist_ms"] = round(
                (time.perf_counter() - persist_started) * 1000, 3
            )
            audit.benchmark_metrics = benchmarks
            await self.session.commit()
            upstream = dict(audit.upstream_execution_ids or {})
            return {
                "execution_id": run_id,
                "dataset_id": request.dataset_id,
                "upload_id": request.upload_id,
                "status": "completed",
                "config_version": config.version,
                "model_version": config.model_version,
                "upstream_execution_ids": upstream,
                "source_pattern_count": len(source["patterns"]),
                "prediction_count": len(persisted),
                "high_confidence_count": sum(
                    1
                    for row in persisted
                    if row.confidence_score >= config.high_confidence
                ),
                "processing_ms": processing_ms,
                "predictions": [serialize_prediction(row) for row in persisted],
                "statistics": result["statistics"],
                "benchmark_metrics": benchmarks,
                "warnings": warnings,
                "disclaimer": (
                    "Predictions are probable fault types only, not definitive root causes."
                ),
            }
        except Exception as exc:
            await self.session.rollback()
            persisted_audit = await self.repo.get_audit(run_id)
            if persisted_audit is not None:
                message = (
                    str(exc.issues)
                    if isinstance(exc, FaultPredictionValidationError)
                    else str(exc)
                )
                await self.repo.mark_failed(persisted_audit, message)
                await self.session.commit()
            raise

    async def submit_feedback(
        self,
        *,
        prediction_id: str,
        validated_fault_type: str,
        feedback_status: str,
        engineer_notes: str,
        learning_weight: float,
        actor: str | None,
    ) -> dict[str, Any]:
        prediction = await self.repo.get_prediction(prediction_id)
        if prediction is None:
            raise LookupError("Prediction not found")
        feedback_id = str(uuid.uuid4())
        row = await self.repo.save_feedback(
            feedback_id=feedback_id,
            prediction_id=prediction_id,
            execution_id=prediction.execution_id,
            pattern_id=prediction.pattern_id,
            validated_fault_type=validated_fault_type.strip().upper(),
            feedback_status=feedback_status,
            engineer_notes=engineer_notes,
            learning_weight=learning_weight,
            actor=actor,
            details={
                "predicted_fault_type": prediction.predicted_fault_type,
                "confidence_score": prediction.confidence_score,
            },
        )
        await self.session.commit()
        return {
            "feedback_id": row.feedback_id,
            "prediction_id": row.prediction_id,
            "pattern_id": row.pattern_id,
            "validated_fault_type": row.validated_fault_type,
            "feedback_status": row.feedback_status,
            "learning_weight": row.learning_weight,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }


def validate_prediction_source(
    source: dict[str, Any],
    config: FaultPredictionConfig,
) -> tuple[list[dict[str, Any]], list[str]]:
    patterns = source.get("patterns", [])
    issues: list[dict[str, Any]] = []
    warnings: list[str] = []

    pattern_ids = [str(row.get("pattern_id", "")).strip() for row in patterns]
    missing = [index for index, value in enumerate(pattern_ids) if not value]
    if missing:
        issues.append(
            {
                "code": "MISSING_PATTERN_ID",
                "message": "Every prediction source pattern requires pattern_id",
                "indexes": missing[:50],
            }
        )

    duplicates = [key for key, count in Counter(pattern_ids).items() if count > 1 and key]
    if duplicates:
        issues.append(
            {
                "code": "DUPLICATE_PATTERN_ID",
                "message": "Duplicate pattern identities in upstream handoff",
                "pattern_ids": duplicates[:50],
            }
        )

    if not patterns:
        issues.append(
            {
                "code": "INCOMPLETE_LINEAGE",
                "message": "FA-FR-001 through FA-FR-008 produced no eligible patterns",
            }
        )

    if config.min_confidence < 0 or config.min_confidence > 1:
        issues.append(
            {
                "code": "INVALID_THRESHOLD",
                "message": "minimum_confidence must be between 0 and 1",
                "value": config.min_confidence,
            }
        )
    if config.min_probability < 0 or config.min_probability > 1:
        issues.append(
            {
                "code": "INVALID_THRESHOLD",
                "message": "minimum_probability must be between 0 and 1",
                "value": config.min_probability,
            }
        )

    if not source.get("correlations"):
        warnings.append("No FA-FR-006 correlations found; scores rely on weaker signals")
    if not source.get("wafers"):
        issues.append(
            {
                "code": "MISSING_WAFER_RESULTS",
                "message": "FA-FR-008 produced no traceable wafer analytics",
            }
        )
    return issues, warnings


def prediction_benchmarks(
    predictions: list[dict[str, Any]],
    expected_fault_types: dict[str, str],
) -> dict[str, Any]:
    if not expected_fault_types:
        return {
            "ground_truth_available": False,
            "prediction_accuracy": None,
            "precision": None,
            "recall": None,
            "f1_score": None,
            "top1_accuracy": None,
            "top3_accuracy": None,
            "false_positive_rate": None,
            "false_negative_rate": None,
        }
    expected = {
        key.strip(): value.strip().upper()
        for key, value in expected_fault_types.items()
        if key.strip() and value.strip()
    }
    predicted = {
        row["pattern_id"]: row["predicted_fault_type"].upper() for row in predictions
    }
    alternatives = {
        row["pattern_id"]: [
            alt["fault_type"].upper() for alt in row.get("alternative_fault_types", [])
        ]
        for row in predictions
    }
    tp = 0
    top3_hits = 0
    fp = 0
    fn = 0
    for pattern_id, truth in expected.items():
        guess = predicted.get(pattern_id)
        alts = alternatives.get(pattern_id, [])
        ranked = ([guess] if guess else []) + [alt for alt in alts if alt != guess]
        if truth in ranked[:3]:
            top3_hits += 1
        if guess == truth:
            tp += 1
        elif guess is not None:
            fp += 1
        else:
            fn += 1
    evaluated = len(expected)
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    return {
        "ground_truth_available": True,
        "prediction_accuracy": round(tp / max(1, evaluated), 6),
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1_score": round(
            2 * precision * recall / max(precision + recall, 0.000001), 6
        ),
        "top1_accuracy": round(tp / max(1, evaluated), 6),
        "top3_accuracy": round(top3_hits / max(1, evaluated), 6),
        "false_positive_rate": round(fp / max(1, evaluated), 6),
        "false_negative_rate": round(fn / max(1, evaluated), 6),
    }


def serialize_prediction(row: Any) -> dict[str, Any]:
    return {
        "prediction_id": row.prediction_id,
        "execution_id": row.execution_id,
        "pattern_id": row.pattern_id,
        "predicted_fault_type": row.predicted_fault_type,
        "alternative_fault_types": row.alternative_fault_types,
        "confidence_score": row.confidence_score,
        "prediction_probability": row.prediction_probability,
        "supporting_evidence": row.supporting_evidence,
        "engineering_explanation": row.engineering_explanation,
        "investigation_steps": row.investigation_steps,
        "model_version": row.model_version,
        "predicted_at": row.predicted_at.isoformat() if row.predicted_at else None,
    }
