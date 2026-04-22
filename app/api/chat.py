"""Chat conversation endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.queries import get_conversation, get_user_conversations
from app.db.session import get_db
from app.models.db_models import User
from app.models.pydantic_models import ChatRequest, ChatResponse, ConversationOut
from app.services.chat_service import process_message

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
async def send_message(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a message to Sunflower and get a response.

    Pass conversation_id to continue an existing conversation,
    or leave it empty to start a new one.
    """
    return await process_message(
        db=db,
        user_id=current_user.id,
        message_text=payload.message,
        conversation_id=payload.conversation_id,
        include_daily_quote=payload.include_daily_quote,
    )


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all conversations for the logged-in user, newest first."""
    return get_user_conversations(db, current_user.id)


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation_by_id(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single conversation with all its messages."""
    conv = get_conversation(db, conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conv
