"""Intelligent format / vendor detection with confidence scoring."""

from __future__ import annotations

from pathlib import Path

from parser_engine.v2.contracts import DetectionResult, ParseContext
from parser_engine.v2.registry import PluginRegistry


class Detector:
    """Run all registered plugins' detect() and rank by confidence."""

    def __init__(self, registry: PluginRegistry) -> None:
        self.registry = registry

    def detect_all(self, path: Path, ctx: ParseContext | None = None) -> list[DetectionResult]:
        ctx = ctx or ParseContext()
        results: list[DetectionResult] = []
        for plugin in self.registry.all():
            try:
                result = plugin.detect(path, ctx)
                if result and result.ok:
                    results.append(result)
            except Exception:
                continue
        results.sort(key=lambda r: r.confidence, reverse=True)
        return results

    def best(
        self,
        path: Path,
        ctx: ParseContext | None = None,
        *,
        threshold: float | None = None,
    ) -> DetectionResult | None:
        ctx = ctx or ParseContext()
        thr = threshold if threshold is not None else ctx.confidence_threshold
        ranked = self.detect_all(path, ctx)
        if not ranked:
            return None
        top = ranked[0]
        if top.confidence < thr:
            return None
        return top
