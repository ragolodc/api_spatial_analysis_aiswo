from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AISWO Spatial Analysis API"
    env: str = "local"
    database_url: str
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"
    clickhouse_host: str = "clickhouse"
    clickhouse_port: int = 8123
    clickhouse_user: str = "default"
    clickhouse_password: str = ""
    clickhouse_database: str = "spatial_analytics"
    profile_analysis_queue: str = "profile_analysis"
    profile_analysis_max_points: int = 500000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
