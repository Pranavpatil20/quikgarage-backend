# QuikGarage Backend (Django + DRF)

Backend for QuikGarage owner/customer app.

## Tech stack
- Django
- Django REST Framework
- PostgreSQL (production)
- SQLite (local fallback)

## 1) Local setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Option A: Local PostgreSQL with Docker

```bash
docker compose up -d
python manage.py migrate
python manage.py runserver
```

### Option B: SQLite fallback (quick local testing)

```bash
USE_SQLITE=True python manage.py migrate
USE_SQLITE=True python manage.py runserver
```

API base (local):
- `http://127.0.0.1:8000/api/`

## 2) Environment variables

Copy `.env.example` to `.env` and update values.

Main variables:
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `USE_SQLITE`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `WHATSAPP_PROVIDER`
- `FIREBASE_CREDENTIALS_PATH`

## 3) Render deployment

### Build command
```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

### Start command
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

Use internal Render Postgres host for `POSTGRES_HOST` when web service and DB are both on Render.

## 4) Useful API routes
- `POST /api/auth/send-otp/`
- `POST /api/auth/verify-otp/`
- `POST /api/auth/verify-firebase-otp/`
- `GET/PATCH /api/auth/me/`
- `GET /api/bookings/dashboard/`
- `GET /api/bookings/slots/?date=YYYY-MM-DD`
- `POST /api/bookings/`
- `GET /api/customers/`
- `GET/PATCH /api/customers/me/`
- `GET/POST /api/customers/vehicles/`

## 5) Admin

Create superuser:
```bash
python manage.py createsuperuser
```

Admin URL:
- `/admin/`
