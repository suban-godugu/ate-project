"""Engineering investigation recommendations."""

from __future__ import annotations

from typing import Any

from backend.classification.taxonomy_manager import TaxonomyManager


class RecommendationEngine:
    """Generate actionable engineering investigations from predictions."""

    def __init__(self, taxonomy_path: str | None = None) -> None:
        from pathlib import Path

        path = (
            Path(taxonomy_path)
            if taxonomy_path
            else Path(__file__).resolve().parents[2] / "config" / "classification_taxonomy.yaml"
        )
        self.taxonomy = TaxonomyManager.load(path)

    def recommend(
        self,
        *,
        prediction: dict[str, Any],
        similar_cases: list[dict[str, Any]],
        ctx: dict[str, Any],
    ) -> list[dict[str, Any]]:
        recommendations: list[dict[str, Any]] = []
        fault_type = prediction.get("predicted_fault_type", "")
        root_cause = prediction.get("predicted_root_cause", fault_type)
        confidence = float(prediction.get("confidence_score", 0.0))

        category_rec = self.taxonomy.recommendation_for(
            self._map_to_category(fault_type, ctx)
        )
        if category_rec:
            recommendations.append(
                {
                    "priority": "HIGH" if confidence >= 0.75 else "MEDIUM",
                    "category": "taxonomy",
                    "action": category_rec,
                    "rationale": f"Standard playbook for fault type '{fault_type}'.",
                }
            )

        for case in similar_cases[:2]:
            investigation = case.get("investigation", "")
            if investigation:
                recommendations.append(
                    {
                        "priority": "HIGH",
                        "category": "historical",
                        "action": investigation,
                        "rationale": (
                            f"Similar case {case.get('case_id')} "
                            f"(similarity={case.get('similarity_score', 0):.2f}) "
                            f"resolved as: {case.get('resolution', 'N/A')}."
                        ),
                    }
                )

        if ctx.get("is_recurring"):
            recommendations.append(
                {
                    "priority": "CRITICAL",
                    "category": "recurrence",
                    "action": (
                        "Escalate to process engineering — failure spans "
                        f"{ctx.get('affected_lots', 0)} lots and "
                        f"{ctx.get('affected_wafers', 0)} wafers."
                    ),
                    "rationale": "Multi-lot recurrence indicates systematic issue.",
                }
            )

        if ctx.get("correlation_score", 0) >= 0.75:
            recommendations.append(
                {
                    "priority": "HIGH",
                    "category": "correlation",
                    "action": (
                        "Prioritize pattern correlation review for high-risk "
                        f"scan chain {ctx.get('scan_chain_id')}."
                    ),
                    "rationale": f"Correlation score={ctx.get('correlation_score'):.2f}.",
                }
            )

        if confidence < 0.6:
            recommendations.append(
                {
                    "priority": "MEDIUM",
                    "category": "manual_review",
                    "action": (
                        f"Manual FA review recommended for '{root_cause}' "
                        f"(confidence={confidence:.2f})."
                    ),
                    "rationale": "Low confidence prediction requires engineer validation.",
                }
            )

        return _dedupe_recommendations(recommendations)

    def _map_to_category(self, fault_type: str, ctx: dict[str, Any]) -> str:
        hint = str(ctx.get("primary_fault_category", ""))
        if hint and hint != "Unknown Failure":
            return hint
        legacy_map = self.taxonomy.legacy_map
        return str(legacy_map.get(fault_type, fault_type))


def _dedupe_recommendations(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for item in items:
        key = item.get("action", "")
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique
