"""Lightweight file validation helpers."""

from __future__ import annotations

from pathlib import Path

from parser_engine.v2.contracts import Issue, ParseContext


class Validator:
    def check(self, path: Path, ctx: ParseContext | None = None) -> list[Issue]:
        ctx = ctx or ParseContext()
        issues: list[Issue] = []
        if not path.exists():
            issues.append(Issue(code="FILE_MISSING", message=f"File not found: {path}"))
            return issues
        if not path.is_file():
            issues.append(Issue(code="NOT_A_FILE", message=f"Not a file: {path}"))
        if ctx.max_size_bytes is not None and path.stat().st_size > ctx.max_size_bytes:
            issues.append(
                Issue(
                    code="FILE_TOO_LARGE",
                    message=f"Size {path.stat().st_size} exceeds {ctx.max_size_bytes}",
                )
            )
        return issues
