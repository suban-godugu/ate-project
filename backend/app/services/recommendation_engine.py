"""Deterministic recommendation engine from aggregated Scan Chain results."""

from __future__ import annotations

from typing import Any


class RecommendationEngine:
    def build(self, merged: dict[str, Any]) -> dict[str, Any]:
        recommendations: list[dict[str, Any]] = []
        failure_kpis = merged.get("failure_kpis") or {}
        diagnosis = merged.get("diagnosis_report") or {}
        yield_pct = failure_kpis.get("yield_pct")
        if yield_pct is not None and float(yield_pct) < 90:
            recommendations.append(
                {
                    "code": "YIELD_BELOW_TARGET",
                    "severity": "high",
                    "message": f"Yield {yield_pct}% below 90% target — prioritize fail signature review.",
                }
            )
        confidence = merged.get("diagnosis_confidence")
        if confidence is not None and float(confidence) < 0.6:
            recommendations.append(
                {
                    "code": "LOW_DIAGNOSIS_CONFIDENCE",
                    "severity": "medium",
                    "message": "Diagnosis confidence is low — collect additional ATE vectors or STIL topology.",
                }
            )
        for item in merged.get("agent_recommendations") or []:
            if isinstance(item, dict):
                recommendations.append(item)
            else:
                recommendations.append({"code": "AGENT", "severity": "info", "message": str(item)})

        chain_fails = (merged.get("pattern_kpis") or {}).get("failing_chains") or 0
        if chain_fails and int(chain_fails) > 0:
            recommendations.append(
                {
                    "code": "SCAN_CHAIN_FAILS",
                    "severity": "high",
                    "message": f"{chain_fails} scan chain(s) reported failures — run repair / retest workflow.",
                }
            )

        root = diagnosis.get("root_cause") if isinstance(diagnosis, dict) else None
        if root:
            recommendations.append(
                {
                    "code": "ROOT_CAUSE",
                    "severity": "info",
                    "message": f"Primary root cause: {root}",
                }
            )

        kpis = {
            "recommendation_count": len(recommendations),
            "high_severity": sum(1 for r in recommendations if r.get("severity") == "high"),
            "yield_pct": yield_pct,
            "diagnosis_confidence": confidence,
        }
        return {"recommendations": recommendations, "kpis": kpis}
