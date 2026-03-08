import csv
import asyncio
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.application.usecases.ingest_use_case import IngestUseCase
from app.infrastructure.db.repositories.chat_repository import ChatRepository
from app.infrastructure.db.models import KnowledgeBase
from app.infrastructure.llm.client import LLMClient
from app.core.settings import get_settings

settings = get_settings()
engine = create_async_engine(settings.DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def run_ingest():
    async with async_session() as session:
        repo = ChatRepository(session)
        llm = LLMClient()
        use_case = IngestUseCase(repo, llm)

        print("🧹 Membersihkan data lama (Truncate)...")
        await session.execute(delete(KnowledgeBase))
        await session.commit()

        print("🚀 Memulai proses ingest data...")

        with open('data.csv', mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            count = 0
            for row in reader:
                # Gabungkan Context dan Response
                full_text = f"Tanya: {row['Context']}\nJawab: {row['Response']}"

                await use_case.execute(full_text)

                count += 1
                if count % 20 == 0:
                    await session.commit()
                    print(f"✅ Berhasil memproses {count} data...")

            await session.commit()
            print(f"✨ Ingestion Selesai! Total: {count} data unik tersimpan.")

if __name__ == "__main__":
    asyncio.run(run_ingest())
