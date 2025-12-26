---
version: v1.0
status: ready_for_production
layer: dev-guide
owner: wade
last_reviewed: 2025-11-27
baseline: MASTER.md v4.4, SoT Freeze v2.6
---

# Developer Onboarding Checklist

## 1. Purpose

Welcome to the AI Ad Spend Management System (AI_ad_spend02). This checklist provides a structured 3-week onboarding program designed to help new developers:

- **Understand** the AI Spec-Driven Development (ASDD) methodology
- **Master** the Single Source of Truth (SoT) document architecture
- **Navigate** the裁判链 (Arbitration Chain) for technical decisions
- **Execute** development workflows with AI agents (SuperClaude, Claude Code)
- **Comply** with invariants, state machines, and business rules from day one
- **Deliver** production-ready code that aligns with frozen specifications

**Target Audience**: Backend developers, frontend developers, full-stack developers, QA engineers

**Prerequisites**: Basic understanding of TypeScript, React, Python, PostgreSQL, and Git

---

## 2. Quick Reference

### 2.1 Essential Resources

| Resource | Location | Purpose |
|----------|----------|---------|
| **MASTER.md** | `docs/sot/MASTER.md` v3.4 | System constitution, highest authority |
| **CLAUDE.md** | `CLAUDE.md` v3.1 | AI agent instructions, auto-loaded in all sessions |
| **PROJECT_RULES.md** | `.claude/PROJECT_RULES.md` v3.1 | Complete rule compendium |
| **SoT裁判链** | `MASTER.md` §6 | Conflict resolution priority chain |
| **Slack Channel** | `#ai-ad-spend-dev` | Team communication |
| **Code Repository** | `https://github.com/[org]/AI_ad_spend02` | Source code |
| **Supabase Dashboard** | `https://app.supabase.com/project/[project-id]` | Database, Auth, Functions |

### 2.2 Timeline Overview

```
Week 1: Foundation + ASDD Architecture Understanding
├─ Day 1: Setup + MASTER.md
├─ Day 2-3: Core SoT Documents (裁判链 order)
├─ Day 4: Development Workflows
└─ Day 5: First Hands-on Exercise (Read-only exploration)

Week 2: Deep Dive + Domain Knowledge
├─ Day 6-7: State Machine + Data Schema mastery
├─ Day 8: Ledger System + Dual-Ledger Architecture
├─ Day 9: Testing Strategy
└─ Day 10: First Code Contribution (Bug fix)

Week 3: Advanced Topics + Independent Work
├─ Day 11-12: API Development Flow + Frontend Rules
├─ Day 13: Agent Workflow Training
├─ Day 14: Feature Implementation (supervised)
└─ Day 15: Knowledge Assessment + Graduation Task
```

---

## 3. Week 1: Foundation + ASDD Architecture

### Day 1: Environment Setup + System Overview

**Goal**: Get your development environment running and understand the system mission.

#### Checklist

- [ ] **Repository Access**
  - [ ] Clone repository: `git clone https://github.com/[org]/AI_ad_spend02.git`
  - [ ] Verify branch: `git checkout master` (main branch is `master`, not `main`)
  - [ ] Check git status: `git status` (should show clean working tree)

- [ ] **Tools Installation**
  - [ ] Install Node.js 20+ LTS
  - [ ] Install Python 3.11+
  - [ ] Install PostgreSQL 15+ (local development)
  - [ ] Install VS Code or Cursor IDE
  - [ ] Install Docker Desktop (for containerized testing)
  - [ ] Install Supabase CLI: `npm install -g supabase`
  - [ ] Install SuperClaude (optional, for AI-assisted development)

- [ ] **Backend Setup**
  - [ ] Follow `docs/2.dev-guides/BACKEND_SETUP.md` §2-5
  - [ ] Create virtual environment: `python -m venv venv`
  - [ ] Install dependencies: `pip install -r backend/requirements.txt`
  - [ ] Copy `.env.example` to `.env` and configure
  - [ ] Run local Supabase: `supabase start`
  - [ ] Apply migrations: `supabase db reset`
  - [ ] Verify backend health: `curl http://localhost:54321/health`

- [ ] **Frontend Setup**
  - [ ] Follow `docs/2.dev-guides/FRONTEND_SETUP.md` §2-4
  - [ ] Install dependencies: `cd frontend && npm install`
  - [ ] Copy `.env.local.example` to `.env.local` and configure
  - [ ] Start dev server: `npm run dev`
  - [ ] Open `http://localhost:3000` and verify login page renders

- [ ] **First Reading: MASTER.md**
  - [ ] Read `docs/sot/MASTER.md` v3.4 **in full** (45 minutes)
  - [ ] Understand the 5 core mechanisms (§1.3):
    - [ ] Dual-Ledger Architecture (PROJECT vs SUPPLIER)
    - [ ] Triple-Stream Separation (raw → real → final)
    - [ ] 8-State Machine Enforcement
    - [ ] Immutable Audit Trail (REVERSAL only)
    - [ ] Separation of Duties (role-based permissions)
  - [ ] Review all invariants (INV-001 to INV-004)
  - [ ] Review business invariants (BI-01 to BI-05)
  - [ ] Review prohibited behaviors (D-01 to D-06)
  - [ ] Memorize SoT裁判链 (§6): MASTER → STATE_MACHINE → DATA_SCHEMA → ...

- [ ] **Verify Understanding (Day 1 Quiz)**
  ```
  Q1: What is the highest-priority document in the system?
  A: MASTER.md v4.4

  Q2: What are the two ledger categories?
  A: PROJECT (revenue side) and SUPPLIER (cost side)

  Q3: What is the terminal state in daily_reports state machine?
  A: final_locked

  Q4: Can you directly UPDATE a ledger_entries record?
  A: No, prohibited by INV-001 (Immutable Audit Trail)

  Q5: What is the only way to correct a locked daily report?
  A: REVERSAL (red-charge mechanism)
  ```

**Estimated Time**: 6-8 hours

**Output**: Working local environment + MASTER.md comprehension

---

### Day 2-3: Core SoT Documents (裁判链 Order)

**Goal**: Read and internalize the top 7 SoT documents in priority order.

#### Day 2 Checklist

- [ ] **STATE_MACHINE.md v2.7** (90 minutes)
  - [ ] Read `docs/sot/STATE_MACHINE.md` §1-10
  - [ ] Understand all 8 states for `daily_reports`:
    - [ ] `raw_submitted` → `trend_pending` → `trend_ok/trend_flagged`
    - [ ] `trend_resolved` → `final_pending` → `final_confirmed` → `final_locked`
  - [ ] Study transition pre-conditions (§8 table)
  - [ ] Review prohibited transitions (§8)
  - [ ] Understand REVERSAL mechanism (§9)
  - [ ] Map roles to allowed operations (§2)

- [ ] **Exercise 1: State Diagram Drawing**
  - [ ] Draw the `daily_reports` state machine on paper/whiteboard
  - [ ] Mark terminal states with double circles
  - [ ] Label all transitions with trigger roles
  - [ ] Show self-review to mentor

- [ ] **DATA_SCHEMA.md v5.3** (120 minutes)
  - [ ] Read `docs/sot/DATA_SCHEMA.md` §1-6 (Table definitions)
  - [ ] Focus on core tables:
    - [ ] `projects` (revenue attribution)
    - [ ] `suppliers` (cost attribution)
    - [ ] `ad_accounts` (lifecycle management)
    - [ ] `daily_reports` (粉数 confirmation workflow)
    - [ ] `ledger_entries` (financial audit trail)
    - [ ] `topup_requests` (recharge workflow)
  - [ ] Understand foreign key relationships
  - [ ] Review CHECK constraints (must match STATE_MACHINE.md)
  - [ ] Note all `DECIMAL(12,2)` columns (financial precision, BR-FIN-003)

- [ ] **Exercise 2: Schema Exploration**
  - [ ] Connect to local database: `psql -h localhost -p 54322 -U postgres -d postgres`
  - [ ] Run: `\dt` to list tables
  - [ ] Run: `\d daily_reports` to inspect schema
  - [ ] Verify `status` CHECK constraint matches STATE_MACHINE.md §8
  - [ ] Check if any columns allow NULL that shouldn't (report to mentor)

**Estimated Time**: 6-8 hours

#### Day 3 Checklist

- [ ] **LEDGER_SOT.md v1.2** (90 minutes)
  - [ ] Read `docs/sot/LEDGER_SOT.md` §1-7
  - [ ] Understand dual-ledger philosophy:
    - [ ] PROJECT ledger = `ledger_entries WHERE category = 'PROJECT'`
    - [ ] SUPPLIER ledger = `ledger_entries WHERE category = 'SUPPLIER'`
  - [ ] Study ledger entry types:
    - [ ] RECHARGE (positive, adds balance)
    - [ ] REVENUE (negative for PROJECT, billing customer)
    - [ ] COST (negative for SUPPLIER, deducting supplier balance)
    - [ ] REVERSAL (reverse sign to cancel)
  - [ ] Memorize balance formula:
    ```
    projects.balance = SUM(ledger_entries.amount WHERE category = 'PROJECT')
    suppliers.balance = SUM(ledger_entries.amount WHERE category = 'SUPPLIER')
    ```
  - [ ] Understand billing trigger (INV-001):
    - [ ] Revenue: `conversions_final × unit_price` when `state = final_locked`
    - [ ] Cost: `real_spend × (1 + fee_rate)` when `state = final_locked`

