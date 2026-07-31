from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import app_settings
from src.infrastructure.database.models import ShortLinkModel

TEST_DATABASE_NAME_PREFIX: str = "tyk_test_"


@pytest.fixture(scope="session")
async def postgresql_database_url() -> AsyncGenerator[str]:
    """Create and remove an isolated PostgreSQL database."""
    app_database_url: URL = make_url(name_or_url=app_settings.database_url)
    database_name: str = f"{TEST_DATABASE_NAME_PREFIX}{uuid4().hex}"
    admin_database_url: URL = app_database_url.set(database="postgres")
    test_database_url: URL = app_database_url.set(database=database_name)
    admin_async_engine: AsyncEngine = create_async_engine(
        url=admin_database_url,
        isolation_level="AUTOCOMMIT",
        connect_args={"ssl": False},
    )
    quoted_database_name: str = (
        admin_async_engine.dialect.identifier_preparer.quote(
            ident=database_name
        )
    )
    database_created: bool = False

    try:
        async with admin_async_engine.connect() as async_connection:
            await async_connection.execute(
                statement=text(text=f"CREATE DATABASE {quoted_database_name}")
            )
        database_created = True

        yield test_database_url.render_as_string(hide_password=False)
    finally:
        if database_created:
            async with admin_async_engine.connect() as async_connection:
                await async_connection.execute(
                    statement=text(
                        text=(
                            f"DROP DATABASE {quoted_database_name} "
                            "WITH (FORCE)"
                        )
                    )
                )

        await admin_async_engine.dispose()


@pytest.fixture
async def postgresql_async_session(
    postgresql_database_url: str,
) -> AsyncGenerator[AsyncSession]:
    """Provide a session with a fresh short links schema."""
    async_engine: AsyncEngine = create_async_engine(
        url=postgresql_database_url,
        connect_args={"ssl": False},
    )

    async with async_engine.begin() as async_connection:
        await async_connection.run_sync(fn=ShortLinkModel.metadata.create_all)

    async_session_factory: async_sessionmaker[AsyncSession] = (
        async_sessionmaker(
            bind=async_engine,
            expire_on_commit=False,
        )
    )

    try:
        async with async_session_factory() as async_session:
            yield async_session
    finally:
        async with async_engine.begin() as async_connection:
            await async_connection.run_sync(
                fn=ShortLinkModel.metadata.drop_all
            )

        await async_engine.dispose()
