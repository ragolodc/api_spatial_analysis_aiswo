"""SQLAlchemy implementation of ElevationAnalysisRepository."""

from uuid import UUID

from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point
from sqlalchemy.orm import Session

from src.modules.elevation_analysis.domain.entities import (
    ElevationAnalysis,
    ElevationPoint,
    PointType,
)
from src.modules.elevation_analysis.domain.ports import ElevationAnalysisRepository
from src.modules.elevation_analysis.infrastructure.persistence.models import (
    ElevationAnalysisModel,
    ElevationPointModel,
)


class SQLAlchemyElevationAnalysisRepository(ElevationAnalysisRepository):
    """SQLAlchemy implementation for elevation analysis persistence."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def save(self, analysis: ElevationAnalysis) -> ElevationAnalysis:
        """Persist an elevation analysis with its characteristic points."""
        model = ElevationAnalysisModel(
            id=analysis.id,
            zone_id=analysis.zone_id,
            source_id=analysis.source_id,
            analyzed_at=analysis.analyzed_at,
            points=[
                ElevationPointModel(
                    id=p.id,
                    analysis_id=p.analysis_id,
                    point_type=p.point_type.value,
                    geometry=from_shape(Point(p.longitude, p.latitude), srid=4326),
                    elevation_m=p.elevation_m,
                )
                for p in analysis.points
            ],
        )
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return self._to_entity(model)

    def find_by_id(self, analysis_id: UUID) -> ElevationAnalysis | None:
        """Retrieve an analysis by ID."""
        model = self._db.get(ElevationAnalysisModel, analysis_id)
        return self._to_entity(model) if model else None

    def find_by_zone(self, zone_id: UUID) -> list[ElevationAnalysis]:
        """Retrieve all analyses for a zone, ordered by most recent first."""
        models = (
            self._db.query(ElevationAnalysisModel)
            .filter(ElevationAnalysisModel.zone_id == zone_id)
            .order_by(ElevationAnalysisModel.analyzed_at.desc())
            .all()
        )
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: ElevationAnalysisModel) -> ElevationAnalysis:
        """Convert SQLAlchemy model to domain entity."""
        points = [
            ElevationPoint(
                id=p.id,
                analysis_id=p.analysis_id,
                point_type=PointType(p.point_type),
                longitude=float(to_shape(p.geometry).x),
                latitude=float(to_shape(p.geometry).y),
                elevation_m=p.elevation_m,
            )
            for p in model.points
        ]
        return ElevationAnalysis(
            id=model.id,
            zone_id=model.zone_id,
            source_id=model.source_id,
            analyzed_at=model.analyzed_at,
            points=points,
        )
