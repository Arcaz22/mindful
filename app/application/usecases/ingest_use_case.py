import re
from app.domain.chat.chat_repository_port import ChatRepositoryPort

class IngestUseCase:
    def __init__(self, repo: ChatRepositoryPort, llm):
        self.repo = repo
        self.llm = llm

    def clean_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    async def execute(self, content: str, metadata: str = None):
        cleaned_content = self.clean_text(content)
        vector = self.llm.generate_embedding(cleaned_content)
        await self.repo.save_knowledge(cleaned_content, vector, metadata)
