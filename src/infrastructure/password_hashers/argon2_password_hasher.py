from pwdlib import PasswordHash

from src.application.interfaces import PasswordHasherInterface
from src.domain.value_objects import Password


class Argon2PasswordHasher(PasswordHasherInterface):
    """Argon2 password hasher."""

    def __init__(self) -> None:
        self._password_hash = PasswordHash.recommended()

    async def hash(self, password: Password) -> str:
        """Hash password."""
        return self._password_hash.hash(password=password.value)

    async def verify(self, password: str, hashed_password: str) -> bool:
        """Verify password."""
        return self._password_hash.verify(
            password=password, hash=hashed_password
        )
