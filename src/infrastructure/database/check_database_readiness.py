from asyncio import timeout

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.infrastructure.database.database_async_engine import (
    database_async_engine,
)


async def check_database_readiness() -> bool:
    """Check database readiness."""
    try:
        async with timeout(1.0):
            async with (
                database_async_engine.connect() as database_async_connection
            ):
                await database_async_connection.execute(
                    statement=text(text="SELECT 1")
                )
    except (SQLAlchemyError, TimeoutError):
        return False

    return True
