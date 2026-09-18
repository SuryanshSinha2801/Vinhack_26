from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.app.core.config import settings
from api.app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from api.app.database import get_db
from api.app.models import User
from api.app.schemas.auth import LoginRequest, RegisterRequest, UserProfile
from api.app.schemas.common import ApiResponse


router = APIRouter(prefix="/auth", tags=["authentication"])
COOKIE_NAME = "mindtrail_session"


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


@router.post("/register", response_model=ApiResponse[UserProfile], status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This username is already in use")
    user = User(username=payload.username, display_name=payload.display_name, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    set_session_cookie(response, user.id)
    return ApiResponse(data=UserProfile.model_validate(user))


@router.post("/login", response_model=ApiResponse[UserProfile])
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == payload.username.strip().lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email or password is incorrect")
    set_session_cookie(response, user.id)
    return ApiResponse(data=UserProfile.model_validate(user))


@router.get("/me", response_model=ApiResponse[UserProfile])
def me(user: User = Depends(current_user)):
    return ApiResponse(data=UserProfile.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
