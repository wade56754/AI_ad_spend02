---
version: v1.0
status: ready_for_production
layer: infrastructure
owner: wade
last_reviewed: 2025-11-27
baseline: MASTER.md v4.4, SoT Freeze v2.6, Dev-Guides Freeze vFinal, Architecture Freeze v1.0
---

# Environment Variables Guide

## 1. Purpose

定义环境变量管理规范，确保配置安全性、一致性和可追溯性。Environment variables 是连接代码和基础设施的桥梁，管理不当会导致安全漏洞或部署失败。

## 2. Environment Variable Naming Conventions

### 2.1 Backend (Python/FastAPI)

**Naming Pattern**: `UPPERCASE_SNAKE_CASE`

**Categories**:

| Category | Prefix | Example | Description |
|----------|--------|---------|-------------|
| **Database** | `DATABASE_` | `DATABASE_URL` | PostgreSQL connection string |
| **Supabase** | `SUPABASE_` | `SUPABASE_URL`, `SUPABASE_KEY` | Supabase project credentials |
| **Authentication** | `JWT_` | `JWT_SECRET`, `JWT_ALGORITHM` | JWT token signing |
| **CORS** | `CORS_` | `CORS_ORIGINS` | Allowed frontend origins |
| **Environment** | `ENVIRONMENT` | `ENVIRONMENT=production` | Deployment environment |
| **Logging** | `LOG_` | `LOG_LEVEL` | Log level (DEBUG, INFO, WARNING, ERROR) |

### 2.2 Frontend (Next.js/TypeScript)

**Naming Pattern**: `NEXT_PUBLIC_*` (for client-side) or `UPPERCASE_SNAKE_CASE` (for server-side)

**Categories**:

| Category | Prefix | Example | Description |
|----------|--------|---------|-------------|
| **Public API** | `NEXT_PUBLIC_API_` | `NEXT_PUBLIC_API_URL` | Backend API URL (exposed to browser) |
| **Supabase** | `NEXT_PUBLIC_SUPABASE_` | `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL (public) |
| **Server-only** | No prefix | `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key (server-side only) |

**Important**: Only `NEXT_PUBLIC_*` variables are exposed to the browser. Never use `NEXT_PUBLIC_` for secrets!

---

## 3. Backend Environment Variables

### 3.1 Production Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require

# Supabase
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_KEY=<anon-key>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>  # Server-side only!

# Authentication
JWT_SECRET=<random-256-bit-secret>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=https://ai-ad-spend.com,https://www.ai-ad-spend.com

# Environment
ENVIRONMENT=production

# Logging
LOG_LEVEL=INFO
```

### 3.2 Development Environment Variables

```bash
# Database (Supabase Local)
DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres

# Supabase (Local)
SUPABASE_URL=http://localhost:54321
SUPABASE_KEY=<local-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<local-service-role-key>

# Authentication (use development secrets)
JWT_SECRET=dev-secret-do-not-use-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (allow localhost)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Environment
ENVIRONMENT=development

# Logging
LOG_LEVEL=DEBUG
```

---

## 4. Frontend Environment Variables

### 4.1 Production Environment Variables

```bash
# Backend API (exposed to browser)
NEXT_PUBLIC_API_URL=https://api.ai-ad-spend.com

# Supabase (exposed to browser)
NEXT_PUBLIC_SUPABASE_URL=https://<project>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon-key>

# Server-side only (not exposed to browser)
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
```

### 4.2 Development Environment Variables

```bash
# Backend API (local)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase (local)
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=<local-anon-key>

# Server-side only
SUPABASE_SERVICE_ROLE_KEY=<local-service-role-key>
```

---

## 5. Environment Variable Management

### 5.1 Local Development (`.env` file)

**Backend** (`backend/.env`):
```bash
# .env file (gitignored!)
DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres
SUPABASE_URL=http://localhost:54321
SUPABASE_KEY=<local-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<local-service-role-key>
JWT_SECRET=dev-secret-do-not-use-in-production
JWT_ALGORITHM=HS256
CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

**Frontend** (`frontend/.env.local`):
```bash
# .env.local file (gitignored!)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=<local-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<local-service-role-key>
```

**Important**: `.env` and `.env.local` are gitignored. Use `.env.example` as template.

**`.gitignore`**:
```
.env
.env.local
.env.production
```

