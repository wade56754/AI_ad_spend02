# Module Specs - 模块规格书索引

> **版本**: v2.3
> **更新日期**: 2025-12-23
> **基准**: MASTER.md v4.4 第六章

---

## 一、概述

本目录存放 MVP 系统 10 个核心页面的模块规格书。每个规格书定义了模块的业务目标、数据需求、UI 规范和代码块组合。

### 开发优先级

| 优先级 | 模块 | 说明 |
|--------|------|------|
| **P0** | A1, A2, A3, C1 | 核心 MVP，首批上线 |
| **P1** | B1, B2, C3 | 流程核心，第二批 |
| **P2** | B3, C2, D1 | 完善功能，第三批 |

---

## 二、模块架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     MVP 系统模块架构                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  【模块 A: 老板视角模块】 P0                                             │
│  ├── A1: 驾驶舱 (Dashboard)                                            │
│  ├── A2: 资金总览 (Fund Overview)                                      │
│  └── A3: 项目盈亏 (Project P&L)                                        │
│                                                                         │
│  【模块 B: 流程管理模块】 P1/P2                                          │
│  ├── B1: 充值审批 (Topup Approval) - P1                                │
│  ├── B2: 日报审核 (Daily Report Review) - P1                           │
│  └── B3: 周度简报 (Weekly Brief) - P2 [待开发]                         │
│                                                                         │
│  【模块 C: 数据管理模块】 P0/P1/P2                                       │
│  ├── C1: 项目管理 (Project Management) - P0                            │
│  ├── C2: 投手管理 (Pitcher Management) - P2                            │
│  └── C3: 消耗明细 (Spend Detail) - P1                                  │
│                                                                         │
│  【模块 D: 结算模块】 P2                                                 │
│  └── D1: 月度结算 (Monthly Settlement)                                 │
│                                                                         │
│  【模块 E: 扩展模块】 Phase 2+ [EXT]                                    │
│  ├── E1: 渠道管理 (Channels)                                           │
│  ├── E2: 供应商管理 (Suppliers)                                        │
│  ├── E3: 转账管理 (Transfers)                                          │
│  └── E4: 对账管理 (Reconciliation)                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 三、模块规格书索引

### 3.1 模块 A: 老板视角 (P0)

| 编号 | 模块 | 规格书 | 状态 | 解决问题 |
|------|------|--------|------|---------|
| A1 | 老板驾驶舱 | [A1-dashboard.md](A1-dashboard.md) | :white_check_mark: 已完成 | 今天公司怎么样？ |
| A2 | 资金总览 | [A2-fund-overview.md](A2-fund-overview.md) | :white_check_mark: 已完成 | 钱在哪里？能收回多少？ |
| A3 | 项目盈亏 | [A3-project-pnl.md](A3-project-pnl.md) | :white_check_mark: 已完成 | 哪个项目赚/亏？ |

### 3.2 模块 B: 流程管理 (P1/P2)

| 编号 | 模块 | 规格书 | 状态 | 解决问题 |
|------|------|--------|------|---------|
| B1 | 充值审批 | [B1-topup-approval.md](B1-topup-approval.md) | :white_check_mark: 已完成 | 该不该批这笔钱？ |
| B2 | 日报审核 | [B2-daily-report-review.md](B2-daily-report-review.md) | :white_check_mark: 已完成 | 投手今天干得怎样？ |
| B3 | 周度简报 | [B3-weekly-brief.md](B3-weekly-brief.md) | :white_check_mark: 规格完成 (功能待开发) | 项目这周进展如何？ |

### 3.3 模块 C: 数据管理 (P0/P1/P2)

| 编号 | 模块 | 规格书 | 状态 | 解决问题 |
|------|------|--------|------|---------|
| C1 | 项目管理 | [C1-project-mgmt.md](C1-project-mgmt.md) | :white_check_mark: 已完成 | 有哪些项目？谁负责？ |
| C2 | 投手管理 | [C2-pitcher-mgmt.md](C2-pitcher-mgmt.md) | :white_check_mark: 已完成 | 有哪些投手？负责什么？ |
| C3 | 消耗明细 | [C3-spend-detail.md](C3-spend-detail.md) | :white_check_mark: 已完成 | 某天/某账户消耗多少？ |

### 3.4 模块 D: 结算 (P2)

| 编号 | 模块 | 规格书 | 状态 | 解决问题 |
|------|------|--------|------|---------|
| D1 | 月度结算 | [D1-monthly-settlement.md](D1-monthly-settlement.md) | :white_check_mark: 已完成 | 这个月赚了还是亏了？ |

### 3.5 后端模块规格书 (AI 代码工厂约束)

