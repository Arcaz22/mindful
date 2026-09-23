from abc import ABC, abstractmethod

class ChatRepositoryPort(ABC):
    @abstractmethod
    async def get_user_status(self, user_id: str, fingerprint: str = None):
        pass

    @abstractmethod
    async def increment_usage(self, user_id: str, fingerprint: str = None):
        pass
