"""Mount all API sub-routers here."""
from fastapi import APIRouter

from app.api import auth, chat, documents, health, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(chat.router)
api_router.include_router(documents.router)
api_router.include_router(health.router)
