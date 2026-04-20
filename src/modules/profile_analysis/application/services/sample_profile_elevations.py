from uuid import UUID

from src.modules.profile_analysis.domain.entities import (
    LongitudinalProfile,
    TransverseProfile,
)
from src.modules.profile_analysis.domain.ports import ProfileElevationProvider


class SampleProfileElevations:
    """Apply DEM sampling over previously generated transverse/longitudinal profiles."""

    def __init__(self, provider: ProfileElevationProvider) -> None:
        self._provider = provider

    @property
    def source_id(self) -> UUID:
        return self._provider.source_id

    def sample_transverse(self, profiles: list[TransverseProfile]) -> list[TransverseProfile]:
        return [
            TransverseProfile(
                radius_m=profile.radius_m,
                points=self._provider.sample_points(profile.points),
            )
            for profile in profiles
        ]

    def sample_longitudinal(self, profiles: list[LongitudinalProfile]) -> list[LongitudinalProfile]:
        return [
            LongitudinalProfile(
                azimuth_deg=profile.azimuth_deg,
                points=self._provider.sample_points(profile.points),
            )
            for profile in profiles
        ]
