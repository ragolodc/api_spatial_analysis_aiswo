from src.modules.profile_analysis.domain.ports import ProfileElevationProvider
from src.modules.profile_analysis.domain.entities import (
    LongitudinalProfile,
    ProfileSamplePoint,
    TransverseProfile,
)


class SampleProfileElevations:
    """Apply DEM sampling over previously generated transverse/longitudinal profiles."""

    def __init__(self, provider: ProfileElevationProvider) -> None:
        self._provider = provider

    @property
    def provider_name(self) -> str:
        return self._provider.name

    @property
    def resolution_m(self) -> float:
        return self._provider.resolution_m

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
