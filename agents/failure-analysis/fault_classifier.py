"""FA-FR-004: Configurable rule + ML fault classification with explanations."""

from __future__ import annotations

import hashlib
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from adapters.schema import TestRecord
from adapters.yaml_config import load_adapter_configs
from ingestor import DieLog, PatternResult

logger = logging.getLogger(__name__)

DEFAULT_TAXONOMY_PATH = (
    Path(__file__).resolve().parent / "config" / "fault_taxonomy.yaml"
)
ML_MIN_TRAINING_SAMPLES = 8
ML_MIN_RULE_SAMPLES = 4


@dataclass
class ClassificationResult:
    fault_type: str
    confidence: float
    method: str  # rule | ml | unclassified
    explanation: str
    severity: str | None = None
    shap_values: dict[str, float] = field(default_factory=dict)
    rule_matched: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "fault_type": self.fault_type,
            "confidence": round(self.confidence, 4),
            "method": self.method,
            "explanation": self.explanation,
            "severity": self.severity,
            "shap_values": self.shap_values,
            "rule_matched": self.rule_matched,
        }


class FaultTaxonomy:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.categories: list[str] = list(config.get("categories", []))
        self.definitions: dict[str, str] = dict(config.get("category_definitions", {}))
        self.unclassified: str = str(config.get("unclassified_label", "Unclassified"))
        self.rules: list[dict[str, Any]] = list(config.get("rules", []))
        self.thresholds: dict[str, float] = {
            k: float(v) for k, v in dict(config.get("thresholds", {})).items()
        }
        self.legacy_map: dict[str, str] = dict(config.get("legacy_category_map", {}))

    @classmethod
    def load(cls, path: Path | None = None) -> FaultTaxonomy:
        cfg_path = path or DEFAULT_TAXONOMY_PATH
        return cls(load_adapter_configs(cfg_path))

    def normalize_category(self, label: str) -> str:
        if label in self.categories:
            return label
        if label in self.legacy_map:
            return self.legacy_map[label]
        return self.unclassified


def classify_fault_types(
    die_logs: list[DieLog],
    *,
    test_records: list[TestRecord] | None = None,
    taxonomy_path: Path | None = None,
    enable_ml: bool = True,
) -> dict[str, Any]:
    """Classify all failing patterns and dies using rules first, then ML."""
    taxonomy = FaultTaxonomy.load(taxonomy_path)
    record_index = _index_records(test_records)

    rule_labeled: list[tuple[list[float], str, dict[str, Any]]] = []
    pending_ml: list[dict[str, Any]] = []
    classified_failures: list[dict[str, Any]] = []
    die_results: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    method_counts: Counter[str] = Counter()
    fail_type_counts: Counter[str] = Counter()

    for die in die_logs:
        rec = record_index.get((die.lot_id, die.wafer_id, die.die_id))
        die_pattern_results: list[ClassificationResult] = []

        for pattern in die.failing_patterns:
            ctx = _build_context(die, pattern, rec)
            result = _apply_rules(ctx, taxonomy)
            features = _feature_vector(ctx, taxonomy)

            if result.method == "rule":
                rule_labeled.append((features, result.fault_type, ctx))
            else:
                pending_ml.append(
                    {"ctx": ctx, "features": features, "die": die, "pattern": pattern}
                )

            die_pattern_results.append(result)
            category_counts[result.fault_type] += 1
            method_counts[result.method] += 1
            fail_type_counts[pattern.raw_fields.get("FAIL_TYPE", "N/A")] += 1
            classified_failures.append(
                {
                    "source_path": die.source_path,
                    "lot_id": die.lot_id,
                    "wafer_id": die.wafer_id,
                    "die_id": die.die_id,
                    "pattern_id": pattern.pattern_id,
                    "scan_chain_id": pattern.scan_chain_id,
                    "fail_type": pattern.raw_fields.get("FAIL_TYPE", ""),
                    "root_cause_hint": pattern.raw_fields.get("ROOT_CAUSE_HINT", ""),
                    "fault_category": result.fault_type,
                    "fault_type": result.fault_type,
                    "confidence": result.confidence,
                    "method": result.method,
                    "explanation": result.explanation,
                    "shap_values": result.shap_values,
                }
            )

        if die.is_failing_die:
            die_result = _aggregate_die_classification(die, die_pattern_results, rec)
            die_results.append(
                {
                    "die_id": die.die_id,
                    "wafer_id": die.wafer_id,
                    "lot_id": die.lot_id,
                    **die_result.to_dict(),
                }
            )

    ml_model = None
    if enable_ml and len(rule_labeled) >= ML_MIN_RULE_SAMPLES and pending_ml:
        ml_model = _train_ml_model(rule_labeled, taxonomy)
        if ml_model is not None:
            _apply_ml_to_pending(
                pending_ml, ml_model, taxonomy, classified_failures, category_counts, method_counts
            )
            _refresh_die_results(die_results, classified_failures, die_logs)

    total = sum(category_counts.values())
    summary = {
        cat: {
            "count": category_counts[cat],
            "percentage": round(category_counts[cat] / total, 6) if total else 0.0,
        }
        for cat in taxonomy.categories + [taxonomy.unclassified]
        if category_counts[cat] > 0
    }

    return {
        "predefined_categories": taxonomy.categories + [taxonomy.unclassified],
        "category_definitions": taxonomy.definitions,
        "taxonomy_source": str(taxonomy_path or DEFAULT_TAXONOMY_PATH),
        "classification_method": (
            "Two-stage FA-FR-004 classifier: (1) auditable YAML rules including customer "
            "bin tables and deterministic thresholds; (2) RandomForest ML for unresolved "
            "cases with confidence + SHAP/feature explanations when sklearn/shap available."
        ),
        "classification_thresholds": taxonomy.thresholds,
        "method_counts": dict(method_counts),
        "ml_enabled": ml_model is not None,
        "ml_model": ml_model.get("model_id") if ml_model else None,
        "total_classified_failures": total,
        "category_summary": summary,
        "source_fail_type_counts": dict(fail_type_counts),
        "classified_failures": classified_failures,
        "die_classifications": die_results,
    }


