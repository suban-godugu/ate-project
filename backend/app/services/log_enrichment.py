"""Apply ATE log parse results to upload jobs, summaries, and scan failures."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import ScanChainFailure
from app.models.uploads import UploadJob
from app.parsers.log_parser import LogParseResult, parse_log_file
from app.services.metadata_upsert import (
    get_or_create_fab,
    get_or_create_lot,
    get_or_create_product,
    get_or_create_tester,
    get_or_create_wafer,
)


async def apply_log_metadata(db: AsyncSession, job: UploadJob, parsed: LogParseResult) -> None:
    fab = await get_or_create_fab(db, parsed.tester_code)
    fab_id = fab.id if fab else job.fab_id
    tester = await get_or_create_tester(db, parsed.tester_code, fab_id=fab_id)
    product = await get_or_create_product(db, parsed.product_code)
    lot = await get_or_create_lot(
        db,
        parsed.lot_id,
        product_id=product.id if product else job.product_id,
        fab_id=fab_id,
    )
    wafer = await get_or_create_wafer(
        db,
        parsed.wafer_id,
        lot_id=lot.id if lot else job.lot_id,
        yield_pct=parsed.yield_pct,
    )
    if fab_id:
        job.fab_id = fab_id
    if tester:
        job.tester_id = tester.id
    if product:
        job.product_id = product.id
    if lot:
        job.lot_id = lot.id
    if wafer:
        job.wafer_id = wafer.id


def merge_log_into_summary_fields(summary_fields: dict, parsed: LogParseResult) -> dict:
    """Overlay cost-bearing LOG fields onto parser-derived summary fields."""
    merged = dict(summary_fields)
    if parsed.patterns_found is not None:
        merged["patterns_found"] = parsed.patterns_found
    if parsed.scan_chains is not None:
        merged["scan_chains"] = parsed.scan_chains
    if parsed.memory_blocks is not None:
        merged["memory_blocks"] = parsed.memory_blocks
    if parsed.logic_blocks is not None:
        merged["logic_blocks"] = parsed.logic_blocks
    if parsed.wafer_count is not None:
        merged["wafer_count"] = parsed.wafer_count
    if parsed.defects_found is not None:
        merged["defects_found"] = parsed.defects_found
    if parsed.yield_pct is not None:
        merged["yield_pct"] = parsed.yield_pct
    if parsed.estimated_cost is not None:
        merged["estimated_cost"] = parsed.estimated_cost
    if parsed.estimated_savings is not None:
        merged["estimated_savings"] = parsed.estimated_savings

    raw = dict(merged.get("raw_summary_json") or {})
    raw.update({"format": "log", **parsed.raw_fields})
    merged["raw_summary_json"] = raw
    return merged


async def persist_log_failures(
    db: AsyncSession, job: UploadJob, parsed: LogParseResult
) -> int:
    count = 0
    for failure in parsed.failures:
        db.add(
            ScanChainFailure(
                chain_id=failure.get("chain_id"),
                pattern_id=failure.get("pattern_id"),
                fail_cycle=failure.get("fail_cycle"),
                fail_type=failure.get("fail_type"),
                root_cause=failure.get("root_cause"),
                diagnosis_status="pending",
                lot_id=job.lot_id,
                wafer_id=job.wafer_id,
            )
        )
        count += 1
    if count:
        await db.flush()
    return count


def parse_log_files(work_files) -> LogParseResult | None:
    """Parse the first readable ATE log among uploaded work files."""
    merged: LogParseResult | None = None
    for path in work_files:
        if path.suffix.lower() not in {".log", ".txt"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        parsed = parse_log_file(text)
        if merged is None:
            merged = parsed
            continue
        # Accumulate failures; prefer explicit cost lines from any file.
        merged.failures.extend(parsed.failures)
        for field in (
            "estimated_cost",
            "estimated_savings",
            "patterns_found",
            "scan_chains",
            "memory_blocks",
            "logic_blocks",
            "wafer_count",
            "defects_found",
            "yield_pct",
            "lot_id",
            "wafer_id",
            "product_code",
            "tester_code",
        ):
            if getattr(merged, field) is None and getattr(parsed, field) is not None:
                setattr(merged, field, getattr(parsed, field))
    return merged
