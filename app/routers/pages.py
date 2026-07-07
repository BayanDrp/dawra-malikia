from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import CourseRegistration, User
from app.templates import render_template
from app.utils.security import decode_token

router = APIRouter(tags=["pages"])


def _is_authenticated(request: Request) -> bool:
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        token = auth[7:] if auth.startswith("Bearer ") else None
    if not token:
        return False
    payload = decode_token(token)
    return payload is not None


@router.get("/")
def landing():
    return render_template("landing.html")


@router.get("/login")
def login_page(request: Request):
    if _is_authenticated(request):
        return RedirectResponse(url="/admin", status_code=302)
    return render_template("login.html")


@router.get("/register")
def register_page():
    return RedirectResponse(url="/", status_code=302)


@router.get("/confirmation")
def confirmation_page(name: str = "", email: str = ""):
    return render_template("confirmation.html", name=name, email=email)


@router.get("/forgot-password")
def forgot_password_page():
    return render_template("forgot_password.html")


@router.get("/reset-password")
def reset_password_page(token: str = ""):
    return render_template("reset_password.html", token=token)


@router.get("/admin")
def admin_dashboard(
    request: Request,
    q: str = Query(default=""),
    status: str = Query(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(CourseRegistration)

    if q:
        like = f"%{q}%"
        query = query.filter(
            CourseRegistration.full_name.ilike(like)
            | CourseRegistration.email.ilike(like)
            | CourseRegistration.phone.ilike(like)
            | CourseRegistration.city.ilike(like)
        )
    if status and status in ("pending", "approved", "rejected"):
        query = query.filter(CourseRegistration.status == status)

    registrations = query.order_by(CourseRegistration.created_at.desc()).all()
    total = len(registrations)
    pending = sum(1 for r in registrations if r.status == "pending")

    return render_template(
        "admin.html",
        user=current_user,
        registrations=registrations,
        total=total,
        pending=pending,
        search_q=q,
        filter_status=status,
    )
