from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    user_id: str
    message: str
    visitor_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    model_used: str
    remaining_chats: int
    context_ids: Optional[list[int]] = None
