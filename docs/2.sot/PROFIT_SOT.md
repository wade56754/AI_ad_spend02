# PROFIT_SOT.md - 财务利润表模块规范（Single Source of Truth）

> **文档版本**: v1.1
> **status**: dev-ready
> **sot_id**: SoT-Profit-001
> **owner**: wade
> **last_reviewed**: 2025-12-02
> **发布日期**: 2025-12-02
> **文档类型**: Profit 模块领域唯一真相源（SoT-Profit）
> **适用范围**: 后端开发、前端开发、财务团队、测试工程师
> **规范级别**: 🟡 待落地（迁移完成后升级为 🔴 强制执行）
> **文档定位**: 利润表自动化模块的数据模型、API、业务规则、测试的唯一定义
> **baseline**: DATA_SCHEMA.md v5.2, LEDGER_SOT.md v1.1, STATE_MACHINE.md v2.6, ERROR_CODES_SOT.md v2.1, API_SOT.md v9.0

---

## 1. 概述

### 1.1 模块职责

**Profit 模块是 AI_AD_SYSTEM 财务闭环的报表层模块**，负责：

- ✅ **利润聚合计算**: 基于 ledger_entries 和 daily_reports 聚合收入/成本/毛利
- ✅ **多维度报表**: 项目级 / 账户级 / 整体级利润表
- ✅ **周期聚合**: 支持日度 / 月度聚合
- ✅ **可追溯链路**: 利润表 → 汇总层 → 原始流水完整追溯
- ✅ **报表快照**: 支持生成不可变的报表快照

### 1.2 在 SoT 体系中的位置

```
AI_AD_SYSTEM 文档体系
│
├─ DATA_SCHEMA.md v5.2        ← ledger_entries / daily_reports 表结构
├─ LEDGER_SOT.md v1.1         ← 双账本逻辑、REVENUE/COST 定义
├─ STATE_MACHINE.md v2.6 §8   ← 粉数确认状态机（8状态：raw_submitted→final_locked）
├─ ERROR_CODES_SOT.md v2.1    ← 错误码定义
├─ API_SOT.md v9.0            ← API 规范
│
└─ PROFIT_SOT.md v1.1 (本文档) ← Profit 模块领域唯一来源
    ├─ 引用 DATA_SCHEMA (新增 profit_aggregates / profit_report_snapshots)
    ├─ 引用 LEDGER_SOT (REVENUE/COST 聚合规则)
    ├─ 引用 STATE_MACHINE §8 (final_locked 作为计费基准)
    └─ 定义 利润聚合逻辑、API、业务规则、测试
```

### 1.3 仲裁规则

| 领域 | 唯一真相源 | 仲裁规则 |
|-----|-----------|---------|
| **ledger_entries 字段** | DATA_SCHEMA.md v5.2 | 本文档不重复定义 |
| **双账本逻辑** | LEDGER_SOT.md v1.1 | 本文档只引用 |
| **粉数确认状态机** | STATE_MACHINE.md v2.6 | 本文档只引用 |
| **利润聚合逻辑** | PROFIT_SOT.md v1.0 (本文档) | 其他文档以本文档为准 |
| **Profit API 定义** | PROFIT_SOT.md v1.0 (本文档) | 其他文档以本文档为准 |

---

## 2. 数据模型

### 2.1 profit_aggregates（利润聚合表）

**表定位**: L2 汇总层核心表，存储预计算的利润聚合数据。
**状态**: 待 Alembic migration 落地

#### 2.1.1 完整字段定义

| 字段名 | 类型 | 约束 | 默认值 | 说明 | 数据来源 |
|-------|------|------|--------|------|---------|
| `id` | BIGSERIAL | PK | auto | 主键 | 系统生成 |
| `period_type` | VARCHAR(20) | NOT NULL, CHECK | - | 周期类型 | API 参数 |
| `period_start` | DATE | NOT NULL | - | 周期开始日期（含） | API 参数 |
| `period_end` | DATE | NOT NULL | - | 周期结束日期（含） | API 参数 |
| `project_id` | BIGINT | FK → projects.id, 可空 | NULL | 项目ID（整体汇总时为 NULL） | ledger_entries.project_id |
| `ad_account_id` | BIGINT | FK → ad_accounts.id, 可空 | NULL | 账户ID（项目级汇总时为 NULL） | daily_reports.ad_account_id |
| `currency` | VARCHAR(10) | NOT NULL | 'CNY' | 记账本币 | 系统配置 |
| `total_revenue` | DECIMAL(15,2) | NOT NULL | 0.00 | 总收入（粉数计费） | SUM(ledger WHERE entry_type=REVENUE) |
| `total_cost` | DECIMAL(15,2) | NOT NULL | 0.00 | 总成本（绝对值） | ABS(SUM(ledger WHERE entry_type=COST)) |
| `gross_profit` | DECIMAL(15,2) | NOT NULL | 0.00 | 毛利 | total_revenue - total_cost |
| `gross_margin_pct` | DECIMAL(8,4) | NOT NULL | 0.0000 | 毛利率 (%) | gross_profit / total_revenue × 100 |
| `total_conversions` | INTEGER | NOT NULL | 0 | 总粉数 | SUM(daily_reports.conversions_final) |
| `total_real_spend` | DECIMAL(15,2) | NOT NULL | 0.00 | 总真实消耗 | SUM(daily_reports.real_spend) |
| `total_topup` | DECIMAL(15,2) | NOT NULL | 0.00 | 总充值 ⚠️ 仅用于资金流入统计，不参与毛利计算 | SUM(ledger WHERE entry_type=TOPUP) |
| `transfer_in` | DECIMAL(15,2) | NOT NULL | 0.00 | 迁入金额 | SUM(ledger WHERE entry_type=TRANSFER_IN) |
| `transfer_out` | DECIMAL(15,2) | NOT NULL | 0.00 | 迁出金额 | ABS(SUM(ledger WHERE entry_type=TRANSFER_OUT)) |
| `report_count` | INTEGER | NOT NULL | 0 | 已锁定日报数量 | COUNT(daily_reports WHERE final_locked) |
| `is_locked` | BOOLEAN | NOT NULL | false | 是否已锁定 | 月度结账时设置 |
| `locked_at` | TIMESTAMPTZ | 可空 | NULL | 锁定时间 | 系统自动 |
| `locked_by` | UUID | FK → users.id, 可空 | NULL | 锁定人 | 操作用户 |
| `created_at` | TIMESTAMPTZ | NOT NULL | NOW() | 创建时间 | 系统自动 |
| `updated_at` | TIMESTAMPTZ | NOT NULL | NOW() | 更新时间 | 系统自动 |

