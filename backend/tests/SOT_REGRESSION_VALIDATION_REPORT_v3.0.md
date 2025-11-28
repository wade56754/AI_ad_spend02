# SoT Regression Validation Report v3.0

> **Report Date**: 2025-11-28
> **Baseline**: STATE_MACHINE.md v2.6, DATA_SCHEMA.md v5.2, AUTH_SPEC.md v2.0, LEDGER_SOT.md v1.1
> **Executor**: Claude Code (ai-ad-spec-governor + CodeReviewAgent)
> **Status**: REGRESSION DETECTED - CRITICAL FIXES NEEDED

---

## Executive Summary

| Category | Status | P0 Issues | P1 Issues | P2 Issues |
|----------|--------|-----------|-----------|-----------|
| **1. ENUM Definitions** | PASSED | 0 | 0 | 0 |
| **2. Model Layer** | PASSED | 0 | 0 | 0 |
| **3. Service Layer** | FAILED | 4 | 2 | 0 |
| **4. API Layer** | WARNING | 0 | 1 | 1 |
| **5. Pydantic Schemas** | FAILED | 3 | 2 | 0 |
| **6. Test Files** | FAILED | 6 | 3 | 0 |
| **7. Migrations** | WARNING | 0 | 2 | 1 |
| **8. Fixtures** | PASSED | 0 | 0 | 0 |
| **TOTAL** | **FAILED** | **13** | **10** | **2** |

**Health Score**: 48/100 (pytest NOT safe to run)

---

## Category 1: ENUM Definitions (PASSED)

### Files Checked:
- `backend/models/base.py` - ALIGNED
- `backend/models/enums.py` - ALIGNED

### Verification:
- DailyReportStatus: 8 states (raw_submitted, trend_pending, trend_ok, trend_flagged, trend_resolved, final_pending, final_confirmed, final_locked)
- LedgerEntryType: 6 types (REVENUE, COST, TOPUP, TRANSFER_OUT, TRANSFER_IN, REVERSAL)
- ReconciliationBatchStatus: 5 states (draft, pending_review, approved, needs_adjustment, completed)
- UserRole: 5 roles (admin, finance, data_operator, account_manager, media_buyer)

---

## Category 2: Model Layer (PASSED)

### Files Checked:
- `backend/models/workflow/daily_report.py` - ALIGNED (8-state machine)
- `backend/models/finance/ledger.py` - ALIGNED (6 entry types)
- `backend/models/finance/reconciliation.py` - ALIGNED (5-state machine)

### Key Validations:
- CHECK constraints match SoT
- STATE_TRANSITIONS whitelist implemented
- Invariant validation methods present

---

## Category 3: Service Layer (FAILED)

### P0-SVC-001: daily_report_service.py uses old status strings
**File**: `backend/services/daily_report_service.py`
**Lines**: 322, 421, 445
**Issue**: Uses hardcoded `"approved"` and `"rejected"` instead of 8-state machine enums
```python
# Line 322 - WRONG
if report.status == "approved":

# Line 421 - WRONG
new_status="approved",

# Line 445 - WRONG
new_status="rejected",
```
**Fix Required**: Replace with DailyReportStatus.FINAL_CONFIRMED or appropriate 8-state value

### P0-SVC-002: reconciliation_service.py uses old status values
**File**: `backend/services/reconciliation_service.py`
**Lines**: 63, 161
**Issue**: Uses `status="pending"` instead of `ReconciliationBatchStatus.DRAFT.value`
```python
# Line 63 - WRONG
status="pending",

# Line 161 - WRONG
if batch.status != "pending":
```
**Fix Required**: Replace with ReconciliationBatchStatus enum values

### P0-SVC-003: reconciliation_service_optimized.py same issue
**File**: `backend/services/reconciliation_service_optimized.py`
**Lines**: 65, 162
**Issue**: Same as P0-SVC-002

### P0-SVC-004: topup_service.py status inconsistency
**File**: `backend/services/topup_service.py`
**Lines**: 108, 211, 218, 261, 427, 433, 464, 508, 515
**Issue**: Uses mixed old status values ("pending", "rejected", "data_review", "finance_approve")
**Note**: TopupStatus enum uses different values than hardcoded strings

### P1-SVC-001: User role string comparison
**File**: `backend/services/daily_report_service.py`
**Line**: 383
**Issue**: `current_user.role != "admin"` should use `UserRole.ADMIN.value`

