"""SQLAlchemy ORM models — maps to PostgreSQL (prod) / SQLite (dev)."""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey,
    Integer, String, Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


# ─── Enums ────────────────────────────────────────────────────────────────────

class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class DocumentType(str, enum.Enum):
    medical_report = "medical_report"
    prescription = "prescription"
    lab_result = "lab_result"
    doctor_notes = "doctor_notes"
    imaging = "imaging"
    other = "other"


class QuotePreference(str, enum.Enum):
    chat = "chat"          # show in daily chat
    notification = "notification"
    both = "both"
    none = "none"


# ─── Tables ───────────────────────────────────────────────────────────────────

class User(Base): # Any class that inherits from Base = a database table
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=True)   # nullable: Google-only users have no password
    google_id = Column(String, unique=True, nullable=True, index=True)  # set for Google OAuth users
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    quote_preference = Column(
        Enum(QuotePreference), default=QuotePreference.chat
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    crisis_alerts = relationship("CrisisAlert", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base): #Any class that inherits from Base = a database table
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=True)          # auto-generated summary
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base): #Any class that inherits from Base = a database table
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    # Metadata: memory context used, guardrail flags, etc.
    was_crisis_flagged = Column(Boolean, default=False)
    memory_context_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class Document(Base): #Any class that inherits from Base = a database table
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    document_type = Column(Enum(DocumentType), default=DocumentType.other)
    s3_key = Column(String, nullable=True)           # S3 object key (raw file)
    supermemory_doc_id = Column(String, nullable=True)  # SuperMemory document id
    notes = Column(Text, nullable=True)              # User-provided notes
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="documents")


class CrisisAlert(Base):
    __tablename__ = "crisis_alerts"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    message_snippet = Column(Text, nullable=False)   # First 500 chars of triggering message
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String, nullable=True)       # Admin user id
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="crisis_alerts")
