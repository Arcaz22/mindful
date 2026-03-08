from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str
    LOG_LEVEL: str
    DATABASE_URL: str

    MAX_FREE_CHAT_LIMIT: int
    ALLOWED_MODELS: list[str]

    SUPER_USERS: list[str]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra='ignore'


@lru_cache
def get_settings() -> Settings:
    return Settings()
