import re

from app.domain.llm.exceptions import ChatLimitExceededException
from app.domain.chat.chat_repository_port import ChatRepositoryPort


class ChatUsecase:
    CRISIS_PATTERN = re.compile(
        r"\b("
        r"bunuh\s*diri|akhiri\s*hidup|mengakhiri\s*hidup|self[\s-]?harm|"
        r"melukai\s*diri|sakiti\s*diri|menyakiti\s*diri|"
        r"suicide|kill\s*myself|end\s*my\s*life|hurt\s*myself|overdose|"
        r"tidak\s*ingin\s*hidup|ingin\s*mati|mau\s*mati|pengen\s*mati|"
        r"nyawa\s*saya|hidup\s*saya\s*selesai"
        r")\b",
        re.IGNORECASE,
    )

    def __init__(
        self,
        repo: ChatRepositoryPort,
        llm,
        max_free_chat_limit: int = 3,
        retrieval_top_k: int = 3,
        retrieval_max_distance: float | None = None,
    ):
        self.repo = repo
        self.llm = llm
        self.max_free_chat_limit = max_free_chat_limit
        self.retrieval_top_k = retrieval_top_k
        self.retrieval_max_distance = retrieval_max_distance

    def _is_high_risk_message(self, message: str) -> bool:
        return bool(self.CRISIS_PATTERN.search(message))

    def _remaining_chats(self, chat_count: int, is_whitelisted: bool) -> int:
        if is_whitelisted:
            return 999
        return max(0, self.max_free_chat_limit - chat_count)

    def _build_guardrail_response(self, remaining_chats: int) -> dict:
        return {
            "answer": (
                "Maaf, saya tidak bisa membantu instruksi untuk menyakiti diri sendiri atau bunuh diri. "
                "Kalau Anda sedang dalam bahaya atau merasa mungkin bertindak sekarang, segera hubungi layanan darurat setempat sekarang juga. "
                "Jika Anda berada di Indonesia, hubungi 119 ext 8 untuk SEJIWA. "
                "Jika Anda berada di AS atau Kanada, hubungi atau SMS 988. "
                "Jika memungkinkan, segera beri tahu orang terdekat yang Anda percaya agar tidak sendirian."
            ),
            "model_used": "guardrail",
            "remaining_chats": remaining_chats,
            "context_ids": [],
        }

    async def execute(self, user_id: str, message: str, fingerprint: str = None):
        user = await self.repo.get_user_status(user_id, fingerprint=fingerprint)
        if not user.is_whitelisted and user.chat_count >= self.max_free_chat_limit:
            raise ChatLimitExceededException(
                message=f"Batas percobaan gratis ({self.max_free_chat_limit}x) telah tercapai."
            )

        if self._is_high_risk_message(message):
            return self._build_guardrail_response(
                remaining_chats=self._remaining_chats(user.chat_count, user.is_whitelisted)
            )

        query_vector = self.llm.generate_embedding(message)
        result = await self.repo.search_knowledge(
            query_vector,
            limit=self.retrieval_top_k,
            max_distance=self.retrieval_max_distance,
        )
        context = result["context"]
        context_ids = result["ids"]
        updated_user = await self.repo.increment_usage(user_id, fingerprint=fingerprint)

        if not context:
            return {
                "answer": "Maaf, data tidak ditemukan di database.",
                "model_used": "-",
                "remaining_chats": self._remaining_chats(
                    updated_user.chat_count, updated_user.is_whitelisted
                ),
                "context_ids": []
            }

        ai_response = await self.llm.ask(message, context)

        return {
            "answer": ai_response.content,
            "model_used": ai_response.model_name,
            "remaining_chats": self._remaining_chats(
                updated_user.chat_count, updated_user.is_whitelisted
            ),
            "context_ids": context_ids
        }
