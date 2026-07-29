"""Confidence scoring and engineering recommendations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.classification.taxonomy_manager import TaxonomyManager


@dataclass
class FinalClassification:
    fault_category: str
    classification_confidence: float
    method: str
    explanation: str
    supporting_parameters: dict[str, Any] = field(default_factory=dict)
    failure_signature: str = ""
    engineering_recommendation: str = ""
    confidence_breakdown: dict[str, float] = field(default_factory=dict)
    severity: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "fault_category": self.fault_category,
            "classification_confidence": round(self.classification_confidence, 4),
            "method": self.method,
            "explanation": self.explanation,
            "supporting_parameters": self.supporting_parameters,
            "failure_signature": self.failure_signature,
            "engineering_recommendation": self.engineering_recommendation,
            "confidence_breakdown": self.confidence_breakdown,
            "severity": self.severity,
        }


class ConfidenceEngine:
    """Fuse rule, ML, and LLM outputs into a final confidence score."""

    RULE_WEIGHT = 0.45
    ML_WEIGHT = 0.35
    LLM_WEIGHT = 0.20

    def finalize(
        self,
        *,
        rule: dict[str, Any],
        ml: dict[str, Any] | None,
        llm: dict[str, Any],
        taxonomy: TaxonomyManager,
    ) -> FinalClassification:
        rule_conf = float(rule.get("confidence", 0.0))
        ml_conf = float(ml.get("confidence", 0.0)) if ml else 0.0
        llm_conf = float(llm.get("confidence", 0.0))

        categories = [rule.get("fault_category")]
        if ml:
            categories.append(ml.get("fault_category"))
        categories.append(llm.get("fault_category"))

        dominant = _consensus_category(categories, taxonomy)
        agreement = sum(1 for c in categories if taxonomy.normalize_category(str(c)) == dominant)
        agreement_boost = 0.05 * max(0, agreement - 1)

        if rule.get("method") == "rule" and rule_conf >= 1.0:
            final_conf = min(1.0, 0.98 + agreement_boost)
            method = "rule+llm" if llm.get("validated") else "rule"
            explanation = rule.get("explanation", "")
        elif ml and ml_conf >= rule_conf:
            final_conf = min(
                1.0,
                self.ML_WEIGHT * ml_conf
                + self.RULE_WEIGHT * rule_conf
                + self.LLM_WEIGHT * llm_conf
                + agreement_boost,
            )
            method = "hybrid_ml"
            explanation = ml.get("explanation", rule.get("explanation", ""))
        else:
            final_conf = min(
                1.0,
                self.RULE_WEIGHT * rule_conf
                + self.LLM_WEIGHT * llm_conf
                + agreement_boost,
            )
            method = "hybrid_rule"
            explanation = llm.get("explanation", rule.get("explanation", ""))

        supporting = dict(rule.get("supporting_parameters", {}))
        if ml:
            supporting.update(ml.get("supporting_parameters", {}))
        supporting.update(llm.get("supporting_parameters", {}))

        return FinalClassification(
            fault_category=dominant,
            classification_confidence=final_conf,
            method=method,
            explanation=explanation,
            supporting_parameters=supporting,
            failure_signature=rule.get("failure_signature", ml.get("failure_signature", "") if ml else ""),
            engineering_recommendation=taxonomy.recommendation_for(dominant),
            confidence_breakdown={
                "rule": round(rule_conf, 4),
                "ml": round(ml_conf, 4),
                "llm": round(llm_conf, 4),
                "agreement_boost": round(agreement_boost, 4),
            },
            severity=rule.get("severity"),
        )


def _consensus_category(categories: list[Any], taxonomy: TaxonomyManager) -> str:
    normalized = [taxonomy.normalize_category(str(c)) for c in categories if c]
    if not normalized:
        return taxonomy.unclassified
    counts: dict[str, int] = {}
    for cat in normalized:
        counts[cat] = counts.get(cat, 0) + 1
    return max(counts, key=counts.get)
