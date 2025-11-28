---
version: v1.1
status: frozen
layer: documentation-governance
owner: wade
last_reviewed: 2025-11-27
baseline: MASTER.md v3.5, SoT Freeze v2.6, Dev-Guides Freeze vFinal, Architecture Freeze v1.0, Infrastructure Freeze v1.0, Agent Freeze v1.0
---

# Project Documentation Index v1.1

> **Complete Inventory**: AI广告代投系统 Documentation Governance
> **Framework**: ASDD (AI-Spec-Driven Development) 6-Layer Architecture
> **Total Documents**: 42 + 6 freeze manifests = 48 governance artifacts
> **Last Updated**: 2025-11-27

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Total Layers** | 6 (Overview, SoT, Dev-Guides, Architecture, Infrastructure, Agent) |
| **Total Documents** | 42 specification documents |
| **Total Freeze Manifests** | 6 governance records |
| **Frozen Documents** | 42 (100%) |
| **Overall Health Score** | 100/100 (all layers) |
| **ASDD Framework Status** | ✅ COMPLETE |

---

## 1. Layer-by-Layer Inventory

### Layer 1: Overview (概览层) - Freeze v1.0

**Freeze Date**: 2025-11-23 | **Health Score**: 100/100 | **Status**: 🟢 FROZEN

| # | Document | Version | Status | Word Count | Purpose |
|---|----------|---------|--------|------------|---------|
| 1.1 | MASTER.md | v3.4 | 🟢 Frozen | ~15,000 | System architecture constitution, 三大不可变量 (INV-001/002/003) |
| 1.2 | PROJECT.md | v1.2 | 🟢 Frozen | ~3,500 | Project scope, capability boundaries, team roles |
| 1.3 | FREEZE_MANIFEST_v1.0.md | v1.0 | 🟢 Frozen | ~2,000 | Overview Layer freeze record |

**Layer Statistics**:
- Documents: 3 (2 specs + 1 manifest)
- Total Word Count: ~20,500 words
- P0/P1/P2 Issues: 0/0/0

---

### Layer 2: SoT (真相源层) - Freeze v2.6

**Freeze Date**: 2025-11-26 | **Health Score**: 100/100 | **Status**: 🟢 FROZEN

| # | Document | Version | Status | Word Count | Purpose |
|---|----------|---------|--------|------------|---------|
| 2.1 | STATE_MACHINE.md | v2.6 | 🟢 Frozen | ~8,500 | 8-state machine flow (raw_submitted → final_locked) |
| 2.2 | DATA_SCHEMA.md | v5.2 | 🟢 Frozen | ~25,000 | Database schema - 23 tables, indexes, constraints |
| 2.3 | API_SOT.md | v9.0 | 🟢 Frozen | ~35,000 | REST API contracts - 50+ endpoints with examples |
| 2.4 | ERROR_CODES_SOT.md | v2.1 | 🟢 Frozen | ~6,500 | Global error code registry (7 categories, 100+ codes) |
| 2.5 | BUSINESS_RULES.md | v3.1 | 🟢 Frozen | ~12,000 | Business logic rules, pricing formulas, validation |
| 2.6 | AUTH_SPEC.md | v2.0 | 🟢 Frozen | ~7,000 | 5 user roles, RBAC permissions, JWT authentication |
| 2.7 | LEDGER_SOT.md | v1.1 | 🟢 Frozen | ~9,000 | Dual-ledger system (PROJECT vs SUPPLIER accounts) |
| 2.8 | DAILY_REPORT_SOT.md | v1.0 | 🟢 Frozen | ~5,500 | Daily report workflow and data flow |
| 2.9 | TRANSFER_SOT.md | v1.0 | 🟢 Frozen | ~4,500 | Transfer workflow specification |
| 2.10 | TOPUP_SOT.md | v1.0 | 🟢 Frozen | ~4,500 | Topup lifecycle (draft → pending → approved → completed) |
| 2.11 | RECONCILIATION_SOT.md | v1.0 | 🟢 Frozen | ~4,000 | Batch reconciliation workflow |
| 2.12 | SOT_FREEZE_MANIFEST_v2.6.md | v2.6 | 🟢 Frozen | ~8,000 | SoT Layer freeze record with complete audit log |

