from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Creditos Carmax"
    environment: str = "local"
    database_url: str = "postgresql+psycopg://creditos:creditos@localhost:5440/creditos"
    cors_origins: str = "http://localhost:4210,http://127.0.0.1:4210"
    auth_secret: str = "change-this-in-production-use-strong-random-key-min-32-chars"
    token_expire_minutes: int = 60  # Reducido de 720 a 60 minutos
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # segundos
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "creditos@localhost"
    smtp_use_tls: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