#### 2.1.2 CHECK 约束

```sql
CHECK (period_type IN ('daily', 'monthly'))
CHECK (period_start <= period_end)
CHECK (total_revenue >= 0)
CHECK (total_cost >= 0)
CHECK (gross_margin_pct >= -100 AND gross_margin_pct <= 100)
```

#### 2.1.3 唯一约束

```sql
UNIQUE (period_type, period_start, period_end, project_id, ad_account_id)
```

**说明**: 对于 `project_id` 或 `ad_account_id` 为 NULL 的情况，PostgreSQL 默认 NULL != NULL，因此需要使用 COALESCE 或部分唯一索引：

```sql
CREATE UNIQUE INDEX uq_profit_agg_period ON profit_aggregates (
    period_type, period_start, period_end,
    COALESCE(project_id, -1),
    COALESCE(ad_account_id, -1)
);
```

#### 2.1.4 索引

| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| `idx_profit_agg_period` | (period_type, period_start, period_end) | BTREE | 周期查询 |
| `idx_profit_agg_project` | (project_id, period_start) | BTREE | 项目查询 |
| `idx_profit_agg_account` | (ad_account_id, period_start) | BTREE | 账户查询 |
| `idx_profit_agg_locked` | (is_locked, period_start) | BTREE | 锁定状态筛选 |

#### 2.1.5 与现有表的关系

| 关联表 | 关联字段 | 关系类型 | 说明 |
|-------|---------|---------|------|
| projects | project_id → projects.id | N:1 | 项目维度聚合 |
| ad_accounts | ad_account_id → ad_accounts.id | N:1 | 账户维度聚合 |
| users | locked_by → users.id | N:1 | 锁定操作人 |
| ledger_entries | - | 读取聚合 | 收入/成本/充值/迁移数据来源 |
| daily_reports | - | 读取聚合 | 粉数/真实消耗/日报数量来源 |

---

### 2.2 profit_report_snapshots（利润报表快照表）

**表定位**: 存储生成的报表快照，支持历史查询和对账。
**状态**: 待 Alembic migration 落地

#### 2.2.1 完整字段定义

| 字段名 | 类型 | 约束 | 默认值 | 说明 | 数据来源 |
|-------|------|------|--------|------|---------|
| `id` | BIGSERIAL | PK | auto | 主键 | 系统生成 |
| `report_type` | VARCHAR(50) | NOT NULL, CHECK | - | 报表类型 | API 参数 |
| `period_month` | DATE | NOT NULL | - | 报表月份（月初日期） | API 参数 |
| `project_id` | BIGINT | FK → projects.id, 可空 | NULL | 项目ID（整体报表时为 NULL） | API 参数 |
| `generated_at` | TIMESTAMPTZ | NOT NULL | NOW() | 生成时间 | 系统自动 |
| `generated_by` | UUID | FK → users.id, NOT NULL | - | 生成人 | 操作用户 |
| `report_data` | JSONB | NOT NULL | - | 报表数据快照 | 聚合计算结果 |
| `checksum` | VARCHAR(64) | 可空 | NULL | SHA-256 校验和 | 系统计算 |
| `status` | VARCHAR(20) | NOT NULL, CHECK | 'draft' | 报表状态 | 状态机 |
| `confirmed_at` | TIMESTAMPTZ | 可空 | NULL | 确认时间 | 操作时间 |
| `confirmed_by` | UUID | FK → users.id, 可空 | NULL | 确认人 | 操作用户 |
| `created_at` | TIMESTAMPTZ | NOT NULL | NOW() | 创建时间 | 系统自动 |

#### 2.2.2 CHECK 约束

```sql
CHECK (report_type IN ('project_monthly', 'account_monthly', 'overall_monthly'))
CHECK (status IN ('draft', 'confirmed', 'locked'))
```

#### 2.2.3 唯一约束

```sql
UNIQUE (report_type, period_month, project_id)
```

#### 2.2.4 report_data JSONB 结构

```json
{
  "period": { "year": 2025, "month": 1 },
  "generated_at": "2025-02-01T10:00:00Z",
  "summary": {
    "total_revenue": "125000.00",
    "total_cost": "98500.00",
    "gross_profit": "26500.00",
    "gross_margin_pct": "21.20",
    "total_conversions": 5000,
    "report_count": 150
  },
  "details": [
    {
      "project_id": 1,
      "project_name": "项目A",
      "revenue": "50000.00",
      "cost": "40000.00",
      "gross_profit": "10000.00",
      "conversions": 2000
    }
  ]
}
```

