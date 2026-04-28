def register_models() -> None:
    import src.modules.pivot_geometry_analysis.infrastructure.persistence.models  # noqa: F401


def init_clickhouse() -> None:
    """Garantiza que el schema de ClickHouse existe al arrancar."""
    import clickhouse_connect

    from src.modules.pivot_geometry_analysis.infrastructure.warehouses.clickhouse_schema import (
        ensure_schema,
    )
    from src.shared.config import settings

    client = clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
    )
    ensure_schema(client, settings.clickhouse_database)
    client.close()


__all__ = ["init_clickhouse", "register_models"]
