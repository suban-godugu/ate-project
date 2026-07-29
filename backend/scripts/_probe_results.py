import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        for tbl in ["pattern_results","failure_results","diagnosis_results","recommendation_results"]:
            rows = (await db.execute(text(
                f"SELECT upload_job_id::text, status, created_at FROM {tbl} ORDER BY created_at DESC LIMIT 3"
            ))).fetchall()
            print(tbl, [dict(r._mapping) for r in rows])

asyncio.run(main())
