class ElevationSourceNotConfigured(Exception):
    """Raised when no active elevation source is available."""

    pass


class DemNotAvailable(Exception):
    """Raised when DEM data is not available for given geometry."""

    pass