---

## 3. API 规格

### 3.1 API 总览

| 端点 | 方法 | 描述 | 鉴权角色 |
|-----|------|------|---------|
| `/api/v1/finance/profit/generate` | POST | 生成/刷新利润聚合 | finance, admin |
| `/api/v1/finance/profit/monthly` | GET | 获取月度利润表 | finance, admin |
| `/api/v1/finance/profit/daily` | GET | 获取日度利润数据 | finance, admin |
| `/api/v1/finance/profit/projects/{project_id}` | GET | 获取项目利润明细 | account_manager, finance, admin |
| `/api/v1/finance/profit/accounts/{account_id}` | GET | 获取账户消耗明细 | media_buyer, data_operator, account_manager, finance, admin |
| `/api/v1/finance/profit/summary` | GET | 获取整体利润汇总 | finance, admin |

---

### 3.2 POST /api/v1/finance/profit/generate

**描述**: 生成或刷新指定周期的利润聚合数据

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 校验规则 |
|-------|------|------|------|---------|
| `period_type` | string | ✅ | 周期类型 | `daily` \| `monthly` |
| `period_start` | date | ✅ | 周期开始日期 | ISO 8601 格式，不能是未来日期 |
| `period_end` | date | ✅ | 周期结束日期 | ISO 8601 格式，≥ period_start |
| `project_id` | integer | ❌ | 指定项目ID | 可选，不传则全量聚合 |
| `force_refresh` | boolean | ❌ | 强制刷新已锁定数据 | 默认 false |

#### 请求示例

```json
{
  "period_type": "monthly",
  "period_start": "2025-01-01",
  "period_end": "2025-01-31",
  "project_id": null,
  "force_refresh": false
}
```

#### 响应结构

```json
{
  "success": true,
  "data": {
    "generated_count": 15,
    "period": {
      "type": "monthly",
      "start": "2025-01-01",
      "end": "2025-01-31"
    },
    "summary": {
      "total_projects": 10,
      "total_accounts": 50,
      "total_revenue": "125000.00",
      "total_cost": "98500.00",
      "gross_profit": "26500.00"
    }
  },
  "message": "利润聚合生成成功",
  "code": "SUCCESS",
  "request_id": "uuid",
  "timestamp": "2025-01-22T10:00:00Z"
}
```

#### 错误场景

| HTTP | 错误码 | 触发条件 |
|-----|-------|---------|
| 400 | PROFIT_001 | period_start > period_end |
| 400 | PROFIT_002 | period_start 是未来日期 |
| 404 | PROFIT_003 | project_id 不存在 |
| 409 | PROFIT_004 | 周期已锁定且 force_refresh=false |
| 403 | AUTH_500 | 用户角色不是 finance/admin |

---

### 3.3 GET /api/v1/finance/profit/monthly

**描述**: 获取指定月份的月度利润表

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 校验规则 |
|-------|------|------|------|---------|
| `year` | integer | ✅ | 年份 | 2020-2099 |
| `month` | integer | ✅ | 月份 | 1-12 |
| `project_id` | integer | ❌ | 指定项目ID | 可选，不传返回所有项目 |
| `include_accounts` | boolean | ❌ | 是否包含账户明细 | 默认 false |

#### 响应结构

```json
{
  "success": true,
  "data": {
    "period": { "year": 2025, "month": 1 },
    "summary": {
      "total_revenue": "125000.00",
      "total_cost": "98500.00",
      "gross_profit": "26500.00",
      "gross_margin_pct": "21.20",
      "total_conversions": 5000,
      "total_real_spend": "95000.00",
      "total_topup": "150000.00",
      "report_count": 150,
      "is_locked": false
    },
    "by_project": [
      {
        "project_id": 1,
        "project_name": "项目A",
        "revenue": "50000.00",
        "cost": "40000.00",
        "gross_profit": "10000.00",
        "gross_margin_pct": "20.00",
        "conversions": 2000,
        "real_spend": "38000.00",
        "report_count": 60,
        "accounts": []
      }
    ]
  },
  "message": "ok",
  "code": "SUCCESS",
  "request_id": "uuid",
  "timestamp": "2025-01-22T10:00:00Z"
}
```

#### 错误场景

| HTTP | 错误码 | 触发条件 |
|-----|-------|---------|
| 400 | PROFIT_001 | year/month 参数无效 |
| 404 | PROFIT_005 | 指定周期无数据 |
| 403 | AUTH_500 | 用户角色不是 finance/admin |

---

### 3.4 GET /api/v1/finance/profit/daily

**描述**: 获取指定日期范围的日度利润数据

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 校验规则 |
|-------|------|------|------|---------|
| `start_date` | date | ✅ | 开始日期 | ISO 8601 格式 |
| `end_date` | date | ✅ | 结束日期 | ISO 8601 格式，≥ start_date |
| `project_id` | integer | ❌ | 指定项目ID | 可选 |
| `page` | integer | ❌ | 页码 | 默认 1 |
| `page_size` | integer | ❌ | 每页数量 | 默认 20，最大 100 |

