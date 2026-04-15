from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.modules.elevation.application.services import ElevationQueryService
from src.shared.db.session import get_db

router = APIRouter(prefix="/elevation", tags=["elevation"])


@router.get("/sources")
def get_elevation_sources(db: Session = Depends(get_db)) -> dict:
    service = ElevationQueryService(db)
    return {"items": service.list_sources()}
