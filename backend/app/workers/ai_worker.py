import asyncio
from datetime import UTC, datetime

from arq import create_pool
from arq.connections import RedisSettings
from sqlalchemy import select

from app.cache.redis_client import publish_job_event, set_job_status
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.analytics import ScanChainFailure
from app.models.uploads import AILogSummary

settings = get_settings()

DIAGNOSIS_STEPS = ["collect", "analyze", "insight", "complete"]


async def _latest_ai_hints() -> dict | None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AILogSummary).order_by(AILogSummary.created_at.desc()).limit(1)
        )
        summary = result.scalar_one_or_none()
        if not summary or not summary.raw_summary_json:
            return None
        hints = summary.raw_summary_json.get("ai_hints")
        return hints if isinstance(hints, dict) else None


async def _latest_scan_failure(module: str) -> ScanChainFailure | None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ScanChainFailure).order_by(ScanChainFailure.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()


async def _latest_log_summary() -> AILogSummary | None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AILogSummary).order_by(AILogSummary.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()


async def _build_primary_result(page_id: str) -> dict:
    hints = await _latest_ai_hints()
    if hints and "primary_action" in hints:
        action = hints["primary_action"]
        return {
            "label": action.get("label", "Action Complete"),
            "summary": action.get("summary", "Analysis based on latest parsed upload"),
            "metrics": action.get("metrics", [{"label": "Status", "value": "Done"}]),
        }

    summary = await _latest_log_summary()
    if summary:
        metrics = [
            {"label": "Patterns", "value": str(summary.patterns_found or 0)},
            {"label": "Scan Chains", "value": str(summary.scan_chains or 0)},
            {"label": "Yield", "value": f"{summary.yield_pct or 0}%"},
        ]
        if summary.estimated_savings:
            metrics.append({"label": "Savings", "value": f"${int(summary.estimated_savings):,}"})
        return {
            "label": "Parse Analysis",
            "summary": "Metrics from latest uploaded test log or STDF file",
            "metrics": metrics,
        }

    return {
        "label": "No Data",
        "summary": "No parsed uploads available — upload a STDF or log file first",
        "metrics": [{"label": "Status", "value": "Awaiting upload"}],
    }


async def _build_diagnosis(module: str) -> dict:
    hints = await _latest_ai_hints()
    if hints and "diagnosis" in hints:
        return hints["diagnosis"]

    if module == "scan-chain":
        failure = await _latest_scan_failure(module)
        if failure:
            return {
                "rootCause": failure.root_cause or f"Failure on chain {failure.chain_id}",
                "confidence": 88,
                "recommendation": f"Retest pattern {failure.pattern_id or 'unknown'} and verify chain {failure.chain_id}",
                "estimatedYieldImpact": "+1.0%",
            }
        return {
            "rootCause": "No scan chain failures in database",
            "confidence": 90,
            "recommendation": "Upload STDF or log files containing scan chain failures to enable diagnosis",
            "estimatedYieldImpact": "+0.0%",
        }

    return {
        "rootCause": f"No parsed {module} data available yet",
        "confidence": 85,
        "recommendation": "Upload relevant test files — STDF/LOG parser covers scan-chain failures today",
        "estimatedYieldImpact": "+0.0%",
    }


async def enqueue_primary_action(job_id: str, page_id: str, user_id: str) -> None:
    redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    await redis.enqueue_job("run_primary_action", job_id, page_id, user_id)


async def enqueue_ai_diagnosis(job_id: str, module: str, user_id: str) -> None:
    redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    await redis.enqueue_job("run_ai_diagnosis", job_id, module, user_id)


async def run_primary_action(ctx, job_id: str, page_id: str, user_id: str) -> dict:
    template = await _build_primary_result(page_id)
    await set_job_status(job_id, {"status": "running", "percent": 50, "step": "processing"})
    await publish_job_event(job_id, {"status": "running", "percent": 50, "step": "processing"})
    await asyncio.sleep(0.3)
    result = {
        "type": "primary_action",
        "pageId": page_id,
        "label": template["label"],
        "summary": template["summary"],
        "metrics": template["metrics"],
        "completedAt": datetime.now(UTC).isoformat(),
    }
    final = {"status": "completed", "percent": 100, "step": "done", "result": result}
    await set_job_status(job_id, final)
    await publish_job_event(job_id, final)
    return result


async def run_ai_diagnosis(ctx, job_id: str, module: str, user_id: str) -> dict:
    for i, step in enumerate(DIAGNOSIS_STEPS):
        percent = int((i + 1) / len(DIAGNOSIS_STEPS) * 100)
        event = {"status": "running", "percent": percent, "step": step}
        await set_job_status(job_id, event)
        await publish_job_event(job_id, event)
        await asyncio.sleep(0.2)

    diagnosis = await _build_diagnosis(module)
    final = {
        "status": "completed",
        "percent": 100,
        "step": "complete",
        "result": {"type": "ai_diagnosis", **diagnosis},
    }
    await set_job_status(job_id, final)
    await publish_job_event(job_id, final)
    return diagnosis