def classify_fault_type(
    pattern: PatternResult,
    *,
    die: DieLog | None = None,
    test_record: TestRecord | None = None,
    taxonomy_path: Path | None = None,
) -> str:
    """Backward-compatible single-pattern classifier returning fault type string."""
    taxonomy = FaultTaxonomy.load(taxonomy_path)
    ctx = _build_context(die or _blank_die(pattern), pattern, test_record)
    return _apply_rules(ctx, taxonomy).fault_type


def _apply_rules(ctx: dict[str, Any], taxonomy: FaultTaxonomy) -> ClassificationResult:
    for rule in taxonomy.rules:
        if _rule_matches(rule, ctx, taxonomy.thresholds):
            category = str(rule.get("category", taxonomy.unclassified))
            return ClassificationResult(
                fault_type=category,
                confidence=1.0,
                method="rule",
                explanation=f"Matched rule '{rule.get('name', 'unnamed')}'",
                rule_matched=str(rule.get("name", "")),
                severity=_derive_severity(ctx),
            )

    return ClassificationResult(
        fault_type=taxonomy.unclassified,
        confidence=0.0,
        method="unclassified",
        explanation="No deterministic rule matched; queued for ML if enabled",
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

    threshold_key = field.lower()
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
            limit = float(when["gte"])
            return float(value) >= limit
        except (TypeError, ValueError):
            return False

    return False


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


def _feature_vector(ctx: dict[str, Any], taxonomy: FaultTaxonomy) -> list[float]:
    def num(key: str) -> float:
        try:
            return float(ctx.get(key, 0) or 0)
        except (TypeError, ValueError):
            return 0.0

    tester_bucket = int(hashlib.md5(str(ctx.get("tester_id", "")).encode()).hexdigest()[:4], 16) % 100
    fail_type_bucket = int(hashlib.md5(str(ctx.get("FAIL_TYPE", "")).encode()).hexdigest()[:4], 16) % 100

    return [
        num("hard_bin"),
        num("soft_bin"),
        num("SETUP_SLACK_PS"),
        num("HOLD_SLACK_PS"),
        num("IR_DROP_MV"),
        num("THERMAL_C"),
        num("TRANSITION_FAULTS"),
        num("x"),
        num("y"),
        float(tester_bucket),
        float(fail_type_bucket),
    ]


FEATURE_NAMES = [
    "hard_bin",
    "soft_bin",
    "setup_slack_ps",
    "hold_slack_ps",
    "ir_drop_mv",
    "thermal_c",
    "transition_faults",
    "x",
    "y",
    "tester_bucket",
    "fail_type_bucket",
]


def _train_ml_model(
    labeled: list[tuple[list[float], str, dict[str, Any]]],
    taxonomy: FaultTaxonomy,
) -> dict[str, Any] | None:
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import LabelEncoder
    except ImportError:
        logger.info("scikit-learn not installed; ML classification skipped")
        return None

    x_train = [row[0] for row in labeled]
    y_train = [row[1] for row in labeled]
    if len(set(y_train)) < 2:
        return None

    encoder = LabelEncoder()
    encoder.fit(taxonomy.categories + [taxonomy.unclassified])
    y_enc = encoder.transform(y_train)

    model = RandomForestClassifier(
        n_estimators=50,
        max_depth=8,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(x_train, y_enc)

    return {
        "model": model,
        "encoder": encoder,
        "model_id": "random_forest_v1",
        "training_samples": len(x_train),
    }


def _apply_ml_to_pending(
    pending: list[dict[str, Any]],
    ml_bundle: dict[str, Any],
    taxonomy: FaultTaxonomy,
    classified_failures: list[dict[str, Any]],
    category_counts: Counter[str],
    method_counts: Counter[str],
) -> None:
    model = ml_bundle["model"]
    encoder = ml_bundle["encoder"]

    for item in pending:
        features = item["features"]
        ctx = item["ctx"]
        pattern = item["pattern"]
        die = item["die"]

        proba = model.predict_proba([features])[0]
        best_idx = int(proba.argmax())
        confidence = float(proba[best_idx])
        fault_type = str(encoder.inverse_transform([best_idx])[0])

        shap_values = _compute_shap(model, features, encoder)

        result = ClassificationResult(
            fault_type=fault_type,
            confidence=confidence,
            method="ml",
            explanation=_ml_explanation(shap_values, confidence),
            severity=_derive_severity(ctx),
            shap_values=shap_values,
        )

        category_counts[fault_type] += 1
        if taxonomy.unclassified in category_counts:
            category_counts[taxonomy.unclassified] -= 1
        method_counts["ml"] += 1
        if method_counts.get("unclassified", 0) > 0:
            method_counts["unclassified"] -= 1

        _upsert_classified_failure(classified_failures, die, pattern, result)


def _compute_shap(model: Any, features: list[float], encoder: Any) -> dict[str, float]:
    try:
        import shap
        import numpy as np

        explainer = shap.TreeExplainer(model)
        shap_output = explainer.shap_values(np.array([features]))
        if isinstance(shap_output, list):
            values = shap_output[0][0]
        else:
            values = shap_output[0]
        return {
            FEATURE_NAMES[i]: round(float(values[i]), 6)
            for i in range(min(len(FEATURE_NAMES), len(values)))
        }
    except Exception:
        importances = getattr(model, "feature_importances_", [])
        return {
            FEATURE_NAMES[i]: round(float(importances[i]), 6)
            for i in range(min(len(FEATURE_NAMES), len(importances)))
        }


def _ml_explanation(shap_values: dict[str, float], confidence: float) -> str:
    if not shap_values:
        return f"ML prediction confidence={confidence:.2f}"
    top = sorted(shap_values.items(), key=lambda kv: abs(kv[1]), reverse=True)[:3]
    parts = ", ".join(f"{k}={v:+.4f}" for k, v in top)
    return f"ML prediction (confidence={confidence:.2f}); top features: {parts}"


def _aggregate_die_classification(
    die: DieLog,
    pattern_results: list[ClassificationResult],
    rec: TestRecord | None,
) -> ClassificationResult:
    if not pattern_results:
        return ClassificationResult(
            fault_type="Unclassified",
            confidence=0.0,
            method="unclassified",
            explanation="No failing patterns on die",
        )

    type_counts = Counter(r.fault_type for r in pattern_results)
    dominant, count = type_counts.most_common(1)[0]
    matching = [r for r in pattern_results if r.fault_type == dominant]
    avg_conf = sum(r.confidence for r in matching) / len(matching)
    methods = Counter(r.method for r in matching)
    method = methods.most_common(1)[0][0]

    return ClassificationResult(
        fault_type=dominant,
        confidence=round(avg_conf, 4),
        method=method,
        explanation=f"Dominant fault on die from {count}/{len(pattern_results)} failing patterns",
        severity=_derive_severity(_build_context(die, die.failing_patterns[0], rec)),
    )


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


def _upsert_classified_failure(
    classified_failures: list[dict[str, Any]],
    die: DieLog,
    pattern: PatternResult,
    result: ClassificationResult,
) -> None:
    for row in classified_failures:
        if (
            row["die_id"] == die.die_id
            and row["pattern_id"] == pattern.pattern_id
            and row["lot_id"] == die.lot_id
        ):
            row.update(result.to_dict())
            row["fault_category"] = result.fault_type
            return


def _refresh_die_results(
    die_results: list[dict[str, Any]],
    classified_failures: list[dict[str, Any]],
    die_logs: list[DieLog],
) -> None:
    by_die = defaultdict(list)
    for row in classified_failures:
        by_die[row["die_id"]].append(row)

    for die_result in die_results:
        rows = by_die.get(die_result["die_id"], [])
        if not rows:
            continue
        type_counts = Counter(r["fault_type"] for r in rows)
        dominant = type_counts.most_common(1)[0][0]
        matching = [r for r in rows if r["fault_type"] == dominant]
        die_result.update(
            {
                "fault_type": dominant,
                "confidence": round(
                    sum(r.get("confidence", 0) for r in matching) / len(matching), 4
                ),
                "method": matching[0].get("method", "ml"),
                "explanation": f"Dominant die fault after ML: {dominant}",
            }
        )


def _index_records(test_records: list[TestRecord] | None) -> dict[tuple[str, str, str], TestRecord]:
    index: dict[tuple[str, str, str], TestRecord] = {}
    if not test_records:
        return index
    for rec in test_records:
        index[(rec.lot_id, rec.wafer_id, rec.die_id)] = rec
    return index


def _blank_die(pattern: PatternResult) -> DieLog:
    return DieLog(
        source_path="",
        tester_name="",
        device_name="",
        lot_id="",
        wafer_id="",
        die_id="",
        header_fields={},
        stored_failing=[pattern],
    )
