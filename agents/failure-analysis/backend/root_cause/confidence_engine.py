"""Confidence scoring for fused root cause predictions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FinalPrediction:
    scan_chain_id: str
    predicted_fault_type: str
    predicted_root_cause: str
    confidence_score: float
    method: str
    ai_explanation: str
    reasoning_steps: list[str] = field(default_factory=list)
    confidence_breakdown: dict[str, float] = field(default_factory=dict)
    similar_historical_cases: list[dict[str, Any]] = field(default_factory=list)
    engineering_recommendations: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    supporting_parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scan_chain_id": self.scan_chain_id,
            "predicted_fault_type": self.predicted_fault_type,
            "predicted_root_cause": self.predicted_root_cause,
            "confidence_score": round(self.confidence_score, 4),
            "method": self.method,
            "ai_explanation": self.ai_explanation,
            "reasoning_steps": self.reasoning_steps,
            "confidence_breakdown": self.confidence_breakdown,
            "similar_historical_cases": self.similar_historical_cases,
            "engineering_recommendations": self.engineering_recommendations,
            "evidence": self.evidence,
            "supporting_parameters": self.supporting_parameters,
        }


class ConfidenceEngine:
    """Fuse baseline, ML, RAG, and LLM signals into a final confidence score."""

    def __init__(
        self,
        *,
        baseline_weight: float = 0.30,
        ml_weight: float = 0.30,
        rag_weight: float = 0.20,
        llm_weight: float = 0.20,
    ) -> None:
        self.baseline_weight = baseline_weight
        self.ml_weight = ml_weight
        self.rag_weight = rag_weight
        self.llm_weight = llm_weight

    def finalize(
        self,
        *,
        ctx: dict[str, Any],
        baseline: dict[str, Any],
        ml: dict[str, Any] | None,
        similar_cases: list[dict[str, Any]],
        llm: dict[str, Any],
        recommendations: list[dict[str, Any]],
    ) -> FinalPrediction:
        baseline_conf = float(baseline.get("confidence_score", 0.0))
        ml_conf = float(ml.get("confidence", 0.0)) if ml else 0.0
        llm_conf = float(llm.get("confidence", 0.0))
        rag_conf = float(similar_cases[0].get("similarity_score", 0.0)) if similar_cases else 0.0

        fault_candidates = [
            baseline.get("predicted_fault_type"),
            ml.get("predicted_fault_type") if ml else None,
            llm.get("predicted_fault_type"),
        ]
        if similar_cases:
            fault_candidates.append(similar_cases[0].get("fault_type"))

        root_candidates = [
            baseline.get("predicted_root_cause", baseline.get("predicted_fault_type")),
            ml.get("predicted_root_cause") if ml else None,
            llm.get("predicted_root_cause"),
        ]
        if similar_cases:
            root_candidates.append(similar_cases[0].get("root_cause"))

        predicted_fault = _consensus([c for c in fault_candidates if c])
        predicted_root = _consensus([c for c in root_candidates if c])

        agreement = sum(
            1
            for c in fault_candidates
            if c and str(c).upper() in str(predicted_fault).upper()
        )
        agreement_boost = 0.05 * max(0, agreement - 1)

        final_conf = min(
            0.99,
            self.baseline_weight * baseline_conf
            + self.ml_weight * ml_conf
            + self.rag_weight * rag_conf
            + self.llm_weight * llm_conf
            + agreement_boost,
        )

        methods: list[str] = ["baseline"]
        if ml:
            methods.append("ml")
        if similar_cases:
            methods.append("rag")
        if llm.get("method") in ("llm", "langchain"):
            methods.append("llm")
        elif llm.get("method") == "heuristic":
            methods.append("heuristic")

        explanation = llm.get("explanation", baseline.get("evidence", [""])[0] if baseline.get("evidence") else "")
        steps = list(llm.get("reasoning_steps", []))

        return FinalPrediction(
            scan_chain_id=str(ctx.get("scan_chain_id", "")),
            predicted_fault_type=str(predicted_fault),
            predicted_root_cause=str(predicted_root),
            confidence_score=final_conf,
            method="+".join(methods),
            ai_explanation=str(explanation),
            reasoning_steps=steps,
            confidence_breakdown={
                "baseline": round(baseline_conf, 4),
                "ml": round(ml_conf, 4),
                "rag": round(rag_conf, 4),
                "llm": round(llm_conf, 4),
                "agreement_boost": round(agreement_boost, 4),
            },
            similar_historical_cases=similar_cases,
            engineering_recommendations=recommendations,
            evidence=list(baseline.get("evidence", [])),
            supporting_parameters={
                "failure_count": ctx.get("failure_count"),
                "affected_dies": ctx.get("affected_dies"),
                "affected_lots": ctx.get("affected_lots"),
                "is_recurring": ctx.get("is_recurring"),
                "primary_hint": ctx.get("primary_hint"),
                "primary_fault_category": ctx.get("primary_fault_category"),
            },
        )


def _consensus(candidates: list[Any]) -> str:
    if not candidates:
        return "UNKNOWN"
    counts: dict[str, int] = {}
    for c in candidates:
        key = str(c)
        counts[key] = counts.get(key, 0) + 1
    return max(counts, key=counts.get)
