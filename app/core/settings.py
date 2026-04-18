from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str
    LOG_LEVEL: str
    DATABASE_URL: str
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_VECTOR_SIZE: int = 384
    DATA_PREP_MODEL: str = "llama3.1:8b"
    KNOWLEDGE_CSV_PATH: str = "data/anxiety_knowledge.csv"
    RAW_SOURCE_DIR: str = "data/raw_sources"
    RETRIEVAL_TOP_K: int = 3
    RETRIEVAL_MAX_DISTANCE: float | None = None

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
