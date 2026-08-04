"""Dispatch parse jobs to the best-matching v2 plugin (v1 fallback)."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from parser_engine.v2.contracts import DetectionResult, Issue, ParseContext, ParseOutcome
from parser_engine.v2.detector import Detector
from parser_engine.v2.models.enterprise_record import EnterpriseRecord
from parser_engine.v2.models.normalize import from_parser_result
from parser_engine.v2.registry import PluginRegistry


class Dispatcher:
    def __init__(self, registry: PluginRegistry, detector: Detector | None = None) -> None:
        self.registry = registry
        self.detector = detector or Detector(registry)

    def resolve(
        self,
        path: Path,
        ctx: ParseContext,
        *,
        parser_id: str | None = None,
    ) -> tuple[DetectionResult | None, str | None]:
        if parser_id:
            return (
                DetectionResult(parser_id=parser_id, confidence=1.0, signals=["forced"]),
                parser_id,
            )
        best = self.detector.best(path, ctx)
        if best:
            return best, best.parser_id
        return None, None

    def parse(
        self,
        path: Path,
        ctx: ParseContext | None = None,
        *,
        parser_id: str | None = None,
    ) -> ParseOutcome:
        ctx = ctx or ParseContext()
        detection, pid = self.resolve(path, ctx, parser_id=parser_id)
        if pid:
            plugin = self.registry.get(pid)
            if plugin is None:
                return ParseOutcome(
                    parser_id=pid,
                    errors=[Issue(code="PLUGIN_MISSING", message=f"No plugin registered: {pid}")],
                    success=False,
                )
            outcome = plugin.parse(path, ctx)
            if detection:
                outcome.metadata.setdefault("detection", {
                    "confidence": detection.confidence,
                    "vendor": detection.vendor,
                    "signals": detection.signals,
                })
            return outcome
        return self._fallback_v1(path, ctx)

    def stream(
        self,
        path: Path,
        ctx: ParseContext | None = None,
        *,
        parser_id: str | None = None,
    ) -> Iterator[EnterpriseRecord]:
        ctx = ctx or ParseContext()
        _, pid = self.resolve(path, ctx, parser_id=parser_id)
        if not pid:
            outcome = self._fallback_v1(path, ctx)
            yield from outcome.records
            return
        plugin = self.registry.get(pid)
        if plugin is None:
            return
        if ctx.enable_stream and plugin.supports_streaming():
            yield from plugin.stream(path, ctx)
        else:
            yield from plugin.parse(path, ctx).records

    def _fallback_v1(self, path: Path, ctx: ParseContext) -> ParseOutcome:
        try:
            from parser_engine.parsers.factory import ParserFactory

            result, pid = ParserFactory().parse(path)
            parser_id = pid or "v1_factory"
            errors = []
            for err in getattr(result, "errors", []) or []:
                errors.append(Issue(code="V1_PARSE", message=str(err.get("error") or err), severity="warning"))
            return ParseOutcome(
                parser_id=parser_id,
                records=from_parser_result(result, parser_id=parser_id),
                errors=errors,
                metadata={"fallback": "v1", "source_file": str(path)},
                raw=result,
                success=not any(e.severity == "error" for e in errors),
            )
        except Exception as exc:  # noqa: BLE001
            return ParseOutcome(
                parser_id="v1_factory",
                errors=[Issue(code="DISPATCH_FAIL", message=str(exc))],
                success=False,
            )
