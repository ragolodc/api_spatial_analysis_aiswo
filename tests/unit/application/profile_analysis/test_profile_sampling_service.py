from uuid import UUID, uuid4

from src.modules.profile_analysis.application.services import SampleProfileElevations
from src.modules.profile_analysis.domain.entities import (
    LongitudinalProfile,
    ProfileSamplePoint,
    TransverseProfile,
)

_FAKE_SOURCE_ID = uuid4()


class FakeElevationProvider:
    @property
    def source_id(self) -> UUID:
        return _FAKE_SOURCE_ID

    def sample_points(self, points):
        return [
            ProfileSamplePoint(
                longitude=point.longitude,
                latitude=point.latitude,
                distance_m=point.distance_m,
                radius_m=point.radius_m,
                angle_deg=point.angle_deg,
                elevation_m=123.4,
            )
            for point in points
        ]


def test_sample_profile_elevations_enriches_transverse_profiles() -> None:
    service = SampleProfileElevations(FakeElevationProvider())
    profile = TransverseProfile(
        radius_m=100.0,
        points=[
            ProfileSamplePoint(
                longitude=0.0, latitude=0.0, distance_m=0.0, radius_m=100.0, angle_deg=0.0
            )
        ],
    )

    result = service.sample_transverse([profile])

    assert result[0].points[0].elevation_m == 123.4
    assert service.source_id == _FAKE_SOURCE_ID


def test_sample_profile_elevations_enriches_longitudinal_profiles() -> None:
    service = SampleProfileElevations(FakeElevationProvider())
    profile = LongitudinalProfile(
        azimuth_deg=45.0,
        points=[
            ProfileSamplePoint(
                longitude=0.0, latitude=0.0, distance_m=10.0, radius_m=10.0, angle_deg=45.0
            )
        ],
    )

    result = service.sample_longitudinal([profile])

    assert result[0].points[0].elevation_m == 123.4


def test_sample_profile_elevations_enriches_all_profiles() -> None:
    service = SampleProfileElevations(FakeElevationProvider())
    profile_transversal = TransverseProfile(
        radius_m=100.0,
        points=[
            ProfileSamplePoint(
                longitude=0.0, latitude=0.0, distance_m=0.0, radius_m=100.0, angle_deg=0.0
            )
        ],
    )
    profile_longitudinal = LongitudinalProfile(
        azimuth_deg=45.0,
        points=[
            ProfileSamplePoint(
                longitude=0.0, latitude=0.0, distance_m=10.0, radius_m=10.0, angle_deg=45.0
            )
        ],
    )

    t, l = service.sample_all_profiles([profile_transversal], [profile_longitudinal])
    assert len(t) == 1
    assert len(l) == 1
    assert t[0].points[0].elevation_m == 123.4
    assert l[0].points[0].elevation_m == 123.4
