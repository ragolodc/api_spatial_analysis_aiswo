"""Domain exceptions for the elevation module."""


class ElevationException(Exception):
    """Base exception for the elevation bounded context."""


class ElevationDataNotFound(ElevationException):
    """Raised when no DEM coverage is found for the requested geometry."""
