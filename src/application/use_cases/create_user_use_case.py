from logging import Logger, getLogger
from uuid import uuid4

from src.application.dtos import CreateUserDTO, UserDTO
from src.application.interfaces import (
    PasswordHasherInterface,
    UserRepositoryInterface,
)
from src.application.mappers import UserMapper
from src.domain.entities import User
from src.domain.value_objects import Email, Password

logger: Logger = getLogger(name=__name__)


class CreateUserUseCase:
    """Create user use case."""

    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        password_hasher: PasswordHasherInterface,
    ) -> None:
        self._user_repository: UserRepositoryInterface = user_repository
        self._password_hasher: PasswordHasherInterface = password_hasher

    async def execute(self, create_user_dto: CreateUserDTO) -> UserDTO:
        """Create user."""
        email: Email = Email(value=create_user_dto.email)
        password: str = await self._password_hasher.hash(
            password=Password(value=create_user_dto.password)
        )

        user: User = User(
            id=uuid4(),
            email=email,
            password=password,
        )

        await self._user_repository.save(user=user)

        logger.info(
            msg="User created.",
            extra={
                "event": "user_created",
                "user_id": str(user.id),
            },
        )

        return UserMapper.to_dto(user=user)
