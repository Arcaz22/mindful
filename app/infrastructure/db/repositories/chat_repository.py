from datetime import datetime
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domain.chat.chat_repository_port import ChatRepositoryPort
from app.infrastructure.db.models import UserUsage, KnowledgeBase

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

    async def search_knowledge(
        self,
        vector: List[float],
        limit: int = 3,
        max_distance: float | None = None,
    ) -> dict:
        distance_expr = KnowledgeBase.embedding.l2_distance(vector)
        stmt = (
            select(
                KnowledgeBase.id,
                KnowledgeBase.content,
                distance_expr.label("distance"),
            )
            .order_by(distance_expr)
            .limit(limit)
        )
        if max_distance is not None:
            stmt = stmt.where(distance_expr <= max_distance)

        result = await self.session.execute(stmt)
        rows = result.all()
        ids = [row[0] for row in rows]
        chunks = [row[1] for row in rows]

        return {
            "context": "\n---\n".join(chunks) if chunks else "",
            "ids": ids
        }

    async def save_knowledge(self, content: str, embedding: list, metadata: str = None, fingerprint: str = None):
        new_data = KnowledgeBase(
            content=content,
            embedding=embedding,
            metadata_info=metadata
        )
        self.session.add(new_data)