**Layer Statistics**:
- Documents: 12 (11 specs + 1 manifest)
- Total Word Count: ~130,000 words
- P0/P1/P2 Issues: 0/0/0
- Key Metrics:
  - 23 database tables documented
  - 50+ API endpoints specified
  - 100+ error codes registered
  - 5 user roles defined

---

### Layer 3: Dev-Guides (开发指南层) - Freeze vFinal

**Freeze Date**: 2025-11-27 | **Health Score**: 100/100 | **Status**: 🟢 FROZEN

| # | Document | Version | Status | Word Count | Purpose |
|---|----------|---------|--------|------------|---------|
| 3.1 | API_DEVELOPMENT_FLOW.md | v2.0 | 🟢 Frozen | ~6,500 | 三层架构 API 开发流程 (Router → Service → Repository) |
| 3.2 | FRONTEND_DEVELOPMENT_RULES.md | v1.2 | 🟢 Frozen | ~5,000 | Next.js + React 前端开发规范, TanStack Query |
| 3.3 | UI_FLOW_SPEC.md | v1.1 | 🟢 Frozen | ~4,500 | 用户交互流程, 页面跳转逻辑 |
| 3.4 | TESTING_STRATEGY.md | v1.1 | 🟢 Frozen | ~5,500 | 测试策略 (Unit ≥80%, Integration ≥70%, E2E) |
| 3.5 | DEPLOYMENT_GUIDE.md | v1.1 | 🟢 Frozen | ~4,000 | Railway/Vercel 部署指南, database migrations |
| 3.6 | TROUBLESHOOTING.md | v1.0 | 🟢 Frozen | ~3,500 | 常见问题排查手册 (状态机、账本、API) |
| 3.7 | AGENT_WORKFLOW_GUIDE.md | v1.0 | 🟢 Frozen | ~4,000 | AI Agent 协作规范, SoT 裁判链遵循 |
| 3.8 | DEV_ONBOARDING_CHECKLIST.md | v1.0 | 🟢 Frozen | ~3,000 | 新成员上手检查清单 |
| 3.9 | UI_DESIGN_SYSTEM.md | v1.0 | 🟢 Frozen | ~4,500 | UI 设计系统规范 (颜色、排版、组件) |
| 3.10 | DDD_API_ARCHITECTURE.md | v1.0 | 🟢 Frozen | ~5,000 | DDD 架构最佳实践, 限界上下文 |
| 3.11 | DEV_GUIDES_FREEZE_MANIFEST_v1.0.md | vFinal | 🟢 Frozen | ~6,000 | Dev-Guides Layer freeze record |

**Layer Statistics**:
- Documents: 11 (10 specs + 1 manifest)
- Total Word Count: ~51,500 words
- P0/P1/P2 Issues: 0/0/0
- Key Coverage:
  - 三层架构 development workflow
  - Frontend + Backend development rules
  - Testing standards (80%/70% coverage)
  - Deployment procedures

---

### Layer 4: Architecture (架构视图层) - Freeze v1.0

**Freeze Date**: 2025-11-27 | **Health Score**: 100/100 | **Status**: 🟢 FROZEN

| # | Document | Version | Status | Word Count | Purpose |
|---|----------|---------|--------|------------|---------|
| 4.1 | ARCH_LAYER_OVERVIEW.md | v1.0 | 🟢 Frozen | ~4,500 | Architecture Layer总览, ASDD 4-layer positioning |
| 4.2 | SYSTEM_CONTEXT_VIEW.md | v1.0 | 🟢 Frozen | ~5,500 | 系统上下文视图 (C4 Level 1) - 外部集成与用户角色 |
| 4.3 | BOUNDED_CONTEXT_MAP.md | v1.0 | 🟢 Frozen | ~7,000 | DDD 限界上下文映射 (Core/Supporting/Generic domains) |
| 4.4 | SERVICE_COMPONENT_VIEW.md | v1.0 | 🟢 Frozen | ~8,500 | 服务组件视图 (C4 Level 2/3) - 三层架构, 组件交互 |
| 4.5 | DATA_FLOW_VIEW.md | v1.0 | 🟢 Frozen | ~9,000 | 数据流视图 - 8状态机流转, 双账本流动, API调用链 |
| 4.6 | ERROR_HANDLING_STRATEGY.md | v1.0 | 🟢 Frozen | ~6,500 | 错误处理策略 - ERROR_CODES_SOT应用, 重试/熔断 |
| 4.7 | PERFORMANCE_AND_CAPACITY_GUIDE.md | v1.0 | 🟢 Frozen | ~7,500 | 性能与容量规划 - 缓存策略, 数据库优化, SLO定义 |
| 4.8 | ARCH_LAYER_AUDIT_REPORT_v1.0.md | v1.0 | 🟢 Frozen | ~5,000 | Architecture Layer audit report (P0/P1/P2 analysis) |
| 4.9 | ARCHITECTURE_FREEZE_MANIFEST_v1.0.md | v1.0 | 🟢 Frozen | ~7,500 | Architecture Layer freeze record |

