"""Serialize ParseOutcome / EnterpriseRecord to common export shapes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from parser_engine.v2.contracts import ParseOutcome
from parser_engine.v2.models.enterprise_record import EnterpriseRecord


class OutputManager:
    def to_dicts(self, records: list[EnterpriseRecord]) -> list[dict[str, Any]]:
        return [r.to_dict() for r in records]

    def to_json(self, outcome: ParseOutcome, *, indent: int = 2) -> str:
        payload = {
            "parser_id": outcome.parser_id,
            "success": outcome.success,
            "cache_hit": outcome.cache_hit,
            "metadata": outcome.metadata,
            "errors": [
                {"code": e.code, "message": e.message, "severity": e.severity, "line": e.line}
                for e in outcome.errors
            ],
            "quarantine": outcome.quarantine,
            "resume_token": outcome.resume_token,
            "records": self.to_dicts(outcome.records),
        }
        return json.dumps(payload, indent=indent, default=str)

    def write_json(self, outcome: ParseOutcome, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(outcome), encoding="utf-8")
        return path

    def write_jsonl(self, records: list[EnterpriseRecord], path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec.to_dict(), default=str) + "\n")
        return path
