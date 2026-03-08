from abc import ABC, abstractmethod

from alembic.environment import List
from .entities import LLMChatResponse

class LLMPort(ABC):
    @abstractmethod
    async def ask(self, prompt: str, context: str) -> LLMChatResponse:
        pass

    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        pass
