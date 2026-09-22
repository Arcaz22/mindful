import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator


class SourcePolicyViolation(ValueError):
    """Raised when a web source cannot be trusted for downstream processing."""


class SourceCandidate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1)
    url: AnyHttpUrl
    domain: str = Field(min_length=1)
    retrieved_at: datetime
    published_at: datetime | None = None

    @field_validator("url")
    @classmethod
    def require_https(cls, url: AnyHttpUrl) -> AnyHttpUrl:
        if url.scheme != "https":
            raise ValueError("URL sumber harus menggunakan HTTPS")
        return url


class SourcePolicy:
    """Allowlist and provenance checks for sources returned by web search."""

    PROMOTIONAL_PATTERNS = (
        r"\bbuy now\b",
        r"\border now\b",
        r"\bshop now\b",
        r"\bpromo(?:tion)?\b",
        r"\bdiscount\b",
        r"\bfree shipping\b",
        r"\bklik untuk membeli\b",
        r"\bbeli sekarang\b",
        r"\bdiskon\b",
    )
    BLOCKED_HOST_MARKERS = (
        "forum",
        "marketplace",
        "reddit.com",
        "quora.com",
        "blogspot.",
        "wordpress.com",
    )

    def __init__(self, trusted_domains: list[str] | tuple[str, ...]):
        self.trusted_domains = {
            self._normalize_domain(domain) for domain in trusted_domains if domain.strip()
        }
        if not self.trusted_domains:
            raise ValueError("Trusted source domain tidak boleh kosong")

    @staticmethod
    def _normalize_domain(domain: str) -> str:
        normalized = domain.strip().lower()
        if "://" in normalized:
            normalized = urlparse(normalized).hostname or ""
        normalized = normalized.removeprefix("www.")
        return normalized.rstrip(".")

    @classmethod
    def domain_from_url(cls, url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise SourcePolicyViolation("URL sumber harus HTTPS dan memiliki hostname")
        return cls._normalize_domain(parsed.hostname)

    def is_domain_allowed(self, domain: str) -> bool:
        normalized = self._normalize_domain(domain)
        return any(
            normalized == trusted or normalized.endswith(f".{trusted}")
            for trusted in self.trusted_domains
        )

    def validate(self, candidate: SourceCandidate) -> SourceCandidate:
        actual_domain = self.domain_from_url(str(candidate.url))
        if actual_domain != self._normalize_domain(candidate.domain):
            raise SourcePolicyViolation("Domain kandidat tidak cocok dengan URL")
        if not self.is_domain_allowed(actual_domain):
            raise SourcePolicyViolation(f"Domain sumber tidak diizinkan: {actual_domain}")
        if any(marker in actual_domain for marker in self.BLOCKED_HOST_MARKERS):
            raise SourcePolicyViolation(f"Domain sumber tidak tepercaya: {actual_domain}")

        text = f"{candidate.title}\n{candidate.content}"
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in self.PROMOTIONAL_PATTERNS):
            raise SourcePolicyViolation("Konten promosi tidak boleh menjadi sumber medis")
        if len(candidate.content.split()) < 20:
            raise SourcePolicyViolation("Isi sumber terlalu pendek untuk diverifikasi")
        return candidate

    def candidate_from_result(self, result: dict) -> SourceCandidate:
        url = result.get("url")
        title = (result.get("title") or "").strip()
        content = (result.get("content") or result.get("raw_content") or "").strip()
        if not url or not title or not content:
            raise SourcePolicyViolation("Sumber wajib memiliki URL, judul, dan isi")

        domain = self.domain_from_url(url)
        published_at = result.get("published_date") or result.get("published_at")
        candidate = SourceCandidate(
            title=title,
            content=content,
            url=url,
            domain=domain,
            retrieved_at=datetime.now(timezone.utc),
            published_at=published_at,
        )
        return self.validate(candidate)
