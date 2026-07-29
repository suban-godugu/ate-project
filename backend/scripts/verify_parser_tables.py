import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import get_settings


async def main() -> None:
    engine = create_async_engine(get_settings().database_url)
    async with engine.connect() as conn:
        row = await conn.execute(
            text(
                "SELECT to_regclass('public.parser_jobs'), "
                "to_regclass('public.parsed_files'), "
                "to_regclass('public.normalized_records')"
            )
        )
        print("tables:", row.fetchone())
        ver = await conn.execute(text("SELECT version_num FROM alembic_version"))
        print("alembic:", ver.scalar())
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
