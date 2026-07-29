"""Stage-level retry helpers."""

from __future__ import annotations

from app.domain.pipeline_stages import PipelineStage

RETRYABLE_FROM: dict[str, list[str]] = {
    PipelineStage.running_pattern: [
        PipelineStage.running_pattern,
        PipelineStage.running_failure,
        PipelineStage.running_scan_diagnosis,
        PipelineStage.aggregating,
        PipelineStage.saving,
        PipelineStage.refreshing_dashboard,
        PipelineStage.completed,
    ],
    PipelineStage.running_failure: [
        PipelineStage.running_pattern,
        PipelineStage.running_failure,
        PipelineStage.running_scan_diagnosis,
        PipelineStage.aggregating,
        PipelineStage.saving,
        PipelineStage.refreshing_dashboard,
        PipelineStage.completed,
    ],
    PipelineStage.running_scan_diagnosis: [
        PipelineStage.running_scan_diagnosis,
        PipelineStage.aggregating,
        PipelineStage.saving,
        PipelineStage.refreshing_dashboard,
        PipelineStage.completed,
    ],
    PipelineStage.aggregating: [
        PipelineStage.aggregating,
        PipelineStage.saving,
        PipelineStage.refreshing_dashboard,
        PipelineStage.completed,
    ],
    PipelineStage.parsing: [
        PipelineStage.validating,
        PipelineStage.detecting_format,
        PipelineStage.parsing,
        PipelineStage.generating_metadata,
        PipelineStage.normalizing,
        PipelineStage.running_pattern,
        PipelineStage.running_failure,
        PipelineStage.running_scan_diagnosis,
        PipelineStage.aggregating,
        PipelineStage.saving,
        PipelineStage.refreshing_dashboard,
        PipelineStage.completed,
    ],
}


def normalize_retry_stage(stage: str | None, failed_stage: str | None) -> str:
    if stage:
        return stage
    if failed_stage in (
        PipelineStage.running_pattern,
        PipelineStage.running_failure,
        PipelineStage.running_scan_diagnosis,
        PipelineStage.aggregating,
        PipelineStage.saving,
        PipelineStage.refreshing_dashboard,
    ):
        return failed_stage
    return PipelineStage.running_pattern