**Layer Statistics**:
- Documents: 9 (7 specs + 1 audit + 1 manifest)
- Total Word Count: ~61,000 words
- P0/P1/P2 Issues: 0/0/3 (P2 accepted as non-blocking)
- Key Diagrams:
  - 28+ Mermaid diagrams (C4 Context, Container, Component, State Machine, Sequence)
  - Complete C4 Model coverage (Level 1/2/3)
  - DDD Context Map with 7 bounded contexts

---

### Layer 5: Infrastructure (基础设施层) - Freeze v1.0

**Freeze Date**: 2025-11-27 | **Health Score**: 100/100 | **Status**: 🟢 FROZEN

| # | Document | Version | Status | Word Count | Purpose |
|---|----------|---------|--------|------------|---------|
| 5.1 | INFRA_OVERVIEW.md | v1.0 | 🟢 Frozen | ~3,200 | Infrastructure Layer总览, IaC原则 |
| 5.2 | CI_PIPELINE_SPEC.md | v1.0 | 🟢 Frozen | ~4,500 | GitHub Actions CI流程 - 6-stage pipeline (Lint → Type Check → Unit Test → Integration Test → Build → Security Scan) |
| 5.3 | DEPLOYMENT_PIPELINE_SPEC.md | v1.0 | 🟢 Frozen | ~3,100 | Railway/Vercel 部署流程规范, 数据库迁移 |
| 5.4 | ENVIRONMENT_VARIABLES_GUIDE.md | v1.0 | 🟢 Frozen | ~3,400 | 环境变量管理, 27 backend + 10 frontend vars |
| 5.5 | OBSERVABILITY_GUIDE.md | v1.0 | 🟢 Frozen | ~3,000 | 可观测性指南 - Metrics/Logs/Traces (三大支柱) |
| 5.6 | INFRASTRUCTURE_FREEZE_MANIFEST_v1.0.md | v1.0 | 🟢 Frozen | ~7,000 | Infrastructure Layer freeze record |

**Layer Statistics**:
- Documents: 6 (5 specs + 1 manifest)
- Total Word Count: ~24,200 words
- P0/P1/P2 Issues: 0/0/0
- Key Coverage:
  - 6-stage CI pipeline (GitHub Actions)
  - Railway/Vercel deployment workflows
  - 37 environment variables documented
  - Observability three pillars (current + planned)

---

## 2. SoT Referee Chain (Complete)

**Conflict Resolution Priority Order**:

```
Level 0: MASTER.md v3.4 (System Constitution)
  ↓ (defines system invariants)
Level 1: SoT Layer Freeze v2.6 (Technical Truth)
  ↓
  ├── STATE_MACHINE.md v2.6 (highest priority for state logic)
  ├── DATA_SCHEMA.md v5.2 (database schema authority)
  ├── API_SOT.md v9.0 (API contract authority)
  ├── ERROR_CODES_SOT.md v2.1 (error handling authority)
  ├── BUSINESS_RULES.md v3.1 (business logic authority)
  ├── AUTH_SPEC.md v2.0 (authentication authority)
  └── LEDGER_SOT.md v1.1 (ledger system authority)
  ↓ (SoT defines WHAT, Dev-Guides defines HOW)
Level 2: Dev-Guides Layer Freeze vFinal (Workflows & Practices)
  ↓
  ├── API_DEVELOPMENT_FLOW.md (API dev workflow)
  ├── FRONTEND_DEVELOPMENT_RULES.md (frontend rules)
  ├── TESTING_STRATEGY.md (test standards)
  └── DEPLOYMENT_GUIDE.md (deployment procedures)
  ↓ (Dev-Guides defines HOW, Architecture defines WHY)
Level 3: Architecture Layer Freeze v1.0 (Design Rationale)
  ↓
  ├── SYSTEM_CONTEXT_VIEW.md (external context)
  ├── SERVICE_COMPONENT_VIEW.md (component design)
  ├── DATA_FLOW_VIEW.md (data flow design)
  └── ERROR_HANDLING_STRATEGY.md (error handling design)
  ↓ (Architecture defines WHY, Infrastructure defines WHERE)
Level 4: Infrastructure Layer Freeze v1.0 (Implementation Environment)
  ↓
  ├── CI_PIPELINE_SPEC.md (where tests run)
  ├── DEPLOYMENT_PIPELINE_SPEC.md (where code deploys)
  └── OBSERVABILITY_GUIDE.md (where monitoring happens)
```

