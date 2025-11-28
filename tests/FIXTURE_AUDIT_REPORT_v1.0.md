---
version: v1.0
status: final
type: audit-report
owner: wade
date: 2025-11-27
baseline: STATE_MACHINE.md v2.6, DATA_SCHEMA.md v5.2, AUTH_SPEC.md v2.0, LEDGER_SOT.md v1.1
---

# Pytest Fixture Audit Report v1.0

> **Audit Date**: 2025-11-27
> **Scope**: backend/tests/conftest.py + backend/models/base.py enums
> **Framework**: ASDD SoT Compliance Verification
> **Executor**: Claude AI Agent

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Files Audited** | 2 (conftest.py, base.py) |
| **P0 Issues (Blocking)** | 2 |
| **P1 Issues (High Priority)** | 3 |
| **P2 Issues (Medium Priority)** | 2 |
| **Health Score** | 40/100 (Critical issues found) |
| **Fixture Status** | :x: **NOT READY FOR PRODUCTION** |

---

## 1. P0 Issues (Blocking - Must Fix Before Tests)

### P0-001: UserRole Enum Mismatch

**Location**: `backend/models/base.py:155-160`

**Current Code**:
```python
class UserRole(str, PyEnum):
    """用户角色枚举"""
    ADMIN = "admin"
    FINANCE = "finance"
    OPERATOR = "operator"    # WRONG
    VIEWER = "viewer"        # WRONG
```

**SoT Reference**: AUTH_SPEC.md v2.0 §2.2

**Expected Values**:
```python
class UserRole(str, PyEnum):
    ADMIN = "admin"
    FINANCE = "finance"
    DATA_OPERATOR = "data_operator"      # CORRECT
    ACCOUNT_MANAGER = "account_manager"  # CORRECT
    MEDIA_BUYER = "media_buyer"          # CORRECT
```

**Impact**:
- Tests using `role="operator"` or `role="viewer"` will pass but create invalid data
- Production database CHECK constraint will reject these values
- All RBAC permission tests will be invalid

**Fix Required**:
1. Update `UserRole` enum in `backend/models/base.py`
2. Generate Alembic migration for CHECK constraint alignment
3. Update all test fixtures using invalid roles

---

### P0-002: DailyReportStatus Enum Mismatch

**Location**: `backend/models/base.py:195-200`

**Current Code**:
```python
class DailyReportStatus(str, PyEnum):
    """每日报告状态枚举"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
```

**SoT Reference**: STATE_MACHINE.md v2.6 §8.1

**Expected Values (8-state machine)**:
```python
class DailyReportStatus(str, PyEnum):
    RAW_SUBMITTED = "raw_submitted"
    TREND_PENDING = "trend_pending"
    TREND_OK = "trend_ok"
    TREND_FLAGGED = "trend_flagged"
    TREND_RESOLVED = "trend_resolved"
    FINAL_PENDING = "final_pending"
    FINAL_CONFIRMED = "final_confirmed"
    FINAL_LOCKED = "final_locked"
```

**Impact**:
- 8-state workflow tests impossible with current 4-state enum
- State transition validation tests will fail
- Trend risk control (TF-001/002/003) tests cannot be implemented

**Fix Required**:
1. Update `DailyReportStatus` enum to 8-state model
2. Generate Alembic migration for CHECK constraint alignment
3. Update all daily report fixtures and tests

---

## 2. P1 Issues (High Priority)

### P1-001: TopupStatus Missing States

**Location**: `backend/models/base.py:203-211`

**Current Code**:
```python
class TopupStatus(str, PyEnum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    FINANCE_APPROVE = "finance_approve"
    PAID = "paid"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
```

**SoT Reference**: STATE_MACHINE.md v2.6 §9

**Analysis**: Current enum matches SoT definition. **No fix required.**

**Status**: :white_check_mark: **COMPLIANT**

---

### P1-002: test_user Fixture Uses Valid Role But Enum is Wrong

**Location**: `backend/tests/conftest.py:190-204`

**Current Code**:
```python
@pytest.fixture(scope="function")
def test_user(db_session):
    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        role="admin",  # Valid value, but enum class is wrong
        is_active=True,
    )
```

**SoT Reference**: AUTH_SPEC.md v2.0 §2.2

**Analysis**:
- The fixture uses `role="admin"` which IS a valid SoT value
- However, the `UserRole` enum class definition is wrong (P0-001)
- Tests will work with string value but type hints will be incorrect

**Impact**: Medium - Works at runtime but violates type safety

**Fix Required**:
1. After fixing P0-001, update fixture to use enum: `role=UserRole.ADMIN`

---

### P1-003: Missing Required Fixtures for SoT Compliance Testing

**Location**: `backend/tests/conftest.py`

**Missing Fixtures**:

