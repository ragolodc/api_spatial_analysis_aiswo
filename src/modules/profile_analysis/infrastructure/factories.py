"""Dependency injection factories for profile analysis module."""

from fastapi import Depends
from sqlalchemy.orm import Session

from src.modules.profile_analysis.application import (
    GetProfileAnalysisAnalytics,
    GetProfileAnalysisJob,
    GetProfileAnalysisPoints,
    GetProfileAnalysisSummary,
)
from src.modules.profile_analysis.application.commands import (
    PersistProfileAnalysisJob,
    PersistProfileAnalysisPoints,
    QueueProfileAnalysis,
    RunProfileAnalysis,
)
from src.modules.profile_analysis.application.services import SampleProfileElevations
from src.modules.profile_analysis.infrastructure.dispatchers import (
    CeleryProfileAnalysisDispatcher,
)
from src.modules.profile_analysis.infrastructure.persistence import (
    SQLAlchemyProfileAnalysisJobRepository,
)
from src.modules.profile_analysis.infrastructure.providers import (
    PlanetaryComputerProfileElevationProvider,
)
from src.modules.profile_analysis.infrastructure.warehouses import (
    ClickHouseProfilePointWarehouse,
)
from src.shared.config import settings
from src.shared.db.session import get_db
from src.shared.domain import ElevationSourceNotConfigured, ElevationSourceReader


def get_profile_analysis_job_repository(db: Session) -> SQLAlchemyProfileAnalysisJobRepository:
    return SQLAlchemyProfileAnalysisJobRepository(db)


def get_profile_analysis_point_warehouse() -> ClickHouseProfilePointWarehouse:
    return ClickHouseProfilePointWarehouse(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
        database=settings.clickhouse_database,
    )


def get_persist_profile_analysis_job(db: Session) -> PersistProfileAnalysisJob:
    return PersistProfileAnalysisJob(repository=get_profile_analysis_job_repository(db))


def get_persist_profile_analysis_points() -> PersistProfileAnalysisPoints:
    return PersistProfileAnalysisPoints(warehouse=get_profile_analysis_point_warehouse())


def get_profile_elevation_provider(
    source_reader: ElevationSourceReader,
) -> PlanetaryComputerProfileElevationProvider:
    source = source_reader.find_active()
    if source is None:
        raise ElevationSourceNotConfigured("No active elevation source configured")
    if not source.source_url or not source.collection:
        raise ElevationSourceNotConfigured(
            "Active elevation source is missing catalog_url or collection"
        )
    return PlanetaryComputerProfileElevationProvider(
        catalog_url=source.source_url,
        collection=source.collection,
        source_id=source.id,
    )


def get_run_profile_analysis(
    db: Session, source_reader: ElevationSourceReader
) -> RunProfileAnalysis:
    return RunProfileAnalysis(
        elevation_sampler=SampleProfileElevations(get_profile_elevation_provider(source_reader))
    )


def get_queue_profile_analysis(db: Session = Depends(get_db)) -> QueueProfileAnalysis:
    return QueueProfileAnalysis(
        dispatcher=CeleryProfileAnalysisDispatcher(),
        persist_job=get_persist_profile_analysis_job(db),
    )


def get_get_profile_analysis_job(db: Session = Depends(get_db)) -> GetProfileAnalysisJob:
    return GetProfileAnalysisJob(repository=get_profile_analysis_job_repository(db))


def get_get_profile_analysis_analytics() -> GetProfileAnalysisAnalytics:
    return GetProfileAnalysisAnalytics(warehouse=get_profile_analysis_point_warehouse())


def get_get_profile_analysis_points() -> GetProfileAnalysisPoints:
    return GetProfileAnalysisPoints(warehouse=get_profile_analysis_point_warehouse())


def get_get_profile_analysis_summary() -> GetProfileAnalysisSummary:
    return GetProfileAnalysisSummary(warehouse=get_profile_analysis_point_warehouse())
