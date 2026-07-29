"""Deterministic explainable fault-type scoring engine for FA-FR-009."""

from __future__ import annotations

import hashlib
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class FaultPredictionComputationError(ValueError):
    pass


@dataclass(frozen=True)
class FaultPredictionConfig:
    version: str
    algorithm: str
    model_version: str
    model_type: str
    top_k_alternatives: int
    min_confidence: float
    high_confidence: float
    min_probability: float
    recurrence_boost: float
    correlation_boost: float
    failure_rate_boost: float
    die_severity_boost: float
    wafer_health_penalty: float
    min_sample_size: int
    weight_correlation: float
    weight_recurrence: float
    weight_classification: float
    weight_failure_rate: float
    weight_die: float
    weight_wafer: float
    batch_size: int
    max_patterns_per_batch: int
    compatible_formula_prefix: str
    require_same_tenant: bool
    require_product_overlap: bool
    require_test_stage_overlap: bool
    feedback_enabled: bool
    default_learning_weight: float

    @classmethod
    def load(cls, path: str | Path | None = None) -> "FaultPredictionConfig":
        target = (
            Path(path)
            if path
            else Path(__file__).resolve().parents[2]
            / "config"
            / "fault_prediction_production.yaml"
        )
        raw = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
        thresholds = raw.get("thresholds", {})
        weights = raw.get("scoring_weights", {})
        cohort = raw.get("cohort", {})
        model = raw.get("model", {})
        feedback = raw.get("feedback", {})
        performance = raw.get("performance", {})
        return cls(
            version=str(raw.get("config_version", "fault-prediction-v2.0")),
            algorithm=str(raw.get("algorithm", "rule_based_explainable_scoring")),
            model_version=str(model.get("model_version", "rule-v2.0")),
            model_type=str(model.get("model_type", "rule_based")),
            top_k_alternatives=int(model.get("top_k_alternatives", 5)),
            min_confidence=float(thresholds.get("minimum_confidence", 0.35)),
            high_confidence=float(thresholds.get("high_confidence", 0.75)),
            min_probability=float(thresholds.get("minimum_probability", 0.05)),
            recurrence_boost=float(thresholds.get("recurrence_boost", 0.12)),
            correlation_boost=float(thresholds.get("correlation_boost", 0.15)),
            failure_rate_boost=float(thresholds.get("failure_rate_boost", 0.10)),
            die_severity_boost=float(thresholds.get("die_severity_boost", 0.08)),
            wafer_health_penalty=float(thresholds.get("wafer_health_penalty", 0.06)),
            min_sample_size=int(thresholds.get("min_sample_size", 1)),
            weight_correlation=float(weights.get("correlation", 0.30)),
            weight_recurrence=float(weights.get("recurrence", 0.20)),
            weight_classification=float(weights.get("classification", 0.20)),
            weight_failure_rate=float(weights.get("failure_rate", 0.15)),
            weight_die=float(weights.get("die_analytics", 0.10)),
            weight_wafer=float(weights.get("wafer_analytics", 0.05)),
            batch_size=int(raw.get("batch_size", 10_000)),
            max_patterns_per_batch=int(performance.get("max_patterns_per_batch", 50_000)),
            compatible_formula_prefix=str(
                cohort.get("compatible_formula_prefix", "failure-rate-v1")
            ),
            require_same_tenant=bool(cohort.get("require_same_tenant", True)),
            require_product_overlap=bool(cohort.get("require_product_overlap", True)),
            require_test_stage_overlap=bool(
                cohort.get("require_test_stage_overlap", True)
            ),
            feedback_enabled=bool(feedback.get("enabled", True)),
            default_learning_weight=float(feedback.get("default_learning_weight", 1.0)),
        )


