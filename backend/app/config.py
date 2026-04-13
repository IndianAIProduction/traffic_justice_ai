from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    # Application
    app_name: str = "Traffic Justice AI"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # Attribution (shown in API docs, /health, logs)
    publisher_name: str = "Indian AI Production"
    publisher_url: str = "https://indianaiproduction.com/"
    publisher_youtube_url: str = "https://www.youtube.com/indianaiproduction"

    # OpenAI
    openai_api_key: str = ""

    # PostgreSQL
    postgres_user: str = "traffic_justice"
    postgres_password: str = "changeme"
    postgres_db: str = "traffic_justice_db"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_psycopg(self) -> str:
        """Connection string for psycopg3 (used by LangGraph checkpointer)."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            f"?sslmode=disable"
        )

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    # ChromaDB (container listens on 8000 internally; host-mapped to 8001)
    chroma_host: str = "chromadb"
    chroma_port: int = 8000

    # JWT
    jwt_secret_key: str = "changeme_generate_a_64_char_random_string"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Evidence
    evidence_encryption_key: str = "changeme_generate_a_fernet_key"
    evidence_storage_path: str = "/app/evidence_storage"
    max_upload_size_mb: int = 100

    # SMTP (for complaint email submission)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Traffic Justice AI"
    smtp_use_tls: bool = True

    # CORS
    backend_cors_origins: str = '["http://localhost:3000"]'

    @property
    def cors_origins(self) -> List[str]:
        return json.loads(self.backend_cors_origins)

    # Rate limiting
    rate_limit_per_minute: int = 60

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
