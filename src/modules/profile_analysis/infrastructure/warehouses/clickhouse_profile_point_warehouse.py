import re
from uuid import UUID

import clickhouse_connect.driver

from src.modules.profile_analysis.domain.entities import (
    ProfileAnalysisAnalytics,
    ProfileAnalysisResult,
    ProfilePointRow,
    ProfileSummaryEntry,
    ProfileType,
)

_MAX_QUERY_LIMIT = 10_000
_SAFE_IDENTIFIER = re.compile(r"^[a-zA-Z0-9_]+$")


class ClickHouseProfilePointWarehouse:
    """ClickHouse adapter for flattened profile-analysis point storage and analytics."""

    def __init__(self, client: clickhouse_connect.driver.Client, database: str) -> None:
        if not _SAFE_IDENTIFIER.match(database):
            raise ValueError(f"Invalid database name: {database!r}")
        self._database = database
        self._client = client

    def __enter__(self) -> "ClickHouseProfilePointWarehouse":
        return self

    def __exit__(self, *args: object) -> None:
        self._client.close()

    def store_result(self, result: ProfileAnalysisResult) -> None:
        rows: list[list] = []

        for profile in result.transverse_profiles:
            for point_index, point in enumerate(profile.points):
                rows.append(
                    [
                        str(result.request_id),
                        str(result.zone_id),
                        ProfileType.TRANSVERSE,
                        f"radius:{profile.radius_m}",
                        point_index,
                        profile.radius_m,
                        point.angle_deg,
                        point.distance_m,
                        point.longitude,
                        point.latitude,
                        point.elevation_m,
                        str(result.source_id),
                    ]
                )

        for profile in result.longitudinal_profiles:
            for point_index, point in enumerate(profile.points):
                rows.append(
                    [
                        str(result.request_id),
                        str(result.zone_id),
                        ProfileType.LONGITUDINAL,
                        f"azimuth:{profile.azimuth_deg}",
                        point_index,
                        point.radius_m,
                        profile.azimuth_deg,
                        point.distance_m,
                        point.longitude,
                        point.latitude,
                        point.elevation_m,
                        str(result.source_id),
                    ]
                )

        if rows:
            self._client.insert(
                f"{self._database}.profile_analysis_points",
                rows,
                column_names=[
                    "request_id",
                    "zone_id",
                    "profile_type",
                    "profile_key",
                    "point_index",
                    "radius_m",
                    "angle_deg",
                    "distance_m",
                    "longitude",
                    "latitude",
                    "elevation_m",
                    "source_id",
                ],
            )

    def get_analytics(self, request_id: UUID) -> ProfileAnalysisAnalytics | None:
        row = self._client.query(
            f"""
            SELECT
                count() AS total_points,
                min(elevation_m) AS min_elevation_m,
                max(elevation_m) AS max_elevation_m,
                avg(elevation_m) AS avg_elevation_m
            FROM {self._database}.profile_analysis_points
            WHERE request_id = %(request_id)s
            """,
            parameters={"request_id": str(request_id)},
        ).first_row

        if row is None or row[0] == 0:
            return None

        return ProfileAnalysisAnalytics(
            request_id=request_id,
            total_points=int(row[0]),
            min_elevation_m=float(row[1]) if row[1] is not None else None,
            max_elevation_m=float(row[2]) if row[2] is not None else None,
            avg_elevation_m=float(row[3]) if row[3] is not None else None,
        )

    def get_points(
        self,
        request_id: UUID,
        profile_type: ProfileType | None,
        limit: int,
        offset: int,
    ) -> list[ProfilePointRow]:
        where = "WHERE request_id = %(request_id)s"
        params: dict = {"request_id": str(request_id)}
        if profile_type:
            where += " AND profile_type = %(profile_type)s"
            params["profile_type"] = profile_type

        rows = self._client.query(
            f"""
            SELECT
                profile_type, profile_key, point_index,
                radius_m, angle_deg, distance_m,
                longitude, latitude, elevation_m
            FROM {self._database}.profile_analysis_points
            {where}
            ORDER BY profile_type, profile_key, point_index
            LIMIT %(limit)s OFFSET %(offset)s
            """,
            parameters={**params, "limit": limit, "offset": offset},
        ).result_rows

        return [
            ProfilePointRow(
                profile_type=ProfileType(r[0]),
                profile_key=r[1],
                point_index=r[2],
                radius_m=r[3],
                angle_deg=r[4],
                distance_m=r[5],
                longitude=r[6],
                latitude=r[7],
                elevation_m=float(r[8]) if r[8] is not None else None,
            )
            for r in rows
        ]

    def get_profile_summaries(self, request_id: UUID) -> list[ProfileSummaryEntry]:
        rows = self._client.query(
            f"""
            SELECT
                profile_type,
                profile_key,
                count() AS total_points,
                min(elevation_m) AS min_elevation_m,
                max(elevation_m) AS max_elevation_m,
                avg(elevation_m) AS avg_elevation_m
            FROM {self._database}.profile_analysis_points
            WHERE request_id = %(request_id)s
            GROUP BY profile_type, profile_key
            ORDER BY profile_type, profile_key
            """,
            parameters={"request_id": str(request_id)},
        ).result_rows

        return [
            ProfileSummaryEntry(
                profile_type=ProfileType(r[0]),
                profile_key=r[1],
                total_points=int(r[2]),
                min_elevation_m=float(r[3]) if r[3] is not None else None,
                max_elevation_m=float(r[4]) if r[4] is not None else None,
                avg_elevation_m=float(r[5]) if r[5] is not None else None,
            )
            for r in rows
        ]
