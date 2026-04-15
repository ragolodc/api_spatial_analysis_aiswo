"""Domain exceptions for elevation analysis module."""


class ElevationAnalysisException(Exception):
    """Base exception for elevation analysis domain."""

    pass


class ZoneNotFound(ElevationAnalysisException):
    """Raised when a zone is not found in repository."""

    pass


class DemNotAvailable(ElevationAnalysisException):
    """Raised when DEM data is not available for given geometry."""

    pass


class ContoursGenerationError(ElevationAnalysisException):
    """Raised when contour generation fails."""

    pass
