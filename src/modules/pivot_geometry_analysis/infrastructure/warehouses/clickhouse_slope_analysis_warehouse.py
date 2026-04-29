import re

import clickhouse_connect.driver

from src.modules.pivot_geometry_analysis.domain.entities import (
    CropClearanceAnalysis,
    LongitudinalSlopeAnalysis,
    SlopeAnalysisJobRequest,
    SlopeAnalysisResult,
    StructuralStressAnalysis,
    TorsionalSlopeAnalysis,
    TransversalSlopeAnalysis,
)

_MAX_QUERY_LIMIT = 10_000
_SAFE_IDENTIFIER = re.compile(r"^[a-zA-Z0-9_]+$")


class ClickHouseSlopeAnalysisWarehouse:
    """ClickHouse adapter for slope analysis storage and analytics."""

    def __init__(self, client: clickhouse_connect.driver.Client, database: str) -> None:
        if not _SAFE_IDENTIFIER.match(database):
            raise ValueError(f"Invalid database name: {database!r}")
        self._database = database
        self._client = client

    def __enter__(self) -> "ClickHouseSlopeAnalysisWarehouse":
        return self

    def __exit__(self, *args: object) -> None:
        self._client.close()

    def store_result(
        self, analysis: SlopeAnalysisResult, job_request: SlopeAnalysisJobRequest
    ) -> None:
        self._store_longitudinal_slope_analysis(
            analysis=analysis.longitudinal_slope_analysis, job_request=job_request
        )
        self._store_transversal_slope_analysis(
            analysis=analysis.transversal_slope_analysis, job_request=job_request
        )
        self._store_torsional_slope_analysis(
            analysis=analysis.torsional_slope_analysis, job_request=job_request
        )

        self._store_structural_stress_analysis(
            analysis=analysis.structural_stress_analysis, job_request=job_request
        )

        self._store_crop_clearance_analysis(
            analysis=analysis.crop_clearance_analysis, job_request=job_request
        )

    def _store_longitudinal_slope_analysis(
        self, analysis: LongitudinalSlopeAnalysis, job_request: SlopeAnalysisJobRequest
    ) -> None:
        rows: list[list] = []

        for span in analysis.spans:
            rows.append(
                [
                    str(analysis.request_id),
                    str(job_request.zone_id),
                    str(job_request.profile_analysis_id),
                    span.azimuth_deg,
                    span.span_index,
                    span.radius_start_m,
                    span.radius_end_m,
                    span.slope.pct,
                    span.slope.deg,
                    span.service_weight,
                    span.classification,
                ]
            )

        self._client.insert(
            table=f"{self._database}.longitudinal_slope_analysis",
            column_names=[
                "request_id",
                "zone_id",
                "profile_analysis_id",
                "azimuth_deg",
                "span_index",
                "radius_start_m",
                "radius_end_m",
                "slope_pct",
                "slope_deg",
                "service_weight",
                "classification",
            ],
            data=rows,
        )

    def _store_transversal_slope_analysis(
        self, analysis: TransversalSlopeAnalysis, job_request: SlopeAnalysisJobRequest
    ) -> None:
        rows: list[list] = []
        for arc in analysis.points:
            rows.append(
                [
                    str(analysis.request_id),
                    str(job_request.zone_id),
                    str(job_request.profile_analysis_id),
                    arc.radius_m,
                    arc.azimuth_from_deg,
                    arc.azimuth_to_deg,
                    arc.arc_length_m,
                    arc.slope.pct,
                    arc.slope.deg,
                    arc.classification,
                ]
            )

        self._client.insert(
            table=f"{self._database}.transversal_slope_analysis",
            column_names=[
                "request_id",
                "zone_id",
                "profile_analysis_id",
                "radius_m",
                "azimuth_from_deg",
                "azimuth_to_deg",
                "arc_length_m",
                "slope_pct",
                "slope_deg",
                "classification",
            ],
            data=rows,
        )

    def _store_torsional_slope_analysis(
        self, analysis: TorsionalSlopeAnalysis, job_request: SlopeAnalysisJobRequest
    ) -> None:
        rows: list[list] = []

        for spans in analysis.spans:
            rows.append(
                [
                    str(analysis.request_id),
                    str(job_request.zone_id),
                    str(job_request.profile_analysis_id),
                    spans.azimuth_deg,
                    spans.span_index,
                    spans.radius_start_m,
                    spans.radius_end_m,
                    spans.alpha_inner.pct,
                    spans.alpha_inner.deg,
                    spans.alpha_outer.pct,
                    spans.alpha_outer.deg,
                    spans.torsion.pct,
                    spans.torsion.deg,
                    spans.longitudinal_slope.pct,
                    spans.longitudinal_slope.deg,
                    spans.combined_load_index,
                    spans.classification,
                ]
            )

        self._client.insert(
            table=f"{self._database}.torsional_slope_analysis",
            column_names=[
                "request_id",
                "zone_id",
                "profile_analysis_id",
                "azimuth_deg",
                "span_index",
                "radius_start_m",
                "radius_end_m",
                "alpha_inner_pct",
                "alpha_inner_deg",
                "alpha_outer_pct",
                "alpha_outer_deg",
                "torsion_pct",
                "torsion_deg",
                "longitudinal_slope_pct",
                "longitudinal_slope_deg",
                "combined_load_index",
                "classification",
            ],
            data=rows,
        )

    def _store_structural_stress_analysis(
        self, analysis: StructuralStressAnalysis, job_request: SlopeAnalysisJobRequest
    ) -> None:
        rows_nodes_stress: list[list] = []
        rows_spans_stress: list[list] = []

        for node in analysis.nodes:
            rows_nodes_stress.append(
                [
                    str(analysis.request_id),
                    str(job_request.zone_id),
                    str(job_request.profile_analysis_id),
                    node.azimuth_deg,
                    node.tower_index,
                    node.radius_m,
                    node.slope_in.pct,
                    node.slope_in.deg,
                    node.slope_out.pct,
                    node.slope_out.deg,
                    node.delta.pct,
                    node.delta.deg,
                    node.node_kind,
                    node.classification,
                    int(node.valley_double_check),
                    node.left_force_kN,
                    node.right_force_kN,
                    node.internal_force_kN,
                    node.force_type,
                    node.safety_factor,
                    int(node.is_critical),
                ]
            )

        for run in analysis.runs:
            rows_spans_stress.append(
                [
                    str(analysis.request_id),
                    str(job_request.zone_id),
                    str(job_request.profile_analysis_id),
                    run.azimuth_deg,
                    run.run_kind,
                    ",".join(map(str, run.span_indices)),
                    run.cumulative_slope_pct,
                ]
            )

        self._client.insert(
            table=f"{self._database}.structural_stress_nodes",
            column_names=[
                "request_id",
                "zone_id",
                "profile_analysis_id",
                "azimuth_deg",
                "tower_index",
                "radius_m",
                "slope_in_pct",
                "slope_in_deg",
                "slope_out_pct",
                "slope_out_deg",
                "delta_pct",
                "delta_deg",
                "node_kind",
                "classification",
                "valley_double_check",
                "left_force_kN",
                "right_force_kN",
                "internal_force_kN",
                "force_type",
                "safety_factor",
                "is_critical",
            ],
            data=rows_nodes_stress,
        )

        self._client.insert(
            table=f"{self._database}.structural_stress_runs",
            column_names=[
                "request_id",
                "zone_id",
                "profile_analysis_id",
                "azimuth_deg",
                "run_kind",
                "span_indices",
                "cumulative_slope_pct",
            ],
            data=rows_spans_stress,
        )

    def _store_crop_clearance_analysis(
        self, analysis: CropClearanceAnalysis, job_request: SlopeAnalysisJobRequest
    ) -> None:
        rows: list[list] = []

        for span in analysis.points:
            rows.append(
                [
                    str(analysis.request_id),
                    str(job_request.zone_id),
                    str(job_request.profile_analysis_id),
                    span.azimuth_deg,
                    span.distance_m,
                    span.boom_elevation_m,
                    span.terrain_elevation_m,
                    span.clearance_m,
                    span.classification,
                    int(span.in_valley_node),
                ]
            )

        self._client.insert(
            table=f"{self._database}.crop_clearance_analysis",
            column_names=[
                "request_id",
                "zone_id",
                "profile_analysis_id",
                "azimuth_deg",
                "distance_m",
                "boom_elevation_m",
                "terrain_elevation_m",
                "clearance_m",
                "classification",
                "in_valley_node",
            ],
            data=rows,
        )