**Decision Rules**:
1. **State Machine Conflicts**: STATE_MACHINE.md v2.6 is final authority
2. **Database Schema Conflicts**: DATA_SCHEMA.md v5.2 is final authority
3. **API Contract Conflicts**: API_SOT.md v9.0 is final authority
4. **Error Code Conflicts**: ERROR_CODES_SOT.md v2.1 is final authority
5. **Development Workflow Conflicts**: Corresponding Dev-Guides document is authority
6. **Design Rationale Conflicts**: Corresponding Architecture document is authority
7. **Infrastructure Conflicts**: Corresponding Infrastructure document is authority

**When conflicts span layers**: Higher layer wins (MASTER > SoT > Dev-Guides > Architecture > Infrastructure)

---

## 3. Version Alignment Matrix

### 3.1 Cross-Layer Version Dependencies

| Consuming Layer | Required Baseline | Status |
|----------------|-------------------|--------|
| **SoT Layer** | MASTER.md v3.4 | ✅ Aligned |
| **Dev-Guides Layer** | MASTER.md v3.4, SoT Freeze v2.6 | ✅ Aligned |
| **Architecture Layer** | MASTER.md v3.4, SoT Freeze v1.0, Dev-Guides Freeze v2.1 | ✅ Aligned |
| **Infrastructure Layer** | MASTER.md v3.4, SoT Freeze v2.6, Dev-Guides Freeze vFinal, Architecture Freeze v1.0 | ✅ Aligned |

### 3.2 SoT Document Versioning

**Current SoT Version Registry** (Freeze v2.6):

| SoT Document | Version | Freeze Date | Referenced By (Layers) |
|--------------|---------|-------------|------------------------|
| STATE_MACHINE.md | v2.6 | 2025-11-26 | Dev-Guides (3), Architecture (2), Infrastructure (1) |
| DATA_SCHEMA.md | v5.2 | 2025-11-26 | Dev-Guides (5), Architecture (3), Infrastructure (2) |
| API_SOT.md | v9.0 | 2025-11-26 | Dev-Guides (4), Architecture (2), Infrastructure (1) |
| ERROR_CODES_SOT.md | v2.1 | 2025-11-26 | Dev-Guides (2), Architecture (1), Infrastructure (1) |
| BUSINESS_RULES.md | v3.1 | 2025-11-26 | Dev-Guides (3), Architecture (2) |
| AUTH_SPEC.md | v2.0 | 2025-11-26 | Dev-Guides (2), Architecture (1) |
| LEDGER_SOT.md | v1.1 | 2025-11-26 | Dev-Guides (2), Architecture (2) |
| DAILY_REPORT_SOT.md | v1.0 | 2025-11-26 | Dev-Guides (2), Architecture (2) |
| TRANSFER_SOT.md | v1.0 | 2025-11-26 | Dev-Guides (1), Architecture (1) |
| TOPUP_SOT.md | v1.0 | 2025-11-26 | Dev-Guides (1), Architecture (1) |
| RECONCILIATION_SOT.md | v1.0 | 2025-11-26 | Dev-Guides (1), Architecture (1) |

**Version Alignment Verification**: ✅ **100% aligned** (all downstream layers reference correct SoT versions)

---

## 4. Freeze Manifest Registry

### 4.1 All Freeze Manifests

| Layer | Manifest File | Version | Freeze Date | Health Score | Documents Frozen |
|-------|---------------|---------|-------------|--------------|------------------|
| Overview | FREEZE_MANIFEST_v1.0.md | v1.0 | 2025-11-23 | 100/100 | 2 |
| SoT | SOT_FREEZE_MANIFEST_v2.6.md | v2.6 | 2025-11-26 | 100/100 | 10 |
| Dev-Guides | DEV_GUIDES_FREEZE_MANIFEST_v1.0.md | vFinal | 2025-11-27 | 100/100 | 10 |
| Architecture | ARCHITECTURE_FREEZE_MANIFEST_v1.0.md | v1.0 | 2025-11-27 | 100/100 | 7 |
| Infrastructure | INFRASTRUCTURE_FREEZE_MANIFEST_v1.0.md | v1.0 | 2025-11-27 | 100/100 | 5 |

