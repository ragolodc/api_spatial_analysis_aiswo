"""Elevation sources metadata endpoint — not an OGC Feature collection (no geometry)."""

from fastapi import APIRouter, Depends

from src.modules.elevation.infrastructure.factories import get_list_elevation_sources
from src.modules.elevation.presentation.schemas import (
    ElevationSourceCollection,
    ElevationSourceItem,
)

router = APIRouter(prefix="/elevation-sources", tags=["Elevation Sources"])


@router.get("", response_model=ElevationSourceCollection)
def list_elevation_sources(
    use_case=Depends(get_list_elevation_sources),
) -> ElevationSourceCollection:
    sources = use_case.execute()
    return ElevationSourceCollection(
        items=[
            ElevationSourceItem(
                id=str(s.id),
                name=s.name,
                srid=s.srid,
                source_url=s.source_url,
                collection=s.collection,
                resolution_m=s.resolution_m,
                is_active=s.is_active,
                created_at=s.created_at.isoformat(),
            )
            for s in sources
        ]
    )
