from datetime import datetime, timezone
from uuid import UUID

import pytest

from src.application.dtos import UserDTO
from src.application.mappers import UserMapper
from src.domain.entities import User
from src.domain.value_objects import Email

STORED_HASH: str = "test-hash"


@pytest.mark.parametrize(argnames="is_active", argvalues=[False, True])
@pytest.mark.parametrize(
    argnames=("last_login_at", "deleted_at"),
    argvalues=[
        (None, None),
        (datetime(year=2030, month=1, day=2, tzinfo=timezone.utc), None),
        (None, datetime(year=2030, month=1, day=3, tzinfo=timezone.utc)),
        (
            datetime(year=2030, month=1, day=2, tzinfo=timezone.utc),
            datetime(year=2030, month=1, day=3, tzinfo=timezone.utc),
        ),
    ],
)
def test_user_mapper_maps_entity_to_dto(
    is_active: bool,
    last_login_at: datetime | None,
    deleted_at: datetime | None,
) -> None:
    """Map stored user data and optional dates without changing the entity."""
    user: User = User(
        id=UUID(hex="4f4c2514-26b0-4c75-a77b-130e7858024e"),
        email=Email(value="User@EXAMPLE.COM"),
        password=STORED_HASH,
        is_active=is_active,
        last_login_at=last_login_at,
        created_at=datetime(year=2030, month=1, day=1, tzinfo=timezone.utc),
        updated_at=datetime(year=2030, month=1, day=4, tzinfo=timezone.utc),
        deleted_at=deleted_at,
    )
    original_email: Email = user.email

    user_dto: UserDTO = UserMapper.to_dto(user=user)

    assert user_dto == UserDTO(
        id=user.id,
        email="User@example.com",
        password=STORED_HASH,
        is_active=is_active,
        last_login_at=last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        deleted_at=deleted_at,
    )
    assert user.email is original_email
    assert user.last_login_at == last_login_at
    assert user.deleted_at == deleted_at
