from src.modules.profile_analysis.infrastructure.factories import (
    get_get_profile_analysis_analytics,
    get_get_profile_analysis_job,
    get_get_profile_analysis_points,
    get_get_profile_analysis_summary,
    get_persist_profile_analysis_job,
    get_persist_profile_analysis_points,
    get_queue_profile_analysis,
)


def register_models() -> None:
    import src.modules.profile_analysis.infrastructure.persistence.models  # noqa: F401


def init_clickhouse() -> None:
    """Garantiza que el schema de ClickHouse existe al arrancar."""
    from src.modules.profile_analysis.infrastructure.warehouses import (
        ClickHouseProfilePointWarehouse,
    )
    from src.shared.config import settings

    wh = ClickHouseProfilePointWarehouse(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
        database=settings.clickhouse_database,
    )
    wh._client.close()


__all__ = [
    "get_queue_profile_analysis",
    "get_get_profile_analysis_job",
    "get_get_profile_analysis_analytics",
    "get_get_profile_analysis_points",
    "get_get_profile_analysis_summary",
    "get_persist_profile_analysis_job",
    "get_persist_profile_analysis_points",
    "register_models",
    "init_clickhouse",
]
