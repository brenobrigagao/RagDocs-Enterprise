from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    app_env: str = "development"
    log_level: str = "INFO"

    # --- Postgres ---
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # --- Groq (LLM) ---
    groq_api_key: str = ""
    groq_model_primary: str = "llama-3.3-70b-versatile"
    groq_model_fallback: str = "llama-3.1-8b-instant"

    # --- Observabilidade ---
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://langfuse:3000"
    langsmith_api_key: str = ""
    langsmith_project: str = "ragdocs-enterprise"

    # --- Fontes externas ---
    confluence_url: str = ""
    confluence_token: str = ""
    notion_token: str = ""

    # --- Segurança ---
    api_auth_mode: str = "api_key"
    api_key: str = ""

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
