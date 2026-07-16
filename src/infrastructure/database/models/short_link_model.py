from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID  # noqa: N811
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.constants import SHORT_CODE_MAX_LENGTH
from src.infrastructure.database import Base


class ShortLinkModel(Base):
    """Short link database model."""

    __tablename__: str = "short_links"
    __table_args__: tuple[CheckConstraint] = (
        CheckConstraint(
            sqltext="expires_at IS NULL OR expires_at > created_at",
            name="ck_short_links_expires_at_after_created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True
    )
    original_url: Mapped[str] = mapped_column(Text())
    short_code: Mapped[str] = mapped_column(
        String(length=SHORT_CODE_MAX_LENGTH), unique=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
