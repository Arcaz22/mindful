from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class LLMChatResponse:
    content: str
    model_name: str
    usage_count: int
    timestamp: datetime
    source_context: Optional[str] = None
