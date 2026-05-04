from typing import Any
from uuid import UUID, uuid4

from src.modules.pivot_geometry_analysis.application.commands.run_slope_analysis import (
    RunSlopeAnalysis,
)
from src.modules.pivot_geometry_analysis.domain.entities import (
    SlopeAnalysisJobRequest,
    SlopeAnalysisResult,
)
from src.modules.pivot_geometry_analysis.domain.ports import ProfileReader


def _slope_value_to_dict(sv) -> dict[str, float]:
    return {"pct": float(sv.pct), "deg": float(sv.deg)}


def _serialize_result(result: SlopeAnalysisResult) -> dict[str, Any]:
    """Convert a SlopeAnalysisResult domain entity to the canonical dict contract.

    The structure mirrors what ClickHouseSlopeAnalysisWarehouse.get_result_payload()
    returns, ensuring identical response shape for persisted and ephemeral endpoints.
    """
    request_id_str = str(result.request_id)
    long = result.longitudinal_slope_analysis
    trans = result.transversal_slope_analysis
    tors = result.torsional_slope_analysis
    stress = result.structural_stress_analysis
    crop = result.crop_clearance_analysis

    return {
        "request_id": request_id_str,
        "longitudinal_slope_analysis": {
            "request_id": request_id_str,
            "spans": [
                {
                    "azimuth_deg": float(s.azimuth_deg),
                    "span_index": int(s.span_index),
                    "radius_start_m": float(s.radius_start_m),
                    "radius_end_m": float(s.radius_end_m),
                    "slope": _slope_value_to_dict(s.slope),
                    "service_weight": float(s.service_weight),
                    "classification": s.classification,
                }
                for s in long.spans
            ],
        },
        "transversal_slope_analysis": {
            "request_id": request_id_str,
            "points": [
                {
                    "radius_m": float(p.radius_m),
                    "azimuth_from_deg": float(p.azimuth_from_deg),
                    "azimuth_to_deg": float(p.azimuth_to_deg),
                    "arc_length_m": float(p.arc_length_m),
                    "slope": _slope_value_to_dict(p.slope),
                    "classification": p.classification,
                }
                for p in trans.points
            ],
        },
        "torsional_slope_analysis": {
            "request_id": request_id_str,
            "spans": [
                {
                    "azimuth_deg": float(s.azimuth_deg),
                    "span_index": int(s.span_index),
                    "radius_start_m": float(s.radius_start_m),
                    "radius_end_m": float(s.radius_end_m),
                    "alpha_inner": _slope_value_to_dict(s.alpha_inner),
                    "alpha_outer": _slope_value_to_dict(s.alpha_outer),
                    "torsion": _slope_value_to_dict(s.torsion),
                    "longitudinal_slope": _slope_value_to_dict(s.longitudinal_slope),
                    "combined_load_index": float(s.combined_load_index),
                    "classification": s.classification,
                }
                for s in tors.spans
            ],
        },
        "structural_stress_analysis": {
            "request_id": request_id_str,
            "nodes": [
                {
                    "azimuth_deg": float(n.azimuth_deg),
                    "tower_index": int(n.tower_index),
                    "radius_m": float(n.radius_m),
                    "slope_in": _slope_value_to_dict(n.slope_in),
                    "slope_out": _slope_value_to_dict(n.slope_out),
                    "delta": _slope_value_to_dict(n.delta),
                    "node_kind": n.node_kind,
                    "classification": n.classification,
                    "valley_double_check": bool(n.valley_double_check),
                    "left_force_kN": float(n.left_force_kN),
                    "right_force_kN": float(n.right_force_kN),
                    "internal_force_kN": float(n.internal_force_kN),
                    "force_type": n.force_type,
                    "safety_factor": float(n.safety_factor),
                    "is_critical": bool(n.is_critical),
                }
                for n in stress.nodes
            ],
            "runs": [
                {
                    "azimuth_deg": float(r.azimuth_deg),
                    "run_kind": r.run_kind,
                    "span_indices": list(r.span_indices),
                    "cumulative_slope_pct": float(r.cumulative_slope_pct),
                }
                for r in stress.runs
            ],
        },
        "crop_clearance_analysis": {
            "request_id": request_id_str,
            "points": [
                {
                    "azimuth_deg": float(p.azimuth_deg),
                    "distance_m": float(p.distance_m),
                    "boom_elevation_m": float(p.boom_elevation_m),
                    "terrain_elevation_m": float(p.terrain_elevation_m),
                    "clearance_m": float(p.clearance_m),
                    "classification": p.classification,
                    "in_valley_node": bool(p.in_valley_node),
                }
                for p in crop.points
            ],
        },
    }


class ComputeSlopeAnalysis:
    """Query use case: run full slope-analysis pipeline without persisting results.

    Accepts the same inputs as the async (persisted) flow but returns results
    directly in the HTTP response. No writes to PostgreSQL or ClickHouse occur.
    """

    def __init__(self, profile_reader: ProfileReader) -> None:
        self._profile_reader = profile_reader

    def execute(self, profile_analysis_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
        """Compute and return slope analysis results synchronously.

        Args:
            profile_analysis_id: UUID of the profile_analysis job whose terrain
                                  profiles will be used as input.
            payload: Analysis configuration dict (same shape as the async endpoint).

        Returns:
            Serialized result dict with the canonical slope-analysis structure.
        """
        # Synthetic IDs — computation only, nothing persisted
        request_id = uuid4()
        zone_id = uuid4()

        job_request = SlopeAnalysisJobRequest(
            request_id=request_id,
            zone_id=zone_id,
            profile_analysis_id=profile_analysis_id,
            payload=payload,
        )

        runner = RunSlopeAnalysis(profile_reader=self._profile_reader)
        result = runner.execute(job_request)
        return _serialize_result(result)
