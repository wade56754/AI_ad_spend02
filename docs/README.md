---
version: v2.1
status: ready_for_production
layer: documentation-index
owner: wade
last_reviewed: 2026-01-16
baseline: MASTER.md v4.9, PRD v5.1
---

# AI广告代投系统 - Documentation Center

> **Documentation Framework**: ASDD (AI-Spec-Driven Development) 5-Layer Architecture
> **Last Updated**: 2026-01-16
> **Baseline**: MASTER v4.9, PRD v5.1

---

## 📐 ASDD 5-Layer Architecture

```
docs/
├── sot/                    # Layer 1: SoT 真相源 (核心文档)
├── guides/                 # Layer 2: 开发与协作指南
├── design/                 # Layer 3: 设计与规范
├── architecture/           # 架构视图
├── integration/            # Layer 4: 集成/修复记录
├── analysis/               # Layer 5: 分析报告
├── review/                 # 评审与缺陷报告
├── adr/                    # 架构决策记录
├── runbooks/               # 运维手册
└── archive/                # 归档
```

**Legend**:
- 🟢 **Frozen**: Production-ready, versioned, locked
- 🟡 **Active**: In use, can be updated
- 🔴 **Draft**: Under development

---

## 🎯 Quick Navigation

### Layer 1: SoT 真相源 (9 Core Documents) 🟢

**Purpose**: Single source of truth for all technical specifications

| Document | Version | Purpose |
|----------|---------|---------|
| [MASTER.md](./sot/MASTER.md) | v4.9 | 系统宪法，三大不可变量 |
| [INDEX.md](./sot/INDEX.md) | v1.0 | SoT 文档索引 |
| [STATE_MACHINE.md](./sot/STATE_MACHINE.md) | v2.9 | 8-state machine flow |
| [DATA_SCHEMA.md](./sot/DATA_SCHEMA.md) | v5.11 | Database schema, 23 tables |
| [API_SOT.md](./sot/API_SOT.md) | v9.7 | REST API contracts, 50+ endpoints |
| [ERROR_CODES_SOT.md](./sot/ERROR_CODES_SOT.md) | v2.2 | Global error code registry |
| [BUSINESS_RULES.md](./sot/BUSINESS_RULES.md) | v5.2 | Business logic rules |
| [AUTH_SPEC.md](./sot/AUTH_SPEC.md) | v2.2 | 6 user roles, RBAC permissions |

---

### Layer 2: Guides 开发与协作指南 🟢

| Document | Purpose |
|----------|---------|
| [FRONTEND_DEVELOPMENT_GUIDE_v3.0.md](./guides/FRONTEND_DEVELOPMENT_GUIDE_v3.0.md) | 前端开发规范 |
| [AI_PROGRAMMING_BEST_PRACTICES_v3.1.md](./guides/AI_PROGRAMMING_BEST_PRACTICES_v3.1.md) | AI 编程规范 |
| [AI_CODING_BEST_PRACTICES.md](./guides/AI_CODING_BEST_PRACTICES.md) | 代码生产规范 |
| [TASK_COMPLEXITY.md](./guides/TASK_COMPLEXITY.md) | 任务复杂度量化 |

---

### Layer 3: Design 设计与规范 🟢

| Document | Purpose |
|----------|---------|
| [FRONTEND_PAGE_DESIGN_v2.1.md](./design/FRONTEND_PAGE_DESIGN_v2.1.md) | 前端页面设计规范 |

---

### Architecture 架构视图 🟢

| Document | Purpose |
|----------|---------|
| [ARCHITECTURE_OVERVIEW_v1.0.md](./architecture/ARCHITECTURE_OVERVIEW_v1.0.md) | 系统上下文、组件、数据流、部署形态 |

---

### Layer 4: Integration 集成与修复记录 🟢

| Document | Purpose |
|----------|---------|
| [INTEGRATION_SUMMARY.md](./integration/INTEGRATION_SUMMARY.md) | 集成总结 |
| [BUG_FIXES_SUMMARY.md](./integration/BUG_FIXES_SUMMARY.md) | 修复摘要 |

---

### Layer 5: Analysis & Review 🟢

| Document | Purpose |
|----------|---------|
| [SKILLS_AUDIT_REPORT.md](./analysis/SKILLS_AUDIT_REPORT.md) | 技能审计报告 |
| [PROJECT_DEFECTS_REPORT.md](./review/PROJECT_DEFECTS_REPORT.md) | 项目缺陷报告 |

---

### ADR / Runbooks / Archive

