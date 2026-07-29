"""Main FA-FR-009 root cause prediction engine orchestrator."""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

from adapters.schema import TestRecord
from adapters.yaml_config import load_adapter_configs
from analyzer import (
    correlate_failures_with_patterns,
    identify_recurring_failures,
    predict_fault_types,
)
from backend.root_cause.confidence_engine import ConfidenceEngine
from backend.root_cause.feature_extraction import (
    extract_cluster_contexts,
    labeled_training_samples,
    signature_hash,
)
from backend.root_cause.llm_reasoning import LLMReasoner
from backend.root_cause.ml_prediction import MLPredictor
from backend.root_cause.rag_engine import RAGEngine
from backend.root_cause.recommendation_engine import RecommendationEngine
from ingestor import DieLog

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "root_cause.yaml"


class RootCauseEngine:
    """
    AI root cause prediction pipeline:
    features → historical retrieval → ML → LLM reasoning → confidence → recommendations
    """

    def __init__(
        self,
        *,
        config_path: Path | str | None = None,
        enable_ml: bool | None = None,
        enable_llm: bool | None = None,
    ) -> None:
        raw = load_adapter_configs(Path(config_path) if config_path else DEFAULT_CONFIG)
        perf = raw.get("performance", {})
        models = raw.get("models", {})
        rag_cfg = raw.get("rag", {})
        conf_cfg = raw.get("confidence", {})
        pred_cfg = raw.get("prediction", {})

        self.prediction_target_ms = int(perf.get("prediction_target_ms", 5000))
        self.semantic_search_target_ms = int(perf.get("semantic_search_target_ms", 2000))
        self.top_n = int(pred_cfg.get("top_n", 50))
        self.ranked_queue_size = int(pred_cfg.get("include_ranked_queue", 20))
        self.recurring_min_lots = int(pred_cfg.get("recurring_min_lots", 2))

        ml_enabled = enable_ml if enable_ml is not None else bool(models.get("enable_ml", True))
        llm_enabled = enable_llm if enable_llm is not None else bool(models.get("enable_llm", True))

        kb_path = Path(rag_cfg.get("knowledge_base_path", "config/root_cause_knowledge.yaml"))
        if not kb_path.is_absolute():
            kb_path = Path(__file__).resolve().parents[2] / kb_path

        self.rag = RAGEngine(
            knowledge_base_path=kb_path,
            top_k=int(rag_cfg.get("top_k", 5)),
            similarity_threshold=float(rag_cfg.get("similarity_threshold", 0.35)),
            embedding_model=str(rag_cfg.get("embedding_model", "all-MiniLM-L6-v2")),
            use_faiss=bool(rag_cfg.get("use_faiss", True)),
        )
        self.ml = (
            MLPredictor(
                prefer_xgboost=bool(models.get("prefer_xgboost", True)),
                min_samples=int(models.get("ml_min_training_samples", 4)),
            )
            if ml_enabled
            else None
        )
        self.llm = LLMReasoner(
            model=str(models.get("llm_model", "gpt-4o-mini")),
            enabled=llm_enabled,
        )
        self.confidence = ConfidenceEngine(
            baseline_weight=float(conf_cfg.get("baseline_weight", 0.30)),
            ml_weight=float(conf_cfg.get("ml_weight", 0.30)),
            rag_weight=float(conf_cfg.get("rag_weight", 0.20)),
            llm_weight=float(conf_cfg.get("llm_weight", 0.20)),
        )
        self.recommendations = RecommendationEngine()

    def predict(
        self,
        *,
        die_logs: list[DieLog],
        test_records: list[TestRecord] | None = None,
        upload_id: str | None = None,
        recurring: dict[str, Any] | None = None,
        correlation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        search_times: list[float] = []

        if recurring is None:
            recurring = identify_recurring_failures(
                die_logs, test_records=test_records, min_lots=self.recurring_min_lots
            )
        if correlation is None:
            correlation = correlate_failures_with_patterns(
                die_logs, test_records=test_records, recurring_failures=recurring
            )

        baseline_report = predict_fault_types(
            die_logs, recurring, correlation, top_n=self.top_n
        )
        baseline_by_chain = {
            p["scan_chain_id"]: p for p in baseline_report.get("predictions", [])
        }

        contexts = extract_cluster_contexts(
            die_logs,
            test_records=test_records,
            recurring=recurring,
            correlation=correlation,
            recurring_min_lots=self.recurring_min_lots,
        )

        ml_trained = False
        if self.ml:
            labeled = labeled_training_samples(contexts)
            ml_trained = self.ml.train(labeled)

        predictions: list[dict[str, Any]] = []
        for ctx in contexts:
            chain_id = ctx["scan_chain_id"]
            baseline = baseline_by_chain.get(
                chain_id,
                {
                    "scan_chain_id": chain_id,
                    "predicted_fault_type": ctx.get("primary_hint") or "UNKNOWN",
                    "predicted_root_cause": ctx.get("primary_hint") or "UNKNOWN",
                    "confidence_score": 0.3,
                    "evidence": [],
                },
            )

            similar_cases, search_ms = self.rag.search_for_context(ctx)
            search_times.append(search_ms)

            ml_result = None
            if self.ml and self.ml.is_trained:
                ml_pred = self.ml.predict(ctx["features"], ctx)
                if ml_pred:
                    ml_result = ml_pred.to_dict()

            llm_result = self.llm.reason(
                ctx=ctx,
                baseline=baseline,
                ml=ml_result,
                similar_cases=similar_cases,
            ).to_dict()

            recs = self.recommendations.recommend(
                prediction={
                    "predicted_fault_type": llm_result.get("predicted_fault_type"),
                    "predicted_root_cause": llm_result.get("predicted_root_cause"),
                    "confidence_score": llm_result.get("confidence", 0.5),
                },
                similar_cases=similar_cases,
                ctx=ctx,
            )

            final = self.confidence.finalize(
                ctx=ctx,
                baseline=baseline,
                ml=ml_result,
                similar_cases=similar_cases,
                llm=llm_result,
                recommendations=recs,
            )
            row = final.to_dict()
            row["prediction_id"] = str(uuid.uuid4())
            row["failure_count"] = ctx.get("failure_count", 0)
            row["affected_dies"] = ctx.get("affected_dies", 0)
            row["affected_lots"] = ctx.get("affected_lots", 0)
            row["affected_wafers"] = ctx.get("affected_wafers", 0)
            row["pattern_count"] = ctx.get("pattern_count", 0)
            row["failure_signature"] = signature_hash(ctx)
            row["ml_prediction"] = ml_result
            row["baseline_prediction"] = {
                "predicted_fault_type": baseline.get("predicted_fault_type"),
                "confidence_score": baseline.get("confidence_score"),
            }
            predictions.append(row)

        predictions.sort(
            key=lambda p: (p["confidence_score"], p.get("failure_count", 0)),
            reverse=True,
        )

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        max_search_ms = max(search_times) if search_times else 0.0
        avg_confidence = (
            sum(p["confidence_score"] for p in predictions) / len(predictions)
            if predictions
            else 0.0
        )

        root_cause_report = _build_root_cause_report(predictions, baseline_report)

        return {
            "requirement": "FA-FR-009",
            "upload_id": upload_id,
            "processing_ms": elapsed_ms,
            "semantic_search_ms": round(max_search_ms, 2),
            "meets_performance_target": (
                elapsed_ms < self.prediction_target_ms
                and max_search_ms < self.semantic_search_target_ms
            ),
            "ml_model_trained": ml_trained,
            "detection_pipeline": [
                "feature_engineering",
                "historical_pattern_retrieval",
                "machine_learning_prediction",
                "llm_engineering_reasoning",
                "confidence_calculation",
                "recommendation_generation",
            ],
            "phase": baseline_report.get("phase", "FAULT_TYPE_PREDICTION"),
            "phase_description": baseline_report.get("phase_description", ""),
            "total_predictions": len(predictions),
            "average_confidence": round(avg_confidence, 4),
            "predictions": predictions[: self.top_n],
            "ranked_hypothesis_queue": [
                {
                    "rank": idx + 1,
                    "scan_chain_id": p["scan_chain_id"],
                    "predicted_fault_type": p["predicted_fault_type"],
                    "predicted_root_cause": p["predicted_root_cause"],
                    "confidence_score": p["confidence_score"],
                }
                for idx, p in enumerate(predictions[: self.ranked_queue_size])
            ],
            "similar_historical_cases": _aggregate_similar_cases(predictions),
            "engineering_recommendations": _aggregate_recommendations(predictions),
            "ai_explanations": [
                {
                    "scan_chain_id": p["scan_chain_id"],
                    "explanation": p["ai_explanation"],
                    "reasoning_steps": p.get("reasoning_steps", []),
                }
                for p in predictions[:10]
            ],
            "root_cause_report": root_cause_report,
            "engineering_dashboard": {
                "summary": {
                    "total_predictions": len(predictions),
                    "average_confidence": round(avg_confidence, 4),
                    "high_confidence_count": sum(
                        1 for p in predictions if p["confidence_score"] >= 0.75
                    ),
                    "recurring_chain_count": sum(
                        1 for c in contexts if c.get("is_recurring")
                    ),
                },
                "top_predictions": predictions[:10],
                "recommendation_summary": _aggregate_recommendations(predictions)[:15],
            },
            "legacy_baseline": baseline_report,
        }


def _build_root_cause_report(
    predictions: list[dict[str, Any]],
    baseline: dict[str, Any],
) -> dict[str, Any]:
    if not predictions:
        return {"status": "no_failures", "summary": "No failing patterns to analyze."}

    top = predictions[0]
    return {
        "status": "completed",
        "executive_summary": (
            f"Top hypothesis: {top['predicted_fault_type']} on scan chain "
            f"{top['scan_chain_id']} (confidence={top['confidence_score']:.2f})."
        ),
        "top_root_cause": top["predicted_root_cause"],
        "top_fault_type": top["predicted_fault_type"],
        "confidence_score": top["confidence_score"],
        "prediction_count": len(predictions),
        "high_confidence_predictions": [
            p for p in predictions if p["confidence_score"] >= 0.75
        ][:10],
        "methodology": baseline.get("phase_description", ""),
    }


def _aggregate_similar_cases(predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    cases: list[dict[str, Any]] = []
    for pred in predictions:
        for case in pred.get("similar_historical_cases", []):
            cid = str(case.get("case_id", ""))
            if cid in seen:
                continue
            seen.add(cid)
            cases.append(case)
    cases.sort(key=lambda c: c.get("similarity_score", 0), reverse=True)
    return cases[:20]


def _aggregate_recommendations(predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    recs: list[dict[str, Any]] = []
    for pred in predictions:
        for rec in pred.get("engineering_recommendations", []):
            action = rec.get("action", "")
            if action in seen:
                continue
            seen.add(action)
            recs.append({**rec, "scan_chain_id": pred.get("scan_chain_id")})
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    recs.sort(key=lambda r: priority_order.get(r.get("priority", "LOW"), 9))
    return recs
