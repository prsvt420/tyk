from datetime import datetime, timezone
from uuid import UUID

import pytest

from src.domain.entities import User
from src.domain.exceptions import InvalidEmailError
from src.domain.value_objects import Email
from src.infrastructure.database.model_mappers import UserModelMapper
from src.infrastructure.database.models import UserModel

USER_ID: UUID = UUID(hex="4f4c2514-26b0-4c75-a77b-130e7858024e")
STORED_HASH: str = "stored-test-hash"
CREATED_AT: datetime = datetime(year=2030, month=1, day=1, tzinfo=timezone.utc)
UPDATED_AT: datetime = datetime(year=2030, month=1, day=4, tzinfo=timezone.utc)


@pytest.mark.parametrize(argnames="is_active", argvalues=[False, True])
@pytest.mark.parametrize(
    argnames="last_login_at", argvalues=[None, CREATED_AT]
)
@pytest.mark.parametrize(argnames="deleted_at", argvalues=[None, UPDATED_AT])
def test_user_model_mapper_maps_entity_and_model(
    is_active: bool,
    last_login_at: datetime | None,
    deleted_at: datetime | None,
) -> None:
    """Preserve all stored fields and optional dates in both directions."""
    user: User = User(
        id=USER_ID,
        email=Email(value="User@example.com"),
        password=STORED_HASH,
        is_active=is_active,
        last_login_at=last_login_at,
        created_at=CREATED_AT,
        updated_at=UPDATED_AT,
        deleted_at=deleted_at,
    )

    model: UserModel = UserModelMapper.to_model(user=user)
    restored: User = UserModelMapper.to_entity(user_model=model)

    assert model.id == USER_ID
    assert model.email == "User@example.com"
    assert model.password == STORED_HASH
    assert model.is_active is is_active
    assert model.last_login_at == last_login_at
    assert model.created_at == CREATED_AT
    assert model.updated_at == UPDATED_AT
    assert model.deleted_at == deleted_at
    assert restored == user
    assert restored is not user


def test_user_model_mapper_validates_stored_email() -> None:
    """Apply domain validation when restoring a database model."""
    model: UserModel = UserModel(
        id=USER_ID,
        email="invalid",
        password=STORED_HASH,
        is_active=True,
        last_login_at=None,
        created_at=CREATED_AT,
        updated_at=UPDATED_AT,
        deleted_at=None,
    )

    with pytest.raises(expected_exception=InvalidEmailError):
        UserModelMapper.to_entity(user_model=model)
