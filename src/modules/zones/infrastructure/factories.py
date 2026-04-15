"""Dependency injection factories for zones module."""

from sqlalchemy.orm import Session

from src.modules.zones.application.commands import CreateZone
from src.modules.zones.application.queries import GetZone, ListZones
from src.modules.zones.infrastructure.persistence.repository import (
    SQLAlchemyZoneRepository,
)


def get_zone_repository(db: Session) -> SQLAlchemyZoneRepository:
    """Factory for zone repository."""
    return SQLAlchemyZoneRepository(db)


def get_create_zone(db: Session) -> CreateZone:
    """Factory for CreateZone command."""
    return CreateZone(get_zone_repository(db))


def get_get_zone(db: Session) -> GetZone:
    """Factory for GetZone query."""
    return GetZone(get_zone_repository(db))


def get_list_zones(db: Session) -> ListZones:
    """Factory for ListZones query."""
    return ListZones(get_zone_repository(db))
