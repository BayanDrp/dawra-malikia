# الدورة العلمية الأولى في الفقه المالكي

موقع تسجيل وإدارة للدورة العلمية الأولى في الفقه المالكي — شرح مختصر الإمام الأخضري.
تقديم فضيلة الدكتور الإمام أسامة شيبان، بتنظيم جمعية العلماء المسلمين الجزائريين — المكتب الولائي سطيف،
بالتعاون مع معهد محمد بن عبد الكريم المغيلي للتربية القرآنية.

## المميزات

- صفحة هبوط (Landing Page) تعرض تفاصيل الدورة
- نموذج تسجيل للمشاركين (رجال ونساء)
- لوحة تحكم إدارية لمشاهدة المسجلين (محمية بكلمة مرور)
- توثيق آمن (bcrypt + JWT)
- إشعارات البريد الإلكتروني عند تسجيل الدخول
- إعادة تعيين كلمة المرور عبر البريد
- دعم Docker
- مُحسّن لخوادم 512MB RAM المجانية
- ليلة (Dark Mode)
- دعم اللغة العربية (RTL)

## البدء السريع

### 1. الإعداد

```bash
cp .env.example .env
# عدل SECRET_KEY (مطلوب) — استخدم: python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. التشغيل محلياً

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 1
```

فتح http://localhost:8000

### 3. إنشاء حساب إداري

```bash
# استخدم واجهة API للتسجيل
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","username":"admin","password":"your-password-123"}'
```

ثم سجل الدخول على http://localhost:8000/login

### 4. التشغيل مع Docker

```bash
docker compose up --build
```

## هيكل المشروع

```
├── app/
│   ├── main.py               # نقطة الدخول الرئيسية
│   ├── config.py             # الإعدادات (تقرأ من .env)
│   ├── database.py           # قاعدة البيانات (SQLite)
│   ├── models.py             # نماذج ORM
│   ├── schemas.py            # نماذج Pydantic
│   ├── templates.py          # محرك القوالب Jinja2
│   ├── routers/
│   │   ├── auth.py           # تسجيل الدخول والتسجيل
│   │   ├── users.py          # إدارة المستخدمين
│   │   ├── pages.py          # الصفحات (HTML)
│   │   └── registration.py   # تسجيل الدورة (API)
│   ├── services/
│   │   ├── email_service.py  # إرسال البريد
│   │   └── user_service.py   # منطق الأعمال
│   └── utils/
│       ├── security.py       # bcrypt + JWT
│       └── logging.py        # التسجيل (logs)
├── templates/                # قوالب HTML
├── static/                   # ملفات ثابتة (CSS, JS)
├── Dockerfile                # بناء Docker متعدد المراحل
├── docker-compose.yml        # Docker Compose
├── nginx.conf                # Nginx reverse proxy
└── requirements.txt
```

## البيئة (Environment Variables)

| المتغير | إجباري | الافتراضي | الشرح |
|---|---|---|---|
| `SECRET_KEY` | نعم | — | مفتاح سري عشوائي 64 حرفاً |
| `DEBUG` | لا | false | وضع التصحيح |
| `SITE_URL` | لا | http://localhost:8000 | رابط الموقع العلني |
| `DATABASE_URL` | لا | sqlite:///./data/app.db | رابط قاعدة البيانات |
| `SMTP_*` | لا | — | إعدادات البريد (اختياري) |

## النشر

### Render / Railway

```
gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 1
```

### Docker VPS

```bash
docker compose up -d --build
```

أنشئ حساباً إدارياً أولاً عبر API:

```bash
curl -X POST https://your-domain.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","username":"admin","password":"your-password-123"}'
```

## ملفات يجب تعديلها قبل النشر

| الملف | التعديل |
|---|---|
| `.env` | `SECRET_KEY` (إجباري)، `SITE_URL`، `SMTP_*` (اختياري) |
| `nginx.conf` | استبدل `your-domain.com` باسم نطاقك |
