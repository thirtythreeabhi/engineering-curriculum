"""Asynchronous database connection pool and session factory."""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.models import Base

DEFAULT_DB_URL = "sqlite+aiosqlite:///test_inventory.db"


class DatabaseManager:
    def __init__(self, db_url: str = DEFAULT_DB_URL):
        self.db_url = db_url
        self._write_lock = asyncio.Lock()

        engine_kwargs = {"echo": False}
        if "sqlite" in db_url:
            pass
        else:
            # PostgreSQL / asyncpg connection pool parameters
            engine_kwargs.update({
                "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
                "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
                "pool_timeout": 30.0,
                "pool_recycle": 1800,
                "pool_pre_ping": True,
            })

        self.engine: AsyncEngine = create_async_engine(db_url, **engine_kwargs)
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    async def init_schema(self) -> None:
        async with self.engine.begin() as conn:
            if "sqlite" in self.db_url:
                await conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
                await conn.exec_driver_sql("PRAGMA busy_timeout=10000;")
            await conn.run_sync(Base.metadata.create_all)

    async def drop_schema(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def close(self) -> None:
        await self.engine.dispose()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provides an async session context manager."""
        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
