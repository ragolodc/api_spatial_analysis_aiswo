# Import de modelos para que Alembic detecte metadata en autogeneracion.
from src.modules.elevation.infrastructure.persistence.models import ElevationSourceModel
from src.modules.zones.infrastructure.persistence.models import ZoneModel

__all__ = ["ElevationSourceModel", "ZoneModel"]
