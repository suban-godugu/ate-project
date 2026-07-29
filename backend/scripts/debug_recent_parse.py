import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import get_settings


async def main() -> None:
    engine = create_async_engine(get_settings().database_url)
    async with engine.connect() as conn:
        rows = await conn.execute(
            text(
                """
                SELECT id::text, status::text, file_name, file_type,
                       left(coalesce(error_message,''), 200) AS err,
                       minio_object_key, module
                FROM upload_jobs
                ORDER BY created_at DESC NULLS LAST
                LIMIT 8
                """
            )
        )
        for row in rows:
            print(row)
        print("--- parser_jobs ---")
        rows2 = await conn.execute(
            text(
                """
                SELECT id::text, upload_job_id::text, status::text, parser_id,
                       left(coalesce(error_message,''), 160) AS err,
                       failed_stage
                FROM parser_jobs
                ORDER BY created_at DESC NULLS LAST
                LIMIT 8
                """
            )
        )
        for row in rows2:
            print(row)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