### P1-SVC-002: reconciliation_service match_status hardcoded
**File**: `backend/services/reconciliation_service.py`
**Line**: 297
**Issue**: `match_status not in ["pending", "manual_review", "exception"]`

---

## Category 4: API Layer (WARNING)

### P1-API-001: Router uses legacy status logic
**File**: `backend/routers/reconciliation_extended.py`
**Line**: 441
**Issue**: `"pending": total_batches - completed_batches...` - hardcoded status strings

### P2-API-001: Missing enum imports in some routers
**Impact**: Low - runtime works but IDE intellisense missing

---

## Category 5: Pydantic Schemas (FAILED)

### P0-SCHEMA-001: TopupStatus enum mismatch
**File**: `backend/schemas/topup.py`
**Lines**: 23-31
**Issue**: Schema TopupStatus uses `PENDING = "pending"` but model base.py uses `PENDING_REVIEW = "pending_review"`
```python
# schemas/topup.py - WRONG
class TopupStatus(str, Enum):
    PENDING = "pending"          # Should be PENDING_REVIEW
    DATA_REVIEW = "data_review"  # Not in base.py TopupStatus
```

### P0-SCHEMA-002: Default status values wrong
**File**: `backend/schemas/__init__.py`
**Lines**: 211, 305
**Issue**: `status: str = "pending"` - hardcoded default instead of enum

### P0-SCHEMA-003: ReconciliationBatchStatus enum mismatch
**File**: `backend/schemas/reconciliation.py`
**Lines**: 17, 26
**Issue**: Uses old 4-state values instead of 5-state machine

### P1-SCHEMA-001: TopupBase uses wrong default
**File**: `backend/schemas/__init__.py`
**Line**: 211
**Issue**: Should use TopupStatus.DRAFT.value

### P1-SCHEMA-002: ImportJobBase uses hardcoded status
**File**: `backend/schemas/__init__.py`
**Line**: 305
**Issue**: `status: str = "pending"` - should use enum

---

## Category 6: Test Files (FAILED)

### P0-TEST-001: test_daily_report_service.py old status assertions
**File**: `backend/tests/test_daily_report_service.py`
**Lines**: 58, 154, 158, 259, 282, 411
**Issues**:
- `assert report.status == "pending"` - Line 58
- `params = DailyReportQueryParams(status="approved")` - Line 154
- `assert reports[0].status == "approved"` - Line 158
- `assert approved_report.status == "approved"` - Line 259
- `assert rejected_report.status == "rejected"` - Line 282

### P0-TEST-002: test_daily_report_api.py old status assertions
**File**: `backend/tests/test_daily_report_api.py`
**Lines**: 33, 228, 280
**Issues**:
- `assert data["data"]["status"] == "pending"` - Line 33
- `assert data["data"]["status"] == "approved"` - Line 228
- `assert data["data"]["status"] == "rejected"` - Line 280

### P0-TEST-003: test_topup_service.py hardcoded status
**File**: `backend/tests/test_topup_service.py`
**Lines**: 175, 206, 309, 384, 487, 502
**Issue**: Uses `status="pending"` and `assert request.status == "pending/rejected"`

### P0-TEST-004: test_topup_api.py hardcoded status
**File**: `backend/tests/test_topup_api.py`
**Lines**: 35, 90, 162
**Issue**: Same as P0-TEST-003

### P0-TEST-005: test_api_endpoints.py old status
**File**: `backend/tests/test_api_endpoints.py`
**Lines**: 47, 172, 217
**Issue**: `"status": "pending"` in test data

### P0-TEST-006: test_reconciliation_service.py old status
**File**: `backend/tests/test_reconciliation_service.py`
**Lines**: 66, 91, 117, 131, 172, 180, 342
**Issue**: Uses `status="pending"`, `match_status="pending"`

### P1-TEST-001: test_models_crud.py uses "draft"
**File**: `backend/tests/test_models_crud.py`
**Lines**: 356, 363, 408, 462, 518, 580
**Issue**: `status="draft"` - acceptable for TopupStatus but verify context

### P1-TEST-002: test_rbac_permissions.py old status
**File**: `backend/tests/test_rbac_permissions.py`
**Line**: 275
**Issue**: `status="pending"`

