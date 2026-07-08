from __future__ import annotations

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.config import settings
from app.utils.logging import get_logger
from app.utils.sanitize import h

logger = get_logger(__name__)

FROM_EMAIL = settings.ADMIN_EMAIL or "noreply@example.com"
FROM_NAME = settings.APP_NAME


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    if not settings.SENDGRID_API_KEY:
        logger.warning("SENDGRID_API_KEY not set — skipping email to %s", to_email)
        return False

    try:
        message = Mail(
            from_email=(FROM_EMAIL, FROM_NAME),
            to_emails=to_email,
            subject=subject,
            html_content=html_body,
        )
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)

        logger.info("Email sent to %s — subject: %s (status: %s)", to_email, subject, response.status_code)
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, e)
        return False


def send_login_notification(to_email: str, username: str, ip_address: str | None, user_agent: str | None) -> bool:
    subject = f"تسجيل دخول جديد إلى حسابك في {settings.APP_NAME}"
    html = f"""\
<!DOCTYPE html>
<html dir="rtl">
<head><meta charset="utf-8"></head>
<body style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:20px;">
  <h2>تم اكتشاف تسجيل دخول جديد</h2>
  <p>مرحباً {h(username)}،</p>
  <p>تم تسجيل دخول جديد إلى حسابك.</p>
  <table style="border-collapse:collapse;width:100%;">
    <tr><td style="padding:8px;background:#f5f5f5;"><strong>عنوان IP:</strong></td><td style="padding:8px;">{h(ip_address) or "غير معروف"}</td></tr>
    <tr><td style="padding:8px;background:#f5f5f5;"><strong>المتصفح:</strong></td><td style="padding:8px;">{h(user_agent) or "غير معروف"}</td></tr>
  </table>
  <p>إذا كان هذا أنت، يمكنك تجاهل هذا البريد.</p>
  <p>إذا لم تكن أنت من سجل الدخول، يرجى تغيير كلمة المرور فوراً.</p>
</body>
</html>"""
    return send_email(to_email, subject, html)


def send_admin_notification(full_name: str, email: str, phone: str, city: str) -> bool:
    admin_email = settings.ADMIN_EMAIL
    if not admin_email:
        logger.info("ADMIN_EMAIL not set — skipping admin notification")
        return False
    subject = f"تسجيل جديد في الدورة: {full_name}"
    html = f"""\
<!DOCTYPE html>
<html dir="rtl">
<head><meta charset="utf-8"></head>
<body style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:20px;">
  <h2>تسجيل جديد</h2>
  <p>تم تسجيل مشارك جديد في الدورة العلمية الأولى:</p>
  <table style="border-collapse:collapse;width:100%;">
    <tr><td style="padding:8px;background:#f5f5f5;"><strong>الاسم:</strong></td><td style="padding:8px;">{h(full_name)}</td></tr>
    <tr><td style="padding:8px;background:#f5f5f5;"><strong>البريد:</strong></td><td style="padding:8px;">{h(email)}</td></tr>
    <tr><td style="padding:8px;background:#f5f5f5;"><strong>الهاتف:</strong></td><td style="padding:8px;" dir="ltr">{h(phone)}</td></tr>
    <tr><td style="padding:8px;background:#f5f5f5;"><strong>المدينة:</strong></td><td style="padding:8px;">{h(city)}</td></tr>
  </table>
  <p><a href="{h(settings.SITE_URL)}/admin" style="display:inline-block;padding:10px 20px;background:#10b981;color:#fff;text-decoration:none;border-radius:4px;">عرض في لوحة التحكم</a></p>
</body>
</html>"""
    return send_email(admin_email, subject, html)


def send_admin_reply(to_email: str, full_name: str, subject: str, message: str) -> bool:
    html = f"""\
<!DOCTYPE html>
<html dir="rtl">
<head><meta charset="utf-8"></head>
<body style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:20px;">
  <h2>{h(subject)}</h2>
  <p>السلام عليكم {h(full_name)}،</p>
  <div style="line-height:1.8;">{h(message)}</div>
  <hr style="margin-top:24px;">
  <p style="color:#888;font-size:0.85rem;">هذا بريد تلقائي من منصة التسجيل في الدورة العلمية الأولى.</p>
</body>
</html>"""
    return send_email(to_email, subject, html)


def send_password_reset_email(to_email: str, username: str, reset_link: str) -> bool:
    subject = f"إعادة تعيين كلمة المرور لحسابك في {settings.APP_NAME}"
    html = f"""\
<!DOCTYPE html>
<html dir="rtl">
<head><meta charset="utf-8"></head>
<body style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:20px;">
  <h2>إعادة تعيين كلمة المرور</h2>
  <p>مرحباً {h(username)}،</p>
  <p>لقد تلقينا طلباً لإعادة تعيين كلمة المرور الخاصة بك.</p>
  <p><a href="{h(reset_link)}" style="display:inline-block;padding:12px 24px;background:#1a73e8;color:#fff;text-decoration:none;border-radius:4px;">إعادة تعيين كلمة المرور</a></p>
  <p>أو انسخ هذا الرابط في متصفحك:</p>
  <p><code>{h(reset_link)}</code></p>
  <p>ينتهي صلاحية هذا الرابط بعد ساعة واحدة.</p>
  <p>إذا لم تطلب ذلك، يرجى تجاهل هذا البريد.</p>
</body>
</html>"""
    return send_email(to_email, subject, html)
