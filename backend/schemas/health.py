from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone

class HealthResponse(BaseModel):
    status: str
    backend_online: bool = True
    ollama_online: bool
    model_available: bool
    model_name: str
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
