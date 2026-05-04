from typing import Any
from uuid import UUID, uuid4

from src.modules.pivot_geometry_analysis.application.commands.run_slope_analysis import (
    RunSlopeAnalysis,
)
from src.modules.pivot_geometry_analysis.domain.entities import (
    ClearancePoint,
    NodeStressResult,
    SlopeAnalysisJobRequest,
    SlopeAnalysisResult,
    SpanSlopeResult,
    StressRunResult,
    TorsionalSlopeResult,
    TransversalSlopePoint,
)
from src.modules.pivot_geometry_analysis.domain.ports import ProfileReader
from src.modules.pivot_geometry_analysis.domain.value_objects import SlopeValue


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
        job_request = self._create_job_request(profile_analysis_id, payload)
        result = self._run_analysis(job_request)
        return SlopeAnalysisResultSerializer.serialize(result)

    def _create_job_request(
        self, profile_analysis_id: UUID, payload: dict[str, Any]
    ) -> SlopeAnalysisJobRequest:
        """Create a job request with synthetic IDs for ephemeral computation."""
        return SlopeAnalysisJobRequest(
            request_id=uuid4(),
            zone_id=uuid4(),
            profile_analysis_id=profile_analysis_id,
            payload=payload,
        )

    def _run_analysis(self, job_request: SlopeAnalysisJobRequest) -> SlopeAnalysisResult:
        """Execute the slope analysis pipeline."""
        runner = RunSlopeAnalysis(profile_reader=self._profile_reader)
        return runner.execute(job_request)


