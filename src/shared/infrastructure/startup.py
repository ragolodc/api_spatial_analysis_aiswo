from src.modules.profile_analysis.infrastructure.warehouses import ClickHouseProfilePointWarehouse
from src.shared.config import settings
from src.shared.db.base import Base
from src.shared.db.session import engine


def init_db() -> None:
    """Crea todas las tablas SQLAlchemy si no existen."""
    import src.shared.db.registry  # noqa: F401 — registra todos los modelos

    Base.metadata.create_all(bind=engine)


def init_clickhouse() -> None:
    """Garantiza que el schema de ClickHouse existe al arrancar."""
    wh = ClickHouseProfilePointWarehouse(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
        database=settings.clickhouse_database,
    )
    wh._client.close()
