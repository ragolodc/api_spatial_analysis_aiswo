from dataclasses import dataclass
from enum import StrEnum
from datetime import datetime
from typing import Any
from uuid import UUID


class PivotKind(StrEnum):
    CIRCULAR = "circular"
    SECTORIAL = "sectorial"


class ProfileType(StrEnum):
    """Discriminates between ring-shaped (transverse) and radial (longitudinal) profiles."""

    TRANSVERSE = "transverse"
    LONGITUDINAL = "longitudinal"


class ProfileAnalysisJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class ProfileAnalysisJobRequest:
    request_id: UUID
    zone_id: UUID
    payload: dict[str, Any]


@dataclass(frozen=True)
class ProfileAnalysisInput:
    zone_id: UUID
    pivot_kind: PivotKind
    center_lon: float
    center_lat: float
    radii_m: tuple[float, ...]
    transverse_spacing_m: float
    longitudinal_spacing_m: float
    angular_spacing_deg: float
    start_angle_deg: float | None = None
    end_angle_deg: float | None = None


@dataclass(frozen=True)
class ProfileSamplePoint:
    longitude: float
    latitude: float
    distance_m: float
    radius_m: float
    angle_deg: float
    elevation_m: float | None = None


@dataclass(frozen=True)
class TransverseProfile:
    radius_m: float
    points: list[ProfileSamplePoint]


@dataclass(frozen=True)
class LongitudinalProfile:
    azimuth_deg: float
    points: list[ProfileSamplePoint]


@dataclass(frozen=True)
class ProfileAnalysisResult:
    request_id: UUID
    zone_id: UUID
    provider: str
    resolution_m: float
    transverse_profiles: list[TransverseProfile]
    longitudinal_profiles: list[LongitudinalProfile]
    total_points: int


@dataclass(frozen=True)
class ProfileAnalysisAnalytics:
    request_id: UUID
    total_points: int
    min_elevation_m: float | None
    max_elevation_m: float | None
    avg_elevation_m: float | None


@dataclass(frozen=True)
class ProfilePointRow:
    profile_type: ProfileType
    profile_key: str
    point_index: int
    radius_m: float
    angle_deg: float
    distance_m: float
    longitude: float
    latitude: float
    elevation_m: float | None


@dataclass(frozen=True)
class ProfileSummaryEntry:
    profile_type: ProfileType
    profile_key: str
    total_points: int
    min_elevation_m: float | None
    max_elevation_m: float | None
    avg_elevation_m: float | None


@dataclass(frozen=True)
class ProfileAnalysisJob:
    request_id: UUID
    zone_id: UUID
    status: ProfileAnalysisJobStatus
    payload: dict[str, Any]
    result_payload: dict[str, Any] | None
    error_message: str | None
    queued_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
