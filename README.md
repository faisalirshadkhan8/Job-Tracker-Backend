# Job Application Tracker

[![CI/CD Pipeline](https://github.com/YOUR_USERNAME/job-application-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/job-application-tracker/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Django 6.0](https://img.shields.io/badge/django-6.0-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready Django REST API for tracking job applications, interviews, and analytics with AI-powered features.

## Features

- 🔐 **JWT Authentication** - Secure token-based auth with refresh tokens
- ✉️ **Email Verification** - Verify email on registration with Resend
- 🔑 **Password Reset** - Secure password reset via email
- 📝 **Application Tracking** - Track job applications with status management
- 🏢 **Company Management** - Organize companies you're applying to
- 📅 **Interview Scheduling** - Schedule and prepare for interviews
- 📊 **Analytics Dashboard** - Visualize your job search progress
- 📄 **Resume Storage** - Upload resumes to Cloudinary
- 🤖 **AI Features** - Cover letters, job match, interview prep (Groq)
- ⚡ **Async AI with Celery** - Background task processing for AI generation
- � **Email Notifications** - Interview reminders & weekly summaries
- 📤 **Data Exports** - Export applications to CSV/JSON/Excel
- 🪝 **Webhooks** - Real-time event notifications to external services
- 🔐 **Two-Factor Authentication (2FA)** - TOTP-based security
- �🔍 **Advanced Filtering** - Search and filter all resources
- 📚 **API Documentation** - Swagger/OpenAPI at `/api/docs/`
- 🐳 **Docker Support** - PostgreSQL + Redis + Celery containers
- ✅ **143+ Tests** - Comprehensive test coverage
- 🚀 **CI/CD Pipeline** - GitHub Actions for automated testing

## Tech Stack

- **Backend:** Django 6.0, Django REST Framework
- **Database:** PostgreSQL 16 (via Docker)
- **Cache:** Redis 7 (via Docker)
- **Task Queue:** Celery with Beat (async AI, notifications)
- **Authentication:** JWT + 2FA (TOTP via pyotp)
- **File Storage:** Cloudinary
- **Email:** Resend
- **AI:** Groq (llama-3.3-70b-versatile)
- **Webhooks:** httpx (async HTTP delivery)
- **API Docs:** drf-spectacular (Swagger UI)
- **Testing:** pytest + pytest-django
- **CI/CD:** GitHub Actions

## Project Structure

```
mysite/
├── .github/workflows/     # CI/CD pipelines
│   └── ci.yml
├── config/                # Project configuration
│   ├── settings/
│   │   ├── base.py       # Common settings
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── users/            # Auth, profiles, email verification
│   ├── companies/        # Company management
│   ├── applications/     # Job applications
│   ├── interviews/       # Interview tracking
│   ├── analytics/        # Dashboard & statistics
│   ├── ai/               # AI-powered features
│   ├── notifications/    # Email reminders & preferences
│   ├── exports/          # Data export (CSV/JSON/Excel)
│   ├── webhooks/         # Webhook event delivery
│   └── twofa/            # Two-factor authentication
├── services/             # External service integrations
│   ├── cloudinary_service.py
│   ├── email_service.py
│   ├── groq_service.py
│   └── sanitizer.py
├── templates/emails/     # Email templates
├── tests/                # Test suite (143+ tests)
├── requirements/
├── docker-compose.yml
├── Dockerfile
├── Makefile
└── manage.py
```

## Quick Start

### 1. Clone and Setup Virtual Environment

```bash
cd mysite
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 2. Install Dependencies

```bash
pip install -r requirements/development.txt
```

### 3. Setup Environment Variables

```bash
copy .env.example .env
# Edit .env with your settings
```

### 4. Start PostgreSQL with Docker

```bash
docker-compose up -d
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Run Development Server

```bash
python manage.py runserver
```

### 8. Access API Documentation

Open http://127.0.0.1:8000/api/docs/ for Swagger UI

## API Endpoints

### Authentication
- `POST /api/v1/auth/register/` - Register new user
- `POST /api/v1/auth/login/` - Login (get JWT tokens)
- `POST /api/v1/auth/logout/` - Logout
- `POST /api/v1/auth/token/refresh/` - Refresh access token
- `GET/PUT /api/v1/auth/profile/` - User profile

### Companies
- `GET /api/v1/companies/` - List companies
- `POST /api/v1/companies/` - Create company
- `GET /api/v1/companies/{id}/` - Get company
- `PUT /api/v1/companies/{id}/` - Update company
- `DELETE /api/v1/companies/{id}/` - Delete company

### Applications
- `GET /api/v1/applications/` - List applications
- `POST /api/v1/applications/` - Create application
- `GET /api/v1/applications/{id}/` - Get application details
- `PUT /api/v1/applications/{id}/` - Update application
- `PATCH /api/v1/applications/{id}/status/` - Quick status update
- `DELETE /api/v1/applications/{id}/` - Delete application

### Interviews
- `GET /api/v1/interviews/` - List interviews
- `GET /api/v1/interviews/upcoming/` - Get upcoming interviews
- `GET /api/v1/interviews/today/` - Get today's interviews
- `POST /api/v1/interviews/` - Create interview
- `PATCH /api/v1/interviews/{id}/outcome/` - Update outcome

### Analytics
- `GET /api/v1/analytics/dashboard/` - Main dashboard stats
- `GET /api/v1/analytics/response-rate/` - Response rate by source
- `GET /api/v1/analytics/funnel/` - Application funnel
- `GET /api/v1/analytics/weekly/` - Weekly activity

### AI Features (Async)
- `POST /api/v1/ai/cover-letter/generate/` - Generate cover letter
- `POST /api/v1/ai/job-match/analyze/` - Analyze job match
- `POST /api/v1/ai/interview-questions/generate/` - Generate interview questions
- `GET /api/v1/ai/tasks/` - List async AI tasks
- `GET /api/v1/ai/tasks/{id}/` - Get task status/result
- `POST /api/v1/ai/tasks/{id}/cancel/` - Cancel pending task
- `GET /api/v1/ai/history/` - AI generation history

### Notifications
- `GET /api/v1/notifications/preferences/` - Get notification preferences
- `PUT /api/v1/notifications/preferences/` - Update preferences
- `GET /api/v1/notifications/log/` - Get notification history
- `GET /api/v1/notifications/log/{id}/` - Get specific notification

### Data Exports
- `POST /api/v1/exports/applications/` - Export applications (CSV/JSON/Excel)
- `GET /api/v1/exports/` - List export history
- `GET /api/v1/exports/{id}/` - Get export details/download

### Webhooks
- `GET /api/v1/webhooks/endpoints/` - List webhook endpoints
- `POST /api/v1/webhooks/endpoints/` - Create webhook endpoint
- `DELETE /api/v1/webhooks/endpoints/{id}/` - Delete endpoint
- `POST /api/v1/webhooks/endpoints/{id}/rotate-secret/` - Rotate secret
- `GET /api/v1/webhooks/deliveries/` - List delivery attempts

### Two-Factor Authentication (2FA)
- `POST /api/v1/auth/2fa/setup/` - Start 2FA setup (get QR code)
- `POST /api/v1/auth/2fa/enable/` - Enable 2FA with TOTP code
- `POST /api/v1/auth/2fa/disable/` - Disable 2FA
- `POST /api/v1/auth/2fa/verify/` - Verify TOTP code
- `GET /api/v1/auth/2fa/backup-codes/` - Get backup codes

## Running Celery (Async AI Tasks & Notifications)

For async AI processing and scheduled notifications, start Celery:

```bash
# Development - Worker (local)
celery -A config worker -l info

# Development - Beat scheduler (for notifications)
celery -A config beat -l info

# Production (via Docker - both start automatically)
docker-compose up -d
```

## Environment Variables

Create a `.env` file with these variables:

```env
# Required
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=jobtracker
DB_USER=jobtracker_user
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Cloudinary (file uploads)
CLOUDINARY_CLOUD_NAME=your-cloud
CLOUDINARY_API_KEY=your-key
CLOUDINARY_API_SECRET=your-secret

# AI (Groq)
GROQ_API_KEY=your-groq-key
MODEL=llama-3.3-70b-versatile

# Email (Resend)
RESEND_API_KEY=your-resend-key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# 2FA (optional)
TWOFA_ISSUER_NAME=JobTracker

# Webhooks (optional)
WEBHOOK_TIMEOUT=30
WEBHOOK_MAX_RETRIES=3
```

## License

MIT
