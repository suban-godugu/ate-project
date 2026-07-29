"""Agent improvement analysis for the evaluation workbench."""

from __future__ import annotations

from typing import Any


def compute_ai_health_score(report: dict[str, Any]) -> dict[str, Any]:
    """Compute 0-100 AI health score from evaluation report."""
    dataset_results = report.get("dataset_results", [])
    if not dataset_results:
        return {"score": 0, "rating": "Poor", "factors": []}

    ds = dataset_results[0]
    ai = ds.get("ai_evaluation", {})
    validation = ds.get("validation", [])
    benchmark = ds.get("benchmark", {})
    pass_fail = report.get("pass_fail_summary", {})

    accuracy = float(ai.get("accuracy") or 0) * 100
    f1 = float(ai.get("f1_score") or 0) * 100
    eng = float(ai.get("engineering_score") or 0) * 100
    pred_conf = float(ai.get("prediction_confidence") or 0) * 100
    sim_acc = float(ai.get("similarity_accuracy") or 0) * 100
    rec_acc = float(ai.get("recommendation_accuracy") or 0) * 100

    pass_count = int(pass_fail.get("PASS", 0))
    fail_count = int(pass_fail.get("FAIL", 0))
    warn_count = int(pass_fail.get("WARNING", 0))
    total_checks = max(pass_count + fail_count + warn_count, 1)
    fr_score = (pass_count + 0.5 * warn_count) / total_checks * 100

    perf_score = 100.0
    for stage in benchmark.get("stages", []):
        if stage.get("meets_target") is False:
            perf_score -= 8

    score = round(
        0.20 * accuracy
        + 0.15 * f1
        + 0.15 * eng
        + 0.10 * pred_conf
        + 0.10 * sim_acc
        + 0.10 * rec_acc
        + 0.20 * fr_score,
        1,
    )
    score = max(0, min(100, score))

    if score >= 90:
        rating = "Excellent"
    elif score >= 75:
        rating = "Good"
    elif score >= 55:
        rating = "Needs Improvement"
    else:
        rating = "Poor"

    return {
        "score": score,
        "rating": rating,
        "factors": {
            "accuracy_pct": round(accuracy, 1),
            "f1_pct": round(f1, 1),
            "engineering_score_pct": round(eng, 1),
            "prediction_confidence_pct": round(pred_conf, 1),
            "functional_requirement_pct": round(fr_score, 1),
            "performance_pct": round(perf_score, 1),
        },
    }