class ProductionFaultPredictionEngine:
    def __init__(self, config: FaultPredictionConfig) -> None:
        self.config = config

    def predict(
        self,
        *,
        patterns: list[dict[str, Any]],
        correlations: list[dict[str, Any]],
        recurrences: list[dict[str, Any]],
        classifications: list[dict[str, Any]],
        failure_rates: dict[str, float],
        dies: list[dict[str, Any]],
        wafers: list[dict[str, Any]],
        feedback_signals: list[dict[str, Any]],
        execution_id: str,
        wafer_analysis_id: str,
    ) -> dict[str, Any]:
        if not patterns:
            raise FaultPredictionComputationError(
                "Fault prediction requires at least one traceable pattern"
            )
        if len(patterns) > self.config.max_patterns_per_batch:
            raise FaultPredictionComputationError(
                f"Pattern count {len(patterns)} exceeds batch limit "
                f"{self.config.max_patterns_per_batch}"
            )

        correlation_by_pattern = {
            str(row.get("pattern_id", "")): row for row in correlations
        }
        recurrence_by_pattern = {
            str(row.get("pattern_id", "")): row for row in recurrences
        }
        classification_by_pattern: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in classifications:
            classification_by_pattern[str(row.get("pattern_id", ""))].append(row)

        die_severity_by_wafer: dict[str, list[float]] = defaultdict(list)
        for die in dies:
            if die.get("is_failing"):
                key = f"{die.get('lot_id', '')}|{die.get('wafer_id', '')}".lower()
                die_severity_by_wafer[key].append(
                    1.0 - float(die.get("health_score", 1.0))
                )
        wafer_by_key = {
            f"{row.get('lot_id', '')}|{row.get('wafer_id', '')}".lower(): row
            for row in wafers
        }
        feedback_by_pattern = _feedback_index(feedback_signals)

        predictions: list[dict[str, Any]] = []
        for pattern in sorted(patterns, key=lambda item: str(item.get("pattern_id", ""))):
            pattern_id = str(pattern.get("pattern_id", "")).strip()
            if not pattern_id:
                continue
            canonical = hashlib.sha256(pattern_id.lower().encode()).hexdigest()
            prediction_id = str(
                uuid.uuid5(uuid.NAMESPACE_URL, f"{execution_id}:{canonical}")
            )
            scores, evidence = _score_fault_types(
                pattern_id=pattern_id,
                pattern=pattern,
                correlation=correlation_by_pattern.get(pattern_id),
                recurrence=recurrence_by_pattern.get(pattern_id),
                classifications=classification_by_pattern.get(pattern_id, []),
                failure_rate=failure_rates.get(pattern_id, 0.0),
                dies=dies,
                wafers=wafers,
                wafer_by_key=wafer_by_key,
                die_severity_by_wafer=die_severity_by_wafer,
                feedback=feedback_by_pattern.get(pattern_id),
                config=self.config,
            )
            if not scores:
                scores = {"UNKNOWN": self.config.min_confidence}
                evidence.append("Insufficient upstream signals; defaulting to UNKNOWN")

            ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
            total = sum(score for _, score in ranked) or 1.0
            alternatives = [
                {
                    "fault_type": fault_type,
                    "probability": round(score / total, 6),
                    "confidence_score": round(min(1.0, score), 6),
                    "rank": index + 1,
                }
                for index, (fault_type, score) in enumerate(
                    ranked[: self.config.top_k_alternatives]
                )
                if score >= self.config.min_probability
            ]
            if not alternatives:
                alternatives = [
                    {
                        "fault_type": ranked[0][0],
                        "probability": 1.0,
                        "confidence_score": round(
                            max(self.config.min_confidence, ranked[0][1]), 6
                        ),
                        "rank": 1,
                    }
                ]

            top = alternatives[0]
            explanation = _engineering_explanation(
                pattern_id=pattern_id,
                top_fault_type=top["fault_type"],
                evidence=evidence,
                correlation=correlation_by_pattern.get(pattern_id),
                recurrence=recurrence_by_pattern.get(pattern_id),
            )
            steps = _investigation_steps(
                top_fault_type=top["fault_type"],
                pattern_id=pattern_id,
                correlation=correlation_by_pattern.get(pattern_id),
                wafers=wafers,
            )
            predictions.append(
                {
                    "prediction_id": prediction_id,
                    "canonical_prediction_key": canonical,
                    "pattern_id": pattern_id,
                    "predicted_fault_type": top["fault_type"],
                    "alternative_fault_types": alternatives,
                    "confidence_score": top["confidence_score"],
                    "prediction_probability": top["probability"],
                    "supporting_evidence": evidence,
                    "engineering_explanation": explanation,
                    "investigation_steps": steps,
                    "model_version": self.config.model_version,
                    "metadata_json": {
                        "score_breakdown": {
                            fault: round(score, 6) for fault, score in ranked[:10]
                        },
                        "disclaimer": (
                            "Probable fault-type prediction only; not a definitive root cause."
                        ),
                    },
                    "wafer_analysis_id": wafer_analysis_id,
                }
            )

        predictions.sort(
            key=lambda item: (
                -item["confidence_score"],
                -item["prediction_probability"],
                item["pattern_id"],
            )
        )
        return {
            "predictions": predictions,
            "statistics": _statistics(predictions, self.config),
            "scoped_statistics": _scoped_statistics(predictions, self.config),
            "model": {
                "model_version": self.config.model_version,
                "model_type": self.config.model_type,
                "algorithm": self.config.algorithm,
            },
        }


