from app.domain.llm.exceptions import ChatLimitExceededException
from app.domain.chat.chat_repository_port import ChatRepositoryPort

class ChatUsecase:
    def __init__(self, repo: ChatRepositoryPort, llm):
        self.repo = repo
        self.llm = llm

    async def execute(self, user_id: str, message: str, fingerprint: str = None):
        user = await self.repo.get_user_status(user_id, fingerprint=fingerprint)
        if not user.is_whitelisted and user.chat_count >= 3:
            raise ChatLimitExceededException()

        query_vector = self.llm.generate_embedding(message)
        result = await self.repo.search_knowledge(query_vector)
        context = result["context"]
        context_ids = result["ids"]
        updated_user = await self.repo.increment_usage(user_id, fingerprint=fingerprint)

        if not context:
            return {
                "answer": "Maaf, data tidak ditemukan di database.",
                "model_used": "-",
                "remaining_chats": 999 if updated_user.is_whitelisted else max(0, 3 - updated_user.chat_count),
                "context_ids": []
            }

        ai_response = await self.llm.ask(message, context)

        metadata = f"fingerprint={fingerprint}" if fingerprint else None

        return {
            "answer": ai_response.content,
            "model_used": ai_response.model_name,
            "remaining_chats": 999 if updated_user.is_whitelisted else max(0, 3 - updated_user.chat_count),
            "context_ids": context_ids
        }
