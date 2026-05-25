from sqlalchemy.orm import Session
from app.models.journal import JournalEntry
from app.schemas.journal_schema import JournalCreate

class JournalService:
    def __init__(self, db: Session):
        self.db = db

    def create_entry(self, entry_data: JournalCreate, user_id: int = 1) -> JournalEntry:
        # Step 1: Create the database record
        new_entry = JournalEntry(
            user_id=user_id,
            content=entry_data.content,
            mood_tag=entry_data.mood_tag
        )
        self.db.add(new_entry)
        self.db.commit()
        self.db.refresh(new_entry)
        
        # Step 2: (Future) Trigger background NLP analysis here
        # self._analyze_content(new_entry.id, new_entry.content)
        
        return new_entry

    def get_user_entries(self, user_id: int = 1):
        return self.db.query(JournalEntry).filter(JournalEntry.user_id == user_id).all()