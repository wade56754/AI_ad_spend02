# AI广告代投系统 - 文档中心

> 版本: v4.0
> 更新日期: 2025-11-22
> 状态: 文档体系重构完成

## 📚 文档体系架构

本文档中心采用**5层分级架构**，为AI广告代投系统提供完整的技术文档、SoT规范和开发指南。

### 🎯 快速导航

| 层级 | 目录 | 描述 | 目标读者 |
|------|------|------|----------|
| **Tier 1** | [1.overview/](#tier-1-系统全局视图) | 系统架构图、职责划分、根规范 | 所有人员 |
| **Tier 2** | [2.sot/](#tier-2-真相来源文档) | 所有SoT文档（API/数据/状态/业务规则） | 开发人员、架构师 |
| **Tier 3** | [3.dev-guides/](#tier-3-开发指南) | 开发规范、环境搭建、测试指南 | 开发人员 |
| **Tier 4** | [4.ui-ux/](#tier-4-ui--ux-文档) | 设计系统、组件库、体验指南 | 设计师、前端开发 |
| **Tier 5** | [5.ops/](#tier-5-运维文档) | 部署、监控、备份恢复 | 运维工程师、DevOps |

---

## 📂 文档结构

```
docs/
├── README.md                    # 文档中心索引（本文件）
│
├── 1.overview/                  # Tier 1: 系统全局视图
│   ├── MASTER_SPEC.md          # 系统根规范（最高优先级SoT）
│   ├── SYSTEM_OVERVIEW.md      # 系统架构图 + 职责划分 + 模块边界
│   └── PROJECT_RULES.md        # 项目开发规则（Cursor/Claude 依赖）
│
├── 2.sot/                       # Tier 2: 真相来源文档（Source of Truth）
│   ├── API_SOT.md              # API接口规范（路由/请求/响应）
│   ├── AUTH_SPEC.md            # 认证授权规范（角色/权限/JWT）
│   ├── BUSINESS_RULES.md       # 业务规则（BR-*系列编码规则）
│   ├── DAILY_REPORT_SOT.md     # 日报模块SoT
│   ├── DATA_SCHEMA.md          # 数据库架构（表结构/字段/约束）
│   ├── ERROR_CODES_SOT.md      # 错误码规范（分类/编码/处理）
│   ├── LEDGER_SOT.md           # 账本系统SoT（双账本/流水/红冲）
│   ├── RECONCILIATION_SOT.md   # 对账模块SoT
│   ├── RLS_POLICIES_SOT.md     # RLS策略规范（Supabase行级安全）
│   ├── STATE_MACHINE.md        # 状态机设计（8大状态机/转换规则）
│   └── TRANSFER_SOT.md         # 划拨模块SoT
│
├── 3.dev-guides/                # Tier 3: 开发指南
│   ├── API_DEVELOPMENT_FLOW.md # API开发生命周期SOP
│   ├── API_RULEBOOK.md         # API开发规则手册
│   ├── BACKEND_SETUP.md        # 后端环境搭建
│   ├── DEVELOPMENT_STANDARDS.md # 开发标准与规范
│   ├── FRONTEND_RULES.md       # 前端开发规则
│   ├── FRONTEND_SETUP.md       # 前端环境搭建
│   └── TESTING_GUIDE.md        # 测试指南
│
├── 4.ui-ux/                     # Tier 4: UI/UX 文档
│   └── README.md               # 待创建：设计系统、组件库、体验指南
│
├── 5.ops/                       # Tier 5: 运维文档
│   └── README.md               # 待创建：部署、监控、备份恢复
│
├── archive/                     # 历史文档归档
│   ├── core_archive/           # 旧核心文档
│   ├── AI_AD_SYSTEM_MASTER_SPEC_v2.2.md
│   ├── BRD_chapter1_v3.1.md
│   ├── FRONTEND_SPEC_v2.md
│   └── ...                     # 其他历史版本
│
├── api/                         # 模块API文档（参考）
├── modules/                     # 业务模块文档（参考）
│   ├── daily_reports/
│   ├── projects/
│   ├── reconciliations/
│   └── topups/
│
└── [其他目录...]               # 开发中的文档目录

```

---

## Tier 1: 系统全局视图

**定位**: 提供系统的顶层架构、设计哲学和开发规则，是所有人员的入口文档。

### 📋 文档列表

1. **[MASTER_SPEC.md](./1.overview/MASTER_SPEC.md)** - 系统根规范
   - 系统定位与架构设计哲学
   - 核心设计原则（三数据流/双账本/SOD/终态保护）
   - 模块边界与SoT文档体系
   - 全局开发约束与冲突仲裁规则
   - **优先级**: 最高（P0）

2. **[SYSTEM_OVERVIEW.md](./1.overview/SYSTEM_OVERVIEW.md)** - 系统概览
   - 业务背景与系统架构图
   - 模块职责划分
   - 技术选型说明

3. **[PROJECT_RULES.md](./1.overview/PROJECT_RULES.md)** - 项目开发规则
   - Cursor/Claude 开发依赖规范
   - 项目总规范清单

### 🎯 适用人群
- 所有项目成员（必读）
- 新加入团队成员（入门）
- 产品经理、架构师、开发人员

---

## Tier 2: 真相来源文档

**定位**: 所有技术决策和实现的唯一真相来源（Single Source of Truth），开发时必须遵循。

### 📝 SoT 文档清单

#### 核心 SoT (P1)
- **[DATA_SCHEMA.md](./2.sot/DATA_SCHEMA.md)** - 数据库架构设计
  - 25+ 业务表结构定义
  - 主键策略：UUID vs BIGSERIAL
  - 外键约束与索引优化
  - 触发器与审计字段

- **[STATE_MACHINE.md](./2.sot/STATE_MACHINE.md)** - 状态机设计
  - 8大状态机定义
  - 状态转换规则与权限矩阵
  - 终态保护机制

- **[BUSINESS_RULES.md](./2.sot/BUSINESS_RULES.md)** - 业务规则
  - BR-AUTH-* 认证规则
  - BR-USER-* 用户规则
  - BR-FIN-* 财务规则
  - BR-RPT-* 日报规则
  - BR-DATA-* 数据规则
  - SOD（职责分离）规则

#### 接口与认证 SoT (P1)
- **[API_SOT.md](./2.sot/API_SOT.md)** - API接口规范
  - 所有路由定义（8大模块）
  - 请求/响应格式
  - 分页/排序/过滤规范

- **[AUTH_SPEC.md](./2.sot/AUTH_SPEC.md)** - 认证授权规范
  - 5大角色定义（admin/finance/data_operator/account_manager/media_buyer）
  - 权限矩阵与RBAC实现
  - JWT Token生命周期
  - Session管理

- **[ERROR_CODES_SOT.md](./2.sot/ERROR_CODES_SOT.md)** - 错误码规范
  - 错误码分类（AUTH_*/BIZ_*/VALIDATION_*/STATE_*/TREND_*）
  - HTTP状态码映射
  - 错误处理最佳实践

#### 业务模块 SoT (P2)
- **[LEDGER_SOT.md](./2.sot/LEDGER_SOT.md)** - 账本系统
  - 双账本设计（PROJECT/SUPPLIER）
  - 流水类型（entry_type）
  - 红冲机制（REVERSAL）
  - 账本校验规则

- **[DAILY_REPORT_SOT.md](./2.sot/DAILY_REPORT_SOT.md)** - 日报模块
  - 三数据流（raw→real→final）
  - 8状态粉丝确认流程
  - 计费逻辑

- **[RECONCILIATION_SOT.md](./2.sot/RECONCILIATION_SOT.md)** - 对账模块
  - 对账规则与流程
  - 差异处理机制

- **[TRANSFER_SOT.md](./2.sot/TRANSFER_SOT.md)** - 划拨模块
  - 账户划拨流程
  - 状态转换规则

#### 安全与策略 SoT (P1)
- **[RLS_POLICIES_SOT.md](./2.sot/RLS_POLICIES_SOT.md)** - RLS策略
  - Supabase行级安全策略
  - 权限过滤规则

### 🎯 适用人群
- 后端开发人员（必读）
- 前端开发人员（API/AUTH部分必读）
- 测试工程师（验收标准）

---

## Tier 3: 开发指南

**定位**: 开发人员日常开发的规范、流程和最佳实践。

### 🛠️ 开发指南清单

1. **[API_DEVELOPMENT_FLOW.md](./3.dev-guides/API_DEVELOPMENT_FLOW.md)**
   - API开发生命周期SOP
   - Router → Service → Model 分层架构
   - 测试驱动开发流程

2. **[API_RULEBOOK.md](./3.dev-guides/API_RULEBOOK.md)**
   - API开发规则手册
   - RESTful设计规范
   - 错误处理标准

3. **[BACKEND_SETUP.md](./3.dev-guides/BACKEND_SETUP.md)**
   - 后端环境搭建（FastAPI + PostgreSQL + Supabase）
   - 依赖安装与配置

4. **[FRONTEND_SETUP.md](./3.dev-guides/FRONTEND_SETUP.md)**
   - 前端环境搭建（Next.js 14）
   - 开发服务器配置

5. **[FRONTEND_RULES.md](./3.dev-guides/FRONTEND_RULES.md)**
   - 前端开发规范
   - TypeScript规范
   - 组件设计原则

6. **[DEVELOPMENT_STANDARDS.md](./3.dev-guides/DEVELOPMENT_STANDARDS.md)**
   - 编码标准
   - Git提交规范

7. **[TESTING_GUIDE.md](./3.dev-guides/TESTING_GUIDE.md)**
   - 测试策略（单元/集成/E2E）
   - pytest/Jest使用指南

### 🎯 适用人群
- 全体开发人员（必读）
- 新加入开发团队成员

---

## Tier 4: UI / UX 文档

**定位**: 设计系统、组件库、用户体验规范。

### 📐 规划中的文档

- **DESIGN_SYSTEM.md** - 设计系统规范（颜色/字体/间距）
- **UI_COMPONENTS.md** - UI组件库（shadcn/ui使用指南）
- **UX_GUIDELINES.md** - 用户体验指南（交互规范）

### 🎯 适用人群
- UI/UX设计师
- 前端开发人员

---

## Tier 5: 运维文档

**定位**: 部署、监控、备份恢复等运维相关文档。

### 🚀 规划中的文档

- **DEPLOYMENT.md** - 部署指南（Docker/K8s）
- **MONITORING.md** - 监控与告警（Prometheus/Grafana）
- **BACKUP_RECOVERY.md** - 备份与恢复（数据库/文件）

### 🎯 适用人群
- 运维工程师
- DevOps团队

---

## 🔄 文档优先级与冲突仲裁

### 优先级层级

根据 [MASTER_SPEC.md](./1.overview/MASTER_SPEC.md) 定义，文档冲突时按以下优先级仲裁：

| 优先级 | 文档 | 说明 |
|--------|------|------|
| **P0** | MASTER_SPEC.md | 系统根规范，最高优先级 |
| **P1** | DATA_SCHEMA.md, STATE_MACHINE.md, BUSINESS_RULES.md | 核心SoT，技术决策依据 |
| **P1** | API_SOT.md, AUTH_SPEC.md, ERROR_CODES_SOT.md | 接口与认证规范 |
| **P2** | LEDGER_SOT.md, DAILY_REPORT_SOT.md, RECONCILIATION_SOT.md 等 | 业务模块SoT |
| **P3** | API_DEVELOPMENT_FLOW.md, API_RULEBOOK.md 等 | 开发指南 |
| **P4** | 模块API文档（modules/*/API_GUIDE.md） | 实现细节 |

### 仲裁原则

1. **优先级高的文档覆盖优先级低的文档**
2. **同优先级文档冲突时，以最新修订版本为准**
3. **发现冲突时，必须修正低优先级文档**

---

## 📚 核心设计原则（快速参考）

根据 [MASTER_SPEC.md](./1.overview/MASTER_SPEC.md) 定义：

### 三数据流
- **raw（投手提交）** → **real（真实消耗）** → **final（最终粉数计费）**
- 数据向下单向流动，禁止逆向覆盖

### 双账本
- **PROJECT Ledger（项目收入）** - 记录客户充值、消耗、余额
- **SUPPLIER Ledger（供应商成本）** - 记录真实成本、利润

### SOD（职责分离）
- **申请人 ≠ 审核人 ≠ 审批人**
- 关键业务流程强制多人审核

### 终态保护
- **final_locked = true** 后仅可通过红冲（REVERSAL）修正
- 保证历史数据可追溯、不可篡改

---

## 🔧 文档维护

### 更新频率
- **Tier 1 (Overview)**: 重大架构变更时更新
- **Tier 2 (SoT)**: 任何规范变更即更新，需Code Review
- **Tier 3 (Dev Guides)**: 每月审查，流程优化时更新
- **Tier 4/5**: 功能上线时同步更新

### 版本管理
- 所有文档使用Git版本控制
- 重要SoT文档变更需创建变更日志
- 历史版本归档至 `docs/archive/`

### 贡献指南
1. 修改前先检查文档优先级
2. SoT文档修改需团队评审
3. 提交时附上修改原因（Git commit message）
4. 更新相关联文档的引用

---

## 📞 联系与支持

- **文档问题**: 在项目仓库提交Issue
- **规范讨论**: 发起团队讨论会议
- **紧急变更**: 联系架构师审批

---

## 🗓️ 文档审查记录

| 日期 | 版本 | 变更说明 | 审查人 |
|------|------|----------|--------|
| 2025-11-22 | v4.0 | 重构文档体系为5层架构，归档旧版本 | Claude |
| 2024-11-18 | v3.0 | 重构优化旧文档结构 | - |

---

*最后更新: 2025-11-22*
*文档体系版本: v4.0*
*下次全面审查: 2025-12-22*
