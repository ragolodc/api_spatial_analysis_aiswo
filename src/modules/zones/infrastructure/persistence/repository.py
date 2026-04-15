from uuid import UUID

from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import mapping, shape
from sqlalchemy.orm import Session

from src.modules.zones.domain.entities import Zone
from src.modules.zones.infrastructure.persistence.models import ZoneModel


class SQLAlchemyZoneRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def save(self, zone: Zone) -> Zone:
        model = ZoneModel(
            id=zone.id,
            name=zone.name,
            zone_type=zone.zone_type,
            geometry=from_shape(shape(zone.geometry), srid=4326),
            created_at=zone.created_at,
        )
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return self._to_entity(model)

    def find_by_id(self, zone_id: UUID) -> Zone | None:
        model = self._db.get(ZoneModel, zone_id)
        return self._to_entity(model) if model else None

    def find_all(self) -> list[Zone]:
        models = self._db.query(ZoneModel).order_by(ZoneModel.created_at.desc()).all()
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: ZoneModel) -> Zone:
        return Zone(
            id=model.id,
            name=model.name,
            zone_type=model.zone_type,
            geometry=mapping(to_shape(model.geometry)),
            created_at=model.created_at,
        )
