"""ParserEngineV2 — additive enterprise facade (v1 APIs unchanged)."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Iterator

from parser_engine.v2.ai.features import AIFeatureService
from parser_engine.v2.analytics.metrics import MetricsStore, ParseMetric
from parser_engine.v2.cache.manager import CacheManager
from parser_engine.v2.contracts import DetectionResult, Issue, ParseContext, ParseOutcome
from parser_engine.v2.detector import Detector
from parser_engine.v2.dispatcher import Dispatcher
from parser_engine.v2.metadata.service import MetadataService
from parser_engine.v2.models.enterprise_record import EnterpriseRecord
from parser_engine.v2.output.manager import OutputManager
from parser_engine.v2.registry import PluginRegistry, default_registry
from parser_engine.v2.security.hooks import SecurityHooks
from parser_engine.v2.streaming.pipeline import parse_paths_parallel
from parser_engine.v2.validator import Validator


class ParserEngineV2:
    """
    Enterprise entry point: detect → validate → parse/stream → normalize → metrics.

    Agents keep using `parser_engine.ParserEngine` (v1) until they opt in.
    """

    def __init__(
        self,
        *,
        registry: PluginRegistry | None = None,
        cache: CacheManager | None = None,
        metrics: MetricsStore | None = None,
        security: SecurityHooks | None = None,
        auto_discover: bool = True,
    ) -> None:
        self.registry = registry or (default_registry() if auto_discover else PluginRegistry())
        self.detector = Detector(self.registry)
        self.dispatcher = Dispatcher(self.registry, self.detector)
        self.validator = Validator()
        self.cache = cache or CacheManager()
        self.metrics = metrics or MetricsStore()
        self.security = security or SecurityHooks()
        self.metadata = MetadataService()
        self.ai = AIFeatureService()
        self.output = OutputManager()

    def detect(self, file: str | Path, ctx: ParseContext | None = None) -> list[DetectionResult]:
        return self.detector.detect_all(Path(file), ctx)

    def parse(
        self,
        file: str | Path,
        *,
        profile: str = "auto",
        parser_id: str | None = None,
        ctx: ParseContext | None = None,
        use_cache: bool | None = None,
        retries: int = 1,
    ) -> ParseOutcome:
        path = Path(file)
        ctx = ctx or ParseContext(profile=profile)
        if profile and not ctx.profile:
            ctx.profile = profile

        sec_issues = self.security.preflight(path, ctx)
        if any(i.severity == "error" for i in sec_issues):
            return ParseOutcome(parser_id=parser_id or "blocked", errors=sec_issues, success=False)

        val_issues = self.validator.check(path, ctx)
        if any(i.severity == "error" for i in val_issues):
            return ParseOutcome(parser_id=parser_id or "invalid", errors=val_issues, success=False)

        enable_cache = self.cache is not None and (use_cache if use_cache is not None else ctx.enable_cache)
        cache_key_id = parser_id or "auto"

        if enable_cache:
            cached = self.cache.get(path, cache_key_id, ctx.profile)
            if cached is not None:
                self._record_metric(path, cached, elapsed_ms=0.0)
                return cached

        last: ParseOutcome | None = None
        attempts = max(1, retries)
        t0 = time.perf_counter()
        for attempt in range(attempts):
            try:
                last = self.dispatcher.parse(path, ctx, parser_id=parser_id)
                break
            except OSError as exc:
                last = ParseOutcome(
                    parser_id=parser_id or "io",
                    errors=[Issue(code="IO_RETRY", message=f"attempt {attempt + 1}: {exc}")],
                    success=False,
                )
                if attempt + 1 >= attempts:
                    break
        assert last is not None
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        kept, quarantined = self.security.quarantine_records(last.records)
        last.records = kept
        last.quarantine.extend(quarantined)
        last.metadata = self.metadata.enrich(path, last)
        last = self.security.annotate_outcome(path, last)
        last.errors = sec_issues + val_issues + list(last.errors)

        if enable_cache and last.success:
            self.cache.put(path, last.parser_id or cache_key_id, last, ctx.profile)

        self._record_metric(path, last, elapsed_ms=elapsed_ms)
        return last

    def stream(
        self,
        file: str | Path,
        *,
        profile: str = "auto",
        parser_id: str | None = None,
        ctx: ParseContext | None = None,
    ) -> Iterator[EnterpriseRecord]:
        path = Path(file)
        ctx = ctx or ParseContext(profile=profile, enable_stream=True)
        yield from self.dispatcher.stream(path, ctx, parser_id=parser_id)

    def parse_many(
        self,
        files: list[str | Path],
        *,
        profile: str = "auto",
        max_workers: int | None = None,
    ) -> list[ParseOutcome]:
        paths = [Path(f) for f in files]

        def _one(p: Path) -> ParseOutcome:
            return self.parse(p, profile=profile)

        # For pickling safety in ProcessPool, run sequentially if workers would fail;
        # pipeline helper used when callers pass a top-level function.
        if max_workers == 1 or len(paths) <= 1:
            return [_one(p) for p in paths]
        try:
            return parse_paths_parallel(paths, _one, max_workers=max_workers)
        except Exception:
            return [_one(p) for p in paths]

    def features(self, outcome: ParseOutcome, **kwargs: Any) -> dict[str, Any]:
        return self.ai.from_outcome(outcome, **kwargs)

    def metrics_snapshot(self) -> dict[str, Any]:
        snap = self.metrics.snapshot()
        snap["cache"] = self.cache.stats()
        snap["plugins"] = self.registry.ids()
        return snap

    def list_plugins(self) -> list[str]:
        return self.registry.ids()

    def _record_metric(self, path: Path, outcome: ParseOutcome, *, elapsed_ms: float) -> None:
        thr = 0.0
        if elapsed_ms > 0 and outcome.records:
            thr = len(outcome.records) / (elapsed_ms / 1000.0)
        self.metrics.record(
            ParseMetric(
                parser_id=outcome.parser_id,
                source_file=str(path),
                success=outcome.success,
                parse_time_ms=elapsed_ms,
                record_count=len(outcome.records),
                cache_hit=outcome.cache_hit,
                throughput_records_per_s=thr,
                error_count=len(outcome.errors),
            )
        )
