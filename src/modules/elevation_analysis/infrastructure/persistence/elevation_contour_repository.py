"""SQLAlchemy implementation of ElevationContourRepository."""

from uuid import UUID

from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import mapping, shape
from sqlalchemy.orm import Session

from src.modules.elevation_analysis.domain.entities import ElevationContour
from src.modules.elevation_analysis.domain.ports import ElevationContourRepository
from src.modules.elevation_analysis.infrastructure.persistence.models import (
    ElevationContourModel,
)


class SQLAlchemyElevationContourRepository(ElevationContourRepository):
    """SQLAlchemy implementation for elevation contour persistence."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def save_all(self, contours: list[ElevationContour]) -> list[ElevationContour]:
        """Persist a batch of elevation contours."""
        models = [
            ElevationContourModel(
                id=c.id,
                zone_id=c.zone_id,
                provider=c.provider,
                interval_m=c.interval_m,
                elevation_m=c.elevation_m,
                geometry=from_shape(shape(c.geometry), srid=4326),
                generated_at=c.generated_at,
            )
            for c in contours
        ]
        self._db.add_all(models)
        self._db.commit()
        return contours

    def find_by_zone(self, zone_id: UUID) -> list[ElevationContour]:
        """Retrieve all contours for a zone, ordered by elevation ascending."""
        models = (
            self._db.query(ElevationContourModel)
            .filter(ElevationContourModel.zone_id == zone_id)
            .order_by(ElevationContourModel.elevation_m)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def delete_by_zone(self, zone_id: UUID) -> None:
        """Delete all contours for a zone (before regenerating)."""
        self._db.query(ElevationContourModel).filter(
            ElevationContourModel.zone_id == zone_id
        ).delete()
        self._db.commit()

    def _to_entity(self, model: ElevationContourModel) -> ElevationContour:
        """Convert SQLAlchemy model to domain entity."""
        return ElevationContour(
            id=model.id,
            zone_id=model.zone_id,
            provider=model.provider,
            interval_m=model.interval_m,
            elevation_m=model.elevation_m,
            geometry=mapping(to_shape(model.geometry)),
            generated_at=model.generated_at,
        )