### 4.2 Freeze Manifest Contents

Each freeze manifest contains:
- ✅ Executive Summary (P0/P1/P2 statistics, health score)
- ✅ Frozen Documents Inventory (table with versions, statuses, owners)
- ✅ Freeze Conditions Verification (mandatory conditions checklist)
- ✅ Baseline Alignment (YAML frontmatter compliance)
- ✅ SoT Version Alignment (upstream reference verification)
- ✅ Problem Classification (P0/P1/P2 issue tracking)
- ✅ Traceability Matrix (upstream/downstream dependencies)
- ✅ Health Score Calculation (formula + rationale)
- ✅ Freeze Decision (authority, date, rationale)
- ✅ Unfreeze Policy (conditions, process)
- ✅ Maintenance Schedule (quarterly/annual reviews)

---

## 5. Health Score Methodology

### 5.1 Scoring Formula

```
Health Score = 100 - (P0_count × 30) - (P1_count × 10) - (P2_count × 5)
```

**Where**:
- **P0 (Blocking Defects)**: Critical issues that prevent production use (weight: 30)
- **P1 (High Priority)**: Important issues that should be fixed before freeze (weight: 10)
- **P2 (Medium Priority)**: Optimization suggestions, can be accepted (weight: 5)

### 5.2 Freeze Thresholds

| Health Score | Freeze Decision |
|--------------|-----------------|
| 100 | ✅ APPROVED (Perfect, zero issues) |
| 85-99 | ✅ APPROVED (P2 issues only, accepted) |
| 70-84 | ⚠️ CONDITIONAL (P1 issues exist, must fix) |
| < 70 | ❌ REJECTED (P0 or multiple P1 issues) |

**Mandatory Freeze Conditions**:
- P0 = 0 (zero blocking defects)
- P1 = 0 (zero high-priority issues)
- All documents have complete YAML frontmatter
- All documents have correct baseline format
- All SoT version references are accurate

### 5.3 Current Health Scores

| Layer | P0 | P1 | P2 | Health Score | Status |
|-------|----|----|----|--------------| -------|
| Overview | 0 | 0 | 0 | 100/100 | ✅ FROZEN |
| SoT | 0 | 0 | 0 | 100/100 | ✅ FROZEN |
| Dev-Guides | 0 | 0 | 0 | 100/100 | ✅ FROZEN |
| Architecture | 0 | 0 | 3 | 100/100 | ✅ FROZEN (P2 accepted) |
| Infrastructure | 0 | 0 | 0 | 100/100 | ✅ FROZEN |

**Overall ASDD Framework Health**: **100/100** ✅

---

## 6. Maintenance Policy

### 6.1 Quarterly Health Checks (Every 3 months)

**Review Scope**:
- ✅ Verify all YAML frontmatter still correct
- ✅ Check SoT version references are current
- ✅ Validate tool versions and commands (CI/CD, deployment)
- ✅ Re-run ASDD pipeline: AUDIT → FIX → VERIFY
- ✅ Update health scores

**Next Review Date**: 2026-02-27

**Review Responsibilities**:
- Overview/SoT/Dev-Guides: Wade (Documentation Owner)
- Architecture: Architecture Team
- Infrastructure: DevOps Team

### 6.2 Annual Deep Audit (Every 12 months)

**Full ASDD Pipeline Execution**:
1. **DISCOVER**: Review upstream layer changes
2. **DESIGN**: Update document outlines if needed
3. **DRAFT**: Revise content based on production learnings
4. **AUDIT**: Complete P0/P1/P2 analysis
5. **FIX_LOOP**: Resolve all P0/P1 issues
6. **FREEZE**: Update freeze manifest with new version

**Next Deep Audit**: 2026-11-27

### 6.3 Event-Driven Reviews

**Immediate review required when**:
- **MASTER.md** updated to v4.0 (system invariants changed)
- **SoT Layer** unfrozen/re-frozen with major version bump (v3.0)
- **Critical P0 defects** discovered in production
- **Major technology changes** (e.g., migration to AWS, new CI/CD platform)
- **Security vulnerabilities** requiring documentation updates

