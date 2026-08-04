"""Parser pipeline — sole raw-file reader via ParserEngineV2."""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
import tempfile
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from arq import create_pool
from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.domain.pipeline_stages import PipelineStage
from app.domain.unified_dataset import UnifiedDataset, UnifiedDatasetRecord, from_enterprise_record
from app.models.pipeline import ParserJobStatus
from app.models.uploads import UploadJob, UploadStatus
from app.orchestration.progress import fail_stage, mark_stage
from app.repositories import pipeline_repo as repo
from app.storage.minio_client import get_object_bytes, put_object_bytes

log = logging.getLogger("verilumen.parser_pipeline")
settings = get_settings()

ALLOWED_EXTENSIONS = {
    ".stdf",
    ".std",
    ".atdf",
    ".atd",
    ".stil",
    ".wgl",
    ".log",
    ".csv",
    ".txt",
    ".json",
    ".xml",
    ".dat",
    ".vcd",
    ".evcd",
    ".zip",
}


def build_unified_dataset_key(upload_job_id: str) -> str:
    return f"{upload_job_id}/unified_dataset.json"


def _ensure_parser_engine_on_path() -> None:
    import sys

    root = Path(settings.parser_engine_path)
    if root.exists() and str(root) not in sys.path:
        sys.path.insert(0, str(root))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _extract_zip(zip_path: Path, dest: Path) -> list[Path]:
    members: list[Path] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = Path(info.filename).name
            ext = Path(name).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS or ext == ".zip":
                continue
            target = dest / name
            with zf.open(info) as src, target.open("wb") as out:
                shutil.copyfileobj(src, out)
            members.append(target)
    return members


async def enqueue_orchestrate(upload_job_id: str) -> None:
    redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    await redis.enqueue_job("orchestrate_agents", upload_job_id)