def _feedback_index(
    feedback_signals: list[dict[str, Any]],
) -> dict[str, dict[str, float]]:
    indexed: dict[str, dict[str, float]] = defaultdict(dict)
    for row in feedback_signals:
        pattern_id = str(row.get("pattern_id", "")).strip()
        fault_type = str(row.get("validated_fault_type", "")).strip().upper()
        if not pattern_id or not fault_type:
            continue
        weight = float(row.get("learning_weight", 1.0))
        indexed[pattern_id][fault_type] = indexed[pattern_id].get(fault_type, 0.0) + weight
    return indexed


def _score_fault_types(
    *,
    pattern_id: str,
    pattern: dict[str, Any],
    correlation: dict[str, Any] | None,
    recurrence: dict[str, Any] | None,
    classifications: list[dict[str, Any]],
    failure_rate: float,
    dies: list[dict[str, Any]],
    wafers: list[dict[str, Any]],
    wafer_by_key: dict[str, dict[str, Any]],
    die_severity_by_wafer: dict[str, list[float]],
    feedback: dict[str, float] | None,
    config: FaultPredictionConfig,
) -> tuple[dict[str, float], list[str]]:
    scores: Counter[str] = Counter()
    evidence: list[str] = []

    if correlation:
        fault = str(correlation.get("fault_type", "UNKNOWN")).upper()
        coeff = abs(float(correlation.get("correlation_coefficient", 0.0)))
        strength = str(correlation.get("correlation_strength", "")).lower()
        base = config.min_confidence + coeff * config.weight_correlation
        if strength in {"strong", "very_strong"}:
            base += config.correlation_boost
        scores[fault] += base
        evidence.append(
            f"FA-FR-006 correlation {coeff:.3f} ({strength or 'n/a'}) for pattern {pattern_id}"
        )

    if recurrence:
        fault = str(recurrence.get("fault_type", "UNKNOWN")).upper()
        recurrence_pct = float(recurrence.get("recurrence_percentage", 0.0)) / 100.0
        scores[fault] += (
            config.min_confidence
            + recurrence_pct * config.weight_recurrence
            + config.recurrence_boost
        )
        evidence.append(
            f"FA-FR-005 recurrence {recurrence_pct * 100:.1f}% across lots for {pattern_id}"
        )

    for row in classifications:
        fault = str(row.get("fault_type", row.get("predicted_fault_type", "UNKNOWN"))).upper()
        confidence = float(row.get("confidence", row.get("confidence_score", 0.5)))
        scores[fault] += config.min_confidence + confidence * config.weight_classification
        evidence.append(
            f"FA-FR-004 classification confidence {confidence:.2f} suggests {fault}"
        )

    if failure_rate > 0:
        dominant = scores.most_common(1)[0][0] if scores else "UNKNOWN"
        scores[dominant] += min(
            1.0,
            config.min_confidence
            + (failure_rate / 100.0) * config.weight_failure_rate
            + config.failure_rate_boost,
        )
        evidence.append(f"FA-FR-003 failure rate {failure_rate:.2f}% for pattern {pattern_id}")

    failing_dies = [row for row in dies if row.get("is_failing")]
    if failing_dies:
        mean_severity = sum(
            1.0 - float(row.get("health_score", 1.0)) for row in failing_dies
        ) / len(failing_dies)
        dominant = scores.most_common(1)[0][0] if scores else "UNKNOWN"
        scores[dominant] += mean_severity * config.weight_die + config.die_severity_boost
        evidence.append(
            f"FA-FR-007 die severity index {mean_severity:.3f} across {len(failing_dies)} failing dies"
        )

    unhealthy_wafers = [
        row for row in wafers if float(row.get("health_score", 1.0)) < 0.75
    ]
    if unhealthy_wafers:
        dominant = scores.most_common(1)[0][0] if scores else "UNKNOWN"
        penalty = min(0.25, len(unhealthy_wafers) / max(1, len(wafers)) * config.wafer_health_penalty)
        scores[dominant] += config.weight_wafer - penalty
        evidence.append(
            f"FA-FR-008 wafer health degraded on {len(unhealthy_wafers)} wafer(s)"
        )

    hinted = str(pattern.get("fault_type", "")).strip().upper()
    if hinted and hinted != "UNKNOWN":
        scores[hinted] += config.min_confidence

    if feedback:
        for fault_type, weight in feedback.items():
            scores[fault_type] += min(0.2, 0.05 * weight)
        evidence.append("Engineering feedback applied to prior validated fault types")

    normalized = {
        fault: round(min(0.99, max(config.min_confidence, score)), 6)
        for fault, score in scores.items()
        if score >= config.min_probability
    }
    return normalized, evidence[:20]


