---
version: v1.0
status: ready_for_production
layer: infrastructure
owner: wade
last_reviewed: 2025-11-27
baseline: MASTER.md v4.4, SoT Freeze v2.6, Dev-Guides Freeze vFinal, Architecture Freeze v1.0
---

# CI Pipeline Specification

## 1. Purpose

定义持续集成（CI）流程规范，确保代码质量门控在合并到主分支之前得到验证。CI Pipeline 是代码质量的第一道防线，通过自动化测试、代码检查和安全扫描，确保每次代码提交都符合项目标准。

## 2. Scope

本文档覆盖:
- GitHub Actions workflow 定义
- CI Pipeline 触发条件
- Pipeline 各阶段（Linting, Type Checking, Testing, Building, Security Scanning）
- Quality Gates（质量门控）
- Artifact 管理
- Failure 处理流程

---

## 3. CI Pipeline Overview

### 3.1 Pipeline Architecture

```
GitHub Push/PR → Trigger CI → [Stage 1: Lint & Format]
                                     ↓
                             [Stage 2: Type Check]
                                     ↓
                             [Stage 3: Unit Tests]
                                     ↓
                             [Stage 4: Integration Tests]
                                     ↓
                             [Stage 5: Build]
                                     ↓
                             [Stage 6: Security Scan]
                                     ↓
                             [Quality Gates Check]
                                     ↓
                             ✅ Pass / ❌ Fail
```

### 3.2 Trigger Conditions

| Event | Trigger | Purpose |
|-------|---------|---------|
| **Push to `main`** | ✅ Yes | Verify main branch integrity |
| **Push to `develop`** | ✅ Yes | Verify develop branch integrity |
| **Pull Request** | ✅ Yes | Block merge if CI fails |
| **Manual Dispatch** | ✅ Yes | Ad-hoc testing |
| **Schedule (Nightly)** | ✅ Yes | Catch flaky tests, dependency issues |

---

## 4. Pipeline Stages

### 4.1 Stage 1: Linting & Formatting

**Purpose**: 确保代码风格一致性，捕获基本语法错误。

#### Backend (Python)

**Tools**:
- **Black**: Python code formatter (opinionated, enforces PEP 8)
- **Ruff**: Fast Python linter (replaces Flake8, isort, pyupgrade)

**Commands**:
```bash
# Backend linting
cd backend
black --check .
ruff check .
```

**Quality Gate**:
- ✅ Pass: Zero linting errors, zero formatting issues
- ❌ Fail: Any linting errors or formatting violations

**Configuration**:
- **pyproject.toml** (Black + Ruff config)
```toml
[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]  # Line too long (handled by Black)
```

#### Frontend (TypeScript)

**Tools**:
- **ESLint**: JavaScript/TypeScript linter (with Next.js config)
- **Prettier**: Code formatter

**Commands**:
```bash
# Frontend linting
cd frontend
npm run lint        # ESLint
npm run format:check  # Prettier
```

**Quality Gate**:
- ✅ Pass: Zero ESLint errors, zero Prettier violations
- ❌ Fail: Any linting errors or formatting issues

**Configuration**:
- **.eslintrc.json** (ESLint config)
```json
{
  "extends": ["next/core-web-vitals", "prettier"],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/no-explicit-any": "warn"
  }
}
```

---

### 4.2 Stage 2: Type Checking

**Purpose**: 捕获类型错误，确保类型安全。

#### Backend (Python)

**Tool**: **Mypy** (static type checker for Python)

**Command**:
```bash
cd backend
mypy app/ --strict
```

**Quality Gate**:
- ✅ Pass: Zero type errors
- ❌ Fail: Any type errors

**Configuration**:
- **pyproject.toml** (Mypy config)
```toml
[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true
```

#### Frontend (TypeScript)

**Tool**: **TypeScript Compiler** (`tsc`)

**Command**:
```bash
cd frontend
npm run type-check  # tsc --noEmit
```

**Quality Gate**:
- ✅ Pass: Zero TypeScript errors
- ❌ Fail: Any TypeScript errors

**Configuration**:
- **tsconfig.json** (TypeScript config)
```json
{
  "compilerOptions": {
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true
  }
}
```

---

### 4.3 Stage 3: Unit Tests

**Purpose**: 验证单元测试覆盖率和测试通过率。

