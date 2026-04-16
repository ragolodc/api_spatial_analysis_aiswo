from uuid import UUID

import clickhouse_connect

from src.modules.profile_analysis.domain.entities import (
    ProfileAnalysisAnalytics,
    ProfileAnalysisResult,
    ProfilePointRow,
    ProfileSummaryEntry,
)


class ClickHouseProfilePointWarehouse:
    """ClickHouse adapter for flattened profile-analysis point storage and analytics."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
    ) -> None:
        self._database = database
        self._client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=username,
            password=password,
        )
        self._ensure_schema()

    def store_result(self, result: ProfileAnalysisResult) -> None:
        rows: list[list] = []

        for profile in result.transverse_profiles:
            for point_index, point in enumerate(profile.points):
                rows.append([
                    str(result.request_id),
                    str(result.zone_id),
                    "transverse",
                    f"radius:{profile.radius_m}",
                    point_index,
                    profile.radius_m,
                    point.angle_deg,
                    point.distance_m,
                    point.longitude,
                    point.latitude,
                    point.elevation_m,
                    result.provider,
                    result.resolution_m,
                ])

        for profile in result.longitudinal_profiles:
            for point_index, point in enumerate(profile.points):
                rows.append([
                    str(result.request_id),
                    str(result.zone_id),
                    "longitudinal",
                    f"azimuth:{profile.azimuth_deg}",
                    point_index,
                    point.radius_m,
                    profile.azimuth_deg,
                    point.distance_m,
                    point.longitude,
                    point.latitude,
                    point.elevation_m,
                    result.provider,
                    result.resolution_m,
                ])

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
                    "provider",
                    "resolution_m",
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
        profile_type: str | None,
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
                profile_type=r[0],
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
                profile_type=r[0],
                profile_key=r[1],
                total_points=int(r[2]),
                min_elevation_m=float(r[3]) if r[3] is not None else None,
                max_elevation_m=float(r[4]) if r[4] is not None else None,
                avg_elevation_m=float(r[5]) if r[5] is not None else None,
            )
            for r in rows
        ]

    def _ensure_schema(self) -> None:
        self._client.command(f"CREATE DATABASE IF NOT EXISTS {self._database}")
        self._client.command(
            f"""
            CREATE TABLE IF NOT EXISTS {self._database}.profile_analysis_points (
                request_id UUID,
                zone_id UUID,
                profile_type LowCardinality(String),
                profile_key String,
                point_index UInt32,
                radius_m Float64,
                angle_deg Float64,
                distance_m Float64,
                longitude Float64,
                latitude Float64,
                elevation_m Nullable(Float64),
                provider LowCardinality(String),
                resolution_m Float64
            )
            ENGINE = MergeTree
            ORDER BY (request_id, profile_type, profile_key, point_index)
            """
        )
