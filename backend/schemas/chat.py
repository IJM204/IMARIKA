from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

class MessageItem(BaseModel):
    id: str
    sender: str  # "user" | "assistant"
    content: str
    created_at: str

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Message de l'utilisateur")
    conversation_id: Optional[str] = None
    language: Optional[str] = "fr"

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    context_used: Optional[List[str]] = None
    status: str = "success"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
