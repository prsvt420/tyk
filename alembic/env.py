import asyncio
from logging.config import fileConfig

from sqlalchemy import MetaData, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    async_engine_from_config,
)

import src.infrastructure.database.models  # noqa: F401
from alembic import context
from alembic.config import Config
from src.config import app_settings
from src.infrastructure.database import Base

alembic_config: Config = context.config

database_url: str = app_settings.database_url

alembic_config.set_main_option(
    name="sqlalchemy.url",
    value=database_url.replace("%", "%%"),
)

alembic_config_file_name: str | None = alembic_config.config_file_name

if alembic_config_file_name is not None:
    fileConfig(fname=alembic_config_file_name)

database_metadata: MetaData = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without creating a database connection."""
    context.configure(
        url=database_url,
        target_metadata=database_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(sync_connection: Connection) -> None:
    """Run migrations using a synchronous database connection."""
    context.configure(
        connection=sync_connection,
        target_metadata=database_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using an asynchronous database engine."""
    sqlalchemy_config: dict[str, str] = (
        alembic_config.get_section(
            name=alembic_config.config_ini_section,
            default={},
        )
        or {}
    )
    async_engine: AsyncEngine = async_engine_from_config(
        configuration=sqlalchemy_config,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async_connection: AsyncConnection = async_engine.connect()
    async with async_connection:
        await async_connection.run_sync(fn=do_run_migrations)

    await async_engine.dispose()


def run_migrations_online() -> None:
    """Run migrations with an active database connection."""
    asyncio.run(main=run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