class ParserPipelineService:
    """Download → detect/validate/parse/normalize via ParserEngineV2 → store → enqueue agents."""

    async def run(self, db: AsyncSession, job: UploadJob) -> dict[str, Any]:
        _ensure_parser_engine_on_path()
        from parser_engine.v2 import ParseContext, ParserEngineV2

        upload_id = str(job.id)
        t0 = time.perf_counter()
        await mark_stage(db, job, PipelineStage.validating, status="active", upload_status=UploadStatus.parsing)

        raw = get_object_bytes(job.minio_bucket, job.minio_object_key)
        if settings.max_upload_bytes and len(raw) > settings.max_upload_bytes:
            await fail_stage(db, job, PipelineStage.validating, f"File exceeds max size {settings.max_upload_bytes}")
            await db.commit()
            return {"ok": False, "error": "FILE_TOO_LARGE"}

        sha = _sha256_bytes(raw)
        job.checksum_sha256 = sha
        await mark_stage(db, job, PipelineStage.validating, status="done")

        dup = await repo.find_duplicate_by_sha256(db, sha, job.id)
        parser_job = await repo.create_parser_job(db, job.id, sha256=sha, status=ParserJobStatus.running)

        if dup and dup.unified_dataset_key:
            parser_job.status = ParserJobStatus.skipped_duplicate
            parser_job.duplicate_of = dup.id
            parser_job.unified_dataset_key = dup.unified_dataset_key
            parser_job.parser_id = dup.parser_id
            parser_job.confidence = dup.confidence
            parser_job.completed_at = datetime.now(UTC)
            # Reuse prior dataset key; still need local normalized rows? Link by copying key only.
            # Materialize local dataset so agents on this host can use a file path.
            try:
                from app.services import artifact_store

                artifact_store.ensure_job_tree(upload_id)
                payload = get_object_bytes(settings.minio_bucket_parsed, dup.unified_dataset_key)
                artifact_store.write_bytes(upload_id, "parser", "unified_dataset.json", payload)
                # Still save the uploaded original into the shared input folder
                artifact_store.save_upload_files_to_input_root(
                    upload_id,
                    original_name=job.file_name or "upload.bin",
                    original_bytes=raw,
                    work_files=None,
                )
                artifact_store.append_log(
                    upload_id,
                    f"parser skipped_duplicate reused_key={dup.unified_dataset_key}",
                )
            except Exception as exc:  # noqa: BLE001
                log.warning("duplicate_local_dataset_failed", extra={"structured_extra": {"error": str(exc)}})
            job.status = UploadStatus.processing
            await mark_stage(db, job, PipelineStage.detecting_format, status="done")
            await mark_stage(db, job, PipelineStage.parsing, status="done")
            await mark_stage(db, job, PipelineStage.generating_metadata, status="done")
            await mark_stage(db, job, PipelineStage.normalizing, status="done")
            await db.commit()
            await enqueue_orchestrate(upload_id)
            return {"ok": True, "duplicate": True, "parser_job_id": str(parser_job.id)}

        with tempfile.TemporaryDirectory(prefix="verilumen_parse_") as tmp:
            tmp_path = Path(tmp)
            original_name = job.file_name or "upload.bin"
            original_path = tmp_path / Path(original_name).name
            original_path.write_bytes(raw)
            # Free the in-memory copy ASAP — free/Starter Render is only 512MB and
            # API + ARQ share the same instance (OOM killed 17MB+ STIL parses).
            del raw
            import gc

            gc.collect()

            ext = original_path.suffix.lower()
            if ext and ext not in ALLOWED_EXTENSIONS:
                await fail_stage(db, job, PipelineStage.validating, f"Extension not allowed: {ext}")
                parser_job.status = ParserJobStatus.failed
                parser_job.error_message = f"EXT_BLOCKED:{ext}"
                parser_job.failed_stage = PipelineStage.validating
                await db.commit()
                return {"ok": False, "error": "EXT_BLOCKED"}

            work_files: list[Path]
            if ext == ".zip":
                extract_dir = tmp_path / "extracted"
                extract_dir.mkdir()
                work_files = _extract_zip(original_path, extract_dir)
                if not work_files:
                    await fail_stage(db, job, PipelineStage.parsing, "ZIP contained no supported files")
                    parser_job.status = ParserJobStatus.failed
                    parser_job.error_message = "ZIP_EMPTY"
                    parser_job.failed_stage = PipelineStage.parsing
                    await db.commit()
                    return {"ok": False, "error": "ZIP_EMPTY"}
            else:
                work_files = [original_path]

            # Always mirror uploads to C:\personal\input all file\<job_id>\
            try:
                from app.services import artifact_store as _astore

                _astore.save_upload_files_to_input_root(
                    upload_id,
                    original_name=original_name,
                    original_path=original_path,
                    work_files=work_files,
                )
            except Exception as mirror_exc:  # noqa: BLE001
                log.warning(
                    "upload_input_mirror_failed",
                    extra={"structured_extra": {"error": str(mirror_exc)}},
                )

            await mark_stage(db, job, PipelineStage.detecting_format, status="active")
            engine = ParserEngineV2()
            all_records: list[UnifiedDatasetRecord] = []
            primary_parser_id: str | None = None
            primary_confidence: float | None = None
            vendor: str | None = None
            quarantine_total = 0
            error_total = 0

            for path in work_files:
                file_sha = _sha256_file(path)
                pf = await repo.create_parsed_file(
                    db,
                    parser_job_id=parser_job.id,
                    upload_job_id=job.id,
                    file_name=path.name,
                    file_type=path.suffix.lower().lstrip(".") or None,
                    size_bytes=path.stat().st_size,
                    sha256=file_sha,
                    status="parsing",
                )
                detections = engine.detect(path)
                top = detections[0] if detections else None
                if top:
                    primary_parser_id = primary_parser_id or top.parser_id
                    primary_confidence = top.confidence
                    vendor = top.vendor

                await mark_stage(db, job, PipelineStage.detecting_format, status="done")
                await mark_stage(db, job, PipelineStage.parsing, status="active")

                # Mixed ZIP uploads (STIL + ATE logs) need per-file profiles.
                # Use diagnosis for STIL too: full "auto/failure" STIL ingest scans the
                # entire pattern body and OOMs on Render free 512MB (API+worker colocated).
                suffix = path.suffix.lower()
                log_like = suffix in {".log", ".txt"}
                stil_like = suffix in {".stil", ".stil.gz"}
                if job.kind.value == "log" or log_like or stil_like:
                    profile = "diagnosis"
                else:
                    profile = "auto"
                ctx = ParseContext(profile=profile, max_size_bytes=settings.max_upload_bytes, enable_cache=False)
                outcome = engine.parse(path, ctx=ctx, use_cache=False)

                if not outcome.success and not outcome.records:
                    err = "; ".join(f"{e.code}:{e.message}" for e in outcome.errors) or "PARSE_FAILED"
                    pf.status = "failed"
                    pf.error_message = err
                    error_total += 1
                    # Stub parsers (WGL/ATDF/VCD) — fail clear, do not orchestrate if nothing parsed
                    continue

                pf.parser_id = outcome.parser_id
                pf.status = "completed"
                primary_parser_id = outcome.parser_id or primary_parser_id
                quarantine_total += len(outcome.quarantine)

                await mark_stage(db, job, PipelineStage.generating_metadata, status="active")
                await mark_stage(db, job, PipelineStage.generating_metadata, status="done")
                await mark_stage(db, job, PipelineStage.normalizing, status="active")

                mapped = [
                    from_enterprise_record(r, upload_id=upload_id, file_id=str(pf.id)).model_dump()
                    for r in outcome.records
                ]
                await repo.bulk_insert_normalized(db, job.id, parser_job.id, mapped, parsed_file_id=pf.id)
                all_records.extend(UnifiedDatasetRecord.model_validate(m) for m in mapped)
                # Drop parse buffers before the next large file (log + stil).
                del outcome, mapped
                gc.collect()

            if not all_records:
                from app.services.log_enrichment import parse_log_files

                log_fallback = parse_log_files(work_files)
                if log_fallback is not None and (
                    log_fallback.estimated_cost is not None
                    or log_fallback.failures
                    or log_fallback.patterns_found
                ):
                    # LOG-only cost path: synthesize unified records from FAIL lines
                    for i, fail in enumerate(log_fallback.failures or []):
                        all_records.append(
                            UnifiedDatasetRecord(
                                upload_id=upload_id,
                                file_id="",
                                lot_id=log_fallback.lot_id or "",
                                wafer_id=log_fallback.wafer_id or "",
                                pattern=str(fail.get("pattern_id") or ""),
                                scan_chain=str(fail.get("chain_id") or ""),
                                pass_fail="FAIL",
                                test_name=str(fail.get("root_cause") or "")[:200],
                                metadata={
                                    "fail_type": fail.get("fail_type"),
                                    "fail_cycle": fail.get("fail_cycle"),
                                    "source": "log_parser",
                                },
                                parser_id="ate-log",
                                source_file=job.file_name or "",
                            )
                        )
                    if not all_records:
                        # Cost-bearing LOG with no FAIL lines — keep a placeholder PASS record
                        all_records.append(
                            UnifiedDatasetRecord(
                                upload_id=upload_id,
                                lot_id=log_fallback.lot_id or "",
                                wafer_id=log_fallback.wafer_id or "",
                                pass_fail="PASS",
                                pattern="",
                                scan_chain="",
                                metadata={"source": "log_parser", "cost_only": True},
                                parser_id="ate-log",
                                source_file=job.file_name or "",
                            )
                        )
                    primary_parser_id = primary_parser_id or "ate-log"
                    vendor = vendor or "ate-log"
                else:
                    msg = "No records produced by Parser Engine (stub or empty parse)"
                    await fail_stage(db, job, PipelineStage.parsing, msg)
                    parser_job.status = ParserJobStatus.failed
                    parser_job.error_message = msg
                    parser_job.failed_stage = PipelineStage.parsing
                    parser_job.parser_id = primary_parser_id
                    await db.commit()
                    return {"ok": False, "error": "NO_RECORDS"}

            await mark_stage(db, job, PipelineStage.parsing, status="done")
            await mark_stage(db, job, PipelineStage.normalizing, status="done")

            dataset = UnifiedDataset(
                upload_id=upload_id,
                record_count=len(all_records),
                records=all_records,
                metadata={
                    "parser_id": primary_parser_id,
                    "vendor": vendor,
                    "sha256": sha,
                    "file_name": job.file_name,
                },
            )
            dataset_key = build_unified_dataset_key(upload_id)
            dataset_bytes = dataset.model_dump_json().encode("utf-8")
            put_object_bytes(
                settings.minio_bucket_parsed,
                dataset_key,
                dataset_bytes,
                content_type="application/json",
            )

            # Local audit tree: C:\personal\agent and parser output\<job_id>\parser\
            # INPUTS stay only under C:\personal\input all file\<job_id>\
            from app.services import artifact_store

            artifact_store.ensure_job_tree(upload_id)
            input_dir = artifact_store.upload_input_job_dir(upload_id)
            stil_files: list[str] = []
            log_files: list[str] = []
            for path in artifact_store.list_job_input_files(upload_id):
                suf = path.suffix.lower()
                if suf == ".stil":
                    stil_files.append(path.name)
                elif suf in {".log", ".txt"}:
                    log_files.append(path.name)
            # Fallback classify from work_files names if input root not yet populated
            if not stil_files and not log_files:
                for path in work_files:
                    suf = path.suffix.lower()
                    if suf == ".stil":
                        stil_files.append(path.name)
                    elif suf in {".log", ".txt"}:
                        log_files.append(path.name)
            artifact_store.write_json(
                upload_id,
                "parser",
                "inputs_manifest.json",
                {
                    "input_root": str(input_dir),
                    "stil_files": stil_files,
                    "log_files": log_files,
                    "all_files": [p.name for p in work_files],
                },
            )
            artifact_store.append_log(
                upload_id,
                f"parser inputs catalogued stil={len(stil_files)} logs={len(log_files)} dir={input_dir}",
            )

            # Bridge: hardlink/symlink into Scan live dirs (no second byte-store of inputs)
            try:
                from app.services.scan_diagnosis_bridge import publish_job_to_scan_diagnosis

                publish_job_to_scan_diagnosis(upload_id)
            except Exception as bridge_exc:  # noqa: BLE001
                log.warning(
                    "scan_diagnosis_bridge_failed",
                    extra={"structured_extra": {"upload_id": upload_id, "error": str(bridge_exc)}},
                )

            local_dataset = artifact_store.write_json(
                upload_id, "parser", "unified_dataset.json", dataset.model_dump()
            )
            artifact_store.write_json(
                upload_id,
                "parser",
                "metadata.json",
                {
                    "parser_id": primary_parser_id,
                    "vendor": vendor,
                    "sha256": sha,
                    "record_count": len(all_records),
                    "minio_key": dataset_key,
                    "local_dataset_path": str(local_dataset),
                },
            )
            artifact_store.append_log(
                upload_id,
                f"parser completed parser_id={primary_parser_id} records={len(all_records)} path={local_dataset}",
            )

            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            thr = (len(all_records) / (elapsed_ms / 1000.0)) if elapsed_ms > 0 else 0.0
            await repo.save_statistics(
                db,
                parser_job.id,
                parse_time_ms=elapsed_ms,
                record_count=len(all_records),
                quarantine_count=quarantine_total,
                throughput_records_per_s=thr,
                cache_hit=False,
                error_count=error_total,
                extras={"vendor": vendor},
            )

            parser_job.status = ParserJobStatus.completed
            parser_job.parser_id = primary_parser_id
            parser_job.confidence = primary_confidence
            parser_job.vendor = vendor
            parser_job.unified_dataset_key = dataset_key
            parser_job.completed_at = datetime.now(UTC)

            # Compatibility summary for existing dashboard AI summary endpoint
            from app.models.analytics import ScanChainFailure
            from app.models.uploads import AILogSummary
            from app.services.log_enrichment import (
                apply_log_metadata,
                merge_log_into_summary_fields,
                parse_log_files,
                persist_log_failures,
            )
            from sqlalchemy import select as sa_select

            fails = sum(1 for r in all_records if str(r.pass_fail).upper() == "FAIL")
            passes = sum(1 for r in all_records if str(r.pass_fail).upper() == "PASS")
            total = max(fails + passes, 1)
            chains = {r.scan_chain for r in all_records if r.scan_chain}
            patterns = {r.pattern for r in all_records if r.pattern}
            existing_summary = await db.scalar(
                sa_select(AILogSummary).where(AILogSummary.upload_job_id == job.id)
            )
            summary_fields = {
                "files_processed": len(work_files),
                "patterns_found": len(patterns),
                "scan_chains": len(chains),
                "defects_found": fails,
                "yield_pct": round(100.0 * passes / total, 2),
                "raw_summary_json": {
                    "parser_id": primary_parser_id,
                    "record_count": len(all_records),
                    "unified_dataset_key": dataset_key,
                },
            }

            log_result = parse_log_files(work_files)
            if log_result is not None:
                await apply_log_metadata(db, job, log_result)
                summary_fields = merge_log_into_summary_fields(summary_fields, log_result)
                await persist_log_failures(db, job, log_result)

            for record in all_records:
                if str(record.pass_fail).upper() != "FAIL":
                    continue
                if not record.scan_chain and not record.pattern:
                    continue
                db.add(
                    ScanChainFailure(
                        chain_id=record.scan_chain or None,
                        pattern_id=record.pattern or None,
                        chip=record.die_id or None,
                        fail_type=str(record.metadata.get("fail_type") or "parsed"),
                        root_cause=record.test_name or None,
                        diagnosis_status="pending",
                        lot_id=job.lot_id,
                        wafer_id=job.wafer_id,
                    )
                )

            if existing_summary:
                for k, v in summary_fields.items():
                    setattr(existing_summary, k, v)
                summary_row = existing_summary
            else:
                summary_row = AILogSummary(upload_job_id=job.id, **summary_fields)
                db.add(summary_row)

            job.status = UploadStatus.processing
            job.processing_ms = int(elapsed_ms)
            await db.flush()

            if summary_fields.get("estimated_cost"):
                from app.services.cost_engine import evaluate_cost_alerts

                await evaluate_cost_alerts(db, upload_id)

            # Persist Cost Intelligence inputs/outputs under personal I/O roots:
            #   INPUT  → C:\personal\input all file\<job_id>\
            #   OUTPUT → C:\personal\agent and parser output\<job_id>\cost\
            try:
                input_dir = artifact_store.upload_input_job_dir(upload_id)
                input_files = [p.name for p in artifact_store.list_job_input_files(upload_id)]
                # Include original + any work files mirrored for audit.
                if input_dir.exists():
                    input_files = sorted(
                        {
                            *input_files,
                            *[p.name for p in input_dir.iterdir() if p.is_file()],
                        }
                    )
                cost_summary = {
                    "upload_job_id": upload_id,
                    "estimated_cost": summary_fields.get("estimated_cost"),
                    "estimated_savings": summary_fields.get("estimated_savings"),
                    "patterns_found": summary_fields.get("patterns_found"),
                    "scan_chains": summary_fields.get("scan_chains"),
                    "memory_blocks": summary_fields.get("memory_blocks"),
                    "logic_blocks": summary_fields.get("logic_blocks"),
                    "wafer_count": summary_fields.get("wafer_count"),
                    "defects_found": summary_fields.get("defects_found"),
                    "yield_pct": summary_fields.get("yield_pct"),
                    "lot_id": str(job.lot_id) if job.lot_id else None,
                    "wafer_id": str(job.wafer_id) if job.wafer_id else None,
                    "product_id": str(job.product_id) if job.product_id else None,
                    "raw_summary_json": summary_fields.get("raw_summary_json"),
                    "log_failures": (log_result.failures if log_result is not None else []),
                }
                # Build live Scan/Wafer cost payloads while summary is flushed.
                from app.schemas.common import GlobalFilters
                from app.services.cost_engine import build_cost_intelligence_payload

                empty = GlobalFilters()
                overview_payload = await build_cost_intelligence_payload(db, "overview", empty)
                scan_payload = await build_cost_intelligence_payload(db, "scan-chain", empty)
                wafer_payload = await build_cost_intelligence_payload(db, "wafer", empty)
                artifact_store.save_cost_intelligence_artifacts(
                    upload_id,
                    summary=cost_summary,
                    overview=overview_payload,
                    scan_chain=scan_payload,
                    wafer=wafer_payload,
                    input_manifest={
                        "input_root": str(input_dir),
                        "files": input_files,
                        "output_root": str(artifact_store.job_root(upload_id) / "cost"),
                    },
                )
            except Exception as cost_io_exc:  # noqa: BLE001
                log.warning(
                    "cost_artifact_save_failed",
                    extra={"structured_extra": {"upload_id": upload_id, "error": str(cost_io_exc)}},
                )

            await db.commit()

            await enqueue_orchestrate(upload_id)
            log.info(
                "parser_pipeline_complete",
                extra={
                    "structured_extra": {
                        "upload_id": upload_id,
                        "records": len(all_records),
                        "parser_id": primary_parser_id,
                    }
                },
            )
            return {
                "ok": True,
                "parser_job_id": str(parser_job.id),
                "record_count": len(all_records),
                "unified_dataset_key": dataset_key,
            }
