from src.domain.entities import User
from src.domain.value_objects import Email
from src.infrastructure.database.models import UserModel


class UserModelMapper:
    """User model mapper."""

    @staticmethod
    def to_model(user: User) -> UserModel:
        """Map user to model."""
        return UserModel(
            id=user.id,
            email=user.email.value,
            password=user.password,
            is_active=user.is_active,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
            deleted_at=user.deleted_at,
        )

    @staticmethod
    def to_entity(user_model: UserModel) -> User:
        """Map user model to entity."""
        return User(
            id=user_model.id,
            email=Email(value=user_model.email),
            password=user_model.password,
            is_active=user_model.is_active,
            last_login_at=user_model.last_login_at,
            created_at=user_model.created_at,
            updated_at=user_model.updated_at,
            deleted_at=user_model.deleted_at,
        )
