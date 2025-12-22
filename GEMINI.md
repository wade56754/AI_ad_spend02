# GEMINI.md - Context & Instructions for Gemini Agents

## 1. Project Overview

**Name:** AI Advertising Spend Management System (AI 广告代投系统)
**Description:** A comprehensive platform for Facebook advertising agencies to manage ad accounts, daily reports, financial reconciliation, and role-based collaboration.
**Key Features:**
*   AI-powered monitoring (anomaly detection, performance forecasting).
*   Automated financial reconciliation.
*   Multi-role collaboration (Media Buyer, Finance, Admin, etc.).
*   Strict "Source of Truth" (SoT) driven architecture.

## 2. Technology Stack

### Backend
*   **Language:** Python 3.11+
*   **Framework:** FastAPI
*   **Data Validation:** Pydantic v2 (`ConfigDict`, `model_dump`)
*   **Database ORM:** SQLAlchemy 2.0 (Async, `select()`, `execute()`)
*   **Migrations:** Alembic
*   **Auth:** JWT + OAuth2 (Supabase integration)
*   **Cache:** Redis

### Frontend
*   **Framework:** Next.js 14+ (App Router)
*   **Language:** TypeScript
*   **State Management:** TanStack Query v5, Zustand
*   **UI Component:** shadcn/ui, Tailwind CSS
*   **HTTP Client:** Custom `apiFetch` wrapper (avoids direct DB access)

### Infrastructure
*   **Database:** PostgreSQL (via Supabase or local Docker)
*   **Containerization:** Docker, Docker Compose

## 3. Critical Architecture Rules (SoT)

**Strict Adherence Required:** All code changes must align with the Source of Truth (SoT) documents in `docs/2.sot/`.

*   **State Machine (Daily Reports):** 8-stage strict pipeline.
    *   `raw_submitted` -> `trend_pending` -> `trend_ok`/`trend_flagged` -> `trend_resolved` -> `final_pending` -> `final_confirmed` -> `final_locked`.
    *   *Prohibited:* `draft`, `pending`, `approved`.
*   **Roles:** 5 valid roles only.
    *   `admin`, `finance`, `data_operator`, `account_manager`, `media_buyer`.
    *   *Prohibited:* `super_admin`, `operator`, `accountant`.
*   **Error Handling:** Must use codes from `docs/2.sot/ERROR_CODES_SOT.md`.
    *   Use `backend.core.error_codes.BusinessError`.
    *   *Prohibited:* Generic `HTTPException` without standard codes.

## 4. Development Workflow

### Setup & Installation
```bash
# Backend
cd backend
python -m venv venv
# Activate venv (Windows: venv\Scripts\activate, Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt

# Frontend
cd frontend
pnpm install

# Database Setup (Docker)
docker-compose up -d postgres redis
cd backend
alembic upgrade head
```

### Running the Application
```bash
# Backend (Port 8000)
cd backend
uvicorn main:app --reload --port 8000

# Frontend (Port 3000)
cd frontend
npm run dev
```

### Testing & Verification
```bash
# Backend Tests
cd backend
pytest tests/ -v
pytest tests/services/test_topup_service.py -v # Specific test

# Frontend Tests
cd frontend
npm test
npm run typecheck # TypeScript validation

# Regression / Full Suite
python run_tests.py --type regression
```

### Code Style & Quality
*   **Python:** PEP 8, Black, isort. Check with `ruff check backend/`.
*   **TypeScript:** Strict mode. No `any`. Check with `npm run lint`.

## 5. Directory Structure Key

*   `backend/`: FastAPI application.
    *   `main.py`: Entry point.
    *   `app/`: Core logic (routers, services, models, schemas).
    *   `alembic/`: DB migrations.
    *   `tests/`: Pytest suite.
*   `frontend/`: Next.js application.
    *   `src/app/`: App router pages.
    *   `src/components/`: Reusable UI.
    *   `src/lib/`: Utilities (API client).
*   `docs/`: Documentation Center.
    *   `2.sot/`: **CRITICAL** Source of Truth documents.
*   `agents/`: AI agent skills and tools.
*   `AGENTS.md`: Specific guidelines for AI coding agents.

## 6. Agent Instructions

1.  **Read `AGENTS.md`**: Before complex tasks, review this file for specific AI-coding protocols.
2.  **Check SoT**: Always cross-reference `docs/2.sot/` before modifying business logic or data schemas.
3.  **No Direct DB**: Frontend must use API endpoints, not direct database calls.
4.  **Use Modern Libraries**: Pydantic v2 and SQLAlchemy 2.0 syntax are mandatory.
