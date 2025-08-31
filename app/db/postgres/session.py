from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from app.core.config import config

ASYNC_POSTGRES_URL = (
    f"postgresql+asyncpg://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@"
    f"{config.POSTGRES_HOST}:{config.POSTGRES_PORT}/{config.POSTGRES_DB}"
)
SYNC_POSTGRES_URL = (
    f"postgresql://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@" f"{config.POSTGRES_HOST}:{config.POSTGRES_PORT}/{config.POSTGRES_DB}"
)

# NOTE: parameters should be considered for production
async_engine = create_async_engine(
    ASYNC_POSTGRES_URL,
    pool_size=5,
    max_overflow=20,
    pool_timeout=60,
    pool_recycle=3600,
    echo=False,
    echo_pool=False,
    future=True,
)
sync_engine = create_engine(
    SYNC_POSTGRES_URL,
    pool_size=5,
    max_overflow=20,
    pool_timeout=60,
    pool_recycle=3600,
    echo=False,
    echo_pool=False,
    future=True,
)

# Session factory
async_session = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
sync_session = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


async def check_db_connection(db: AsyncSession) -> bool:
    """
    Check database connection
    """
    try:
        # Execute a simple query
        await db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


# default session is async
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get a database session"""
    async with async_session() as db:
        try:
            yield db
        finally:
            await db.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as db:
        try:
            yield db
        finally:
            await db.close()


@contextmanager
def get_sync_db_session():
    db = sync_session()
    try:
        yield db
    finally:
        db.close()