def generate_improvement_recommendations(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Analyze evaluation report and produce prioritized engineering recommendations."""
    recs: list[dict[str, Any]] = []
    dataset_results = report.get("dataset_results", [])

    for ds in dataset_results:
        dataset_id = ds.get("dataset", {}).get("dataset_id", "unknown")
        validation = {v["module"]: v for v in ds.get("validation", [])}
        ai = ds.get("ai_evaluation", {})
        benchmark = ds.get("benchmark", {})
        training = ds.get("training", {})
        modules = ds.get("module_outputs", {})

        for module, result in validation.items():
            status = result.get("status")
            if status == "FAIL":
                recs.append(
                    {
                        "priority": "High",
                        "category": "Functional Validation",
                        "module": module,
                        "dataset_id": dataset_id,
                        "recommendation": f"{module} failed validation: {result.get('explanation', '')}",
                        "rationale": "Functional requirement must pass before production deployment.",
                    }
                )
            elif status == "WARNING":
                recs.append(
                    {
                        "priority": "Medium",
                        "category": "Functional Validation",
                        "module": module,
                        "dataset_id": dataset_id,
                        "recommendation": f"Review {module} warning: {result.get('explanation', '')}",
                        "rationale": "Partial compliance detected; investigate before release.",
                    }
                )

        acc = float(ai.get("accuracy") or 0)
        if acc < 0.85:
            recs.append(
                {
                    "priority": "High",
                    "category": "AI Accuracy",
                    "module": "AI Evaluation",
                    "dataset_id": dataset_id,
                    "recommendation": "Classification accuracy is below 85%; retrain models or refine taxonomy rules.",
                    "rationale": f"Current accuracy={acc:.2%}.",
                }
            )

        pred_conf = float(ai.get("prediction_confidence") or 0)
        if pred_conf < 0.6:
            recs.append(
                {
                    "priority": "High",
                    "category": "Prediction Quality",
                    "module": "FA-FR-009",
                    "dataset_id": dataset_id,
                    "recommendation": "Root cause prediction confidence is low; improve RAG knowledge base and LLM prompts.",
                    "rationale": f"Average prediction confidence={pred_conf:.2f}.",
                }
            )

        for stage in benchmark.get("stages", []):
            if stage.get("meets_target") is False:
                recs.append(
                    {
                        "priority": "Medium",
                        "category": "Performance",
                        "module": stage.get("name", ""),
                        "dataset_id": dataset_id,
                        "recommendation": (
                            f"Execution time for '{stage.get('name')}' ({stage.get('avg_ms')}ms) "
                            "exceeds recommended threshold."
                        ),
                        "rationale": "Optimize pipeline stage or increase hardware resources.",
                    }
                )

        if not training.get("trained"):
            reason = training.get("reason", "")
            if "Insufficient" in str(reason):
                recs.append(
                    {
                        "priority": "Low",
                        "category": "Model Training",
                        "module": "Training Pipeline",
                        "dataset_id": dataset_id,
                        "recommendation": "Increase labelled sample count to enable supervised model training.",
                        "rationale": reason,
                    }
                )

        fr004 = modules.get("FA-FR-004", {})
        avg_conf = float(fr004.get("average_confidence") or 0)
        if avg_conf < 0.75 and fr004.get("total_faults", 0) > 0:
            recs.append(
                {
                    "priority": "Medium",
                    "category": "Classification",
                    "module": "FA-FR-004",
                    "dataset_id": dataset_id,
                    "recommendation": "Classification confidence is low; review rule engine thresholds and ML training data.",
                    "rationale": f"Average classification confidence={avg_conf:.2f}.",
                }
            )

        fr006 = modules.get("FA-FR-006", {})
        if fr006.get("correlation_rows", 0) == 0:
            recs.append(
                {
                    "priority": "Medium",
                    "category": "Correlation",
                    "module": "FA-FR-006",
                    "dataset_id": dataset_id,
                    "recommendation": "Correlation engine produced empty results; verify statistical normalization and input features.",
                    "rationale": "No correlation relationships ranked for this dataset sample.",
                }
            )

    if not recs:
        recs.append(
            {
                "priority": "Low",
                "category": "Production Readiness",
                "module": "Overall",
                "dataset_id": "all",
                "recommendation": "All checks passed within thresholds. Proceed with extended benchmark on full datasets.",
                "rationale": "No critical issues detected in latest evaluation run.",
            }
        )

    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    recs.sort(key=lambda r: priority_order.get(r.get("priority", "Low"), 9))
    return recs


def production_readiness(report: dict[str, Any]) -> dict[str, Any]:
    """Summarize whether agent is production-ready."""
    pass_fail = report.get("pass_fail_summary", {})
    fail_count = int(pass_fail.get("FAIL", 0))
    health = compute_ai_health_score(report)

    ready = fail_count == 0 and health["score"] >= 75
    blockers: list[str] = []
    if fail_count:
        blockers.append(f"{fail_count} functional requirement(s) failed")
    if health["score"] < 75:
        blockers.append(f"AI health score {health['score']} below 75 threshold")

    return {
        "production_ready": ready,
        "ai_health_score": health["score"],
        "ai_health_rating": health["rating"],
        "blockers": blockers,
        "pass_count": pass_fail.get("PASS", 0),
        "fail_count": fail_count,
        "warning_count": pass_fail.get("WARNING", 0),
    }
