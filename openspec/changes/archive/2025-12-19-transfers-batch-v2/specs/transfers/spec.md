# Transfers Module Spec

## ADDED Requirements

### Requirement: Transfer Request State Machine
The system SHALL implement a 5-state machine for transfer requests as defined in STATE_MACHINE.md v2.6 Chapter 12.

**States:**
- `draft`: Initial state for new transfer requests
- `pending_approval`: Submitted and awaiting approval
- `approved`: Approval granted, ready for execution
- `rejected`: Approval rejected (terminal state)
- `completed`: Transfer executed successfully (terminal state)

**Transition Whitelist:**
```
draft → pending_approval, rejected
pending_approval → approved, rejected
approved → completed
rejected → (terminal)
completed → (terminal)
```

#### Scenario: Create transfer in draft state
- **WHEN** a new transfer request is created
- **THEN** it SHALL have status `draft`
- **AND** version SHALL be 1

#### Scenario: Submit transfer for approval
- **WHEN** a draft transfer is submitted
- **THEN** status SHALL change to `pending_approval`
- **AND** version SHALL be incremented

#### Scenario: Approve transfer
- **WHEN** a pending_approval transfer is approved
- **THEN** status SHALL change to `approved`
- **AND** approved_by and approved_at SHALL be set
- **AND** version SHALL be incremented

#### Scenario: Complete transfer
- **WHEN** an approved transfer is completed
- **THEN** status SHALL change to `completed`
- **AND** completed_at SHALL be set
- **AND** TRANSFER_OUT/TRANSFER_IN ledger entries SHALL be created

### Requirement: Transfer Request Data Model
The system SHALL store transfer requests in `transfer_requests` table as defined in DATA_SCHEMA.md v5.2 Section 3.4.6.

**Required Fields:**
- `id`: BIGSERIAL primary key
- `request_no`: VARCHAR(50) unique, not null
- `source_ad_account_id`: BIGINT FK to ad_accounts
- `target_ad_account_id`: BIGINT FK to ad_accounts
- `transfer_amount`: NUMERIC(15,2) not null
- `status`: VARCHAR(20) not null
- `version`: INTEGER default 1
- `created_by`: UUID FK to users
- `approved_by`: UUID FK to users (nullable)
- `created_at`, `updated_at`, `approved_at`, `completed_at`: TIMESTAMPTZ

#### Scenario: Request number uniqueness
- **WHEN** a transfer request is created
- **THEN** request_no SHALL be unique (format: TRF-YYYYMMDDHHMMSS-XXXX)
- **AND** duplicate request_no SHALL raise E-TRANS-001

### Requirement: Transfer Business Rules
The system SHALL enforce transfer business rules as defined in TRANSFER_SOT.md v1.0.

#### Scenario: Source and target account validation
- **WHEN** creating a transfer request
- **THEN** source_ad_account_id SHALL NOT equal target_ad_account_id
- **AND** both accounts SHALL exist

#### Scenario: Transfer amount validation
- **WHEN** creating a transfer request
- **THEN** transfer_amount SHALL be greater than 0
- **AND** transfer_amount SHALL NOT exceed source account balance

### Requirement: Transfer API Endpoints
The system SHALL expose transfer API endpoints as defined in API_SOT.md v9.0.

**Endpoints:**
| Method | Path | Operation | Roles |
|--------|------|-----------|-------|
| POST | /api/v1/transfers | Create transfer | admin, account_manager, finance |
| GET | /api/v1/transfers | List transfers | all authenticated |
| GET | /api/v1/transfers/{id} | Get transfer detail | all authenticated |
| POST | /api/v1/transfers/{id}/submit | Submit for approval | creator, admin |
| POST | /api/v1/transfers/{id}/approve | Approve transfer | finance, admin |
| POST | /api/v1/transfers/{id}/reject | Reject transfer | finance, admin |
| POST | /api/v1/transfers/{id}/complete | Complete transfer | admin |

#### Scenario: Create transfer API
- **WHEN** POST /api/v1/transfers is called with valid data
- **THEN** response status SHALL be 201
- **AND** response body SHALL contain transfer with status `draft`

#### Scenario: Get non-existent transfer
- **WHEN** GET /api/v1/transfers/{id} is called with invalid id
- **THEN** response status SHALL be 404
- **AND** error code SHALL be BIZ_002

### Requirement: Transfer Permission Control
The system SHALL enforce role-based permission control for transfer operations.

#### Scenario: Media buyer cannot create transfer
- **WHEN** a user with role `media_buyer` attempts to create a transfer
- **THEN** response status SHALL be 403
- **AND** error code SHALL be AUTH_500

#### Scenario: Account manager cannot approve transfer
- **WHEN** a user with role `account_manager` attempts to approve a transfer
- **THEN** response status SHALL be 403
- **AND** error code SHALL be AUTH_500

### Requirement: Transfer Error Codes
The system SHALL use standard error codes as defined in ERROR_CODES_SOT.md v2.1.

**Error Code Mappings:**
- `BIZ_001`: Business logic error (same account, insufficient balance)
- `BIZ_002`: Resource not found
- `STATE_001`: Invalid state transition
- `AUTH_500`: Permission denied
- `VALIDATION_001`: Input validation error
