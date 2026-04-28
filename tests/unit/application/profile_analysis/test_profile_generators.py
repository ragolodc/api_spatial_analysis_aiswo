from uuid import UUID, uuid4

from src.modules.profile_analysis.application.commands import RunProfileAnalysis
from src.modules.profile_analysis.application.services import (
    GenerateLongitudinalProfiles,
    GenerateTransverseProfiles,
    SampleProfileElevations,
)
from src.modules.profile_analysis.domain.entities import (
    PivotKind,
    ProfileAnalysisInput,
    ProfileAnalysisJobRequest,
)
from src.shared.domain.entities import Spans, SpansConfig

_FAKE_SOURCE_ID = uuid4()


class FakeElevationProvider:
    @property
    def source_id(self) -> UUID:
        return _FAKE_SOURCE_ID

    def sample_points(self, points):
        sampled = []
        for index, point in enumerate(points, start=1):
            sampled.append(
                point.__class__(
                    longitude=point.longitude,
                    latitude=point.latitude,
                    distance_m=point.distance_m,
                    radius_m=point.radius_m,
                    angle_deg=point.angle_deg,
                    elevation_m=float(index),
                )
            )
        return sampled


def _base_input(pivot_kind: PivotKind = PivotKind.CIRCULAR) -> ProfileAnalysisInput:
    return ProfileAnalysisInput(
        zone_id=uuid4(),
        pivot_kind=pivot_kind,
        center_lon=-74.05,
        center_lat=4.61,
        radii_m=(100.0, 200.0),
        spans_config=SpansConfig(
            [
                Spans(position=1, length=100, dry_weight=29, service_weight=45),
                Spans(position=2, length=200, dry_weight=30, service_weight=40),
            ]
        ),
        transverse_spacing_m=10.0,
        longitudinal_spacing_m=50.0,
        angular_spacing_deg=90.0,
        start_angle_deg=30.0 if pivot_kind == PivotKind.SECTORIAL else None,
        end_angle_deg=120.0 if pivot_kind == PivotKind.SECTORIAL else None,
    )


def test_transverse_profiles_are_generated_per_radius() -> None:
    generator = GenerateTransverseProfiles()

    profiles = generator.execute(_base_input(PivotKind.CIRCULAR))

    assert len(profiles) == 2
    assert profiles[0].radius_m == 100.0
    assert len(profiles[0].points) > 10
    assert profiles[0].points[0].distance_m == 0.0


def test_longitudinal_profiles_are_generated_per_azimuth() -> None:
    generator = GenerateLongitudinalProfiles()

    profiles = generator.execute(_base_input(PivotKind.CIRCULAR))

    assert len(profiles) == 4
    assert profiles[0].azimuth_deg == 0.0
    assert profiles[1].azimuth_deg == 90.0
    assert profiles[0].points[0].distance_m == 0.0
    assert profiles[0].points[-1].radius_m == 300.0


def test_sectorial_generators_respect_angular_window() -> None:
    transverse = GenerateTransverseProfiles().execute(_base_input(PivotKind.SECTORIAL))
    longitudinal = GenerateLongitudinalProfiles().execute(_base_input(PivotKind.SECTORIAL))

    assert all(30.0 <= p.angle_deg <= 120.0 for profile in transverse for p in profile.points)
    assert all(30.0 <= profile.azimuth_deg <= 120.0 for profile in longitudinal)


def test_run_profile_analysis_orchestrates_both_generators() -> None:
    request = ProfileAnalysisJobRequest(
        request_id=uuid4(),
        zone_id=uuid4(),
        payload={
            "inputs": {
                "zone_id": str(uuid4()),
                "pivot_kind": "circular",
                "center": [-74.05, 4.61],
                "spans": [
                    {"position": 1, "length": 100, "dry_weight": 29, "service_weight": 45},
                    {"position": 2, "length": 200, "dry_weight": 30, "service_weight": 40},
                ],
                "radii_m": [100.0, 200.0],
                "transverse_spacing_m": 10.0,
                "longitudinal_spacing_m": 50.0,
                "angular_spacing_deg": 90.0,
            }
        },
    )

    result = RunProfileAnalysis(
        elevation_sampler=SampleProfileElevations(FakeElevationProvider())
    ).execute(request)

    assert len(result.transverse_profiles) == 2
    assert len(result.longitudinal_profiles) == 4
    assert result.source_id == _FAKE_SOURCE_ID
    assert result.transverse_profiles[0].points[0].elevation_m == 1.0
    assert result.total_points > 0
