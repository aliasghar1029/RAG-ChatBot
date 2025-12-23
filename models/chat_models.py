from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from typing import Optional, List
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv("NEON_DB_URL")
if not DATABASE_URL:
    raise ValueError("NEON_DB_URL environment variable is required")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    session_metadata = Column(JSONB)  # Renamed from 'metadata' to avoid SQLAlchemy reserved name

    # Relationship to queries
    queries = relationship("UserQuery", back_populates="session")

class UserQuery(Base):
    __tablename__ = "user_queries"

    query_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.session_id"))
    content = Column(Text, nullable=False)
    selected_text = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    context_chunks = Column(ARRAY(String))

    # Relationship to session and responses
    session = relationship("ChatSession", back_populates="queries")
    responses = relationship("Response", back_populates="query")

class Response(Base):
    __tablename__ = "responses"

    response_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_id = Column(UUID(as_uuid=True), ForeignKey("user_queries.query_id"), nullable=False)
    content = Column(Text, nullable=False)
    source_chunks = Column(ARRAY(String))
    confidence_score = Column(Integer)  # Using Integer for simplicity (0-100 scale)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    token_count = Column(Integer)
    validation_result = Column(JSONB)  # Store validation result as JSON

    # Relationship to query
    query = relationship("UserQuery", back_populates="responses")

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()