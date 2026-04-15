from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.modules.elevation.infrastructure.factories import get_list_elevation_sources
from src.shared.db.session import get_db

router = APIRouter(prefix="/elevation", tags=["elevation"])


@router.get("/sources")
def get_elevation_sources(db: Session = Depends(get_db)) -> dict:
    sources = get_list_elevation_sources(db).execute()
    return {"items": sources}
