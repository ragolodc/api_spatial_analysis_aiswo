import clickhouse_connect
from fastapi import Depends
from sqlalchemy.orm import Session

from src.modules.pivot_geometry_analysis.application.commands import (
    PersistSlopeAnalysisJob,
    QueueSlopeAnalysis,
    RunSlopeAnalysis,
)
from src.modules.pivot_geometry_analysis.infrastructure.adapters.clickhouse_profile_reader import (
    ClickHouseProfileReader,
)
from src.modules.pivot_geometry_analysis.infrastructure.dispatchers import (
    CelerySlopeAnalysisDispatcher,
)
from src.modules.pivot_geometry_analysis.infrastructure.persistence.job_repository import (
    SQLAlchemySlopeAnalysisJobRepository,
)
from src.shared.config import settings
from src.shared.db.session import get_db


def get_slope_analysis_job_repository(db: Session) -> SQLAlchemySlopeAnalysisJobRepository:
    return SQLAlchemySlopeAnalysisJobRepository(db)


def get_profile_reader() -> ClickHouseProfileReader:
    client = clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
    )
    return ClickHouseProfileReader(
        ch_client=client, database=settings.clickhouse_database, db=get_db()
    )


def get_persist_slope_analysis_job(db: Session) -> PersistSlopeAnalysisJob:
    return PersistSlopeAnalysisJob(repository=get_slope_analysis_job_repository(db))


def get_run_slope_analysis(db: Session) -> RunSlopeAnalysis:
    return RunSlopeAnalysis(profile_reader=get_profile_reader())


def get_queue_slope_analysis(db: Session = Depends(get_db)) -> QueueSlopeAnalysis:
    return QueueSlopeAnalysis(
        dispatcher=CelerySlopeAnalysisDispatcher(), persist_job=get_persist_slope_analysis_job(db)
    )
