# AI 广告代投系统 - 文档中心

> **版本**: v5.0 (ASDD Freeze v1.0)
> **更新日期**: 2025-11-25
> **状态**: ASDD 7 核心文档体系已冻结

---

## 文档体系架构

本系统采用 **ASDD (AI Spec-Driven Development)** 文档驱动开发方法论。

### 快速导航

| 层级 | 目录 | 描述 | 状态 |
|------|------|------|------|
| **ASDD Core** | [1.overview/](#asdd-7-核心文档) | 7 大核心文档 | Frozen |
| **SoT** | [2.sot/](#sot-真相来源文档) | 11 个 SoT 规范文档 | Frozen |
| **Dev Guides** | [3.dev-guides/](#开发指南) | 开发规范与指南 | Active |
| **UI/UX** | [4.ui-ux/](#uiux-文档) | 设计系统 | Planning |
| **Ops** | [5.ops/](#运维文档) | 部署与运维 | Planning |

---

## ASDD 7 核心文档

> **路径**: `docs/1.overview/`
> **状态**: Frozen (ASDD_Freeze_v1.0)

### 文档清单

| 文档 | 版本 | 职责 | 状态 |
|------|------|------|------|
| [MASTER.md](1.overview/MASTER.md) | v3.4 | 系统架构宪法 (最高仲裁权) | Frozen |
| [PROJECT.md](1.overview/PROJECT.md) | v1.2 | 业务定义与边界声明 | Frozen |
| [ARCHITECTURE.md](1.overview/ARCHITECTURE.md) | v1.0 | 技术架构约束 | Frozen |
| [DOMAIN.md](1.overview/DOMAIN.md) | v1.0 | 领域索引导航 | Frozen |
| [PATTERNS.md](1.overview/PATTERNS.md) | v1.0 | 反模式清单 (37 个) | Frozen |
| [TESTING.md](1.overview/TESTING.md) | v1.0 | 测试规范 (13 必测项) | Frozen |
| [DEPLOYMENT.md](1.overview/DEPLOYMENT.md) | v1.0 | 部署规范 | Frozen |

### 文档引用关系

```
                    MASTER.md (v3.4)
                         |
          +--------------+--------------+
          |              |              |
     PROJECT.md    ARCHITECTURE.md  DOMAIN.md
       (v1.2)         (v1.0)        (v1.0)
          |              |              |
          |         PATTERNS.md    [SoT 文档]
          |           (v1.0)
          |              |
          +------+-------+
                 |
            TESTING.md
              (v1.0)
                 |
           DEPLOYMENT.md
              (v1.0)
```

### Freeze 保护规则

- 禁止直接修改 MASTER.md 不可变量
- 禁止修改状态枚举定义 (必须先更新 STATE_MACHINE.md)
- 任何修改需要 RFC 流程

---

## SoT 真相来源文档

> **路径**: `docs/2.sot/`
> **状态**: Frozen (SoT Freeze v1.0)

### SoT 裁判链 (优先级从高到低)

```
1. STATE_MACHINE.md v2.6   - 状态定义与转换
2. DATA_SCHEMA.md v5.2     - 表结构与字段
3. BUSINESS_RULES.md v3.1  - 业务规则
4. API_SOT.md v2.2         - API 定义
5. ERROR_CODES_SOT.md v2.1 - 错误码
6. AUTH_SPEC.md v2.0       - 认证授权
7. LEDGER_SOT.md v1.1      - 账本规则
8. DAILY_REPORT_SOT.md v1.0
9. RECONCILIATION_SOT.md v1.0
10. TRANSFER_SOT.md v1.0
11. RLS_POLICIES_SOT.md v1.0
```

### 核心 SoT 文档

| 文档 | 版本 | 职责 |
|------|------|------|
| [STATE_MACHINE.md](2.sot/STATE_MACHINE.md) | v2.6 | 8 状态机定义 (raw_submitted → final_locked) |
| [DATA_SCHEMA.md](2.sot/DATA_SCHEMA.md) | v5.2 | 27+ 业务表结构 |
| [BUSINESS_RULES.md](2.sot/BUSINESS_RULES.md) | v3.1 | BR-* 业务规则编码 |
| [API_SOT.md](2.sot/API_SOT.md) | v2.2 | REST API 规范 |
| [ERROR_CODES_SOT.md](2.sot/ERROR_CODES_SOT.md) | v2.1 | 59 个错误码 |
| [AUTH_SPEC.md](2.sot/AUTH_SPEC.md) | v2.0 | 5 大角色 RBAC |
| [LEDGER_SOT.md](2.sot/LEDGER_SOT.md) | v1.1 | 双账本 (PROJECT/SUPPLIER) |
| [DAILY_REPORT_SOT.md](2.sot/DAILY_REPORT_SOT.md) | v1.0 | 日报模块规则 |
| [RECONCILIATION_SOT.md](2.sot/RECONCILIATION_SOT.md) | v1.0 | 对账模块规则 |
| [TRANSFER_SOT.md](2.sot/TRANSFER_SOT.md) | v1.0 | 划拨模块规则 |
| [RLS_POLICIES_SOT.md](2.sot/RLS_POLICIES_SOT.md) | v1.0 | RLS 策略规范 |

---

## 开发指南

> **路径**: `docs/3.dev-guides/`
> **状态**: Active

| 文档 | 职责 |
|------|------|
| [API_DEVELOPMENT_FLOW.md](3.dev-guides/API_DEVELOPMENT_FLOW.md) | API 开发生命周期 |
| [API_RULEBOOK.md](3.dev-guides/API_RULEBOOK.md) | API 开发规则手册 |
| [BACKEND_SETUP.md](3.dev-guides/BACKEND_SETUP.md) | 后端环境搭建 |
| [BACKEND_DEV_GUIDE.md](3.dev-guides/BACKEND_DEV_GUIDE.md) | 后端开发指南 |
| [FRONTEND_SETUP.md](3.dev-guides/FRONTEND_SETUP.md) | 前端环境搭建 |
| [FRONTEND_RULES.md](3.dev-guides/FRONTEND_RULES.md) | 前端开发规范 |
| [TESTING_GUIDE.md](3.dev-guides/TESTING_GUIDE.md) | 测试指南 |
| [DEVELOPMENT_STANDARDS.md](3.dev-guides/DEVELOPMENT_STANDARDS.md) | 开发标准 |
| [DDD_API_ARCHITECTURE.md](3.dev-guides/DDD_API_ARCHITECTURE.md) | DDD API 架构 |

---

## UI/UX 文档

> **路径**: `docs/4.ui-ux/`
> **状态**: Planning

- 设计系统规范 (待创建)
- UI 组件库 (待创建)
- 用户体验指南 (待创建)

---

## 运维文档

> **路径**: `docs/5.ops/`
> **状态**: Planning

- 部署指南 (待创建)
- 监控与告警 (待创建)
- 备份与恢复 (待创建)

---

## 归档文档

> **路径**: `docs/archive/`
> **状态**: Deprecated

### ASDD 迁移归档

以下旧文档已被 ASDD 7 核心文档取代：

| 旧文档 | 取代文档 | 归档位置 |
|-------|---------|---------|
| MASTER_SPEC.md v1.1 | MASTER.md v3.4 | 1.overview/ (标记废弃) |
| SYSTEM_OVERVIEW.md | DOMAIN.md v1.0 | 1.overview/ (标记废弃) |
| PROJECT_RULES.md v3.0 | PATTERNS.md v1.0 | 1.overview/ (标记废弃) |
| SOT_FREEZE.md | ASDD_FREEZE_v1.0.md | 1.overview/ (标记废弃) |

### 历史文档分类

```
docs/archive/
├── asdd_migration/      # ASDD 迁移说明
├── core_archive/        # 旧核心文档 (MASTER_SPEC v1.x, v2.x)
├── old_core/            # 旧 SoT 文档
├── old_dev/             # 旧开发指南
├── old_modules/         # 旧模块文档
├── old_migrations/      # 旧迁移文档
└── [其他历史版本]
```

---

## 核心设计原则速查

### 三数据流

```
raw (投手提交) → real (真实消耗) → final (最终粉数计费)
```

- `conversions_final` 是计费唯一来源
- `real_spend + fee` 是成本唯一来源
- 禁止使用 raw 数据计费

### 双账本

```
PROJECT Ledger (项目收入)     SUPPLIER Ledger (供应商成本)
    ├─ 客户充值                   ├─ 财务充值
    ├─ 粉数计费收入 (REVENUE)     ├─ 真实消耗成本 (COST)
    ├─ 红冲修正 (REVERSAL)        ├─ 死号迁移 (TRANSFER)
    └─ 项目余额                   └─ 供应商余额
```

### 8 状态机 (日报)

```
raw_submitted → trend_pending → trend_ok/trend_flagged
             → trend_resolved → final_pending
             → final_confirmed → final_locked
```

### 5 大角色

- admin, finance, data_operator, account_manager, media_buyer

---

## 文档优先级与冲突仲裁

当文档冲突时，按以下优先级仲裁：

1. **MASTER.md** - 架构宪法 (最高)
2. **STATE_MACHINE.md** - 状态定义
3. **DATA_SCHEMA.md** - 数据结构
4. **BUSINESS_RULES.md** - 业务规则
5. **API_SOT.md** - API 规范
6. **其他 SoT 文档**
7. **开发指南**

---

## 变更记录

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v5.0 | 2025-11-25 | ASDD 7 核心文档体系完成，索引更新 |
| v4.0 | 2025-11-22 | 5 层架构重构 |
| v3.0 | 2024-11-18 | 旧文档结构 |

---

**文档版本**: v5.0
**最后更新**: 2025-11-25
**基准**: ASDD_Freeze_v1.0 + SoT_Freeze_v1.0