| Document | Purpose |
|----------|---------|
| [adr/](./adr/) | 架构决策记录 |
| [runbooks/](./runbooks/) | 运维手册 |
| [archive/](./archive/) | 归档文档 |

---

## 🔗 SoT Referee Chain (裁判链)

When technical conflicts arise, follow this priority order:

```
MASTER.md v4.9 (System Constitution)
  ↓
SoT Layer (Technical Truth)
  ├── STATE_MACHINE.md v2.9 (State transitions)
  ├── DATA_SCHEMA.md v5.11 (Database schema)
  ├── API_SOT.md v9.7 (API contracts)
  ├── ERROR_CODES_SOT.md v2.2 (Error codes)
  ├── BUSINESS_RULES.md v5.2 (Business logic)
  └── AUTH_SPEC.md v2.2 (Authentication)
  ↓
Guides Layer (Workflows)
  ├── FRONTEND_DEVELOPMENT_GUIDE_v3.0.md
  ├── AI_PROGRAMMING_BEST_PRACTICES_v3.1.md
  └── AI_CODING_BEST_PRACTICES.md
  ↓
Design/Integration/Runbooks
  ├── design/
  ├── integration/
  └── runbooks/
```

**Rule**: Higher layers override lower layers. When in doubt, consult MASTER.md first.

---

## 📖 Document Usage Guidelines

### For New Team Members

**Start here** (in order):
1. Read [MASTER.md](./sot/MASTER.md) - Understand system philosophy and invariants
2. Read [PRD_v5.1.md](./PRD_v5.1.md) - Understand product goals and scope
3. Read [FRONTEND_DEVELOPMENT_GUIDE_v3.0.md](./guides/FRONTEND_DEVELOPMENT_GUIDE_v3.0.md) - Frontend workflow
4. Read [AI_PROGRAMMING_BEST_PRACTICES_v3.1.md](./guides/AI_PROGRAMMING_BEST_PRACTICES_v3.1.md) - AI coding norms
5. Browse [SoT Layer](./sot/) - Reference technical specifications as needed

### For AI Agents (Claude, Cursor, etc.)

**Mandatory reading before code generation**:
1. Consult SoT Layer documents for technical truth
2. Follow Dev-Guides for workflows
3. Reference Architecture Layer for design decisions

**Rule**: Never generate code that conflicts with SoT documents.

---

## 🔍 Quick Search

### By Role

- **老板 (CEO)**: [PRD_v5.1.md](./PRD_v5.1.md) → goals & scope
- **项目负责人**: [BUSINESS_RULES.md](./sot/BUSINESS_RULES.md) → pricing & profit rules
- **财务**: [DATA_SCHEMA.md](./sot/DATA_SCHEMA.md) → ledger & reconciliation fields
- **投手**: [STATE_MACHINE.md](./sot/STATE_MACHINE.md) → daily report flow
- **户管**: [STATE_MACHINE.md](./sot/STATE_MACHINE.md) → topup & transfer flows
- **管理员**: [AUTH_SPEC.md](./sot/AUTH_SPEC.md) → roles & permissions

### By Technical Topic

- **Database**: [DATA_SCHEMA.md](./sot/DATA_SCHEMA.md) v5.11
- **API**: [API_SOT.md](./sot/API_SOT.md) v9.7
- **State Machine**: [STATE_MACHINE.md](./sot/STATE_MACHINE.md) v2.9
- **Error Handling**: [ERROR_CODES_SOT.md](./sot/ERROR_CODES_SOT.md) v2.2
- **Auth**: [AUTH_SPEC.md](./sot/AUTH_SPEC.md) v2.2

---

## 📂 Archive

Archived documents are stored in `archive/` with date prefixes:

| Archive | Contents |
|---------|----------|
| `2025-12-structure-cleanup/` | Infrastructure, Agent, Appendix, Code-blocks layers |
| `2025-12-structure-cleanup/sot-extended/` | Extended SoT (TOPUP, TRANSFER, RECONCILIATION, etc.) |
| `2025-12-doc-cleanup/` | Previous cleanup |
| `2.sot-legacy/` | Legacy SoT versions |

---

## 📞 Contact & Support

**Documentation Owner**: Wade

**Questions?**
1. Check [TROUBLESHOOTING.md](./2.dev-guides/TROUBLESHOOTING.md) for common issues
2. Consult SoT Layer for technical specifications

---

**Last Updated**: 2025-12-27 | **ASDD Framework Version**: 5-Layer ✅
