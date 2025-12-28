---
version: v2.0
status: ready_for_production
layer: documentation-index
owner: wade
last_reviewed: 2025-12-27
baseline: MASTER.md v4.4, SoT Core v2.6
---

# AI广告代投系统 - Documentation Center

> **Documentation Framework**: ASDD (AI-Spec-Driven Development) 5-Layer Architecture
> **Last Updated**: 2025-12-27
> **Baseline**: MASTER v4.4, SoT Core v2.6

---

## 📐 ASDD 5-Layer Architecture

```
docs/
├── sot/                    # Layer 1: SoT 真相源 (9 核心文档)
├── 1.overview/             # Layer 2: 项目概览
├── 2.dev-guides/           # Layer 3: 开发指南
├── 3.architecture/         # Layer 4: 架构视图
├── 4.testing/              # Layer 5: 测试文档
├── 5.module-specs/         # 模块规格 (按需扩展)
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
| [MASTER.md](./sot/MASTER.md) | v4.4 | 系统宪法，三大不可变量 |
| [INDEX.md](./sot/INDEX.md) | v1.0 | SoT 文档索引 |
| [STATE_MACHINE.md](./sot/STATE_MACHINE.md) | v2.7 | 8-state machine flow |
| [DATA_SCHEMA.md](./sot/DATA_SCHEMA.md) | v5.3 | Database schema, 23 tables |
| [API_SOT.md](./sot/API_SOT.md) | v9.3 | REST API contracts, 50+ endpoints |
| [ERROR_CODES_SOT.md](./sot/ERROR_CODES_SOT.md) | v2.1 | Global error code registry |
| [BUSINESS_RULES.md](./sot/BUSINESS_RULES.md) | v4.1 | Business logic rules |
| [AUTH_SPEC.md](./sot/AUTH_SPEC.md) | v2.0 | 7 user roles, RBAC permissions |
| [LEDGER_SOT.md](./sot/LEDGER_SOT.md) | v1.2 | Dual-ledger system |

---

### Layer 2: Overview 项目概览 🟢

| Document | Purpose |
|----------|---------|
| [PROJECT.md](./1.overview/PROJECT.md) | Project scope, capability boundaries |
| [DOMAIN.md](./1.overview/DOMAIN.md) | Domain model and business context |
| [ARCHITECTURE.md](./1.overview/ARCHITECTURE.md) | High-level architecture overview |

---

### Layer 3: Dev-Guides 开发指南 🟢

| Document | Purpose |
|----------|---------|
| [API_DEVELOPMENT_FLOW.md](./2.dev-guides/API_DEVELOPMENT_FLOW.md) | 三层架构 API 开发流程 |
| [FRONTEND_DEVELOPMENT_RULES.md](./2.dev-guides/FRONTEND_DEVELOPMENT_RULES.md) | Next.js + React 前端开发规范 |
| [UI_FLOW_SPEC.md](./2.dev-guides/UI_FLOW_SPEC.md) | 用户交互流程规范 |
| [TESTING_STRATEGY.md](./2.dev-guides/TESTING_STRATEGY.md) | 测试策略 |
| [DEPLOYMENT_GUIDE.md](./2.dev-guides/DEPLOYMENT_GUIDE.md) | 部署指南 |
| [DEV_ONBOARDING_CHECKLIST.md](./2.dev-guides/DEV_ONBOARDING_CHECKLIST.md) | 新成员上手检查清单 |
| [DDD_API_ARCHITECTURE.md](./2.dev-guides/DDD_API_ARCHITECTURE.md) | DDD 架构最佳实践 |

---

### Layer 4: Architecture 架构视图 🟢

| Document | Purpose |
|----------|---------|
| [ARCH_LAYER_OVERVIEW.md](./3.architecture/ARCH_LAYER_OVERVIEW.md) | Architecture Layer 总览 |
| [SYSTEM_CONTEXT_VIEW.md](./3.architecture/SYSTEM_CONTEXT_VIEW.md) | 系统上下文视图 (C4 Level 1) |
| [BOUNDED_CONTEXT_MAP.md](./3.architecture/BOUNDED_CONTEXT_MAP.md) | DDD 限界上下文映射 |
| [SERVICE_COMPONENT_VIEW.md](./3.architecture/SERVICE_COMPONENT_VIEW.md) | 服务组件视图 (C4 Level 2/3) |
| [DATA_FLOW_VIEW.md](./3.architecture/DATA_FLOW_VIEW.md) | 数据流视图 |
| [ERROR_HANDLING_STRATEGY.md](./3.architecture/ERROR_HANDLING_STRATEGY.md) | 错误处理策略 |

---

### Layer 5: Testing 测试文档 🟢

| Document | Purpose |
|----------|---------|
| [AUTOMATION_TEST_SPEC_v1.5.1.md](./4.testing/AUTOMATION_TEST_SPEC_v1.5.1.md) | API 自动化测试规范 |
| [BACKEND_TEST_FREEZE_REPORT_v1.4.md](./4.testing/BACKEND_TEST_FREEZE_REPORT_v1.4.md) | 后端测试冻结报告 |

---

### Module Specs 模块规格

| Document | Purpose |
|----------|---------|
| [5.module-specs/](./5.module-specs/) | 模块规格目录 (A1-E3) |
| [README.md](./5.module-specs/README.md) | 模块规格索引 |

---

## 🔗 SoT Referee Chain (裁判链)

When technical conflicts arise, follow this priority order:

```
MASTER.md v4.4 (System Constitution)
  ↓