| 编号 | 模块 | 规格书 | 状态 | 用途 |
|------|------|--------|------|------|
| A1 | 老板驾驶舱 | [A1-dashboard-backend.md](A1-dashboard-backend.md) | :white_check_mark: 已完成 | 约束 KPI 聚合 + 权限过滤 + 趋势分析 |
| A2 | 资金总览 | [A2-fund-overview-backend.md](A2-fund-overview-backend.md) | :white_check_mark: 已完成 | 约束资金聚合 + 5 指标计算 + 预警 |
| A3 | 项目盈亏 | [A3-project-pnl-backend.md](A3-project-pnl-backend.md) | :white_check_mark: 已完成 | 约束盈亏聚合 + CPL 异常标记 + 负责人 |
| B1 | 日报提交 | [B1-daily-report-submit.md](B1-daily-report-submit.md) | :white_check_mark: 已完成 | 约束日报 CRUD + 8状态机前半段 |
| B2 | 日报审核 | [B2-daily-report-review-backend.md](B2-daily-report-review-backend.md) | :white_check_mark: 已完成 | 约束趋势风控 + 8状态机后半段 |
| C1 | 充值审批 | [C1-topup-approval-backend.md](C1-topup-approval-backend.md) | :white_check_mark: 已完成 | 约束充值流程 + 7状态机 + 责任追溯 |
| C2 | 投手管理 | [C2-pitcher-mgmt-backend.md](C2-pitcher-mgmt-backend.md) | :white_check_mark: 已完成 | 约束用户 CRUD + 角色管理 + 软删除 |
| D1 | 项目管理 | [D1-project-mgmt-backend.md](D1-project-mgmt-backend.md) | :white_check_mark: 已完成 | 约束项目 CRUD + 5状态机 + 成员管理 |
| C3 | 消耗明细 | [C3-spend-detail-backend.md](C3-spend-detail-backend.md) | :white_check_mark: 已完成 | 约束消耗导入 + 5状态机 + 账本分录 |
| E1 | 月度结算 | [E1-monthly-settlement-backend.md](E1-monthly-settlement-backend.md) | :white_check_mark: 已完成 | 约束月度盈亏 + 4状态机 + 锁定机制 |
| B3 | 周度简报 | [B3-weekly-brief-backend.md](B3-weekly-brief-backend.md) | :white_check_mark: 已完成 | 约束周报 CRUD + 2状态机 + 周数据汇总 |

> **后端规格书用途**: 为 AI 代码工厂提供严格约束，防止 AI 幻觉，确保生成代码符合 SoT 规范。
> **参考指南**: [BACKEND_MODULE_SPEC_GUIDE.md](../3.dev-guides/BACKEND_MODULE_SPEC_GUIDE.md)

---

## 四、模块规格书模板

每个模块规格书应包含以下内容：

```markdown
# [模块编号] [模块名称] - 模块规格书

## 1. 模块概述
### 1.1 业务目标
### 1.2 用户角色
### 1.3 核心用例

## 2. 数据需求
### 2.1 数据源 (SoT)
### 2.2 字段清单 (MASTER.md §6.5)
### 2.3 计算公式

## 3. UI 规范
### 3.1 页面布局
### 3.2 组件清单
### 3.3 交互规则

## 4. 代码块组合
### 4.1 前端代码块
### 4.2 后端代码块
### 4.3 组合图

## 5. API 接口
### 5.1 接口清单
### 5.2 请求/响应示例

## 6. 状态与权限
### 6.1 状态机 (如适用)
### 6.2 权限矩阵

## 7. 测试检查点

## 8. 源码位置
```

---

## 五、模块与责任模型映射

来源: MASTER.md v4.4 §6.3

| 责任问题 | 对应模块 | 系统如何支撑 |
|----------|----------|-------------|
| 谁对钱负责？ | B1 充值审批 | 记录申请人、审批人、审批结果 |
| 钱在哪里？ | A2 资金总览 | 展示充值、消耗、余额、应收 |
| 谁对结果负责？ | C1 项目管理 | 展示项目负责人 |
| 项目赚钱吗？ | A3 盈亏看板 | 展示项目盈亏与负责人 |
| 投手干得怎样？ | B2 日报审核 | 主管审核，高亮异常 |
| 需要纠偏吗？ | A1 驾驶舱 | 展示异常项目数、待审批数 |

---

## 六、模块与代码块映射

| 模块 | 前端代码块 | 后端代码块 |
|------|-----------|-----------|
| A1 驾驶舱 | StatCard, TrendChart, TopList, GlobalFilters | kpi-calculator, dashboard-aggregation |
| A2 资金总览 | StatCard, DataTable | kpi-calculator, ledger-entry |
| A3 盈亏看板 | StatCard, DataTable, TopList | kpi-calculator, profit-aggregation |
| B1 充值审批 | DataTable, ApprovalTimeline, ActionButtons | state-machine, approval-workflow |
| B2 日报审核 | DataTable, StatusBadge, ActionButtons | state-machine, trend-risk-control |
| B3 周度简报 | WeeklyBriefPage, WeeklyBriefForm, WeekPicker, StatCard | weekly-brief-service, aggregation-service |
| C1 项目管理 | DataTable, FormDialog, StatusBadge | permission-filter, audit-log |
| C2 投手管理 | DataTable, FormDialog | permission-filter |
| C3 消耗明细 | DataTable | pagination, permission-filter |
| D1 月度结算 | DataTable, StatCard | ledger-entry, settlement-service |