#### 响应结构

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "period_start": "2025-01-15",
        "period_end": "2025-01-15",
        "project_id": 1,
        "project_name": "项目A",
        "revenue": "5000.00",
        "cost": "4000.00",
        "gross_profit": "1000.00",
        "conversions": 200
      }
    ],
    "total": 150,
    "page": 1,
    "page_size": 20,
    "pages": 8
  },
  "message": "ok",
  "code": "SUCCESS",
  "request_id": "uuid",
  "timestamp": "2025-01-22T10:00:00Z"
}
```

---

### 3.5 GET /api/v1/finance/profit/projects/{project_id}

**描述**: 获取单个项目的利润明细

#### 路径参数

| 参数名 | 类型 | 说明 |
|-------|------|------|
| `project_id` | integer | 项目ID |

#### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| `start_date` | date | ✅ | 开始日期 |
| `end_date` | date | ✅ | 结束日期 |
| `granularity` | string | ❌ | 粒度: `daily` \| `monthly`，默认 `monthly` |

#### 响应结构

```json
{
  "success": true,
  "data": {
    "project": {
      "id": 1,
      "name": "项目A",
      "unit_price": "25.00"
    },
    "period": {
      "start": "2025-01-01",
      "end": "2025-01-31"
    },
    "summary": {
      "revenue": "50000.00",
      "cost": "40000.00",
      "gross_profit": "10000.00",
      "gross_margin_pct": "20.00",
      "conversions": 2000,
      "avg_unit_cost": "20.00"
    },
    "trend": [
      { "date": "2025-01-01", "revenue": "1500.00", "cost": "1200.00" }
    ],
    "by_account": [
      {
        "account_id": 101,
        "account_name": "账户A",
        "revenue": "25000.00",
        "cost": "20000.00",
        "conversions": 1000
      }
    ]
  },
  "message": "ok",
  "code": "SUCCESS",
  "request_id": "uuid",
  "timestamp": "2025-01-22T10:00:00Z"
}
```

#### 权限控制

| 角色 | 访问范围 |
|-----|---------|
| admin | 所有项目（读写） |
| finance | 所有项目（读写） |
| data_operator | 所有项目（只读） |
| account_manager | 仅自己管理的项目 (`projects.account_manager_id = user_id`)（只读） |
| media_buyer | ❌ 无权限 |

#### 错误场景

| HTTP | 错误码 | 触发条件 |
|-----|-------|---------|
| 404 | PROFIT_003 | project_id 不存在 |
| 403 | AUTH_500 | 无权限访问该项目 |

---

### 3.6 GET /api/v1/finance/profit/accounts/{account_id}

**描述**: 获取单个广告账户的消耗与利润明细

#### 路径参数

| 参数名 | 类型 | 说明 |
|-------|------|------|
| `account_id` | integer | 广告账户ID |

#### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| `start_date` | date | ✅ | 开始日期 |
| `end_date` | date | ✅ | 结束日期 |

#### 响应结构

```json
{
  "success": true,
  "data": {
    "account": {
      "id": 101,
      "name": "账户A",
      "account_code": "FB12345",
      "project_id": 1,
      "project_name": "项目A"
    },
    "period": {
      "start": "2025-01-01",
      "end": "2025-01-31"
    },
    "summary": {
      "revenue": "25000.00",
      "cost": "20000.00",
      "gross_profit": "5000.00",
      "gross_margin_pct": "20.00",
      "conversions": 1000,
      "real_spend": "19500.00",
      "avg_unit_cost": "20.00",
      "report_count": 31
    },
    "daily_trend": [
      {
        "date": "2025-01-01",
        "revenue": "800.00",
        "cost": "650.00",
        "conversions": 32,
        "real_spend": "630.00"
      }
    ]
  },
  "message": "ok",
  "code": "SUCCESS",
  "request_id": "uuid",
  "timestamp": "2025-01-22T10:00:00Z"
}
```

#### 权限控制

| 角色 | 访问范围 |
|-----|---------|
| admin / finance | 所有账户 |
| account_manager | 自己管理的项目下的账户 |
| data_operator | 所有账户（只读） |
| media_buyer | 仅自己创建的日报对应的账户 |

---

### 3.7 GET /api/v1/finance/profit/summary

**描述**: 获取整体利润汇总（跨所有项目）

#### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| `year` | integer | ✅ | 年份 |
| `month` | integer | ✅ | 月份 |

#### 响应结构

```json
{
  "success": true,
  "data": {
    "period": { "year": 2025, "month": 1 },
    "overall": {
      "total_revenue": "500000.00",
      "total_cost": "400000.00",
      "gross_profit": "100000.00",
      "gross_margin_pct": "20.00",
      "total_conversions": 20000,
      "total_topup": "600000.00",
      "net_transfer": "5000.00",
      "project_count": 10,
      "account_count": 50,
      "report_count": 1500
    },
    "top_projects": [
      { "project_id": 1, "project_name": "项目A", "gross_profit": "30000.00" }
    ],
    "is_locked": false
  },
  "message": "ok",
  "code": "SUCCESS",
  "request_id": "uuid",
  "timestamp": "2025-01-22T10:00:00Z"
}
```

---

## 4. 业务规则

### 4.1 业务规则总览

| 规则编号 | 规则名称 | 优先级 | 关联字段/模块 |
|---------|---------|--------|--------------|
| BR-PROFIT-001 | 聚合数据来源限定 | P0 | ledger_entries, daily_reports |
| BR-PROFIT-002 | 毛利计算公式 | P0 | gross_profit |
| BR-PROFIT-003 | 聚合数据只读原则 | P0 | profit_aggregates |
| BR-PROFIT-004 | 锁定后禁止刷新 | P1 | is_locked |
| BR-PROFIT-005 | 周期参数校验 | P1 | period_start, period_end |
| BR-PROFIT-006 | 收入来源限定 | P0 | total_revenue | (详见 BR-PROFIT-001) |
| BR-PROFIT-007 | 成本来源限定 | P0 | total_cost | (详见 BR-PROFIT-001) |
| BR-PROFIT-008 | 毛利率边界处理 | P2 | gross_margin_pct |

---

### 4.2 规则详细定义

#### BR-PROFIT-001: 聚合数据来源限定

**业务场景**: 利润聚合仅基于已完成计费的数据

**详细约束**:
- ✅ `total_revenue` 仅聚合 `ledger_entries` 中 `entry_type = 'REVENUE'` 且 `ledger_type = 'PROJECT'` 的记录
- ✅ `total_cost` 仅聚合 `ledger_entries` 中 `entry_type = 'COST'` 且 `ledger_type = 'SUPPLIER'` 的记录
- ✅ `total_conversions` / `total_real_spend` 仅聚合 `daily_reports` 中 `status = 'final_locked'` 的记录
- ❌ **禁止**聚合非 `final_locked` 状态的日报数据
- ❌ **禁止**聚合 `entry_type` 为 `REVERSAL` 时不考虑方向

**引用**: LEDGER_SOT.md v1.1 §2.2, STATE_MACHINE.md v2.6 §8

**错误码映射**: 无直接错误码（内部逻辑）

**Test Intent**:
- 创建 raw_submitted/final_pending 状态日报，验证不被聚合
- 创建 REVERSAL 记录，验证正确冲抵

---

#### BR-PROFIT-002: 毛利计算公式

**业务场景**: 毛利和毛利率的计算规则

**详细约束**:
```
gross_profit = total_revenue - total_cost
gross_margin_pct = (gross_profit / total_revenue) × 100   (当 total_revenue > 0)
gross_margin_pct = 0                                       (当 total_revenue = 0)
```

**引用**: LEDGER_SOT.md v1.1 §2.1

**错误码映射**: 无直接错误码

**Test Intent**:
- 验证 revenue=100, cost=80 → profit=20, margin=20%
- 验证 revenue=0, cost=50 → profit=-50, margin=0%
- 验证 revenue=100, cost=0 → profit=100, margin=100%

---

#### BR-PROFIT-003: 聚合数据只读原则

**业务场景**: 防止手工篡改聚合数据

**详细约束**:
- ✅ `profit_aggregates` 表只能通过 `/generate` API 写入
- ❌ **禁止**任何直接 UPDATE 聚合字段（total_revenue / total_cost / gross_profit 等）
- ✅ 仅允许更新 `is_locked` / `locked_at` / `locked_by` 字段
- ✅ 仅 admin/finance 角色可执行锁定操作

**引用**: BUSINESS_RULES.md BR-DATA-001

**错误码映射**: PROFIT_006

**Test Intent**:
- 尝试直接 PATCH 聚合字段，期望返回 PROFIT_006
- 验证 admin 可锁定，media_buyer 不可锁定

---

#### BR-PROFIT-004: 锁定后禁止刷新

**业务场景**: 月度结账后数据不可变

**详细约束**:
- ✅ 当 `is_locked = true` 时，默认禁止重新生成
- ✅ 如需强制刷新，必须传 `force_refresh = true` 且角色为 admin
- ❌ finance 角色无 `force_refresh` 权限

**引用**: BUSINESS_RULES.md BR-RPT-005 (类比)

**错误码映射**: PROFIT_004

**Test Intent**:
- 锁定后调用 generate（force_refresh=false），期望返回 PROFIT_004
- admin 传 force_refresh=true，期望成功
- finance 传 force_refresh=true，期望返回 AUTH_500

---

#### BR-PROFIT-005: 周期参数校验

**业务场景**: 防止无效的时间范围

**详细约束**:
- ✅ `period_start` 必须 ≤ `period_end`
- ✅ `period_start` 不能是未来日期（基于服务器 UTC 时间）
- ✅ `period_type = 'monthly'` 时，period_start 必须是月初（day=1）
- ✅ `period_type = 'monthly'` 时，period_end 必须是月末

**错误码映射**: PROFIT_001, PROFIT_002

**Test Intent**:
- start > end → PROFIT_001
- start = 未来日期 → PROFIT_002
- monthly 但 start.day != 1 → PROFIT_001

---

#### BR-PROFIT-006: 收入来源限定

**业务场景**: 确保收入数据来源正确

**详细约束**:
- ✅ `total_revenue` = SUM(ledger_entries.amount WHERE entry_type='REVENUE' AND ledger_type='PROJECT')
- ✅ REVENUE 金额在 ledger_entries 中必须为正数（引用 LEDGER_SOT.md §4）
- ❌ **禁止**将 TOPUP 计入收入

**引用**: LEDGER_SOT.md v1.1 §4, §7

**错误码映射**: 无直接错误码

---

#### BR-PROFIT-007: 成本来源限定

**业务场景**: 确保成本数据来源正确

**详细约束**:
- ✅ `total_cost` = ABS(SUM(ledger_entries.amount WHERE entry_type='COST' AND ledger_type='SUPPLIER'))
- ✅ COST 金额在 ledger_entries 中为负数，聚合时取绝对值
- ❌ **禁止**将 TRANSFER_OUT/TRANSFER_IN 计入成本

**引用**: LEDGER_SOT.md v1.1 §4, §7

**错误码映射**: 无直接错误码

---

#### BR-PROFIT-008: 毛利率边界处理

**业务场景**: 处理极端情况下的毛利率

**详细约束**:
- ✅ 当 `total_revenue = 0` 且 `total_cost > 0`，`gross_margin_pct = 0`（而非负无穷）
- ✅ 当 `total_revenue = 0` 且 `total_cost = 0`，`gross_margin_pct = 0`
- ✅ `gross_margin_pct` 保留 4 位小数，使用 **HALF_UP** 舍入规则（与系统金额字段一致）

**错误码映射**: 无直接错误码

**Test Intent**:
- revenue=0, cost=100 → margin=0%
- revenue=0, cost=0 → margin=0%

---

## 5. 错误码

### 5.1 错误码分配说明

根据 ERROR_CODES_SOT.md v2.1 的命名规范，Profit 模块使用 `PROFIT_` 前缀，编码范围 001-099。

> ⚠️ **前置依赖**: 需要先在 ERROR_CODES_SOT.md v2.1 §2.2 类别前缀定义表中新增 `PROFIT_` 前缀行：
> `| PROFIT_ | 利润报表 | 利润聚合、报表生成相关错误 | 400, 403, 404, 409 | 8 |`

### 5.2 错误码完整清单

| 错误码 | HTTP | 消息 | 触发场景 | 业务规则 | 状态 |
|-------|------|------|---------|---------|------|
| `PROFIT_001` | 400 | 周期参数无效 | period_start > period_end，或 monthly 类型但日期非月初/月末 | BR-PROFIT-005 | NEW |
| `PROFIT_002` | 400 | 开始日期不能是未来 | period_start > 当前日期（UTC） | BR-PROFIT-005 | NEW |
| `PROFIT_003` | 404 | 项目不存在 | 指定的 project_id 在 projects 表中不存在 | - | NEW |
| `PROFIT_004` | 409 | 周期已锁定，无法刷新 | is_locked=true 且 force_refresh=false | BR-PROFIT-004 | NEW |
| `PROFIT_005` | 404 | 指定周期无数据 | 查询的周期在 profit_aggregates 中无记录 | - | NEW |
| `PROFIT_006` | 403 | 禁止手工修改聚合数据 | 尝试直接 PATCH/PUT 聚合字段 | BR-PROFIT-003 | NEW |
| `PROFIT_007` | 404 | 账户不存在 | 指定的 account_id 在 ad_accounts 表中不存在 | - | NEW |
| `PROFIT_008` | 400 | 日期范围超出限制 | 单次查询日期范围 > 366 天 | - | NEW |

### 5.3 与现有错误码的复用

| 场景 | 复用错误码 | 说明 |
|-----|-----------|------|
| 未提供认证令牌 | AUTH_400 | 请求头缺少 Authorization |
| 令牌无效/过期 | AUTH_401/AUTH_402 | Token 验证失败 |
| 权限不足 | AUTH_500 | 用户角色不满足 API 要求 |
| 必填字段缺失 | VALIDATION_001 | Pydantic 校验失败 |
| 系统内部错误 | SYS_001 | 未捕获的异常 |

### 5.4 错误响应示例

```json
{
  "success": false,
  "message": "周期已锁定，无法刷新",
  "code": "PROFIT_004",
  "data": {
    "period_type": "monthly",
    "period_start": "2025-01-01",
    "period_end": "2025-01-31",
    "locked_at": "2025-02-01T10:00:00Z"
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-02-05T10:30:00Z"
}
```

---

## 6. 测试用例

### 6.1 测试文件结构

```
backend/tests/
├── api/
│   ├── test_finance_profit_api.py          # API 集成测试
│   └── test_finance_profit_generated.py    # ai-ad-api-automation-test 生成
├── services/
│   └── test_profit_service.py              # Service 单元测试
└── unit/
    └── test_profit_calculation.py          # 计算逻辑单元测试
```

### 6.2 测试覆盖矩阵

| test_id | 场景 | 用例类别 | 测试文件 | 覆盖规则/错误码 |
|---------|-----|---------|---------|----------------|
| **Happy Path** |||||
| TC-PROFIT-HP-001 | 生成月度聚合成功 | Happy Path | test_finance_profit_api.py | - |
| TC-PROFIT-HP-002 | 查询月度利润表 | Happy Path | test_finance_profit_api.py | - |
| TC-PROFIT-HP-003 | 查询项目利润明细 | Happy Path | test_finance_profit_api.py | - |
| TC-PROFIT-HP-004 | 查询账户消耗明细 | Happy Path | test_finance_profit_api.py | - |
| TC-PROFIT-HP-005 | 查询整体汇总 | Happy Path | test_finance_profit_api.py | - |
| **Validation** |||||
| TC-PROFIT-VAL-001 | period_start > period_end | Validation | test_finance_profit_api.py | PROFIT_001 |
| TC-PROFIT-VAL-002 | period_start 是未来日期 | Validation | test_finance_profit_api.py | PROFIT_002 |
| TC-PROFIT-VAL-003 | monthly 但非月初/月末 | Validation | test_finance_profit_api.py | PROFIT_001 |
| TC-PROFIT-VAL-004 | year/month 参数无效 | Validation | test_finance_profit_api.py | PROFIT_001 |
| TC-PROFIT-VAL-005 | 日期范围超 366 天 | Validation | test_finance_profit_api.py | PROFIT_008 |
| **Permission** |||||
| TC-PROFIT-PERM-001 | media_buyer 访问整体汇总 | Permission | test_finance_profit_api.py | AUTH_500 |
| TC-PROFIT-PERM-002 | account_manager 访问非自己项目 | Permission | test_finance_profit_api.py | AUTH_500 |
| TC-PROFIT-PERM-003 | finance 强制刷新锁定周期 | Permission | test_finance_profit_api.py | AUTH_500 |
| TC-PROFIT-PERM-004 | admin 强制刷新锁定周期 | Permission | test_finance_profit_api.py | - (成功) |
| **Error Codes** |||||
| TC-PROFIT-ERR-001 | 项目不存在 | Error Codes | test_finance_profit_api.py | PROFIT_003 |
| TC-PROFIT-ERR-002 | 账户不存在 | Error Codes | test_finance_profit_api.py | PROFIT_007 |
| TC-PROFIT-ERR-003 | 周期无数据 | Error Codes | test_finance_profit_api.py | PROFIT_005 |
| TC-PROFIT-ERR-004 | 周期已锁定 | Error Codes | test_finance_profit_api.py | PROFIT_004 |
| **State Machine** |||||
| TC-PROFIT-SM-001 | 仅聚合 final_locked 日报 | State Machine | test_profit_service.py | BR-PROFIT-001 |
| TC-PROFIT-SM-002 | REVERSAL 正确冲抵 | State Machine | test_profit_service.py | BR-PROFIT-001 |
| **Calculation** |||||
| TC-PROFIT-CALC-001 | 毛利计算正确 | Calculation | test_profit_calculation.py | BR-PROFIT-002 |
| TC-PROFIT-CALC-002 | 毛利率边界 (revenue=0) | Calculation | test_profit_calculation.py | BR-PROFIT-008 |
| TC-PROFIT-CALC-003 | 收入来源正确 (仅 REVENUE) | Calculation | test_profit_calculation.py | BR-PROFIT-006 |
| TC-PROFIT-CALC-004 | 成本来源正确 (仅 COST) | Calculation | test_profit_calculation.py | BR-PROFIT-007 |
| **Regression** |||||
| TC-PROFIT-REG-001 | 现有 198+ 用例不受影响 | Regression | run_tests.py | - |

### 6.3 ai-ad-api-automation-test 使用说明

#### GENERATE 模式

```bash
/ai-ad-api-automation-test mode=GENERATE \
  target_module=finance/profit \
  endpoints='[
    "POST /api/v1/finance/profit/generate",
    "GET /api/v1/finance/profit/monthly",
    "GET /api/v1/finance/profit/daily",
    "GET /api/v1/finance/profit/projects/{project_id}",
    "GET /api/v1/finance/profit/accounts/{account_id}",
    "GET /api/v1/finance/profit/summary"
  ]' \
  sot_refs='["PROFIT_SOT.md v1.0", "LEDGER_SOT.md v1.1"]' \
  output_path=backend/tests/api/test_finance_profit_generated.py
