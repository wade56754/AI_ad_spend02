# reconciliation Specification

## Purpose
TBD - created by archiving change align-reconciliation-batch-v2. Update Purpose after archive.
## Requirements
### Requirement: Reconciliation Adjustment Model
The system SHALL provide ReconciliationAdjustment model as defined in DATA_SCHEMA.md 3.5.3.

**Fields:**
- `id`: Primary key
- `detail_id`: Foreign key to reconciliation_details
- `adjustment_type`: One of 'increase', 'decrease', 'writeoff'
- `amount`: Decimal(15,2)
- `reason`: Text
- `created_by`: Foreign key to users
- `created_at`: Timestamp

#### Scenario: Create adjustment record
- **WHEN** a reconciliation detail requires adjustment
- **THEN** a ReconciliationAdjustment record SHALL be created
- **AND** the adjustment_type SHALL be one of: increase, decrease, writeoff

#### Scenario: Query adjustments
- **WHEN** adjustments for a detail are queried
- **THEN** all adjustment records linked to that detail SHALL be returned

### Requirement: Reconciliation Service Field Alignment
ReconciliationService SHALL use model field names consistently across all methods.

#### Scenario: Create batch with period
- **WHEN** creating a new reconciliation batch
- **THEN** the service SHALL use `batch_code`, `period_start`, `period_end` fields
- **AND** NOT use non-existent fields like `batch_no`, `reconciliation_date`, `auto_match`

#### Scenario: Export uses correct fields
- **WHEN** exporting reconciliation data
- **THEN** the export SHALL use `batch.batch_code` (or `batch_no` alias)
- **AND** use `period_start`/`period_end` for date range

