import re
from typing import Any
from uuid import UUID

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

    def get_result_payload(self, request_id: UUID) -> dict[str, Any] | None:
        request_id_str = str(request_id)

        longitudinal_rows = self._client.query(
            f"""
            SELECT azimuth_deg, span_index, radius_start_m, radius_end_m,
                   slope_pct, slope_deg, service_weight, classification
            FROM {self._database}.longitudinal_slope_analysis
            WHERE request_id = %(request_id)s
            ORDER BY azimuth_deg, span_index
            LIMIT {_MAX_QUERY_LIMIT}
            """,
            parameters={"request_id": request_id_str},
        ).result_rows

        transversal_rows = self._client.query(
            f"""
            SELECT radius_m, azimuth_from_deg, azimuth_to_deg, arc_length_m,
                   slope_pct, slope_deg, classification
            FROM {self._database}.transversal_slope_analysis
            WHERE request_id = %(request_id)s
            ORDER BY radius_m, azimuth_from_deg, azimuth_to_deg
            LIMIT {_MAX_QUERY_LIMIT}
            """,
            parameters={"request_id": request_id_str},
        ).result_rows

        torsional_rows = self._client.query(
            f"""
            SELECT azimuth_deg, span_index, radius_start_m, radius_end_m,
                   alpha_inner_pct, alpha_inner_deg, alpha_outer_pct, alpha_outer_deg,
                   torsion_pct, torsion_deg, longitudinal_slope_pct, longitudinal_slope_deg,
                   combined_load_index, classification
            FROM {self._database}.torsional_slope_analysis
            WHERE request_id = %(request_id)s
            ORDER BY azimuth_deg, span_index
            LIMIT {_MAX_QUERY_LIMIT}
            """,
            parameters={"request_id": request_id_str},
        ).result_rows

        structural_node_rows = self._client.query(
            f"""
            SELECT azimuth_deg, tower_index, radius_m,
                   slope_in_pct, slope_in_deg, slope_out_pct, slope_out_deg,
                   delta_pct, delta_deg, node_kind, classification,
                   valley_double_check, left_force_kN, right_force_kN, internal_force_kN,
                   force_type, safety_factor, is_critical
            FROM {self._database}.structural_stress_nodes
            WHERE request_id = %(request_id)s
            ORDER BY azimuth_deg, tower_index
            LIMIT {_MAX_QUERY_LIMIT}
            """,
            parameters={"request_id": request_id_str},
        ).result_rows

        structural_run_rows = self._client.query(
            f"""
            SELECT azimuth_deg, run_kind, span_indices, cumulative_slope_pct
            FROM {self._database}.structural_stress_runs
            WHERE request_id = %(request_id)s
            ORDER BY azimuth_deg
            LIMIT {_MAX_QUERY_LIMIT}
            """,
            parameters={"request_id": request_id_str},
        ).result_rows

        crop_rows = self._client.query(
            f"""
            SELECT azimuth_deg, distance_m, boom_elevation_m, terrain_elevation_m,
                   clearance_m, classification, in_valley_node
            FROM {self._database}.crop_clearance_analysis
            WHERE request_id = %(request_id)s
            ORDER BY azimuth_deg, distance_m
            LIMIT {_MAX_QUERY_LIMIT}
            """,
            parameters={"request_id": request_id_str},
        ).result_rows

        has_any_data = any(
            [
                longitudinal_rows,
                transversal_rows,
                torsional_rows,
                structural_node_rows,
                structural_run_rows,
                crop_rows,
            ]
        )
        if not has_any_data:
            return None

        return {
            "request_id": request_id_str,
            "longitudinal_slope_analysis": {
                "request_id": request_id_str,
                "spans": [
                    {
                        "azimuth_deg": float(r[0]),
                        "span_index": int(r[1]),
                        "radius_start_m": float(r[2]),
                        "radius_end_m": float(r[3]),
                        "slope": {"pct": float(r[4]), "deg": float(r[5])},
                        "service_weight": float(r[6]),
                        "classification": r[7],
                    }
                    for r in longitudinal_rows
                ],
            },
            "transversal_slope_analysis": {
                "request_id": request_id_str,
                "points": [
                    {
                        "radius_m": float(r[0]),
                        "azimuth_from_deg": float(r[1]),
                        "azimuth_to_deg": float(r[2]),
                        "arc_length_m": float(r[3]),
                        "slope": {"pct": float(r[4]), "deg": float(r[5])},
                        "classification": r[6],
                    }
                    for r in transversal_rows
                ],
            },
            "torsional_slope_analysis": {
                "request_id": request_id_str,
                "spans": [
                    {
                        "azimuth_deg": float(r[0]),
                        "span_index": int(r[1]),
                        "radius_start_m": float(r[2]),
                        "radius_end_m": float(r[3]),
                        "alpha_inner": {"pct": float(r[4]), "deg": float(r[5])},
                        "alpha_outer": {"pct": float(r[6]), "deg": float(r[7])},
                        "torsion": {"pct": float(r[8]), "deg": float(r[9])},
                        "longitudinal_slope": {"pct": float(r[10]), "deg": float(r[11])},
                        "combined_load_index": float(r[12]),
                        "classification": r[13],
                    }
                    for r in torsional_rows
                ],
            },
            "structural_stress_analysis": {
                "request_id": request_id_str,
                "nodes": [
                    {
                        "azimuth_deg": float(r[0]),
                        "tower_index": int(r[1]),
                        "radius_m": float(r[2]),
                        "slope_in": {"pct": float(r[3]), "deg": float(r[4])},
                        "slope_out": {"pct": float(r[5]), "deg": float(r[6])},
                        "delta": {"pct": float(r[7]), "deg": float(r[8])},
                        "node_kind": r[9],
                        "classification": r[10],
                        "valley_double_check": bool(r[11]),
                        "left_force_kN": float(r[12]),
                        "right_force_kN": float(r[13]),
                        "internal_force_kN": float(r[14]),
                        "force_type": r[15],
                        "safety_factor": float(r[16]),
                        "is_critical": bool(r[17]),
                    }
                    for r in structural_node_rows
                ],
                "runs": [
                    {
                        "azimuth_deg": float(r[0]),
                        "run_kind": r[1],
                        "span_indices": [
                            int(v) for v in str(r[2]).split(",") if str(r[2]).strip() and v
                        ],
                        "cumulative_slope_pct": float(r[3]),
                    }
                    for r in structural_run_rows
                ],
            },
            "crop_clearance_analysis": {
                "request_id": request_id_str,
                "points": [
                    {
                        "azimuth_deg": float(r[0]),
                        "distance_m": float(r[1]),
                        "boom_elevation_m": float(r[2]),
                        "terrain_elevation_m": float(r[3]),
                        "clearance_m": float(r[4]),
                        "classification": r[5],
                        "in_valley_node": bool(r[6]),
                    }
                    for r in crop_rows
                ],
            },
        }
