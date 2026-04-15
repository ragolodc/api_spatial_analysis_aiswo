from uuid import UUID

from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import MultiLineString, Point, mapping, shape
from sqlalchemy.orm import Session

from src.modules.elevation_analysis.domain.entities import (
    ElevationAnalysis,
    ElevationContour,
    ElevationPoint,
    PointType,
)
from src.modules.elevation_analysis.infrastructure.persistence.models import (
    ElevationAnalysisModel,
    ElevationContourModel,
    ElevationPointModel,
)


class SQLAlchemyElevationAnalysisRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def save(self, analysis: ElevationAnalysis) -> ElevationAnalysis:
        model = ElevationAnalysisModel(
            id=analysis.id,
            zone_id=analysis.zone_id,
            provider=analysis.provider,
            resolution_m=analysis.resolution_m,
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
        model = self._db.get(ElevationAnalysisModel, analysis_id)
        return self._to_entity(model) if model else None

    def find_by_zone(self, zone_id: UUID) -> list[ElevationAnalysis]:
        models = (
            self._db.query(ElevationAnalysisModel)
            .filter(ElevationAnalysisModel.zone_id == zone_id)
            .order_by(ElevationAnalysisModel.analyzed_at.desc())
            .all()
        )
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: ElevationAnalysisModel) -> ElevationAnalysis:
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
            provider=model.provider,
            resolution_m=model.resolution_m,
            analyzed_at=model.analyzed_at,
            points=points,
        )


class SQLAlchemyElevationContourRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def save_all(self, contours: list[ElevationContour]) -> list[ElevationContour]:
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
        models = (
            self._db.query(ElevationContourModel)
            .filter(ElevationContourModel.zone_id == zone_id)
            .order_by(ElevationContourModel.elevation_m)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def delete_by_zone(self, zone_id: UUID) -> None:
        self._db.query(ElevationContourModel).filter(
            ElevationContourModel.zone_id == zone_id
        ).delete()
        self._db.commit()

    def _to_entity(self, model: ElevationContourModel) -> ElevationContour:
        return ElevationContour(
            id=model.id,
            zone_id=model.zone_id,
            provider=model.provider,
            interval_m=model.interval_m,
            elevation_m=model.elevation_m,
            geometry=mapping(to_shape(model.geometry)),
            generated_at=model.generated_at,
        )
