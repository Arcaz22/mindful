from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.chat.chat_repository_port import ChatRepositoryPort
from app.infrastructure.db.session import get_db_session
from app.core.settings import Settings, get_settings

from app.infrastructure.llm.client import LLMClient
from app.infrastructure.ai.source_research import TavilySourceResearch
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
    )

def source_research(settings: Settings = Depends(get_settings)):
    return TavilySourceResearch(
        api_key=settings.TAVILY_API_KEY,
        trusted_domains=settings.TRUSTED_SOURCE_DOMAINS,
        max_results=settings.TAVILY_MAX_RESULTS,
        search_depth=settings.TAVILY_SEARCH_DEPTH,
        timeout_seconds=settings.TAVILY_TIMEOUT_SECONDS,
    )

# ============================================================
# Usecase Providers
# ============================================================

def get_chat_use_case(
    repo: ChatRepository = Depends(chat_repo),
    llm: LLMClient = Depends(llm_client),
    research: TavilySourceResearch = Depends(source_research),
    settings: Settings = Depends(get_settings),
):
    return ChatUsecase(
        repo,
        llm,
        max_free_chat_limit=settings.MAX_FREE_CHAT_LIMIT,
        source_research=research,
    )
