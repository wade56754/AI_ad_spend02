# Profit Module Spec

> **Source**: PROFIT_SOT.md v1.1
> **Change**: finance-profit-v1
> **Date**: 2025-12-02

---

## ADDED Requirements

### Requirement: Profit Calculation Formula
The system SHALL calculate gross profit using the dual-ledger model as defined in LEDGER_SOT.md v1.1.

**Formula:**
```
gross_profit = total_revenue - total_cost
gross_margin_pct = (gross_profit / total_revenue) × 100
```

**Data Sources:**
- `total_revenue`: Sum of `ledger_entries` where `ledger_type = 'PROJECT'` and `entry_type = 'REVENUE'`
- `total_cost`: Sum of `ledger_entries` where `ledger_type = 'SUPPLIER'` and `entry_type = 'COST'`

#### Scenario: Calculate gross profit with positive margin
- **GIVEN** total_revenue = 10000, total_cost = 7000
- **WHEN** the system calculates gross profit
- **THEN** gross_profit SHALL be 3000
- **AND** gross_margin_pct SHALL be 30.00 (HALF_UP rounding)

#### Scenario: Calculate gross profit with zero revenue
- **GIVEN** total_revenue = 0, total_cost = 500
- **WHEN** the system calculates gross profit
- **THEN** gross_profit SHALL be -500
- **AND** gross_margin_pct SHALL be NULL (division by zero protection)

#### Scenario: Calculate gross profit with negative margin
- **GIVEN** total_revenue = 5000, total_cost = 6000
- **WHEN** the system calculates gross profit
- **THEN** gross_profit SHALL be -1000
- **AND** gross_margin_pct SHALL be -20.00

---

### Requirement: TOPUP Exclusion from Profit Calculation
The system SHALL NOT include TOPUP transactions in profit calculation as per BR-PROFIT-002.

**Rationale:** TOPUP represents balance changes (资金流入), NOT revenue. It is tracked separately in `total_topup` field for cash flow analysis.

#### Scenario: TOPUP not included in revenue
- **GIVEN** a period with daily_reports revenue = 10000
- **AND** topup_requests amount = 5000 (RECHARGE type)
- **WHEN** the system aggregates profit
- **THEN** total_revenue SHALL be 10000 (NOT 15000)
- **AND** total_topup SHALL be 5000 (separate tracking)

---

### Requirement: Data Aggregation Source Constraint
The system SHALL only aggregate data from `daily_reports` with status `final_locked` as per BR-PROFIT-003.

**Reference:** STATE_MACHINE.md v2.6 §8 defines the 8-state machine:
```
raw_submitted → trend_pending → trend_ok/trend_flagged
→ trend_resolved → final_pending → final_confirmed → final_locked
```

#### Scenario: Only final_locked data is aggregated
- **GIVEN** daily_reports with various statuses:
  - Report A: status = `final_locked`, revenue = 1000
  - Report B: status = `final_confirmed`, revenue = 2000
  - Report C: status = `trend_ok`, revenue = 500
- **WHEN** the system aggregates profit for the period
- **THEN** total_revenue SHALL be 1000 (only Report A)
- **AND** Reports B and C SHALL be excluded

#### Scenario: Re-aggregation after status change
- **GIVEN** an existing profit aggregate
- **AND** Report B status changes from `final_confirmed` to `final_locked`
- **WHEN** the system re-aggregates profit
- **THEN** total_revenue SHALL be updated to include Report B

---

### Requirement: Profit Aggregates Data Model
The system SHALL store profit aggregates in `profit_aggregates` table as defined in PROFIT_SOT.md v1.1 §2.1.

**Table: profit_aggregates** (L2 汇总层)

| Column | Type | Constraint | Description |
|--------|------|------------|-------------|
| id | BIGSERIAL | PK | 主键 |
| period_type | VARCHAR(20) | NOT NULL | 周期类型: daily/weekly/monthly |
| period_start | TIMESTAMPTZ | NOT NULL | 周期开始时间 |
| period_end | TIMESTAMPTZ | NOT NULL | 周期结束时间 |
| project_id | BIGINT | FK → projects | 项目ID（可空表示全局） |
| ad_account_id | BIGINT | FK → ad_accounts | 账户ID（可空表示项目级） |
| total_revenue | NUMERIC(18,2) | NOT NULL | 总收入 |
| total_cost | NUMERIC(18,2) | NOT NULL | 总成本 |
| gross_profit | NUMERIC(18,2) | NOT NULL | 毛利 |
| gross_margin_pct | NUMERIC(5,2) | NULLABLE | 毛利率 (%) |
| total_conversions | INTEGER | DEFAULT 0 | 转化数 |
| total_real_spend | NUMERIC(18,2) | DEFAULT 0 | 实际消耗 |
| total_topup | NUMERIC(18,2) | DEFAULT 0 | 充值金额（仅统计） |
| transfer_in | NUMERIC(18,2) | DEFAULT 0 | 转入金额 |
| transfer_out | NUMERIC(18,2) | DEFAULT 0 | 转出金额 |
| is_locked | BOOLEAN | DEFAULT FALSE | 是否锁定 |
| locked_at | TIMESTAMPTZ | NULLABLE | 锁定时间 |
| locked_by | UUID | FK → users | 锁定人 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**Unique Constraint:**
```sql
UNIQUE (period_type, period_start, project_id, ad_account_id)
```

