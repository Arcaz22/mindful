from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.chat.chat_repository_port import ChatRepositoryPort
from app.infrastructure.db.session import get_db_session
from app.core.settings import Settings, get_settings

from app.infrastructure.llm.client import LLMClient
from app.infrastructure.db.repositories.chat_repository import ChatRepository

from app.application.usecases.chat_use_case import ChatUsecase

# ============================================================
# Repository Providers (factory)
# ============================================================

def chat_repo(session: AsyncSession = Depends(get_db_session)) -> ChatRepositoryPort:
    return ChatRepository(session)

def llm_client(settings: Settings = Depends(get_settings)):
    return LLMClient(
        base_url=settings.OLLAMA_BASE_URL,
        model_name=settings.OLLAMA_MODEL,
        embedding_model_name=settings.EMBEDDING_MODEL_NAME,
        embedding_vector_size=settings.EMBEDDING_VECTOR_SIZE,
    )

# ============================================================
# Usecase Providers
# ============================================================

def get_chat_use_case(
    repo: ChatRepository = Depends(chat_repo),
    llm: LLMClient = Depends(llm_client),
    settings: Settings = Depends(get_settings),
):
    return ChatUsecase(
        repo,
        llm,
        max_free_chat_limit=settings.MAX_FREE_CHAT_LIMIT,
        retrieval_top_k=settings.RETRIEVAL_TOP_K,
        retrieval_max_distance=settings.RETRIEVAL_MAX_DISTANCE,
    )
