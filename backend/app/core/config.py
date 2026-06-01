from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BidPilot AI"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./bidpilot.db"
    knowledge_chunk_size: int = 120
    rag_retriever_type: str = "simple"
    chroma_persist_dir: str = ".chroma"
    embedding_provider: str = "mock"
    embedding_base_url: str | None = None
    embedding_api_key: str | None = None
    embedding_model_name: str | None = None
    model_config_secret_key: str = "bidpilot-dev-model-config-secret"
    default_provider: str = "mock"
    cors_allow_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