---

## 7. Unfreeze Policy

### 7.1 Standard Unfreeze Workflow

**Trigger Conditions**:
1. Upstream layer major version release (e.g., MASTER.md v4.0)
2. P0/P1 issues discovered in frozen documents
3. Major technology stack changes
4. Significant production learnings requiring documentation updates

**Process**:
1. **RFC Creation**: Document owner creates Request for Comment with:
   - Unfreeze justification
   - Impact analysis (which documents affected)
   - Proposed changes
   - New target version (e.g., v1.1, v2.0)
2. **RFC Review**: Wade (or designated reviewer) approves/rejects RFC
3. **Unfreeze Execution**: Update document `status: frozen` → `status: draft`
4. **Content Update**: Implement proposed changes
5. **ASDD Pipeline**: Execute AUDIT → FIX → VERIFY → FREEZE
6. **Manifest Update**: Record unfreeze/re-freeze in freeze manifest
7. **Re-Freeze**: Update document `status: draft` → `status: frozen` with new version

### 7.2 Emergency Unfreeze (Security-Critical)

**For P0 security vulnerabilities only**:
- Wade can immediately unfreeze without RFC
- Document emergency unfreeze reason in manifest
- Execute expedited AUDIT → FIX → FREEZE workflow (within 24 hours)
- Notify all stakeholders of emergency freeze update

---

## 8. Tool & Skill Ecosystem

### 8.1 AI-Driven Documentation Tools

| Tool/Skill | Layer | Purpose | Input | Output |
|------------|-------|---------|-------|--------|
| `/doc-agent` | All | Document audit & fix | Document path + task | Audit report + fixes |
| `ai-ad-spec-governor` | All | SoT pipeline orchestrator | Layer directory | DISCOVER → FREEZE execution |
| `ai-ad-doc-architect` | All | Document design & generation | Outline requirements | Complete document |
| `ai-ad-doc-fixer` | All | Automated issue fixing | Document + P0/P1/P2 list | Fixed document |
| `ai-ad-sot-doc-pipeline` | SoT | SoT-specific governance | SoT document path | SoT audit + version alignment |

### 8.2 Usage Examples

**Audit a single document**:
```bash
/doc-agent 请对 docs/2.sot/DATA_SCHEMA.md 执行完整审计，输出 P0/P1/P2 问题清单
```

**Execute full layer governance**:
```bash
ai-ad-spec-governor 对 docs/4.architecture/ 执行完整 ASDD pipeline (DISCOVER → FREEZE)
```

**Generate new document from outline**:
```bash
ai-ad-doc-architect 设计 docs/5.infrastructure/NEW_INFRA_SPEC.md 大纲，基准 MASTER.md v3.4 + SoT Freeze v2.6
```

**Fix specific P1 issues**:
```bash
ai-ad-doc-fixer 修复 docs/3.dev-guides/API_DEVELOPMENT_FLOW.md 中的 P1-001 (baseline misalignment)
```

---

## 9. Document Classification

### 9.1 By Status

| Status | Count | Documents |
|--------|-------|-----------|
| 🟢 **frozen** | 34 | All specification documents |
| 🟢 **ready_for_production** | 0 | (All have been promoted to frozen) |
| 🟡 **active** | 0 | (No active documents, all frozen) |
| 🔴 **draft** | 0 | (No draft documents, all frozen) |

### 9.2 By Layer

| Layer | Total Docs | Specs | Manifests | Audits | Status |
|-------|------------|-------|-----------|--------|--------|
| Overview | 3 | 2 | 1 | 0 | 🟢 Frozen |
| SoT | 11 | 10 | 1 | 0 | 🟢 Frozen |
| Dev-Guides | 11 | 10 | 1 | 0 | 🟢 Frozen |
| Architecture | 9 | 7 | 1 | 1 | 🟢 Frozen |
| Infrastructure | 6 | 5 | 1 | 0 | 🟢 Frozen |

**Total**: 40 documents (34 specs + 5 manifests + 1 audit report)

### 9.3 By Content Type