#### Backend (Python)

**Tool**: **Pytest** + **pytest-cov** (coverage plugin)

**Command**:
```bash
cd backend
pytest tests/unit/ --cov=app --cov-report=xml --cov-report=term
```

**Quality Gate**:
- ✅ Pass: Coverage ≥ 80%, all tests pass
- ❌ Fail: Coverage < 80% or any test failure

**Coverage Thresholds** (from [TESTING_STRATEGY.md](../3.dev-guides/TESTING_STRATEGY.md)):
- **Unit Tests**: ≥ 80% coverage
- **Critical Modules** (accounting, state machine): ≥ 90% coverage

#### Frontend (TypeScript)

**Tool**: **Jest** + **React Testing Library**

**Command**:
```bash
cd frontend
npm run test:unit -- --coverage
```

**Quality Gate**:
- ✅ Pass: Coverage ≥ 80%, all tests pass
- ❌ Fail: Coverage < 80% or any test failure

**Configuration**:
- **jest.config.js** (Jest config)
```javascript
module.exports = {
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};
```

---

### 4.4 Stage 4: Integration Tests

**Purpose**: 验证 API 契约和数据库集成测试。

#### Backend (Python)

**Tool**: **Pytest** with **TestClient** (FastAPI) + **Supabase Test Database**

**Command**:
```bash
cd backend
pytest tests/integration/ --cov=app --cov-report=xml
```

**Quality Gate**:
- ✅ Pass: Coverage ≥ 70%, all tests pass
- ❌ Fail: Coverage < 70% or any test failure

**Test Scope**:
- API endpoint testing (`GET /api/v1/daily-reports`, `POST /api/v1/topups`, etc.)
- Database transaction testing (rollback, commit, isolation)
- State machine transition testing (8-state workflow validation)

**Configuration**:
- **pytest.ini** (Pytest config)
```ini
[pytest]
testpaths = tests/integration
```

#### Frontend (TypeScript)

**Tool**: **Jest** + **MSW** (Mock Service Worker for API mocking)

**Command**:
```bash
cd frontend
npm run test:integration
```

**Quality Gate**:
- ✅ Pass: Coverage ≥ 70%, all tests pass
- ❌ Fail: Coverage < 70% or any test failure

**Test Scope**:
- API call integration (React Query hooks with MSW)
- Form submission flows
- Authentication flows (login, MFA, logout)

---

### 4.5 Stage 5: Build

**Purpose**: 验证代码可以成功构建为生产 artifacts。

#### Backend (Python)

**Tool**: **Docker** (multi-stage build)

**Command**:
```bash
cd backend
docker build -t ai-ad-backend:${GITHUB_SHA} .
```

**Quality Gate**:
- ✅ Pass: Docker image builds successfully
- ❌ Fail: Build errors (dependency issues, syntax errors)

**Dockerfile** (multi-stage build):
```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend (TypeScript)

**Tool**: **Next.js** build

**Command**:
```bash
cd frontend
npm run build  # next build
```

**Quality Gate**:
- ✅ Pass: Next.js build succeeds, no warnings
- ❌ Fail: Build errors or critical warnings

**Build Artifacts**:
- `.next/` directory (optimized production build)
- Static pages (pre-rendered at build time)

---

### 4.6 Stage 6: Security Scan

**Purpose**: 检测依赖漏洞和安全风险。

#### Backend (Python)

**Tools**:
- **Snyk**: Dependency vulnerability scanning
- **Trivy**: Container image vulnerability scanning

**Commands**:
```bash
# Snyk: Scan dependencies
snyk test --file=backend/requirements.txt --severity-threshold=high

# Trivy: Scan Docker image
trivy image --severity HIGH,CRITICAL ai-ad-backend:${GITHUB_SHA}
```

**Quality Gate**:
- ✅ Pass: Zero HIGH or CRITICAL vulnerabilities
- ⚠️ Warn: MEDIUM vulnerabilities (allow merge, create issue)
- ❌ Fail: Any HIGH or CRITICAL vulnerabilities

#### Frontend (TypeScript)

**Tool**: **Snyk** + **npm audit**

**Commands**:
```bash
# Snyk: Scan dependencies
cd frontend
snyk test --severity-threshold=high

