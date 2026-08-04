"""Canonical normalized test record schema (FA-FR-001)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

SCHEMA_VERSION = "1.0.0"

MANDATORY_FIELDS = (
    "lot_id",
    "wafer_id",
    "die_id",
    "test_stage",
    "tester_id",
    "pass_fail",
    "timestamp",
    "source_file",
    "adapter_id",
)


@dataclass
class TestRecord:
    """Normalized output of ingestion — one row per die-level or test-level record."""

    lot_id: str
    wafer_id: str
    die_id: str
    test_stage: str
    tester_id: str
    pass_fail: str
    timestamp: str
    source_file: str
    adapter_id: str
    x: int | None = None
    y: int | None = None
    product_id: str = ""
    hard_bin: str = ""
    soft_bin: str = ""
    failing_tests: list[str] = field(default_factory=list)
    failing_patterns: list[str] = field(default_factory=list)
    scan_fail_data: dict[str, Any] = field(default_factory=dict)
    parametric: dict[str, float | str] = field(default_factory=dict)
    record_key: str = ""
    raw_fields: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schema_version"] = SCHEMA_VERSION
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TestRecord:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known}
        return cls(**kwargs)

    def missing_mandatory(self) -> list[str]:
        missing: list[str] = []
        for name in MANDATORY_FIELDS:
            value = getattr(self, name, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(name)
        return missing

    def is_valid(self) -> bool:
        return not self.missing_mandatory()

    def build_record_key(self) -> str:
        """Stable dedupe key for idempotent re-ingestion."""
        parts = [
            self.source_file,
            self.lot_id,
            self.wafer_id,
            self.die_id,
            self.test_stage,
            str(self.x) if self.x is not None else "",
            str(self.y) if self.y is not None else "",
            "|".join(sorted(self.failing_patterns[:3])),
        ]
        return "::".join(parts)
