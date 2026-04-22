"""Pydantic request/response models for the API."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, field_validator

from app.models.db_models import DocumentType, MessageRole, QuotePreference


# ─── Auth ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username may only contain letters, numbers, _ and -")
        return v.lower()


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    quote_preference: QuotePreference
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


# ─── Chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None   # None → start new conversation
    message: str
    include_daily_quote: bool = False


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    response: str
    was_crisis_flagged: bool = False
    memory_context_used: bool = False
    daily_quote: Optional[str] = None
    disclaimer: str = (
        "I am a wellness companion, not a medical provider. "
        "Please consult a qualified doctor for medical advice."
    )
    search_queries: Optional[List[str]] = None  # for debugging / transparency
    supermemory_results: Optional[List[dict]] = None  # for debugging / transparency
    context_block: Optional[str] = None  # for debugging / transparency


class MessageOut(BaseModel):
    id: str
    role: MessageRole
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: str
    title: Optional[str]
    created_at: datetime
    messages: List[MessageOut] = []

    model_config = {"from_attributes": True}


# ─── Documents ────────────────────────────────────────────────────────────────

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    document_type: DocumentType
    s3_key: Optional[str]
    message: str


class DocumentOut(BaseModel):
    id: str
    filename: str
    document_type: DocumentType
    notes: Optional[str]
    is_processed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Quotes ───────────────────────────────────────────────────────────────────

class HealthQuote(BaseModel):
    quote: str
    author: Optional[str] = None
    category: str


# ─── Admin ────────────────────────────────────────────────────────────────────

class CrisisAlertOut(BaseModel):
    id: str
    user_id: str
    message_snippet: str
    is_resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── User Preferences ─────────────────────────────────────────────────────────

class UpdateQuotePreference(BaseModel):
    quote_preference: QuotePreference


# ─── Google OAuth ─────────────────────────────────────────────────────────────

class GoogleLoginResponse(BaseModel):
    auth_url: str
