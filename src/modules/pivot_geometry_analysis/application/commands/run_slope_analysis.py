import logging

from src.modules.pivot_geometry_analysis.application.services import (
    ComputeCropClearance,
    ComputeLongitudinalSlope,
    ComputeStructuralStress,
    ComputeTorsionalSlope,
    ComputeTransversalSlope,
)
from src.modules.pivot_geometry_analysis.domain.entities import (
    SlopeAnalysisInput,
    SlopeAnalysisJobRequest,
    SlopeAnalysisResult,
)
from src.modules.pivot_geometry_analysis.domain.ports import ProfileReader
from src.modules.pivot_geometry_analysis.domain.value_objects import ThresholdConfig

logger = logging.getLogger(__name__)


class RunSlopeAnalysis:
    """Orchestrates analysis responsibilities for transverse and longitudinal slope."""

    def __init__(
        self,
        profile_reader: ProfileReader,
        crop_clearence_computator: ComputeCropClearance,
        longitudinal_slope_computator: ComputeLongitudinalSlope,
        transverse_slope_computator: ComputeTransversalSlope,
        torsional_slope_computator: ComputeTorsionalSlope,
        structural_stress_computador: ComputeStructuralStress,
    ) -> None:
        self._profile_reader = profile_reader
        self._crop_clearence_computator = crop_clearence_computator or ComputeCropClearance()
        self._longitudinal_slope_computator = (
            longitudinal_slope_computator or ComputeLongitudinalSlope()
        )
        self._transverse_slope_computator = transverse_slope_computator or ComputeTransversalSlope()
        self._torsional_slope_computator = torsional_slope_computator or ComputeTorsionalSlope()
        self._structural_stress_computator = (
            structural_stress_computador or ComputeStructuralStress()
        )

    def execute(self, request: SlopeAnalysisJobRequest) -> SlopeAnalysisResult:
        analysis_input = self._parse_input(request)
        longitudinal_profiles = self._profile_reader.get_longitudinal_profiles(
            request_id=request.request_id
        )
        transversal_profiles = self._profile_reader.get_transversal_profiles(
            request_id=request.request_id
        )
        radii_m = self._profile_reader.get_radii_m(request_id=request.request_id)

        longitudinal_slope_analysis = self._longitudinal_slope_computator.execute(
            profiles=longitudinal_profiles,
            radii_m=radii_m,
            config=analysis_input.longitudinal_slope_config,
        )

        transversal_slope_analysis = self._transverse_slope_computator.execute(
            request_id=request.request_id,
            profiles=transversal_profiles,
            config=analysis_input.transversal_slope_config,
        )

        torsional_slope_analysis = self._torsional_slope_computator.execute(
            request_id=request.request_id,
            longitudinal=longitudinal_slope_analysis,
            transversal=transversal_slope_analysis,
            torsion_config=analysis_input.torsional_config,
            longitudinal_config=analysis_input.torsional_longitudinal_config,
        )

        structural_stress_analysis = self._structural_stress_computator.execute(
            request_id=request.request_id,
            longitudinal=longitudinal_slope_analysis,
            config=analysis_input.structural_stress_config,
        )

        crop_clearence_analysis = self._crop_clearence_computator.execute(
            request_id=request.request_id,
            profiles=longitudinal_profiles,
            radii_m=radii_m,
            h_boom_m=analysis_input.crop_clearence_h_boom_meters,
            crop_risk_m=analysis_input.crop_clearence_crop_risk_meters,
            ground_risk_m=analysis_input.crop_clearence_ground_risk_meters,
        )

        return SlopeAnalysisResult(
            request_id=request.request_id,
            longitudinal_slope_analysis=longitudinal_slope_analysis,
            transversal_slope_analysis=transversal_slope_analysis,
            torsional_slope_analysis=torsional_slope_analysis,
            structural_stress_analysis=structural_stress_analysis,
            crop_clearence_analysis=crop_clearence_analysis,
        )

    def _parse_input(self, request: SlopeAnalysisJobRequest) -> SlopeAnalysisInput:
        raw_input = request.payload.get("inputs", request.payload)

        longitudinal_slope_config = raw_input.get("longitudinal_slope_config", ThresholdConfig(18))

        transversal_slope_config = raw_input.get("transversal_slope_config", ThresholdConfig(18))

        torsional_config = raw_input.get("torsional_config", ThresholdConfig(18))

        torsional_longitudinal_config = raw_input.get(
            "torsional_longitudinal_config", ThresholdConfig(18)
        )

        structural_stress_config = raw_input.get("structural_stress_config", ThresholdConfig(23))

        crop_clearence_h_boom_meters = raw_input.get("crop_clearence_h_boom_meters", 2.90)

        crop_clearence_crop_risk_meters = raw_input.get("crop_clearence_crop_risk_meters", 2.0)

        crop_clearence_ground_risk_meters = raw_input.get("crop_clearence_ground_risk_meters", 1.0)

        return SlopeAnalysisInput(
            longitudinal_slope_config=longitudinal_slope_config,
            transversal_slope_config=transversal_slope_config,
            torsional_config=torsional_config,
            torsional_longitudinal_config=torsional_longitudinal_config,
            structural_stress_config=structural_stress_config,
            crop_clearence_h_boom_meters=crop_clearence_h_boom_meters,
            crop_clearence_crop_risk_meters=crop_clearence_crop_risk_meters,
            crop_clearence_ground_risk_meters=crop_clearence_ground_risk_meters,
        )