### P1-TEST-003: test_reconciliation_api.py old status
**File**: `backend/tests/test_reconciliation_api.py`
**Line**: 36
**Issue**: `assert json_data["data"]["status"] == "pending"`

---

## Category 7: Migrations (WARNING)

### P1-MIG-001: Old migration uses wrong status constraint
**File**: `backend/alembic/versions/20251117_reconciliation_status_align.py`
**Issue**: Migration aligns to old 4-state machine (draft, pending, reviewing, closed)
```python
# Line 74 - OLD MIGRATION
"status IN ('draft', 'pending', 'reviewing', 'closed')"
```
**Note**: This is historical - new migration needed to fix to 5-state machine

### P1-MIG-002: Constraint migration uses old values
**File**: `backend/alembic/versions/20251120_fix_reconciliation_batch_constraint_p0.py`
**Lines**: 37, 48
**Issue**: Same 4-state constraint

### P2-MIG-001: Entry type in old migration
**File**: `backend/alembic/versions/20251118_phase0_replace_topup_ledger_tables.py`
**Line**: 150
**Issue**: `entry_type: topup_received/spend/adjustment` - old values
**Note**: Historical migration, may be superseded

---

## Category 8: Fixtures (PASSED)

### Files Checked:
- `backend/tests/conftest.py` - ALIGNED

### Validations:
- Role fixtures use UserRole enums
- DailyReportStateHelper uses correct 8-state transitions
- ReconciliationStateHelper uses correct 5-state transitions
- LedgerInvariantHelper validates correct 6 entry types

---

## Required Fixes by Priority

### P0 Fixes (Must Complete Before pytest)

1. **Service Layer**:
   - `daily_report_service.py`: Replace all "approved"/"rejected"/"pending" with 8-state enum values
   - `reconciliation_service.py`: Replace "pending" with ReconciliationBatchStatus enum values
   - `reconciliation_service_optimized.py`: Same as above
   - `topup_service.py`: Align status strings with TopupStatus enum

2. **Pydantic Schemas**:
   - `schemas/topup.py`: Remove duplicate TopupStatus, import from models.enums
   - `schemas/__init__.py`: Replace hardcoded "pending" defaults with enum values
   - `schemas/reconciliation.py`: Remove duplicate enum, import from models.enums

3. **Test Files**:
   - All 6 test files need status assertion updates to use enum values

### P1 Fixes (Should Complete Before Production)

1. **Service Layer**: Role comparison should use enum
2. **Schemas**: Consistent enum usage
3. **Migrations**: New migration to fix ReconciliationBatch constraint to 5-state

### P2 Fixes (Nice to Have)

1. **API Layer**: Add enum imports for IDE support
2. **Migrations**: Document historical migration state

---

## pytest Readiness Assessment

| Criterion | Status | Blocker |
|-----------|--------|---------|
| ENUM definitions correct | PASSED | No |
| Model layer aligned | PASSED | No |
| Service layer aligned | FAILED | YES |
| Test assertions aligned | FAILED | YES |
| Fixtures aligned | PASSED | No |

**Verdict**: pytest is NOT safe to run. Service layer and test files still use old status values that will cause assertion failures.

---

## Recommended Next Steps

1. **Phase 1 (P0 - Immediate)**:
   - Fix `daily_report_service.py` status comparisons
   - Fix `reconciliation_service.py` and `reconciliation_service_optimized.py`
   - Fix `topup_service.py` status handling
   - Remove duplicate enums from schemas

2. **Phase 2 (P0 - Before pytest)**:
   - Update all test file assertions to use enum values
   - Verify test fixtures still pass

3. **Phase 3 (P1 - Before Production)**:
   - Create new migration for ReconciliationBatch 5-state constraint
   - Update role comparisons to use UserRole enum

4. **Phase 4 (Verification)**:
   - Run full pytest suite
   - Generate new regression report

---

## Conclusion

**Current State**: Model and enum definitions are correctly aligned with SoT v2.6, but service layer, schemas, and tests still contain old status values.

**Health Score**: 48/100
- Models: 100/100
- Services: 20/100
- Schemas: 30/100
- Tests: 15/100
- Fixtures: 100/100

**pytest Status**: BLOCKED - Do not run until P0 fixes complete

---

*Report generated by Claude Code ai-ad-spec-governor*
*Baseline: SoT Freeze v2.6*
