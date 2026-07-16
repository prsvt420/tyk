from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.config import application_settings

async_engine: AsyncEngine = create_async_engine(
    url=application_settings.database_url
)
