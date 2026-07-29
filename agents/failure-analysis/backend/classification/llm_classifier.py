"""LLM-assisted fault classification validation (optional)."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

from backend.classification.taxonomy_manager import TaxonomyManager

logger = logging.getLogger(__name__)


@dataclass
class LLMClassification:
    fault_category: str
    confidence: float
    method: str = "llm"
    explanation: str = ""
    validated: bool = False
    supporting_parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fault_category": self.fault_category,
            "confidence": round(self.confidence, 4),
            "method": self.method,
            "explanation": self.explanation,
            "validated": self.validated,
            "supporting_parameters": self.supporting_parameters,
        }


class LLMClassifier:
    """
    Optional LLM validation layer. Uses OpenAI/Azure when configured;
    otherwise applies deterministic heuristic validation without external calls.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.enabled = bool(self.api_key)

    def validate(
        self,
        *,
        ctx: dict[str, Any],
        rule_result: dict[str, Any],
        ml_result: dict[str, Any] | None,
        taxonomy: TaxonomyManager,
    ) -> LLMClassification:
        candidates = [
            (rule_result.get("fault_category"), rule_result.get("confidence", 0.0), "rule"),
        ]
        if ml_result:
            candidates.append(
                (ml_result.get("fault_category"), ml_result.get("confidence", 0.0), "ml")
            )

        if self.enabled:
            llm_result = self._call_llm(ctx, candidates, taxonomy)
            if llm_result:
                return llm_result

        return self._heuristic_validate(ctx, candidates, taxonomy)

    def _heuristic_validate(
        self,
        ctx: dict[str, Any],
        candidates: list[tuple[str | None, float, str]],
        taxonomy: TaxonomyManager,
    ) -> LLMClassification:
        """Deterministic validation when LLM is unavailable."""
        best_cat, best_conf, best_method = max(candidates, key=lambda c: c[1] or 0.0)
        category = taxonomy.normalize_category(str(best_cat or taxonomy.unclassified))

        if best_method == "rule" and best_conf >= 1.0:
            explanation = (
                f"LLM validation skipped (no API key); rule classification '{category}' "
                "accepted with full confidence."
            )
            confidence = 0.98
            validated = True
        elif best_conf >= 0.75:
            explanation = (
                f"LLM validation skipped; ML/rule consensus on '{category}' "
                f"(base confidence={best_conf:.2f})."
            )
            confidence = min(0.95, best_conf + 0.05)
            validated = True
        else:
            explanation = (
                f"Low-confidence classification '{category}'; recommend manual FA review."
            )
            confidence = max(best_conf, 0.5)
            validated = False

        return LLMClassification(
            fault_category=category,
            confidence=confidence,
            explanation=explanation,
            validated=validated,
            supporting_parameters={
                k: ctx[k]
                for k in ("FAIL_TYPE", "ROOT_CAUSE_HINT", "failing_test", "hard_bin")
                if ctx.get(k)
            },
        )

    def _call_llm(
        self,
        ctx: dict[str, Any],
        candidates: list[tuple[str | None, float, str]],
        taxonomy: TaxonomyManager,
    ) -> LLMClassification | None:
        try:
            from openai import OpenAI
        except ImportError:
            logger.info("openai package not installed; using heuristic LLM validation")
            return None

        client = OpenAI(api_key=self.api_key)
        prompt = {
            "categories": taxonomy.categories,
            "failure_context": {
                k: ctx.get(k)
                for k in (
                    "FAIL_TYPE",
                    "ROOT_CAUSE_HINT",
                    "FAILURE_REGION",
                    "failing_test",
                    "hard_bin",
                    "SETUP_SLACK_PS",
                    "HOLD_SLACK_PS",
                )
                if ctx.get(k)
            },
            "candidates": [
                {"category": c, "confidence": conf, "method": m}
                for c, conf, m in candidates
            ],
            "instruction": (
                "Select the best fault category from the allowed list. "
                "Return JSON with keys: fault_category, confidence (0-1), explanation."
            ),
        }

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a semiconductor failure analysis expert.",
                    },
                    {"role": "user", "content": json.dumps(prompt)},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            parsed = json.loads(content)
            category = taxonomy.normalize_category(
                str(parsed.get("fault_category", taxonomy.unclassified))
            )
            return LLMClassification(
                fault_category=category,
                confidence=float(parsed.get("confidence", 0.85)),
                explanation=str(parsed.get("explanation", "LLM validated classification")),
                validated=True,
                supporting_parameters=prompt["failure_context"],
            )
        except Exception as exc:
            logger.warning("LLM validation failed: %s", exc)
            return None
