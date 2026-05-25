from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.schemas.journal_schema import JournalCreate, JournalResponse
from app.services.journal_service import JournalService

router = APIRouter()

@router.post("/", response_model=JournalResponse, status_code=status.HTTP_201_CREATED)
def write_journal(entry: JournalCreate, db: Session = Depends(get_db)):
    """
    Saves a new private journal entry.
    """
    service = JournalService(db)
    try:
        return service.create_entry(entry_data=entry)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to save reflection."
        )

@router.get("/", response_model=List[JournalResponse])
def get_journals(db: Session = Depends(get_db)):
    """
    Retrieves all past reflections for the user.
    """
    service = JournalService(db)
    return service.get_user_entries()