class SlopeAnalysisResultSerializer:
    """Handles serialization of SlopeAnalysisResult to the canonical dict format.

    The structure mirrors what ClickHouseSlopeAnalysisWarehouse.get_result_payload()
    returns, ensuring identical response shape for persisted and ephemeral endpoints.
    """

    @staticmethod
    def serialize(result: SlopeAnalysisResult) -> dict[str, Any]:
        """Convert a SlopeAnalysisResult domain entity to the canonical dict contract."""
        request_id = str(result.request_id)

        return {
            "request_id": request_id,
            "longitudinal_slope_analysis": SlopeAnalysisResultSerializer._serialize_longitudinal_analysis(
                request_id, result.longitudinal_slope_analysis
            ),
            "transversal_slope_analysis": SlopeAnalysisResultSerializer._serialize_transversal_analysis(
                request_id, result.transversal_slope_analysis
            ),
            "torsional_slope_analysis": SlopeAnalysisResultSerializer._serialize_torsional_analysis(
                request_id, result.torsional_slope_analysis
            ),
            "structural_stress_analysis": SlopeAnalysisResultSerializer._serialize_stress_analysis(
                request_id, result.structural_stress_analysis
            ),
            "crop_clearance_analysis": SlopeAnalysisResultSerializer._serialize_crop_analysis(
                request_id, result.crop_clearance_analysis
            ),
        }

    # ==================== Longitudinal Analysis ====================

    @staticmethod
    def _serialize_longitudinal_analysis(request_id: str, analysis) -> dict[str, Any]:
        """Serialize longitudinal slope analysis section."""
        return {
            "request_id": request_id,
            "spans": [
                SlopeAnalysisResultSerializer._serialize_longitudinal_span(span)
                for span in analysis.spans
            ],
        }

    @staticmethod
    def _serialize_longitudinal_span(span: SpanSlopeResult) -> dict[str, Any]:
        """Serialize a single longitudinal span."""
        return {
            "azimuth_deg": float(span.azimuth_deg),
            "span_index": int(span.span_index),
            "radius_start_m": float(span.radius_start_m),
            "radius_end_m": float(span.radius_end_m),
            "slope": SlopeAnalysisResultSerializer._serialize_slope_value(span.slope),
            "service_weight": float(span.service_weight),
            "classification": span.classification,
        }

    # ==================== Transversal Analysis ====================

    @staticmethod
    def _serialize_transversal_analysis(request_id: str, analysis) -> dict[str, Any]:
        """Serialize transversal slope analysis section."""
        return {
            "request_id": request_id,
            "points": [
                SlopeAnalysisResultSerializer._serialize_transversal_point(point)
                for point in analysis.points
            ],
        }

    @staticmethod
    def _serialize_transversal_point(point: TransversalSlopePoint) -> dict[str, Any]:
        """Serialize a single transversal point."""
        return {
            "radius_m": float(point.radius_m),
            "azimuth_from_deg": float(point.azimuth_from_deg),
            "azimuth_to_deg": float(point.azimuth_to_deg),
            "arc_length_m": float(point.arc_length_m),
            "slope": SlopeAnalysisResultSerializer._serialize_slope_value(point.slope),
            "classification": point.classification,
        }

    # ==================== Torsional Analysis ====================

    @staticmethod
    def _serialize_torsional_analysis(request_id: str, analysis) -> dict[str, Any]:
        """Serialize torsional slope analysis section."""
        return {
            "request_id": request_id,
            "spans": [
                SlopeAnalysisResultSerializer._serialize_torsional_span(span)
                for span in analysis.spans
            ],
        }

    @staticmethod
    def _serialize_torsional_span(span: TorsionalSlopeResult) -> dict[str, Any]:
        """Serialize a single torsional span."""
        return {
            "azimuth_deg": float(span.azimuth_deg),
            "span_index": int(span.span_index),
            "radius_start_m": float(span.radius_start_m),
            "radius_end_m": float(span.radius_end_m),
            "alpha_inner": SlopeAnalysisResultSerializer._serialize_slope_value(span.alpha_inner),
            "alpha_outer": SlopeAnalysisResultSerializer._serialize_slope_value(span.alpha_outer),
            "torsion": SlopeAnalysisResultSerializer._serialize_slope_value(span.torsion),
            "longitudinal_slope": SlopeAnalysisResultSerializer._serialize_slope_value(
                span.longitudinal_slope
            ),
            "combined_load_index": float(span.combined_load_index),
            "classification": span.classification,
        }

    # ==================== Structural Stress Analysis ====================

    @staticmethod
    def _serialize_stress_analysis(request_id: str, analysis) -> dict[str, Any]:
        """Serialize structural stress analysis section."""
        return {
            "request_id": request_id,
            "nodes": [
                SlopeAnalysisResultSerializer._serialize_stress_node(node)
                for node in analysis.nodes
            ],
            "runs": [
                SlopeAnalysisResultSerializer._serialize_stress_run(run) for run in analysis.runs
            ],
        }

    @staticmethod
    def _serialize_stress_node(node: NodeStressResult) -> dict[str, Any]:
        """Serialize a single stress node."""
        return {
            "azimuth_deg": float(node.azimuth_deg),
            "tower_index": int(node.tower_index),
            "radius_m": float(node.radius_m),
            "slope_in": SlopeAnalysisResultSerializer._serialize_slope_value(node.slope_in),
            "slope_out": SlopeAnalysisResultSerializer._serialize_slope_value(node.slope_out),
            "delta": SlopeAnalysisResultSerializer._serialize_slope_value(node.delta),
            "node_kind": node.node_kind,
            "classification": node.classification,
            "valley_double_check": bool(node.valley_double_check),
            "left_force_kN": float(node.left_force_kN),
            "right_force_kN": float(node.right_force_kN),
            "internal_force_kN": float(node.internal_force_kN),
            "force_type": node.force_type,
            "safety_factor": float(node.safety_factor),
            "is_critical": bool(node.is_critical),
        }

    @staticmethod
    def _serialize_stress_run(run: StressRunResult) -> dict[str, Any]:
        """Serialize a single stress run."""
        return {
            "azimuth_deg": float(run.azimuth_deg),
            "run_kind": run.run_kind,
            "span_indices": list(run.span_indices),
            "cumulative_slope_pct": float(run.cumulative_slope_pct),
        }

    # ==================== Crop Clearance Analysis ====================

    @staticmethod
    def _serialize_crop_analysis(request_id: str, analysis) -> dict[str, Any]:
        """Serialize crop clearance analysis section."""
        return {
            "request_id": request_id,
            "points": [
                SlopeAnalysisResultSerializer._serialize_crop_point(point)
                for point in analysis.points
            ],
        }

    @staticmethod
    def _serialize_crop_point(point: ClearancePoint) -> dict[str, Any]:
        """Serialize a single crop clearance point."""
        return {
            "azimuth_deg": float(point.azimuth_deg),
            "distance_m": float(point.distance_m),
            "boom_elevation_m": float(point.boom_elevation_m),
            "terrain_elevation_m": float(point.terrain_elevation_m),
            "clearance_m": float(point.clearance_m),
            "classification": point.classification,
            "in_valley_node": bool(point.in_valley_node),
        }

    # ==================== Helpers ====================

    @staticmethod
    def _serialize_slope_value(slope_value: SlopeValue) -> dict[str, float]:
        """Convert a SlopeValue value object to dictionary representation."""
        return {
            "pct": float(slope_value.pct),
            "deg": float(slope_value.deg),
        }
