import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        cols = (await db.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='parser_jobs' ORDER BY ordinal_position"
        ))).fetchall()
        print("parser_jobs cols:", [c[0] for c in cols])
        rows = (await db.execute(text(
            "SELECT id::text, upload_job_id::text, status::text, parser_id, "
            "left(coalesce(error_message,''),120) as err, unified_dataset_key, created_at "
            "FROM parser_jobs ORDER BY created_at DESC LIMIT 6"
        ))).fetchall()
        print("=== parser_jobs ===")
        for r in rows:
            print(dict(r._mapping))
        tables = (await db.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' AND ("
            "table_name ILIKE '%agent%' OR table_name ILIKE '%pattern%' OR "
            "table_name ILIKE '%failure%' OR table_name ILIKE '%scan%' OR "
            "table_name ILIKE '%orchestr%' OR table_name ILIKE '%result%' OR "
            "table_name ILIKE '%pipeline%')"
            " ORDER BY 1"
        ))).fetchall()
        print("related tables:", [t[0] for t in tables])
        stuck = (await db.execute(text(
            "SELECT id::text, file_name, status::text, created_at FROM upload_jobs "
            "WHERE status::text IN ('processing','parsing','uploading','queued') "
            "ORDER BY created_at DESC LIMIT 10"
        ))).fetchall()
        print("=== stuck uploads ===")
        for r in stuck:
            print(dict(r._mapping))

asyncio.run(main())