---

## 七、测试用例文档

**测试用例索引**:
- [TEST_CASES_v3.md](./TEST_CASES_v3.md) (推荐) - 基于 AI_TEST_GUIDE_v2.1.md 规范
- [TEST_CASES.md](./TEST_CASES.md) - 旧版测试用例 (已归档)

### 7.1 测试用例统计 (TEST_CASES_v3.md)

基于 AI_TEST_GUIDE_v2.1.md 规范，按 5 类检查点分类：

| 模块 | 权限 | UI | 数据 | 功能 | Phase1 | 合计 |
|------|------|-----|------|------|--------|------|
| A1 驾驶舱 | 9 | 5 | 4 | 5 | 2 | 25 |
| A2 资金总览 | 9 | 3 | 4 | 3 | 1 | 20 |
| A3 项目盈亏 | 7 | 4 | 4 | 4 | 2 | 21 |
| B1 充值审批 | 7 | 4 | 4 | 8 | 1 | 24 |
| B2 日报审核 | 7 | 4 | 4 | 11 | 2 | 28 |
| B3 周度简报 | 7 | 3 | 4 | 4 | 1 | 19 |
| C1 项目管理 | 7 | 4 | 4 | 7 | 1 | 23 |
| C2 投手管理 | 7 | 2 | 4 | 5 | 1 | 19 |
| C3 消耗明细 | 7 | 3 | 4 | 5 | 1 | 20 |
| D1 月度结算 | 7 | 3 | 4 | 5 | 1 | 20 |
| 跨模块集成 | 2 | - | 2 | 4 | - | 8 |
| **合计** | **76** | **35** | **42** | **61** | **13** | **227** |

### 7.2 测试优先级分布

| 优先级 | 用例数 | 占比 | 说明 |
|--------|--------|------|------|
| P0 (核心) | ~35 | 16% | 每次构建必测 |
| P1 (重要) | ~90 | 41% | 每日测试 |
| P2 (一般) | ~70 | 32% | 回归测试 |
| P3 (边缘) | ~22 | 10% | 发布前 |

### 7.3 Smoke Test 子集

带有 **[SMOKE]** 标记的用例构成冒烟测试子集 (~25 用例)，覆盖各模块核心功能入口、关键计算验证和主要权限验证。

---

## 八、版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.3 | 2025-12-23 | 新增 B3-weekly-brief-backend.md: 周度简报后端规格书，2状态机 + 周数据汇总 |
| v2.2 | 2025-12-23 | 新增 A3-project-pnl-backend.md: 项目盈亏后端规格书，CPL 异常标记 + 负责人关联 |
| v2.1 | 2025-12-23 | 新增 A2-fund-overview-backend.md: 资金总览后端规格书，5 指标聚合 + 预警机制 |
| v2.0 | 2025-12-23 | 新增 A1-dashboard-backend.md: 老板驾驶舱后端规格书，KPI 聚合 + 权限过滤 |
| v1.9 | 2025-12-23 | 新增 E1-monthly-settlement-backend.md: 月度结算后端规格书，4状态机 + 锁定机制 |
| v1.8 | 2025-12-23 | 新增 C3-spend-detail-backend.md: 消耗明细后端规格书，5状态机 + 账本分录 |
| v1.7 | 2025-12-23 | 新增 C2-pitcher-mgmt-backend.md: 投手管理后端规格书，用户 CRUD + 角色映射 |
| v1.6 | 2025-12-23 | 新增 D1-project-mgmt-backend.md: 项目管理后端规格书，5状态机 + 成员管理 |
| v1.5 | 2025-12-23 | 新增 C1-topup-approval-backend.md: 充值审批后端规格书，7状态机 + 责任追溯 |
| v1.4 | 2025-12-23 | 新增后端模块规格书索引 (§3.5): B1-daily-report-submit.md, B2-daily-report-review-backend.md |
| v1.3 | 2025-12-23 | 新增 TEST_CASES_v3.md：基于 AI_TEST_GUIDE_v2.1.md 全面重构，检查点清单格式、5类测试、7角色覆盖、Playwright 代码规范 |
| v1.2 | 2025-12-23 | 更新 TEST_CASES.md 至 v2.0：添加跨模块集成测试、UI 通用测试、权限测试完善、状态机非法转换测试 |
| v1.1 | 2025-12-23 | 添加测试用例文档 TEST_CASES.md |
| v1.0 | 2025-12-22 | 初始版本，建立模块规格书体系 |

---

**维护者**: AI 广告代投系统开发团队
**关联文档**: MASTER.md v4.4, 代码块索引
