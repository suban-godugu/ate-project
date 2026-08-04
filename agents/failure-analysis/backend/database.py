"""Async SQLAlchemy PostgreSQL session factory and initialization."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

import sqlalchemy
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from backend.settings import DatabaseConfigurationError, get_settings

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Application-level database connectivity or initialization failure."""


class Base(DeclarativeBase):
    pass


def _map_driver_error(exc: BaseException) -> DatabaseError:
    message = str(exc).lower()
    name = type(exc).__name__

    if "password authentication failed" in message or "invalidpassword" in message:
        return DatabaseError(
            "PostgreSQL authentication failed. Verify DATABASE_USER and DATABASE_PASSWORD."
        )
    if "does not exist" in message and "database" in message:
        return DatabaseError(
            "Database not found. Expected existing database 'failure_analysis_db'. "
            "Do not create a new database — update DATABASE_NAME if using a different name."
        )
    if "connection refused" in message or "could not connect" in message:
        return DatabaseError(
            "Cannot reach PostgreSQL. Confirm the server is running on the configured "
            "DATABASE_HOST and DATABASE_PORT."
        )
    if "timeout" in message:
        return DatabaseError(
            "PostgreSQL connection timed out. Check network, host, port, and pool settings."
        )
    if "too many clients" in message or "remaining connection slots" in message:
        return DatabaseError(
            "PostgreSQL connection pool exhausted. Reduce concurrent load or increase "
            "max_connections / pool sizing."
        )
    if "role" in message and "does not exist" in message:
        return DatabaseError(
            "PostgreSQL role (user) does not exist. Verify DATABASE_USER."
        )
    return DatabaseError(
        f"PostgreSQL connection error ({name}). Check DATABASE_* settings in .env. "
        f"Details: {exc}"
    )


def create_engine() -> AsyncEngine:
    """Create the async SQLAlchemy engine for PostgreSQL (asyncpg)."""
    settings = get_settings()
    url = settings.resolved_database_url()

    if "sqlite" in url.lower():
        raise DatabaseConfigurationError(
            "SQLite URLs are rejected. This application uses PostgreSQL exclusively."
        )

    connect_args: dict = {}
    # asyncpg + Render: ensure TLS even if URL omitted ssl=
    if "render.com" in url and "ssl=" not in url:
        connect_args["ssl"] = True

    try:
        return create_async_engine(
            url,
            echo=False,
            future=True,
            pool_size=min(settings.db_pool_size, 5),
            max_overflow=min(settings.db_max_overflow, 5),
            pool_timeout=settings.db_pool_timeout,
            pool_recycle=settings.db_pool_recycle,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
    except DatabaseConfigurationError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _map_driver_error(exc) from None


# Lazy placeholders — real engine created in lifespan via rebind_engine().
engine: AsyncEngine | None = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None


def rebind_engine() -> AsyncEngine:
    """
    Recreate the global async engine / session factory.

    Required after ``dispose_engine`` (e.g. multiple TestClient lifecycles in one
    process) because asyncpg connections are bound to a specific event loop.
    """
    global engine, SessionLocal
    engine = create_engine()
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return engine


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an async session and closes it afterwards."""
    if SessionLocal is None:
        rebind_engine()
    assert SessionLocal is not None
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def validate_connection() -> None:
    """Verify credentials, host/port reachability, and pool health."""
    settings = get_settings()
    settings.assert_credentials_ready()
    if engine is None:
        rebind_engine()
    assert engine is not None
    logger.info("Database Type      : PostgreSQL")
    logger.info("Database Host      : %s", settings.database_host)
    logger.info("Database Port      : %s", settings.database_port)
    logger.info("Database Name      : %s", settings.database_name)
    logger.info("Database User      : %s", settings.database_user)
    logger.info("SQLAlchemy Version : %s", sqlalchemy.__version__)
    logger.info("Database URL       : %s", settings.safe_database_url())

    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.scalar_one()
            server_version = await conn.execute(text("SHOW server_version"))
            version = server_version.scalar_one()
        logger.info("Connection Status  : PostgreSQL Connected (server %s)", version)
    except DatabaseError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _map_driver_error(exc) from None


async def init_db() -> None:
    """
    Validate PostgreSQL availability and ensure ORM metadata tables exist.

    Uses ``create_all`` for bootstrap compatibility; Alembic remains the source
    of truth for future schema evolution (see ``alembic/``).
    """
    from backend import models  # noqa: F401 — register models on Base.metadata

    if engine is None:
        rebind_engine()
    assert engine is not None

    try:
        await validate_connection()
    except DatabaseError:
        # Pool may have been disposed by a prior app lifespan / test client.
        rebind_engine()
        await validate_connection()

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # Confirm schema objects are visible
            table_count = await conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = 'public'"
                )
            )
            count = table_count.scalar_one()
        logger.info("Schema Status      : Tables Created/Verified (%s public tables)", count)
        logger.info("Initialization     : Database Initialized")
        logger.info("Migration Status   : metadata.create_all + Alembic ready")
    except DatabaseError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise DatabaseError(
            f"Schema initialization failed. Details: {exc}"
        ) from None


async def dispose_engine() -> None:
    """Dispose the connection pool on application shutdown."""
    global engine, SessionLocal
    if engine is not None:
        await engine.dispose()
    engine = None
    SessionLocal = None
    logger.info("Connection Pool    : disposed")
