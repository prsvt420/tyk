from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.infrastructure.database.database_async_engine import (
    database_async_engine,
)

database_async_session_factory: async_sessionmaker[AsyncSession] = (
    async_sessionmaker(
        bind=database_async_engine,
        expire_on_commit=False,
    )
)
