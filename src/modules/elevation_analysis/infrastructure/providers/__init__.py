"""Provider factories for elevation analysis infrastructure."""

from src.modules.elevation_analysis.infrastructure.providers.planetary_computer import (
    PlanetaryComputerAnalysisProvider,
)


def get_dem_provider():
    """Factory for DEM provider adapter."""
    return PlanetaryComputerAnalysisProvider()