| Required Fixture | SoT Reference | Purpose |
|-----------------|---------------|---------|
| `test_finance_user` | AUTH_SPEC.md §2.2 | Finance role testing |
| `test_data_operator` | AUTH_SPEC.md §2.2 | Data operator role testing |
| `test_account_manager` | AUTH_SPEC.md §2.2 | Account manager role testing |
| `test_media_buyer` | AUTH_SPEC.md §2.2 | Media buyer role testing |
| `test_daily_report` | STATE_MACHINE.md §8 | Daily report workflow testing |
| `test_topup_request` | STATE_MACHINE.md §9 | Topup workflow testing |
| `test_project` | DATA_SCHEMA.md §3.2 | Project entity testing |
| `test_ad_account` | DATA_SCHEMA.md §3.3 | Ad account entity testing |

**Impact**: Cannot test RBAC, SOD (Separation of Duties), or state machine transitions

**Fix Required**: Add missing fixtures with SoT-compliant values

---

### P1-004: conftest.py Missing LEDGER_SOT Fixtures

**Location**: `backend/tests/conftest.py`

**SoT Reference**: LEDGER_SOT.md v1.1

**Missing**:
- `test_ledger_entry` fixture for dual-ledger testing
- `LedgerEntryType` enum validation

**Impact**: Cannot test ledger isolation (PROJECT vs SUPPLIER accounts)

---

## 3. P2 Issues (Medium Priority)

### P2-001: ReconciliationBatchStatus Enum Review

**Location**: `backend/models/base.py:221-226`

**Current Code**:
```python
class ReconciliationBatchStatus(str, PyEnum):
    DRAFT = "draft"
    PENDING = "pending"
    REVIEWING = "reviewing"
    CLOSED = "closed"
```

**SoT Reference**: STATE_MACHINE.md v2.6 §10

**Expected**: `draft`, `pending_review`, `approved`, `needs_adjustment`, `completed`

**Analysis**: Minor mismatch - `REVIEWING` vs `approved`, `CLOSED` vs `completed`

**Impact**: Low - Reconciliation tests may use incorrect states

---

### P2-002: LedgerEntryType Enum Incomplete

**Location**: `backend/models/base.py:214-218`

**Current Code**:
```python
class LedgerEntryType(str, PyEnum):
    TOPUP_RECEIVED = "topup_received"
    SPEND = "spend"
    ADJUSTMENT = "adjustment"
```

**SoT Reference**: LEDGER_SOT.md v1.1 §3.2

**Expected Values**:
```python
class LedgerEntryType(str, PyEnum):
    RECHARGE = "RECHARGE"           # 充值入账
    SPEND = "SPEND"                 # 消耗扣减
    TRANSFER_IN = "TRANSFER_IN"     # 转入
    TRANSFER_OUT = "TRANSFER_OUT"   # 转出
    REVERSAL = "REVERSAL"           # 红冲修正
    ADJUSTMENT = "ADJUSTMENT"       # 人工调整
```

**Impact**: Cannot test transfer and reversal flows

---

## 4. Compliant Items (No Issues)

| Item | Location | SoT Reference | Status |
|------|----------|---------------|--------|
| `ChannelStatus` | base.py:163-166 | DATA_SCHEMA.md | :white_check_mark: Compliant |
| `ProjectStatus` | base.py:169-174 | STATE_MACHINE.md | :white_check_mark: Compliant |
| `ReviewStatus` | base.py:177-182 | STATE_MACHINE.md | :white_check_mark: Compliant |
| `AdAccountStatus` | base.py:185-192 | STATE_MACHINE.md | :white_check_mark: Compliant |
| `AccountAlertStatus` | base.py:236-240 | STATE_MACHINE.md | :white_check_mark: Compliant |
| `AccountAlertSeverity` | base.py:243-248 | DATA_SCHEMA.md | :white_check_mark: Compliant |
| `db_session` fixture | conftest.py:148-172 | - | :white_check_mark: Correct |
| `client` fixture | conftest.py:175-187 | - | :white_check_mark: Correct |
| `auth_token` fixture | conftest.py:207-215 | AUTH_SPEC.md | :white_check_mark: Correct |
| `auth_headers` fixture | conftest.py:218-221 | AUTH_SPEC.md | :white_check_mark: Correct |

---

## 5. Recommended Fix Order

### Phase 1: Critical (P0) - Block All Tests Until Fixed

| Priority | Task | Estimated Effort | Dependency |
|----------|------|------------------|------------|
| 1.1 | Fix `UserRole` enum (5 roles) | 30 min | None |
| 1.2 | Fix `DailyReportStatus` enum (8 states) | 30 min | None |
| 1.3 | Generate Alembic migration | 1 hour | 1.1, 1.2 |
| 1.4 | Update conftest.py fixtures | 1 hour | 1.1, 1.2 |

### Phase 2: High Priority (P1) - Required for CI/CD

| Priority | Task | Estimated Effort | Dependency |
|----------|------|------------------|------------|
| 2.1 | Add role-based test fixtures (5 roles) | 2 hours | Phase 1 |
| 2.2 | Add entity fixtures (project, account, report) | 3 hours | Phase 1 |
| 2.3 | Add ledger fixtures | 2 hours | Phase 1 |

### Phase 3: Medium Priority (P2) - Nice to Have