def _engineering_explanation(
    *,
    pattern_id: str,
    top_fault_type: str,
    evidence: list[str],
    correlation: dict[str, Any] | None,
    recurrence: dict[str, Any] | None,
) -> str:
    parts = [
        f"Probable fault type for pattern {pattern_id} is {top_fault_type}.",
        "This is a ranked hypothesis, not a confirmed root cause.",
    ]
    if correlation:
        parts.append(
            f"Correlation strength is {correlation.get('correlation_strength', 'unknown')} "
            f"with coefficient {float(correlation.get('correlation_coefficient', 0.0)):.3f}."
        )
    if recurrence:
        parts.append(
            f"Recurrence observed in {recurrence.get('recurrence_count', 'multiple')} execution(s)."
        )
    if evidence:
        parts.append("Key evidence: " + "; ".join(evidence[:5]) + ".")
    return " ".join(parts)


def _investigation_steps(
    *,
    top_fault_type: str,
    pattern_id: str,
    correlation: dict[str, Any] | None,
    wafers: list[dict[str, Any]],
) -> list[dict[str, str]]:
    steps = [
        {
            "step_code": "REVIEW_PATTERN_SIGNATURE",
            "action": f"Review failing signature and bin history for pattern {pattern_id}",
            "priority": "high",
        },
        {
            "step_code": "VALIDATE_FAULT_HYPOTHESIS",
            "action": (
                f"Validate probable fault type {top_fault_type} with targeted diagnostics"
            ),
            "priority": "high",
        },
    ]
    if correlation and correlation.get("hotspot_location"):
        steps.append(
            {
                "step_code": "INSPECT_HOTSPOT",
                "action": (
                    f"Inspect hotspot at {correlation.get('hotspot_location')} "
                    "for spatial correlation"
                ),
                "priority": "medium",
            }
        )
    degraded = [row for row in wafers if float(row.get("health_score", 1.0)) < 0.6]
    if degraded:
        steps.append(
            {
                "step_code": "WAFER_LEVEL_RETEST",
                "action": "Retest degraded wafers and compare yield against lot baseline",
                "priority": "medium",
            }
        )
    steps.append(
        {
            "step_code": "SUBMIT_ENGINEERING_FEEDBACK",
            "action": "Submit validated fault type via feedback API for model learning",
            "priority": "low",
        }
    )
    return steps


def _statistics(
    predictions: list[dict[str, Any]], config: FaultPredictionConfig
) -> dict[str, Any]:
    if not predictions:
        return {
            "total_predictions": 0,
            "high_confidence_count": 0,
            "mean_confidence": 0.0,
            "mean_probability": 0.0,
            "top_fault_type": "",
        }
    confidences = [float(row["confidence_score"]) for row in predictions]
    probabilities = [float(row["prediction_probability"]) for row in predictions]
    fault_counter = Counter(row["predicted_fault_type"] for row in predictions)
    return {
        "total_predictions": len(predictions),
        "high_confidence_count": sum(
            1 for value in confidences if value >= config.high_confidence
        ),
        "mean_confidence": round(sum(confidences) / len(confidences), 6),
        "mean_probability": round(sum(probabilities) / len(probabilities), 6),
        "top_fault_type": fault_counter.most_common(1)[0][0],
        "fault_type_distribution": dict(fault_counter),
    }


def _scoped_statistics(
    predictions: list[dict[str, Any]], config: FaultPredictionConfig
) -> list[dict[str, Any]]:
    stats = _statistics(predictions, config)
    rows = [
        {
            "scope_type": "execution",
            "scope_key": "all",
            **stats,
            "details": stats,
        }
    ]
    by_fault: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in predictions:
        by_fault[row["predicted_fault_type"]].append(row)
    for fault_type, items in sorted(by_fault.items()):
        confidences = [float(item["confidence_score"]) for item in items]
        rows.append(
            {
                "scope_type": "fault_type",
                "scope_key": fault_type,
                "total_predictions": len(items),
                "high_confidence_count": sum(
                    1 for value in confidences if value >= config.high_confidence
                ),
                "mean_confidence": round(sum(confidences) / len(confidences), 6),
                "mean_probability": round(
                    sum(float(item["prediction_probability"]) for item in items)
                    / len(items),
                    6,
                ),
                "top_fault_type": fault_type,
                "details": {"pattern_ids": [item["pattern_id"] for item in items[:50]]},
            }
        )
    return rows
