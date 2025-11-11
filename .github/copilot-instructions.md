# Copilot Instructions - Santé Medical Platform

## Project Overview
This is a **FastAPI-based medical appointment platform** (inspired by Doctolib) with a Svelte frontend. The backend provides comprehensive REST APIs for doctors, patients, and administrators to manage medical appointments, consultations, and patient records.

**Core architecture**: FastAPI backend + PostgreSQL + Redis + Celery + Svelte frontend (under development)

## Critical Architecture Patterns

### Multi-Role System
- **Three user roles**: `patient`, `doctor`, `admin` (see `app/models/user.py::UserRole`)
- Role-based access enforced via dependencies in `app/core/dependencies.py`
- Use `get_current_doctor()`, `get_current_patient()`, `get_current_admin()` or `require_role([UserRole.DOCTOR])` for endpoint protection
- Doctors require `admin_approved=True` AND `is_verified=True` before accessing doctor endpoints

### Database & Migrations
- **Alembic** for all schema changes - NEVER modify tables directly
- Run `alembic revision --autogenerate -m "description"` then `alembic upgrade head`
- Base model: `app.core.database.Base` (SQLAlchemy declarative)
- Enum types are PostgreSQL-native (e.g., `SpecialtyEnum`, `AppointmentStatusEnum`)
- Key tables: `users`, `doctor_profiles`, `appointments`, `doctor_schedule_entries`, `email_blacklist`

### Authentication Flow
1. Registration via `/api/v1/auth/register` (role-specific schemas: `PatientRegister`, `PractitionerRegister`)
2. Email verification required (`VerificationToken` model, configurable via `EMAIL_ENABLED`)
3. Login returns JWT access + refresh tokens (30min/7day expiry - see `app/core/config.py`)
4. Token validation in `app/core/dependencies::get_current_user()`
5. Account lockout after 5 failed attempts (15min) - uses Redis (`app/core/security::AccountLockout`)

### Service Layer Pattern
- **All business logic** goes in `app/services/*.py` (not in endpoints!)
- Services are stateless classes with static methods or factory-created instances
- Example services: `AuthService`, `DoctorService`, `EmailService`, `BlacklistService`
- Endpoints in `app/api/v1/endpoints/*.py` handle HTTP concerns only (validation, responses)

### Doctor Module Specifics
- Doctor profile creation is **separate** from user registration (`POST /doctors/`)
- `rpps_number` (French medical ID) is now OPTIONAL but must be unique if provided
- Weekly schedules use `DoctorScheduleEntry` (recurring) + `DoctorBlockedSlot` (exceptions)
- Appointments link to `doctor_id` (profile) NOT `user_id`
- Statistics calculated on-demand (no caching yet) via `GET /doctors/statistics`

## Development Workflow

### Running the Project
```bash
# Start all services (Postgres, Redis, Mailpit, Backend, Celery)
docker-compose up -d

# Backend only (with hot reload)
docker-compose up backend

# Check service health
docker-compose ps
curl http://localhost:8000/health
```

### Database Commands
```bash
# Create migration after model changes
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback one version
docker-compose exec backend alembic downgrade -1

# Access database shell
docker-compose exec postgres psql -U sante_user -d sante_db
```

### Testing
- Use provided shell scripts: `backend/test_doctor_module.sh`, `test_doctor_patients_api.sh`
- Pytest fixtures in `backend/tests/conftest.py` (in-memory SQLite for unit tests)
- Manual testing via Swagger UI: http://localhost:8000/docs

## Code Conventions

### Password Validation
- **12+ characters** minimum (enforced in `app/core/password_policy.py`)
- Requires: uppercase, lowercase, digit, special char (!@#$%^&*(),.?":{}|<>)
- Test password format: `SecurePass123!`

### Email System (Development)
- Uses **Mailpit** for local testing (SMTP on port 1025, UI on http://localhost:8025)
- Production ready for Amazon SES (set `EMAIL_PROVIDER=ses` in `.env`)
- Email templates in `app/services/email_service.py` (`send_appointment_confirmation`, `send_password_reset`, etc.)
- Emails sent async via Celery tasks (`app/tasks.py::send_email_task`)

### Logging
- Structured JSON logging in production (`app/core/logging.py`)
- Use `logger.info(f"[ACTION] | action=event_name | key=value")` format
- Available via `get_logger(__name__)` - don't create raw loggers

### Error Handling
- Custom errors in `app/core/errors.py` (`APIError` with error codes)
- Return HTTP exceptions with detail messages (FastAPI auto-converts to JSON)
- Email blacklist checked before registration (`app/services/blacklist_service.py`)

## API Versioning
- Current version: `/api/v1/*` (see `app/api/v1/__init__.py`)
- Future versions planned in `app/api/v2/` (endpoint compatibility via `app/api/v1/versioning.py`)

## Frontend Integration (In Progress)
- **Svelte 5 + TypeScript + Tailwind CSS** in `backoff/frontend/`
- API client uses Axios (base URL: `http://localhost:8000`)
- Frontend empty currently - use Swagger for API testing
- Medical theme colors: Primary Green #00B894, Medical Blue #3498DB

## Key Files to Reference
- Config: `backend/app/core/config.py` (all env vars, defaults)
- Security: `backend/app/core/security.py` (JWT, rate limiting, account lockout)
- Enums: `backend/app/models/doctor.py` (SpecialtyEnum, ConsultationTypeEnum, AppointmentStatusEnum)
- Dependencies: `backend/app/core/dependencies.py` (auth & role checks)
- Quick Start: `backend/DOCTOR_QUICK_START.md` (doctor module testing guide)
- Email Setup: `backend/EMAIL_SETUP.md` (Mailpit + SES configuration)

## Common Pitfalls
- **Don't** create database tables manually - use Alembic migrations
- **Don't** put business logic in API endpoints - use service layer
- **Always** use `Depends(get_current_doctor)` for doctor-only endpoints (not just `get_current_user`)
- **Remember** doctors need BOTH `is_verified=True` AND `admin_approved=True`
- **Check** email blacklist before user registration (`blacklist_service.is_email_blacklisted()`)
- **Never** commit `.env` files or expose `SECRET_KEY` in code
- **Test** with provided scripts before claiming endpoints work

## Next Steps for AI Agents
When adding features, maintain these patterns:
1. Create Pydantic schemas first (`app/schemas/*.py`)
2. Add service methods (`app/services/*.py`)
3. Create endpoints with proper dependencies (`app/api/v1/endpoints/*.py`)
4. Write Alembic migration if DB changes needed
5. Add audit logging for sensitive operations
6. Test with shell scripts or Swagger UI
