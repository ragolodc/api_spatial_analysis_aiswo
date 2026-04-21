"""Domain exceptions for profile analysis."""


class ProfileAnalysisException(Exception):
    """Base exception for the profile analysis bounded context."""

    pass


class ProfileAnalysisJobNotFound(ProfileAnalysisException):
    """Raised when a profile analysis job cannot be found by its request ID."""

    pass
