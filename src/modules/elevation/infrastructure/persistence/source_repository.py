"""SQLAlchemy implementation of ElevationSourceRepository."""

from sqlalchemy.orm import Session

from src.modules.elevation.domain.ports import ElevationSourceRepository
from src.modules.elevation.infrastructure.persistence.models import ElevationSourceModel
from src.shared.domain import ElevationSource


class SQLAlchemyElevationSourceRepository(ElevationSourceRepository):
    """SQLAlchemy implementation for elevation source persistence."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def _to_entity(self, row: ElevationSourceModel) -> ElevationSource:
        return ElevationSource(
            id=row.id,
            name=row.name,
            srid=row.srid,
            source_url=row.source_url,
            collection=row.collection,
            resolution_m=row.resolution_m,
            is_active=row.is_active,
            created_at=row.created_at,
        )

    def find_all(self) -> list[ElevationSource]:
        rows = (
            self._db.query(ElevationSourceModel)
            .order_by(ElevationSourceModel.created_at.desc())
            .all()
        )
        return [self._to_entity(row) for row in rows]

    def find_active(self) -> ElevationSource | None:
        row = (
            self._db.query(ElevationSourceModel)
            .filter(ElevationSourceModel.is_active.is_(True))
            .first()
        )
        return self._to_entity(row) if row else None
