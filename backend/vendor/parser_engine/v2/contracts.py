"""Parser Engine v2 contracts — common plugin interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from parser_engine.v2.models.enterprise_record import EnterpriseRecord


@dataclass
class ParseContext:
    """Runtime options for a parse job."""

    profile: str = "auto"
    max_size_bytes: int | None = None
    resume_offset: int = 0
    resume_line: int = 0
    enable_stream: bool = True
    enable_cache: bool = True
    confidence_threshold: float = 0.6
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class DetectionResult:
    parser_id: str
    confidence: float
    vendor: str = "unknown"
    signals: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.confidence > 0.0 and bool(self.parser_id)


@dataclass
class Issue:
    code: str
    message: str
    severity: str = "error"  # error | warning | info
    line: int | None = None


@dataclass
class ParseOutcome:
    """Unified parse result for v2."""

    parser_id: str
    records: list[EnterpriseRecord] = field(default_factory=list)
    errors: list[Issue] = field(default_factory=list)
    quarantine: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    raw: Any = None
    resume_token: dict[str, Any] | None = None
    cache_hit: bool = False
    success: bool = True


class BaseParserV2(ABC):
    """Every v2 parser plugin implements this contract."""

    parser_id: str = "base"
    extensions: set[str] = set()

    @abstractmethod
    def detect(self, path: Path, ctx: ParseContext) -> DetectionResult:
        raise NotImplementedError

    def validate(self, path: Path, ctx: ParseContext) -> list[Issue]:
        issues: list[Issue] = []
        if not path.exists():
            issues.append(Issue(code="FILE_MISSING", message=f"File not found: {path}"))
            return issues
        if not path.is_file():
            issues.append(Issue(code="NOT_A_FILE", message=f"Not a file: {path}"))
        if ctx.max_size_bytes is not None:
            size = path.stat().st_size
            if size > ctx.max_size_bytes:
                issues.append(
                    Issue(
                        code="FILE_TOO_LARGE",
                        message=f"Size {size} exceeds limit {ctx.max_size_bytes}",
                    )
                )
        return issues

    @abstractmethod
    def parse(self, path: Path, ctx: ParseContext) -> ParseOutcome:
        raise NotImplementedError

    def normalize(self, raw: Any) -> list[EnterpriseRecord]:
        return []

    def metadata(self, path: Path, outcome: ParseOutcome) -> dict[str, Any]:
        return {
            "parser_id": self.parser_id,
            "source_file": str(path),
            "record_count": len(outcome.records),
            "error_count": len(outcome.errors),
            "quarantine_count": len(outcome.quarantine),
        }

    def stream(self, path: Path, ctx: ParseContext) -> Iterator[EnterpriseRecord]:
        """Default: parse fully then yield records."""
        outcome = self.parse(path, ctx)
        yield from outcome.records

    def supports_streaming(self) -> bool:
        return False
