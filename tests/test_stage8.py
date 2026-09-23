import unittest
from types import SimpleNamespace

from pydantic import ValidationError

from app.application.usecases.chat_use_case import ChatUsecase
from app.infrastructure.ai.medical_guardrail import MedicalRedFlagGuardrail
from app.infrastructure.ai.medical_response import MedicalResponse
from app.infrastructure.ai.source_policy import (
    SourcePolicy,
    SourcePolicyViolation,
    content_fingerprint,
)
from app.infrastructure.ai.source_research import TavilySourceResearch


class FakeSearch:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error

    def invoke(self, payload):
        if self.error:
            raise self.error
        return self.result


class FakeRepository:
    def __init__(self):
        self.user = SimpleNamespace(chat_count=0, is_whitelisted=False)
        self.audit_calls = []

    async def get_user_status(self, user_id, fingerprint=None):
        return self.user

    async def increment_usage(self, user_id, fingerprint=None):
        self.user.chat_count += 1
        return self.user

    async def save_source_audit(self, query, candidates, response_id):
        self.audit_calls.append((query, candidates, response_id))


class FakeLLM:
    model_name = "test-model"

    async def ask(self, prompt, context):
        return SimpleNamespace(content="jawaban tervalidasi", model_name=self.model_name)


def valid_result():
    return {
        "results": [
            {
                "title": "Trusted health guidance",
                "url": "https://www.who.int/health-topics/medication-safety",
                "content": (
                    "This source provides evidence based information for patients and health "
                    "professionals about safe medication use and risks across common situations."
                ),
            }
        ]
    }


class SourcePolicyTests(unittest.TestCase):
    def test_rejects_untrusted_and_non_https_sources(self):
        policy = SourcePolicy(["who.int"])
        for url in ("http://www.who.int/page", "https://example.com/page"):
            with self.assertRaises((SourcePolicyViolation, ValidationError)):
                policy.candidate_from_result(
                    {"title": "Source", "url": url, "content": "valid content " * 10}
                )

    def test_fingerprint_normalizes_whitespace(self):
        self.assertEqual(
            content_fingerprint("A  source\ntext"), content_fingerprint("a source text")
        )


class TavilyResearchTests(unittest.IsolatedAsyncioTestCase):
    async def test_filters_invalid_sources(self):
        service = TavilySourceResearch(
            api_key=None,
            trusted_domains=["who.int"],
            search_client=FakeSearch(valid_result()),
        )
        results = await service.search("medication safety")
        self.assertEqual(len(results), 1)

    async def test_provider_failure_is_translated(self):
        service = TavilySourceResearch(
            api_key=None,
            trusted_domains=["who.int"],
            search_client=FakeSearch(error=RuntimeError("429 rate limit")),
        )
        with self.assertRaisesRegex(RuntimeError, "Tavily search gagal"):
            await service.search("medication safety")


class GuardrailTests(unittest.TestCase):
    def test_red_flags(self):
        guardrail = MedicalRedFlagGuardrail()
        emergency = guardrail.assess("Saya sesak napas")
        child = guardrail.assess("Berapa dosis untuk anak saya?")
        self.assertTrue(emergency.requires_immediate_help)
        self.assertIn("anak atau bayi", child.flags)


class StructuredOutputTests(unittest.TestCase):
    def test_invalid_structured_response_is_rejected(self):
        with self.assertRaises(ValidationError):
            MedicalResponse(
                answer="Anda menderita penyakit tertentu.",
                sources=["https://www.who.int/"],
                recommended_next_step="Konsultasi.",
                confidence=0.5,
            )

    def test_valid_response_contains_source(self):
        response = MedicalResponse(
            answer="Informasi umum tersedia.",
            sources=["https://www.who.int/"],
            recommended_next_step="Konsultasikan kondisi spesifik.",
            confidence=0.8,
        )
        self.assertIn("https://www.who.int/", response.to_text())


class ChatUsecaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_chat_uses_web_context_and_keeps_response_contract(self):
        repository = FakeRepository()
        research = TavilySourceResearch(
            api_key=None,
            trusted_domains=["who.int"],
            search_client=FakeSearch(valid_result()),
        )
        usecase = ChatUsecase(repository, FakeLLM(), source_research=research)

        result = await usecase.execute("user-1", "Apa informasi umumnya?")

        self.assertEqual(
            set(result), {"answer", "model_used", "remaining_chats", "context_ids"}
        )
        self.assertEqual(result["context_ids"], [])
        self.assertEqual(len(repository.audit_calls), 1)


if __name__ == "__main__":
    unittest.main()
