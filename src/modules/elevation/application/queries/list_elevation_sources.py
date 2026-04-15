"""Query: List configured elevation sources."""

from src.modules.elevation.domain.entities import ElevationSource
from src.modules.elevation.domain.ports import ElevationSourceRepository


class ListElevationSources:
    """Query use case to list configured elevation data sources."""

    def __init__(self, repo: ElevationSourceRepository) -> None:
        self._repo = repo

    def execute(self) -> list[ElevationSource]:
        return self._repo.find_all()

