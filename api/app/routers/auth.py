import secrets
import hashlib
from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.app.core.config import settings
from api.app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from api.app.database import get_db
from api.app.models import User
from api.app.schemas.auth import LoginRequest, RegisterRequest, UserProfile
from api.app.schemas.common import ApiResponse
from api.app.services.audit import record_audit


router = APIRouter(prefix="/auth", tags=["authentication"])
COOKIE_NAME = "mindtrail_session"
CSRF_COOKIE_NAME = "mindtrail_csrf"
ACCOUNT_LOGIN_LIMIT = 6
ACCOUNT_LOGIN_WINDOW_SECONDS = 300
_login_attempts: dict[str, deque[float]] = defaultdict(deque)
_login_attempts_lock = Lock()


def enforce_account_login_limit(username: str) -> None:
    key = hashlib.sha256(username.strip().lower().encode()).hexdigest()
    now = monotonic()
    with _login_attempts_lock:
        bucket = _login_attempts[key]
        while bucket and bucket[0] <= now - ACCOUNT_LOGIN_WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= ACCOUNT_LOGIN_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts for this account. Try again later.",
                headers={"Retry-After": str(ACCOUNT_LOGIN_WINDOW_SECONDS)},
            )
        bucket.append(now)
        if len(_login_attempts) > 10_000:
            stale = [stored_key for stored_key, values in _login_attempts.items() if not values or values[-1] <= now - ACCOUNT_LOGIN_WINDOW_SECONDS]
            for stored_key in stale[:1_000]:
                _login_attempts.pop(stored_key, None)


def set_session_cookie(response: Response, user_id: int) -> None:
    response.set_cookie(
        COOKIE_NAME,
        create_access_token(user_id),
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        CSRF_COOKIE_NAME,
        secrets.token_urlsafe(32),
        max_age=settings.access_token_expire_minutes * 60,
        httponly=False,
        secure=settings.app_env == "production",
        samesite="strict",
        path="/",
    )


def current_user(
    session_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    token = session_token
    if not token and authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    user_id = decode_access_token(token) if token else None
    user = db.get(User, user_id) if user_id else None
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user


def current_admin(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access required")
    return user


@router.post("/register", response_model=ApiResponse[UserProfile], status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    if not settings.allow_public_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public account registration is disabled.",
        )
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This username is already in use")
    user = User(username=payload.username, display_name=payload.display_name, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    record_audit(db, "auth.register", "success", user=user)
    set_session_cookie(response, user.id)
    return ApiResponse(data=UserProfile.model_validate(user))


@router.post("/login", response_model=ApiResponse[UserProfile])
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    enforce_account_login_limit(payload.username)
    user = db.scalar(select(User).where(User.username == payload.username.strip().lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        record_audit(
            db,
            "auth.login",
            "failure",
            attempted_username=payload.username,
            event_data={"reason": "invalid_credentials"},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email or password is incorrect")
    with _login_attempts_lock:
        _login_attempts.pop(hashlib.sha256(payload.username.strip().lower().encode()).hexdigest(), None)
    record_audit(db, "auth.login", "success", user=user)
    set_session_cookie(response, user.id)
    return ApiResponse(data=UserProfile.model_validate(user))


@router.get("/me", response_model=ApiResponse[UserProfile])
def me(user: User = Depends(current_user)):
    return ApiResponse(data=UserProfile.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    record_audit(db, "auth.logout", "success", user=user)
    response.delete_cookie(COOKIE_NAME, path="/")
    response.delete_cookie(CSRF_COOKIE_NAME, path="/")
