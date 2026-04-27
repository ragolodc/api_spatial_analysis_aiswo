from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    app_name: str
    env: str

    # API
    api_host: str
    api_port: int
    uvicorn_workers: int = 1

    # Database
    database_url: str

    # Redis
    redis_host: str
    redis_port: int
    redis_db: int = 0

    # Celery
    celery_broker_url: str
    celery_result_backend: str

    # ClickHouse
    clickhouse_host: str = "clickhouse"
    clickhouse_port: int = 8123
    clickhouse_user: str
    clickhouse_password: str
    clickhouse_database: str

    # Queues (puedes llevarlas a .env si quieres más flexibilidad)
    profile_analysis_queue: str
    slope_analysis_queue: str

    # Domain config
    profile_analysis_max_points: int = 500000

    model_config = SettingsConfigDict(
        env_file=".env",  # opcional si usas docker compose
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
