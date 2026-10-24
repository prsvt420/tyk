from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.config import app_settings

database_async_engine: AsyncEngine = create_async_engine(
    url=app_settings.database_url
)