```

#### RUN 模式

```bash
/ai-ad-api-automation-test mode=RUN \
  test_suite=finance_profit \
  baseline_check=true \
  fail_on_regression=true
```

#### REPORT 模式

```bash
/ai-ad-api-automation-test mode=REPORT \
  test_suite=finance_profit \
  output_format=markdown \
  include_coverage=true
```

### 6.4 单元测试示例骨架

```python
# backend/tests/unit/test_profit_calculation.py

import pytest
from decimal import Decimal
from backend.services.profit_service import ProfitService

class TestProfitCalculation:
    """毛利计算单元测试 - 覆盖 BR-PROFIT-002, BR-PROFIT-008"""

    def test_gross_profit_normal(self):
        """正常场景：revenue=100, cost=80"""
        result = ProfitService.calculate_profit(
            revenue=Decimal("100.00"),
            cost=Decimal("80.00")
        )
        assert result["gross_profit"] == Decimal("20.00")
        assert result["gross_margin_pct"] == Decimal("20.0000")

    def test_gross_profit_zero_revenue(self):
        """边界场景：revenue=0, cost=50 -> margin=0"""
        result = ProfitService.calculate_profit(
            revenue=Decimal("0.00"),
            cost=Decimal("50.00")
        )
        assert result["gross_profit"] == Decimal("-50.00")
        assert result["gross_margin_pct"] == Decimal("0.0000")

    def test_gross_profit_zero_both(self):
        """边界场景：revenue=0, cost=0 -> margin=0"""
        result = ProfitService.calculate_profit(
            revenue=Decimal("0.00"),
            cost=Decimal("0.00")
        )
        assert result["gross_profit"] == Decimal("0.00")
        assert result["gross_margin_pct"] == Decimal("0.0000")

    def test_gross_profit_full_margin(self):
        """边界场景：revenue=100, cost=0 -> margin=100%"""
        result = ProfitService.calculate_profit(
            revenue=Decimal("100.00"),
            cost=Decimal("0.00")
        )
        assert result["gross_profit"] == Decimal("100.00")
        assert result["gross_margin_pct"] == Decimal("100.0000")
