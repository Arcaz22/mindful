from abc import ABC, abstractmethod
from typing import List

class ChatRepositoryPort(ABC):
    @abstractmethod
    async def get_user_status(self, user_id: str, fingerprint: str = None):
        pass

    @abstractmethod
    async def increment_usage(self, user_id: str, fingerprint: str = None):
        pass

    @abstractmethod
    async def search_knowledge(
        self,
        vector: List[float],
        limit: int = 3,
        max_distance: float | None = None,
    ) -> dict:
        pass

    @abstractmethod
    async def save_knowledge(self, content: str, embedding: list, metadata: str = None, fingerprint: str = None):
        pass
