"""Query: List configured elevation sources."""

from sqlalchemy.orm import Session

from src.modules.elevation.infrastructure.persistence.models import ElevationSourceModel


class ListElevationSources:
    """Query use case to list configured elevation data sources."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def execute(self) -> list[dict]:
        rows = (
            self._db.query(ElevationSourceModel)
            .order_by(ElevationSourceModel.created_at.desc())
            .all()
        )
        return [
            {
                "id": str(row.id),
                "name": row.name,
                "srid": row.srid,
                "source_url": row.source_url,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
