from fastapi import FastAPI
from app.core.config import settings
from app.api import routes_journal
from app.db.database import engine
from app.db.base import Base

# This line creates the tables in SQLite automatically for now
Base.metadata.create_all(bind=engine)

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
    )

    # Plug in the journal feature
    app.include_router(
        routes_journal.router, 
        prefix=f"{settings.API_V1_STR}/journals", 
        tags=["Private Journal"]
    )

    @app.get("/")
    def root():
        return {"message": "Welcome to the Muse API. Contemplation awaits."}

    return app

app = create_app()