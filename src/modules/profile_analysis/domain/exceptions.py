"""Domain exceptions for profile analysis."""


class ProfileAnalysisException(Exception):
    """Base exception for the profile analysis bounded context."""


class DemNotAvailable(ProfileAnalysisException):
    """Raised when no DEM coverage is available for the requested profile points."""
