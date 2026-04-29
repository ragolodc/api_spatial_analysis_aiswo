from itertools import groupby
from uuid import UUID

import clickhouse_connect.driver
from sqlalchemy.orm import Session

from src.modules.profile_analysis.domain.entities import (
    LongitudinalProfile,
    ProfileSamplePoint,
    TransverseProfile,
)
from src.modules.profile_analysis.infrastructure.persistence.models import ProfileAnalysisJobModel
from src.shared.domain.entities import Spans, SpansConfig


class ClickHouseProfileReader:
    """Implements ProfileReader port reading from ClickHouse + PostgreSQL."""

    def __init__(
        self,
        ch_client: clickhouse_connect.driver.Client,
        database: str,
        db: Session,
    ) -> None:
        self._ch = ch_client
        self._database = database
        self._db = db

    def get_longitudinal_profiles(self, request_id: UUID) -> list[LongitudinalProfile]:
        rows = self._ch.query(
            f"""
            SELECT profile_key, point_index, radius_m, angle_deg, distance_m,
                   longitude, latitude, elevation_m
            FROM {self._database}.profile_analysis_points
            WHERE request_id = %(request_id)s
              AND profile_type = 'longitudinal'
            ORDER BY profile_key, point_index
            """,
            parameters={"request_id": str(request_id)},
        ).result_rows

        profiles: list[LongitudinalProfile] = []
        for profile_key, group in groupby(rows, key=lambda r: r[0]):
            azimuth_deg = float(profile_key.split(":")[1])
            points = [
                ProfileSamplePoint(
                    longitude=float(r[5]),
                    latitude=float(r[6]),
                    distance_m=float(r[4]),
                    radius_m=float(r[2]),
                    angle_deg=float(r[3]),
                    elevation_m=float(r[7]) if r[7] is not None else None,
                )
                for r in group
            ]
            profiles.append(LongitudinalProfile(azimuth_deg=azimuth_deg, points=points))
        return profiles

    def get_transversal_profiles(self, request_id: UUID) -> list[TransverseProfile]:
        rows = self._ch.query(
            f"""
            SELECT profile_key, point_index, radius_m, angle_deg, distance_m,
                   longitude, latitude, elevation_m
            FROM {self._database}.profile_analysis_points
            WHERE request_id = %(request_id)s
              AND profile_type = 'transverse'
            ORDER BY profile_key, point_index
            """,
            parameters={"request_id": str(request_id)},
        ).result_rows

        profiles: list[TransverseProfile] = []
        for profile_key, group in groupby(rows, key=lambda r: r[0]):
            radius_m = float(profile_key.split(":")[1])
            points = [
                ProfileSamplePoint(
                    longitude=float(r[5]),
                    latitude=float(r[6]),
                    distance_m=float(r[4]),
                    radius_m=float(r[2]),
                    angle_deg=float(r[3]),
                    elevation_m=float(r[7]) if r[7] is not None else None,
                )
                for r in group
            ]
            profiles.append(TransverseProfile(radius_m=radius_m, points=points))
        return profiles

    def get_radii_m(self, request_id: UUID) -> tuple[float, ...]:
        model = self._db.get(ProfileAnalysisJobModel, request_id)
        if model is None:
            raise ValueError(f"ProfileAnalysisJob {request_id} not found")
        return tuple(sorted(float(r) for r in model.payload["inputs"]["radii_m"]))

    def get_spans_configurations(self, request_id: UUID) -> SpansConfig:
        model = self._db.get(ProfileAnalysisJobModel, request_id)
        if model is None:
            raise ValueError(f"ProfileAnalysisJob {request_id} not found")
        spans = model.payload["inputs"]["spans"]
        return SpansConfig(spans=[Spans(**span) for span in spans])
