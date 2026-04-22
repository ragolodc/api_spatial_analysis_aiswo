import math

from src.modules.profile_analysis.application.services._geometry import (
    circular_window,
    degrees_for_arc_step,
    iter_linear_space,
    normalize_angle,
    polar_to_lon_lat,
)
from src.modules.profile_analysis.domain.entities import (
    PivotKind,
    ProfileAnalysisInput,
    ProfileSamplePoint,
    TransverseProfile,
)


class GenerateTransverseProfiles:
    """Build transverse profiles (rings/arcs) for a pivot."""

    def execute(self, analysis_input: ProfileAnalysisInput) -> list[TransverseProfile]:
        profiles: list[TransverseProfile] = []

        for radius_m in analysis_input.radii_m:
            points = self._build_points(analysis_input, radius_m)
            profiles.append(TransverseProfile(radius_m=radius_m, points=points))

        return profiles

    def _build_points(
        self, analysis_input: ProfileAnalysisInput, radius_m: float
    ) -> list[ProfileSamplePoint]:
        if analysis_input.pivot_kind == PivotKind.CIRCULAR:
            angle_start = 0.0
            angle_end = 360.0
            include_end = False
        else:
            if analysis_input.start_angle_deg is None or analysis_input.end_angle_deg is None:
                raise ValueError("Sectorial pivot requires start_angle_deg and end_angle_deg")
            angle_start, angle_end = circular_window(
                analysis_input.start_angle_deg,
                analysis_input.end_angle_deg,
            )
            include_end = True

        step_deg = max(0.1, degrees_for_arc_step(radius_m, analysis_input.transverse_spacing_m))
        angles = iter_linear_space(angle_start, angle_end, step_deg, include_end=include_end)

        points: list[ProfileSamplePoint] = []
        for angle in angles:
            lon, lat = polar_to_lon_lat(
                analysis_input.center_lon,
                analysis_input.center_lat,
                radius_m,
                normalize_angle(angle),
            )
            distance_m = radius_m * math.radians(max(0.0, angle - angle_start))
            points.append(
                ProfileSamplePoint(
                    longitude=lon,
                    latitude=lat,
                    distance_m=distance_m,
                    radius_m=radius_m,
                    angle_deg=normalize_angle(angle),
                )
            )

        return points