- [ ] **BUSINESS_RULES.md v4.1** (60 minutes)
  - [ ] Read `docs/sot/BUSINESS_RULES.md` §1-8
  - [ ] Review key rules:
    - [ ] BR-FIN-003: All financial amounts use `DECIMAL(12,2)`
    - [ ] BR-RPT-001: Daily reports must have unique (ad_account_id, report_date)
    - [ ] BR-TREND-001/002: Trend check thresholds
    - [ ] BR-LED-001: REVERSAL requires approval_ref
  - [ ] Understand validation rules
  - [ ] Note business constraints not enforced by DB (require application logic)

- [ ] **API_SOT.md v9.3** (60 minutes)
  - [ ] Read `docs/sot/API_SOT.md` §1-4
  - [ ] Understand API structure: `/api/v1/{resource}`
  - [ ] Review HTTP method conventions (GET/POST/PUT/DELETE)
  - [ ] Study response format (JSON with `data`/`error` envelope)
  - [ ] Review error handling pattern (ERROR_CODES_SOT references)
  - [ ] Note authentication headers (Authorization: Bearer {token})

- [ ] **ERROR_CODES_SOT.md v2.1** (30 minutes)
  - [ ] Read `docs/sot/ERROR_CODES_SOT.md` §1-5
  - [ ] Understand error code categories:
    - [ ] `AUTH-xxx`: Authentication/Authorization errors
    - [ ] `VAL-xxx`: Validation errors
    - [ ] `BIZ-xxx`: Business logic errors
    - [ ] `SYS-xxx`: System errors
  - [ ] Review error response format: `{"code": "BIZ-101", "message": "..."}`
  - [ ] Note: Never create custom error codes (prohibited by MASTER.md §7.1)

- [ ] **Exercise 3: SoT Cross-Reference**
  - [ ] Pick `daily_reports` table
  - [ ] List all SoT documents that define its behavior:
    - [ ] STATE_MACHINE.md v2.7 (states and transitions)
    - [ ] DATA_SCHEMA.md v5.3 (schema definition)
    - [ ] LEDGER_SOT.md v1.2 (billing/cost triggers)
    - [ ] BUSINESS_RULES.md v4.1 (validation rules)
    - [ ] API_SOT.md v9.3 (endpoints: `/daily-reports`)
    - [ ] ERROR_CODES_SOT.md v2.1 (error responses)
  - [ ] Identify any conflicts (should be none if SoT is frozen)

**Estimated Time**: 6-7 hours

**Output**: Solid understanding of core SoT documents and their relationships

---

### Day 4: Development Workflows

**Goal**: Learn the standard development workflows and agent usage patterns.

#### Checklist

- [ ] **API_DEVELOPMENT_FLOW.md** (90 minutes)
  - [ ] Read `docs/2.dev-guides/API_DEVELOPMENT_FLOW.md` §1-10
  - [ ] Understand 7-step API development process:
    1. Query SoT documents
    2. Design endpoint contract
    3. Define types and schemas
    4. Implement service layer
    5. Implement API endpoint
    6. Write tests
    7. Generate documentation
  - [ ] Study Result<T, E> pattern for error handling
  - [ ] Review validation flow (Zod schema → business rules → database constraints)
  - [ ] Understand transaction patterns for state machine transitions

- [ ] **FRONTEND_DEVELOPMENT_RULES.md v1.0** (60 minutes)
  - [ ] Read `docs/2.dev-guides/FRONTEND_DEVELOPMENT_RULES.md` §1-8
  - [ ] Understand React component architecture
  - [ ] Review state management with Zustand
  - [ ] Study React Query data fetching patterns
  - [ ] Learn SoT-driven UI state mapping (frontend mirrors backend states)
  - [ ] Review role-based rendering rules

- [ ] **TESTING_STRATEGY.md v1.0** (60 minutes)
  - [ ] Read `docs/2.dev-guides/TESTING_STRATEGY.md` §1-10
  - [ ] Understand test pyramid:
    - [ ] 60% Unit tests (service layer logic)
    - [ ] 30% Integration tests (API + DB)
    - [ ] 10% E2E tests (critical user flows)
  - [ ] Review SoT-driven testing principles
  - [ ] Study state machine test patterns
  - [ ] Learn invariant testing approach

- [ ] **AGENT_WORKFLOW_GUIDE.md v1.0** (60 minutes)
  - [ ] Read `docs/2.dev-guides/AGENT_WORKFLOW_GUIDE.md` §1-7
  - [ ] Understand SoT-first mindset (query SoT before coding)
  - [ ] Learn agent role: executor, not inventor
  - [ ] Study common agent commands:
    - [ ] `/sc:implement` - Feature implementation
    - [ ] `/sc:test` - Test generation
    - [ ] `/sc:explain` - Code explanation
  - [ ] Review quality checkpoints
  - [ ] Practice agent prompt patterns

- [ ] **Exercise 4: Trace an API Request**
  - [ ] Choose endpoint: `POST /api/v1/daily-reports`
  - [ ] Trace the request flow:
    1. Frontend: `DailyReportForm.tsx` (submit button)
    2. API Client: `useDailyReports.ts` (React Query mutation)
    3. Backend: `routes/daily_reports.py` (endpoint handler)
    4. Service: `services/daily_report_service.py` (business logic)
    5. Model: `models/daily_report.py` (SQLAlchemy model)
    6. Database: `daily_reports` table (PostgreSQL)
  - [ ] Identify SoT validations at each layer
  - [ ] Document findings in `notes/exercise-4-trace.md`

- [ ] **Exercise 5: Run Existing Tests**
  - [ ] Backend tests: `cd backend && pytest tests/ -v`
  - [ ] Frontend tests: `cd frontend && npm test`
  - [ ] Review test output, note any failures
  - [ ] Read 3 test files to understand patterns:
    - [ ] `backend/tests/test_daily_report_state_machine.py`
    - [ ] `backend/tests/test_ledger_invariants.py`
    - [ ] `frontend/src/components/DailyReportForm.test.tsx`

**Estimated Time**: 6-7 hours

**Output**: Understanding of development workflows and testing patterns

---

### Day 5: First Hands-on Exercise (Read-only)

**Goal**: Explore the codebase with specific tasks to build familiarity.

#### Checklist

- [ ] **Exercise 6: Find SoT Violations (if any)**
  - [ ] Search for hardcoded states: `grep -r "final_locked" backend/` (should reference STATE_MACHINE.md)
  - [ ] Search for magic numbers: `grep -r "unit_price \* " backend/` (should have BR-xxx comments)
  - [ ] Search for custom error codes: `grep -r '"code":' backend/` (verify all exist in ERROR_CODES_SOT.md)
  - [ ] Search for direct UPDATE on ledger: `grep -r "UPDATE ledger_entries" backend/` (should be zero results)
  - [ ] Document findings in `notes/exercise-6-sot-audit.md`
  - [ ] Discuss with mentor if violations found

- [ ] **Exercise 7: State Machine Exploration**
  - [ ] Run local backend
  - [ ] Use Postman/curl to create a daily report:
    ```bash
    curl -X POST http://localhost:8000/api/v1/daily-reports \
      -H "Authorization: Bearer {token}" \
      -H "Content-Type: application/json" \
      -d '{
        "ad_account_id": 1,
        "report_date": "2025-11-27",
        "conversions_raw": 100,
        "raw_spend": 50.00
      }'
    ```
  - [ ] Observe response status (should be `raw_submitted`)
  - [ ] Try invalid transition: `PUT /daily-reports/{id}/state` with `final_locked` (should fail)
  - [ ] Check database: `SELECT * FROM daily_reports WHERE id = {id};`
  - [ ] Verify no ledger entry created (only happens at `final_locked`)

- [ ] **Exercise 8: Ledger System Inspection**
  - [ ] Query PROJECT ledger:
    ```sql
    SELECT type, amount, created_at
    FROM ledger_entries
    WHERE category = 'PROJECT'
    ORDER BY created_at DESC
    LIMIT 10;
    ```
  - [ ] Query SUPPLIER ledger:
    ```sql
    SELECT type, amount, created_at
    FROM ledger_entries
    WHERE category = 'SUPPLIER'
    ORDER BY created_at DESC
    LIMIT 10;
    ```
  - [ ] Verify balance formula:
    ```sql
    SELECT SUM(amount) as calculated_balance
    FROM ledger_entries
    WHERE category = 'PROJECT' AND project_id = 1;

    SELECT balance as stored_balance
    FROM projects
    WHERE id = 1;

    -- calculated_balance should equal stored_balance
    ```
  - [ ] Document any discrepancies

