from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AISWO Spatial Analysis API"
    env: str = "local"
    database_url: str = "postgresql+psycopg2://spatial_user:spatial_password@db:5432/spatial_analysis"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
