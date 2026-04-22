class PivotGeometryException(Exception):
    pass


class ProfileNotReady(PivotGeometryException):
    """Raised when the referenced profile analysis job has no sampled points yet."""


class ProfileJobNotFound(PivotGeometryException):
    """Raised when the referenced profile analysis job does not exist."""
