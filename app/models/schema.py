from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

# --- JUNCTION TABLES ---
circle_members = Table(
    "circle_members",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("circle_id", Integer, ForeignKey("thought_circles.id", ondelete="CASCADE"), primary_key=True)
)

# --- CORE TABLES ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    folders = relationship("Folder", back_populates="user", cascade="all, delete-orphan")
    journal_entries = relationship("JournalEntry", back_populates="user", cascade="all, delete-orphan")
    threads = relationship("Thread", back_populates="author", cascade="all, delete-orphan")
    circles = relationship("ThoughtCircle", secondary=circle_members, back_populates="members")


class Folder(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False) # e.g., "Music", "Tech"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="folders")
    items = relationship("SavedItem", back_populates="folder", cascade="all, delete-orphan")


class SavedItem(Base):
    """The Vault: Where external links and rich metadata live."""
    __tablename__ = "saved_items"

    id = Column(Integer, primary_key=True, index=True)
    folder_id = Column(Integer, ForeignKey("folders.id", ondelete="CASCADE"), nullable=False)
    source_platform = Column(String(50)) # e.g., "TikTok", "Substack"
    original_url = Column(Text, nullable=False)
    
    # Crucial: Using JSONB to dynamically store platform-specific scraping data
    metadata_payload = Column(JSONB, nullable=True, server_default='{}') 
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    folder = relationship("Folder", back_populates="items")
    sparked_journals = relationship("JournalEntry", back_populates="linked_item")


class JournalEntry(Base):
    """The Contemplation Engine: The core rabbit hole."""
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    mood_tag = Column(String(50)) # Validated by Pydantic Enums at the route level
    
    # The Spark: What external media caused this thought?
    linked_item_id = Column(Integer, ForeignKey("saved_items.id", ondelete="SET NULL"), nullable=True)
    
    # The Rabbit Hole: Self-referencing loop for nested thoughts
    parent_entry_id = Column(Integer, ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="journal_entries")
    linked_item = relationship("SavedItem", back_populates="sparked_journals")
    insights = relationship("ReflectionInsight", back_populates="journal", uselist=False, cascade="all, delete-orphan")
    
    # Self-referential relationship
    replies = relationship("JournalEntry", backref="parent", remote_side=[id])


class ReflectionInsight(Base):
    """The Mirror: Machine Learning outputs."""
    __tablename__ = "reflection_insights"

    id = Column(Integer, primary_key=True, index=True)
    journal_id = Column(Integer, ForeignKey("journal_entries.id", ondelete="CASCADE"), unique=True, nullable=False)
    sentiment_score = Column(Float, nullable=True)
    
    # JSONB array of strings for fast querying of growth themes
    growth_themes = Column(JSONB, nullable=True, server_default='[]') 
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    journal = relationship("JournalEntry", back_populates="insights")


class ThoughtCircle(Base):
    __tablename__ = "thought_circles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    members = relationship("User", secondary=circle_members, back_populates="circles")
    threads = relationship("Thread", back_populates="circle", cascade="all, delete-orphan")


class Thread(Base):
    __tablename__ = "threads"

    id = Column(Integer, primary_key=True, index=True)
    circle_id = Column(Integer, ForeignKey("thought_circles.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    circle = relationship("ThoughtCircle", back_populates="threads")
    author = relationship("User", back_populates="threads")