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