SoT Layer (Technical Truth)
  ├── STATE_MACHINE.md v2.7 (State transitions)
  ├── DATA_SCHEMA.md v5.3 (Database schema)
  ├── API_SOT.md v9.3 (API contracts)
  ├── ERROR_CODES_SOT.md v2.1 (Error codes)
  ├── BUSINESS_RULES.md v4.1 (Business logic)
  ├── AUTH_SPEC.md v2.0 (Authentication)
  └── LEDGER_SOT.md v1.2 (Ledger system)
  ↓
Dev-Guides Layer (Workflows)
  ├── API_DEVELOPMENT_FLOW.md
  ├── FRONTEND_DEVELOPMENT_RULES.md
  └── TESTING_STRATEGY.md
  ↓
Architecture Layer (Design Views)
  ├── SYSTEM_CONTEXT_VIEW.md
  ├── SERVICE_COMPONENT_VIEW.md
  └── DATA_FLOW_VIEW.md
```

**Rule**: Higher layers override lower layers. When in doubt, consult MASTER.md first.

---

## 📖 Document Usage Guidelines

### For New Team Members

**Start here** (in order):
1. Read [MASTER.md](./sot/MASTER.md) - Understand system philosophy and invariants
2. Read [PROJECT.md](./1.overview/PROJECT.md) - Understand project scope
3. Read [DEV_ONBOARDING_CHECKLIST.md](./2.dev-guides/DEV_ONBOARDING_CHECKLIST.md) - Follow onboarding steps
4. Read [API_DEVELOPMENT_FLOW.md](./2.dev-guides/API_DEVELOPMENT_FLOW.md) - Learn development workflow
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

- **投手 (Media Buyer)**: [UI_FLOW_SPEC.md](./2.dev-guides/UI_FLOW_SPEC.md) → daily report submission
- **数据运营 (Data Operator)**: [STATE_MACHINE.md](./sot/STATE_MACHINE.md) → 8-state machine flow
- **财务 (Finance)**: [LEDGER_SOT.md](./sot/LEDGER_SOT.md) → dual-ledger system
- **项目经理 (Account Manager)**: [BUSINESS_RULES.md](./sot/BUSINESS_RULES.md) → pricing rules
- **系统管理员 (Admin)**: [AUTH_SPEC.md](./sot/AUTH_SPEC.md) → user roles & permissions

### By Technical Topic

- **Database**: [DATA_SCHEMA.md](./sot/DATA_SCHEMA.md) v5.3
- **API**: [API_SOT.md](./sot/API_SOT.md) v9.3
- **State Machine**: [STATE_MACHINE.md](./sot/STATE_MACHINE.md) v2.7
- **Error Handling**: [ERROR_CODES_SOT.md](./sot/ERROR_CODES_SOT.md) v2.1
- **Testing**: [TESTING_STRATEGY.md](./2.dev-guides/TESTING_STRATEGY.md)

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
