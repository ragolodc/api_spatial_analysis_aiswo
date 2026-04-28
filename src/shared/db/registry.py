# Registra los modelos ORM de cada módulo para que Alembic detecte su metadata.
# Cada módulo es responsable de importar sus propios modelos.
from src.modules.elevation.infrastructure import register_models as _elevation_models
from src.modules.elevation_analysis.infrastructure import (
    register_models as _elevation_analysis_models,
)
from src.modules.pivot_geometry_analysis.infrastructure import (
    register_models as _slope_analysis_models,
)
from src.modules.profile_analysis.infrastructure import (
    register_models as _profile_analysis_models,
)
from src.modules.zones.infrastructure import register_models as _zones_models

_elevation_models()
_elevation_analysis_models()
_profile_analysis_models()
_zones_models()
_slope_analysis_models()