# npm audit
npm audit --audit-level=high
```

**Quality Gate**:
- ✅ Pass: Zero HIGH or CRITICAL vulnerabilities
- ⚠️ Warn: MEDIUM vulnerabilities (allow merge, create issue)
- ❌ Fail: Any HIGH or CRITICAL vulnerabilities

---

## 5. Quality Gates Summary

| Gate | Requirement | Enforcement |
|------|-------------|-------------|
| **Linting** | Zero linting errors | ✅ Blocking |
| **Type Checking** | Zero type errors | ✅ Blocking |
| **Unit Tests** | Coverage ≥ 80%, all tests pass | ✅ Blocking |
| **Integration Tests** | Coverage ≥ 70%, all tests pass | ✅ Blocking |
| **Build** | Build succeeds | ✅ Blocking |
| **Security Scan** | Zero HIGH/CRITICAL vulnerabilities | ✅ Blocking |

**Blocking**: CI fails if gate is not met → PR cannot be merged
**Non-Blocking** (planned): CI passes with warnings → PR can be merged, issue created

---

## 6. GitHub Actions Workflows

### 6.1 Backend CI Workflow

**File**: `.github/workflows/ci-backend.yml`

```yaml
name: Backend CI

on:
  push:
    branches: [main, develop]
    paths:
      - 'backend/**'
      - '.github/workflows/ci-backend.yml'
  pull_request:
    branches: [main, develop]
    paths:
      - 'backend/**'
  workflow_dispatch:

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install black ruff
      - name: Lint with Black
        run: cd backend && black --check .
      - name: Lint with Ruff
        run: cd backend && ruff check .

  type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install mypy
      - name: Type check with Mypy
        run: cd backend && mypy app/ --strict

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run unit tests
        run: cd backend && pytest tests/unit/ --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: backend/coverage.xml

  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: cd backend && docker build -t ai-ad-backend:${GITHUB_SHA} .

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Snyk
        uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --file=backend/requirements.txt --severity-threshold=high
```

### 6.2 Frontend CI Workflow

**File**: `.github/workflows/ci-frontend.yml`

```yaml
name: Frontend CI

on:
  push:
    branches: [main, develop]
    paths:
      - 'frontend/**'
      - '.github/workflows/ci-frontend.yml'
  pull_request:
    branches: [main, develop]
    paths:
      - 'frontend/**'
  workflow_dispatch:

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Lint with ESLint
        run: cd frontend && npm run lint
      - name: Check formatting
        run: cd frontend && npm run format:check

  type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Type check
        run: cd frontend && npm run type-check

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Run unit tests
        run: cd frontend && npm run test:unit -- --coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: frontend/coverage/coverage-final.json

  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Build Next.js app
        run: cd frontend && npm run build

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Snyk
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high
```

---

## 7. Environment Variables (CI/CD)

| Variable | Source | Purpose |
|----------|--------|---------|
| `GITHUB_SHA` | GitHub Actions (built-in) | Docker image tagging |
| `SNYK_TOKEN` | GitHub Secrets | Snyk security scanning authentication |
| `CODECOV_TOKEN` | GitHub Secrets | Code coverage reporting |
| `DATABASE_URL` | GitHub Secrets | Integration test database connection |

**Setup**:
```bash
# Add secrets via GitHub UI: Settings → Secrets and variables → Actions
# Example:
# SNYK_TOKEN=<your-snyk-token>
# CODECOV_TOKEN=<your-codecov-token>
```

---

## 8. Failure Handling

### 8.1 CI Failure Workflow

```
CI Failure → GitHub PR Status Check ❌
            ↓
       Notify Developer (email + GitHub notification)
            ↓
       Developer investigates logs
            ↓
       Fix issue + Push new commit
            ↓
       CI re-runs automatically
            ↓
       ✅ Pass → PR can be merged
```

### 8.2 Common Failure Scenarios

| Failure Type | Root Cause | Resolution |
|--------------|-----------|-----------|
| **Linting Error** | Code style violation | Run `black .` (backend) or `npm run format` (frontend) |
| **Type Error** | Missing type annotation | Add type hints (Python) or fix TypeScript types |
| **Unit Test Failure** | Logic error or flaky test | Debug test, fix code, or mark test as `@pytest.mark.flaky` |
| **Coverage Below Threshold** | New code not tested | Add unit tests to cover new code |
| **Build Failure** | Dependency issue or syntax error | Fix dependency versions or syntax |
| **Security Vulnerability** | Outdated dependency | Update dependency: `pip install --upgrade <package>` or `npm update` |

### 8.3 Flaky Test Handling

**Problem**: Tests that intermittently fail due to timing issues, network issues, or race conditions.

**Solution**:
1. Mark flaky tests with `@pytest.mark.flaky` (backend) or `jest.retryTimes(3)` (frontend)
2. Re-run failed tests up to 3 times before marking CI as failed
3. Create issue to fix flaky test root cause

**Example** (Pytest):
```python
import pytest

