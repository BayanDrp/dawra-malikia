from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import LoginLogResponse, MessageResponse, UserResponse, UserUpdate
from app.services.user_service import get_login_history, update_user_profile

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
def update_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_user_profile(db, current_user, payload.display_name, payload.email_notifications)


@router.get("/me/login-history", response_model=list[LoginLogResponse])
def login_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_login_history(db, current_user)
