from src.modules.profile_analysis.application.services import (
    GenerateLongitudinalProfiles,
    SampleProfileElevations,
    GenerateTransverseProfiles,
)
from src.modules.profile_analysis.domain.entities import (
    PivotKind,
    ProfileAnalysisInput,
    ProfileAnalysisJobRequest,
    ProfileAnalysisResult,
)


class RunProfileAnalysis:
    """Orchestrates profile generation responsibilities for transverse and longitudinal outputs."""

    def __init__(
        self,
        elevation_sampler: SampleProfileElevations,
        transverse_generator: GenerateTransverseProfiles | None = None,
        longitudinal_generator: GenerateLongitudinalProfiles | None = None,
    ) -> None:
        self._elevation_sampler = elevation_sampler
        self._transverse_generator = transverse_generator or GenerateTransverseProfiles()
        self._longitudinal_generator = longitudinal_generator or GenerateLongitudinalProfiles()

    def execute(self, request: ProfileAnalysisJobRequest) -> ProfileAnalysisResult:
        analysis_input = self._parse_input(request)

        transverse_profiles = self._transverse_generator.execute(analysis_input)
        longitudinal_profiles = self._longitudinal_generator.execute(analysis_input)

        sampled_transverse_profiles = self._elevation_sampler.sample_transverse(transverse_profiles)
        sampled_longitudinal_profiles = self._elevation_sampler.sample_longitudinal(longitudinal_profiles)

        total_points = sum(len(p.points) for p in sampled_transverse_profiles) + sum(
            len(p.points) for p in sampled_longitudinal_profiles
        )

        return ProfileAnalysisResult(
            request_id=request.request_id,
            zone_id=request.zone_id,
            provider=self._elevation_sampler.provider_name,
            resolution_m=self._elevation_sampler.resolution_m,
            transverse_profiles=sampled_transverse_profiles,
            longitudinal_profiles=sampled_longitudinal_profiles,
            total_points=total_points,
        )

    def _parse_input(self, request: ProfileAnalysisJobRequest) -> ProfileAnalysisInput:
        raw_inputs = request.payload.get("inputs", request.payload)

        center = raw_inputs.get("center")
        if not isinstance(center, list) or len(center) != 2:
            raise ValueError("center must be a list of [longitude, latitude]")

        radii = raw_inputs.get("radii_m", [])
        if not isinstance(radii, list) or not radii:
            raise ValueError("radii_m must contain at least one radius")

        parsed_radii = tuple(sorted(float(radius) for radius in radii if float(radius) > 0.0))
        if not parsed_radii:
            raise ValueError("radii_m must contain positive values")

        pivot_kind = PivotKind(raw_inputs["pivot_kind"])

        transverse_spacing_m = float(raw_inputs.get("transverse_spacing_m", 5.0))
        longitudinal_spacing_m = float(raw_inputs.get("longitudinal_spacing_m", 5.0))
        angular_spacing_deg = float(raw_inputs.get("angular_spacing_deg", 10.0))

        if transverse_spacing_m <= 0:
            raise ValueError("transverse_spacing_m must be positive")
        if longitudinal_spacing_m <= 0:
            raise ValueError("longitudinal_spacing_m must be positive")
        if angular_spacing_deg <= 0:
            raise ValueError("angular_spacing_deg must be positive")

        start_angle_deg = raw_inputs.get("start_angle_deg")
        end_angle_deg = raw_inputs.get("end_angle_deg")
        if pivot_kind == PivotKind.SECTORIAL:
            if start_angle_deg is None or end_angle_deg is None:
                raise ValueError("sectorial pivots require start_angle_deg and end_angle_deg")

        return ProfileAnalysisInput(
            zone_id=request.zone_id,
            pivot_kind=pivot_kind,
            center_lon=float(center[0]),
            center_lat=float(center[1]),
            radii_m=parsed_radii,
            transverse_spacing_m=transverse_spacing_m,
            longitudinal_spacing_m=longitudinal_spacing_m,
            angular_spacing_deg=angular_spacing_deg,
            start_angle_deg=float(start_angle_deg) if start_angle_deg is not None else None,
            end_angle_deg=float(end_angle_deg) if end_angle_deg is not None else None,
        )
