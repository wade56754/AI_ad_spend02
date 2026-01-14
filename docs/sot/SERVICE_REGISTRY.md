# Service Registry (服务注册表)

> **版本**: v1.0
> **更新日期**: 2026-01-12
> **维护者**: AI Code Factory

---

## 概述

此文档定义了每个业务功能的**权威服务文件**，解决代码碎片化问题。
开发时必须修改权威文件，禁止修改废弃文件。

---

## 服务注册表

### 财务模块

| 业务功能 | 权威文件 | 路由器 | 废弃文件 |
|---------|---------|--------|---------|
| **资金总览** | `services/fund_service_v2.py` | `routers/finance_v2.py` | `services/fund_service.py`, `routers/fund.py` |
| **项目盈亏** | `services/profit_service_v2.py` | `routers/finance_v2.py` | `services/finance/profit_service.py`, `routers/profit.py` |
| **利润聚合** | `services/finance/profit_service.py` | `routers/finance_profit.py` | - |
| **财务总账** | `services/ledger_service.py` | `routers/ledger.py` | - |

### 对账模块

| 业务功能 | 权威文件 | 路由器 | 废弃文件 |
|---------|---------|--------|---------|
| **对账管理** | `services/reconciliation_service.py` | `routers/reconciliation.py` | `services/reconciliation_service_extended.py`, `services/reconciliation_service_optimized.py` |
| **对账中控** | `services/reconciliation_control_service.py` | `routers/reconciliation_control.py` | - |

### 日报模块

| 业务功能 | 权威文件 | 路由器 | 废弃文件 |
|---------|---------|--------|---------|
| **日报管理** | `services/daily_report_service.py` | `routers/daily_reports.py` | - |

### Dashboard 模块

| 业务功能 | 权威文件 | 路由器 | 废弃文件 |
|---------|---------|--------|---------|
| **CEO 驾驶舱** | `services/dashboard/metrics_service.py` | `routers/dashboard.py` | - |
| **利润指标** | `services/dashboard/profit_service.py` | `routers/dashboard.py` | - |

---

## 数据模型关系

### DailyReport 查询路径

```
DailyReport (日报)
    ↓ ad_account_id
AdAccount (广告账户)
    ↓ project_id        ↓ supplier_id
Project (项目)      Supplier (供应商)
```

**关键约束**:
- `DailyReport` **没有** `project_id` 字段
- `AdAccount` **没有** `supplier_name` 字段
- 获取项目需要 JOIN: `DailyReport.ad_account_id → AdAccount.project_id`
- 获取供应商名称需要 JOIN: `AdAccount.supplier_id → Supplier.name`

---

## 废弃文件清单

以下文件应在下次重构中删除：

### 高优先级（已被替代）

| 文件 | 替代方案 | 状态 |
|------|---------|------|
| `services/fund_service.py` | `fund_service_v2.py` | 可删除 |
| `routers/fund.py` | `finance_v2.py` | 可删除 |
| `routers/profit.py` | `finance_v2.py` | 可删除 |

### 中优先级（未被引用）

| 文件 | 原因 | 状态 |
|------|------|------|
| `services/reconciliation_service_extended.py` | 无路由引用 | 可删除 |
| `services/reconciliation_service_optimized.py` | 无路由引用 | 可删除 |

---

## 路由注册规则

### main.py 路由注册顺序

```python
# ✅ 权威路由
app.include_router(finance_v2.router)  # /api/v1/finance/fund + /api/v1/finance/profit
app.include_router(finance_profit.router)  # /api/v1/finance/profit (聚合功能)
app.include_router(reconciliation.router)  # /api/v1/reconciliation

# ❌ 废弃路由（已注释）
# app.include_router(fund.router)  # 使用 finance_v2.router
# app.include_router(profit.router)  # 使用 finance_v2.router
```

---

## 修改指南

### 修复 Bug 时

1. 查阅此注册表，确认权威文件
2. 只修改权威文件
3. 如果需要修改废弃文件，先迁移到权威文件

### 新增功能时

1. 添加到已有权威服务（如果属于该模块）
2. 或创建新服务并注册到此文档
3. 禁止创建 `_v2`、`_extended` 等后缀文件

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-01-12 | 初始版本，统一财务模块路由 |
