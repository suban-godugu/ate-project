"""Functional validation of FA-FR-001..010 module outputs."""

from __future__ import annotations

from typing import Any

from evaluation.domain import ModuleValidationResult, ValidationStatus


class ValidationEngine:
    """Produce PASS/FAIL/WARNING results with engineering explanations."""

    def __init__(self, *, config: dict[str, Any] | None = None) -> None:
        cfg = (config or {}).get("validation", {})
        self.min_detection_accuracy = float(cfg.get("min_detection_accuracy_pct", 95.0))
        self.min_classification_confidence = float(cfg.get("min_classification_confidence", 0.5))
        self.min_prediction_confidence = float(cfg.get("min_prediction_confidence", 0.3))
        self.require_exports = bool(cfg.get("require_export_artifacts", True))

    def validate_all(self, module_outputs: dict[str, Any]) -> list[ModuleValidationResult]:
        validators = {
            "FA-FR-001": self.validate_fr001,
            "FA-FR-002": self.validate_fr002,
            "FA-FR-003": self.validate_fr003,
            "FA-FR-004": self.validate_fr004,
            "FA-FR-005": self.validate_fr005,
            "FA-FR-006": self.validate_fr006,
            "FA-FR-007": self.validate_fr007,
            "FA-FR-008": self.validate_fr008,
            "FA-FR-009": self.validate_fr009,
            "FA-FR-010": self.validate_fr010,
        }
        results: list[ModuleValidationResult] = []
        for module, fn in validators.items():
            payload = module_outputs.get(module)
            if payload is None:
                results.append(
                    ModuleValidationResult(
                        module=module,
                        status=ValidationStatus.SKIPPED,
                        explanation="Module was not executed in this run.",
                    )
                )
            else:
                results.append(fn(payload))
        return results

    def validate_fr001(self, payload: dict[str, Any]) -> ModuleValidationResult:
        records = int(payload.get("record_count") or 0)
        patterns = int(payload.get("pattern_count") or 0)
        stil_ok = bool(payload.get("stil_validation_passed", True))
        skipped_full_parse = bool(payload.get("skipped_full_parse"))
        if records <= 0:
            return ModuleValidationResult(
                "FA-FR-001",
                ValidationStatus.FAIL,
                "Ingestion produced zero records; parsing or dataset selection failed.",
                {"record_count": records, "pattern_count": patterns},
                duration_ms=float(payload.get("duration_ms", 0)),
            )
        if not stil_ok and payload.get("stil_path"):
            return ModuleValidationResult(
                "FA-FR-001",
                ValidationStatus.WARNING,
                "Records ingested but STIL validation reported issues.",
                {"record_count": records, "pattern_count": patterns, "stil_notes": payload.get("stil_notes", [])},
                duration_ms=float(payload.get("duration_ms", 0)),
            )
        explanation = f"Upload/parsing OK: {records} records, {patterns} patterns referenced."
        if skipped_full_parse:
            explanation += " Large STIL used metadata-only parse threshold."
        return ModuleValidationResult(
            "FA-FR-001",
            ValidationStatus.PASS if not skipped_full_parse else ValidationStatus.WARNING,
            explanation,
            {
                "record_count": records,
                "pattern_count": patterns,
                "die_count": payload.get("die_count", 0),
                "skipped_full_parse": skipped_full_parse,
            },
            duration_ms=float(payload.get("duration_ms", 0)),
        )

    def validate_fr002(self, payload: dict[str, Any]) -> ModuleValidationResult:
        accuracy = float(
            payload.get("detection_accuracy", {})
            .get("accuracy_pct", payload.get("accuracy_pct", 0.0))
        )
        detected = int(payload.get("detected_count", payload.get("total_patterns", 0)))
        metrics = {
            "accuracy_pct": accuracy,
            "detected_count": detected,
            "false_positives": payload.get("false_positives"),
            "false_negatives": payload.get("false_negatives"),
        }
        if detected <= 0:
            return ModuleValidationResult(
                "FA-FR-002",
                ValidationStatus.FAIL,
                "Pattern detection returned no failing patterns.",
                metrics,
                duration_ms=float(payload.get("duration_ms", 0)),
            )
        if accuracy < self.min_detection_accuracy:
            return ModuleValidationResult(
                "FA-FR-002",
                ValidationStatus.WARNING,
                f"Detection accuracy {accuracy:.2f}% below target {self.min_detection_accuracy:.2f}%.",
                metrics,
                duration_ms=float(payload.get("duration_ms", 0)),
            )
        return ModuleValidationResult(
            "FA-FR-002",
            ValidationStatus.PASS,
            f"Pattern detection OK ({detected} patterns, accuracy={accuracy:.2f}%).",
            metrics,
            duration_ms=float(payload.get("duration_ms", 0)),
        )

    def validate_fr003(self, payload: dict[str, Any]) -> ModuleValidationResult:
        levels = payload.get("levels_present", [])
        required = {"device_level", "lot_level", "wafer_level", "pattern_level"}
        missing = sorted(required - set(levels))
        metrics = {"levels_present": levels, "missing_levels": missing}
        if missing:
            return ModuleValidationResult(
                "FA-FR-003",
                ValidationStatus.FAIL,
                f"Failure-rate levels missing: {', '.join(missing)}.",
                metrics,
                duration_ms=float(payload.get("duration_ms", 0)),
            )
        return ModuleValidationResult(
            "FA-FR-003",
            ValidationStatus.PASS,
            "Failure rates computed for device/lot/wafer/pattern.",
            metrics,
            duration_ms=float(payload.get("duration_ms", 0)),
        )

    def validate_fr004(self, payload: dict[str, Any]) -> ModuleValidationResult:
        total = int(payload.get("total_faults", 0))
        avg_conf = float(payload.get("average_confidence", 0.0))
        metrics = {
            "total_faults": total,
            "average_confidence": avg_conf,
            "unique_categories": payload.get("unique_categories"),
            "methods": payload.get("methods", {}),
        }
        if total <= 0:
            return ModuleValidationResult(
                "FA-FR-004",
                ValidationStatus.WARNING,
                "No faults classified (dataset may be all-pass).",
                metrics,
                duration_ms=float(payload.get("duration_ms", 0)),
            )
        if avg_conf < self.min_classification_confidence:
            return ModuleValidationResult(
                "FA-FR-004",
                ValidationStatus.WARNING,
                f"Average classification confidence {avg_conf:.2f} below threshold.",
                metrics,
                duration_ms=float(payload.get("duration_ms", 0)),
            )
        return ModuleValidationResult(
            "FA-FR-004",
            ValidationStatus.PASS,
            f"Classified {total} faults (avg confidence={avg_conf:.2f}).",
            metrics,
            duration_ms=float(payload.get("duration_ms", 0)),
        )

    def validate_fr005(self, payload: dict[str, Any]) -> ModuleValidationResult:
        recurring = int(payload.get("recurring_count", 0))
        metrics = {
            "recurring_count": recurring,
            "frequency_summary": payload.get("frequency_summary"),
            "similarity_pairs": payload.get("similarity_pairs"),
        }
        status = ValidationStatus.PASS if recurring >= 0 else ValidationStatus.FAIL
        explanation = (
            f"Recurring detection completed ({recurring} recurring signatures)."
            if recurring
            else "Recurring detection completed; no multi-lot recurrence found (valid for small samples)."
        )
        return ModuleValidationResult(
            "FA-FR-005",
            status if recurring or payload.get("executed") else ValidationStatus.WARNING,
            explanation,
            metrics,
            duration_ms=float(payload.get("duration_ms", 0)),
        )

    def validate_fr006(self, payload: dict[str, Any]) -> ModuleValidationResult:
        report_rows = int(payload.get("correlation_rows", 0))
        has_matrix = bool(payload.get("has_matrix"))
        metrics = {"correlation_rows": report_rows, "has_matrix": has_matrix}
        if report_rows <= 0 and not has_matrix:
            return ModuleValidationResult(
                "FA-FR-006",
                ValidationStatus.WARNING,
                "Correlation produced empty matrix/report for this sample.",
                metrics,
                duration_ms=float(payload.get("duration_ms", 0)),
            )
        return ModuleValidationResult(
            "FA-FR-006",
            ValidationStatus.PASS,
            f"Correlation relationships computed ({report_rows} ranked rows).",
            metrics,
            duration_ms=float(payload.get("duration_ms", 0)),
        )

    def validate_fr007(self, payload: dict[str, Any]) -> ModuleValidationResult:
        dies = int(payload.get("total_dies", 0))
        has_heatmap = bool(payload.get("has_heatmap"))
        metrics = {
            "total_dies": dies,
            "hotspot_count": payload.get("hotspot_count"),
            "has_heatmap": has_heatmap,
        }
        if dies <= 0:
            return ModuleValidationResult(
                "FA-FR-007",
                ValidationStatus.FAIL,
                "Die analytics returned zero dies.",
                metrics,
                duration_ms=float(payload.get("duration_ms", 0)),
            )
        if not has_heatmap:
            return ModuleValidationResult(
                "FA-FR-007",
                ValidationStatus.WARNING,
                "Die statistics present but heatmap payload missing.",
                metrics,
                duration_ms=float(payload.get("duration_ms", 0)),
            )
        return ModuleValidationResult(
            "FA-FR-007",
            ValidationStatus.PASS,
            f"Die analytics OK ({dies} dies, hotspots={payload.get('hotspot_count', 0)}).",
            metrics,
            duration_ms=float(payload.get("duration_ms", 0)),
        )

    def validate_fr008(self, payload: dict[str, Any]) -> ModuleValidationResult:
        wafers = int(payload.get("total_wafers") or 0)
        checks = {
            "has_heatmap": bool(payload.get("has_heatmap")),
            "has_edge_center": bool(payload.get("has_edge_center")),
            "has_radial": bool(payload.get("has_radial")),
        }
        optional = {
            "has_clusters": bool(payload.get("has_clusters")),
        }
        metrics = {"total_wafers": wafers, **checks, **optional}
        if wafers <= 0:
            return ModuleValidationResult(
                "FA-FR-008",
                ValidationStatus.FAIL,
                "Wafer analytics returned zero wafers.",
                metrics,
                duration_ms=float(payload.get("duration_ms", 0)),
            )
        missing = [k for k, v in checks.items() if not v]
        if missing:
            return ModuleValidationResult(
                "FA-FR-008",
                ValidationStatus.WARNING,
                f"Wafer analytics incomplete; missing: {', '.join(missing)}.",
                metrics,
                duration_ms=float(payload.get("duration_ms", 0)),
            )
        note = ""
        if not optional["has_clusters"]:
            note = " Cluster report empty (acceptable for sparse lots)."
        return ModuleValidationResult(
            "FA-FR-008",
            ValidationStatus.PASS,
            f"Wafer analytics OK ({wafers} wafers; heatmap/edge-center/radial present).{note}",
            metrics,
            duration_ms=float(payload.get("duration_ms", 0)),
        )

    def validate_fr009(self, payload: dict[str, Any]) -> ModuleValidationResult:
        preds = int(payload.get("total_predictions", 0))
        avg_conf = float(payload.get("average_confidence", 0.0))
        has_hist = bool(payload.get("has_historical_cases"))
        has_recs = bool(payload.get("has_recommendations"))
        metrics = {
            "total_predictions": preds,
            "average_confidence": avg_conf,
            "has_historical_cases": has_hist,
            "has_recommendations": has_recs,
        }
        if preds <= 0:
            return ModuleValidationResult(
                "FA-FR-009",
                ValidationStatus.WARNING,
                "No root-cause predictions generated for this sample.",
                metrics,
                duration_ms=float(payload.get("duration_ms", 0)),
            )
        if avg_conf < self.min_prediction_confidence:
            return ModuleValidationResult(
                "FA-FR-009",
                ValidationStatus.WARNING,
                f"Prediction confidence {avg_conf:.2f} below threshold.",
                metrics,
                duration_ms=float(payload.get("duration_ms", 0)),
            )
        return ModuleValidationResult(
            "FA-FR-009",
            ValidationStatus.PASS,
            f"Root-cause predictions OK ({preds}, avg confidence={avg_conf:.2f}).",
            metrics,
            duration_ms=float(payload.get("duration_ms", 0)),
        )

    def validate_fr010(self, payload: dict[str, Any]) -> ModuleValidationResult:
        has_exec = bool(payload.get("has_executive_summary"))
        has_eng = bool(payload.get("has_engineering_summary"))
        has_dash = bool(payload.get("has_dashboard"))
        exports = payload.get("exports", {})
        metrics = {
            "has_executive_summary": has_exec,
            "has_engineering_summary": has_eng,
            "has_dashboard": has_dash,
            "exports": exports,
        }
        if not (has_exec and has_eng and has_dash):
            return ModuleValidationResult(
                "FA-FR-010",
                ValidationStatus.FAIL,
                "Report missing executive/engineering summary or dashboard dataset.",
                metrics,
                duration_ms=float(payload.get("duration_ms", 0)),
            )
        if self.require_exports:
            missing = [k for k in ("pdf", "excel", "json") if not exports.get(k)]
            if missing:
                return ModuleValidationResult(
                    "FA-FR-010",
                    ValidationStatus.WARNING,
                    f"Summaries generated but export artifacts missing: {', '.join(missing)}.",
                    metrics,
                    duration_ms=float(payload.get("duration_ms", 0)),
                )
        return ModuleValidationResult(
            "FA-FR-010",
            ValidationStatus.PASS,
            "Engineering report, dashboard, and exports generated.",
            metrics,
            duration_ms=float(payload.get("duration_ms", 0)),
        )
