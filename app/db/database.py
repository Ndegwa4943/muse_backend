from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# SQLite requires a specific argument to work properly with FastAPI's async nature
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL, 
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Dependency function to yield a database session for each request,
    ensuring it closes cleanly afterward.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()