"""Domain entities for the evaluation framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ValidationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"


@dataclass
class ModuleValidationResult:
    module: str
    status: ValidationStatus
    explanation: str
    metrics: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    exceptions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "module": self.module,
            "status": self.status.value,
            "explanation": self.explanation,
            "metrics": self.metrics,
            "duration_ms": self.duration_ms,
            "exceptions": self.exceptions,
        }


@dataclass
class DatasetBundle:
    """Matched STIL + log corpus for a pattern scale (1000/2000/full)."""

    dataset_id: str
    scale_token: str
    stil_paths: list[Path] = field(default_factory=list)
    log_paths: list[Path] = field(default_factory=list)
    labelled_log_paths: list[Path] = field(default_factory=list)
    tabular_paths: list[Path] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def primary_stil(self) -> Path | None:
        return self.stil_paths[0] if self.stil_paths else None

    @property
    def preferred_logs(self) -> list[Path]:
        if self.labelled_log_paths:
            return self.labelled_log_paths
        return self.log_paths

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "scale_token": self.scale_token,
            "stil_paths": [str(p) for p in self.stil_paths],
            "log_count": len(self.log_paths),
            "labelled_log_count": len(self.labelled_log_paths),
            "tabular_paths": [str(p) for p in self.tabular_paths],
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


@dataclass
class DiscoveredInventory:
    roots: list[str]
    stil_files: list[Path]
    log_files: list[Path]
    tabular_files: list[Path]
    bundles: list[DatasetBundle]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "roots": self.roots,
            "stil_count": len(self.stil_files),
            "log_count": len(self.log_files),
            "tabular_count": len(self.tabular_files),
            "bundles": [b.to_dict() for b in self.bundles],
            "warnings": self.warnings,
            "stil_files": [str(p) for p in self.stil_files],
            "log_files_sample": [str(p) for p in self.log_files[:50]],
            "tabular_files": [str(p) for p in self.tabular_files],
        }