#### Scenario: Create profit aggregate
- **WHEN** a new profit aggregate is created for period 2025-01
- **THEN** period_type SHALL be 'monthly'
- **AND** period_start SHALL be '2025-01-01 00:00:00+00'
- **AND** period_end SHALL be '2025-01-31 23:59:59+00'

---

### Requirement: Profit Report Snapshots Data Model
The system SHALL store report snapshots in `profit_report_snapshots` table as defined in PROFIT_SOT.md v1.1 §2.2.

**Table: profit_report_snapshots** (报表快照层)

| Column | Type | Constraint | Description |
|--------|------|------------|-------------|
| id | BIGSERIAL | PK | 主键 |
| report_type | VARCHAR(30) | NOT NULL | 报表类型 |
| period_month | VARCHAR(7) | NOT NULL | 月份 (YYYY-MM) |
| project_id | BIGINT | FK → projects | 项目ID（可空） |
| report_data | JSONB | NOT NULL | 报表数据 |
| status | VARCHAR(20) | NOT NULL | 状态: draft/confirmed/locked |
| generated_at | TIMESTAMPTZ | NOT NULL | 生成时间 |
| generated_by | UUID | FK → users | 生成人 |
| confirmed_at | TIMESTAMPTZ | NULLABLE | 确认时间 |
| confirmed_by | UUID | FK → users | 确认人 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |

**Report Types:**
- `monthly_summary`: 月度汇总报表
- `project_detail`: 项目明细报表
- `account_detail`: 账户明细报表

#### Scenario: Create monthly summary snapshot
- **WHEN** a monthly summary report is generated
- **THEN** report_type SHALL be 'monthly_summary'
- **AND** status SHALL be 'draft'
- **AND** report_data SHALL contain aggregated profit metrics

---

### Requirement: Finance Profit API Endpoints
The system SHALL expose 6 API endpoints for profit operations as defined in PROFIT_SOT.md v1.1 §3.

**Base Path:** `/api/v1/finance/profit`

| Method | Path | Operation | Description |
|--------|------|-----------|-------------|
| POST | /generate | GenerateProfit | 生成利润聚合 |
| GET | /monthly | GetMonthlyProfit | 月度利润表 |
| GET | /daily | GetDailyProfit | 日度利润数据 |
| GET | /projects/{id} | GetProjectProfit | 项目利润明细 |
| GET | /accounts/{id} | GetAccountProfit | 账户消耗明细 |
| GET | /summary | GetProfitSummary | 整体利润汇总 |

#### Scenario: POST /generate success
- **GIVEN** authenticated user with role 'finance'
- **AND** valid request body with period_type='monthly', period_month='2025-01'
- **WHEN** POST /api/v1/finance/profit/generate is called
- **THEN** response status SHALL be 201
- **AND** response body SHALL contain generated aggregate ID

#### Scenario: GET /monthly success
- **GIVEN** authenticated user with role 'admin'
- **AND** query params: month='2025-01'
- **WHEN** GET /api/v1/finance/profit/monthly is called
- **THEN** response status SHALL be 200
- **AND** response body SHALL follow API_SOT.md v9.0 format

#### Scenario: GET /projects/{id} not found
- **GIVEN** authenticated user with role 'account_manager'
- **AND** project_id = 99999 (non-existent)
- **WHEN** GET /api/v1/finance/profit/projects/99999 is called
- **THEN** response status SHALL be 404
- **AND** error code SHALL be PROFIT_003

---

### Requirement: Role-Based Permission Control
The system SHALL enforce 5-role permission matrix for profit API endpoints as defined in PROFIT_SOT.md v1.1 §3.

**Permission Matrix:**

