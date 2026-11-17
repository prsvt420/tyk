from uuid import UUID

from asyncpg import UniqueViolationError
from sqlalchemy import ScalarResult, Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.exceptions import EmailAlreadyExistsError
from src.application.interfaces import UserRepositoryInterface
from src.domain.entities import User
from src.domain.value_objects import Email
from src.infrastructure.database.model_mappers import UserModelMapper
from src.infrastructure.database.models import UserModel


class PostgreSQLUserRepository(UserRepositoryInterface):
    """PostgreSQL user repository."""

    def __init__(self, database_async_session: AsyncSession) -> None:
        self._database_async_session: AsyncSession = database_async_session

    async def save(self, user: User) -> None:
        """Save user."""
        user_model: UserModel = UserModelMapper.to_model(user=user)

        try:
            async with self._database_async_session.begin():
                self._database_async_session.add(instance=user_model)
                await self._database_async_session.flush()
        except IntegrityError as error:
            original_error: BaseException | None = error.orig
            database_error: BaseException | None = (
                original_error.__cause__
                if original_error is not None
                else None
            )

            if (
                isinstance(database_error, UniqueViolationError)
                and database_error.constraint_name == "uq_users_email"
            ):
                raise EmailAlreadyExistsError() from error

            raise

    async def get_by_id(self, id: UUID) -> User | None:
        """Return user by id."""
        statement: Select[tuple[UserModel]] = select(UserModel).where(
            UserModel.id == id
        )

        return await self._get_by_statement(statement=statement)

    async def get_by_email(self, email: Email) -> User | None:
        """Return user by email."""
        statement: Select[tuple[UserModel]] = select(UserModel).where(
            UserModel.email == email.value
        )

        return await self._get_by_statement(statement=statement)

    async def _get_by_statement(
        self, statement: Select[tuple[UserModel]]
    ) -> User | None:
        """Return user by statement."""
        user_models: ScalarResult[UserModel] = (
            await self._database_async_session.scalars(statement=statement)
        )
        user_model: UserModel | None = user_models.one_or_none()

        if user_model is not None:
            return UserModelMapper.to_entity(user_model=user_model)
        return None
