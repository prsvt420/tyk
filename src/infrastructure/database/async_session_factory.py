from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.infrastructure.database.async_engine import async_engine

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
)
