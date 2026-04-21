from src.modules.zones.infrastructure.zone_geometry_adapter import SQLAlchemyZoneGeometryAdapter


def register_models() -> None:
    import src.modules.zones.infrastructure.persistence.models  # noqa: F401


__all__ = ["SQLAlchemyZoneGeometryAdapter", "register_models"]