- [ ] **Week 1 Knowledge Checkpoint**
  - [ ] Complete the quiz below (answers in appendix)
  - [ ] Schedule 30-minute review with mentor
  - [ ] Discuss any confusion or questions

**Estimated Time**: 6-7 hours

**Output**: Hands-on familiarity with system behavior

---

### Week 1 Quiz (Self-Assessment)

**Instructions**: Answer without looking at docs. Check answers in §9.1.

```
Q1: In the裁判链, which document has higher priority:
    STATE_MACHINE.md or API_SOT.md?
A: _______________________

Q2: What are the 3 data streams in daily reports?
A: _______________________

Q3: Can a user with role 'media_buyer' modify conversions_final?
A: _______________________

Q4: What is the formula for calculating revenue in PROJECT ledger?
A: _______________________

Q5: If a daily_report is in state 'trend_pending', what are the valid
    next states?
A: _______________________

Q6: What is the only mechanism to correct a final_locked daily report?
A: _______________________

Q7: Which column type must be used for all financial amounts?
A: _______________________

Q8: What happens if you try to DELETE a ledger_entries record?
A: _______________________

Q9: Where is the single source of truth for error code definitions?
A: _______________________

Q10: What is the terminal state for topup_requests?
A: _______________________
```

**Passing Score**: 8/10 correct (review missed topics before Week 2)

---

## 4. Week 2: Deep Dive + Domain Knowledge

### Day 6-7: State Machine + Data Schema Mastery

**Goal**: Achieve expert-level understanding of state machines and schema design.

#### Day 6 Checklist

- [ ] **Deep Dive: daily_reports State Machine**
  - [ ] Re-read STATE_MACHINE.md §8 (Daily Report Lifecycle)
  - [ ] Study code implementation: `backend/services/daily_report_state_service.py`
  - [ ] Trace each transition function:
    - [ ] `submit_raw_data()` → `raw_submitted`
    - [ ] `start_trend_check()` → `trend_pending`
    - [ ] `approve_trend()` → `trend_ok`
    - [ ] `flag_trend()` → `trend_flagged`
    - [ ] `resolve_flagged_trend()` → `trend_resolved`
    - [ ] `initiate_final_review()` → `final_pending`
    - [ ] `confirm_final_data()` → `final_confirmed`
    - [ ] `lock_report()` → `final_locked` (triggers billing)
  - [ ] Review pre-condition checks in each function
  - [ ] Identify where ledger entries are created (`lock_report()`)

- [ ] **Deep Dive: topup_requests State Machine**
  - [ ] Read STATE_MACHINE.md §11 (Topup Lifecycle)
  - [ ] Study code: `backend/services/topup_service.py`
  - [ ] Trace transitions:
    - [ ] `draft` → `pending_review` (media_buyer submits)
    - [ ] `pending_review` → `finance_approve` (finance reviews)
    - [ ] `finance_approve` → `paid` (payment confirmed)
    - [ ] `paid` → `completed` (ledger entry created)
  - [ ] Understand rejection path: `pending_review` → `rejected`
  - [ ] Identify ledger creation point (`mark_as_completed()`)

- [ ] **Exercise 9: State Machine Bug Hunt**
  - [ ] Review `backend/services/daily_report_state_service.py`
  - [ ] Check if all transitions validate pre-conditions per STATE_MACHINE.md
  - [ ] Verify error codes match ERROR_CODES_SOT.md
  - [ ] Check if `lock_report()` correctly creates both REVENUE and COST entries
  - [ ] Look for any direct `UPDATE daily_reports SET status = ...` (prohibited)
  - [ ] Document findings in `notes/exercise-9-state-machine-audit.md`

**Estimated Time**: 6-7 hours

#### Day 7 Checklist

- [ ] **Deep Dive: Ledger Tables**
  - [ ] Re-read DATA_SCHEMA.md §4.12 (ledger_entries)
  - [ ] Study schema constraints:
    - [ ] `amount DECIMAL(12,2)` (precision enforcement)
    - [ ] `category CHECK IN ('PROJECT', 'SUPPLIER')` (dual-ledger)
    - [ ] `type CHECK IN ('RECHARGE', 'REVENUE', 'COST', 'REVERSAL', 'TRANSFER')`
    - [ ] `reversal_id` (nullable, links to original entry if REVERSAL)
  - [ ] Review indexes:
    - [ ] `idx_ledger_project` (project_id, category)
    - [ ] `idx_ledger_supplier` (supplier_id, category)
    - [ ] `idx_ledger_created` (created_at)

- [ ] **Deep Dive: Daily Reports Table**
  - [ ] Re-read DATA_SCHEMA.md §4.7 (daily_reports)
  - [ ] Study columns:
    - [ ] `conversions_raw` (投手提交, for trend check only)
    - [ ] `raw_spend` (投手提交, for trend check only)
    - [ ] `conversions_final` (运营确认, used for billing)
    - [ ] `real_spend` (运营录入, used for cost calculation)
    - [ ] `status` (state machine position)
    - [ ] `reversal_id` (if report was reversed)
  - [ ] Review UNIQUE constraint: `(ad_account_id, report_date)`
  - [ ] Review foreign keys: `ad_account_id`, `project_id`, `supplier_id`

- [ ] **Exercise 10: Schema Migration Practice**
  - [ ] Read a migration file: `supabase/migrations/20231115_create_daily_reports.sql`
  - [ ] Understand structure:
    - [ ] CREATE TABLE
    - [ ] ALTER TABLE ADD CONSTRAINT (CHECK)
    - [ ] CREATE INDEX
    - [ ] COMMENT ON COLUMN (documentation)
  - [ ] Practice writing a migration (not applied):
    ```sql
    -- Add a new column to daily_reports (example only, do not run)
    ALTER TABLE daily_reports
    ADD COLUMN notes TEXT;

    COMMENT ON COLUMN daily_reports.notes IS
    'Optional notes for trend resolution (BR-RPT-007)';
    ```
  - [ ] Review with mentor to ensure migration best practices

- [ ] **Exercise 11: Cross-Table Query Practice**
  - [ ] Write SQL to calculate total revenue for project_id=1:
    ```sql
    SELECT
      p.name as project_name,
      SUM(CASE WHEN le.type = 'REVENUE' THEN le.amount ELSE 0 END) as total_revenue,
      COUNT(DISTINCT dr.id) as num_reports
    FROM projects p
    LEFT JOIN ledger_entries le ON le.project_id = p.id AND le.category = 'PROJECT'
    LEFT JOIN daily_reports dr ON dr.project_id = p.id AND dr.status = 'final_locked'
    WHERE p.id = 1
    GROUP BY p.id, p.name;
    ```
  - [ ] Write SQL to find all unresolved trend-flagged reports:
    ```sql
    SELECT
      dr.id,
      dr.report_date,
      aa.name as account_name,
      dr.conversions_raw,
      dr.raw_spend,
      dr.created_at
    FROM daily_reports dr
    JOIN ad_accounts aa ON aa.id = dr.ad_account_id
    WHERE dr.status = 'trend_flagged'
    ORDER BY dr.created_at ASC;
    ```
  - [ ] Test queries on local database

**Estimated Time**: 6-7 hours

**Output**: Mastery of state machines and schema relationships

---

### Day 8: Ledger System + Dual-Ledger Architecture

**Goal**: Master the financial audit trail and dual-ledger system.

#### Checklist

- [ ] **Deep Dive: Ledger Service**
  - [ ] Read `backend/services/ledger_service.py` in full
  - [ ] Study key functions:
    - [ ] `create_recharge_entry()` (adds balance)
    - [ ] `create_revenue_entry()` (deducts from PROJECT balance)
    - [ ] `create_cost_entry()` (deducts from SUPPLIER balance)
    - [ ] `create_reversal_entry()` (cancels previous entry)
    - [ ] `calculate_balance()` (SUM aggregation)
  - [ ] Verify each function validates category (PROJECT vs SUPPLIER)
  - [ ] Check REVERSAL logic (must have approval_ref, must reference original entry)

- [ ] **Deep Dive: Balance Calculation**
  - [ ] Review LEDGER_SOT.md §4 (Balance Calculation)
  - [ ] Study implementation:
    ```python
    def calculate_balance(category: str, entity_id: int) -> Decimal:
        result = db.query(func.sum(LedgerEntry.amount)).\
            filter(LedgerEntry.category == category).\
            filter(
                LedgerEntry.project_id == entity_id if category == 'PROJECT'
                else LedgerEntry.supplier_id == entity_id
            ).scalar()
        return result or Decimal('0.00')
    ```
  - [ ] Verify no direct UPDATE of balance columns (should only update via triggers or batch jobs)

