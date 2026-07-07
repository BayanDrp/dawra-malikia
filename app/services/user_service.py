from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models import LoginLog, PasswordResetToken, User
from app.services.email_service import send_login_notification, send_password_reset_email
from app.utils.logging import get_logger
from app.utils.sanitize import sanitize_user_agent
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

logger = get_logger(__name__)


def register_user(db: Session, email: str, username: str, password: str) -> User:
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        email=email,
        username=username,
        hashed_password=hash_password(password),
        display_name=username,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("New user registered: %s (%s)", username, email)
    return user


def authenticate_user(db: Session, email: str, password: str, request: Request) -> tuple[User, str, str]:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        logger.warning("Failed login attempt for email: %s", email)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    ip = request.client.host if request.client else None
    ua = sanitize_user_agent(request.headers.get("user-agent"))

    log_entry = LoginLog(user_id=user.id, ip_address=ip, user_agent=ua, successful=True)
    db.add(log_entry)
    db.commit()

    if user.email_notifications:
        send_login_notification(user.email, user.username, ip, ua)

    access_token = create_access_token({"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    logger.info("User logged in: %s (%s)", user.username, user.email)
    return user, access_token, refresh_token


def refresh_user_tokens(db: Session, refresh_token: str) -> tuple[str, str]:
    payload = decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    new_access = create_access_token({"sub": str(user.id), "email": user.email})
    new_refresh = create_refresh_token({"sub": str(user.id)})
    return new_access, new_refresh


def update_user_profile(db: Session, user: User, display_name: str | None, email_notifications: bool | None) -> User:
    if display_name is not None:
        user.display_name = display_name
    if email_notifications is not None:
        user.email_notifications = email_notifications
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user


def change_user_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.hashed_password = hash_password(new_password)
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    logger.info("Password changed for user: %s", user.username)


def request_password_reset(db: Session, email: str) -> None:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        logger.info("Password reset requested for non-existent email: %s", email)
        return

    old_tokens = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used == False,
    ).all()
    for t in old_tokens:
        t.used = True
    db.commit()

    reset_token = PasswordResetToken.create(user)
    db.add(reset_token)
    db.commit()

    reset_link = f"{settings.SITE_URL}/reset-password?token={reset_token.token}"
    send_password_reset_email(user.email, user.username, reset_link)
    logger.info("Password reset email sent to: %s", email)


def reset_user_password(db: Session, token: str, new_password: str) -> None:
    reset = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.used == False,
    ).first()

    if not reset or reset.is_expired():
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = db.query(User).filter(User.id == reset.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    user.hashed_password = hash_password(new_password)
    user.updated_at = datetime.now(timezone.utc)
    reset.used = True
    db.commit()
    logger.info("Password reset completed for user: %s", user.username)


def get_login_history(db: Session, user: User, limit: int = 20) -> list[LoginLog]:
    return (
        db.query(LoginLog)
        .filter(LoginLog.user_id == user.id)
        .order_by(LoginLog.timestamp.desc())
        .limit(limit)
        .all()
    )



