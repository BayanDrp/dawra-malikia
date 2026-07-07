from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import (
    ChangePassword,
    ForgotPassword,
    MessageResponse,
    RefreshToken,
    ResetPassword,
    TokenResponse,
    UserCreate,
    UserLogin,
)
from app.services.user_service import (
    authenticate_user,
    change_user_password,
    refresh_user_tokens,
    register_user,
    request_password_reset,
    reset_user_password,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=MessageResponse)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    register_user(db, payload.email, payload.username, payload.password)
    logger.info("New registration: %s", payload.email)
    return {"message": "Registration successful. You can now log in."}


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, request: Request, db: Session = Depends(get_db)):
    user, access_token, refresh_token = authenticate_user(db, payload.email, payload.password, request)
    secure = request.url.scheme == "https"
    response = Response(
        status_code=200,
        content=TokenResponse(access_token=access_token, refresh_token=refresh_token).model_dump_json(),
        media_type="application/json",
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=secure,
        max_age=1800,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=secure,
        max_age=604800,
    )
    return response


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshToken, db: Session = Depends(get_db)):
    access_token, refresh_token = refresh_user_tokens(db, payload.refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    change_user_password(db, current_user, payload.current_password, payload.new_password)
    return {"message": "Password changed successfully."}


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPassword, db: Session = Depends(get_db)):
    request_password_reset(db, payload.email)
    return {"message": "If the email exists, a reset link has been sent."}


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPassword, db: Session = Depends(get_db)):
    reset_user_password(db, payload.token, payload.new_password)
    return {"message": "Password reset successful. You can now log in with your new password."}
