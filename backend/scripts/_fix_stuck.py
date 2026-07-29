import asyncio
from datetime import UTC, datetime
from sqlalchemy import text
from arq import create_pool
from arq.connections import RedisSettings
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal

async def main():
    settings = get_settings()
    redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    async with AsyncSessionLocal() as db:
        stuck = (await db.execute(text(
            "SELECT id::text FROM upload_jobs WHERE status::text = 'processing'"
        ))).fetchall()
        for row in stuck:
            jid = row[0]
            has = (await db.execute(text(
                "SELECT 1 FROM diagnosis_results WHERE upload_job_id = :id::uuid AND status='completed' LIMIT 1"
            ), {"id": jid})).first()
            if has:
                await db.execute(text(
                    "UPDATE upload_jobs SET status='completed', completed_at=NOW(), error_message=NULL WHERE id=:id::uuid"
                ), {"id": jid})
                print("marked completed", jid)
            else:
                await redis.enqueue_job("orchestrate_agents", jid)
                print("re-enqueued orchestrate", jid)
        await db.commit()
    await redis.aclose()

asyncio.run(main())
