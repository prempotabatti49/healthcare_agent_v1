"""
Auth utilities and Google OAuth endpoints.

How authentication works in this app:
  1. Email/password login  → POST /api/users/login  → returns JWT
  2. Google OAuth login    → GET  /api/auth/google   → redirects to Google
                             GET  /api/auth/google/callback → Google redirects back here
                                                           → issues JWT → redirects to frontend

Every protected route calls get_user_from_request(request) at the top of
the route handler instead of using FastAPI's Depends() system.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx
from authlib.integrations.httpx_client import OAuth2Client
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config.secrets import get_secret
from app.config.settings import get_settings
from app.db.queries import (
    create_user,
    get_user_by_email,
    get_user_by_google_id,
    get_user_by_id,
)
from app.db.session import get_db, get_db_session
from app.models.db_models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")

logger = logging.getLogger(__name__)
_settings = get_settings()
_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Google OAuth endpoints (standard, do not change)
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    print(f"Hashing password: {plain}")  # Debug log
    print(f"hashed password: {_pwd_ctx.hash(plain)}")  # Debug log
    # return _pwd_ctx.hash(plain[:72])
    return plain


def verify_password(plain: str, hashed: str) -> bool:
    print(f"Verifying password: {plain}")  # Debug log
    print(f"Verified against hashed password: {hashed}")  # Debug log
    # return _pwd_ctx.verify(plain[:72], hashed)
    return plain == hashed

# ── JWT helpers ───────────────────────────────────────────────────────────────

def create_access_token(user_id: str) -> str:
    """Create a signed JWT for the given user id."""
    secret = get_secret("SECRET_KEY")
    expire = datetime.utcnow() + timedelta(minutes=_settings.access_token_expire_minutes)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, secret, algorithm=_settings.algorithm)


def _decode_token(token: str) -> Optional[str]:
    """Decode a JWT and return the user_id (sub claim), or None if invalid."""
    secret = get_secret("SECRET_KEY")
    try:
        payload = jwt.decode(token, secret, algorithms=[_settings.algorithm])
        return payload.get("sub")
    except JWTError:
        return None


# ── Request-level auth (replaces FastAPI Depends) ────────────────────────────

def get_user_from_request(request: Request) -> User:
    """
    Extract the Bearer token from the Authorization header, validate it,
    and return the matching User from the database.

    Call this at the top of any route that requires a logged-in user:

        @router.get("/me")
        def get_me(request: Request):
            user = get_user_from_request(request)
            ...

    Raises HTTP 401 if the token is missing, invalid, or the user doesn't exist.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.removeprefix("Bearer ").strip()
    user_id = _decode_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    with get_db_session() as db:
        user = get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )
    return user


def require_admin(user: User) -> None:
    """
    Call after get_user_from_request() to enforce admin-only access.

        user = get_user_from_request(request)
        require_admin(user)
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )


# ── FastAPI Depends-based auth (use these in route signatures) ────────────────

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency. Validates the Bearer token and returns the User.

    Usage in a route:
        @router.get("/me")
        def get_me(current_user: User = Depends(get_current_user)):
            return current_user
    """
    user_id = _decode_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )
    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    FastAPI dependency. Same as get_current_user but also enforces admin role.

    Usage:
        @router.get("/admin/alerts")
        def list_alerts(admin: User = Depends(get_admin_user)):
            ...
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user


# ── Google OAuth helpers ──────────────────────────────────────────────────────

def get_google_auth_url() -> str:
    """Build the Google OAuth authorization URL the user should be redirected to."""
    client = OAuth2Client(
        client_id=_settings.google_client_id,
        client_secret=get_secret("GOOGLE_CLIENT_SECRET"),
        redirect_uri=_settings.google_redirect_uri,
        scope="openid email profile",
    )
    url, _ = client.create_authorization_url(GOOGLE_AUTH_URL)
    return url


def exchange_google_code(code: str) -> dict:
    """
    Exchange the one-time Google auth code for user info.
    Returns a dict: {"google_id": str, "email": str, "name": str}
    """
    client = OAuth2Client(
        client_id=_settings.google_client_id,
        client_secret=get_secret("GOOGLE_CLIENT_SECRET"),
        redirect_uri=_settings.google_redirect_uri,
    )
    token = client.fetch_token(GOOGLE_TOKEN_URL, code=code)

    # Fetch the user's profile from Google
    resp = httpx.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {token['access_token']}"},
    )
    resp.raise_for_status()
    info = resp.json()

    return {
        "google_id": info["sub"],
        "email": info.get("email", ""),
        "name": info.get("name", ""),
    }


def get_or_create_google_user(google_id: str, email: str, name: str) -> User:
    """
    Find an existing user by google_id or email, or create a new one.
    If the user previously registered with email/password, we link their
    google_id to the existing account.
    """
    with get_db_session() as db:
        # 1. Already signed in with Google before
        user = get_user_by_google_id(db, google_id)
        if user:
            return user

        # 2. Registered with email/password previously — link Google to account
        user = get_user_by_email(db, email)
        if user:
            user.google_id = google_id
            db.commit()
            db.refresh(user)
            return user

        # 3. Brand new user — create account (no password needed)
        username = email.split("@")[0].lower().replace(".", "_")
        user = create_user(
            db,
            email=email,
            username=username,
            full_name=name,
            google_id=google_id,
        )
        return user


# ── Google OAuth routes ───────────────────────────────────────────────────────

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/google")
def google_login():
    """
    Step 1 of Google OAuth.
    Returns the Google authorization URL. The frontend should redirect
    the user to this URL.
    """
    if not _settings.google_client_id:
        raise HTTPException(
            status_code=503,
            detail="Google login is not configured. Set GOOGLE_CLIENT_ID in your environment.",
        )
    auth_url = get_google_auth_url()
    return {"auth_url": auth_url}


@router.get("/google/callback")
def google_callback(code: str):
    """
    Step 2 of Google OAuth — Google redirects here after the user approves.
    Exchanges the code, finds or creates the user, issues a JWT, and
    redirects to the frontend with the token in the query string.

    Frontend reads: window.location.search → ?token=<jwt>
    """
    try:
        user_info = exchange_google_code(code)
    except Exception as exc:
        logger.error("Google OAuth code exchange failed: %s", exc)
        raise HTTPException(status_code=400, detail="Google authentication failed.")

    user = get_or_create_google_user(
        google_id=user_info["google_id"],
        email=user_info["email"],
        name=user_info["name"],
    )
    token = create_access_token(user.id)

    # Redirect to the frontend with the token in the URL
    frontend_url = _settings.frontend_url
    return RedirectResponse(url=f"{frontend_url}?token={token}")
