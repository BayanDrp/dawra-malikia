from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def generate_token():
    return uuid.uuid4().hex


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    display_name = Column(String(200), default="")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_notifications = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    login_logs = relationship("LoginLog", back_populates="user", lazy="dynamic")
    reset_tokens = relationship("PasswordResetToken", back_populates="user", lazy="dynamic")


class LoginLog(Base):
    __tablename__ = "login_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    successful = Column(Boolean, default=True)

    user = relationship("User", back_populates="login_logs")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(64), unique=True, nullable=False, index=True, default=generate_token)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="reset_tokens")

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    @classmethod
    def create(cls, user: User, hours: int = 1) -> PasswordResetToken:
        return cls(
            user_id=user.id,
            token=generate_token(),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=hours),
        )


class CourseRegistration(Base):
    __tablename__ = "course_registrations"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(200), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    gender = Column(String(10), nullable=False)
    city = Column(String(100), nullable=False)
    status = Column(String(20), default="pending")
    notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
