from asyncio import timeout

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.infrastructure.database.async_engine import async_engine


async def check_database_readiness() -> bool:
    """Check database readiness."""
    try:
        async with timeout(1.0):
            async with async_engine.connect() as async_connection:
                await async_connection.execute(statement=text(text="SELECT 1"))
    except (SQLAlchemyError, TimeoutError):
        return False

    return True
