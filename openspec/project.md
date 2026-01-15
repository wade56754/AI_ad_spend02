# Project Context

## Purpose

AI 广告代投系统 (AI Ad Spend System) - 管理广告代投业务的三方资金流转：

- **客户** → 充值至项目账户 → 按粉数计费扣款
- **平台** → 管理项目账本（收入侧）与供应商账本（成本侧）
- **供应商** → 接收充值 → 按真实消耗扣款

**核心目标**：
- 双账本架构防止资金混乱
- 8 状态机强制流转确保审计链完整
- 三数据流分离（Raw/Real/Final）防止数据篡改
- 终态不可变保证审计不可逆

## Tech Stack

### Backend
- **Runtime**: Python 3.11+
- **Framework**: FastAPI (async)
- **ORM**: SQLAlchemy 2.x (async)
- **Database**: PostgreSQL 15+ (Supabase hosted)
- **Validation**: Pydantic v2
- **Authentication**: JWT + Supabase Auth
- **Testing**: pytest 8.x

### Frontend
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript 5.x
- **UI Components**: shadcn/ui + Tailwind CSS
- **State Management**: Zustand / React Query
- **Testing**: Jest + React Testing Library

### Infrastructure
- **Backend Hosting**: Railway
- **Frontend Hosting**: Vercel
- **Database**: Supabase (PostgreSQL)
- **CI/CD**: GitHub Actions (6-stage pipeline)
- **Monitoring**: Structured logging + Supabase observability

### AI Agent System
- **Framework**: Claude Code + Custom Skills
- **Protocol**: AgentProtocol (TypedDict)
- **Orchestration**: 4-mode patterns (Sequential/Parallel/Conditional/Loop)

## Project Conventions

### Code Style

**Python (Backend)**:
- Black formatter (line-length=88)
- isort imports (profile=black)
- Type hints required for all public functions
- Docstrings follow Google style

**TypeScript (Frontend)**:
- ESLint + Prettier
- Strict TypeScript mode
- React functional components only
- Named exports preferred

**Naming Conventions**:
- Files: `snake_case.py` (Python), `kebab-case.tsx` (React)
- Classes: `PascalCase`
- Functions/Variables: `snake_case` (Python), `camelCase` (TypeScript)
- Constants: `UPPER_SNAKE_CASE`
- Database tables: `snake_case` (plural)

### Architecture Patterns

**Backend (Three-Layer Architecture)**:
```
Router Layer (api/)
    ↓ Request validation, auth
Service Layer (services/)
    ↓ Business logic, orchestration
Repository Layer (repositories/)
    ↓ Database operations
```

**State Machine Pattern**:
- All entities with lifecycle use explicit state machines
- State transitions defined in `STATE_MACHINE.md`
- Transitions enforced via `StateHelper` classes

**Dual-Ledger Pattern**:
- PROJECT ledger: Revenue tracking (client billing)
- SUPPLIER ledger: Cost tracking (supplier payments)
- Never mix ledger categories

### Testing Strategy

**Test Levels (Pyramid)**:
| Level | Type | Location | Coverage Target |
|-------|------|----------|-----------------|
| L0 | Unit | `tests/unit/` | ≥80% |
| L1 | Integration | `tests/integration/` | ≥70% |
| L2 | API | `tests/api/` | ≥60% |
| L3 | E2E | `tests/e2e/` | Key flows |

**Test Naming**: `test_<condition>__<expected_result>`

**Markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.api`, `@pytest.mark.e2e`

### Git Workflow

**Branch Strategy**:
- `master`: Production-ready code
- `develop`: Integration branch
- `feature/<name>`: New features
- `fix/<name>`: Bug fixes
- `sot-fix-*`: SoT alignment fixes

**Commit Convention**:
```
<type>(<scope>): <subject>

Types: feat, fix, docs, style, refactor, test, chore
Scope: backend, frontend, docs, agents, infra
```

**PR Requirements**:
- Must pass CI (lint, type-check, tests)
- Must not conflict with frozen SoT documents
- Requires review for `docs/sot/` changes

## Domain Context

### Business Entities

| Entity | Purpose | State Machine |
|--------|---------|---------------|
| **DailyReport** | Daily ad performance data | 8-state (raw_submitted → final_locked) |
| **TopupRequest** | Client recharge requests | 7-state (draft → completed/rejected) |
| **Transfer** | Internal fund transfers | 5-state (draft → completed/failed) |
| **Project** | Client project accounts | Balance via PROJECT ledger |
| **Supplier** | Ad supplier accounts | Balance via SUPPLIER ledger |

### User Roles (5 Roles - AUTH_SPEC.md v2.0)

| Role | Key Permissions |
|------|-----------------|
| **admin** | Full system access |
| **finance** | Ledger operations, REVERSAL, topup approval |
| **data_operator** | Daily report real/final input, trend resolution |
| **account_manager** | Project management, client relations |
| **media_buyer** | Raw data submission only |

### Data Flow Rules (INV-002)

```
Raw Data (media_buyer)
    ↓ Trend risk control
