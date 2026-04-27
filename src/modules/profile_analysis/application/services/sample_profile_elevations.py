from uuid import UUID

from src.modules.profile_analysis.domain.entities import (
    LongitudinalProfile,
    ProfileSamplePoint,
    ProfileType,
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
        sampled_transverse, _ = self.sample_all_profiles(profiles, [])
        return sampled_transverse

    def sample_longitudinal(self, profiles: list[LongitudinalProfile]) -> list[LongitudinalProfile]:
        _, sampled_longitudinal = self.sample_all_profiles([], profiles)
        return sampled_longitudinal

    def sample_all_profiles(
        self,
        transverse_profiles: list[TransverseProfile],
        longitudinal_profiles: list[LongitudinalProfile],
    ) -> tuple[list[TransverseProfile], list[LongitudinalProfile]]:
        all_points: list[ProfileSamplePoint] = []
        profile_slices = []

        for profile in transverse_profiles:
            start = len(all_points)
            all_points.extend(profile.points)
            end = len(all_points)
            profile_slices.append((ProfileType.TRANSVERSE, profile.radius_m, start, end))

        for profile in longitudinal_profiles:
            start = len(all_points)
            all_points.extend(profile.points)
            end = len(all_points)
            profile_slices.append((ProfileType.LONGITUDINAL, profile.azimuth_deg, start, end))

        if not all_points:
            return [], []

        sampled_points = self._provider.sample_points(all_points)

        new_transverse: list[TransverseProfile] = []
        new_longitudinal: list[LongitudinalProfile] = []

        for kind, value, start, end in profile_slices:
            points = sampled_points[start:end]
            if kind == ProfileType.TRANSVERSE:
                new_transverse.append(TransverseProfile(radius_m=value, points=points))
            else:
                new_longitudinal.append(LongitudinalProfile(azimuth_deg=value, points=points))

        return new_transverse, new_longitudinal
