import asyncio
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.settings import get_settings

settings = get_settings()
OUTPUT_COLUMNS = [
    "id",
    "category",
    "topic",
    "title",
    "content",
    "source_name",
    "source_url",
    "language",
    "tags",
    "last_updated",
]


@dataclass
class SourceDocument:
    metadata: dict[str, str]
    sections: list[tuple[str, str]]


def resolve_path(path_value: str) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_source_document(path: Path) -> SourceDocument:
    raw_text = path.read_text(encoding="utf-8")
    if "\n---\n" not in raw_text:
        raise ValueError(f"{path.name}: format file sumber tidak valid. Pemisah '---' tidak ditemukan.")

    header_text, body_text = raw_text.split("\n---\n", maxsplit=1)
    metadata: dict[str, str] = {}
    for line in header_text.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"{path.name}: metadata tidak valid pada baris '{line}'.")
        key, value = line.split(":", maxsplit=1)
        metadata[key.strip()] = value.strip()

    required_metadata = {
        "source_name",
        "source_url",
        "language",
        "last_updated",
        "category",
        "topic",
    }
    missing_metadata = required_metadata - set(metadata)
    if missing_metadata:
        missing = ", ".join(sorted(missing_metadata))
        raise ValueError(f"{path.name}: metadata wajib belum lengkap: {missing}")

    sections = split_sections(body_text)
    if not sections:
        raise ValueError(f"{path.name}: tidak ada section yang bisa diproses.")

    return SourceDocument(metadata=metadata, sections=sections)


def split_sections(body_text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    for line in body_text.splitlines():
        if line.startswith("## "):
            if current_heading and current_lines:
                sections.append((current_heading, clean_text("\n".join(current_lines))))
            current_heading = line[3:].strip()
            current_lines = []
            continue
        current_lines.append(line)

    if current_heading and current_lines:
        sections.append((current_heading, clean_text("\n".join(current_lines))))

    return [(heading, content) for heading, content in sections if content]


def build_prompt(source: SourceDocument, section_title: str, section_text: str) -> str:
    return f"""Anda membantu menyiapkan knowledge base RAG bertopik anxiety.

TUGAS:
- Baca section sumber di bawah ini.
- Buat tepat satu objek JSON.
- Ringkas hanya dari teks sumber yang diberikan.
- Jangan tambahkan fakta baru dari luar teks.
- Jangan menulis diagnosis pasti atau saran obat spesifik.

FORMAT JSON WAJIB:
{{
  "title": "judul chunk yang singkat dan jelas",
  "content": "ringkasan 2-4 kalimat dalam bahasa Indonesia yang tetap setia pada sumber",
  "tags": ["tag1", "tag2", "tag3"],
  "skip": false
}}

ATURAN:
- Jika section hanya berisi navigasi, promosi, CTA, atau isi yang tidak cocok untuk knowledge base, balas dengan:
  {{"title":"","content":"","tags":[],"skip":true}}
- `content` harus cukup informatif untuk retrieval dan berdiri sendiri.
- `tags` gunakan tag pendek lowercase dengan topik utama seperti anxiety, symptoms, self_help, treatment, causes, help_seeking, overview.
- Jangan gunakan markdown.
- Balas hanya JSON.

METADATA SUMBER:
- source_name: {source.metadata["source_name"]}
- source_url: {source.metadata["source_url"]}
- language: {source.metadata["language"]}
- last_updated: {source.metadata["last_updated"]}
- category: {source.metadata["category"]}
- topic: {source.metadata["topic"]}

SECTION TITLE:
{section_title}

SECTION TEXT:
{section_text}
"""


async def generate_chunk(
    client: httpx.AsyncClient,
    base_url: str,
    model_name: str,
    source: SourceDocument,
    section_title: str,
    section_text: str,
) -> dict[str, Any]:
    payload = {
        "model": model_name,
        "prompt": build_prompt(source, section_title, section_text),
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
            "top_p": 0.9,
        },
    }

    endpoint = f"{base_url.rstrip('/')}/api/generate"
    try:
        response = await client.post(endpoint, json=payload)
    except httpx.ConnectError as exc:
        hint_lines = [
            f"Gagal terhubung ke Ollama di {endpoint}.",
            "Periksa apakah server Ollama sedang berjalan dan `OLLAMA_BASE_URL` sudah benar.",
        ]
        if "localhost" in base_url or "127.0.0.1" in base_url:
            hint_lines.append(
                "Jika script berjalan di WSL tetapi Ollama berjalan di Windows host, ganti `OLLAMA_BASE_URL` dari `localhost` ke IP host Windows."
            )
        raise RuntimeError(" ".join(hint_lines)) from exc
    response.raise_for_status()
    data = response.json()
    raw_response = data.get("response", "").strip()
    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Gagal parse JSON dari Ollama untuk section '{section_title}': {raw_response}") from exc

    if not isinstance(parsed, dict):
        raise ValueError(f"Output Ollama untuk section '{section_title}' bukan objek JSON.")

    return parsed


def validate_chunk(chunk: dict[str, Any], section_title: str) -> bool:
    if chunk.get("skip") is True:
        return False

    title = str(chunk.get("title", "")).strip()
    content = str(chunk.get("content", "")).strip()
    tags = chunk.get("tags", [])

    if not title or not content:
        raise ValueError(f"Section '{section_title}' menghasilkan chunk kosong.")
    if len(content) < 80:
        raise ValueError(f"Section '{section_title}' menghasilkan content terlalu pendek.")
    if not isinstance(tags, list) or not all(str(tag).strip() for tag in tags):
        raise ValueError(f"Section '{section_title}' memiliki tags tidak valid.")

    return True


def build_csv_row(row_id: int, source: SourceDocument, chunk: dict[str, Any]) -> dict[str, str]:
    tags = ";".join(str(tag).strip().lower() for tag in chunk["tags"] if str(tag).strip())
    return {
        "id": str(row_id),
        "category": source.metadata["category"],
        "topic": source.metadata["topic"],
        "title": str(chunk["title"]).strip(),
        "content": clean_text(str(chunk["content"]).strip()),
        "source_name": source.metadata["source_name"],
        "source_url": source.metadata["source_url"],
        "language": source.metadata["language"],
        "tags": tags,
        "last_updated": source.metadata["last_updated"],
    }


async def run_prepare() -> None:
    source_dir = resolve_path(settings.RAW_SOURCE_DIR)
    output_path = resolve_path(settings.KNOWLEDGE_CSV_PATH)
    source_files = sorted(source_dir.glob("*.md"))

    if not source_files:
        raise FileNotFoundError(f"Tidak ada file sumber .md di {source_dir}")

    documents = [parse_source_document(path) for path in source_files]
    rows: list[dict[str, str]] = []
    row_id = 1

    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
        for document, source_path in zip(documents, source_files):
            print(f"📄 Memproses sumber: {source_path.name}")
            for section_title, section_text in document.sections:
                chunk = await generate_chunk(
                    client=client,
                    base_url=settings.OLLAMA_BASE_URL,
                    model_name=settings.DATA_PREP_MODEL,
                    source=document,
                    section_title=section_title,
                    section_text=section_text,
                )
                if not validate_chunk(chunk, section_title):
                    print(f"⏭️ Lewati section '{section_title}'")
                    continue

                rows.append(build_csv_row(row_id, document, chunk))
                row_id += 1
                print(f"✅ Section '{section_title}' menjadi chunk '{chunk['title']}'")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✨ Dataset selesai dibuat: {output_path}")
    print(f"📦 Total chunk: {len(rows)}")


if __name__ == "__main__":
    asyncio.run(run_prepare())
