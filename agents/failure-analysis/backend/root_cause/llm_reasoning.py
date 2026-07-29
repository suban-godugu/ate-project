"""LLM-based engineering reasoning (separate from ML inference)."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LLMReasoning:
    predicted_fault_type: str
    predicted_root_cause: str
    confidence: float
    explanation: str
    reasoning_steps: list[str] = field(default_factory=list)
    method: str = "llm"

    def to_dict(self) -> dict[str, Any]:
        return {
            "predicted_fault_type": self.predicted_fault_type,
            "predicted_root_cause": self.predicted_root_cause,
            "confidence": round(self.confidence, 4),
            "explanation": self.explanation,
            "reasoning_steps": self.reasoning_steps,
            "method": self.method,
        }


class LLMReasoner:
    """
    Engineering reasoning layer using OpenAI/Azure when configured.
    Optional LangChain integration; deterministic heuristic fallback otherwise.
    """

    def __init__(self, *, model: str = "gpt-4o-mini", enabled: bool = True) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("OPENAI_MODEL", model)
        self.enabled = enabled and bool(self.api_key)

    def reason(
        self,
        *,
        ctx: dict[str, Any],
        baseline: dict[str, Any],
        ml: dict[str, Any] | None,
        similar_cases: list[dict[str, Any]],
    ) -> LLMReasoning:
        if self.enabled:
            result = self._call_openai(ctx, baseline, ml, similar_cases)
            if result:
                return result

            langchain_result = self._call_langchain(ctx, baseline, ml, similar_cases)
            if langchain_result:
                return langchain_result

        return self._heuristic_reason(ctx, baseline, ml, similar_cases)

    def _heuristic_reason(
        self,
        ctx: dict[str, Any],
        baseline: dict[str, Any],
        ml: dict[str, Any] | None,
        similar_cases: list[dict[str, Any]],
    ) -> LLMReasoning:
        """Deterministic explainable reasoning when LLM is unavailable."""
        fault_type = baseline.get("predicted_fault_type", ctx.get("primary_hint", "UNKNOWN"))
        root_cause = fault_type
        steps: list[str] = []

        if similar_cases:
            best = similar_cases[0]
            fault_type = str(best.get("fault_type", fault_type))
            root_cause = str(best.get("root_cause", root_cause))
            steps.append(
                f"Retrieved historical case {best.get('case_id')} "
                f"(similarity={best.get('similarity_score', 0):.2f})."
            )

        if ml and ml.get("confidence", 0) > baseline.get("confidence_score", 0):
            fault_type = str(ml.get("predicted_fault_type", fault_type))
            root_cause = str(ml.get("predicted_root_cause", root_cause))
            steps.append(f"ML model '{ml.get('model_id')}' supports this hypothesis.")

        if ctx.get("is_recurring"):
            steps.append(
                f"Failure is recurring across {ctx.get('affected_lots', 0)} lot(s) — "
                "systematic process issue likely."
            )

        if ctx.get("primary_hint"):
            steps.append(f"Tester ROOT_CAUSE_HINT indicates: {ctx['primary_hint']}.")

        evidence = baseline.get("evidence", [])
        for item in evidence[:3]:
            steps.append(f"Evidence: {item}")

        confidence = float(baseline.get("confidence_score", 0.5))
        if similar_cases:
            confidence = min(0.99, confidence + 0.1 * similar_cases[0].get("similarity_score", 0))

        explanation = (
            f"Engineering reasoning for scan chain {ctx.get('scan_chain_id')}: "
            f"most probable fault type is '{fault_type}' with root cause '{root_cause}'. "
            + " ".join(steps[:2])
        )

        return LLMReasoning(
            predicted_fault_type=fault_type,
            predicted_root_cause=root_cause,
            confidence=round(confidence, 4),
            explanation=explanation,
            reasoning_steps=steps,
            method="heuristic",
        )

    def _call_openai(
        self,
        ctx: dict[str, Any],
        baseline: dict[str, Any],
        ml: dict[str, Any] | None,
        similar_cases: list[dict[str, Any]],
    ) -> LLMReasoning | None:
        try:
            from openai import OpenAI
        except ImportError:
            return None

        client = OpenAI(api_key=self.api_key)
        prompt = {
            "failure_context": {
                "scan_chain_id": ctx.get("scan_chain_id"),
                "failure_count": ctx.get("failure_count"),
                "primary_hint": ctx.get("primary_hint"),
                "primary_fault_category": ctx.get("primary_fault_category"),
                "is_recurring": ctx.get("is_recurring"),
                "sample_patterns": ctx.get("sample_patterns", [])[:2],
            },
            "baseline_prediction": baseline,
            "ml_prediction": ml,
            "similar_historical_cases": similar_cases[:3],
            "instruction": (
                "As a semiconductor FA engineer, predict the most probable fault_type "
                "and engineering root_cause. Return JSON with keys: "
                "predicted_fault_type, predicted_root_cause, confidence (0-1), "
                "explanation, reasoning_steps (array of strings)."
            ),
        }

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a semiconductor failure analysis expert. "
                            "Provide explainable, evidence-based root cause predictions."
                        ),
                    },
                    {"role": "user", "content": json.dumps(prompt)},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            parsed = json.loads(content)
            return LLMReasoning(
                predicted_fault_type=str(parsed.get("predicted_fault_type", "UNKNOWN")),
                predicted_root_cause=str(parsed.get("predicted_root_cause", "UNKNOWN")),
                confidence=float(parsed.get("confidence", 0.85)),
                explanation=str(parsed.get("explanation", "LLM engineering reasoning")),
                reasoning_steps=list(parsed.get("reasoning_steps", [])),
                method="llm",
            )
        except Exception as exc:
            logger.warning("LLM reasoning failed: %s", exc)
            return None

    def _call_langchain(
        self,
        ctx: dict[str, Any],
        baseline: dict[str, Any],
        ml: dict[str, Any] | None,
        similar_cases: list[dict[str, Any]],
    ) -> LLMReasoning | None:
        """Optional LangChain path when package is installed."""
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage, SystemMessage
        except ImportError:
            return None

        if not self.api_key:
            return None

        llm = ChatOpenAI(api_key=self.api_key, model=self.model, temperature=0.1)
        prompt = json.dumps(
            {
                "context": ctx,
                "baseline": baseline,
                "ml": ml,
                "similar_cases": similar_cases[:3],
            }
        )
        try:
            response = llm.invoke(
                [
                    SystemMessage(content="Semiconductor FA root cause expert."),
                    HumanMessage(
                        content=(
                            "Predict fault_type and root_cause as JSON with keys "
                            "predicted_fault_type, predicted_root_cause, confidence, "
                            f"explanation, reasoning_steps. Data: {prompt}"
                        )
                    ),
                ]
            )
            parsed = json.loads(response.content)
            return LLMReasoning(
                predicted_fault_type=str(parsed.get("predicted_fault_type", "UNKNOWN")),
                predicted_root_cause=str(parsed.get("predicted_root_cause", "UNKNOWN")),
                confidence=float(parsed.get("confidence", 0.85)),
                explanation=str(parsed.get("explanation", "LangChain reasoning")),
                reasoning_steps=list(parsed.get("reasoning_steps", [])),
                method="langchain",
            )
        except Exception as exc:
            logger.info("LangChain reasoning unavailable: %s", exc)
            return None
