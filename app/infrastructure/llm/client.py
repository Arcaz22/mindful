import re
from datetime import datetime
from typing import Any, List

import httpx
from langchain_ollama import ChatOllama
from pydantic import ValidationError

from app.domain.llm.exceptions import (
    LLMOutputValidationException,
    LLMProviderUnavailableException,
)
from app.domain.llm.entities import LLMChatResponse
from app.domain.llm.ports import LLMPort
from app.infrastructure.ai.medical_response import MedicalResponse
from app.infrastructure.embeddings.hf_embedding import HuggingFaceEmbedding

class LLMClient(LLMPort):
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "llama3.1:8b",
        embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        embedding_vector_size: int = 384,
    ):
        self.base_url = base_url
        self.model_name = model_name
        self.embedding_vector_size = embedding_vector_size
        self.embed_model = HuggingFaceEmbedding(embedding_model_name)
        self.timeout = httpx.Timeout(120.0, connect=10.0)
        self.chat_model = ChatOllama(
            base_url=self.base_url,
            model=self.model_name,
            temperature=0.3,
            top_p=0.9,
            client_kwargs={"timeout": 120.0},
        )
        self.structured_chat_model = self.chat_model.with_structured_output(
            MedicalResponse
        )

    def generate_embedding(self, text: str) -> List[float]:
        embedding = self.embed_model.generate_embedding(text)
        if len(embedding) != self.embedding_vector_size:
            raise ValueError(
                f"Dimensi embedding tidak cocok. Expected={self.embedding_vector_size}, got={len(embedding)}"
            )
        return embedding

    def _clean_response(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text

    async def check_connection(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0)) as client:
            try:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                return {
                    "ok": True,
                    "base_url": self.base_url,
                    "models": [model.get("name") for model in data.get("models", [])],
                }
            except Exception as exc:
                return {
                    "ok": False,
                    "base_url": self.base_url,
                    "models": [],
                    "error": str(exc),
                }

    async def ask(self, prompt: str, context: str) -> LLMChatResponse:
        full_prompt = f"""Anda adalah asisten informasi kesehatan digital yang empati dan grounded.
Gunakan KONTEKS berikut untuk menjawab pertanyaan USER.

ATURAN:
1. Jawab berdasarkan KONTEKS yang diberikan.
2. Jika jawaban tidak ada di KONTEKS, nyatakan bahwa informasi tidak ditemukan.
3. Jangan pernah mengarang data medis, nama orang, atau URL sumber.
4. Sertakan setidaknya satu URL HTTPS yang benar-benar ada di KONTEKS.
5. Jangan mendiagnosis, meresepkan obat, memberikan dosis personal, atau menyarankan penghentian obat.
6. Untuk kondisi berisiko, isi red_flags dan arahkan pengguna ke tenaga kesehatan atau layanan darurat.

KONTEKS:
{context}

PERTANYAAN USER:
{prompt}

JAWABAN HARUS MENGIKUTI SCHEMA STRUCTURED OUTPUT."""

        try:
            response = await self.structured_chat_model.ainvoke(full_prompt)
            if not isinstance(response, MedicalResponse):
                response = MedicalResponse.model_validate(response)

            return LLMChatResponse(
                content=self._clean_response(response.to_text()),
                model_name=self.model_name,
                usage_count=0,
                timestamp=datetime.now(),
                source_context=context,
            )
        except (TimeoutError, httpx.TimeoutException):
            raise LLMProviderUnavailableException("Ollama terlalu lama merespon.")
        except (ValidationError, ValueError, TypeError) as exc:
            raise LLMOutputValidationException(str(exc)) from exc
        except Exception as exc:
            raise LLMProviderUnavailableException(
                f"Koneksi Ollama bermasalah: {str(exc)}"
            ) from exc
