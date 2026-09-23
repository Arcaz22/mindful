from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str
    LOG_LEVEL: str
    DATABASE_URL: str
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    TAVILY_API_KEY: str | None = None
    TAVILY_MAX_RESULTS: int = 5
    TAVILY_SEARCH_DEPTH: str = "advanced"
    TAVILY_TIMEOUT_SECONDS: float = 20.0
    TRUSTED_SOURCE_DOMAINS: list[str] = [
        "who.int",
        "nhs.uk",
        "mayoclinic.org",
        "nimh.nih.gov",
        "kemkes.go.id",
    ]
    REQUIRE_SOURCE_APPROVAL: bool = True

    MAX_FREE_CHAT_LIMIT: int
    ALLOWED_MODELS: str

    SUPER_USERS: list[str]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra='ignore'


@lru_cache
def get_settings() -> Settings:
    return Settings()