```

### 6.5 REGRESSION_TEST_SUITE.md 增量内容

```markdown
## Finance Profit API 回归套件 (新增)

| 测试文件 | 测试数量 | 覆盖场景 | 状态 |
|---------|---------|---------|------|
| test_finance_profit_api.py | ~20 | API 全路径 | 待编写 |
| test_finance_profit_generated.py | ~15 | GENERATE 生成 | 待生成 |
| test_profit_service.py | ~10 | Service 逻辑 | 待编写 |
| test_profit_calculation.py | ~8 | 计算逻辑 | 待编写 |

**总计**: ~53 个测试用例

### 验收标准
- [ ] 所有 PROFIT_00X 错误码有对应测试用例
- [ ] 所有 BR-PROFIT-00X 业务规则有对应测试用例
- [ ] 现有 198+ 回归用例不受影响
- [ ] 利润数据与 ledger_entries 对账通过（抽样验证）
```

---

## 7. SoT 增量补丁汇总

### 7.1 DATA_SCHEMA.md 补丁

在 3.5 对账模块之后新增章节：

```markdown
### 3.6 利润表模块

#### 3.6.1 `profit_aggregates`（待落地）

**说明**: 利润聚合汇总表，存储预计算的收入/成本/毛利数据。

[完整字段定义见 PROFIT_SOT.md 2.1]

