"""Shared helpers for v2 plugins that wrap v1 parsers."""

from __future__ import annotations

from pathlib import Path

from parser_engine.v2.contracts import DetectionResult, ParseContext


def ext_of(path: Path) -> str:
    return path.suffix.lower()


def read_head_text(path: Path, n: int = 4096) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as fh:
            return fh.read(n)
    except OSError:
        return ""


def read_head_bytes(path: Path, n: int = 16) -> bytes:
    try:
        with path.open("rb") as fh:
            return fh.read(n)
    except OSError:
        return b""


def score_extension(path: Path, extensions: set[str], base: float = 0.45) -> float:
    return base if ext_of(path) in extensions else 0.0


def clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def detection(
    parser_id: str,
    confidence: float,
    vendor: str = "unknown",
    signals: list[str] | None = None,
) -> DetectionResult:
    return DetectionResult(
        parser_id=parser_id,
        confidence=clamp01(confidence),
        vendor=vendor,
        signals=signals or [],
    )


def default_ctx(ctx: ParseContext | None) -> ParseContext:
    return ctx or ParseContext()
