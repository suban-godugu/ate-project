import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_client import get_redis, prefix_key, publish_job_event, set_job_status
from app.core.database import get_db
from app.models.users import User
from app.schemas.common import AIDiagnosisResult, JobCreatedResponse, PrimaryActionResult
from app.services.deps import get_current_user
from app.workers.ai_worker import enqueue_ai_diagnosis, enqueue_primary_action

router = APIRouter(tags=["actions"])

PRIMARY_ACTIONS: dict[str, dict] = {
    "dashboard": {
        "label": "AI Optimize",
        "summary": "Optimization complete — projected savings identified across test patterns.",
        "metrics": [
            {"label": "Cost Reduction", "value": "12.4%"},
            {"label": "Time Savings", "value": "8.2 min/wafer"},
            {"label": "Projected Yield", "value": "95.1%"},
            {"label": "Total Savings", "value": "$284K"},
        ],
    },
    "scan-chain": {
        "label": "Run AI Diagnosis",
        "summary": "Scan chain diagnosis complete — root cause identified for critical chains.",
        "metrics": [
            {"label": "Critical Chains", "value": "12"},
            {"label": "Confidence", "value": "91.2%"},
            {"label": "Repair Success", "value": "87%"},
        ],
    },
}


@router.post("/actions/primary/{page_id}", response_model=JobCreatedResponse)
async def trigger_primary_action(page_id: str, user: User = Depends(get_current_user)):
    job_id = str(uuid.uuid4())
    await set_job_status(job_id, {"status": "queued", "percent": 0, "step": "init"})
    await enqueue_primary_action(job_id, page_id, str(user.id))
    return JobCreatedResponse(job_id=job_id)


@router.post("/ai-diagnosis/{module}", response_model=JobCreatedResponse)
async def trigger_ai_diagnosis(module: str, user: User = Depends(get_current_user)):
    job_id = str(uuid.uuid4())
    await set_job_status(job_id, {"status": "queued", "percent": 0, "step": "collect"})
    await enqueue_ai_diagnosis(job_id, module, str(user.id))
    return JobCreatedResponse(job_id=job_id)


@router.get("/actions/{job_id}/status")
async def action_status_stream(job_id: str):
    async def event_generator():
        redis = await get_redis()
        pubsub = redis.pubsub()
        channel = prefix_key(f"job:{job_id}:events")
        await pubsub.subscribe(channel)
        async for message in pubsub.listen():
            if message["type"] == "message":
                yield f"data: {message['data']}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
