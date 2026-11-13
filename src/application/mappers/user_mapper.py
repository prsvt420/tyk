from src.application.dtos import UserDTO
from src.domain.entities import User


class UserMapper:
    """User mapper."""

    @staticmethod
    def to_dto(user: User) -> UserDTO:
        """Map user to DTO."""
        return UserDTO(
            id=user.id,
            email=user.email.value,
            password=user.password,
            is_active=user.is_active,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
            deleted_at=user.deleted_at,
        )