- [ ] **Exercise 12: Simulate Billing Flow**
  - [ ] Create test scenario:
    1. Create project with `unit_price = 1.50`
    2. Create daily_report with `conversions_final = 100`
    3. Transition to `final_locked`
    4. Verify ledger entry created:
       - `type = 'REVENUE'`
       - `category = 'PROJECT'`
       - `amount = -150.00` (negative, deducts balance)
    5. Verify project balance decreased by 150.00
  - [ ] Write SQL to validate:
    ```sql
    SELECT * FROM ledger_entries
    WHERE daily_report_id = {id} AND type = 'REVENUE';

    SELECT balance FROM projects WHERE id = {project_id};
    ```
  - [ ] Document flow in `notes/exercise-12-billing-flow.md`

- [ ] **Exercise 13: Simulate REVERSAL**
  - [ ] Continue from Exercise 12
  - [ ] Assume ledger entry from step 4 above has id = 123
  - [ ] Execute REVERSAL (via API or SQL):
    ```python
    reversal_entry = create_reversal_entry(
        original_entry_id=123,
        approval_ref='APPROVAL-2025-001',
        operator='finance_user'
    )
    ```
  - [ ] Verify reversal entry:
    - `type = 'REVERSAL'`
    - `category = 'PROJECT'`
    - `amount = +150.00` (positive, reverses the -150.00)
    - `reversal_id = 123` (links to original)
  - [ ] Verify balance restored:
    ```sql
    SELECT SUM(amount) FROM ledger_entries
    WHERE category = 'PROJECT' AND project_id = {project_id};
    -- Should be original balance
    ```

- [ ] **Exercise 14: Test Prohibited Operations**
  - [ ] Try direct UPDATE on ledger (should fail):
    ```sql
    UPDATE ledger_entries SET amount = 0.00 WHERE id = 123;
    -- Expected: Error or prevented by RLS/triggers
    ```
  - [ ] Try DELETE on ledger (should fail):
    ```sql
    DELETE FROM ledger_entries WHERE id = 123;
    -- Expected: Error or prevented by RLS
    ```
  - [ ] Try mixed category (should fail):
    ```python
    create_revenue_entry(
        category='SUPPLIER',  # Wrong! Revenue must be PROJECT
        project_id=1,
        amount=100.00
    )
    # Expected: ValidationError
    ```
  - [ ] Document results

**Estimated Time**: 6-7 hours

**Output**: Deep understanding of ledger system and financial invariants

---

### Day 9: Testing Strategy

**Goal**: Learn to write SoT-compliant tests and achieve >80% coverage.

#### Checklist

- [ ] **Review Testing Pyramid**
  - [ ] Re-read TESTING_STRATEGY.md §2 (Test Pyramid)
  - [ ] Understand test distribution:
    - [ ] 60% Unit tests (fast, isolated, pure logic)
    - [ ] 30% Integration tests (API + DB, realistic scenarios)
    - [ ] 10% E2E tests (full user flows, critical paths)

- [ ] **Study Unit Test Patterns**
  - [ ] Read `backend/tests/unit/test_ledger_service.py`
  - [ ] Note test structure:
    ```python
    # Test: INV-001 - Ledger immutability
    def test_ledger_entry_cannot_be_updated():
        # Setup
        entry = create_test_ledger_entry()

        # Execute & Assert
        with pytest.raises(ImmutabilityError) as exc:
            update_ledger_entry(entry.id, amount=0.00)

        assert exc.value.code == "BIZ-201"
    ```
  - [ ] Review mocking strategy:
    ```python
    @patch('services.ledger_service.db.query')
    def test_calculate_balance(mock_query):
        mock_query.return_value.scalar.return_value = Decimal('1000.00')
        balance = calculate_balance('PROJECT', 1)
        assert balance == Decimal('1000.00')
    ```

- [ ] **Study Integration Test Patterns**
  - [ ] Read `backend/tests/integration/test_daily_report_api.py`
  - [ ] Note test structure:
    ```python
    # Test: STATE_MACHINE.md §8 - Daily report lifecycle
    def test_daily_report_full_lifecycle(client, db_session):
        # Create report
        response = client.post('/api/v1/daily-reports', json={...})
        assert response.status_code == 201
        report_id = response.json()['data']['id']

        # Verify initial state
        report = db_session.query(DailyReport).get(report_id)
        assert report.status == 'raw_submitted'

        # Transition to trend_pending
        response = client.put(f'/api/v1/daily-reports/{report_id}/transition',
                              json={'action': 'start_trend_check'})
        assert response.status_code == 200

        # ... continue testing all transitions
    ```

- [ ] **Study E2E Test Patterns**
  - [ ] Read `frontend/tests/e2e/daily-report-submission.spec.ts` (Playwright)
  - [ ] Note test structure:
    ```typescript
    test('media buyer submits daily report', async ({ page }) => {
      // Login
      await page.goto('/login');
      await page.fill('[name="email"]', 'media_buyer@test.com');
      await page.fill('[name="password"]', 'password');
      await page.click('button[type="submit"]');

      // Navigate to daily reports
      await page.click('text=Daily Reports');

      // Submit report
      await page.click('text=New Report');
      await page.fill('[name="conversions_raw"]', '100');
      await page.fill('[name="raw_spend"]', '50.00');
      await page.click('button:has-text("Submit")');

      // Verify success
      await expect(page.locator('.success-message')).toBeVisible();
      await expect(page.locator('[data-status="raw_submitted"]')).toBeVisible();
    });
    ```

- [ ] **Exercise 15: Write Your First Unit Test**
  - [ ] Create `backend/tests/unit/test_my_first_test.py`
  - [ ] Write test for balance calculation:
    ```python
    import pytest
    from decimal import Decimal
    from services.ledger_service import calculate_balance
    from models import LedgerEntry

    # Test: BR-FIN-003 - Decimal precision for balances
    def test_balance_calculation_decimal_precision():
        # This is a simplified example; use fixtures in real tests
        entries = [
            {'amount': Decimal('100.00')},
            {'amount': Decimal('-25.50')},
            {'amount': Decimal('10.75')}
        ]

        total = sum(e['amount'] for e in entries)
        assert total == Decimal('85.25')
        assert isinstance(total, Decimal)
    ```
  - [ ] Run test: `pytest backend/tests/unit/test_my_first_test.py -v`
  - [ ] Verify it passes

- [ ] **Exercise 16: Write Your First Integration Test**
  - [ ] Create `backend/tests/integration/test_my_first_integration.py`
  - [ ] Write test for topup creation:
    ```python
    # Test: STATE_MACHINE.md §11 - Topup request creation
    def test_create_topup_request(client, auth_headers):
        response = client.post('/api/v1/topup-requests',
                               headers=auth_headers,
                               json={
                                   'project_id': 1,
                                   'amount': '500.00',
                                   'notes': 'Test topup'
                               })

        assert response.status_code == 201
        data = response.json()['data']
        assert data['status'] == 'draft'
        assert Decimal(data['amount']) == Decimal('500.00')
    ```
  - [ ] Run test: `pytest backend/tests/integration/test_my_first_integration.py -v`
  - [ ] Verify it passes

- [ ] **Review Test Coverage**
  - [ ] Run backend coverage: `pytest --cov=backend --cov-report=html`
  - [ ] Open `htmlcov/index.html` in browser
  - [ ] Identify uncovered lines in `services/ledger_service.py`
  - [ ] Run frontend coverage: `npm test -- --coverage`
  - [ ] Review coverage report

**Estimated Time**: 6-7 hours

**Output**: Ability to write unit and integration tests aligned with SoT

---

### Day 10: First Code Contribution (Bug Fix)

**Goal**: Make your first commit to the codebase by fixing a simple bug.

#### Checklist

- [ ] **Find a Suitable Bug**
  - [ ] Check issue tracker for `good-first-issue` label
  - [ ] Ask mentor to assign a simple bug (e.g., validation error, UI text fix)
  - [ ] Example bugs:
    - [ ] Missing error message for invalid date range
    - [ ] Typo in API response field name
    - [ ] Missing validation for negative amounts

- [ ] **Create Feature Branch**
  - [ ] Checkout master: `git checkout master`
  - [ ] Pull latest: `git pull origin master`
  - [ ] Create branch: `git checkout -b fix/issue-123-validation-error`

- [ ] **Fix the Bug (SoT-First Process)**
  - [ ] Query relevant SoT documents (use裁判链)
  - [ ] Verify fix doesn't violate invariants
  - [ ] Implement fix in code
  - [ ] Add/update tests to cover the bug
  - [ ] Run tests: `pytest` (backend) or `npm test` (frontend)
  - [ ] Verify all tests pass

- [ ] **Code Review Checklist (Self-Review)**
  - [ ] SoT Compliance:
    - [ ] All states from STATE_MACHINE.md?
    - [ ] All error codes from ERROR_CODES_SOT.md?
    - [ ] Decimal types for financial amounts?
  - [ ] Code Quality:
    - [ ] No magic numbers (named constants with BR-xxx comments)
    - [ ] TypeScript strict mode (no `any` types)
    - [ ] Proper error handling (Result<T, E> pattern)
  - [ ] Testing:
    - [ ] Test added/updated?
    - [ ] Coverage >80%?
    - [ ] Test references SoT rules in comments?

