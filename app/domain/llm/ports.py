from abc import ABC, abstractmethod
from .entities import LLMChatResponse

class LLMPort(ABC):
    @abstractmethod
    async def ask(self, prompt: str, context: str) -> LLMChatResponse:
        pass
