from datetime import datetime
from typing import Optional
from sqlalchemy import Text, DateTime, func, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

class UserUsage(Base):
    __tablename__ = "user_usage"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    chat_count: Mapped[int] = mapped_column(Integer, default=0)

    is_whitelisted: Mapped[bool] = mapped_column(Boolean, default=False)

    last_accessed: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    fingerprint: Mapped[Optional[str]] = mapped_column(String(255))


class SourceSearchCache(Base):
    """Audited web-source snapshot used for cache/audit follow-up."""

    __tablename__ = "source_search_cache"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    query: Mapped[str] = mapped_column(String(500), index=True)
    source_url: Mapped[str] = mapped_column(Text, index=True)
    source_title: Mapped[str] = mapped_column(String(500))
    source_domain: Mapped[str] = mapped_column(String(255), index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    response_id: Mapped[str] = mapped_column(String(64), index=True)
