from datetime import datetime
from uuid import UUID as UUIDType, uuid4

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.db.base import Base


class ElevationSourceModel(Base):
    __tablename__ = "elevation_sources"

    id: Mapped[UUIDType] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    srid: Mapped[int] = mapped_column(Integer, nullable=False, default=4326)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    collection: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
