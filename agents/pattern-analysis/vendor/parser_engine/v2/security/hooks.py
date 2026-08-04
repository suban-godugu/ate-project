"""Security hooks — hashing, size/extension gates, quarantine, callbacks."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Callable

from parser_engine.v2.contracts import Issue, ParseContext, ParseOutcome
from parser_engine.v2.models.enterprise_record import EnterpriseRecord

DEFAULT_ALLOW_EXT = {
    ".stil",
    ".log",
    ".txt",
    ".dat",
    ".stdf",
    ".std",
    ".csv",
    ".json",
    ".xml",
    ".wgl",
    ".atdf",
    ".atd",
    ".vcd",
    ".evcd",
}


class SecurityHooks:
    def __init__(
        self,
        *,
        allow_extensions: set[str] | None = None,
        max_size_bytes: int | None = 10 * 1024**3,
        virus_scan: Callable[[Path], bool] | None = None,
        audit: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.allow_extensions = allow_extensions or set(DEFAULT_ALLOW_EXT)
        self.max_size_bytes = max_size_bytes
        self.virus_scan = virus_scan
        self.audit = audit

    def sha256(self, path: Path, *, chunk: int = 1024 * 1024) -> str:
        h = hashlib.sha256()
        with path.open("rb") as fh:
            while True:
                block = fh.read(chunk)
                if not block:
                    break
                h.update(block)
        return h.hexdigest()

    def preflight(self, path: Path, ctx: ParseContext | None = None) -> list[Issue]:
        issues: list[Issue] = []
        ext = path.suffix.lower()
        if self.allow_extensions and ext and ext not in self.allow_extensions:
            issues.append(Issue(code="EXT_BLOCKED", message=f"Extension not allowed: {ext}"))
        limit = (ctx.max_size_bytes if ctx and ctx.max_size_bytes is not None else self.max_size_bytes)
        if limit is not None and path.exists():
            size = path.stat().st_size
            if size > limit:
                issues.append(Issue(code="SIZE_BLOCKED", message=f"File size {size} > {limit}"))
        if self.virus_scan is not None and path.exists():
            try:
                if not self.virus_scan(path):
                    issues.append(Issue(code="VIRUS_BLOCKED", message="Virus scan rejected file"))
            except Exception as exc:  # noqa: BLE001
                issues.append(Issue(code="VIRUS_ERROR", message=str(exc), severity="warning"))
        return issues

    def quarantine_records(
        self,
        records: list[EnterpriseRecord],
        *,
        reason: str = "low_confidence",
        min_confidence: float = 0.3,
    ) -> tuple[list[EnterpriseRecord], list[dict[str, Any]]]:
        kept: list[EnterpriseRecord] = []
        quarantined: list[dict[str, Any]] = []
        for rec in records:
            if rec.parse_confidence < min_confidence or rec.quarantine_reason:
                rec.quarantine_reason = rec.quarantine_reason or reason
                quarantined.append(rec.to_dict())
            else:
                kept.append(rec)
        return kept, quarantined

    def audit_event(self, event: dict[str, Any]) -> None:
        if self.audit:
            try:
                self.audit(event)
            except Exception:
                pass

    def annotate_outcome(self, path: Path, outcome: ParseOutcome) -> ParseOutcome:
        try:
            digest = self.sha256(path)
            outcome.metadata["sha256"] = digest
            if outcome.resume_token is None:
                outcome.resume_token = {"file_sha256": digest, "byte_offset": 0, "line_no": 0}
            else:
                outcome.resume_token.setdefault("file_sha256", digest)
        except OSError:
            pass
        self.audit_event(
            {
                "event": "parse_complete",
                "parser_id": outcome.parser_id,
                "source_file": str(path),
                "success": outcome.success,
                "record_count": len(outcome.records),
                "sha256": outcome.metadata.get("sha256"),
            }
        )
        return outcome
