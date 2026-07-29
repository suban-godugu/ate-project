"""ARQ worker: consume RL training jobs and update recommendation confidence from feedback."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from arq import create_pool
from arq.connections import RedisSettings
from sqlalchemy import select

from app.cache.redis_client import cache_delete_pattern, get_redis, prefix_key
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.recommendations import Recommendation, RecommendationFeedback, RecommendationTrainingRun
from app.services.audit_service import write_audit_log
from app.services.rl_feedback_consumer import (
    aggregate_feedback,
    confidence_target_from_aggregate,
    priority_from_confidence,
    update_confidence_wma,
)

settings = get_settings()
logger = logging.getLogger(__name__)

RL_QUEUE_STREAM = "rl_training"


async def publish_rl_training_event(recommendation_id: str, feedback_id: str | None, action: str) -> None:
    client = await get_redis()
    await client.xadd(
        prefix_key(RL_QUEUE_STREAM),
        {
            "recommendation_id": recommendation_id,
            "feedback_id": feedback_id or "",
            "action": action,
        },
        maxlen=5000,
    )


async def enqueue_rl_training(recommendation_id: str, feedback_id: str | None, action: str = "feedback") -> None:
    await publish_rl_training_event(recommendation_id, feedback_id, action)
    redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    await redis.enqueue_job("train_recommendation", recommendation_id, feedback_id)


async def invalidate_recommendation_caches() -> None:
    await cache_delete_pattern("dash:recommendation*")
    await cache_delete_pattern("dash:recommendation-analysis*")
    await cache_delete_pattern("recommendations:*")


async def train_recommendation(_ctx, recommendation_id: str, feedback_id: str | None = None) -> dict:
    """Process feedback for one recommendation and update confidence / ranking fields."""
    run_id = str(uuid.uuid4())
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Recommendation).where(Recommendation.id == uuid.UUID(recommendation_id))
            )
            rec = result.scalar_one_or_none()
            if not rec:
                return {"error": "not_found"}

            await write_audit_log(
                db,
                user_id=None,
                action="rl_training_started",
                entity_type="recommendation",
                entity_id=recommendation_id,
                meta={"training_run": run_id, "feedback_id": feedback_id},
            )

            fb_result = await db.execute(
                select(RecommendationFeedback)
                .where(RecommendationFeedback.recommendation_id == rec.id)
                .order_by(RecommendationFeedback.created_at.asc())
            )
            feedback_rows = fb_result.scalars().all()
            pairs = [(f.action_taken, float(f.reward_value) if f.reward_value is not None else None) for f in feedback_rows]
            agg = aggregate_feedback(pairs)

            confidence_before = float(rec.confidence) if rec.confidence is not None else None
            target = confidence_target_from_aggregate(agg)
            confidence_after = update_confidence_wma(confidence_before, target)

            rec.confidence = confidence_after
            rec.priority = priority_from_confidence(confidence_after)
            rec.reward_score = agg.reward_avg
            rec.approval_rate = agg.approval_rate
            rec.rejection_rate = agg.rejection_rate
            rec.application_rate = agg.application_rate
            rec.feedback_count = agg.total
            rec.last_trained_at = datetime.now(UTC)

            db.add(
                RecommendationTrainingRun(
                    id=uuid.uuid4(),
                    recommendation_id=rec.id,
                    training_run=run_id,
                    reward=agg.reward_avg,
                    confidence_before=confidence_before,
                    confidence_after=confidence_after,
                    feedback_count=agg.total,
                )
            )

            await write_audit_log(
                db,
                user_id=None,
                action="rl_training_completed",
                entity_type="recommendation",
                entity_id=recommendation_id,
                meta={
                    "training_run": run_id,
                    "confidence_before": confidence_before,
                    "confidence_after": confidence_after,
                    "reward_avg": agg.reward_avg,
                    "feedback_count": agg.total,
                },
            )
            await db.commit()

        await invalidate_recommendation_caches()
        logger.info("RL training completed for %s run=%s", recommendation_id, run_id)
        return {"ok": True, "training_run": run_id, "confidence_after": confidence_after}

    except Exception as exc:
        logger.exception("RL training failed for %s", recommendation_id)
        async with AsyncSessionLocal() as db:
            await write_audit_log(
                db,
                user_id=None,
                action="rl_training_failed",
                entity_type="recommendation",
                entity_id=recommendation_id,
                meta={"training_run": run_id, "error": str(exc)},
            )
            await db.commit()
        raise


train_recommendation.max_tries = 3