- [ ] **Commit and Push**
  - [ ] Stage changes: `git add .`
  - [ ] Commit with conventional message:
    ```
    fix(validation): add date range validation for daily reports

    - Add validation to prevent future dates in daily_reports.report_date
    - Return error code VAL-005 per ERROR_CODES_SOT.md v2.1
    - Add test case to cover invalid date scenarios
    - Ref: BR-RPT-003 (BUSINESS_RULES.md)

    Closes #123
    ```
  - [ ] Push: `git push origin fix/issue-123-validation-error`

- [ ] **Create Pull Request**
  - [ ] Open GitHub/GitLab
  - [ ] Create PR from your branch to `master`
  - [ ] Fill PR template:
    - [ ] Description: What bug was fixed and how
    - [ ] SoT References: Which documents were consulted
    - [ ] Testing: How was the fix verified
    - [ ] Breaking Changes: None (for bug fixes)
  - [ ] Request review from mentor
  - [ ] Address review comments
  - [ ] Merge after approval

- [ ] **Celebrate First Contribution!**
  - [ ] Share in `#ai-ad-spend-dev` Slack channel
  - [ ] Update onboarding notes with lessons learned

**Estimated Time**: 6-8 hours

**Output**: First merged pull request

---

### Week 2 Quiz (Self-Assessment)

**Instructions**: Answer without looking at docs. Check answers in §9.2.

```
Q1: What are the 8 states in daily_reports state machine (in order)?
A: _______________________

Q2: At which state does billing (REVENUE) get triggered?
A: _______________________

Q3: What is the balance calculation formula for PROJECT ledger?
A: _______________________

Q4: What are the 5 ledger entry types?
A: _______________________

Q5: Can you UPDATE a ledger_entries.amount field after creation?
A: _______________________

Q6: What are the 3 test layers in the test pyramid and their percentages?
A: _______________________

Q7: Which service function creates a REVERSAL entry?
A: _______________________

Q8: What column constraint ensures dual-ledger separation?
A: _______________________

Q9: What is the UNIQUE constraint on daily_reports table?
A: _______________________

Q10: What is the minimum test coverage requirement for new code?
A: _______________________
```

**Passing Score**: 9/10 correct (review missed topics before Week 3)

---

## 5. Week 3: Advanced Topics + Independent Work

### Day 11-12: API Development Flow + Frontend Rules

**Goal**: Master full-stack development workflows.

#### Day 11 Checklist (Backend Focus)

- [ ] **Deep Dive: API Development Flow**
  - [ ] Re-read API_DEVELOPMENT_FLOW.md §1-10 in detail
  - [ ] Study the 7-step process with real example (`POST /api/v1/topup-requests`)

- [ ] **Step 1-3: Design Phase**
  - [ ] Query SoT: TOPUP_SOT.md, STATE_MACHINE.md §11, DATA_SCHEMA.md §4.10
  - [ ] Design endpoint contract:
    ```typescript
    // Request
    POST /api/v1/topup-requests
    {
      "project_id": number,
      "amount": string (decimal),
      "notes"?: string
    }

    // Response 201
    {
      "data": {
        "id": number,
        "status": "draft",
        "project_id": number,
        "amount": string,
        "created_at": string (ISO 8601)
      }
    }

    // Error Response 400
    {
      "error": {
        "code": "VAL-003",
        "message": "Amount must be positive"
      }
    }
    ```
  - [ ] Define Zod schema:
    ```typescript
    const CreateTopupRequestSchema = z.object({
      project_id: z.number().int().positive(),
      amount: z.string().regex(/^\d+\.\d{2}$/),
      notes: z.string().optional()
    });
    ```

- [ ] **Step 4-5: Implementation**
  - [ ] Service layer: `services/topup_service.py`
    ```python
    def create_topup_request(data: CreateTopupDTO) -> Result[TopupRequest, Error]:
        # Validate amount precision (BR-FIN-003)
        if not is_valid_decimal(data.amount, 12, 2):
            return Err(Error(code="VAL-003", message="Invalid amount precision"))

        # Check project exists
        project = db.query(Project).get(data.project_id)
        if not project:
            return Err(Error(code="BIZ-101", message="Project not found"))

        # Create request
        topup = TopupRequest(
            project_id=data.project_id,
            amount=data.amount,
            status='draft',  # STATE_MACHINE.md §11
            notes=data.notes
        )
        db.add(topup)
        db.commit()

        return Ok(topup)
    ```
  - [ ] API endpoint: `routes/topup_requests.py`
    ```python
    @router.post('/topup-requests', status_code=201)
    def create_topup(request: CreateTopupRequest, current_user: User = Depends(get_current_user)):
        # Authorize (AUTH_SPEC.md - media_buyer or account_manager)
        if current_user.role not in ['media_buyer', 'account_manager']:
            raise ForbiddenError(code="AUTH-003")

        # Validate schema
        validated = CreateTopupRequestSchema.parse(request.dict())

        # Call service
        result = topup_service.create_topup_request(validated)

        # Handle result
        if result.is_err():
            error = result.unwrap_err()
            raise HTTPException(status_code=400, detail=error.dict())

        return {"data": result.unwrap().dict()}
    ```

- [ ] **Exercise 17: Implement a Simple Endpoint**
  - [ ] Task: Add `GET /api/v1/daily-reports/:id` endpoint
  - [ ] Follow 7-step process:
    1. Query SoT: API_SOT.md, DATA_SCHEMA.md
    2. Design contract (request/response schema)
    3. Define Zod schema
    4. Implement service function
    5. Implement endpoint handler
    6. Write unit + integration tests
    7. Update API documentation (OpenAPI)
  - [ ] Submit for mentor review

**Estimated Time**: 6-7 hours

#### Day 12 Checklist (Frontend Focus)

- [ ] **Deep Dive: Frontend Development Rules**
  - [ ] Re-read FRONTEND_DEVELOPMENT_RULES.md §1-10

- [ ] **Component Architecture**
  - [ ] Study project structure: `frontend/src/`
  - [ ] Review component patterns:
    - [ ] Presentational components: `components/common/Button.tsx`
    - [ ] Container components: `components/features/DailyReportList.tsx`
    - [ ] Page components: `pages/DailyReportsPage.tsx`
  - [ ] Understand props typing:
    ```typescript
    interface DailyReportFormProps {
      initialData?: DailyReport;
      onSubmit: (data: CreateDailyReportDTO) => Promise<void>;
      readOnly?: boolean;
    }
    ```

- [ ] **State Management (Zustand)**
  - [ ] Study store: `frontend/src/stores/authStore.ts`
    ```typescript
    interface AuthState {
      user: User | null;
      token: string | null;
      login: (email: string, password: string) => Promise<void>;
      logout: () => void;
    }

    export const useAuthStore = create<AuthState>((set) => ({
      user: null,
      token: null,
      login: async (email, password) => {
        const { user, token } = await authService.login(email, password);
        set({ user, token });
      },
      logout: () => set({ user: null, token: null })
    }));
    ```

- [ ] **Data Fetching (React Query)**
  - [ ] Study hook: `frontend/src/hooks/useDailyReports.ts`
    ```typescript
    export function useDailyReports(filters?: DailyReportFilters) {
      return useQuery({
        queryKey: ['daily-reports', filters],
        queryFn: () => apiClient.get('/daily-reports', { params: filters }),
        staleTime: 5 * 60 * 1000, // 5 minutes
      });
    }

    export function useCreateDailyReport() {
      const queryClient = useQueryClient();

      return useMutation({
        mutationFn: (data: CreateDailyReportDTO) =>
          apiClient.post('/daily-reports', data),
        onSuccess: () => {
          // Invalidate cache to refetch
          queryClient.invalidateQueries(['daily-reports']);
        }
      });
    }
    ```

- [ ] **SoT-Driven UI State Mapping**
  - [ ] Study status badge: `components/common/StatusBadge.tsx`
    ```typescript
    // STATE_MACHINE.md §8 - Maps backend states to UI
    const STATUS_CONFIG: Record<DailyReportStatus, StatusBadgeConfig> = {
      raw_submitted: { color: 'blue', label: 'Raw Submitted' },
      trend_pending: { color: 'yellow', label: 'Trend Check Pending' },
      trend_ok: { color: 'green', label: 'Trend OK' },
      trend_flagged: { color: 'red', label: 'Trend Flagged' },
      trend_resolved: { color: 'green', label: 'Trend Resolved' },
      final_pending: { color: 'yellow', label: 'Final Review Pending' },
      final_confirmed: { color: 'blue', label: 'Final Confirmed' },
      final_locked: { color: 'gray', label: 'Locked', icon: 'LockIcon' }
    };
    ```

- [ ] **Exercise 18: Build a Simple Form Component**
  - [ ] Task: Create `TopupRequestForm.tsx`
  - [ ] Requirements:
    - [ ] Props: `onSubmit`, `initialData?`, `readOnly?`
    - [ ] Fields: `project_id` (select), `amount` (number), `notes` (textarea)
    - [ ] Validation: Zod schema matching backend
    - [ ] Submit handler: Call `useCreateTopupRequest` mutation
    - [ ] Error handling: Display error messages from API
    - [ ] Loading state: Disable form during submission
  - [ ] Write Vitest tests: `TopupRequestForm.test.tsx`
  - [ ] Submit for mentor review

