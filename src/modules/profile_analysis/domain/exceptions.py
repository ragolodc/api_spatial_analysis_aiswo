"""Domain exceptions for profile analysis."""


class ProfileAnalysisException(Exception):
    """Base exception for the profile analysis bounded context."""

    pass


class DemNotAvailable(ProfileAnalysisException):
    """Raised when no DEM coverage is available for the requested profile points."""

    pass


class ElevationSourceNotConfigured(ProfileAnalysisException):
    """Raised when no active elevation source is available."""

    pass
