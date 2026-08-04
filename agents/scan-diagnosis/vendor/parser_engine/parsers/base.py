"""Common parser interface for FA-FR-001 enterprise ingestion."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from parser_engine.adapters.schema import TestRecord


@dataclass
class ParserResult:
    records: list[TestRecord] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseParser(ABC):
    """Strategy interface — every format parser implements detect + parse."""

    parser_id: str = "base"

    @abstractmethod
    def detect(self, path: Path) -> bool:
        raise NotImplementedError

    @abstractmethod
    def parse(self, path: Path) -> ParserResult:
        raise NotImplementedError

    def supported_extensions(self) -> set[str]:
        return set()
