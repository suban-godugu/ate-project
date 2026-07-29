"""Independent AI Evaluation, Validation & Model Training Framework."""

from __future__ import annotations

__all__ = ["EvaluationOrchestrator"]


def __getattr__(name: str):
    if name == "EvaluationOrchestrator":
        from evaluation.pipeline_orchestrator import EvaluationOrchestrator

        return EvaluationOrchestrator
    raise AttributeError(name)
