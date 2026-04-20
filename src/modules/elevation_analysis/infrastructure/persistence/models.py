from datetime import datetime
from uuid import UUID as UUIDType
from uuid import uuid4

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, ForeignKey, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.elevation_analysis.domain.entities import PointType
from src.shared.db.base import Base


class ElevationAnalysisModel(Base):
    __tablename__ = "elevation_analyses"

    id: Mapped[UUIDType] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    zone_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True), ForeignKey("elevation_sources.id"), nullable=False
    )
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    points: Mapped[list["ElevationPointModel"]] = relationship(
        "ElevationPointModel", back_populates="analysis", cascade="all, delete-orphan"
    )


class ElevationPointModel(Base):
    __tablename__ = "elevation_points"

    id: Mapped[UUIDType] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("elevation_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    point_type: Mapped[PointType] = mapped_column(
        SAEnum(
            *[e.value for e in PointType], name="elevation_point_type_enum", create_constraint=False
        ),
        nullable=False,
    )
    geometry: Mapped[object] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326), nullable=False
    )
    elevation_m: Mapped[float] = mapped_column(Float, nullable=False)

    analysis: Mapped["ElevationAnalysisModel"] = relationship(
        "ElevationAnalysisModel", back_populates="points"
    )


class ElevationContourModel(Base):
    __tablename__ = "elevation_contours"

    id: Mapped[UUIDType] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    zone_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True), ForeignKey("elevation_sources.id"), nullable=False
    )
    interval_m: Mapped[float] = mapped_column(Float, nullable=False)
    elevation_m: Mapped[float] = mapped_column(Float, nullable=False)
    geometry: Mapped[object] = mapped_column(
        Geometry(geometry_type="MULTILINESTRING", srid=4326), nullable=False
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
