from asyncpg import UniqueViolationError
from sqlalchemy import ScalarResult, Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.exceptions import ShortCodeAlreadyExistsError
from src.application.interfaces import ShortLinkRepositoryInterface
from src.domain.entities import ShortLink
from src.domain.value_objects import ShortCode
from src.infrastructure.database.model_mappers import ShortLinkModelMapper
from src.infrastructure.database.models import ShortLinkModel


class PostgreSQLShortLinkRepository(ShortLinkRepositoryInterface):
    """PostgreSQL short link repository."""

    def __init__(self, async_session: AsyncSession) -> None:
        self._async_session: AsyncSession = async_session

    async def save(self, short_link: ShortLink) -> None:
        """Save short link."""
        short_link_model: ShortLinkModel = ShortLinkModelMapper.to_model(
            short_link=short_link
        )

        try:
            async with self._async_session.begin():
                self._async_session.add(instance=short_link_model)
                await self._async_session.flush()
        except IntegrityError as error:
            original_error: BaseException | None = error.orig
            database_error: BaseException | None = (
                original_error.__cause__
                if original_error is not None
                else None
            )

            if (
                isinstance(database_error, UniqueViolationError)
                and database_error.constraint_name
                == "uq_short_links_short_code"
            ):
                raise ShortCodeAlreadyExistsError() from error

            raise

    async def get_by_short_code(
        self, short_code: ShortCode
    ) -> ShortLink | None:
        """Return short link by short code."""
        statement: Select[tuple[ShortLinkModel]] = select(
            ShortLinkModel
        ).where(ShortLinkModel.short_code == short_code.value)

        short_link_models: ScalarResult[ShortLinkModel] = (
            await self._async_session.scalars(statement=statement)
        )
        short_link_model: ShortLinkModel | None = (
            short_link_models.one_or_none()
        )

        if short_link_model is not None:
            return ShortLinkModelMapper.to_entity(
                short_link_model=short_link_model
            )
        return None
