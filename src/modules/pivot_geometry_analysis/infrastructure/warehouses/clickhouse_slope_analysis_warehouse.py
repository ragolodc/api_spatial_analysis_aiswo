import re

import clickhouse_connect.driver

from src.modules.pivot_geometry_analysis.domain.entities import (
    LongitudinalSlopeAnalysis,
    SlopeAnalysisJobRequest,
    SlopeAnalysisResult,
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
        self._store_longitudinal_slope_analysis(analysis.longitudinal_slope_analysis, job_request)

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
                "classification",
            ],
            data=rows,
        )