**`.env.example`** (template for developers):
```bash
# Backend .env.example
DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres
SUPABASE_URL=http://localhost:54321
SUPABASE_KEY=<local-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<local-service-role-key>
JWT_SECRET=dev-secret-do-not-use-in-production
JWT_ALGORITHM=HS256
CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

### 5.2 CI/CD (GitHub Secrets)

**Setup**:
1. Navigate to GitHub repository → Settings → Secrets and variables → Actions
2. Add the following secrets:

| Secret Name | Value | Usage |
|------------|-------|-------|
| `DATABASE_URL` | Production database URL | Integration tests |
| `SUPABASE_URL` | Supabase production URL | Integration tests |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | Integration tests |
| `JWT_SECRET` | Production JWT secret | Integration tests |
| `SNYK_TOKEN` | Snyk API token | Security scanning |
| `CODECOV_TOKEN` | Codecov API token | Coverage reporting |

**Access in GitHub Actions**:
```yaml
- name: Run integration tests
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
    SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
    SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
    JWT_SECRET: ${{ secrets.JWT_SECRET }}
  run: pytest tests/integration/
```

### 5.3 Staging (Railway Environment Variables)

**Setup** (Railway Dashboard):
1. Navigate to Railway Project → Variables tab
2. Add the following variables for staging environment:

| Variable | Value | Notes |
|----------|-------|-------|
| `DATABASE_URL` | Supabase staging database URL | Automatically provided by Railway if using Railway PostgreSQL |
| `SUPABASE_URL` | `https://<staging-project>.supabase.co` | From Supabase staging project |
| `SUPABASE_KEY` | Staging anon key | From Supabase staging project |
| `SUPABASE_SERVICE_ROLE_KEY` | Staging service role key | From Supabase staging project |
| `JWT_SECRET` | Staging JWT secret (different from prod!) | Generate with `openssl rand -hex 32` |
| `CORS_ORIGINS` | `https://<staging-url>.vercel.app` | Vercel preview URL |
| `ENVIRONMENT` | `staging` | Deployment environment identifier |
| `LOG_LEVEL` | `INFO` | Log level for staging |

### 5.4 Production (Railway + Vercel Environment Variables)

**Railway (Backend)**:
1. Navigate to Railway Project → Variables tab (Production environment)
2. Add the following variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `DATABASE_URL` | Supabase production database URL | From Supabase production project |
| `SUPABASE_URL` | `https://<prod-project>.supabase.co` | From Supabase production project |
| `SUPABASE_KEY` | Production anon key | From Supabase production project |
| `SUPABASE_SERVICE_ROLE_KEY` | Production service role key | **Never expose to frontend!** |
| `JWT_SECRET` | Production JWT secret | **Rotate quarterly!** |
| `CORS_ORIGINS` | `https://ai-ad-spend.com,https://www.ai-ad-spend.com` | Production domain(s) |
| `ENVIRONMENT` | `production` | Deployment environment identifier |
| `LOG_LEVEL` | `INFO` | Log level for production |

**Vercel (Frontend)**:
1. Navigate to Vercel Project → Settings → Environment Variables
2. Add the following variables for production:

| Variable | Value | Environment | Notes |
|----------|-------|-------------|-------|
| `NEXT_PUBLIC_API_URL` | `https://api.ai-ad-spend.com` | Production | Backend API URL |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://<prod-project>.supabase.co` | Production | Supabase production URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Production anon key | Production | Public, safe to expose |
| `SUPABASE_SERVICE_ROLE_KEY` | Production service role key | Production | **Server-side only!** |

---

## 6. Security Best Practices

### 6.1 Never Commit Secrets to Git

**Anti-Pattern**:
```python
# ❌ BAD: Hardcoded secret in code
JWT_SECRET = "my-secret-key-123"
DATABASE_URL = "postgresql://user:password@localhost/db"
```

**Correct Pattern**:
```python
# ✅ GOOD: Load from environment variables
import os
JWT_SECRET = os.getenv("JWT_SECRET")
DATABASE_URL = os.getenv("DATABASE_URL")

if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable not set")
```

### 6.2 Use Different Secrets per Environment

**Anti-Pattern**:
```bash
# ❌ BAD: Same JWT secret for dev and production
JWT_SECRET=dev-secret-123  # Used in both dev and prod
```

**Correct Pattern**:
```bash
# ✅ GOOD: Different secrets per environment
# Development
JWT_SECRET=dev-secret-do-not-use-in-production

# Production
JWT_SECRET=<random-256-bit-secret>  # Generated with openssl rand -hex 32
```

### 6.3 Rotate Secrets Regularly

