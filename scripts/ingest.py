import csv
import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.application.usecases.ingest_use_case import IngestUseCase
from app.core.settings import get_settings
from app.infrastructure.db.models import KnowledgeBase
from app.infrastructure.db.repositories.chat_repository import ChatRepository
from app.infrastructure.llm.client import LLMClient

settings = get_settings()
engine = create_async_engine(settings.DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)
REQUIRED_COLUMNS = {
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
}


def resolve_dataset_path() -> Path:
    dataset_path = Path(settings.KNOWLEDGE_CSV_PATH)
    if not dataset_path.is_absolute():
        dataset_path = PROJECT_ROOT / dataset_path
    return dataset_path


def clean_value(value: str) -> str:
    return " ".join((value or "").split()).strip()


def validate_columns(fieldnames: list[str] | None) -> None:
    available_columns = set(fieldnames or [])
    missing_columns = REQUIRED_COLUMNS - available_columns
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Kolom dataset belum lengkap: {missing}")


def build_content(row: dict[str, str]) -> str:
    return "\n".join(
        [
            f"Title: {clean_value(row['title'])}",
            f"Category: {clean_value(row['category'])}",
            f"Topic: {clean_value(row['topic'])}",
            clean_value(row["content"]),
        ]
    )


def build_metadata(row: dict[str, str]) -> str:
    metadata = {
        "source_id": clean_value(row["id"]),
        "category": clean_value(row["category"]),
        "topic": clean_value(row["topic"]),
        "title": clean_value(row["title"]),
        "source_name": clean_value(row["source_name"]),
        "source_url": clean_value(row["source_url"]),
        "language": clean_value(row["language"]),
        "tags": [tag.strip() for tag in row["tags"].split(";") if tag.strip()],
        "last_updated": clean_value(row["last_updated"]),
    }
    return json.dumps(metadata, ensure_ascii=False)


def validate_row(row: dict[str, str], row_number: int) -> None:
    for column in REQUIRED_COLUMNS:
        if not clean_value(row.get(column, "")):
            raise ValueError(f"Baris {row_number}: kolom '{column}' wajib diisi.")

    if not clean_value(row["source_url"]).startswith(("http://", "https://")):
        raise ValueError(f"Baris {row_number}: source_url harus berupa URL http/https.")

    content = clean_value(row["content"])
    if len(content) < 80:
        raise ValueError(f"Baris {row_number}: content terlalu pendek untuk dijadikan chunk.")


async def run_ingest():
    async with async_session() as session:
        repo = ChatRepository(session)
        llm = LLMClient(
            base_url=settings.OLLAMA_BASE_URL,
            model_name=settings.OLLAMA_MODEL,
            embedding_model_name=settings.EMBEDDING_MODEL_NAME,
            embedding_vector_size=settings.EMBEDDING_VECTOR_SIZE,
        )
        use_case = IngestUseCase(repo, llm)
        dataset_path = resolve_dataset_path()

        print("🧹 Membersihkan data lama (Truncate)...")
        await session.execute(delete(KnowledgeBase))
        await session.commit()

        print(f"🚀 Memulai proses ingest data dari {dataset_path}...")

        with dataset_path.open(mode="r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            validate_columns(reader.fieldnames)
            count = 0
            seen_fingerprints: set[tuple[str, str, str]] = set()
            for row_number, row in enumerate(reader, start=2):
                validate_row(row, row_number)

                fingerprint = (
                    clean_value(row["topic"]).lower(),
                    clean_value(row["title"]).lower(),
                    clean_value(row["content"]).lower(),
                )
                if fingerprint in seen_fingerprints:
                    print(f"⏭️ Lewati duplikasi pada baris {row_number}: {row['title']}")
                    continue

                seen_fingerprints.add(fingerprint)
                full_text = build_content(row)
                metadata = build_metadata(row)

                await use_case.execute(full_text, metadata=metadata)

                count += 1
                if count % 20 == 0:
                    await session.commit()
                    print(f"✅ Berhasil memproses {count} data...")

        await session.commit()
        print(f"✨ Ingestion Selesai! Total: {count} data unik tersimpan.")

if __name__ == "__main__":
    asyncio.run(run_ingest())
