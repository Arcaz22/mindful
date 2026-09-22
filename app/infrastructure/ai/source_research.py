import asyncio
import json
from typing import Any

from langchain_tavily import TavilySearch
from langchain_tavily._utilities import TavilySearchAPIWrapper

from app.infrastructure.ai.source_policy import SourceCandidate, SourcePolicy, SourcePolicyViolation


class TavilySearchError(RuntimeError):
    """Safe, non-provider-specific error for source discovery failures."""

    def __init__(self, message: str, *, kind: str = "provider"):
        super().__init__(message)
        self.kind = kind


class TavilySourceResearch:
    """Search-only Tavily adapter; it never writes to the knowledge base."""

    def __init__(
        self,
        api_key: str | None,
        trusted_domains: list[str] | tuple[str, ...],
        max_results: int = 5,
        search_depth: str = "advanced",
        timeout_seconds: float = 20.0,
        search_client: Any | None = None,
    ):
        api_key = api_key.strip() if api_key else None
        if not api_key and search_client is None:
            raise ValueError("TAVILY_API_KEY wajib diisi untuk source research")
        if max_results < 1 or max_results > 20:
            raise ValueError("TAVILY_MAX_RESULTS harus berada di antara 1 dan 20")
        if timeout_seconds <= 0:
            raise ValueError("TAVILY_TIMEOUT_SECONDS harus lebih besar dari 0")
        if search_depth not in {"basic", "advanced", "fast", "ultra-fast"}:
            raise ValueError("TAVILY_SEARCH_DEPTH tidak valid")

        self.policy = SourcePolicy(trusted_domains)
        self.max_results = max_results
        self.timeout_seconds = timeout_seconds
        self.search_client = search_client if search_client is not None else TavilySearch(
            api_wrapper=TavilySearchAPIWrapper(tavily_api_key=api_key),
            max_results=max_results,
            search_depth=search_depth,
            include_domains=sorted(self.policy.trusted_domains),
            include_raw_content="markdown",
            topic="general",
        )

    async def search(self, query: str) -> list[SourceCandidate]:
        query = query.strip()
        if not query:
            raise ValueError("Query pencarian tidak boleh kosong")
        if len(query) > 500:
            raise ValueError("Query pencarian terlalu panjang")

        try:
            raw_result = await asyncio.wait_for(
                asyncio.to_thread(self.search_client.invoke, {"query": query}),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            raise TavilySearchError("Tavily timeout", kind="timeout") from exc
        except Exception as exc:
            message = str(exc)
            lowered = message.casefold()
            if "401" in lowered or "api key" in lowered or "unauthorized" in lowered:
                kind = "authentication"
            elif "429" in lowered or "rate limit" in lowered or "too many" in lowered:
                kind = "rate_limit"
            else:
                kind = "provider"
            raise TavilySearchError("Tavily search gagal", kind=kind) from exc

        results = self._extract_results(raw_result)
        candidates: list[SourceCandidate] = []
        for result in results[: self.max_results]:
            try:
                candidates.append(self.policy.candidate_from_result(result))
            except (SourcePolicyViolation, ValueError, TypeError):
                continue
        return candidates

    @staticmethod
    def _extract_results(raw_result: Any) -> list[dict[str, Any]]:
        if isinstance(raw_result, str):
            try:
                raw_result = json.loads(raw_result)
            except json.JSONDecodeError:
                return []
        if isinstance(raw_result, dict):
            raw_result = raw_result.get("results", [])
        if not isinstance(raw_result, list):
            return []
        return [item for item in raw_result if isinstance(item, dict)]
