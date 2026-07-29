import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_client import (
    cache_delete_pattern,
    cache_set,
    get_unread_notification_count,
    invalidate_unread_notification_count,
    set_unread_notification_count,
)
from app.core.database import get_db
from app.models.analytics import Notification
from app.models.recommendations import Recommendation, RecommendationFeedback, RecommendationTrainingRun
from app.models.uploads import UploadJob
from app.models.users import User
from app.schemas.common import NotificationOut, RecommendationFeedbackRequest
from app.services.rl_feedback_consumer import compute_reward_value
from app.services.audit_service import write_audit_log
from app.services.deps import format_relative_time, get_current_user
from app.workers.rl_training_worker import enqueue_rl_training

router = APIRouter(tags=["notifications"])
rec_router = APIRouter(prefix="/recommendations", tags=["recommendations"])
export_router = APIRouter(prefix="/export", tags=["export"])


@router.get("/notifications", response_model=list[NotificationOut])
async def list_notifications(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cached_count = await get_unread_notification_count(str(user.id))
    result = await db.execute(
        select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(50)
    )
    rows = result.scalars().all()
    unread = sum(1 for n in rows if not n.read)
    if cached_count is None or cached_count != unread:
        await set_unread_notification_count(str(user.id), unread)
    return [
        NotificationOut(
            id=str(n.id),
            title=n.title or "",
            message=n.message or "",
            severity=n.severity or "info",
            read=n.read,
            timestamp=format_relative_time(n.created_at),
            alertRoute=n.alert_route,
        )
        for n in rows
    ]


@router.patch("/notifications/read-all")
async def mark_all_read(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(update(Notification).where(Notification.user_id == user.id).values(read=True))
    await cache_delete_pattern("notif:*")
    await invalidate_unread_notification_count(str(user.id))
    return {"ok": True}


@router.patch("/notifications/{notification_id}/read")
async def mark_read(
    notification_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification).where(Notification.id == uuid.UUID(notification_id), Notification.user_id == user.id)
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.read = True
    await invalidate_unread_notification_count(str(user.id))
    return {"ok": True}


@rec_router.post("/{recommendation_id}/feedback")
async def recommendation_feedback(
    recommendation_id: str,
    body: RecommendationFeedbackRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Recommendation).where(Recommendation.id == uuid.UUID(recommendation_id)))
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    reward = compute_reward_value(body.action_taken, body.outcome_value)
    action_l = body.action_taken.lower()
    if action_l in ("approved", "approve"):
        rec.status = "approved"
    elif action_l == "applied":
        rec.status = "applied"
    elif action_l == "rejected":
        rec.status = "rejected"
    feedback = RecommendationFeedback(
        recommendation_id=rec.id,
        agent_type=rec.agent_type or "pattern",
        action_taken=body.action_taken,
        outcome_metric=body.outcome_metric,
        outcome_value=body.outcome_value,
        reward_value=reward,
        model_version="v1",
    )
    db.add(feedback)
    await db.flush()
    await write_audit_log(
        db,
        user_id=user.id,
        action="recommendation_feedback",
        entity_type="recommendation",
        entity_id=recommendation_id,
        meta={"action_taken": body.action_taken, "reward_value": reward},
    )
    await enqueue_rl_training(recommendation_id, str(feedback.id), body.action_taken)
    await cache_delete_pattern("dash:recommendation*")
    await cache_delete_pattern("recommendations:*")
    return {"ok": True, "reward_value": reward, "feedback_id": str(feedback.id)}


@rec_router.get("/{recommendation_id}/metrics")
async def recommendation_metrics(
    recommendation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Recommendation).where(Recommendation.id == uuid.UUID(recommendation_id)))
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    fb_result = await db.execute(
        select(RecommendationFeedback)
        .where(RecommendationFeedback.recommendation_id == rec.id)
        .order_by(RecommendationFeedback.created_at.desc())
        .limit(100)
    )
    feedback_rows = fb_result.scalars().all()

    run_result = await db.execute(
        select(RecommendationTrainingRun)
        .where(RecommendationTrainingRun.recommendation_id == rec.id)
        .order_by(RecommendationTrainingRun.processed_at.desc())
        .limit(20)
    )
    training_runs = run_result.scalars().all()

    confidence_change = None
    if training_runs:
        latest = training_runs[0]
        if latest.confidence_before is not None and latest.confidence_after is not None:
            confidence_change = round(float(latest.confidence_after) - float(latest.confidence_before), 2)

    trend = [
        {
            "training_run": t.training_run,
            "confidence": float(t.confidence_after) if t.confidence_after is not None else None,
            "reward": float(t.reward) if t.reward is not None else None,
            "feedback_count": t.feedback_count,
            "processed_at": t.processed_at.isoformat() if t.processed_at else None,
        }
        for t in reversed(training_runs)
    ]

    return {
        "recommendation_id": recommendation_id,
        "confidence": float(rec.confidence or 0),
        "confidence_change": confidence_change,
        "reward_score": float(rec.reward_score or 0),
        "approval_rate": float(rec.approval_rate or 0),
        "rejection_rate": float(rec.rejection_rate or 0),
        "application_rate": float(rec.application_rate or 0),
        "feedback_count": int(rec.feedback_count or 0),
        "last_trained_at": rec.last_trained_at.isoformat() if rec.last_trained_at else None,
        "trend": trend,
        "feedback_history": [
            {
                "id": str(f.id),
                "action_taken": f.action_taken,
                "reward_value": float(f.reward_value) if f.reward_value is not None else None,
                "outcome_metric": f.outcome_metric,
                "outcome_value": float(f.outcome_value) if f.outcome_value is not None else None,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in feedback_rows
        ],
    }


@rec_router.get("/training-data")
async def recommendation_training_data(
    agent_type: str = Query(..., min_length=1),
    limit: int = Query(500, ge=1, le=5000),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reward-labeled feedback rows for offline RL / bandit training pipelines."""
    result = await db.execute(
        select(RecommendationFeedback)
        .where(RecommendationFeedback.agent_type == agent_type)
        .where(RecommendationFeedback.reward_value.isnot(None))
        .order_by(RecommendationFeedback.created_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "recommendation_id": str(r.recommendation_id),
            "agent_type": r.agent_type,
            "action_taken": r.action_taken,
            "outcome_metric": r.outcome_metric,
            "outcome_value": float(r.outcome_value) if r.outcome_value is not None else None,
            "reward_value": float(r.reward_value) if r.reward_value is not None else None,
            "model_version": r.model_version,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@export_router.post("/pdf")
async def export_pdf(body: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from datetime import UTC, datetime
    from io import BytesIO

    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    title = body.get("title", "Report")
    lines = body.get("lines", [])
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setTitle(title)
    y = 750
    c.drawString(50, y, title)
    y -= 30
    c.drawString(50, y, f"Generated: {datetime.now(UTC).isoformat()}")
    y -= 30
    for line in lines:
        c.drawString(50, y, str(line)[:100])
        y -= 20
        if y < 50:
            c.showPage()
            y = 750
    c.save()
    pdf_bytes = buffer.getvalue()

    from app.core.config import get_settings
    from app.storage.minio_client import build_export_key, get_presigned_get_url, put_object_bytes

    settings = get_settings()
    now = datetime.now(UTC)
    export_id = str(uuid.uuid4())
    key = build_export_key(str(user.id), export_id, now.year, now.month)
    put_object_bytes(settings.minio_bucket_exports, key, pdf_bytes, "application/pdf")
    url = get_presigned_get_url(settings.minio_bucket_exports, key)
    await write_audit_log(
        db,
        user_id=user.id,
        action="export_pdf",
        entity_type="export",
        entity_id=export_id,
        meta={"title": title},
    )
    await db.commit()
    return {"url": url}
