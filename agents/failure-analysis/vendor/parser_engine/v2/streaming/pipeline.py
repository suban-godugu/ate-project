"""Streaming parse pipeline helpers."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Iterable

from parser_engine.v2.contracts import ParseContext, ParseOutcome
from parser_engine.v2.models.enterprise_record import EnterpriseRecord


def batch_records(records: Iterable[EnterpriseRecord], batch_size: int = 1000) -> Iterable[list[EnterpriseRecord]]:
    batch: list[EnterpriseRecord] = []
    for rec in records:
        batch.append(rec)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def parse_paths_parallel(
    paths: list[Path],
    parse_fn: Callable[[Path], ParseOutcome],
    *,
    max_workers: int | None = None,
) -> list[ParseOutcome]:
    """Process-pool multi-file parse (CPU-bound)."""
    if not paths:
        return []
    if len(paths) == 1:
        return [parse_fn(paths[0])]
    outcomes: list[ParseOutcome] = []
    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        futs = {pool.submit(parse_fn, p): p for p in paths}
        for fut in as_completed(futs):
            try:
                outcomes.append(fut.result())
            except Exception as exc:  # noqa: BLE001
                p = futs[fut]
                from parser_engine.v2.contracts import Issue

                outcomes.append(
                    ParseOutcome(
                        parser_id="parallel",
                        errors=[Issue(code="PARALLEL_FAIL", message=f"{p}: {exc}")],
                        success=False,
                        metadata={"source_file": str(p)},
                    )
                )
    return outcomes


def apply_resume(ctx: ParseContext, *, line: int | None = None, offset: int | None = None) -> ParseContext:
    if line is not None:
        ctx.resume_line = line
    if offset is not None:
        ctx.resume_offset = offset
    return ctx
