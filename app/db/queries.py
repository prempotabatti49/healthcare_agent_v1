"""
DB Query Helpers
================
One function per database operation. All functions take `db: Session`
as their first argument. No business logic lives here — just reads and writes.

Usage example:
    from app.db.session import get_db_session
    from app.db import queries

    with get_db_session() as db:
        user = queries.get_user_by_email(db, "alice@example.com")
"""
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models.db_models import (
    Conversation,
    CrisisAlert,
    Document,
    DocumentType,
    Message,
    MessageRole,
    QuotePreference,
    User,
)


# ── Users ─────────────────────────────────────────────────────────────────────

def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.id == user_id, User.is_active == True).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_user_by_google_id(db: Session, google_id: str) -> Optional[User]:
    return db.query(User).filter(User.google_id == google_id).first()


def create_user(
    db: Session,
    email: str,
    username: str,
    hashed_password: Optional[str] = None,
    full_name: Optional[str] = None,
    google_id: Optional[str] = None,
) -> User:
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        username=username,
        hashed_password=hashed_password,
        full_name=full_name,
        google_id=google_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_quote_preference(
    db: Session, user_id: str, preference: QuotePreference
) -> Optional[User]:
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    user.quote_preference = preference
    db.commit()
    db.refresh(user)
    return user


# ── Conversations ─────────────────────────────────────────────────────────────

def create_conversation(db: Session, user_id: str) -> Conversation:
    conv = Conversation(id=str(uuid.uuid4()), user_id=user_id)
    db.add(conv)
    db.flush()  # makes the id available without a full commit
    return conv


def get_conversation(
    db: Session, conversation_id: str, user_id: str
) -> Optional[Conversation]:
    return db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id,
    ).first()


def get_user_conversations(db: Session, user_id: str) -> list[Conversation]:
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )


# ── Messages ──────────────────────────────────────────────────────────────────

def save_message(
    db: Session,
    conversation_id: str,
    role: MessageRole,
    content: str,
    was_crisis_flagged: bool = False,
    memory_context_used: bool = False,
) -> Message:
    msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role=role,
        content=content,
        was_crisis_flagged=was_crisis_flagged,
        memory_context_used=memory_context_used,
    )
    db.add(msg)
    return msg


def get_conversation_messages(
    db: Session, conversation_id: str, limit: int = 15
) -> list[Message]:
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )
    # Return in chronological order (oldest first) for LLM context
    return list(reversed(messages))


# ── Documents ─────────────────────────────────────────────────────────────────

def create_document(
    db: Session,
    user_id: str,
    filename: str,
    document_type: DocumentType,
    s3_key: Optional[str],
    supermemory_doc_id: Optional[str],
    notes: Optional[str],
) -> Document:
    doc = Document(
        id=str(uuid.uuid4()),
        user_id=user_id,
        filename=filename,
        document_type=document_type,
        s3_key=s3_key,
        supermemory_doc_id=supermemory_doc_id,
        notes=notes,
        is_processed=True,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_user_documents(db: Session, user_id: str) -> list[Document]:
    return (
        db.query(Document)
        .filter(Document.user_id == user_id)
        .order_by(Document.created_at.desc())
        .all()
    )


def get_document(
    db: Session, document_id: str, user_id: str
) -> Optional[Document]:
    return db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user_id,
    ).first()


# ── Crisis Alerts ─────────────────────────────────────────────────────────────

def create_crisis_alert(
    db: Session, user_id: str, message_snippet: str
) -> CrisisAlert:
    alert = CrisisAlert(
        id=str(uuid.uuid4()),
        user_id=user_id,
        message_snippet=message_snippet[:500],
    )
    db.add(alert)
    return alert


def get_crisis_alerts(
    db: Session, resolved: bool = False
) -> list[CrisisAlert]:
    return (
        db.query(CrisisAlert)
        .filter(CrisisAlert.is_resolved == resolved)
        .order_by(CrisisAlert.created_at.desc())
        .all()
    )


def resolve_crisis_alert(
    db: Session, alert_id: str, admin_id: str
) -> Optional[CrisisAlert]:
    alert = db.query(CrisisAlert).filter(CrisisAlert.id == alert_id).first()
    if not alert:
        return None
    alert.is_resolved = True
    alert.resolved_by = admin_id
    db.commit()
    db.refresh(alert)
    return alert
