import re
from datetime import datetime
from typing import Any, List

import httpx

from app.domain.llm.exceptions import LLMProviderUnavailableException
from app.domain.llm.entities import LLMChatResponse
from app.domain.llm.ports import LLMPort
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
        full_prompt = f"""Anda adalah asisten psikologi digital yang empati dan grounded.
Gunakan KONTEKS berikut untuk menjawab pertanyaan USER.

ATURAN:
1. Jawab berdasarkan KONTEKS yang diberikan.
2. Jika jawaban tidak ada di KONTEKS, katakan bahwa Anda tidak memiliki informasi spesifik di database, namun berikan saran umum yang bijak sebagai asisten psikologi.
3. Jangan pernah mengarang data medis atau nama orang jika tidak ada di konteks.

KONTEKS:
{context}

PERTANYAAN USER:
{prompt}

JAWABAN:"""

        payload = {
            "model": self.model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9
            }
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()

                raw_content = data['response']
                clean_content = self._clean_response(raw_content)

                return LLMChatResponse(
                    content=clean_content,
                    model_name=self.model_name,
                    usage_count=0,
                    timestamp=datetime.now(),
                    source_context=context
                )
            except httpx.ReadTimeout:
                raise LLMProviderUnavailableException("Ollama terlalu lama merespon.")
            except Exception as e:
                raise LLMProviderUnavailableException(f"Koneksi Ollama bermasalah: {str(e)}")
