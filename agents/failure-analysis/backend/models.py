"""SQLAlchemy models for upload history and canonical test records."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from backend.database import Base

# Register FA-FR-001 production tables on Base.metadata
from backend.ingestion.models_ingestion import (  # noqa: E402,F401
    AuditLog,
    IngestionDataset,
    IngestionStatistics,
    NormalizedRecord,
    ParserMetadata,
    UploadHistory,
    ValidationResult,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Upload(Base):
    __tablename__ = "uploads"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    dataset_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(512))
    sanitized_filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    stored_filename: Mapped[str] = mapped_column(String(512))
    relative_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    content_type: Mapped[str] = mapped_column(String(128), default="application/octet-stream")
    detected_mime: Mapped[str | None] = mapped_column(String(128), nullable=True)
    file_extension: Mapped[str] = mapped_column(String(16))
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    checksum_sha256: Mapped[str] = mapped_column(String(64), index=True)
    parser_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    records_accepted: Mapped[int] = mapped_column(Integer, default=0)
    records_quarantined: Mapped[int] = mapped_column(Integer, default=0)
    integrity_pct: Mapped[float] = mapped_column(Float, default=0.0)
    validation_report: Mapped[dict] = mapped_column(JSON, default=dict)
    processing_stats: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tenant_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UploadMetadata(Base):
    __tablename__ = "upload_metadata"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    upload_id: Mapped[str] = mapped_column(String(36), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class TestRecordRow(Base):
    __tablename__ = "test_records"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    upload_id: Mapped[str] = mapped_column(String(36), index=True)
    record_key: Mapped[str] = mapped_column(String(512), index=True)
    lot_id: Mapped[str] = mapped_column(String(128), index=True)
    wafer_id: Mapped[str] = mapped_column(String(128), index=True)
    die_id: Mapped[str] = mapped_column(String(128), index=True)
    test_stage: Mapped[str] = mapped_column(String(64))
    tester_id: Mapped[str] = mapped_column(String(128))
    pass_fail: Mapped[str] = mapped_column(String(16))
    timestamp: Mapped[str] = mapped_column(String(64))
    adapter_id: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PatternAnalysisRun(Base):
    __tablename__ = "pattern_analysis_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="completed")
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    unique_patterns: Mapped[int] = mapped_column(Integer, default=0)
    processing_ms: Mapped[float] = mapped_column(Float, default=0.0)
    report_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class FailureRateRun(Base):
    __tablename__ = "failure_rate_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    processing_ms: Mapped[float] = mapped_column(Float, default=0.0)
    overall_yield_pct: Mapped[float] = mapped_column(Float, default=0.0)
    overall_failure_rate_pct: Mapped[float] = mapped_column(Float, default=0.0)
    report_json: Mapped[dict] = mapped_column(JSON, default=dict)
    dashboard_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ClassifiedFault(Base):
    __tablename__ = "classified_faults"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    lot_id: Mapped[str] = mapped_column(String(128), index=True)
    wafer_id: Mapped[str] = mapped_column(String(128), index=True)
    die_id: Mapped[str] = mapped_column(String(128), index=True)
    pattern_id: Mapped[str] = mapped_column(String(128), index=True)
    fault_category: Mapped[str] = mapped_column(String(128), index=True)
    classification_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    method: Mapped[str] = mapped_column(String(64), default="")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ClassificationRun(Base):
    __tablename__ = "classification_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="completed")
    processing_ms: Mapped[float] = mapped_column(Float, default=0.0)
    total_faults: Mapped[int] = mapped_column(Integer, default=0)
    unique_categories: Mapped[int] = mapped_column(Integer, default=0)
    dominant_category: Mapped[str] = mapped_column(String(128), default="")
    estimated_accuracy_pct: Mapped[float] = mapped_column(Float, default=0.0)
    report_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RecurringEvent(Base):
    __tablename__ = "recurring_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    signature_type: Mapped[str] = mapped_column(String(64), index=True)
    entity_key: Mapped[str] = mapped_column(String(256), index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    entity_count: Mapped[int] = mapped_column(Integer, default=0)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RecurringAnalysisRun(Base):
    __tablename__ = "recurring_analysis_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="completed")
    processing_ms: Mapped[float] = mapped_column(Float, default=0.0)
    recurring_count: Mapped[int] = mapped_column(Integer, default=0)
    impacted_lot_count: Mapped[int] = mapped_column(Integer, default=0)
    alert_count: Mapped[int] = mapped_column(Integer, default=0)
    report_json: Mapped[dict] = mapped_column(JSON, default=dict)
    dashboard_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CorrelationAnalysisRun(Base):
    __tablename__ = "correlation_analysis_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="completed")
    processing_ms: Mapped[float] = mapped_column(Float, default=0.0)
    pattern_count: Mapped[int] = mapped_column(Integer, default=0)
    top_correlation_score: Mapped[float] = mapped_column(Float, default=0.0)
    report_json: Mapped[dict] = mapped_column(JSON, default=dict)
    matrix_json: Mapped[dict] = mapped_column(JSON, default=dict)
    network_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DieAnalysisRun(Base):
    __tablename__ = "die_analysis_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="completed")
    processing_ms: Mapped[float] = mapped_column(Float, default=0.0)
    total_dies: Mapped[int] = mapped_column(Integer, default=0)
    failing_dies: Mapped[int] = mapped_column(Integer, default=0)
    overall_yield_pct: Mapped[float] = mapped_column(Float, default=0.0)
    hotspot_count: Mapped[int] = mapped_column(Integer, default=0)
    cluster_count: Mapped[int] = mapped_column(Integer, default=0)
    report_json: Mapped[dict] = mapped_column(JSON, default=dict)
    heatmap_json: Mapped[dict] = mapped_column(JSON, default=dict)
    dashboard_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EngineeringReportRun(Base):
    __tablename__ = "engineering_report_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="completed")
    processing_ms: Mapped[float] = mapped_column(Float, default=0.0)
    pdf_ms: Mapped[float] = mapped_column(Float, default=0.0)
    excel_ms: Mapped[float] = mapped_column(Float, default=0.0)
    total_dies: Mapped[int] = mapped_column(Integer, default=0)
    failing_dies: Mapped[int] = mapped_column(Integer, default=0)
    overall_yield_pct: Mapped[float] = mapped_column(Float, default=0.0)
    pdf_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    excel_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    json_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    report_json: Mapped[dict] = mapped_column(JSON, default=dict)
    dashboard_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RootCausePredictionRun(Base):
    __tablename__ = "root_cause_prediction_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="completed")
    processing_ms: Mapped[float] = mapped_column(Float, default=0.0)
    semantic_search_ms: Mapped[float] = mapped_column(Float, default=0.0)
    total_predictions: Mapped[int] = mapped_column(Integer, default=0)
    average_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    high_confidence_count: Mapped[int] = mapped_column(Integer, default=0)
    ml_model_trained: Mapped[int] = mapped_column(Integer, default=0)
    report_json: Mapped[dict] = mapped_column(JSON, default=dict)
    dashboard_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class WaferAnalysisRun(Base):
    __tablename__ = "wafer_analysis_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="completed")
    processing_ms: Mapped[float] = mapped_column(Float, default=0.0)
    total_wafers: Mapped[int] = mapped_column(Integer, default=0)
    overall_yield_pct: Mapped[float] = mapped_column(Float, default=0.0)
    outlier_wafer_count: Mapped[int] = mapped_column(Integer, default=0)
    hotspot_count: Mapped[int] = mapped_column(Integer, default=0)
    cluster_count: Mapped[int] = mapped_column(Integer, default=0)
    report_json: Mapped[dict] = mapped_column(JSON, default=dict)
    map_json: Mapped[dict] = mapped_column(JSON, default=dict)
    dashboard_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), default="completed")
    processing_ms: Mapped[float] = mapped_column(Float, default=0.0)
    datasets_evaluated: Mapped[int] = mapped_column(Integer, default=0)
    pass_count: Mapped[int] = mapped_column(Integer, default=0)
    fail_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    model_version: Mapped[str] = mapped_column(String(64), default="")
    report_json: Mapped[dict] = mapped_column(JSON, default=dict)
    dashboard_json: Mapped[dict] = mapped_column(JSON, default=dict)
    export_paths: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ModelTrainingRun(Base):
    __tablename__ = "model_training_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    evaluation_run_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    model_name: Mapped[str] = mapped_column(String(128), default="")
    model_version: Mapped[str] = mapped_column(String(64), default="")
    validation_accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    artifact_path: Mapped[str] = mapped_column(String(1024), default="")
    comparison_json: Mapped[list] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DetectedPattern(Base):
    __tablename__ = "detected_patterns"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    pattern_id: Mapped[str] = mapped_column(String(128), index=True)
    rank: Mapped[int] = mapped_column(Integer, default=0)
    rank_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    cluster_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_anomaly: Mapped[int] = mapped_column(Integer, default=0)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    dataset_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    pattern_name: Mapped[str] = mapped_column(String(256), default="")
    pattern_category: Mapped[str] = mapped_column(String(128), default="unknown")
    pattern_frequency: Mapped[float] = mapped_column(Float, default=0.0)
    detection_method: Mapped[str] = mapped_column(String(64), default="statistical")
    severity_level: Mapped[str] = mapped_column(String(32), default="medium")
    affected_devices: Mapped[list] = mapped_column(JSON, default=list)
    affected_dies: Mapped[list] = mapped_column(JSON, default=list)
    affected_wafers: Mapped[list] = mapped_column(JSON, default=list)
    affected_lots: Mapped[list] = mapped_column(JSON, default=list)
    engineering_explanation: Mapped[str] = mapped_column(Text, default="")
    source_signature: Mapped[str] = mapped_column(String(512), default="", index=True)
    rule_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PatternOccurrence(Base):
    __tablename__ = "pattern_occurrences"
    __table_args__ = (
        UniqueConstraint(
            "detected_pattern_id",
            "source_record_id",
            name="uq_pattern_occurrence_source",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    detected_pattern_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("detected_patterns.id", ondelete="CASCADE"), index=True
    )
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    source_record_id: Mapped[str] = mapped_column(String(512))
    lot_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    wafer_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    die_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    device_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    x: Mapped[int | None] = mapped_column(Integer, nullable=True)
    y: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PatternStatistic(Base):
    __tablename__ = "pattern_statistics"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    detected_pattern_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("detected_patterns.id", ondelete="CASCADE"), index=True
    )
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    scope_type: Mapped[str] = mapped_column(String(32), index=True)
    scope_key: Mapped[str] = mapped_column(String(384), index=True)
    occurrence_count: Mapped[int] = mapped_column(Integer, default=0)
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    frequency: Mapped[float] = mapped_column(Float, default=0.0)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PatternConfidence(Base):
    __tablename__ = "pattern_confidence"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    detected_pattern_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("detected_patterns.id", ondelete="CASCADE"), index=True
    )
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    composite_score: Mapped[float] = mapped_column(Float, default=0.0)
    rule_score: Mapped[float] = mapped_column(Float, default=0.0)
    statistical_score: Mapped[float] = mapped_column(Float, default=0.0)
    similarity_score: Mapped[float] = mapped_column(Float, default=0.0)
    threshold: Mapped[float] = mapped_column(Float, default=0.0)
    passed_threshold: Mapped[bool] = mapped_column(Boolean, default=False)
    breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DetectionHistory(Base):
    __tablename__ = "detection_history"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    execution_status: Mapped[str] = mapped_column(String(32), index=True)
    rule_set_version: Mapped[str] = mapped_column(String(64), default="")
    pattern_count: Mapped[int] = mapped_column(Integer, default=0)
    source_record_count: Mapped[int] = mapped_column(Integer, default=0)
    processing_ms: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_distribution: Mapped[dict] = mapped_column(JSON, default=dict)
    benchmark_metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    errors: Mapped[list] = mapped_column(JSON, default=list)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    actor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RuleLibrary(Base):
    __tablename__ = "rule_library"
    __table_args__ = (
        UniqueConstraint("rule_key", "version", name="uq_rule_library_key_version"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    rule_key: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str] = mapped_column(String(256))
    category: Mapped[str] = mapped_column(String(128), index=True)
    version: Mapped[str] = mapped_column(String(64))
    customer_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    severity_level: Mapped[str] = mapped_column(String(32), default="medium")
    confidence_weight: Mapped[float] = mapped_column(Float, default=1.0)
    definition: Mapped[dict] = mapped_column(JSON, default=dict)
    explanation_template: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class FailureRateMetric(Base):
    __tablename__ = "failure_rates"
    __table_args__ = (
        UniqueConstraint(
            "computation_id",
            "pattern_id",
            "aggregation_level",
            "aggregation_key",
            name="uq_failure_rate_computation_scope",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    computation_id: Mapped[str] = mapped_column(String(36), index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    detection_execution_id: Mapped[str] = mapped_column(String(36), index=True)
    detected_pattern_id: Mapped[str] = mapped_column(String(36), index=True)
    pattern_id: Mapped[str] = mapped_column(String(128), index=True)
    aggregation_level: Mapped[str] = mapped_column(String(32), index=True)
    aggregation_key: Mapped[str] = mapped_column(String(512), index=True)
    formula_version: Mapped[str] = mapped_column(String(64))
    total_tests: Mapped[int] = mapped_column(BigInteger, default=0)
    pass_count: Mapped[int] = mapped_column(BigInteger, default=0)
    fail_count: Mapped[int] = mapped_column(BigInteger, default=0)
    failure_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    failure_density: Mapped[float] = mapped_column(Float, default=0.0)
    pattern_frequency: Mapped[float] = mapped_column(Float, default=0.0)
    moving_average: Mapped[float | None] = mapped_column(Float, nullable=True)
    baseline_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    historical_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    trend_status: Mapped[str] = mapped_column(String(32), default="insufficient_data")
    threshold_status: Mapped[str] = mapped_column(String(32), default="within_limit")
    threshold_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    severity_level: Mapped[str] = mapped_column(String(32), default="low")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class FailureStatistic(Base):
    __tablename__ = "failure_statistics"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    computation_id: Mapped[str] = mapped_column(String(36), index=True)
    aggregation_level: Mapped[str] = mapped_column(String(32), index=True)
    metric_count: Mapped[int] = mapped_column(Integer, default=0)
    mean_failure_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    median_failure_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    std_dev: Mapped[float] = mapped_column(Float, default=0.0)
    minimum: Mapped[float] = mapped_column(Float, default=0.0)
    maximum: Mapped[float] = mapped_column(Float, default=0.0)
    total_tests: Mapped[int] = mapped_column(BigInteger, default=0)
    total_failures: Mapped[int] = mapped_column(BigInteger, default=0)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class HistoricalFailureRate(Base):
    __tablename__ = "historical_failure_rates"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    failure_rate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("failure_rates.id", ondelete="CASCADE"), index=True
    )
    computation_id: Mapped[str] = mapped_column(String(36), index=True)
    pattern_id: Mapped[str] = mapped_column(String(128), index=True)
    aggregation_level: Mapped[str] = mapped_column(String(32), index=True)
    aggregation_key: Mapped[str] = mapped_column(String(512), index=True)
    failure_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    baseline_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    snapshot_version: Mapped[int] = mapped_column(Integer, default=1)
    source_computation_ids: Mapped[list] = mapped_column(JSON, default=list)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class FailureTrendAnalysis(Base):
    __tablename__ = "trend_analysis"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    computation_id: Mapped[str] = mapped_column(String(36), index=True)
    failure_rate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("failure_rates.id", ondelete="CASCADE"), index=True
    )
    pattern_id: Mapped[str] = mapped_column(String(128), index=True)
    aggregation_level: Mapped[str] = mapped_column(String(32), index=True)
    aggregation_key: Mapped[str] = mapped_column(String(512), index=True)
    trend_direction: Mapped[str] = mapped_column(String(32))
    current_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    moving_average: Mapped[float | None] = mapped_column(Float, nullable=True)
    baseline_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    absolute_change: Mapped[float | None] = mapped_column(Float, nullable=True)
    relative_change: Mapped[float | None] = mapped_column(Float, nullable=True)
    abnormal_increase: Mapped[bool] = mapped_column(Boolean, default=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ThresholdConfiguration(Base):
    __tablename__ = "threshold_configuration"
    __table_args__ = (
        UniqueConstraint(
            "configuration_key",
            "version",
            name="uq_threshold_configuration_key_version",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    configuration_key: Mapped[str] = mapped_column(String(128), index=True)
    version: Mapped[str] = mapped_column(String(64))
    pattern_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    aggregation_level: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    warning_percentage: Mapped[float] = mapped_column(Float)
    critical_percentage: Mapped[float] = mapped_column(Float)
    abnormal_delta_percentage: Mapped[float] = mapped_column(Float)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ComputationHistory(Base):
    __tablename__ = "computation_history"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    computation_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    detection_execution_id: Mapped[str] = mapped_column(String(36), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    formula_version: Mapped[str] = mapped_column(String(64))
    aggregation_levels: Mapped[list] = mapped_column(JSON, default=list)
    window_size: Mapped[int] = mapped_column(Integer, default=5)
    source_record_count: Mapped[int] = mapped_column(BigInteger, default=0)
    pattern_count: Mapped[int] = mapped_column(Integer, default=0)
    metric_count: Mapped[int] = mapped_column(Integer, default=0)
    processing_ms: Mapped[float] = mapped_column(Float, default=0.0)
    benchmark_metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    errors: Mapped[list] = mapped_column(JSON, default=list)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    actor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RecurringFailure(Base):
    __tablename__ = "recurring_failures"
    __table_args__ = (
        UniqueConstraint(
            "analysis_id",
            "canonical_recurrence_key",
            name="uq_recurring_failure_analysis_canonical",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    recurrence_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    detection_execution_id: Mapped[str] = mapped_column(String(36), index=True)
    computation_id: Mapped[str] = mapped_column(String(36), index=True)
    classification_execution_id: Mapped[str] = mapped_column(String(36), index=True)
    detected_pattern_id: Mapped[str] = mapped_column(String(36), index=True)
    pattern_id: Mapped[str] = mapped_column(String(128), index=True)
    pattern_name: Mapped[str] = mapped_column(String(256), default="")
    fault_type: Mapped[str] = mapped_column(String(128), index=True)
    canonical_recurrence_key: Mapped[str] = mapped_column(String(64), index=True)
    signature_hash: Mapped[str] = mapped_column(String(64), index=True)
    similarity_group: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    recurrence_count: Mapped[int] = mapped_column(BigInteger, default=0)
    recurrence_frequency: Mapped[float] = mapped_column(Float, default=0.0)
    recurrence_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    severity: Mapped[str] = mapped_column(String(32), default="low", index=True)
    trend_direction: Mapped[str] = mapped_column(String(32), default="stable", index=True)
    first_occurrence: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    latest_occurrence: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    historical_frequency: Mapped[float] = mapped_column(Float, default=0.0)
    hotspot_location: Mapped[dict] = mapped_column(JSON, default=dict)
    engineering_recommendation: Mapped[str] = mapped_column(Text, default="")
    config_version: Mapped[str] = mapped_column(String(64))
    incremental: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RecurrenceStatistic(Base):
    __tablename__ = "recurrence_statistics"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    scope_type: Mapped[str] = mapped_column(String(32), index=True)
    scope_key: Mapped[str] = mapped_column(String(512), index=True)
    pattern_count: Mapped[int] = mapped_column(Integer, default=0)
    recurrence_count: Mapped[int] = mapped_column(BigInteger, default=0)
    mean_frequency: Mapped[float] = mapped_column(Float, default=0.0)
    mean_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    hotspot_count: Mapped[int] = mapped_column(Integer, default=0)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RecurrenceHistory(Base):
    __tablename__ = "recurrence_history"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    recurrence_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("recurring_failures.recurrence_id", ondelete="CASCADE"), index=True
    )
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    pattern_id: Mapped[str] = mapped_column(String(128), index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    occurrence_count: Mapped[int] = mapped_column(BigInteger, default=0)
    frequency: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    snapshot_version: Mapped[int] = mapped_column(Integer, default=1)
    source_execution_ids: Mapped[list] = mapped_column(JSON, default=list)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RecurrenceTrend(Base):
    __tablename__ = "recurrence_trends"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    recurrence_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("recurring_failures.recurrence_id", ondelete="CASCADE"), index=True
    )
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    pattern_id: Mapped[str] = mapped_column(String(128), index=True)
    trend_direction: Mapped[str] = mapped_column(String(32), index=True)
    current_frequency: Mapped[float] = mapped_column(Float, default=0.0)
    historical_frequency: Mapped[float] = mapped_column(Float, default=0.0)
    absolute_change: Mapped[float] = mapped_column(Float, default=0.0)
    relative_change: Mapped[float | None] = mapped_column(Float, nullable=True)
    newly_emerging: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    time_series: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class HotspotAnalysis(Base):
    __tablename__ = "hotspot_analysis"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    hotspot_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    recurrence_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("recurring_failures.recurrence_id", ondelete="CASCADE"), index=True
    )
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    pattern_id: Mapped[str] = mapped_column(String(128), index=True)
    lot_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    wafer_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    x: Mapped[int | None] = mapped_column(Integer, nullable=True)
    y: Mapped[int | None] = mapped_column(Integer, nullable=True)
    radius: Mapped[float] = mapped_column(Float, default=0.0)
    occurrence_count: Mapped[int] = mapped_column(BigInteger, default=0)
    density: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    severity: Mapped[str] = mapped_column(String(32), default="low", index=True)
    coordinates: Mapped[list] = mapped_column(JSON, default=list)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EngineeringRecommendation(Base):
    __tablename__ = "engineering_recommendations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    recommendation_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    recurrence_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("recurring_failures.recurrence_id", ondelete="CASCADE"), index=True, nullable=True
    )
    correlation_id: Mapped[str | None] = mapped_column(
        String(36), index=True, nullable=True
    )
    source_module: Mapped[str] = mapped_column(String(32), default="FA-FR-005", index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    report_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    pattern_id: Mapped[str] = mapped_column(String(128), index=True)
    fault_type: Mapped[str] = mapped_column(String(128), index=True)
    recommendation_code: Mapped[str] = mapped_column(String(64), index=True)
    priority: Mapped[str] = mapped_column(String(32), index=True)
    action: Mapped[str] = mapped_column(Text)
    rationale: Mapped[str] = mapped_column(Text, default="")
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    config_version: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RecurrenceAuditLog(Base):
    __tablename__ = "recurrence_audit_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    detection_execution_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    computation_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    config_version: Mapped[str] = mapped_column(String(64), default="")
    source_record_count: Mapped[int] = mapped_column(BigInteger, default=0)
    pattern_count: Mapped[int] = mapped_column(Integer, default=0)
    recurrence_count: Mapped[int] = mapped_column(Integer, default=0)
    processing_ms: Mapped[float] = mapped_column(Float, default=0.0)
    benchmark_metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    errors: Mapped[list] = mapped_column(JSON, default=list)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    actor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class FailurePatternCorrelation(Base):
    __tablename__ = "failure_pattern_correlations"
    __table_args__ = (
        UniqueConstraint(
            "analysis_id",
            "canonical_correlation_key",
            name="uq_correlation_analysis_canonical",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    correlation_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    detection_execution_id: Mapped[str] = mapped_column(String(36), index=True)
    computation_id: Mapped[str] = mapped_column(String(36), index=True)
    classification_execution_id: Mapped[str] = mapped_column(String(36), index=True)
    recurrence_analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    recurrence_id: Mapped[str] = mapped_column(String(36), index=True)
    pattern_id: Mapped[str] = mapped_column(String(128), index=True)
    fault_type: Mapped[str] = mapped_column(String(128), index=True)
    canonical_correlation_key: Mapped[str] = mapped_column(String(64), index=True)
    correlated_failures: Mapped[int] = mapped_column(BigInteger, default=0)
    correlation_coefficient: Mapped[float] = mapped_column(Float, default=0.0)
    correlation_strength: Mapped[str] = mapped_column(String(32), index=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    p_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    sample_size: Mapped[int] = mapped_column(BigInteger, default=0)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    trend_status: Mapped[str] = mapped_column(String(32), index=True)
    hotspot_location: Mapped[dict] = mapped_column(JSON, default=dict)
    engineering_recommendation: Mapped[str] = mapped_column(Text, default="")
    algorithm: Mapped[str] = mapped_column(String(64))
    config_version: Mapped[str] = mapped_column(String(64))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    correlation_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CorrelationStatistic(Base):
    __tablename__ = "correlation_statistics"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    scope_type: Mapped[str] = mapped_column(String(32), index=True)
    scope_key: Mapped[str] = mapped_column(String(512), index=True)
    correlation_count: Mapped[int] = mapped_column(Integer, default=0)
    strong_count: Mapped[int] = mapped_column(Integer, default=0)
    mean_coefficient: Mapped[float] = mapped_column(Float, default=0.0)
    mean_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CorrelationHistory(Base):
    __tablename__ = "correlation_history"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    correlation_id: Mapped[str] = mapped_column(String(36), index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    pattern_id: Mapped[str] = mapped_column(String(128), index=True)
    fault_type: Mapped[str] = mapped_column(String(128), index=True)
    coefficient: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    snapshot_version: Mapped[int] = mapped_column(Integer, default=1)
    source_execution_ids: Mapped[list] = mapped_column(JSON, default=list)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CorrelationTrend(Base):
    __tablename__ = "correlation_trends"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    correlation_id: Mapped[str] = mapped_column(String(36), index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    pattern_id: Mapped[str] = mapped_column(String(128), index=True)
    fault_type: Mapped[str] = mapped_column(String(128), index=True)
    trend_status: Mapped[str] = mapped_column(String(32), index=True)
    current_coefficient: Mapped[float] = mapped_column(Float, default=0.0)
    historical_coefficient: Mapped[float] = mapped_column(Float, default=0.0)
    absolute_change: Mapped[float] = mapped_column(Float, default=0.0)
    time_series: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CorrelationAuditLog(Base):
    __tablename__ = "correlation_audit_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    config_version: Mapped[str] = mapped_column(String(64))
    source_record_count: Mapped[int] = mapped_column(BigInteger, default=0)
    pattern_count: Mapped[int] = mapped_column(Integer, default=0)
    correlation_count: Mapped[int] = mapped_column(Integer, default=0)
    processing_ms: Mapped[float] = mapped_column(Float, default=0.0)
    benchmark_metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    upstream_execution_ids: Mapped[dict] = mapped_column(JSON, default=dict)
    errors: Mapped[list] = mapped_column(JSON, default=list)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    actor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DieAnalysis(Base):
    """Immutable per-die FA-FR-007 analysis facts with exact upstream lineage."""

    __tablename__ = "die_analysis"
    __table_args__ = (
        UniqueConstraint(
            "analysis_id",
            "canonical_die_key",
            name="uq_die_analysis_canonical",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    die_result_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    detection_execution_id: Mapped[str] = mapped_column(String(36), index=True)
    computation_id: Mapped[str] = mapped_column(String(36), index=True)
    classification_execution_id: Mapped[str] = mapped_column(String(36), index=True)
    recurrence_analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    correlation_analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    lot_id: Mapped[str] = mapped_column(String(128), index=True)
    wafer_id: Mapped[str] = mapped_column(String(128), index=True)
    die_id: Mapped[str] = mapped_column(String(128), index=True)
    canonical_die_key: Mapped[str] = mapped_column(String(64), index=True)
    x: Mapped[float | None] = mapped_column(Float, nullable=True)
    y: Mapped[float | None] = mapped_column(Float, nullable=True)
    failure_count: Mapped[int] = mapped_column(BigInteger, default=0)
    total_tests: Mapped[int] = mapped_column(BigInteger, default=0)
    failure_density: Mapped[float] = mapped_column(Float, default=0.0)
    neighbor_failure_count: Mapped[int] = mapped_column(Integer, default=0)
    is_isolated: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_failing: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    health_score: Mapped[float] = mapped_column(Float, default=1.0)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    trend_status: Mapped[str] = mapped_column(String(32), index=True)
    dominant_fault_type: Mapped[str] = mapped_column(String(128), default="", index=True)
    dominant_pattern_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    hotspot_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    cluster_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    engineering_recommendation: Mapped[str] = mapped_column(Text, default="")
    lot_comparison: Mapped[dict] = mapped_column(JSON, default=dict)
    wafer_comparison: Mapped[dict] = mapped_column(JSON, default=dict)
    config_version: Mapped[str] = mapped_column(String(64))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DieFailureStatistic(Base):
    __tablename__ = "die_failure_statistics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    scope_type: Mapped[str] = mapped_column(String(32), index=True)
    scope_key: Mapped[str] = mapped_column(String(512), index=True)
    total_dies: Mapped[int] = mapped_column(Integer, default=0)
    failing_dies: Mapped[int] = mapped_column(Integer, default=0)
    isolated_failures: Mapped[int] = mapped_column(Integer, default=0)
    mean_failure_density: Mapped[float] = mapped_column(Float, default=0.0)
    mean_health_score: Mapped[float] = mapped_column(Float, default=0.0)
    mean_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    hotspot_count: Mapped[int] = mapped_column(Integer, default=0)
    cluster_count: Mapped[int] = mapped_column(Integer, default=0)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DieHotspot(Base):
    __tablename__ = "die_hotspots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hotspot_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    lot_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    wafer_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    center_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    center_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    radius: Mapped[float] = mapped_column(Float, default=0.0)
    die_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(BigInteger, default=0)
    density: Mapped[float] = mapped_column(Float, default=0.0)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    member_die_ids: Mapped[list] = mapped_column(JSON, default=list)
    coordinates: Mapped[list] = mapped_column(JSON, default=list)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DieCluster(Base):
    __tablename__ = "die_clusters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cluster_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    lot_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    wafer_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    algorithm: Mapped[str] = mapped_column(String(64), default="grid_union_find")
    die_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(BigInteger, default=0)
    density: Mapped[float] = mapped_column(Float, default=0.0)
    centroid_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    centroid_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    member_die_ids: Mapped[list] = mapped_column(JSON, default=list)
    coordinates: Mapped[list] = mapped_column(JSON, default=list)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DieHealthScore(Base):
    __tablename__ = "die_health_scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    die_result_id: Mapped[str] = mapped_column(String(36), index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    lot_id: Mapped[str] = mapped_column(String(128), index=True)
    wafer_id: Mapped[str] = mapped_column(String(128), index=True)
    die_id: Mapped[str] = mapped_column(String(128), index=True)
    health_score: Mapped[float] = mapped_column(Float, default=1.0)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    contributing_factors: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DieAnalysisHistory(Base):
    __tablename__ = "die_analysis_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    die_result_id: Mapped[str] = mapped_column(String(36), index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    lot_id: Mapped[str] = mapped_column(String(128), index=True)
    wafer_id: Mapped[str] = mapped_column(String(128), index=True)
    die_id: Mapped[str] = mapped_column(String(128), index=True)
    failure_count: Mapped[int] = mapped_column(BigInteger, default=0)
    failure_density: Mapped[float] = mapped_column(Float, default=0.0)
    health_score: Mapped[float] = mapped_column(Float, default=1.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    snapshot_version: Mapped[int] = mapped_column(Integer, default=1)
    source_execution_ids: Mapped[list] = mapped_column(JSON, default=list)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DieAuditLog(Base):
    __tablename__ = "die_audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    config_version: Mapped[str] = mapped_column(String(64))
    source_record_count: Mapped[int] = mapped_column(BigInteger, default=0)
    die_count: Mapped[int] = mapped_column(Integer, default=0)
    failing_die_count: Mapped[int] = mapped_column(Integer, default=0)
    hotspot_count: Mapped[int] = mapped_column(Integer, default=0)
    cluster_count: Mapped[int] = mapped_column(Integer, default=0)
    processing_ms: Mapped[float] = mapped_column(Float, default=0.0)
    benchmark_metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    upstream_execution_ids: Mapped[dict] = mapped_column(JSON, default=dict)
    errors: Mapped[list] = mapped_column(JSON, default=list)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    actor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WaferAnalysis(Base):
    """Immutable per-wafer FA-FR-008 analysis facts with exact upstream lineage."""

    __tablename__ = "wafer_analysis"
    __table_args__ = (
        UniqueConstraint(
            "analysis_id",
            "canonical_wafer_key",
            name="uq_wafer_analysis_canonical",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    wafer_result_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    detection_execution_id: Mapped[str] = mapped_column(String(36), index=True)
    computation_id: Mapped[str] = mapped_column(String(36), index=True)
    classification_execution_id: Mapped[str] = mapped_column(String(36), index=True)
    recurrence_analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    correlation_analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    die_analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    lot_id: Mapped[str] = mapped_column(String(128), index=True)
    wafer_id: Mapped[str] = mapped_column(String(128), index=True)
    canonical_wafer_key: Mapped[str] = mapped_column(String(64), index=True)
    total_dies: Mapped[int] = mapped_column(Integer, default=0)
    failing_dies: Mapped[int] = mapped_column(Integer, default=0)
    yield_pct: Mapped[float] = mapped_column(Float, default=100.0)
    failure_density: Mapped[float] = mapped_column(Float, default=0.0)
    edge_failure_rate: Mapped[float] = mapped_column(Float, default=0.0)
    center_failure_rate: Mapped[float] = mapped_column(Float, default=0.0)
    health_score: Mapped[float] = mapped_column(Float, default=1.0)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    trend_status: Mapped[str] = mapped_column(String(32), index=True)
    radial_distribution: Mapped[dict] = mapped_column(JSON, default=dict)
    lot_comparison: Mapped[dict] = mapped_column(JSON, default=dict)
    engineering_recommendation: Mapped[str] = mapped_column(Text, default="")
    config_version: Mapped[str] = mapped_column(String(64))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class WaferStatistic(Base):
    __tablename__ = "wafer_statistics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    scope_type: Mapped[str] = mapped_column(String(32), index=True)
    scope_key: Mapped[str] = mapped_column(String(512), index=True)
    total_wafers: Mapped[int] = mapped_column(Integer, default=0)
    failing_wafers: Mapped[int] = mapped_column(Integer, default=0)
    total_dies: Mapped[int] = mapped_column(Integer, default=0)
    failing_dies: Mapped[int] = mapped_column(Integer, default=0)
    mean_yield_pct: Mapped[float] = mapped_column(Float, default=100.0)
    mean_failure_density: Mapped[float] = mapped_column(Float, default=0.0)
    mean_health_score: Mapped[float] = mapped_column(Float, default=1.0)
    mean_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    hotspot_count: Mapped[int] = mapped_column(Integer, default=0)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class WaferHotspot(Base):
    __tablename__ = "wafer_hotspots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hotspot_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    lot_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    wafer_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    center_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    center_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    radius: Mapped[float] = mapped_column(Float, default=0.0)
    die_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(BigInteger, default=0)
    density: Mapped[float] = mapped_column(Float, default=0.0)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    member_die_ids: Mapped[list] = mapped_column(JSON, default=list)
    density_grid: Mapped[list] = mapped_column(JSON, default=list)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class WaferHealthScore(Base):
    __tablename__ = "wafer_health_scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    wafer_result_id: Mapped[str] = mapped_column(String(36), index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    lot_id: Mapped[str] = mapped_column(String(128), index=True)
    wafer_id: Mapped[str] = mapped_column(String(128), index=True)
    health_score: Mapped[float] = mapped_column(Float, default=1.0)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    contributing_factors: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class WaferYieldMetric(Base):
    __tablename__ = "wafer_yield_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    wafer_result_id: Mapped[str] = mapped_column(String(36), index=True)
    lot_id: Mapped[str] = mapped_column(String(128), index=True)
    wafer_id: Mapped[str] = mapped_column(String(128), index=True)
    yield_pct: Mapped[float] = mapped_column(Float, default=100.0)
    historical_yield_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    yield_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    trend_status: Mapped[str] = mapped_column(String(32), index=True)
    lot_yield_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class WaferAnalysisHistory(Base):
    __tablename__ = "wafer_analysis_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    wafer_result_id: Mapped[str] = mapped_column(String(36), index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    lot_id: Mapped[str] = mapped_column(String(128), index=True)
    wafer_id: Mapped[str] = mapped_column(String(128), index=True)
    yield_pct: Mapped[float] = mapped_column(Float, default=100.0)
    failure_density: Mapped[float] = mapped_column(Float, default=0.0)
    health_score: Mapped[float] = mapped_column(Float, default=1.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    snapshot_version: Mapped[int] = mapped_column(Integer, default=1)
    source_execution_ids: Mapped[list] = mapped_column(JSON, default=list)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class WaferAuditLog(Base):
    __tablename__ = "wafer_audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    config_version: Mapped[str] = mapped_column(String(64))
    source_die_count: Mapped[int] = mapped_column(Integer, default=0)
    wafer_count: Mapped[int] = mapped_column(Integer, default=0)
    failing_wafer_count: Mapped[int] = mapped_column(Integer, default=0)
    hotspot_count: Mapped[int] = mapped_column(Integer, default=0)
    processing_ms: Mapped[float] = mapped_column(Float, default=0.0)
    benchmark_metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    upstream_execution_ids: Mapped[dict] = mapped_column(JSON, default=dict)
    errors: Mapped[list] = mapped_column(JSON, default=list)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    actor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class FaultPrediction(Base):
    """Immutable per-pattern FA-FR-009 fault-type prediction with full lineage."""

    __tablename__ = "fault_predictions"
    __table_args__ = (
        UniqueConstraint(
            "execution_id",
            "canonical_prediction_key",
            name="uq_fault_prediction_canonical",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prediction_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    execution_id: Mapped[str] = mapped_column(String(36), index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    detection_execution_id: Mapped[str] = mapped_column(String(36), index=True)
    computation_id: Mapped[str] = mapped_column(String(36), index=True)
    classification_execution_id: Mapped[str] = mapped_column(String(36), index=True)
    recurrence_analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    correlation_analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    die_analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    wafer_analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    pattern_id: Mapped[str] = mapped_column(String(128), index=True)
    canonical_prediction_key: Mapped[str] = mapped_column(String(64), index=True)
    predicted_fault_type: Mapped[str] = mapped_column(String(128), index=True)
    alternative_fault_types: Mapped[list] = mapped_column(JSON, default=list)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    prediction_probability: Mapped[float] = mapped_column(Float, default=0.0)
    supporting_evidence: Mapped[list] = mapped_column(JSON, default=list)
    engineering_explanation: Mapped[str] = mapped_column(Text, default="")
    investigation_steps: Mapped[list] = mapped_column(JSON, default=list)
    model_version: Mapped[str] = mapped_column(String(64), index=True)
    config_version: Mapped[str] = mapped_column(String(64))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    predicted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prediction_id: Mapped[str] = mapped_column(String(36), index=True)
    execution_id: Mapped[str] = mapped_column(String(36), index=True)
    pattern_id: Mapped[str] = mapped_column(String(128), index=True)
    predicted_fault_type: Mapped[str] = mapped_column(String(128), index=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    prediction_probability: Mapped[float] = mapped_column(Float, default=0.0)
    snapshot_version: Mapped[int] = mapped_column(Integer, default=1)
    source_execution_ids: Mapped[list] = mapped_column(JSON, default=list)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PredictionStatistic(Base):
    __tablename__ = "prediction_statistics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id: Mapped[str] = mapped_column(String(36), index=True)
    scope_type: Mapped[str] = mapped_column(String(32), index=True)
    scope_key: Mapped[str] = mapped_column(String(512), index=True)
    total_predictions: Mapped[int] = mapped_column(Integer, default=0)
    high_confidence_count: Mapped[int] = mapped_column(Integer, default=0)
    mean_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    mean_probability: Mapped[float] = mapped_column(Float, default=0.0)
    top_fault_type: Mapped[str] = mapped_column(String(128), default="")
    top1_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    top3_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PredictionFeedback(Base):
    __tablename__ = "prediction_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    feedback_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    prediction_id: Mapped[str] = mapped_column(String(36), index=True)
    execution_id: Mapped[str] = mapped_column(String(36), index=True)
    pattern_id: Mapped[str] = mapped_column(String(128), index=True)
    validated_fault_type: Mapped[str] = mapped_column(String(128), index=True)
    feedback_status: Mapped[str] = mapped_column(String(32), index=True)
    engineer_notes: Mapped[str] = mapped_column(Text, default="")
    learning_weight: Mapped[float] = mapped_column(Float, default=1.0)
    actor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PredictionModel(Base):
    __tablename__ = "prediction_models"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    model_version: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    model_type: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    config_version: Mapped[str] = mapped_column(String(64))
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PredictionAuditLog(Base):
    __tablename__ = "prediction_audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id: Mapped[str] = mapped_column(String(36), index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    config_version: Mapped[str] = mapped_column(String(64))
    model_version: Mapped[str] = mapped_column(String(64), index=True)
    source_pattern_count: Mapped[int] = mapped_column(Integer, default=0)
    prediction_count: Mapped[int] = mapped_column(Integer, default=0)
    high_confidence_count: Mapped[int] = mapped_column(Integer, default=0)
    processing_ms: Mapped[float] = mapped_column(Float, default=0.0)
    benchmark_metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    upstream_execution_ids: Mapped[dict] = mapped_column(JSON, default=dict)
    errors: Mapped[list] = mapped_column(JSON, default=list)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    actor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReportTemplate(Base):
    __tablename__ = "report_templates"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    template_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(256))
    version: Mapped[str] = mapped_column(String(64), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    sections_json: Mapped[dict] = mapped_column(JSON, default=dict)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    report_name: Mapped[str] = mapped_column(String(256))
    report_version: Mapped[int] = mapped_column(Integer, default=1)
    template_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    completeness_score: Mapped[float] = mapped_column(Float, default=0.0)
    consistency_score: Mapped[float] = mapped_column(Float, default=0.0)
    traceability_json: Mapped[dict] = mapped_column(JSON, default=dict)
    upstream_execution_ids: Mapped[dict] = mapped_column(JSON, default=dict)
    report_json: Mapped[dict] = mapped_column(JSON, default=dict)
    dashboard_json: Mapped[dict] = mapped_column(JSON, default=dict)
    executive_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    engineering_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    benchmark_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    config_version: Mapped[str] = mapped_column(String(64), default="")
    actor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    processing_ms: Mapped[float] = mapped_column(Float, default=0.0)
    pdf_ms: Mapped[float] = mapped_column(Float, default=0.0)
    excel_ms: Mapped[float] = mapped_column(Float, default=0.0)
    export_ms: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReportHistory(Base):
    __tablename__ = "report_history"
    __table_args__ = (UniqueConstraint("report_id", "version", name="uq_report_history_version"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    report_id: Mapped[str] = mapped_column(String(36), index=True)
    version: Mapped[int] = mapped_column(Integer, index=True)
    snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    change_reason: Mapped[str] = mapped_column(String(256), default="")
    actor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ReportExport(Base):
    __tablename__ = "report_exports"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    export_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    report_id: Mapped[str] = mapped_column(String(36), index=True)
    format: Mapped[str] = mapped_column(String(16), index=True)
    file_path: Mapped[str] = mapped_column(String(1024), default="")
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    processing_ms: Mapped[float] = mapped_column(Float, default=0.0)
    actor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class BenchmarkResult(Base):
    __tablename__ = "benchmark_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    report_id: Mapped[str] = mapped_column(String(36), index=True)
    benchmark_type: Mapped[str] = mapped_column(String(64), index=True)
    metric_name: Mapped[str] = mapped_column(String(128), index=True)
    metric_value: Mapped[float] = mapped_column(Float, default=0.0)
    target_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ReportAuditLog(Base):
    __tablename__ = "report_audit_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    report_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    actor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    upload_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    template_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    export_format: Mapped[str | None] = mapped_column(String(16), nullable=True)
    processing_ms: Mapped[float] = mapped_column(Float, default=0.0)
    errors: Mapped[list] = mapped_column(JSON, default=list)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    benchmark_metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