#### 3.6.2 `profit_report_snapshots`（待落地）

**说明**: 利润报表快照表，存储不可变的报表数据。

[完整字段定义见 PROFIT_SOT.md 2.2]
```

### 7.2 API_SOT.md 补丁

在 12 对账 API 之后新增章节：

```markdown
## 13. Finance Profit API（利润报表）

[完整 API 定义见 PROFIT_SOT.md 3]

### 13.1 端点总览

| 端点 | 方法 | 描述 | 鉴权角色 |
|-----|------|------|---------|
| `/api/v1/finance/profit/generate` | POST | 生成利润聚合 | finance, admin |
| `/api/v1/finance/profit/monthly` | GET | 月度利润表 | finance, admin |
| `/api/v1/finance/profit/daily` | GET | 日度利润数据 | finance, admin |
| `/api/v1/finance/profit/projects/{project_id}` | GET | 项目利润明细 | account_manager+ |
| `/api/v1/finance/profit/accounts/{account_id}` | GET | 账户消耗明细 | media_buyer+ |
| `/api/v1/finance/profit/summary` | GET | 整体利润汇总 | finance, admin |
```

### 7.3 BUSINESS_RULES.md 补丁

在规则导航表中新增：

```markdown
| **BR-PROFIT** | 利润报表 | [PROFIT_SOT.md](./PROFIT_SOT.md) | P1 | 待落地 |
```

### 7.4 ERROR_CODES_SOT.md 补丁

在 2.2 类别前缀定义中新增：

```markdown
| `PROFIT_` | 利润报表 | 利润聚合、报表生成相关错误 | 400, 403, 404, 409 | 8 |
```

在 4 错误码完整清单中新增：

```markdown
### 4.X 利润报表类（PROFIT_）

