"""Unified enterprise record model for all parser formats."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

ENTERPRISE_SCHEMA_VERSION = "2.0.0"


@dataclass
class EnterpriseRecord:
    """Canonical record shared by Pattern / Failure / Diagnosis / future agents."""

    lot_id: str = ""
    wafer_id: str = ""
    die_id: str = ""
    test_stage: str = ""
    tester_id: str = ""
    pass_fail: str = ""
    timestamp: str = ""
    source_file: str = ""
    parser_id: str = ""
    product_id: str = ""
    hard_bin: str = ""
    soft_bin: str = ""
    x: int | None = None
    y: int | None = None
    failing_tests: list[str] = field(default_factory=list)
    failing_patterns: list[str] = field(default_factory=list)
    chain_id: str = ""
    fail_flop_id: str = ""
    fail_type: str = ""
    expected_signature: str = ""
    actual_signature: str = ""
    scan_fail_data: dict[str, Any] = field(default_factory=dict)
    parametric: dict[str, float | str] = field(default_factory=dict)
    raw_fields: dict[str, Any] = field(default_factory=dict)
    record_key: str = ""
    parse_confidence: float = 1.0
    quarantine_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schema_version"] = ENTERPRISE_SCHEMA_VERSION
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnterpriseRecord:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})

    def build_record_key(self) -> str:
        parts = [
            self.source_file,
            self.lot_id,
            self.wafer_id,
            self.die_id,
            self.test_stage,
            self.chain_id,
            self.fail_flop_id,
            str(self.x) if self.x is not None else "",
            str(self.y) if self.y is not None else "",
            "|".join(sorted(self.failing_patterns[:3])),
        ]
        return "::".join(parts)

    def is_quarantined(self) -> bool:
        return bool(self.quarantine_reason)