| Endpoint | admin | finance | account_manager | media_buyer | viewer |
|----------|-------|---------|-----------------|-------------|--------|
| POST /generate | ✅ | ✅ | ❌ | ❌ | ❌ |
| GET /monthly | ✅ | ✅ | ❌ | ❌ | ❌ |
| GET /daily | ✅ | ✅ | ❌ | ❌ | ❌ |
| GET /projects/{id} | ✅ | ✅ | ✅ (own projects) | ❌ | ❌ |
| GET /accounts/{id} | ✅ | ✅ | ✅ | ✅ (own accounts) | ❌ |
| GET /summary | ✅ | ✅ | ❌ | ❌ | ❌ |

#### Scenario: media_buyer cannot access monthly
- **GIVEN** authenticated user with role 'media_buyer'
- **WHEN** GET /api/v1/finance/profit/monthly is called
- **THEN** response status SHALL be 403
- **AND** error code SHALL be PROFIT_005

#### Scenario: account_manager limited to own projects
- **GIVEN** authenticated user with role 'account_manager'
- **AND** user is assigned to project_id = 1
- **WHEN** GET /api/v1/finance/profit/projects/2 is called (not assigned)
- **THEN** response status SHALL be 403
- **AND** error code SHALL be PROFIT_005

#### Scenario: viewer has no access
- **GIVEN** authenticated user with role 'viewer'
- **WHEN** any profit endpoint is called
- **THEN** response status SHALL be 403
- **AND** error code SHALL be PROFIT_005

---

### Requirement: Profit Error Codes
The system SHALL use PROFIT_ prefixed error codes as defined in PROFIT_SOT.md v1.1 §5.

**Error Code Mapping:**

| Code | HTTP | Message | Scenario |
|------|------|---------|----------|
| PROFIT_001 | 404 | No data for specified period | 查询期间无数据 |
| PROFIT_002 | 400 | Invalid period parameter | 周期参数无效 |
| PROFIT_003 | 404 | Project not found | 项目不存在 |
| PROFIT_004 | 404 | Account not found | 账户不存在 |
| PROFIT_005 | 403 | Permission denied | 无权限访问 |
| PROFIT_006 | 500 | Aggregation failed | 聚合计算失败 |
| PROFIT_007 | 500 | Report generation failed | 报表生成失败 |
| PROFIT_008 | 409 | Data is locked | 数据已锁定，不可修改 |

**Error Response Format** (per API_SOT.md v9.0):
```json
{
  "success": false,
  "error": {
    "code": "PROFIT_001",
    "message": "No data for specified period",
    "details": { "period_month": "2025-01" }
  }
}
```

#### Scenario: PROFIT_001 no data
- **GIVEN** no daily_reports with final_locked status in 2025-01
- **WHEN** GET /api/v1/finance/profit/monthly?month=2025-01 is called
- **THEN** response status SHALL be 404
- **AND** error.code SHALL be "PROFIT_001"

#### Scenario: PROFIT_008 locked data
- **GIVEN** profit aggregate for 2025-01 with is_locked = true
- **WHEN** POST /api/v1/finance/profit/generate with period_month='2025-01'
- **THEN** response status SHALL be 409
- **AND** error.code SHALL be "PROFIT_008"

---

## Business Rules Reference

The following business rules from PROFIT_SOT.md v1.1 §4 SHALL be implemented:

| Rule ID | Description | Implementation |
|---------|-------------|----------------|
| BR-PROFIT-001 | gross_profit = total_revenue - total_cost | profit_service.py |
| BR-PROFIT-002 | TOPUP 不参与利润计算 | profit_service.py |
| BR-PROFIT-003 | 仅聚合 final_locked 数据 | profit_service.py |
| BR-PROFIT-004 | gross_margin_pct 使用 HALF_UP 四舍五入 | profit_service.py |
| BR-PROFIT-005 | 已锁定聚合不可重新生成 | profit_service.py |
| BR-PROFIT-006 | 月度报表基于 L2 聚合层生成 | profit_service.py |
| BR-PROFIT-007 | 跨账户转账不影响利润 | profit_service.py |
| BR-PROFIT-008 | 权限按 5 角色矩阵控制 | finance_profit.py |

---

## Dependencies

This spec depends on:

| Document | Version | Reference |
|----------|---------|-----------|
| PROFIT_SOT.md | v1.1 | Design source |
| DATA_SCHEMA.md | v5.2 | Table structures |
| LEDGER_SOT.md | v1.1 | Dual ledger model |
| STATE_MACHINE.md | v2.6 | 8-state machine (§8) |
| ERROR_CODES_SOT.md | v2.1 | Error code format |
| API_SOT.md | v9.0 | Response format |