| Priority | Task | Estimated Effort | Dependency |
|----------|------|------------------|------------|
| 3.1 | Fix `ReconciliationBatchStatus` enum | 30 min | None |
| 3.2 | Fix `LedgerEntryType` enum | 30 min | None |

---

## 6. Code Snippets for Fixes

### Fix P0-001: UserRole Enum

```python
# backend/models/base.py

class UserRole(str, PyEnum):
    """
    用户角色枚举

    引用: AUTH_SPEC.md v2.0 §2.2 - role五枚举固定定义
    引用: BUSINESS_RULES.md v3.1 - BR-AUTH-001, BR-USER-001

    五个固定角色（禁止添加新角色）:
    - admin: 系统管理员 (L5)
    - finance: 财务 (L4)
    - data_operator: 数据操作员/户管 (L3)
    - account_manager: 客户经理 (L2)
    - media_buyer: 投手/媒体采购 (L1)
    """
    ADMIN = "admin"
    FINANCE = "finance"
    DATA_OPERATOR = "data_operator"
    ACCOUNT_MANAGER = "account_manager"
    MEDIA_BUYER = "media_buyer"
```

### Fix P0-002: DailyReportStatus Enum

```python
# backend/models/base.py

class DailyReportStatus(str, PyEnum):
    """
    每日报告状态枚举（8状态机）

    引用: STATE_MACHINE.md v2.6 §8.1 - 粉数确认状态机

    状态流转:
    raw_submitted → trend_pending → trend_ok/trend_flagged
    → trend_resolved → final_pending → final_confirmed → final_locked

    终态: final_locked（仅可通过红冲修正）
    """
    RAW_SUBMITTED = "raw_submitted"
    TREND_PENDING = "trend_pending"
    TREND_OK = "trend_ok"
    TREND_FLAGGED = "trend_flagged"
    TREND_RESOLVED = "trend_resolved"
    FINAL_PENDING = "final_pending"
    FINAL_CONFIRMED = "final_confirmed"
    FINAL_LOCKED = "final_locked"
```

### Add Missing Role Fixtures

```python
# backend/tests/conftest.py

@pytest.fixture(scope="function")
def test_finance_user(db_session):
    """创建财务角色测试用户 - AUTH_SPEC.md v2.0 §2.2"""
    from uuid import uuid4
    user = User(
        id=uuid4(),
        email="finance@example.com",
        username="financeuser",
        role="finance",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_data_operator(db_session):
    """创建数据操作员测试用户 - AUTH_SPEC.md v2.0 §2.2"""
    from uuid import uuid4
    user = User(
        id=uuid4(),
        email="dataop@example.com",
        username="dataoperator",
        role="data_operator",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_account_manager(db_session):
    """创建客户经理测试用户 - AUTH_SPEC.md v2.0 §2.2"""
    from uuid import uuid4
    user = User(
        id=uuid4(),
        email="am@example.com",
        username="accountmanager",
        role="account_manager",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_media_buyer(db_session):
    """创建投手测试用户 - AUTH_SPEC.md v2.0 §2.2"""
    from uuid import uuid4
    user = User(
        id=uuid4(),
        email="buyer@example.com",
        username="mediabuyer",
        role="media_buyer",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
```

---

## 7. Migration Script Template

```sql
-- Alembic Migration: Fix UserRole and DailyReportStatus enums
-- Generated: 2025-11-27
-- SoT Reference: AUTH_SPEC.md v2.0, STATE_MACHINE.md v2.6

-- Step 1: Update users.role CHECK constraint
ALTER TABLE users DROP CONSTRAINT IF EXISTS chk_users_role;
ALTER TABLE users ADD CONSTRAINT chk_users_role CHECK (role IN (
    'admin',
    'finance',
    'data_operator',
    'account_manager',
    'media_buyer'
));

-- Step 2: Update daily_reports.status CHECK constraint
ALTER TABLE daily_reports DROP CONSTRAINT IF EXISTS chk_daily_reports_status;
ALTER TABLE daily_reports ADD CONSTRAINT chk_daily_reports_status CHECK (status IN (
    'raw_submitted',
    'trend_pending',
    'trend_ok',
    'trend_flagged',
    'trend_resolved',
    'final_pending',
    'final_confirmed',
    'final_locked'
));

-- Step 3: Set default for daily_reports.status
ALTER TABLE daily_reports ALTER COLUMN status SET DEFAULT 'raw_submitted';
```

---

## 8. Sign-Off

| Role | Name | Status |
|------|------|--------|
| Auditor | Claude AI Agent | :white_check_mark: Complete |
| Reviewer | Wade (Pending) | :hourglass_flowing_sand: Pending |
| Approver | Wade (Pending) | :hourglass_flowing_sand: Pending |

**Report Generated**: 2025-11-27
**Health Score**: 40/100 (2 P0, 3 P1, 2 P2)
**Recommendation**: **DO NOT RUN TESTS** until P0 issues are resolved

---

**End of Fixture Audit Report v1.0**
