from abc import ABC, abstractmethod


class PasswordHasherInterface(ABC):
    """Password hasher interface."""

    @abstractmethod
    async def hash(self, password: str) -> str:
        """Hash password."""
        ...

    @abstractmethod
    async def verify(self, password: str, hashed_password: str) -> bool:
        """Verify password."""
        ...
