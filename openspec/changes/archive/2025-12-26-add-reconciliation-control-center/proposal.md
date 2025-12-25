# OpenSpec Change Proposal: Reconciliation Control Center

**Change-ID**: `add-reconciliation-control-center`
**Status**: ARCHIVED (Deployed 2025-12-26)
**Author**: Claude Code
**Commit**: 469c5bd

---

## Summary

Implement the Reconciliation Control Center module to provide:
1. Settlement rules configuration (tiered/markup pricing)
2. Ad account balance/deposit snapshot tracking
3. Reconciliation issue workflow management

## Motivation

The finance team needs tools to:
- Configure flexible settlement rules per project
- Track daily balance and deposit changes for each ad account
- Manage reconciliation discrepancies through a structured workflow

## Affected SoT Documents

| Document | Version Change | Description |
|----------|---------------|-------------|
| DATA_SCHEMA.md | v5.3 → v5.4 | New tables: settlement_rules, ad_account_balance_snapshots, reconciliation_issues |
| STATE_MACHINE.md | v2.6 → v2.7 | New 5-state workflow for reconciliation issues |
| LEDGER_SOT.md | v1.1 | Conservation formula reference |

## Implementation Summary

### New Database Tables

1. **settlement_rules** - Tiered/markup pricing configuration
   - `rule_type`: tiered | markup
   - `config`: JSONB with tier definitions or markup values
   - Soft delete via `effective_to` date

2. **ad_account_balance_snapshots** - Daily balance tracking
   - `balance`, `deposit`, `remaining_balance` (computed)
   - Unique constraint on (ad_account_id, snapshot_date)
   - Conservation formula verification

3. **reconciliation_issues** - Discrepancy tracking
   - 5-state workflow: open → assigned → investigating → resolved → closed
   - SLA tracking with `sla_deadline` and `sla_breached`
   - Resolution types: data_correction, ledger_adjustment, external_confirm, write_off, false_positive

### Extended Tables

- **projects**: Added `settlement_type`, `settlement_rules_id`
- **ad_accounts**: Added `deposit`, `deposit_updated_at`

### API Endpoints

```
POST   /api/v1/reconciliation/settlement-rules
GET    /api/v1/reconciliation/settlement-rules
GET    /api/v1/reconciliation/settlement-rules/{id}
PATCH  /api/v1/reconciliation/settlement-rules/{id}
DELETE /api/v1/reconciliation/settlement-rules/{id}

POST   /api/v1/reconciliation/balance-snapshots
POST   /api/v1/reconciliation/balance-snapshots/batch
GET    /api/v1/reconciliation/balance-snapshots
GET    /api/v1/reconciliation/balance-snapshots/{id}
POST   /api/v1/reconciliation/balance-snapshots/verify

POST   /api/v1/reconciliation/issues
GET    /api/v1/reconciliation/issues
GET    /api/v1/reconciliation/issues/{id}
GET    /api/v1/reconciliation/issues/summary
POST   /api/v1/reconciliation/issues/{id}/assign
POST   /api/v1/reconciliation/issues/{id}/investigate
POST   /api/v1/reconciliation/issues/{id}/resolve
POST   /api/v1/reconciliation/issues/{id}/close
```

### Conservation Formula

```
Σ(topup) - Σ(spend) = Δ(balance) + Δ(deposit)
```

Used by `BalanceSnapshotService.verify_conservation()` to detect accounting anomalies.

## Files Changed

### New Files
- `backend/alembic/versions/20251226_add_reconciliation_control_center.py`
- `backend/models/reconciliation/__init__.py`
- `backend/models/reconciliation/settlement_rule.py`
- `backend/models/reconciliation/balance_snapshot.py`
- `backend/models/reconciliation/reconciliation_issue.py`
- `backend/services/reconciliation_control_service.py`
- `backend/routers/reconciliation_control.py`
- `docs/2.sot/RECONCILIATION_CONTROL_CENTER_SOT_v2.0.md`
- `docs/4.architecture/RECONCILIATION_CONTROL_CENTER_ARCHITECTURE.md`
- `test_reconciliation_api.py`

### Modified Files
- `backend/models/accounts/ad_account.py` - Added deposit fields and relationships
- `backend/models/core/project.py` - Added settlement fields
- `backend/schemas/reconciliation.py` - Added new schemas
- `docs/2.sot/DATA_SCHEMA.md` - Updated to v5.4
- `docs/2.sot/STATE_MACHINE.md` - Added reconciliation issue workflow

## Testing

All API tests passed via `test_reconciliation_api.py`:
- Settlement Rules: CRUD + soft delete
- Balance Snapshots: CRUD + conservation verification
- Reconciliation Issues: Full 5-state workflow

---

**Archived**: 2025-12-26
