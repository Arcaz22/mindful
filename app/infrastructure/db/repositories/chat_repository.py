from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domain.chat.chat_repository_port import ChatRepositoryPort
from app.infrastructure.ai.source_policy import content_fingerprint
from app.infrastructure.db.models import SourceSearchCache, UserUsage

class ChatRepository(ChatRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_status(self, user_id: str, fingerprint: str = None) -> UserUsage:
        stmt = select(UserUsage).where(UserUsage.user_id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        now = datetime.now()

        if user:
            if not user.fingerprint and fingerprint:
                user.fingerprint = fingerprint
                await self.session.commit()
                await self.session.refresh(user)
            if user.last_accessed.date() < now.date():
                user.chat_count = 0
                await self.session.commit()
                await self.session.refresh(user)
        else:
            user = UserUsage(user_id=user_id, chat_count=0, fingerprint=fingerprint)
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)

        return user

    async def increment_usage(self, user_id: str, fingerprint: str = None) -> UserUsage:
        stmt = select(UserUsage).where(UserUsage.user_id == user_id)
        result = await self.session.execute(stmt)
        usage = result.scalar_one_or_none()

        if usage:
            usage.chat_count += 1
            if not usage.fingerprint and fingerprint:
                usage.fingerprint = fingerprint
        else:
            usage = UserUsage(user_id=user_id, chat_count=1, fingerprint=fingerprint)
            self.session.add(usage)

        await self.session.commit()
        await self.session.refresh(usage)
        return usage

    async def save_source_audit(self, query: str, candidates: list, response_id: str) -> None:
        for candidate in candidates:
            self.session.add(
                SourceSearchCache(
                    query=query,
                    source_url=str(candidate.url),
                    source_title=candidate.title,
                    source_domain=candidate.domain,
                    retrieved_at=candidate.retrieved_at,
                    content_hash=content_fingerprint(candidate.content),
                    response_id=response_id,
                )
            )
        await self.session.commit()