@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_external_api_integration():
    # Test that may fail due to network issues
    response = requests.get("https://external-api.com")
    assert response.status_code == 200
```

---

## 9. Artifact Management

### 9.1 Build Artifacts

| Artifact | Storage | Retention | Purpose |
|----------|---------|-----------|---------|
| **Docker Images** | GitHub Container Registry (GHCR) | 30 days | Backend deployment to Railway |
| **Coverage Reports** | Codecov | Permanent | Track coverage trends over time |
| **Test Reports** | GitHub Actions Artifacts | 30 days | Debug test failures |

### 9.2 Artifact Upload (Backend)

```yaml
# Upload Docker image to GHCR
- name: Log in to GHCR
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}

- name: Push Docker image
  run: |
    docker tag ai-ad-backend:${GITHUB_SHA} ghcr.io/${{ github.repository }}/backend:${GITHUB_SHA}
    docker push ghcr.io/${{ github.repository }}/backend:${GITHUB_SHA}
```

---

## 10. Monitoring and Metrics

### 10.1 CI Pipeline Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| **Pipeline Success Rate** | ≥ 95% | < 90% |
| **Pipeline Duration** | < 10 minutes | > 15 minutes |
| **Flaky Test Rate** | < 5% | > 10% |
| **Security Vulnerabilities** | 0 HIGH/CRITICAL | Any HIGH/CRITICAL |

### 10.2 Dashboard (Planned)

**Tool**: GitHub Actions Insights (built-in) + Grafana dashboard (planned)

**Metrics to Track**:
- CI success rate by branch (main, develop, feature branches)
- Average CI duration by stage (lint, test, build, security)
- Test coverage trends over time
- Security vulnerability trends

---

## 11. Traceability

### 11.1 References to Dev-Guides Layer

| Dev-Guide Document | CI Pipeline Implementation |
|--------------------|---------------------------|
| [TESTING_STRATEGY.md](../3.dev-guides/TESTING_STRATEGY.md) | Coverage thresholds (80% unit, 70% integration) enforced in Stage 3 & 4 |
| [API_DEVELOPMENT_FLOW.md](../3.dev-guides/API_DEVELOPMENT_FLOW.md) | API tests run in integration test stage |
| [FRONTEND_DEVELOPMENT_RULES.md](../3.dev-guides/FRONTEND_DEVELOPMENT_RULES.md) | ESLint rules enforced in Stage 1 |

### 11.2 References to SoT Layer

| SoT Document | CI Pipeline Validation |
|--------------|------------------------|
| [STATE_MACHINE.md](../sot/STATE_MACHINE.md) v2.6 | State transition tests run in integration tests |
| [DATA_SCHEMA.md](../sot/DATA_SCHEMA.md) v5.2 | Database schema validation tests |
| [ERROR_CODES_SOT.md](../sot/ERROR_CODES_SOT.md) v2.1 | Error code usage tests |

---

## 12. Future Enhancements

### 12.1 Planned Improvements (2026-Q1)

- [ ] Add E2E tests with Playwright (Stage 7)
- [ ] Implement parallel test execution (reduce CI duration from 10min → 5min)
- [ ] Add performance regression tests (lighthouse scores, API response times)
- [ ] Implement automatic dependency updates (Dependabot + auto-merge for patch versions)

### 12.2 Long-Term Goals (2026-H2)

- [ ] Implement dynamic test selection (only run tests affected by code changes)
- [ ] Add chaos engineering tests (inject failures, test resilience)
- [ ] Implement contract testing (Pact.io for API contracts)

---

**Document Version**: v1.0
**Last Updated**: 2025-11-27
**Baseline**: MASTER.md v4.4, SoT Freeze v2.6, Dev-Guides Freeze vFinal, Architecture Freeze v1.0
