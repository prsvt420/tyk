from abc import ABC, abstractmethod

from src.domain.value_objects import Password


class PasswordHasherInterface(ABC):
    """Password hasher interface."""

    @abstractmethod
    async def hash(self, password: Password) -> str:
        """Hash password."""
        ...

    @abstractmethod
    async def verify(self, password: str, hashed_password: str) -> bool:
        """Verify password."""
        ...
