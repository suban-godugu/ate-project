from arq.connections import RedisSettings

from app.core.config import get_settings
from app.workers.ai_worker import run_ai_diagnosis, run_primary_action
from app.workers.heartbeat import record_worker_heartbeat, worker_heartbeat_loop
from app.workers.orchestrator_worker import orchestrate_agents
from app.workers.parse_worker import parse_upload
from app.workers.rl_training_worker import train_recommendation

settings = get_settings()


async def on_worker_startup(ctx):
    await record_worker_heartbeat()
    import asyncio

    asyncio.create_task(worker_heartbeat_loop(30))


class WorkerSettings:
    functions = [
        parse_upload,
        orchestrate_agents,
        run_primary_action,
        run_ai_diagnosis,
        train_recommendation,
    ]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 10
    job_timeout = 1800
    on_startup = on_worker_startup
