from src.shared.db.base import Base
from src.shared.db.session import engine


def init_db() -> None:
    """Crea todas las tablas SQLAlchemy si no existen."""
    import src.shared.db.registry  # noqa: F401 — registra todos los modelos

    Base.metadata.create_all(bind=engine)


def init_clickhouse() -> None:
    """Garantiza que el schema de ClickHouse existe al arrancar."""
    from src.modules.profile_analysis.infrastructure import (
        init_clickhouse as _init_clickhouse,
    )

    _init_clickhouse()
