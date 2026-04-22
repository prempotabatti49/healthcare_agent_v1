"""Database session factory."""
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.secrets import get_secret
from app.models.db_models import Base

database_url = get_secret("DATABASE_URL")

# connect_args only needed for SQLite (thread safety)
_connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}


engine = create_engine(
    database_url,
    connect_args=_connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables (idempotent). Called on app startup."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db_session():
    """
    Context manager for use inside route handlers and services.

    Usage:
        with get_db_session() as db:
            user = db.query(User).filter_by(id=user_id).first()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db():
    """FastAPI Depends generator. Use with Depends(get_db) in route signatures."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
