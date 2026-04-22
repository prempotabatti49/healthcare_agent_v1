"""Health check and quotes endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.db_models import User
from app.models.pydantic_models import HealthQuote
from app.utils.quotes import get_all_categories, get_daily_quote, get_random_quote

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/ping")
def ping():
    """Simple health check — no auth required."""
    return {"status": "ok", "service": "Sunflower Health AI"}


@router.get("/quotes/daily", response_model=HealthQuote)
def daily_quote(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Return today's health quote. Optionally filter by category."""
    return get_daily_quote(category)


@router.get("/quotes/random", response_model=HealthQuote)
def random_quote(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Return a random health quote. Optionally filter by category."""
    return get_random_quote(category)


@router.get("/quotes/categories")
def quote_categories(current_user: User = Depends(get_current_user)):
    """List all available quote categories."""
    return {"categories": get_all_categories()}
