from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    user_id: str
    message: str = Field(min_length=1, max_length=4000)
    visitor_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    model_used: str
    remaining_chats: int
    context_ids: Optional[list[int]] = None
