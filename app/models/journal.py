from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    # user_id = Column(Integer, ForeignKey("users.id")) # We'll uncomment this when we build users
    user_id = Column(Integer, index=True, default=1) # Hardcoded for now to keep things moving
    content = Column(Text, nullable=False)
    mood_tag = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())