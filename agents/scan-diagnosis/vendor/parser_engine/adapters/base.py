"""LogAdapter plugin base classes and ingestion result types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from parser_engine.adapters.schema import TestRecord


@dataclass
class AdapterParseResult:
    """Output of a single adapter parse() call."""

    records: list[TestRecord] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IngestionReport:
    """Aggregate ingestion outcome for a directory or file batch."""

    files_discovered: int = 0
    files_parsed: int = 0
    files_failed: int = 0
    records_accepted: int = 0
    records_quarantined: int = 0
    adapters_used: dict[str, int] = field(default_factory=dict)
    errors: list[dict[str, str]] = field(default_factory=list)
    quarantine: list[dict[str, Any]] = field(default_factory=list)
    integrity_pct: float = 100.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "files_discovered": self.files_discovered,
            "files_parsed": self.files_parsed,
            "files_failed": self.files_failed,
            "records_accepted": self.records_accepted,
            "records_quarantined": self.records_quarantined,
            "adapters_used": self.adapters_used,
            "integrity_pct": self.integrity_pct,
            "errors": self.errors,
            "quarantine_count": len(self.quarantine),
            "quarantine_sample": self.quarantine[:10],
        }


class LogAdapter(ABC):
    """Plugin interface for customer-specific log formats (FA-FR-001)."""

    adapter_id: str = "base"

    @abstractmethod
    def detect(self, path: Path) -> bool:
        """Return True if this adapter can parse *path*."""

    @abstractmethod
    def parse(self, path: Path) -> AdapterParseResult:
        """Parse *path* into canonical TestRecord objects."""

    def validate(self, records: list[TestRecord]) -> tuple[list[TestRecord], list[dict[str, Any]]]:
        """Optional post-parse validation; default accepts all records."""
        from parser_engine.adapters.validation import partition_records

        return partition_records(records)
