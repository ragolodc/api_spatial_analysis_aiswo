from src.modules.profile_analysis.application.services._geometry import (
    circular_window,
    iter_linear_space,
    normalize_angle,
    polar_to_lon_lat,
)
from src.modules.profile_analysis.domain.entities import (
    LongitudinalProfile,
    PivotKind,
    ProfileAnalysisInput,
    ProfileSamplePoint,
)


class GenerateLongitudinalProfiles:
    """Build longitudinal profiles (radial lines) for a pivot."""

    def execute(self, analysis_input: ProfileAnalysisInput) -> list[LongitudinalProfile]:
        max_radius = max(analysis_input.radii_m)
        radii = iter_linear_space(
            0.0,
            max_radius,
            analysis_input.longitudinal_spacing_m,
            include_end=True,
        )

        if analysis_input.pivot_kind == PivotKind.CIRCULAR:
            angle_start = 0.0
            angle_end = 360.0
            include_end = False
        else:
            assert analysis_input.start_angle_deg is not None
            assert analysis_input.end_angle_deg is not None
            angle_start, angle_end = circular_window(
                analysis_input.start_angle_deg,
                analysis_input.end_angle_deg,
            )
            include_end = True

        angles = iter_linear_space(
            angle_start,
            angle_end,
            analysis_input.angular_spacing_deg,
            include_end=include_end,
        )

        profiles: list[LongitudinalProfile] = []
        for angle in angles:
            normalized_angle = normalize_angle(angle)
            points: list[ProfileSamplePoint] = []
            for radius_m in radii:
                lon, lat = polar_to_lon_lat(
                    analysis_input.center_lon,
                    analysis_input.center_lat,
                    radius_m,
                    normalized_angle,
                )
                points.append(
                    ProfileSamplePoint(
                        longitude=lon,
                        latitude=lat,
                        distance_m=radius_m,
                        radius_m=radius_m,
                        angle_deg=normalized_angle,
                    )
                )
            profiles.append(LongitudinalProfile(azimuth_deg=normalized_angle, points=points))

        return profiles
