from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
import datetime

# Note: In a real app, `db` would be injected via a SQLAlchemy dependency
# We use mock dependency injections here to immediately unblock UI development

router = APIRouter(tags=["UI Prototype Endpoints"])

# --- Pydantic Schemas for the UI ---

class UIVaultSaveRequest(BaseModel):
    url: HttpUrl
    source_platform: Optional[str] = "Unknown"

class UIJournalCreateRequest(BaseModel):
    content: str
    mood_tag: str
    linked_item_id: Optional[int] = None
    parent_entry_id: Optional[int] = None

class UIJournalResponse(BaseModel):
    id: int
    content: str
    mood_tag: str
    linked_item_id: Optional[int]
    created_at: datetime.datetime

# --- Mock Background Tasks ---
def mock_extract_and_update(item_id: int, url: str):
    """Simulates background scraping for the UI to test async behavior"""
    print(f"[Scraper Task] Extracting metadata for {url} into item_id {item_id}")
    # In production: extract metadata and update `saved_items` table (JSONB column)

# --- Endpoints ---

@router.post("/api/vault/save", status_code=status.HTTP_202_ACCEPTED)
async def save_to_vault_from_ui(
    request: UIVaultSaveRequest, 
    background_tasks: BackgroundTasks
):
    """
    Called when the user clicks 'Share to Muse' from an external app.
    Instantly returns a success message to the UI while scraping in the background.
    """
    mock_item_id = 99 # Simulating a database insert returning an ID
    
    # Fire off background extraction task (Ingestion Layer)
    background_tasks.add_task(mock_extract_and_update, mock_item_id, str(request.url))
    
    return {
        "status": "success",
        "message": "Saved to your Inspiration Vault.",
        "item_id": mock_item_id
    }

@router.post("/api/journals", response_model=UIJournalResponse)
async def create_journal_from_ui(request: UIJournalCreateRequest):
    """
    Called when the user submits a new thought from the Canvas.
    Supports 'The Spark' (linked_item_id) and 'The Rabbit Hole' (parent_entry_id).
    """
    # Simulate DB insert
    response = UIJournalResponse(
        id=101,
        content=request.content,
        mood_tag=request.mood_tag,
        linked_item_id=request.linked_item_id,
        created_at=datetime.datetime.now()
    )
    
    # This is where Lowell's NLP pipeline will hook in later via a background task!
    print(f"[NLP Task] Analyzing journal {response.id} for Mirror Insights...")
    
    return response

@router.get("/api/mirror/insights")
async def get_mirror_dashboard_data():
    """
    Provides mock data for the Mirror UI to display growth themes.
    """
    return {
        "weekly_sentiment_average": 0.82,
        "active_growth_themes": ["Mindfulness", "Career Transitions", "Creative Focus"],
        "rabbit_hole_streak": 4 # Days in a row connecting thoughts
    }