from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID  # noqa: N811
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database import Base


class UserModel(Base):
    """User database model."""

    __tablename__: str = "users"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True
    )
    email: Mapped[str] = mapped_column(String(length=254), unique=True)
    password: Mapped[str] = mapped_column(String())
    is_active: Mapped[bool] = mapped_column(
        Boolean(), server_default=text("true")
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
