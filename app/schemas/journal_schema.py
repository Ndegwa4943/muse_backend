from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class JournalCreate(BaseModel):
    content: str = Field(..., min_length=2, description="The user's reflection.")
    mood_tag: Optional[str] = Field(None, description="E.g., Calm, Inspired, Anxious")

class JournalResponse(BaseModel):
    id: int
    content: str
    mood_tag: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True # Tells Pydantic to read SQLAlchemy models