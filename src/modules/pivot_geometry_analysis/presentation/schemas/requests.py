from uuid import UUID

from pydantic import BaseModel


class SlopeAnalysisInputs(BaseModel):
    zone_id: UUID
    profile_analysis_id: UUID
    longitudinal_slope_max_threshold: float | None = None
    transversal_slope_max_threshold: float | None = None
    torsional_max_threshold: float | None = None
    torsional_longitudinal_max_threshold: float | None = None
    structural_stress_max_threshold: float | None = None
    crop_clearance_h_boom_meters: float | None = None
    crop_clearance_crop_risk_meters: float | None = None
    crop_clearance_ground_risk_meters: float | None = None


class QueueSlopeAnalysisRequest(BaseModel):
    inputs: SlopeAnalysisInputs


class ComputeSlopeAnalysisInputs(BaseModel):
    """Inputs for ephemeral full-pipeline computation (all 5 analyses)."""

    profile_analysis_id: UUID
    longitudinal_slope_max_threshold: float | None = None
    transversal_slope_max_threshold: float | None = None
    torsional_max_threshold: float | None = None
    torsional_longitudinal_max_threshold: float | None = None
    structural_stress_max_threshold: float | None = None
    crop_clearance_h_boom_meters: float | None = None
    crop_clearance_crop_risk_meters: float | None = None
    crop_clearance_ground_risk_meters: float | None = None


class ComputeSlopeAnalysisRequest(BaseModel):
    inputs: ComputeSlopeAnalysisInputs


# ---------------------------------------------------------------------------
# Specific compute request schemas — only the relevant parameters per analysis
# ---------------------------------------------------------------------------


class ComputeLongitudinalSlopeInputs(BaseModel):
    profile_analysis_id: UUID
    longitudinal_slope_max_threshold: float | None = None


class ComputeLongitudinalSlopeRequest(BaseModel):
    inputs: ComputeLongitudinalSlopeInputs


class ComputeTransversalSlopeInputs(BaseModel):
    profile_analysis_id: UUID
    transversal_slope_max_threshold: float | None = None


class ComputeTransversalSlopeRequest(BaseModel):
    inputs: ComputeTransversalSlopeInputs


class ComputeTorsionalSlopeInputs(BaseModel):
    profile_analysis_id: UUID
    torsional_max_threshold: float | None = None
    torsional_longitudinal_max_threshold: float | None = None


class ComputeTorsionalSlopeRequest(BaseModel):
    inputs: ComputeTorsionalSlopeInputs


class ComputeStructuralStressInputs(BaseModel):
    profile_analysis_id: UUID
    structural_stress_max_threshold: float | None = None


class ComputeStructuralStressRequest(BaseModel):
    inputs: ComputeStructuralStressInputs


class ComputeCropClearanceInputs(BaseModel):
    profile_analysis_id: UUID
    crop_clearance_h_boom_meters: float | None = None
    crop_clearance_crop_risk_meters: float | None = None
    crop_clearance_ground_risk_meters: float | None = None


class ComputeCropClearanceRequest(BaseModel):
    inputs: ComputeCropClearanceInputs
