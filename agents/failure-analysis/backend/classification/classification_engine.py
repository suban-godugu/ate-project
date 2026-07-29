"""Main FA-FR-004 classification pipeline orchestrator."""

from __future__ import annotations

import time
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

from adapters.schema import TestRecord
from backend.classification.confidence_engine import ConfidenceEngine
from backend.classification.llm_classifier import LLMClassifier
from backend.classification.ml_classifier import MLClassifier, feature_vector
from backend.classification.rule_engine import RuleEngine
from backend.classification.taxonomy_manager import TaxonomyManager
from ingestor import DieLog, PatternResult


class ClassificationEngine:
    """
    Hybrid classification pipeline:
    Normalized data → features → rules → ML → LLM → confidence → recommendation
    """

    def __init__(
        self,
        *,
        taxonomy_path: Path | str | None = None,
        enable_ml: bool = True,
        enable_llm: bool = True,
    ) -> None:
        self.taxonomy = TaxonomyManager.load(taxonomy_path)
        self.rule_engine = RuleEngine()
        self.ml_classifier = MLClassifier() if enable_ml else None
        self.llm_classifier = LLMClassifier() if enable_llm else None
        self.confidence_engine = ConfidenceEngine()

    def analyze(
        self,
        *,
        die_logs: list[DieLog],
        test_records: list[TestRecord] | None = None,
        upload_id: str | None = None,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        record_index = _index_records(test_records)

        rule_labeled: list[tuple[list[float], str, dict[str, Any]]] = []
        pending: list[dict[str, Any]] = []
        classified_faults: list[dict[str, Any]] = []
        die_classifications: list[dict[str, Any]] = []
        category_counts: Counter[str] = Counter()
        method_counts: Counter[str] = Counter()

        for die in die_logs:
            die_results: list[dict[str, Any]] = []
            for pattern in die.failing_patterns:
                rec = record_index.get((die.lot_id, die.wafer_id, die.die_id))
                ctx = _build_context(die, pattern, rec)
                features = feature_vector(ctx)
                rule_result = self.rule_engine.classify(ctx, self.taxonomy).to_dict()

                if rule_result["method"] == "rule":
                    rule_labeled.append((features, rule_result["fault_category"], ctx))
                    final = self._finalize_single(rule_result, None, ctx)
                else:
                    pending.append(
                        {
                            "ctx": ctx,
                            "features": features,
                            "rule_result": rule_result,
                            "die": die,
                            "pattern": pattern,
                            "rec": rec,
                        }
                    )
                    final = self._finalize_single(rule_result, None, ctx)

                fault_row = _build_fault_row(die, pattern, rec, final)
                classified_faults.append(fault_row)
                die_results.append(final)
                category_counts[final["fault_category"]] += 1
                method_counts[final["method"]] += 1

            if die.is_failing_die and die_results:
                die_classifications.append(_aggregate_die(die, die_results))

        ml_trained = False
        if self.ml_classifier and rule_labeled and pending:
            ml_trained = self.ml_classifier.train(rule_labeled, self.taxonomy)
            if ml_trained:
                self._apply_ml_to_pending(pending, classified_faults, category_counts, method_counts)
                die_classifications = _refresh_die_classifications(
                    classified_faults, die_logs
                )

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        total = sum(category_counts.values())
        rule_accuracy = _estimate_rule_accuracy(classified_faults)

        return {
            "requirement": "FA-FR-004",
            "upload_id": upload_id,
            "processing_ms": elapsed_ms,
            "meets_performance_target": elapsed_ms < 3000,
            "taxonomy": self.taxonomy.to_dict(),
            "classification_pipeline": [
                "feature_extraction",
                "rule_based_classification",
                "machine_learning_classification",
                "llm_validation",
                "confidence_calculation",
                "engineering_recommendation",
            ],
            "ml_enabled": ml_trained,
            "llm_enabled": self.llm_classifier is not None,
            "llm_api_configured": bool(self.llm_classifier and self.llm_classifier.enabled),
            "estimated_accuracy_pct": rule_accuracy,
            "meets_accuracy_target": rule_accuracy >= 95.0 or total == 0,
            "method_counts": dict(method_counts),
            "total_classified_failures": total,
            "category_summary": {
                cat: {
                    "count": category_counts[cat],
                    "percentage": round(category_counts[cat] / total, 6) if total else 0.0,
                }
                for cat in self.taxonomy.categories
                if category_counts[cat] > 0
            },
            "classified_faults": classified_faults,
            "die_classifications": die_classifications,
            "classification_summary": {
                "total_faults": total,
                "unique_categories": len(category_counts),
                "dominant_category": category_counts.most_common(1)[0][0]
                if category_counts
                else self.taxonomy.unclassified,
                "high_confidence_count": sum(
                    1 for f in classified_faults if f["classification_confidence"] >= 0.9
                ),
            },
        }

    def _finalize_single(
        self,
        rule_result: dict[str, Any],
        ml_result: dict[str, Any] | None,
        ctx: dict[str, Any],
    ) -> dict[str, Any]:
        llm_result = (
            self.llm_classifier.validate(
                ctx=ctx,
                rule_result=rule_result,
                ml_result=ml_result,
                taxonomy=self.taxonomy,
            ).to_dict()
            if self.llm_classifier
            else {
                "fault_category": rule_result["fault_category"],
                "confidence": rule_result["confidence"],
                "validated": False,
                "explanation": "LLM validation disabled",
            }
        )
        return self.confidence_engine.finalize(
            rule=rule_result,
            ml=ml_result,
            llm=llm_result,
            taxonomy=self.taxonomy,
        ).to_dict()

    def _apply_ml_to_pending(
        self,
        pending: list[dict[str, Any]],
        classified_faults: list[dict[str, Any]],
        category_counts: Counter[str],
        method_counts: Counter[str],
    ) -> None:
        assert self.ml_classifier is not None
        for item in pending:
            ml_result = self.ml_classifier.predict(
                item["features"], item["ctx"], self.taxonomy
            )
            if ml_result is None:
                continue

            ml_dict = ml_result.to_dict()
            final = self._finalize_single(item["rule_result"], ml_dict, item["ctx"])
            fault_id = _find_fault_id(classified_faults, item["die"], item["pattern"])
            for row in classified_faults:
                if row["fault_id"] == fault_id:
                    old_cat = row["fault_category"]
                    row.update(final)
                    row["fault_id"] = fault_id
                    if category_counts[old_cat] > 0:
                        category_counts[old_cat] -= 1
                    category_counts[final["fault_category"]] += 1
                    method_counts["hybrid_ml"] = method_counts.get("hybrid_ml", 0) + 1
                    break


def _build_context(
    die: DieLog,
    pattern: PatternResult,
    rec: TestRecord | None,
) -> dict[str, Any]:
    fields = dict(pattern.raw_fields)
    ctx: dict[str, Any] = {
        **fields,
        "STATUS": pattern.status,
        "FAIL_TYPE": fields.get("FAIL_TYPE", ""),
        "ROOT_CAUSE_HINT": fields.get("ROOT_CAUSE_HINT", ""),
        "FAILURE_REGION": fields.get("FAILURE_REGION", ""),
        "SETUP_SLACK_PS": fields.get("SETUP_SLACK_PS", ""),
        "HOLD_SLACK_PS": fields.get("HOLD_SLACK_PS", ""),
        "IR_DROP_MV": fields.get("IR_DROP_MV", ""),
        "THERMAL_C": fields.get("THERMAL_C", ""),
        "TRANSITION_FAULTS": fields.get("TRANSITION_FAULTS", ""),
        "pattern_id": pattern.pattern_id,
        "scan_chain_id": pattern.scan_chain_id,
        "tester_id": die.tester_name,
        "lot_id": die.lot_id,
        "wafer_id": die.wafer_id,
        "die_id": die.die_id,
        "x": die.header_fields.get("DIE_X", getattr(rec, "x", "") if rec else ""),
        "y": die.header_fields.get("DIE_Y", getattr(rec, "y", "") if rec else ""),
    }
    if rec:
        ctx["hard_bin"] = rec.hard_bin
        ctx["soft_bin"] = rec.soft_bin
        if rec.failing_tests:
            ctx["failing_test"] = rec.failing_tests[0]
        for key, val in rec.parametric.items():
            ctx[str(key).upper()] = val
    elif die.header_fields.get("HARD_BIN"):
        ctx["hard_bin"] = die.header_fields["HARD_BIN"]
    return ctx


def _build_fault_row(
    die: DieLog,
    pattern: PatternResult,
    rec: TestRecord | None,
    final: dict[str, Any],
) -> dict[str, Any]:
    return {
        "fault_id": str(uuid.uuid4()),
        "lot_id": die.lot_id,
        "wafer_id": die.wafer_id,
        "die_id": die.die_id,
        "pattern_id": pattern.pattern_id,
        "scan_chain_id": pattern.scan_chain_id,
        "test_stage": rec.test_stage if rec else die.header_fields.get("TEST_STAGE", ""),
        "tester_id": die.tester_name or (rec.tester_id if rec else ""),
        "fail_type": pattern.raw_fields.get("FAIL_TYPE", ""),
        **final,
    }


def _aggregate_die(die: DieLog, results: list[dict[str, Any]]) -> dict[str, Any]:
    type_counts = Counter(r["fault_category"] for r in results)
    dominant = type_counts.most_common(1)[0][0]
    matching = [r for r in results if r["fault_category"] == dominant]
    avg_conf = sum(r["classification_confidence"] for r in matching) / len(matching)
    return {
        "die_id": die.die_id,
        "wafer_id": die.wafer_id,
        "lot_id": die.lot_id,
        "fault_category": dominant,
        "classification_confidence": round(avg_conf, 4),
        "method": matching[0].get("method", "hybrid"),
        "explanation": f"Dominant fault on die from {len(matching)}/{len(results)} patterns",
        "engineering_recommendation": matching[0].get("engineering_recommendation", ""),
    }


def _refresh_die_classifications(
    classified_faults: list[dict[str, Any]],
    die_logs: list[DieLog],
) -> list[dict[str, Any]]:
    by_die: dict[str, list[dict[str, Any]]] = {}
    for row in classified_faults:
        by_die.setdefault(row["die_id"], []).append(row)

    results = []
    for die in die_logs:
        if not die.is_failing_die:
            continue
        rows = by_die.get(die.die_id, [])
        if rows:
            finals = [
                {
                    "fault_category": r["fault_category"],
                    "classification_confidence": r["classification_confidence"],
                    "method": r["method"],
                    "engineering_recommendation": r.get("engineering_recommendation", ""),
                }
                for r in rows
            ]
            results.append(_aggregate_die(die, finals))
    return results


def _find_fault_id(
    classified_faults: list[dict[str, Any]],
    die: DieLog,
    pattern: PatternResult,
) -> str:
    for row in classified_faults:
        if row["die_id"] == die.die_id and row["pattern_id"] == pattern.pattern_id:
            return row["fault_id"]
    return ""


def _index_records(
    test_records: list[TestRecord] | None,
) -> dict[tuple[str, str, str], TestRecord]:
    index: dict[tuple[str, str, str], TestRecord] = {}
    if not test_records:
        return index
    for rec in test_records:
        index[(rec.lot_id, rec.wafer_id, rec.die_id)] = rec
    return index


def _estimate_rule_accuracy(classified_faults: list[dict[str, Any]]) -> float:
    if not classified_faults:
        return 100.0
    high_conf = sum(
        1 for f in classified_faults if f.get("classification_confidence", 0) >= 0.9
    )
    return round(100.0 * high_conf / len(classified_faults), 2)
