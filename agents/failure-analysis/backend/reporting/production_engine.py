"""Production handoff gates, completeness, and consistency scoring."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from adapters.yaml_config import load_adapter_configs

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "reporting.yaml"

REQUIRED_MODULES = (
    "FA-FR-001",
    "FA-FR-002",
    "FA-FR-003",
    "FA-FR-004",
    "FA-FR-005",
    "FA-FR-006",
    "FA-FR-007",
    "FA-FR-008",
    "FA-FR-009",
)


@dataclass
class ReportingConfig:
    version: str
    report_target_ms: int
    pdf_target_ms: int
    excel_target_ms: int
    min_completeness_score: float
    min_consistency_score: float
    storage_dir: Path
    pdf_enabled: bool
    excel_enabled: bool
    json_enabled: bool
    html_enabled: bool
    csv_enabled: bool
    template_path: Path
    sections: dict[str, bool]

    @classmethod
    def load(cls, config_path: Path | str | None = None) -> "ReportingConfig":
        raw = load_adapter_configs(Path(config_path) if config_path else DEFAULT_CONFIG)
        perf = raw.get("performance", {})
        export_cfg = raw.get("export", {})
        storage = export_cfg.get("storage_dir", "backend/storage/reports")
        storage_path = Path(storage)
        if not storage_path.is_absolute():
            storage_path = Path(__file__).resolve().parents[2] / storage
        template_rel = raw.get("report", {}).get(
            "template_path", "backend/reporting/templates/engineering_report.html.j2"
        )
        template_path = Path(template_rel)
        if not template_path.is_absolute():
            template_path = Path(__file__).resolve().parents[2] / template_path
        gates = raw.get("production_gates", {})
        return cls(
            version=str(raw.get("schema_version", "1.0")),
            report_target_ms=int(perf.get("report_generation_target_ms", 10000)),
            pdf_target_ms=int(perf.get("pdf_generation_target_ms", 5000)),
            excel_target_ms=int(perf.get("excel_export_target_ms", 5000)),
            min_completeness_score=float(gates.get("min_completeness_score", 0.85)),
            min_consistency_score=float(gates.get("min_consistency_score", 0.80)),
            storage_dir=storage_path,
            pdf_enabled=bool(export_cfg.get("pdf_enabled", True)),
            excel_enabled=bool(export_cfg.get("excel_enabled", True)),
            json_enabled=bool(export_cfg.get("json_enabled", True)),
            html_enabled=bool(export_cfg.get("html_enabled", True)),
            csv_enabled=bool(export_cfg.get("csv_enabled", True)),
            template_path=template_path,
            sections=raw.get("sections", {}),
        )


class ReportHandoffGateError(ValueError):
    def __init__(self, issues: list[dict[str, Any]]) -> None:
        self.issues = issues
        super().__init__("Upstream production handoff gates failed")


def validate_upstream_handoff(upstream: dict[str, Any]) -> list[dict[str, Any]]:
    """Require completed production audits for FA-FR-001..009 where available."""
    issues: list[dict[str, Any]] = []
    checks = [
        ("FA-FR-001", "ingestion", "status", "completed"),
        ("FA-FR-002", "detection", "execution_status", "completed"),
        ("FA-FR-003", "computation", "status", "completed"),
        ("FA-FR-004", "classification", "status", "completed"),
        ("FA-FR-005", "recurrence", "status", "completed"),
        ("FA-FR-006", "correlation", "status", "completed"),
        ("FA-FR-007", "die_analysis", "status", "completed"),
        ("FA-FR-008", "wafer_analysis", "status", "completed"),
        ("FA-FR-009", "fault_prediction", "status", "completed"),
    ]
    for requirement, key, field, expected in checks:
        record = upstream.get(key)
        if not record:
            issues.append(
                {
                    "code": "UPSTREAM_MISSING",
                    "requirement": requirement,
                    "message": f"Missing completed {requirement} audit",
                }
            )
            continue
        actual = record.get(field)
        if actual != expected:
            issues.append(
                {
                    "code": "UPSTREAM_INCOMPLETE",
                    "requirement": requirement,
                    "message": f"{requirement} audit {field}={actual!r}, expected {expected!r}",
                }
            )
    return issues


def score_completeness(
    *,
    module_outputs: dict[str, Any],
    module_sections: dict[str, Any],
    recommendations: list[dict[str, Any]],
) -> float:
    weights = {
        "fa_fr_001_ingestion": 0.08,
        "fa_fr_002_patterns": 0.12,
        "fa_fr_003_failure_rates": 0.10,
        "fa_fr_004_classification": 0.10,
        "fa_fr_005_recurrence": 0.10,
        "fa_fr_006_correlation": 0.10,
        "fa_fr_007_die_analysis": 0.12,
        "fa_fr_008_wafer_analysis": 0.12,
        "fa_fr_009_fault_prediction": 0.10,
        "recommendations": 0.06,
    }
    earned = 0.0
    for section, weight in weights.items():
        if section == "recommendations":
            if recommendations:
                earned += weight
            continue
        payload = module_sections.get(section, {})
        if payload and _section_has_data(payload):
            earned += weight
    return round(min(earned, 1.0), 4)


def score_consistency(
    *,
    upstream: dict[str, Any],
    module_outputs: dict[str, Any],
) -> float:
    checks = 0
    passed = 0
    detection_id = upstream.get("detection", {}).get("analysis_id")
    computation_id = upstream.get("computation", {}).get("computation_id")
    recurrence_id = upstream.get("recurrence", {}).get("analysis_id")
    correlation_id = upstream.get("correlation", {}).get("analysis_id")
    die_id = upstream.get("die_analysis", {}).get("analysis_id")
    wafer_id = upstream.get("wafer_analysis", {}).get("analysis_id")
    prediction_upstream = upstream.get("fault_prediction", {}).get("upstream_execution_ids", {})

    lineage_pairs = [
        (computation_id, upstream.get("computation", {}).get("detection_execution_id")),
        (recurrence_id, upstream.get("recurrence", {}).get("detection_execution_id")),
        (correlation_id, upstream.get("correlation", {}).get("detection_execution_id")),
        (die_id, upstream.get("die_analysis", {}).get("detection_execution_id")),
        (wafer_id, upstream.get("wafer_analysis", {}).get("detection_execution_id")),
    ]
    for left, right in lineage_pairs:
        if left and right:
            checks += 1
            if left == right or right == detection_id:
                passed += 1

    if prediction_upstream:
        checks += 1
        if prediction_upstream.get("detection_execution_id") == detection_id:
            passed += 1

    die_mod = module_outputs.get("die_analysis", {})
    wafer_mod = module_outputs.get("wafer_analysis", {})
    if die_mod.get("total_dies") and wafer_mod.get("total_dies"):
        checks += 1
        if die_mod["total_dies"] <= wafer_mod["total_dies"] * 2:
            passed += 1

    if checks == 0:
        return 1.0
    return round(passed / checks, 4)


def build_benchmark_summary(
    *,
    completeness_score: float,
    consistency_score: float,
    processing_ms: float,
    pdf_ms: float,
    excel_ms: float,
    config: ReportingConfig,
    upstream_benchmarks: dict[str, Any],
) -> dict[str, Any]:
    return {
        "completeness_score": completeness_score,
        "consistency_score": consistency_score,
        "processing_ms": processing_ms,
        "pdf_ms": pdf_ms,
        "excel_ms": excel_ms,
        "meets_performance_target": (
            processing_ms < config.report_target_ms
            and pdf_ms < config.pdf_target_ms
            and excel_ms < config.excel_target_ms
        ),
        "completeness_passed": completeness_score >= config.min_completeness_score,
        "consistency_passed": consistency_score >= config.min_consistency_score,
        "upstream_benchmarks": upstream_benchmarks,
    }


def build_traceability(
    *,
    report_id: str,
    dataset_id: str | None,
    upload_id: str | None,
    template_key: str,
    upstream: dict[str, Any],
) -> dict[str, Any]:
    return {
        "report_id": report_id,
        "dataset_id": dataset_id,
        "upload_id": upload_id,
        "template_key": template_key,
        "requirements": REQUIRED_MODULES,
        "upstream": {
            key: {
                "id": record.get(
                    "analysis_id",
                    record.get(
                        "computation_id",
                        record.get("execution_id", record.get("source_id")),
                    ),
                ),
                "status": record.get(
                    "status", record.get("execution_status", "unknown")
                ),
            }
            for key, record in upstream.items()
            if isinstance(record, dict)
        },
    }


def _section_has_data(payload: dict[str, Any]) -> bool:
    for key, value in payload.items():
        if key in {"requirement", "disclaimer", "status"}:
            continue
        if isinstance(value, (list, dict)) and value:
            return True
        if isinstance(value, (int, float)) and value:
            return True
        if isinstance(value, str) and value.strip():
            return True
    return False
