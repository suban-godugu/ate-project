"""Rule-based fault classification engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.classification.taxonomy_manager import TaxonomyManager


@dataclass
class RuleClassification:
    fault_category: str
    confidence: float
    method: str = "rule"
    explanation: str = ""
    rule_matched: str = ""
    supporting_parameters: dict[str, Any] = field(default_factory=dict)
    failure_signature: str = ""
    severity: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "fault_category": self.fault_category,
            "confidence": round(self.confidence, 4),
            "method": self.method,
            "explanation": self.explanation,
            "rule_matched": self.rule_matched,
            "supporting_parameters": self.supporting_parameters,
            "failure_signature": self.failure_signature,
            "severity": self.severity,
        }


class RuleEngine:
    """Deterministic YAML rule classifier."""

    def classify(self, ctx: dict[str, Any], taxonomy: TaxonomyManager) -> RuleClassification:
        for rule in taxonomy.rules:
            if _rule_matches(rule, ctx, taxonomy.thresholds):
                category = taxonomy.normalize_category(str(rule.get("category", taxonomy.unclassified)))
                return RuleClassification(
                    fault_category=category,
                    confidence=1.0,
                    method="rule",
                    explanation=f"Matched rule '{rule.get('name', 'unnamed')}'",
                    rule_matched=str(rule.get("name", "")),
                    supporting_parameters=_extract_supporting(ctx),
                    failure_signature=_build_signature(ctx),
                    severity=_derive_severity(ctx),
                )

        return RuleClassification(
            fault_category=taxonomy.unclassified,
            confidence=0.0,
            method="unclassified",
            explanation="No deterministic rule matched; queued for ML/LLM",
            supporting_parameters=_extract_supporting(ctx),
            failure_signature=_build_signature(ctx),
            severity=_derive_severity(ctx),
        )


def _rule_matches(
    rule: dict[str, Any],
    ctx: dict[str, Any],
    thresholds: dict[str, float],
) -> bool:
    when = rule.get("when", {})
    field = str(when.get("field", ""))
    value = ctx.get(field)
    if value is None or value == "":
        return False

    if "equals" in when:
        return str(value).upper() == str(when["equals"]).upper()
    if "contains" in when:
        return str(when["contains"]).upper() in str(value).upper()
    if "in" in when:
        return str(value) in [str(v) for v in when["in"]]
    if "lt" in when:
        try:
            return float(value) < float(when["lt"])
        except (TypeError, ValueError):
            return False
    if "gt" in when:
        try:
            return float(value) > float(when["gt"])
        except (TypeError, ValueError):
            return False
    if "gte" in when:
        try:
            return float(value) >= float(when["gte"])
        except (TypeError, ValueError):
            return False
    return False


def _extract_supporting(ctx: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "FAIL_TYPE",
        "ROOT_CAUSE_HINT",
        "FAILURE_REGION",
        "SETUP_SLACK_PS",
        "HOLD_SLACK_PS",
        "IR_DROP_MV",
        "THERMAL_C",
        "TRANSITION_FAULTS",
        "hard_bin",
        "soft_bin",
        "failing_test",
        "tester_id",
        "lot_id",
        "wafer_id",
        "die_id",
    )
    return {k: ctx[k] for k in keys if ctx.get(k) not in (None, "")}


def _build_signature(ctx: dict[str, Any]) -> str:
    parts = [
        str(ctx.get("FAIL_TYPE", "")),
        str(ctx.get("ROOT_CAUSE_HINT", "")),
        str(ctx.get("failing_test", "")),
        f"bin={ctx.get('hard_bin', '')}",
    ]
    return "|".join(p for p in parts if p and p != "bin=")


def _derive_severity(ctx: dict[str, Any]) -> str | None:
    try:
        setup = float(ctx.get("SETUP_SLACK_PS") or 0)
        hold = float(ctx.get("HOLD_SLACK_PS") or 0)
        ir_drop = float(ctx.get("IR_DROP_MV") or 0)
        thermal = float(ctx.get("THERMAL_C") or 0)
    except (TypeError, ValueError):
        return None

    if any([setup, hold, ir_drop, thermal]) or ctx.get("AI_SEVERITY_SCORE"):
        if setup < 0 or hold < 0 or ir_drop >= 50 or thermal >= 80:
            return "high"
        return "marginal"
    return None