**Estimated Time**: 6-7 hours

**Output**: Full-stack development capability

---

### Day 13: Agent Workflow Training

**Goal**: Master AI agent usage for accelerated development.

#### Checklist

- [ ] **Setup SuperClaude Commands**
  - [ ] Review installed commands: Open Cursor, type `/sc:help`
  - [ ] Verify key commands available:
    - [ ] `/sc:implement` - Feature implementation
    - [ ] `/sc:test` - Test generation
    - [ ] `/sc:explain` - Code explanation
    - [ ] `/sc:analyze` - Code analysis
    - [ ] `/sc:improve` - Code improvements

- [ ] **Practice: SoT-First Query**
  - [ ] Open terminal in Cursor
  - [ ] Type: `/sc:explain @docs/sot/STATE_MACHINE.md daily_reports state machine`
  - [ ] Review agent's explanation
  - [ ] Ask follow-up: "What are the prohibited transitions?"
  - [ ] Verify agent references STATE_MACHINE.md v2.7

- [ ] **Practice: Code Generation**
  - [ ] Type: `/sc:implement`
  - [ ] Prompt:
    ```
    Implement a service function to transition daily_report
    from 'final_confirmed' to 'final_locked'.

    Requirements:
    - Follow STATE_MACHINE.md v2.7 §8
    - Create REVENUE entry per LEDGER_SOT.md v1.2
    - Create COST entry per LEDGER_SOT.md v1.2
    - Validate pre-conditions per MASTER.md INV-003
    - Use error codes from ERROR_CODES_SOT.md v2.1
    - Return Result<DailyReport, Error>
    ```
  - [ ] Review generated code
  - [ ] Verify SoT references in comments
  - [ ] Check error codes match ERROR_CODES_SOT.md
  - [ ] Run tests if generated

- [ ] **Practice: Test Generation**
  - [ ] Type: `/sc:test`
  - [ ] Prompt:
    ```
    Generate integration tests for the lock_daily_report function.

    Test cases:
    1. Successful lock with REVENUE + COST creation
    2. Lock fails if status != 'final_confirmed'
    3. Lock fails if conversions_final = 0 AND real_spend = 0
    4. Verify ledger entries created with correct amounts

    Reference:
    - STATE_MACHINE.md v2.7 §8
    - LEDGER_SOT.md v1.2 §3-4
    - TESTING_STRATEGY.md v1.0 §5
    ```
  - [ ] Review generated tests
  - [ ] Verify test structure matches existing patterns
  - [ ] Run tests: `pytest -v`

- [ ] **Practice: Code Review with Agent**
  - [ ] Find a complex function: `services/reconciliation_service.py`
  - [ ] Type: `/sc:analyze @backend/services/reconciliation_service.py`
  - [ ] Ask agent:
    ```
    Analyze this code for SoT compliance:
    1. Are all states from STATE_MACHINE.md?
    2. Are all error codes from ERROR_CODES_SOT.md?
    3. Are financial amounts using Decimal?
    4. Are there any prohibited operations (UPDATE ledger, etc.)?
    5. Are there missing tests for edge cases?
    ```
  - [ ] Review agent's findings
  - [ ] Create issues for any violations found

- [ ] **Practice: Refactoring**
  - [ ] Type: `/sc:improve @backend/services/old_topup_service.py`
  - [ ] Prompt:
    ```
    Refactor this service to align with:
    - API_DEVELOPMENT_FLOW.md (Result pattern)
    - BUSINESS_RULES.md (validation rules)
    - STATE_MACHINE.md (state transitions)

    Improvements needed:
    1. Replace exceptions with Result<T, E>
    2. Add SoT rule comments (BR-xxx, INV-xxx)
    3. Extract validation logic to separate functions
    4. Add missing pre-condition checks
    ```
  - [ ] Review refactored code
  - [ ] Test refactored version

- [ ] **Agent Workflow Best Practices**
  - [ ] Always reference specific SoT documents in prompts
  - [ ] Use `@file:docs/sot/MASTER.md` to include context
  - [ ] Break complex tasks into small agent calls
  - [ ] Review all agent-generated code (do not blindly accept)
  - [ ] Verify SoT references are accurate and up-to-date
  - [ ] Re-run tests after any agent changes

**Estimated Time**: 6-7 hours

**Output**: Proficiency in AI-assisted development

---

### Day 14: Feature Implementation (Supervised)

**Goal**: Implement a small feature end-to-end with mentor supervision.

#### Checklist

- [ ] **Choose Feature**
  - [ ] Mentor assigns a small feature (e.g., "Add filter by status to daily reports list")
  - [ ] Alternative features:
    - [ ] Add export-to-CSV for daily reports
    - [ ] Add pagination to topup requests list
    - [ ] Add bulk status update for ad accounts

- [ ] **Planning Phase (SoT-First)**
  - [ ] Query relevant SoT documents:
    - [ ] STATE_MACHINE.md (for valid status values)
    - [ ] API_SOT.md (for endpoint design)
    - [ ] DATA_SCHEMA.md (for query structure)
    - [ ] FRONTEND_DEVELOPMENT_RULES.md (for UI patterns)
  - [ ] Write design doc in `notes/feature-[name]-design.md`:
    ```markdown
    # Feature: Filter Daily Reports by Status

    ## SoT References
    - STATE_MACHINE.md v2.7 §8 (valid status values)
    - API_SOT.md v9.3 §3 (query parameter conventions)
    - DATA_SCHEMA.md v5.3 §4.7 (daily_reports schema)

    ## Backend Changes
    - Modify `GET /api/v1/daily-reports` to accept `?status=` query param
    - Validate status value against STATE_MACHINE.md enum
    - Return error VAL-006 if invalid status

    ## Frontend Changes
    - Add status filter dropdown to DailyReportList
    - Map backend states to UI labels (StatusBadge config)
    - Update URL query params on filter change

    ## Tests
    - Unit: Validate status enum values
    - Integration: Filter returns correct reports
    - E2E: User can filter via dropdown
    ```
  - [ ] Review design with mentor

- [ ] **Implementation Phase**
  - [ ] Backend:
    - [ ] Modify endpoint handler to accept `status` param
    - [ ] Add validation per STATE_MACHINE.md
    - [ ] Update service layer query
    - [ ] Write unit tests for validation
    - [ ] Write integration tests for endpoint
  - [ ] Frontend:
    - [ ] Add filter component to page
    - [ ] Update React Query hook to include filter
    - [ ] Add Vitest tests for filter component
    - [ ] Add Playwright E2E test

- [ ] **Testing Phase**
  - [ ] Run backend tests: `pytest -v`
  - [ ] Run frontend tests: `npm test`
  - [ ] Run E2E tests: `npm run test:e2e`
  - [ ] Manual testing in browser:
    - [ ] Select each status from dropdown
    - [ ] Verify filtered results
    - [ ] Check URL updates correctly
    - [ ] Test edge cases (no results, invalid status)

- [ ] **Code Review Phase**
  - [ ] Self-review against checklist:
    - [ ] SoT compliance verified?
    - [ ] All tests passing?
    - [ ] Coverage >80%?
    - [ ] Comments include SoT references?
    - [ ] No TypeScript `any` types?
    - [ ] Decimal types for amounts?
  - [ ] Create PR with detailed description
  - [ ] Request mentor review
  - [ ] Address review feedback
  - [ ] Merge after approval

**Estimated Time**: 6-8 hours

**Output**: Complete feature implementation following all best practices

---

### Day 15: Knowledge Assessment + Graduation Task

**Goal**: Validate onboarding completion and graduate to independent development.

#### Checklist

- [ ] **Comprehensive Knowledge Assessment**
  - [ ] Complete the quiz in §7 (30 questions covering all topics)
  - [ ] Review with mentor, discuss any wrong answers
  - [ ] Passing score: 27/30 (90%)

- [ ] **Graduation Task: Independent Feature**
  - [ ] Mentor assigns a medium-complexity feature (no hand-holding)
  - [ ] Example tasks:
    - [ ] Implement REVERSAL API endpoint with full workflow
    - [ ] Add reconciliation batch creation feature
    - [ ] Implement ad account status transition with alerts
  - [ ] Requirements:
    - [ ] Complete design doc
    - [ ] Full backend + frontend implementation
    - [ ] Comprehensive test suite (>85% coverage)
    - [ ] Documentation updates
    - [ ] PR passes CI/CD checks
  - [ ] Timeline: 2-3 days (Days 15-17)

- [ ] **Code Review Presentation**
  - [ ] Present your graduation task to team
  - [ ] Explain SoT-driven design decisions
  - [ ] Demo the feature in action
  - [ ] Walk through test coverage
  - [ ] Answer questions from team