| 错误码 | 消息 | HTTP | 触发场景 | 状态 |
|--------|------|------|----------|------|
| `PROFIT_001` | 周期参数无效 | 400 | period_start > period_end | NEW |
| `PROFIT_002` | 开始日期不能是未来 | 400 | period_start > 当前日期 | NEW |
| `PROFIT_003` | 项目不存在 | 404 | project_id 不存在 | NEW |
| `PROFIT_004` | 周期已锁定，无法刷新 | 409 | is_locked=true | NEW |
| `PROFIT_005` | 指定周期无数据 | 404 | 无聚合记录 | NEW |
| `PROFIT_006` | 禁止手工修改聚合数据 | 403 | 直接 PATCH 聚合字段 | NEW |
| `PROFIT_007` | 账户不存在 | 404 | account_id 不存在 | NEW |
| `PROFIT_008` | 日期范围超出限制 | 400 | 范围 > 366 天 | NEW |
```

---

## 8. 文档版本与变更历史

### 8.1 版本历史

| 版本 | 日期 | 作者 | 变更说明 |
|-----|------|------|---------|
| v1.0 | 2025-12-02 | Claude | 初始版本，完整定义数据模型、API、业务规则、错误码、测试 |
| v1.1 | 2025-12-02 | Claude (doc-fixer) | **SoT 上线审计修复**: P0×2, P1×4 问题已修复。添加 sot_id/baseline；更新 STATE_MACHINE 引用；明确 TOPUP 不参与毛利；补充错误码前缀注册说明；统一业务规则引用；添加测试用例编号；完善权限矩阵；明确舍入规则 |

### 8.2 待落地事项

| 事项 | 优先级 | 负责人 | 预计完成 |
|-----|-------|-------|---------|
| 创建 profit_aggregates 表迁移 | P0 | 后端开发 | TBD |
| 创建 profit_report_snapshots 表迁移 | P0 | 后端开发 | TBD |
| 实现 ProfitService | P0 | 后端开发 | TBD |
| 实现 6 个 API 端点 | P0 | 后端开发 | TBD |
| 更新 DATA_SCHEMA.md | P1 | 文档维护 | TBD |
| 更新 API_SOT.md | P1 | 文档维护 | TBD |
| 更新 ERROR_CODES_SOT.md | P1 | 文档维护 | TBD |
| 生成测试骨架 | P1 | 测试工程师 | TBD |
| 执行 openspec validate | P2 | 架构师 | TBD |

---

**文档性质**: Profit 模块领域唯一真相源（SoT-Profit）
**执行级别**: 🟡 待落地（迁移完成后升级为 🔴 强制执行）
**违规处理**: PR 自动拒绝 / 代码回滚
**最后更新**: 2025-12-02
**版本**: v1.1
**审计状态**: ✅ dev-ready (P0=0, P1=0, P2=2)

---

**END OF DOCUMENT**
