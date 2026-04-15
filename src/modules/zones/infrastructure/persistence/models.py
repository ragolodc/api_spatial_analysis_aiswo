from datetime import datetime
from uuid import UUID as UUIDType, uuid4

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Enum as SAEnum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.modules.zones.domain.entities import ZoneType
from src.shared.db.base import Base


class ZoneModel(Base):
    __tablename__ = "zones"

    id: Mapped[UUIDType] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    zone_type: Mapped[ZoneType] = mapped_column(SAEnum(ZoneType, name="zone_type_enum"), nullable=False)
    geometry: Mapped[object] = mapped_column(Geometry(geometry_type="POLYGON", srid=4326), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
