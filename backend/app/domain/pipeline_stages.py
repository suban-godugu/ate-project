"""Pipeline stage keys for Scan Chain upload → parse → orchestrate → dashboard."""

from __future__ import annotations

from enum import StrEnum


class PipelineStage(StrEnum):
    uploading = "uploading"
    validating = "validating"
    detecting_format = "detecting_format"
    parsing = "parsing"
    generating_metadata = "generating_metadata"
    normalizing = "normalizing"
    running_pattern = "running_pattern"
    running_failure = "running_failure"
    running_scan_diagnosis = "running_scan_diagnosis"
    aggregating = "aggregating"
    saving = "saving"
    refreshing_dashboard = "refreshing_dashboard"
    completed = "completed"
    failed = "failed"


# Ordered stages created on upload (excluding terminal failed)
PIPELINE_STEP_DEFS: list[tuple[str, str]] = [
    (PipelineStage.uploading, "Uploading"),
    (PipelineStage.validating, "Validating"),
    (PipelineStage.detecting_format, "Detecting Format"),
    (PipelineStage.parsing, "Parsing"),
    (PipelineStage.generating_metadata, "Generating Metadata"),
    (PipelineStage.normalizing, "Normalizing"),
    (PipelineStage.running_pattern, "Running Pattern Analysis"),
    (PipelineStage.running_failure, "Running Failure Analysis"),
    (PipelineStage.running_scan_diagnosis, "Running Scan Diagnosis"),
    (PipelineStage.aggregating, "Aggregating Results"),
    (PipelineStage.saving, "Saving Results"),
    (PipelineStage.refreshing_dashboard, "Refreshing Dashboard"),
    (PipelineStage.completed, "Completed"),
]

STAGE_PERCENT: dict[str, int] = {
    PipelineStage.uploading: 5,
    PipelineStage.validating: 10,
    PipelineStage.detecting_format: 15,
    PipelineStage.parsing: 30,
    PipelineStage.generating_metadata: 40,
    PipelineStage.normalizing: 50,
    PipelineStage.running_pattern: 60,
    PipelineStage.running_failure: 70,
    PipelineStage.running_scan_diagnosis: 80,
    PipelineStage.aggregating: 88,
    PipelineStage.saving: 94,
    PipelineStage.refreshing_dashboard: 98,
    PipelineStage.completed: 100,
    PipelineStage.failed: 0,
}

AGENT_STAGES = {
    PipelineStage.running_pattern,
    PipelineStage.running_failure,
    PipelineStage.running_scan_diagnosis,
    PipelineStage.aggregating,
    PipelineStage.saving,
    PipelineStage.refreshing_dashboard,
}
