from uuid import UUID

from pydantic import BaseModel


class SlopeAnalysisInputs(BaseModel):
    zone_id: UUID
    profile_analysis_id: UUID
    longitudinal_slope_max_threshold: float
    transversal_slope_max_threshold: float
    torsional_max_threshold: float
    torsional_longitudinal_max_threshold: float
    structural_stress_max_threshold: float
    crop_clearance_h_boom_meters: float
    crop_clearance_crop_risk_meters: float
    crop_clearance_ground_risk_meters: float


class QueueSlopeAnalysisRequest(BaseModel):
    inputs: SlopeAnalysisInputs
