from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.chat.chat_repository_port import ChatRepositoryPort
from app.infrastructure.db.session import get_db_session

from app.infrastructure.llm.client import LLMClient
from app.infrastructure.db.repositories.chat_repository import ChatRepository

from app.application.usecases.chat_use_case import ChatUsecase

# ============================================================
# Repository Providers (factory)
# ============================================================

def chat_repo(session: AsyncSession = Depends(get_db_session)) -> ChatRepositoryPort:
    return ChatRepository(session)

def llm_client():
    # Karena LLMClient tidak butuh session DB, kita inisialisasi langsung
    return LLMClient()

# ============================================================
# Usecase Providers
# ============================================================

def get_chat_use_case(
    repo: ChatRepository = Depends(chat_repo),
    llm: LLMClient = Depends(llm_client)
):
    return ChatUsecase(repo, llm)
