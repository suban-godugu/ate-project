"""Dashboard dataset builder for the evaluation UI / API."""

from __future__ import annotations

from typing import Any


def build_evaluation_dashboard(report: dict[str, Any]) -> dict[str, Any]:
    inventory = report.get("inventory", {})
    pass_fail = report.get("pass_fail_summary", {})
    dataset_results = report.get("dataset_results", [])

    validation_rows: list[dict[str, Any]] = []
    metric_cards: list[dict[str, Any]] = []
    progress: list[dict[str, Any]] = []

    for dataset in dataset_results:
        dataset_id = dataset.get("dataset", {}).get("dataset_id", "")
        scale = dataset.get("dataset", {}).get("scale_token", "")
        ai = dataset.get("ai_evaluation", {})
        metric_cards.append(
            {
                "dataset_id": dataset_id,
                "scale": scale,
                "accuracy": ai.get("accuracy"),
                "precision": ai.get("precision"),
                "recall": ai.get("recall"),
                "f1_score": ai.get("f1_score"),
                "roc_auc": ai.get("roc_auc"),
                "engineering_score": ai.get("engineering_score"),
                "prediction_confidence": ai.get("prediction_confidence"),
            }
        )
        for item in dataset.get("validation", []):
            validation_rows.append(
                {
                    "dataset_id": dataset_id,
                    "module": item.get("module"),
                    "status": item.get("status"),
                    "explanation": item.get("explanation"),
                    "duration_ms": item.get("duration_ms"),
                }
            )
            progress.append(
                {
                    "dataset_id": dataset_id,
                    "module": item.get("module"),
                    "status": item.get("status"),
                }
            )

    training = report.get("latest_training") or {}
    stages = []
    for dataset in dataset_results:
        for stage in dataset.get("benchmark", {}).get("stages", []):
            stages.append(
                {
                    "dataset_id": dataset.get("dataset", {}).get("dataset_id"),
                    **stage,
                }
            )

    return {
        "summary_cards": [
            {"label": "STIL Files", "value": inventory.get("stil_count", 0)},
            {"label": "Log Files", "value": inventory.get("log_count", 0)},
            {"label": "Datasets Evaluated", "value": report.get("datasets_evaluated", 0)},
            {"label": "PASS", "value": pass_fail.get("PASS", 0)},
            {"label": "FAIL", "value": pass_fail.get("FAIL", 0)},
            {"label": "WARNING", "value": pass_fail.get("WARNING", 0)},
            {
                "label": "Model Version",
                "value": training.get("model_version") or "n/a",
            },
            {
                "label": "Training Status",
                "value": "trained" if training.get("trained") else "not_trained",
            },
        ],
        "dataset_inventory": inventory.get("bundles", []),
        "validation_status": validation_rows,
        "execution_progress": progress,
        "ai_metrics": metric_cards,
        "benchmark_stages": stages,
        "model_performance": training.get("comparisons", []),
        "training_status": training,
        "pass_fail_summary": pass_fail,
        "charts": {
            "pass_fail_bar": {
                "type": "bar",
                "x": list(pass_fail.keys()),
                "y": list(pass_fail.values()),
            },
            "accuracy_by_dataset": {
                "type": "bar",
                "x": [m.get("dataset_id") for m in metric_cards],
                "y": [m.get("accuracy") or 0 for m in metric_cards],
            },
            "benchmark_avg_ms": {
                "type": "bar",
                "x": [s.get("name") for s in stages],
                "y": [s.get("avg_ms") for s in stages],
            },
        },
    }
