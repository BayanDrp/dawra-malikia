from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import CourseRegistration, User
from app.schemas import (
    AdminReply,
    BulkAction,
    CourseRegistrationCreate,
    CourseRegistrationResponse,
    MessageResponse,
    UpdateStatus,
)
from app.services.email_service import send_admin_notification, send_admin_reply
from app.utils.logging import get_logger
from app.utils.ratelimit import check_register_limit, get_ip

logger = get_logger(__name__)

router = APIRouter(tags=["registration"])


@router.post("/api/register", response_model=MessageResponse)
def register_for_course(payload: CourseRegistrationCreate, db: Session = Depends(get_db), _=Depends(check_register_limit)):

    existing = db.query(CourseRegistration).filter(
        CourseRegistration.email == payload.email
    ).first()
    if existing:
        return {"message": "تم تسجيلك مسبقاً. سيتم التواصل معك قريباً."}

    registration = CourseRegistration(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        gender=payload.gender,
        city=payload.city,
        notes=payload.notes,
    )
    db.add(registration)
    db.commit()
    logger.info("New registration: %s (%s)", payload.full_name, payload.email)

    send_admin_notification(payload.full_name, payload.email, payload.phone, payload.city)

    return {"message": "تم التسجيل بنجاح. سيتم التواصل معك قريباً."}


def _build_registrations_query(db: Session, q: str | None, status: str | None):
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
    return query


@router.get("/api/admin/registrations", response_model=list[CourseRegistrationResponse])
def list_registrations(
    q: str | None = Query(None),
    status: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = _build_registrations_query(db, q, status)
    return query.order_by(CourseRegistration.created_at.desc()).all()


@router.get("/api/admin/registrations/count")
def registration_count(
    q: str | None = Query(None),
    status: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = _build_registrations_query(db, q, status)
    total = query.count()
    pending = query.filter(CourseRegistration.status == "pending").count()
    return {"total": total, "pending": pending}


@router.get("/api/admin/registrations/export.csv")
def export_registrations_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    registrations = (
        db.query(CourseRegistration)
        .order_by(CourseRegistration.created_at.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "الاسم", "البريد", "الهاتف", "الجنس", "المدينة", "الحالة", "ملاحظات", "تاريخ التسجيل"])
    for r in registrations:
        writer.writerow([r.id, r.full_name, r.email, r.phone, r.gender, r.city, r.status, r.notes, r.created_at.strftime("%Y-%m-%d %H:%M")])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": "attachment; filename=registrations.csv"},
    )


@router.put("/api/admin/registrations/{reg_id}/status", response_model=MessageResponse)
def update_registration_status(
    reg_id: int,
    payload: UpdateStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reg = db.query(CourseRegistration).filter(CourseRegistration.id == reg_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="التسجيل غير موجود")

    reg.status = payload.status
    db.commit()
    logger.info("Registration %d status updated to %s by %s", reg_id, payload.status, current_user.email)
    return {"message": f"تم تحديث الحالة إلى {payload.status}"}


@router.delete("/api/admin/registrations/{reg_id}", response_model=MessageResponse)
def delete_registration(
    reg_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reg = db.query(CourseRegistration).filter(CourseRegistration.id == reg_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="التسجيل غير موجود")

    db.delete(reg)
    db.commit()
    logger.info("Registration %d deleted by %s", reg_id, current_user.email)
    return {"message": "تم حذف التسجيل بنجاح"}


@router.post("/api/admin/registrations/bulk", response_model=MessageResponse)
def bulk_action(
    payload: BulkAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    registrations = db.query(CourseRegistration).filter(CourseRegistration.id.in_(payload.ids)).all()
    if not registrations:
        raise HTTPException(status_code=404, detail="لم يتم العثور على تسجيلات")

    if payload.action == "delete":
        for reg in registrations:
            db.delete(reg)
        msg = f"تم حذف {len(registrations)} تسجيل"
    else:
        new_status = "approved" if payload.action == "approve" else "rejected"
        for reg in registrations:
            reg.status = new_status
        status_label = "قبول" if new_status == "approved" else "رفض"
        msg = f"تم {status_label} {len(registrations)} تسجيل"

    db.commit()
    logger.info("Bulk %s on %d registrations by %s", payload.action, len(registrations), current_user.email)
    return {"message": msg}


@router.post("/api/admin/registrations/{reg_id}/reply", response_model=MessageResponse)
def reply_to_registrant(
    reg_id: int,
    payload: AdminReply,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reg = db.query(CourseRegistration).filter(CourseRegistration.id == reg_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="التسجيل غير موجود")

    sent = send_admin_reply(reg.email, reg.full_name, payload.subject, payload.message)
    if sent:
        logger.info("Reply sent to %s (%s) by %s", reg.full_name, reg.email, current_user.email)
        return {"message": "تم إرسال الرد بنجاح"}
    else:
        return {"message": "لم يتم إرسال البريد (SMTP غير مهيأ). تم تسجيل الرد محلياً."}
