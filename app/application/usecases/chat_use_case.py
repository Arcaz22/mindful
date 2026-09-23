import logging
import re
from uuid import uuid4

from app.domain.llm.exceptions import ChatLimitExceededException
from app.domain.chat.chat_repository_port import ChatRepositoryPort
from app.infrastructure.ai.medical_guardrail import MedicalRedFlagGuardrail
from app.infrastructure.ai.source_research import TavilySearchError, TavilySourceResearch


logger = logging.getLogger(__name__)


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
        source_research: TavilySourceResearch | None = None,
        medical_guardrail: MedicalRedFlagGuardrail | None = None,
    ):
        self.repo = repo
        self.llm = llm
        self.max_free_chat_limit = max_free_chat_limit
        self.source_research = source_research
        self.medical_guardrail = medical_guardrail or MedicalRedFlagGuardrail()

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

    def _build_medical_guardrail_response(
        self, remaining_chats: int, assessment
    ) -> dict:
        urgency = "Ini dapat merupakan keadaan darurat. " if assessment.requires_immediate_help else ""
        return {
            "answer": (
                f"{urgency}{assessment.recommended_action} "
                "Saya tidak akan memberikan rekomendasi obat personal melalui chat."
            ),
            "model_used": "medical-guardrail",
            "remaining_chats": remaining_chats,
            "context_ids": [],
        }

    def _build_source_fallback(self, remaining_chats: int) -> dict:
        return {
            "answer": (
                "Maaf, sumber kesehatan tepercaya tidak tersedia saat ini. "
                "Silakan coba lagi nanti atau konsultasikan pertanyaan Anda kepada dokter atau apoteker."
            ),
            "model_used": "tavily-fallback",
            "remaining_chats": remaining_chats,
            "context_ids": [],
        }

    @staticmethod
    def _build_source_context(candidates) -> str:
        return "\n\n---\n\n".join(
            "\n".join(
                [
                    f"SUMBER {index}: {candidate.title}",
                    f"URL: {candidate.url}",
                    f"DOMAIN: {candidate.domain}",
                    f"DIAMBIL: {candidate.retrieved_at.isoformat()}",
                    f"ISI:\n{candidate.content}",
                ]
            )
            for index, candidate in enumerate(candidates, start=1)
        )

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

        assessment = self.medical_guardrail.assess(message)
        if assessment.triggered:
            return self._build_medical_guardrail_response(
                remaining_chats=self._remaining_chats(user.chat_count, user.is_whitelisted),
                assessment=assessment,
            )

        updated_user = await self.repo.increment_usage(user_id, fingerprint=fingerprint)

        if self.source_research is None:
            return self._build_source_fallback(
                self._remaining_chats(updated_user.chat_count, updated_user.is_whitelisted)
            )

        try:
            candidates = await self.source_research.search(message)
        except (TavilySearchError, ValueError):
            return self._build_source_fallback(
                self._remaining_chats(updated_user.chat_count, updated_user.is_whitelisted)
            )

        if not candidates:
            return self._build_source_fallback(
                self._remaining_chats(updated_user.chat_count, updated_user.is_whitelisted)
            )

        context = self._build_source_context(candidates)

        ai_response = await self.llm.ask(message, context)
        audit_method = getattr(self.repo, "save_source_audit", None)
        if audit_method is not None:
            try:
                await audit_method(message, candidates, str(uuid4()))
            except Exception:
                # Audit/cache persistence is optional and must not break chat.
                logger.warning("Gagal menyimpan audit sumber web", exc_info=True)

        return {
            "answer": ai_response.content,
            "model_used": ai_response.model_name,
            "remaining_chats": self._remaining_chats(
                updated_user.chat_count, updated_user.is_whitelisted
            ),
            "context_ids": []
        }