Real Data (data_operator)
    ↓ Cost calculation
Final Data (data_operator)
    ↓ Revenue calculation
final_locked (TERMINAL - immutable)
```

**Critical Constraints**:
- Raw data NEVER used for billing
- Final data required for billing
- Real data required for cost calculation
- Terminal state is irreversible

## Important Constraints

### System Invariants (from MASTER.md v3.5)

**INV-001: Dual-Ledger Independence**
- PROJECT ledger: Only RECHARGE, REVENUE, TRANSFER, REVERSAL
- SUPPLIER ledger: Only RECHARGE, COST, TRANSFER, REVERSAL
- Cross-category operations FORBIDDEN

**INV-002: Triple-Stream Separation**
- Raw → Trend control only
- Real → Cost calculation only
- Final → Revenue calculation only
- Reverse derivation FORBIDDEN

**INV-003: 8-State Machine Enforcement**
- All transitions via whitelist
- Terminal state protection (final_locked)
- No direct database updates bypassing state machine

**INV-004: Audit Immutability**
- `ledger_entries` table: INSERT-only, no UPDATE/DELETE
- Corrections via REVERSAL entries only
- Balance = SUM(all entries)

### Regulatory Constraints

- Financial audit trail required
- Data retention: 7 years minimum
- Role-based access control mandatory
- All state transitions logged

### Performance SLOs

| Metric | Target |
|--------|--------|
| API P95 latency | < 500ms |
| API P99 latency | < 1000ms |
| Availability | 99.9% |
| Error rate | < 0.1% |

## External Dependencies

### Supabase (Database + Auth)
- PostgreSQL 15 hosted database
- Row-Level Security (RLS) policies
- Real-time subscriptions
- Built-in authentication

### Railway (Backend Hosting)
- Docker-based deployment
- Auto-scaling
- Environment variable management
- Health checks

### Vercel (Frontend Hosting)
- Next.js optimized deployment
- Edge functions
- Preview deployments
- CDN distribution

### GitHub Actions (CI/CD)
- 6-stage pipeline: Checkout → Setup → Lint → Type → Test → Deploy
- Parallel job execution
- Environment-specific deployments

## Documentation Framework

### ASDD 6-Layer Architecture

```
Layer 1: Overview     → MASTER.md, PROJECT.md (Freeze v1.0)
Layer 2: SoT          → 10 SoT documents (Freeze v2.6)
Layer 3: Dev-Guides   → 10 development guides (Freeze vFinal)
Layer 4: Architecture → 7 architecture views (Freeze v1.0)
Layer 5: Infrastructure → 5 infrastructure specs (Freeze v1.0)
Layer 6: Agent        → 7 agent specifications (Freeze v1.0)
```

### SoT Referee Chain (Priority Order)

When conflicts arise, follow this hierarchy:
1. MASTER.md v4.9 (System Constitution)
2. STATE_MACHINE.md v2.9 (State definitions)
3. DATA_SCHEMA.md v5.11 (Database schema + ledger rules §3.4.4)
4. API_SOT.md v9.7 (API contracts)
5. ERROR_CODES_SOT.md v2.2 (Error codes)
6. BUSINESS_RULES.md v5.2 (Business logic)
7. AUTH_SPEC.md v2.2 (Permissions)

### Key SoT Documents

| Document | Version | Purpose |
|----------|---------|---------|
| `docs/sot/STATE_MACHINE.md` | v2.9 | 8-state machine definitions |
| `docs/sot/DATA_SCHEMA.md` | v5.11 | 23 database tables + ledger rules §3.4.4 |
| `docs/sot/API_SOT.md` | v9.7 | 50+ REST API endpoints |
| `docs/sot/ERROR_CODES_SOT.md` | v2.2 | Error code registry |

## OpenSpec Integration Notes

### When to Create Proposals

**Requires proposal**:
- New API endpoints
- State machine modifications
- Database schema changes
- New business rules
- Breaking changes to existing specs

**Skip proposal for**:
- Bug fixes restoring spec behavior
- Documentation typos
- Dependency updates (non-breaking)
- Test additions for existing behavior

### Mapping to ASDD

| OpenSpec Concept | ASDD Equivalent |
|------------------|-----------------|
| `specs/` | `docs/sot/` (SoT Layer) |
| `proposal.md` | RFC in `docs/1.overview/` |
| `design.md` | Architecture views in `docs/4.architecture/` |
| `tasks.md` | Dev-Guides implementation checklists |

### Freeze Alignment

Before creating OpenSpec changes that affect frozen documents:
1. Check freeze status in layer's `FREEZE_MANIFEST_*.md`
2. Follow unfreeze procedures if modification required
3. Ensure version alignment in proposal references