- [ ] **Onboarding Feedback**
  - [ ] Fill out onboarding survey (link from mentor)
  - [ ] Provide feedback on:
    - [ ] Most helpful resources
    - [ ] Confusing sections
    - [ ] Suggested improvements
    - [ ] Missing topics

- [ ] **Graduation Checklist**
  - [ ] All Week 1-3 exercises completed
  - [ ] All quizzes passed (>90% each)
  - [ ] At least 3 merged PRs (bug fix + feature + graduation task)
  - [ ] Test coverage >80% on all new code
  - [ ] No SoT violations in code reviews
  - [ ] Can independently query裁判链 for decisions
  - [ ] Comfortable using AI agents for development

- [ ] **Welcome to the Team!**
  - [ ] Add yourself to `CONTRIBUTORS.md`
  - [ ] Update team Slack channel with introduction
  - [ ] Schedule regular sync with team lead

**Estimated Time**: 8-10 hours (plus graduation task)

**Output**: Certified onboarding completion, ready for independent work

---

## 6. Knowledge Checkpoints

### 6.1 Daily Micro-Quizzes

**Day 1 Quiz**: See §3 (Day 1 section)
**Day 3 Quiz**: See §3 (Day 2-3 section)
**Day 5 Quiz**: See §3 (Week 1 section)
**Day 10 Quiz**: See §4 (Week 2 section)

### 6.2 Comprehensive Final Assessment (Day 15)

**Instructions**: Answer all 30 questions without reference materials. Passing score: 27/30.

#### Section A: Architecture & SoT (10 questions)

1. What is the highest-priority document in the裁判链?
2. What are the 5 core mechanisms in MASTER.md §1.3?
3. What is the terminal state for `daily_reports`?
4. What is the terminal state for `topup_requests`?
5. Which document defines error codes?
6. Which document defines state transitions?
7. Which document defines database schema?
8. What is the purpose of the Freeze mechanism?
9. What are the 3 data streams in daily reports?
10. What are the 2 ledger categories?

#### Section B: State Machines (5 questions)

11. What are the 8 states of `daily_reports` in order?
12. Can you transition from `trend_flagged` directly to `final_pending`? Why?
13. What pre-condition is required to transition to `final_locked`?
14. What is triggered when a daily report reaches `final_locked`?
15. Can you transition from `final_locked` to any other state? Why?

#### Section C: Ledger System (5 questions)

16. What is the balance calculation formula for PROJECT ledger?
17. What are the 5 ledger entry types?
18. Can you UPDATE a `ledger_entries.amount` field? Why?
19. What is the sign of a REVENUE entry amount?
20. What is required to create a REVERSAL entry?

#### Section D: Business Rules (5 questions)

21. What data type must be used for all financial amounts (BR-FIN-003)?
22. What is the UNIQUE constraint on `daily_reports`?
23. Can a `media_buyer` modify `conversions_final`? Why?
24. What role can execute REVERSAL operations?
25. What is the formula for calculating REVENUE?

#### Section E: Development Practices (5 questions)

26. What are the 3 test layers and their percentages?
27. What is the minimum test coverage requirement?
28. What pattern should be used for error handling in services?
29. What is prohibited in TypeScript strict mode?
30. What is the conventional commit message format?

**Answers**: See §9.3 for answer key

---

## 7. Resources & Contacts

### 7.1 Documentation Quick Links

| Category | Document | Location | Version |
|----------|----------|----------|---------|
| **Architecture** | MASTER.md | `docs/sot/MASTER.md` | v3.4 |
| **Architecture** | PROJECT.md | `docs/1.overview/PROJECT.md` | v1.2 |
| **SoT** | STATE_MACHINE.md | `docs/sot/STATE_MACHINE.md` | v2.6 |
| **SoT** | DATA_SCHEMA.md | `docs/sot/DATA_SCHEMA.md` | v5.2 |
| **SoT** | LEDGER_SOT.md | `docs/sot/LEDGER_SOT.md` | v1.1 |
| **SoT** | BUSINESS_RULES.md | `docs/sot/BUSINESS_RULES.md` | v3.1 |
| **SoT** | API_SOT.md | `docs/sot/API_SOT.md` | v9.0 |
| **SoT** | ERROR_CODES_SOT.md | `docs/sot/ERROR_CODES_SOT.md` | v2.1 |
| **Dev Guide** | API_DEVELOPMENT_FLOW.md | `docs/2.dev-guides/API_DEVELOPMENT_FLOW.md` | v1.0 |
| **Dev Guide** | FRONTEND_DEVELOPMENT_RULES.md | `docs/2.dev-guides/FRONTEND_DEVELOPMENT_RULES.md` | v1.0 |
| **Dev Guide** | TESTING_STRATEGY.md | `docs/2.dev-guides/TESTING_STRATEGY.md` | v1.0 |
| **Dev Guide** | AGENT_WORKFLOW_GUIDE.md | `docs/2.dev-guides/AGENT_WORKFLOW_GUIDE.md` | v1.0 |
| **Dev Guide** | DEPLOYMENT_GUIDE.md | `docs/2.dev-guides/DEPLOYMENT_GUIDE.md` | v1.0 |
| **Setup** | BACKEND_SETUP.md | `docs/2.dev-guides/BACKEND_SETUP.md` | v1.0 |
| **Setup** | FRONTEND_SETUP.md | `docs/2.dev-guides/FRONTEND_SETUP.md` | v1.0 |

### 7.2 Reading Time Estimates

| Document | Estimated Time | Priority |
|----------|----------------|----------|
| MASTER.md v4.4 | 45 min | P0 (Day 1) |
| STATE_MACHINE.md v2.7 | 90 min | P0 (Day 2) |
| DATA_SCHEMA.md v5.3 | 120 min | P0 (Day 2) |
| LEDGER_SOT.md v1.2 | 90 min | P0 (Day 3) |
| BUSINESS_RULES.md v4.1 | 60 min | P0 (Day 3) |
| API_SOT.md v9.3 | 60 min | P1 (Day 3) |
| ERROR_CODES_SOT.md v2.1 | 30 min | P1 (Day 3) |
| API_DEVELOPMENT_FLOW.md | 90 min | P0 (Day 4) |
| FRONTEND_DEVELOPMENT_RULES.md | 60 min | P0 (Day 4) |
| TESTING_STRATEGY.md | 60 min | P0 (Day 4) |
| AGENT_WORKFLOW_GUIDE.md | 60 min | P1 (Day 4) |
| DEPLOYMENT_GUIDE.md | 45 min | P2 (Week 3) |
| **Total Reading Time** | **~13 hours** | - |

### 7.3 Team Contacts

| Role | Name | Slack | Email | Responsibilities |
|------|------|-------|-------|------------------|
| **Tech Lead** | Wade | @wade | wade@example.com | Architecture, SoT governance, RFC reviews |
| **Backend Lead** | TBD | @backend-lead | backend@example.com | Backend development, API reviews |
| **Frontend Lead** | TBD | @frontend-lead | frontend@example.com | Frontend development, UI/UX |
| **QA Lead** | TBD | @qa-lead | qa@example.com | Testing strategy, test reviews |
| **DevOps** | TBD | @devops | devops@example.com | CI/CD, deployment, infrastructure |
| **Onboarding Mentor** | (Assigned) | @your-mentor | mentor@example.com | 1:1 support, code reviews, questions |

### 7.4 Communication Channels

- **Slack Channels**:
  - `#ai-ad-spend-dev` - General development discussion
  - `#ai-ad-spend-sot` - SoT updates, RFC discussions
  - `#ai-ad-spend-alerts` - CI/CD alerts, deployment notifications
  - `#ai-ad-spend-onboarding` - Onboarding questions and support

- **Meetings**:
  - Daily Standup: Mon-Fri 10:00 AM (15 min)
  - Sprint Planning: Every 2 weeks, Monday 2:00 PM (2 hours)
  - Code Review Sessions: Wed 3:00 PM (1 hour)
  - Onboarding Check-ins: Week 1/2/3 Friday 4:00 PM with mentor (30 min)

### 7.5 External Resources

- **Supabase Docs**: https://supabase.com/docs
- **React Query Docs**: https://tanstack.com/query/latest
- **Zustand Docs**: https://docs.pmnd.rs/zustand/getting-started/introduction
- **Zod Docs**: https://zod.dev/
- **Playwright Docs**: https://playwright.dev/
- **Pytest Docs**: https://docs.pytest.org/

---

## 8. Hands-on Exercises Summary

