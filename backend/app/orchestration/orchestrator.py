"""Agent Orchestrator — sole executor of Pattern / Failure / Scan Diagnosis agents."""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_client import cache_delete_pattern
from app.core.config import get_settings
from app.domain.pipeline_stages import PipelineStage
from app.models.pipeline import ParserJob, ParserJobStatus
from app.models.uploads import UploadJob, UploadStatus
from app.orchestration.agent_clients import (
    AgentClientError,
    FailureAgentClient,
    PatternAgentClient,
    ScanDiagnosisAgentClient,
)
from app.orchestration.aggregator import ResultAggregator
from app.orchestration.progress import fail_stage, mark_stage
from app.orchestration.retry import normalize_retry_stage
from app.repositories import pipeline_repo as repo
from app.services.recommendation_engine import RecommendationEngine
from app.services import artifact_store
from app.storage.minio_client import (
    build_diagnosis_artifact_key,
    build_failure_artifact_key,
    build_pattern_artifact_key,
    build_scan_chain_result_key,
    get_presigned_get_url,
    put_object_bytes,
)

log = logging.getLogger("verilumen.orchestrator")
settings = get_settings()


class AgentOrchestrator:
    def __init__(self) -> None:
        self.pattern = PatternAgentClient()
        self.failure = FailureAgentClient()
        self.scan = ScanDiagnosisAgentClient()
        self.aggregator = ResultAggregator()
        self.recommendations = RecommendationEngine()

    async def start(self, db: AsyncSession, upload_job_id: str, *, from_stage: str | None = None) -> dict[str, Any]:
        job = await db.get(UploadJob, uuid.UUID(upload_job_id))
        if job is None:
            return {"ok": False, "error": "upload_not_found"}

        parser = await db.scalar(
            select(ParserJob)
            .where(ParserJob.upload_job_id == job.id)
            .order_by(ParserJob.created_at.desc())
        )
        if parser is None or parser.status not in (
            ParserJobStatus.completed,
            ParserJobStatus.skipped_duplicate,
        ):
            await fail_stage(db, job, PipelineStage.running_pattern, "Parser job not completed")
            await db.commit()
            return {"ok": False, "error": "parser_incomplete"}

        dataset_key = parser.unified_dataset_key
        if not dataset_key:
            await fail_stage(db, job, PipelineStage.running_pattern, "Unified dataset missing")
            await db.commit()
            return {"ok": False, "error": "dataset_missing"}

        dataset_url = get_presigned_get_url(settings.minio_bucket_parsed, dataset_key, expires=7200)
        # Prefer local dataset path for agents (same host / shared FS); fall back to MinIO URL
        artifact_store.ensure_job_tree(upload_job_id)
        local_dataset = artifact_store.dataset_path(upload_job_id)
        dataset_path = str(local_dataset) if local_dataset.exists() else dataset_url

        stage = normalize_retry_stage(from_stage, parser.failed_stage)
        job.status = UploadStatus.processing
        job.error_message = None
        await db.flush()

        pattern_payload: dict[str, Any] | None = None
        failure_payload: dict[str, Any] | None = None

        base_req = {
            "job_id": upload_job_id,
            "upload_id": upload_job_id,
            "dataset_path": dataset_path,
            "dataset_uri": dataset_path,
            "dataset_sha256": parser.sha256 or job.checksum_sha256,
            "metadata": {
                "file_name": job.file_name,
                "module": job.module,
                "parser_id": parser.parser_id,
            },
            "callback_context": {"orchestrator_job_id": upload_job_id},
        }
        if settings.agent_fast_mode:
            # Skip Pattern Validate re-parse + FA Postgres dual-write (minutes → seconds).
            base_req["mode"] = "dataset_kpis"
            base_req["skip_ingest"] = True
            base_req["wait_for_modules"] = False
        artifact_store.append_log(
            upload_job_id,
            f"orchestrator start dataset_path={dataset_path} fast_mode={settings.agent_fast_mode}",
        )

        # Pattern + Failure in parallel (unless retrying from later stage)
        if stage in (PipelineStage.running_pattern, PipelineStage.running_failure):
            await mark_stage(db, job, PipelineStage.running_pattern, status="active")
            await mark_stage(db, job, PipelineStage.running_failure, status="active")
            await db.commit()

            pattern_payload, failure_payload = await self._run_pattern_and_failure(db, job, base_req)
            if pattern_payload is None or failure_payload is None:
                await db.commit()
                return {"ok": False, "error": "agent_parallel_failed"}

            await mark_stage(db, job, PipelineStage.running_pattern, status="done")
            await mark_stage(db, job, PipelineStage.running_failure, status="done")
            await db.commit()
        else:
            # Load prior results from DB for later-stage retry
            from app.models.pipeline import FailureResult, PatternResult

            pr_row = await db.scalar(select(PatternResult).where(PatternResult.upload_job_id == job.id))
            fr_row = await db.scalar(select(FailureResult).where(FailureResult.upload_job_id == job.id))
            pattern_payload = {
                "report": pr_row.report if pr_row else {},
                "kpis": pr_row.kpis if pr_row else {},
                "artifact_key": pr_row.artifact_key if pr_row else None,
            }
            failure_payload = {
                "report": fr_row.report if fr_row else {},
                "yield_report": fr_row.yield_report if fr_row else {},
                "kpis": fr_row.kpis if fr_row else {},
                "artifact_key": fr_row.artifact_key if fr_row else None,
            }

        # Ensure Scan Diagnosis live engine has STIL+LOG before agent run
        try:
            from app.services.scan_diagnosis_bridge import publish_job_to_scan_diagnosis

            pub = publish_job_to_scan_diagnosis(upload_job_id)
            artifact_store.append_log(
                upload_job_id,
                f"pre-scan publish stil={pub.get('stil_count')} logs={pub.get('log_count')}",
            )
            # Ask Scan agent to drop caches so live dashboard sees new files (non-blocking).
            # Heavy validate_live_path often exceeds 30s; do not stall the pipeline on it.
            try:
                import httpx

                reload_url = f"{settings.scan_diagnosis_agent_api_url.rstrip('/')}/api/v1/scan/reload-live"

                def _reload_live() -> None:
                    try:
                        httpx.post(
                            reload_url,
                            headers={"X-Verilumen-Service-Key": settings.verilumen_service_key},
                            timeout=5.0,
                        )
                    except Exception as reload_exc:  # noqa: BLE001
                        artifact_store.append_log(
                            upload_job_id,
                            f"scan reload-live (bg) failed: {reload_exc}",
                            level="WARN",
                        )

                asyncio.create_task(asyncio.to_thread(_reload_live))
                artifact_store.append_log(upload_job_id, "scan reload-live kicked off (background)")
            except Exception as reload_exc:  # noqa: BLE001
                artifact_store.append_log(
                    upload_job_id, f"scan reload-live schedule failed: {reload_exc}", level="WARN"
                )
        except Exception as pub_exc:  # noqa: BLE001
            artifact_store.append_log(upload_job_id, f"pre-scan publish failed: {pub_exc}", level="WARN")

        # Scan Diagnosis
        await mark_stage(db, job, PipelineStage.running_scan_diagnosis, status="active")
        await db.commit()
        diagnosis_payload = await self._run_scan(db, job, base_req, pattern_payload, failure_payload)
        if diagnosis_payload is None:
            await db.commit()
            return {"ok": False, "error": "scan_failed"}
        await mark_stage(db, job, PipelineStage.running_scan_diagnosis, status="done")

        # Aggregate + recommendations
        await mark_stage(db, job, PipelineStage.aggregating, status="active")
        merged = self.aggregator.merge(
            upload_id=upload_job_id,
            pattern=pattern_payload,
            failure=failure_payload,
            diagnosis=diagnosis_payload,
        )
        rec = self.recommendations.build(merged)
        merged["recommendations"] = rec["recommendations"]
        merged["recommendation_kpis"] = rec["kpis"]
        artifact_store.write_json(upload_job_id, "recommendation", "recommendations.json", rec)
        artifact_store.write_json(upload_job_id, "reports", "scan_chain_result.json", merged)
        artifact_store.append_log(upload_job_id, "recommendation engine completed")
        await mark_stage(db, job, PipelineStage.aggregating, status="done")

        await mark_stage(db, job, PipelineStage.saving, status="active")
        result_key = build_scan_chain_result_key(upload_job_id)
        put_object_bytes(
            settings.minio_bucket_parsed,
            result_key,
            json.dumps(merged, default=str).encode("utf-8"),
            content_type="application/json",
        )
        await repo.upsert_recommendation_result(
            db, job.id, status="completed", payload=rec, kpis=rec.get("kpis")
        )
        dash_payload = {
            "executive_kpis": {
                "record_ready": True,
                "upload_id": upload_job_id,
                "yield_pct": (failure_payload or {}).get("kpis", {}).get("yield_pct"),
                "diagnosis_confidence": diagnosis_payload.get("confidence"),
                "recommendation_count": rec["kpis"].get("recommendation_count"),
            },
            "pattern_kpis": (pattern_payload or {}).get("kpis"),
            "failure_kpis": (failure_payload or {}).get("kpis"),
            "diagnosis_kpis": diagnosis_payload.get("kpis"),
            "recommendation_kpis": rec.get("kpis"),
        }
        await repo.upsert_dashboard_metrics(
            db,
            job.id,
            executive_kpis=dash_payload["executive_kpis"],
            pattern_kpis=dash_payload["pattern_kpis"],
            failure_kpis=dash_payload["failure_kpis"],
            diagnosis_kpis=dash_payload["diagnosis_kpis"],
            recommendation_kpis=dash_payload["recommendation_kpis"],
        )
        artifact_store.write_json(upload_job_id, "dashboard", "kpis.json", dash_payload)
        await mark_stage(db, job, PipelineStage.saving, status="done")

        await mark_stage(db, job, PipelineStage.refreshing_dashboard, status="active")
        await cache_delete_pattern("dash:*")
        await mark_stage(db, job, PipelineStage.refreshing_dashboard, status="done")

        # Persist Scan + Wafer Cost Intelligence payloads to personal output root
        try:
            from app.schemas.common import GlobalFilters
            from app.services.cost_engine import build_cost_intelligence_payload

            empty = GlobalFilters()
            overview = await build_cost_intelligence_payload(db, "overview", empty)
            scan_cost = await build_cost_intelligence_payload(db, "scan-chain", empty)
            wafer_cost = await build_cost_intelligence_payload(db, "wafer", empty)
            artifact_store.save_cost_intelligence_artifacts(
                upload_job_id,
                overview=overview,
                scan_chain=scan_cost,
                wafer=wafer_cost,
                input_manifest={
                    "input_root": str(artifact_store.upload_input_job_dir(upload_job_id)),
                    "files": [p.name for p in artifact_store.list_job_input_files(upload_job_id)],
                    "output_root": str(artifact_store.job_root(upload_job_id) / "cost"),
                },
            )
            artifact_store.append_log(
                upload_job_id,
                "cost intelligence scan/wafer payloads written to agent and parser output",
            )
        except Exception as cost_exc:  # noqa: BLE001
            artifact_store.append_log(
                upload_job_id, f"cost intelligence artifact save failed: {cost_exc}", level="WARN"
            )

        job.status = UploadStatus.completed
        job.completed_at = datetime.now(UTC)
        parser.failed_stage = None
        await mark_stage(db, job, PipelineStage.completed, status="done", upload_status=UploadStatus.completed)
        await db.commit()
        return {"ok": True, "result_key": result_key, "merged": merged}

    async def _run_pattern_and_failure(
        self, db: AsyncSession, job: UploadJob, base_req: dict[str, Any]
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        # HTTP in parallel — never share one AsyncSession across concurrent tasks.
        pattern_exc: Exception | None = None
        failure_exc: Exception | None = None
        pattern_raw: dict[str, Any] | None = None
        failure_raw: dict[str, Any] | None = None

        async def _call_pattern() -> dict[str, Any]:
            return await self.pattern.consume(base_req)

        async def _call_failure() -> dict[str, Any]:
            return await self.failure.consume(base_req)

        results = await asyncio.gather(_call_pattern(), _call_failure(), return_exceptions=True)
        if isinstance(results[0], Exception):
            pattern_exc = results[0]
        else:
            pattern_raw = results[0]  # type: ignore[assignment]
        if isinstance(results[1], Exception):
            failure_exc = results[1]
        else:
            failure_raw = results[1]  # type: ignore[assignment]

        pattern_data: dict[str, Any] | None = None
        failure_data: dict[str, Any] | None = None

        if pattern_raw is not None:
            t0 = time.perf_counter()
            try:
                data = dict(pattern_raw)
                key = build_pattern_artifact_key(str(job.id))
                put_object_bytes(
                    settings.minio_bucket_parsed,
                    key,
                    json.dumps(data, default=str).encode("utf-8"),
                    content_type="application/json",
                )
                local_path = artifact_store.write_json(str(job.id), "pattern", "report.json", data)
                data["artifact_key"] = key
                data["local_path"] = str(local_path)
                artifact_store.append_log(str(job.id), f"pattern agent ok path={local_path}")
                await repo.upsert_pattern_result(
                    db,
                    job.id,
                    status="completed",
                    report=data.get("report") or data,
                    kpis=data.get("kpis") or {},
                    artifact_key=key,
                    agent_job_id=str(data.get("job_id") or ""),
                    completed_at=datetime.now(UTC),
                    error_message=None,
                )
                await repo.log_execution(
                    db,
                    job.id,
                    stage=PipelineStage.running_pattern,
                    agent="pattern",
                    status="ok",
                    latency_ms=(time.perf_counter() - t0) * 1000,
                )
                pattern_data = data
            except Exception as exc:  # noqa: BLE001
                pattern_exc = exc
                await repo.upsert_pattern_result(
                    db, job.id, status="failed", error_message=str(exc), completed_at=datetime.now(UTC)
                )
                await repo.log_execution(
                    db,
                    job.id,
                    stage=PipelineStage.running_pattern,
                    agent="pattern",
                    status="failed",
                    error_message=str(exc),
                )
        elif pattern_exc is not None:
            await repo.upsert_pattern_result(
                db, job.id, status="failed", error_message=str(pattern_exc), completed_at=datetime.now(UTC)
            )
            await repo.log_execution(
                db,
                job.id,
                stage=PipelineStage.running_pattern,
                agent="pattern",
                status="failed",
                error_message=str(pattern_exc),
            )

        if failure_raw is not None:
            t0 = time.perf_counter()
            try:
                data = dict(failure_raw)
                key = build_failure_artifact_key(str(job.id))
                put_object_bytes(
                    settings.minio_bucket_parsed,
                    key,
                    json.dumps(data, default=str).encode("utf-8"),
                    content_type="application/json",
                )
                local_path = artifact_store.write_json(str(job.id), "failure", "report.json", data)
                data["artifact_key"] = key
                data["local_path"] = str(local_path)
                artifact_store.append_log(str(job.id), f"failure agent ok path={local_path}")
                await repo.upsert_failure_result(
                    db,
                    job.id,
                    status="completed",
                    report=data.get("report") or data,
                    yield_report=data.get("yield_report"),
                    kpis=data.get("kpis") or {},
                    artifact_key=key,
                    agent_job_id=str(data.get("job_id") or ""),
                    completed_at=datetime.now(UTC),
                    error_message=None,
                )
                await repo.log_execution(
                    db,
                    job.id,
                    stage=PipelineStage.running_failure,
                    agent="failure",
                    status="ok",
                    latency_ms=(time.perf_counter() - t0) * 1000,
                )
                failure_data = data
            except Exception as exc:  # noqa: BLE001
                failure_exc = exc
                await repo.upsert_failure_result(
                    db, job.id, status="failed", error_message=str(exc), completed_at=datetime.now(UTC)
                )
                await repo.log_execution(
                    db,
                    job.id,
                    stage=PipelineStage.running_failure,
                    agent="failure",
                    status="failed",
                    error_message=str(exc),
                )
        elif failure_exc is not None:
            await repo.upsert_failure_result(
                db, job.id, status="failed", error_message=str(failure_exc), completed_at=datetime.now(UTC)
            )
            await repo.log_execution(
                db,
                job.id,
                stage=PipelineStage.running_failure,
                agent="failure",
                status="failed",
                error_message=str(failure_exc),
            )

        if pattern_exc is not None or failure_exc is not None:
            err = pattern_exc or failure_exc
            assert err is not None
            await fail_stage(db, job, PipelineStage.running_pattern, str(err))
            return None, None

        return pattern_data, failure_data

    async def _run_scan(
        self,
        db: AsyncSession,
        job: UploadJob,
        base_req: dict[str, Any],
        pattern_payload: dict[str, Any] | None,
        failure_payload: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        t0 = time.perf_counter()
        pattern_local = (pattern_payload or {}).get("local_path") or str(
            artifact_store.job_root(str(job.id)) / "pattern" / "report.json"
        )
        failure_local = (failure_payload or {}).get("local_path") or str(
            artifact_store.job_root(str(job.id)) / "failure" / "report.json"
        )
        payload = {
            **base_req,
            "pattern_result_path": pattern_local,
            "failure_result_path": failure_local,
            "pattern_result_uri": pattern_local,
            "failure_result_uri": failure_local,
        }
        try:
            data = await self.scan.consume(payload)
            latency = (time.perf_counter() - t0) * 1000
            key = build_diagnosis_artifact_key(str(job.id))
            put_object_bytes(
                settings.minio_bucket_parsed,
                key,
                json.dumps(data, default=str).encode("utf-8"),
                content_type="application/json",
            )
            local_path = artifact_store.write_json(str(job.id), "scan", "report.json", data)
            artifact_store.append_log(str(job.id), f"scan diagnosis ok path={local_path}")
            data = dict(data)
            data["artifact_key"] = key
            data["local_path"] = str(local_path)
            await repo.upsert_diagnosis_result(
                db,
                job.id,
                status="completed",
                report=data.get("report") or data,
                kpis=data.get("kpis") or {},
                recommendations=data.get("recommendations"),
                confidence=data.get("confidence"),
                artifact_key=key,
                agent_job_id=str(data.get("job_id") or ""),
                completed_at=datetime.now(UTC),
                error_message=None,
            )
            await repo.log_execution(
                db,
                job.id,
                stage=PipelineStage.running_scan_diagnosis,
                agent="scan_diagnosis",
                status="ok",
                latency_ms=latency,
            )
            return data
        except (AgentClientError, Exception) as exc:  # noqa: BLE001
            await repo.upsert_diagnosis_result(
                db, job.id, status="failed", error_message=str(exc), completed_at=datetime.now(UTC)
            )
            await repo.log_execution(
                db,
                job.id,
                stage=PipelineStage.running_scan_diagnosis,
                agent="scan_diagnosis",
                status="failed",
                error_message=str(exc),
            )
            await fail_stage(db, job, PipelineStage.running_scan_diagnosis, str(exc))
            return None
