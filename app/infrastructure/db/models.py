from datetime import datetime
from typing import Optional, List
from sqlalchemy import Text, DateTime, func, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from .base import Base

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[List[float]] = mapped_column(Vector(384), nullable=False)
    metadata_info: Mapped[Optional[str]] = mapped_column(Text)

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