| Exercise | Day | Topic | Time | Deliverable |
|----------|-----|-------|------|-------------|
| Exercise 1 | 2 | State Diagram Drawing | 30 min | Hand-drawn state machine diagram |
| Exercise 2 | 2 | Schema Exploration | 30 min | SQL query results |
| Exercise 3 | 3 | SoT Cross-Reference | 30 min | Document mapping table |
| Exercise 4 | 4 | Trace API Request | 60 min | Flow diagram in notes |
| Exercise 5 | 4 | Run Existing Tests | 30 min | Test output review |
| Exercise 6 | 5 | Find SoT Violations | 60 min | Audit report |
| Exercise 7 | 5 | State Machine Exploration | 45 min | API test results |
| Exercise 8 | 5 | Ledger System Inspection | 45 min | SQL query results |
| Exercise 9 | 6 | State Machine Bug Hunt | 90 min | Code audit report |
| Exercise 10 | 7 | Schema Migration Practice | 60 min | Migration SQL script |
| Exercise 11 | 7 | Cross-Table Query Practice | 60 min | SQL queries |
| Exercise 12 | 8 | Simulate Billing Flow | 90 min | Test scenario documentation |
| Exercise 13 | 8 | Simulate REVERSAL | 60 min | REVERSAL test results |
| Exercise 14 | 8 | Test Prohibited Operations | 30 min | Error message documentation |
| Exercise 15 | 9 | Write First Unit Test | 60 min | Working unit test file |
| Exercise 16 | 9 | Write First Integration Test | 90 min | Working integration test |
| Exercise 17 | 11 | Implement Simple Endpoint | 180 min | Merged PR |
| Exercise 18 | 12 | Build Form Component | 180 min | React component + tests |
| **Total** | - | - | **~23 hours** | Portfolio of work |

---

## 9. Answer Keys

### 9.1 Week 1 Quiz Answers

```
Q1: STATE_MACHINE.md (裁判链 position 1, higher than API_SOT at position 5)
Q2: raw (conversions_raw, raw_spend), real (real_spend), final (conversions_final)
Q3: No (AUTH_SPEC.md - only 'data_operator' role can modify conversions_final)
Q4: conversions_final × projects.unit_price (LEDGER_SOT.md v1.2)
Q5: trend_ok or trend_flagged (STATE_MACHINE.md v2.7 §8)
Q6: REVERSAL with approval_ref (MASTER.md v4.4 INV-003)
Q7: DECIMAL(12,2) (BR-FIN-003 in BUSINESS_RULES.md v4.1)
Q8: Prohibited, should fail (INV-001 Immutable Audit Trail)
Q9: ERROR_CODES_SOT.md v2.1 (docs/sot/ERROR_CODES_SOT.md)
Q10: completed, rejected, or cancelled (STATE_MACHINE.md v2.7 §11)
```

### 9.2 Week 2 Quiz Answers

```
Q1: raw_submitted → trend_pending → trend_ok/trend_flagged → trend_resolved →
    final_pending → final_confirmed → final_locked
Q2: final_locked (terminal state, triggers billing per INV-001)
Q3: SUM(ledger_entries.amount) WHERE category = 'PROJECT' (LEDGER_SOT.md §4)
Q4: RECHARGE, REVENUE, COST, REVERSAL, TRANSFER (LEDGER_SOT.md §2)
Q5: No, prohibited by INV-001 (Immutable Audit Trail), only REVERSAL allowed
Q6: 60% Unit, 30% Integration, 10% E2E (TESTING_STRATEGY.md v1.0 §2)
Q7: create_reversal_entry() in services/ledger_service.py
Q8: category CHECK (category IN ('PROJECT', 'SUPPLIER')) in DATA_SCHEMA.md
Q9: UNIQUE (ad_account_id, report_date) on daily_reports table
Q10: 80% (MASTER.md v4.4 §7.2)
```

### 9.3 Final Assessment Answers (Day 15)

#### Section A: Architecture & SoT
```
1. MASTER.md v4.4 (裁判链 position 0)
2. Dual-Ledger, Triple-Stream, 8-State Machine, Immutable Audit Trail, Separation of Duties
3. final_locked
4. completed, rejected, cancelled (any terminal state acceptable)
5. ERROR_CODES_SOT.md v2.1
6. STATE_MACHINE.md v2.7
7. DATA_SCHEMA.md v5.3
8. Governance mechanism to prevent modifications during frozen periods
9. raw (raw data), real (real data), final (final data)
10. PROJECT (revenue), SUPPLIER (cost)
```

#### Section B: State Machines
```
11. raw_submitted → trend_pending → trend_ok → trend_resolved → final_pending →
    final_confirmed → final_locked (or include trend_flagged path)
12. No, must go through trend_resolved first (STATE_MACHINE.md prohibited transitions)
13. conversions_final > 0 OR real_spend > 0 (at least one must be positive)
14. Ledger entries created: REVENUE (if conversions_final > 0) and COST (if real_spend > 0)
15. No, final_locked is terminal, irreversible (only REVERSAL mechanism available)
```

#### Section C: Ledger System
```
16. SUM(ledger_entries.amount WHERE category = 'PROJECT')
17. RECHARGE, REVENUE, COST, REVERSAL, TRANSFER
18. No, violates INV-001 Immutable Audit Trail
19. Negative (deducts from PROJECT balance: -conversions_final × unit_price)
20. approval_ref (external approval reference, non-null, unique)
```

#### Section D: Business Rules
```
21. DECIMAL(12,2)
22. UNIQUE (ad_account_id, report_date)
23. No, only data_operator role can modify conversions_final (AUTH_SPEC.md)
24. finance role (AUTH_SPEC.md, MASTER.md INV-004)
25. conversions_final × projects.unit_price (LEDGER_SOT.md v1.2 INV-001)
```

#### Section E: Development Practices
```
26. 60% Unit, 30% Integration, 10% E2E (TESTING_STRATEGY.md v1.0)
27. 80% (MASTER.md v4.4 §7.2)
28. Result<T, E> pattern (API_DEVELOPMENT_FLOW.md)
29. Using 'any' type (must use strict typing)
30. <type>(<scope>): <subject> (e.g., "fix(validation): add date range check")
```

**Passing Score**: 27/30 (90%)

---

## 10. Onboarding Completion Checklist

**Developer Name**: ___________________________
**Start Date**: ___________________________
**Completion Date**: ___________________________
**Mentor**: ___________________________

### Week 1 Completion

- [ ] Development environment setup complete (Day 1)
- [ ] MASTER.md v4.4 read and understood (Day 1)
- [ ] Core SoT documents read (Day 2-3)
- [ ] Development workflows reviewed (Day 4)
- [ ] All Week 1 exercises completed (Day 5)
- [ ] Week 1 quiz passed (≥8/10)

**Mentor Signature**: ___________________________
**Date**: ___________________________

### Week 2 Completion

- [ ] State machine mastery demonstrated (Day 6-7)
- [ ] Ledger system understanding verified (Day 8)
- [ ] Testing strategy learned (Day 9)
- [ ] First bug fix merged (Day 10)
- [ ] All Week 2 exercises completed
- [ ] Week 2 quiz passed (≥9/10)

**Mentor Signature**: ___________________________
**Date**: ___________________________

### Week 3 Completion

- [ ] Full-stack development capability (Day 11-12)
- [ ] AI agent proficiency demonstrated (Day 13)
- [ ] Feature implementation completed (Day 14)
- [ ] Final assessment passed (≥27/30) (Day 15)
- [ ] Graduation task merged
- [ ] Code review presentation completed

**Mentor Signature**: ___________________________
**Date**: ___________________________

### Final Approval

- [ ] All quizzes passed
- [ ] At least 3 merged PRs
- [ ] Test coverage >80% on all contributions
- [ ] No SoT violations in code reviews
- [ ] Onboarding feedback submitted

**Tech Lead Approval**: ___________________________
**Date**: ___________________________

---

## 11. Continuous Learning (Post-Onboarding)

### 11.1 Ongoing Training

- **Monthly SoT Updates**: Review SoT document changes in team meetings
- **RFC Participation**: Attend RFC review sessions for new features
- **Code Review Rotation**: Participate in peer code reviews weekly
- **Tech Talks**: Attend or present monthly tech talks on advanced topics
- **Pair Programming**: Schedule weekly pair programming sessions

### 11.2 Advanced Topics (Self-Study)

- [ ] RLS_POLICIES_SOT.md v2.1 (Row-Level Security deep dive)
- [ ] RECONCILIATION_SOT.md (Advanced reconciliation workflows)
- [ ] TRANSFER_SOT.md (Dead account migration)
- [ ] Performance optimization patterns
- [ ] Advanced React Query patterns (optimistic updates, prefetching)
- [ ] Supabase Edge Functions deployment
- [ ] Database query optimization

### 11.3 Mentorship Opportunities

After 3 months on the team, consider:
- [ ] Mentoring new developers through onboarding
- [ ] Contributing to SoT documentation improvements
- [ ] Leading RFC reviews for your domain
- [ ] Presenting at team knowledge-sharing sessions

---

## 12. Document Metadata

**Version**: v1.0
**Status**: ready_for_production
**Layer**: dev-guide
**Owner**: wade
**Last Reviewed**: 2025-11-27
**Baseline**: MASTER.md v4.4, SoT Freeze v1.0

**Change History**:

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| v1.0 | 2025-11-27 | wade | Initial version, comprehensive 3-week onboarding program |

**Review Schedule**: Quarterly (or after major SoT updates)

**Feedback**: Submit onboarding feedback to #ai-ad-spend-onboarding or via onboarding survey

---

**End of Document**