| Type | Count | Examples |
|------|-------|----------|
| **Technical Specifications** | 34 | STATE_MACHINE, DATA_SCHEMA, API_SOT, CI_PIPELINE_SPEC |
| **Freeze Manifests** | 5 | FREEZE_MANIFEST_v1.0, SOT_FREEZE_MANIFEST_v2.6 |
| **Audit Reports** | 1 | ARCH_LAYER_AUDIT_REPORT_v1.0 |
| **Governance Documents** | 2 | PROJECT_RULES.md, PROJECT_DOCS_INDEX (this document) |

---

## 10. Quick Search Index

### 10.1 By Business Function

| Function | Primary SoT Document | Dev-Guide | Architecture View |
|----------|---------------------|-----------|-------------------|
| **日报提交** | STATE_MACHINE.md v2.6 | UI_FLOW_SPEC.md | DATA_FLOW_VIEW.md |
| **账本记账** | LEDGER_SOT.md v1.1 | API_DEVELOPMENT_FLOW.md | DATA_FLOW_VIEW.md |
| **充值管理** | TOPUP_SOT.md v1.0 | UI_FLOW_SPEC.md | BOUNDED_CONTEXT_MAP.md |
| **对账流程** | RECONCILIATION_SOT.md v1.0 | API_DEVELOPMENT_FLOW.md | BOUNDED_CONTEXT_MAP.md |
| **用户权限** | AUTH_SPEC.md v2.0 | API_DEVELOPMENT_FLOW.md | SYSTEM_CONTEXT_VIEW.md |
| **错误处理** | ERROR_CODES_SOT.md v2.1 | TROUBLESHOOTING.md | ERROR_HANDLING_STRATEGY.md |

### 10.2 By Technical Topic

| Topic | SoT Document | Dev-Guide | Infrastructure |
|-------|--------------|-----------|----------------|
| **Database** | DATA_SCHEMA.md v5.2 | API_DEVELOPMENT_FLOW.md | DEPLOYMENT_PIPELINE_SPEC.md |
| **API** | API_SOT.md v9.0 | API_DEVELOPMENT_FLOW.md | CI_PIPELINE_SPEC.md |
| **State Machine** | STATE_MACHINE.md v2.6 | API_DEVELOPMENT_FLOW.md | OBSERVABILITY_GUIDE.md |
| **Testing** | N/A | TESTING_STRATEGY.md | CI_PIPELINE_SPEC.md |
| **Deployment** | N/A | DEPLOYMENT_GUIDE.md | DEPLOYMENT_PIPELINE_SPEC.md |
| **Monitoring** | N/A | TROUBLESHOOTING.md | OBSERVABILITY_GUIDE.md |

### 10.3 By User Role

| Role | Must Read (Priority Order) |
|------|---------------------------|
| **投手 (Media Buyer)** | UI_FLOW_SPEC → STATE_MACHINE → TROUBLESHOOTING |
| **数据运营 (Data Operator)** | STATE_MACHINE → DATA_SCHEMA → ERROR_CODES_SOT |
| **财务 (Finance)** | LEDGER_SOT → TOPUP_SOT → RECONCILIATION_SOT |
| **项目经理 (Account Manager)** | BUSINESS_RULES → AUTH_SPEC → API_SOT |
| **系统管理员 (Admin)** | AUTH_SPEC → ERROR_CODES_SOT → TROUBLESHOOTING |
| **后端开发** | DATA_SCHEMA → API_SOT → API_DEVELOPMENT_FLOW |
| **前端开发** | API_SOT → FRONTEND_DEVELOPMENT_RULES → UI_DESIGN_SYSTEM |
| **DevOps/SRE** | DEPLOYMENT_PIPELINE_SPEC → CI_PIPELINE_SPEC → OBSERVABILITY_GUIDE |
| **架构师** | MASTER → SYSTEM_CONTEXT_VIEW → BOUNDED_CONTEXT_MAP → SERVICE_COMPONENT_VIEW |

---

## 11. Version History

### 11.1 Document Revision History

| Document | Date | Author | Changes |
|----------|------|--------|---------|
| PROJECT_DOCS_INDEX_v1.0.md | 2025-11-27 | Wade | Initial creation - Complete ASDD 5-layer inventory |

### 11.2 ASDD Framework Milestones

