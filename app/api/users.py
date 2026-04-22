"""User management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.auth import (
    create_access_token,
    get_admin_user,
    get_current_user,
    hash_password,
    verify_password,
)
from app.db.queries import (
    create_user,
    get_crisis_alerts,
    get_user_by_email,
    get_user_by_username,
    resolve_crisis_alert,
    update_user_quote_preference,
)
from app.db.session import get_db
from app.models.db_models import User
from app.models.pydantic_models import (
    CrisisAlertOut,
    TokenResponse,
    UpdateQuotePreference,
    UserCreate,
    UserResponse,
)

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with email and password."""
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=400, detail="Email already registered.")
    if get_user_by_username(db, payload.username):
        raise HTTPException(status_code=400, detail="Username already taken.")
    user = create_user(
        db,
        email=payload.email,
        username=payload.username,
        hashed_password=payload.password,
        full_name=payload.full_name,
    )
    return user


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Log in with username and password. Returns a JWT access token."""
    user = get_user_by_username(db, form.username)
    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    if not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive.")
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the profile of the currently logged-in user."""
    return current_user


@router.patch("/me/quote-preference", response_model=UserResponse)
def update_quote_preference(
    payload: UpdateQuotePreference,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update how the user wants to receive daily health quotes."""
    return update_user_quote_preference(db, current_user.id, payload.quote_preference)


# ── Admin endpoints ───────────────────────────────────────────────────────────

@router.get("/admin/crisis-alerts", response_model=list[CrisisAlertOut])
def list_crisis_alerts(
    resolved: bool = False,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """List crisis alerts. Defaults to unresolved. Pass ?resolved=true for resolved. Admin only."""
    return get_crisis_alerts(db, resolved=resolved)


@router.patch("/admin/crisis-alerts/{alert_id}/resolve", response_model=CrisisAlertOut)
def resolve_crisis_alert_route(
    alert_id: str,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Mark a crisis alert as resolved. Admin only."""
    alert = resolve_crisis_alert(db, alert_id, admin_id=admin.id)
    if not alert:
        raise HTTPException(status_code=404, detail="Crisis alert not found.")
    return alert
