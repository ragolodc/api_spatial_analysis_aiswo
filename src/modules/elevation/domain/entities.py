from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class ElevationSource:
    id: str
    name: str
    srid: int
    source_url: str | None
    created_at: datetime