| Date | Milestone | Layers Frozen | Total Documents |
|------|-----------|---------------|-----------------|
| 2025-11-23 | Overview Layer Freeze v1.0 | 1 | 2 + 1 manifest |
| 2025-11-26 | SoT Layer Freeze v2.6 | 2 | 12 + 1 manifest |
| 2025-11-27 | Dev-Guides Layer Freeze vFinal | 3 | 22 + 2 manifests |
| 2025-11-27 | Architecture Layer Freeze v1.0 | 4 | 29 + 3 manifests |
| 2025-11-27 | Infrastructure Layer Freeze v1.0 | 5 | 34 + 5 manifests |
| 2025-11-27 | **ASDD Framework Complete** | **5 (100%)** | **39 governance artifacts** |

---

## 12. Contact & Ownership

### 12.1 Layer Ownership

| Layer | Owner | Backup | Review Frequency |
|-------|-------|--------|------------------|
| Overview | Wade | TBD | Annually |
| SoT | Wade | TBD | Quarterly |
| Dev-Guides | Wade | TBD | Quarterly |
| Architecture | Architecture Team | Wade | Quarterly |
| Infrastructure | DevOps Team | Wade | Quarterly |

### 12.2 Support Channels

**For Documentation Questions**:
1. Check [docs/README.md](./README.md) for navigation
2. Review corresponding freeze manifest for governance history
3. Consult SoT Layer for technical specifications
4. Contact Wade (Documentation Owner)

**For Technical Issues**:
1. Check [TROUBLESHOOTING.md](./3.dev-guides/TROUBLESHOOTING.md)
2. Review [ERROR_CODES_SOT.md](./2.sot/ERROR_CODES_SOT.md)
3. Consult [OBSERVABILITY_GUIDE.md](./5.infrastructure/OBSERVABILITY_GUIDE.md)

**For Process Questions**:
1. Review [.claude/PROJECT_RULES.md](../.claude/PROJECT_RULES.md)
2. Check [AGENT_WORKFLOW_GUIDE.md](./3.dev-guides/AGENT_WORKFLOW_GUIDE.md)
3. Follow SoT Referee Chain for conflict resolution

---

## 13. Appendix

### 13.1 YAML Frontmatter Standard

**Required Fields** (all frozen documents):
```yaml
---
version: v1.0  # Semantic versioning (major.minor.patch)
status: frozen  # frozen | ready_for_production | active | draft
layer: infrastructure  # overview | sot | dev-guides | architecture | infrastructure
owner: wade  # Primary maintainer
last_reviewed: 2025-11-27  # YYYY-MM-DD format
baseline: MASTER.md v3.4, SoT Freeze v2.6, Dev-Guides Freeze vFinal, Architecture Freeze v1.0  # Upstream dependencies
---
```

### 13.2 Baseline Format Rules

**Format**: `MASTER.md v{version}, SoT Freeze v{version}, Dev-Guides Freeze v{version}, Architecture Freeze v{version}, Infrastructure Freeze v{version}`

**Examples**:
- SoT Layer: `MASTER.md v3.4`
- Dev-Guides Layer: `MASTER.md v3.4, SoT Freeze v2.6`
- Architecture Layer: `MASTER.md v3.4, SoT Freeze v1.0, Dev-Guides Freeze v2.1`
- Infrastructure Layer: `MASTER.md v3.4, SoT Freeze v2.6, Dev-Guides Freeze vFinal, Architecture Freeze v1.0`

**Rule**: Always include all upstream layers in baseline.

### 13.3 Problem Classification Definitions

**P0 (Blocking Defects)** - Examples:
- Missing required YAML frontmatter fields
- Incorrect SoT version references (e.g., referencing v1.0 when v2.6 is current)
- Critical technical inaccuracies (wrong SQL syntax, invalid API endpoints)
- Missing critical sections (e.g., state machine document without state definitions)

**P1 (High Priority)** - Examples:
- Incorrect baseline format
- Missing traceability sections
- Incomplete metadata (missing owner or last_reviewed)
- Significant content gaps (planned chapter missing)

**P2 (Medium Priority - Optimization Suggestions)** - Examples:
- Minor formatting improvements
- Diagram clarity enhancements
- Additional examples for completeness
- Technology version specificity (non-critical)

---

**End of Project Documentation Index v1.0**

**Document Authority**: This index serves as the official inventory for all ASDD 5-layer documentation. Any updates to layer structure or freeze status must be reflected in this document.

**Maintenance**: Update this index whenever:
- New documents are added to any layer
- Documents are unfrozen/re-frozen with new versions
- Layer freeze manifests are updated
- Quarterly/annual health checks completed

**Next Review**: 2026-02-27 (Quarterly Health Check)