**Rotation Schedule**:
| Secret | Rotation Frequency | Process |
|--------|-------------------|---------|
| **JWT Secret** | Quarterly (every 3 months) | Generate new secret → Update Railway/Vercel → Redeploy → Verify → Deactivate old secret |
| **Database Password** | Semi-annually (every 6 months) | Update Supabase password → Update Railway `DATABASE_URL` → Redeploy |
| **API Keys** (Supabase, third-party) | Annually | Regenerate keys in service dashboard → Update Railway/Vercel → Redeploy |

**Rotation Procedure** (JWT Secret):
1. Generate new secret: `openssl rand -hex 32`
2. Add new secret to Railway/Vercel (as `JWT_SECRET_NEW`)
3. Update backend code to accept both `JWT_SECRET` and `JWT_SECRET_NEW` (grace period)
4. Deploy new version
5. After 24 hours, remove `JWT_SECRET` (old secret), rename `JWT_SECRET_NEW` → `JWT_SECRET`
6. Deploy again to use only new secret

### 6.4 Use Secret Scanning

**GitHub Dependabot** (automatically enabled):
- Scans commits for accidentally committed secrets
- Alerts repository admins if secrets detected
- Recommends revoking and rotating secrets

**Pre-commit Hook** (optional):
```bash
# .git/hooks/pre-commit
#!/bin/bash
# Check for potential secrets in staged files
git diff --cached --name-only | xargs grep -E "(SECRET|PASSWORD|API_KEY|TOKEN)" && echo "⚠️  Warning: Potential secret detected!" && exit 1
exit 0
```

---

## 7. Environment Variable Validation

### 7.1 Backend Validation (Pydantic Settings)

**File**: `backend/app/config.py`

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str

    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_service_role_key: str

    # Authentication
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # CORS
    cors_origins: str  # Comma-separated list

    # Environment
    environment: str = "development"

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

# Initialize settings (validates environment variables at startup)
settings = Settings()
```

**Startup Validation**:
```python
# backend/app/main.py
from app.config import settings

@app.on_event("startup")
async def startup_event():
    # Validate environment variables (Pydantic raises error if missing)
    print(f"Environment: {settings.environment}")
    print(f"Database URL: {settings.database_url[:20]}...")  # Don't log full URL
    print(f"Supabase URL: {settings.supabase_url}")
    print(f"CORS Origins: {settings.cors_origins_list}")
```

### 7.2 Frontend Validation (TypeScript)

**File**: `frontend/lib/config.ts`

```typescript
// Validate required environment variables at build time
const requiredEnvVars = [
  'NEXT_PUBLIC_API_URL',
  'NEXT_PUBLIC_SUPABASE_URL',
  'NEXT_PUBLIC_SUPABASE_ANON_KEY',
] as const;

for (const envVar of requiredEnvVars) {
  if (!process.env[envVar]) {
    throw new Error(`Missing required environment variable: ${envVar}`);
  }
}

export const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL!,
  supabase: {
    url: process.env.NEXT_PUBLIC_SUPABASE_URL!,
    anonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  },
} as const;
```

---

## 8. Traceability

### 8.1 References to Dev-Guides Layer

| Dev-Guide Document | Environment Variable Usage |
|--------------------|---------------------------|
| [DEPLOYMENT_GUIDE.md](../3.dev-guides/DEPLOYMENT_GUIDE.md) | Lists all required environment variables for deployment |

### 8.2 References to SoT Layer

| SoT Document | Environment Variable Impact |
|--------------|---------------------------|
| [AUTH_SPEC.md](../2.sot/AUTH_SPEC.md) v2.0 | JWT token configuration (`JWT_SECRET`, `JWT_ALGORITHM`) |
| [DATA_SCHEMA.md](../2.sot/DATA_SCHEMA.md) v5.2 | Database connection (`DATABASE_URL`) |

---

## 9. Troubleshooting

### 9.1 Common Issues

| Issue | Root Cause | Resolution |
|-------|-----------|-----------|
| `Missing required environment variable: JWT_SECRET` | `.env` file not loaded or variable not set | Create `.env` file, add `JWT_SECRET=<value>` |
| `CORS error: Origin not allowed` | `CORS_ORIGINS` doesn't include frontend URL | Update `CORS_ORIGINS` to include frontend URL |
| `Database connection failed` | `DATABASE_URL` incorrect or database down | Verify `DATABASE_URL` format, check database status |
| `Supabase client initialization failed` | `SUPABASE_URL` or `SUPABASE_KEY` incorrect | Verify Supabase credentials in dashboard |

---

**Document Version**: v1.0
**Last Updated**: 2025-11-27
**Baseline**: MASTER.md v4.4, SoT Freeze v2.6, Dev-Guides Freeze vFinal, Architecture Freeze v1.0
