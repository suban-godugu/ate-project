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
                SELECT id::text, status::text, file_name,
                       left(coalesce(error_message, ''), 160) AS err
                FROM upload_jobs
                ORDER BY created_at DESC NULLS LAST
                LIMIT 5
                """
            )
        )
        for row in rows:
            print(row)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
