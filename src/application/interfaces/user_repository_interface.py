from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities import User
from src.domain.value_objects import Email


class UserRepositoryInterface(ABC):
    """User repository interface."""

    @abstractmethod
    async def save(self, user: User) -> None:
        """Save user."""
        ...

    @abstractmethod
    async def get_by_id(self, id: UUID) -> User | None:
        """Return user by id."""
        ...

    @abstractmethod
    async def get_by_email(self, email: Email) -> User | None:
        """Return user by email."""
        ...
