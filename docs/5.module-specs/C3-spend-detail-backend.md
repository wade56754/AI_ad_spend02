# C3 消耗明细 - 后端模块规格书

> **版本**: v1.0
> **更新日期**: 2025-12-23
> **SoT 基准**: DATA_SCHEMA.md v5.3, STATE_MACHINE.md v2.7, LEDGER_SOT.md v1.2
> **参考指南**: docs/2.dev-guides/BACKEND_MODULE_SPEC_GUIDE.md

---

## 目录

- [§1 模块概述](#1-模块概述)
- [§2 数据模型](#2-数据模型)
- [§3 API 设计](#3-api-设计)
- [§4 权限控制](#4-权限控制)
- [§5 业务逻辑](#5-业务逻辑)
- [§6 前后端接口契约](#6-前后端接口契约)
- [§7 测试要点](#7-测试要点)
- [§8 性能要求](#8-性能要求)
- [§9 安全规范](#9-安全规范)

---

## §1 模块概述

### 1.1 业务目标

本模块实现广告消耗数据的导入、查询、流转和统计，解答核心管理问题：**"某天/某账户消耗多少？"**。通过 FinancialEvent 事件模型实现消耗数据的完整生命周期管理，支持 Excel 导入、状态流转、账本入账和冲正。

### 1.2 涉及角色

| 角色 | 系统角色名 | 本模块权限 |
|------|------------|------------|
| 老板 | ceo | 查看整体消耗概况 |
| 财务 | finance | **核心角色**: 导入、验证、确认、入账、导出 |
| 主管 | supervisor (data_operator) | 导入、验证、查看统计 |
| 投手 | pitcher (media_buyer) | 查看自己负责账户消耗 |
| 管理员 | admin | **超级权限**: 所有操作含冲正 |

### 1.3 模块边界

**本模块负责：**
- 消耗数据 Excel 导入
- 消耗事件 CRUD 和查询
- 消耗事件状态流转 (5 状态)
- 账本分录生成 (入账/冲正)
- 消耗统计和导出

**本模块不负责：**
- 日报数据管理（由 B1/B2 模块负责）
- 账户余额管理（由账户模块负责）
- 月度结算（由 D1 模块负责）

### 1.4 SoT 引用清单 (AI 防幻觉)

| SoT 文档 | 版本 | 引用章节 | 用途 |
|---------|------|---------|------|
| MASTER.md | v4.4 | §4.5.7 消耗SoT | 消耗数据来源规则 |
| STATE_MACHINE.md | v2.7 | §6 事件状态机 | 5 状态流转规则 |
| DATA_SCHEMA.md | v5.3 | §4.1 financial_events | 表结构定义 |
| LEDGER_SOT.md | v1.2 | §3 分录规则 | 账本规则 |
| BUSINESS_RULES.md | v4.1 | BR-FIN-* | 财务业务规则 |
| ERROR_CODES_SOT.md | v2.1 | BIZ_500-599, STATE_* | 错误码定义 |
| API_SOT.md | v9.3 | §7 Spend | API 端点规范 |
| AUTH_SPEC.md | v2.0 | §3 权限矩阵 | 角色权限 |

### 1.5 消耗 SoT 约束

**Phase 1 消耗来源** (MASTER.md §4.5.7):

| Phase | 消耗 SoT | 来源 | 说明 |
|-------|----------|------|------|
| Phase 1 | financial_events (SPEND) | Excel 导入 / 手工录入 | 代理商后台数据 |
| Phase 2 | daily_report.real_spend | supervisor/finance 确认 | 成本核算、结算 |

**强制约束**: Phase 1 的消耗 SoT 只能是 `financial_events (SPEND 类型)`。

---

## §2 数据模型

### 2.1 表结构定义

**来源**: DATA_SCHEMA.md v5.3 §4.1, `backend/models/finance/financial_event.py`

```sql
CREATE TABLE financial_events (
  -- 主键
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- 事件类型与状态
  event_type      VARCHAR(20) NOT NULL,           -- SPEND/TOPUP/TRANSFER/FEE
  event_status    VARCHAR(20) NOT NULL DEFAULT 'raw',

  -- 来源追溯
  source_type     VARCHAR(20),                    -- EXCEL_IMPORT/API/SYSTEM
  source_ref      VARCHAR(200),                   -- 来源引用（文件名等）
  idempotency_key VARCHAR(200) UNIQUE,            -- 幂等键

  -- 金额字段
  amount          DECIMAL(15,4) NOT NULL,         -- 净消耗金额
  fee_amount      DECIMAL(15,4) DEFAULT 0,        -- 手续费
  gross_amount    DECIMAL(15,4),                  -- 含费金额
  currency        VARCHAR(3) DEFAULT 'USD',       -- 货币

  -- 日期
  event_date      DATE NOT NULL,                  -- 事件日期

  -- 关联实体
  team_id         UUID,                           -- 团队ID
  buyer_id        UUID,                           -- 投手ID
  supplier_id     INTEGER,                        -- 供应商ID
  ad_account_id   INTEGER,                        -- 广告账户ID
  project_id      INTEGER,                        -- 项目ID

  -- 扩展数据
  payload         JSONB,                          -- 扩展字段 (today_max, fee_rate 等)

  -- 审计字段
  created_by      UUID,
  confirmed_by    UUID,
  confirmed_at    TIMESTAMPTZ,
  posted_at       TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- 约束
  CONSTRAINT chk_event_type CHECK (event_type IN ('SPEND', 'TOPUP', 'TRANSFER', 'FEE')),
  CONSTRAINT chk_event_status CHECK (event_status IN ('raw', 'pending', 'confirmed', 'posted', 'reversed'))
);

-- 索引
CREATE INDEX idx_financial_events_type ON financial_events(event_type);
CREATE INDEX idx_financial_events_status ON financial_events(event_status);
CREATE INDEX idx_financial_events_date ON financial_events(event_date);
CREATE INDEX idx_financial_events_account ON financial_events(ad_account_id);
CREATE INDEX idx_financial_events_supplier ON financial_events(supplier_id);
CREATE UNIQUE INDEX idx_financial_events_idempotency ON financial_events(idempotency_key);
```

### 2.2 字段说明

| 字段 | 类型 | 必填 | 说明 | 验证规则 |
|------|------|------|------|----------|
| id | UUID | 自动 | 主键 | 系统生成 |
| event_type | VARCHAR(20) | ✅ | 事件类型 | SPEND 固定 |
| event_status | VARCHAR(20) | 自动 | 事件状态 | 见状态机 |
| idempotency_key | VARCHAR(200) | 自动 | 幂等键 | SPEND:{account_id}:{date} |
| amount | DECIMAL(15,4) | ✅ | 净消耗金额 | > 0 |
| fee_amount | DECIMAL(15,4) | 自动 | 手续费 | = amount × fee_rate |
| gross_amount | DECIMAL(15,4) | 自动 | 含费金额 | = amount + fee_amount |
| event_date | DATE | ✅ | 事件日期 | ≤ 今天 |
| ad_account_id | INTEGER | ✅ | 广告账户ID | 外键 |
| supplier_id | INTEGER | ❌ | 供应商ID | 外键 |

### 2.3 payload 扩展字段

| 字段 | 类型 | 说明 |
|------|------|------|
| today_max | Decimal | 当日最大消耗 |
| yesterday_max | Decimal | 前日最大消耗 |
| fee_rate | Decimal | 手续费率 |
| import_row | Integer | 导入行号 |
| confirm_notes | String | 确认备注 |
| reversal_reason | String | 冲正原因 |
| reversed_by | UUID | 冲正操作人 |
| reversed_at | String | 冲正时间 |

### 2.4 关联关系

```
financial_events (event_type=SPEND)
    ├──→ teams (team_id → id) 多对一: 所属团队
    ├──→ ad_accounts (ad_account_id → id) 多对一: 广告账户
    ├──→ suppliers (supplier_id → id) 多对一: 供应商
    ├──→ projects (project_id → id) 多对一: 所属项目
    ├──→ users (created_by → id) 多对一: 创建者
    ├──→ users (confirmed_by → id) 多对一: 确认人
    └──→ ledger_entries (id → event_id) 一对多: 账本分录
```

---

## §3 API 设计

### 3.1 端点清单

**来源**: API_SOT.md v9.3 §7, `backend/routers/spend.py`

| 方法 | 端点 | 描述 | 权限 |
|------|------|------|------|
| POST | /api/v1/spend/import | Excel 导入消耗 | finance, data_operator, admin |
| POST | /api/v1/spend/events | 手动创建消耗事件 | finance, admin |
| GET | /api/v1/spend/events | 查询消耗事件列表 | finance, data_operator, admin |
| GET | /api/v1/spend/events/:id | 获取消耗事件详情 | finance, data_operator, admin |
| POST | /api/v1/spend/events/validate | 验证事件 (raw→pending) | finance, data_operator, admin |
| POST | /api/v1/spend/events/confirm | 确认事件 (pending→confirmed) | finance, admin |
| POST | /api/v1/spend/events/post | 入账事件 (confirmed→posted) | finance, admin |
| POST | /api/v1/spend/events/reverse | 冲正事件 (posted→reversed) | admin |
| POST | /api/v1/spend/events/batch-reverse | 批量冲正 | admin |
| GET | /api/v1/spend/statistics | 获取消耗统计 | finance, data_operator, admin |
| GET | /api/v1/spend/export | 导出消耗数据 | finance, data_operator, admin |
| GET | /api/v1/spend/template | 获取导入模板 | finance, data_operator, admin |

### 3.2 请求/响应格式

**Excel 导入请求**:
```typescript
// Query Parameters
interface SpendImportQuery {
  team_code: 'SZ' | 'ZZ';     // 团队代码 (必填)
  event_date?: string;         // 事件日期 (可选，默认从文件名推断)
  dry_run?: boolean;           // 试运行 (默认 false)
  skip_duplicates?: boolean;   // 跳过重复 (默认 true)
}

// File: multipart/form-data
// field name: file
// type: .xlsx, .xls
```

**手动创建请求**:
```typescript
interface SpendEventCreate {
  ad_account_id: number;       // 必填
  supplier_id: number;         // 必填
  event_date: string;          // 必填，YYYY-MM-DD
  amount: number;              // 必填，≥0，最多4位小数
  fee_amount?: number;         // 可选，默认自动计算
  currency?: string;           // 可选，默认 USD
  today_max?: number;          // 可选
  yesterday_max?: number;      // 可选
  notes?: string;              // 可选，最多500字符
}
```

**批量操作请求**:
```typescript
interface SpendEventBatchRequest {
  event_ids: string[];         // UUID 列表，1-1000 条
  notes?: string;              // 操作备注
}

interface SpendEventValidateRequest extends SpendEventBatchRequest {
  force?: boolean;             // 强制验证（忽略警告）
}

interface SpendEventPostRequest extends SpendEventBatchRequest {
  post_date?: string;          // 入账日期，默认今天
}

interface SpendEventReverseRequest {
  event_id: string;            // UUID
  reason: string;              // 冲正原因，5-500字符
}

interface SpendEventBatchReverseRequest {
  event_ids: string[];         // UUID 列表，1-100 条
  reason: string;              // 冲正原因
}
```

**导入结果响应**:
```typescript
interface SpendImportResultResponse {
  // 统计
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  duplicate_rows: number;
  imported_rows: number;
  skipped_rows: number;

  // 金额
  total_amount: number;
  total_fee: number;
  total_gross: number;

  // 错误和警告
  errors: ImportRowError[];
  warnings: ImportRowWarning[];

  // 结果
  event_ids: string[];
  file_name: string;
  team_code: string;
  import_date: string;
  dry_run: boolean;
}
```

**消耗事件响应**:
```typescript
interface SpendEventResponse {
  id: string;
  event_type: 'SPEND';
  event_status: string;

  // 来源
  source_type: string;
  source_ref: string;
  idempotency_key: string;

  // 金额
  amount: number;
  fee_amount: number;
  gross_amount: number;
  currency: string;
  event_date: string;

  // 关联实体
  team_id: string;
  team_code: string;
  supplier_id: number;
  supplier_name: string;
  ad_account_id: number;
  ad_account_name: string;
  project_id: number;
  project_name: string;

  // 扩展数据
  today_max: number;
  yesterday_max: number;
  fee_rate: number;

  // 审计
  created_by: string;
  created_by_name: string;
  confirmed_by: string;
  confirmed_by_name: string;
  confirmed_at: string;
  posted_at: string;
  created_at: string;
  updated_at: string;
}
```

### 3.3 错误码定义

**来源**: ERROR_CODES_SOT.md v2.1

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| BIZ_500 | 400 | 文件格式错误（非 Excel） |
| BIZ_501 | 400 | Excel 解析失败 |
| BIZ_502 | 400 | Excel 文件为空 |
| BIZ_503 | 409 | 重复记录（幂等键冲突） |
| BIZ_504 | 404 | 广告账户不存在 |
| BIZ_505 | 400 | 行数据格式错误 |
| BIZ_506 | 500 | 数据库插入失败 |
| BIZ_507 | 400 | 入账失败 |
| BIZ_508 | 400 | 冲正失败 |
| STATE_401 | 400 | 事件状态不是 raw |
| STATE_402 | 400 | 事件状态不是 pending |
| STATE_403 | 400 | 状态转换失败 |
| STATE_404 | 400 | 事件状态不是 confirmed |
| STATE_405 | 400 | 只能冲正已入账事件 |
| BIZ_002 | 404 | 事件不存在 |
| VALIDATION_001 | 400 | 金额必须大于 0 |
| WARN_501 | - | 重复记录已跳过（警告） |
| WARN_502 | - | 事件日期是未来日期（警告） |

### 3.4 分页/筛选规范

```yaml
分页:
  页码: 从 1 开始
  默认每页: 20 条
  最大每页: 100 条

筛选:
  event_status: 精确匹配 (raw/pending/confirmed/posted/reversed)
  team_id: 精确匹配 (UUID)
  supplier_id: 精确匹配 (Integer)
  ad_account_id: 精确匹配 (Integer)
  start_date: 日期范围开始
  end_date: 日期范围结束
  source_type: 精确匹配 (EXCEL_IMPORT/API/SYSTEM)

排序:
  默认: event_date DESC, created_at DESC
```

---

## §4 权限控制

### 4.1 角色权限矩阵 (7 角色)

**来源**: AUTH_SPEC.md v2.0, MASTER.md v4.4 §2.4

| 操作 | ceo | project_owner | finance | supervisor | pitcher | account_manager | admin |
|------|-----|---------------|---------|------------|---------|-----------------|-------|
| Excel 导入 | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| 手动创建 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 列表查询 | ✅ | ✅ (项目) | ✅ | ✅ | ✅ (账户) | ❌ | ✅ |
| 详情查看 | ✅ | ✅ (项目) | ✅ | ✅ | ✅ (账户) | ❌ | ✅ |
| 验证 (raw→pending) | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| 确认 (pending→confirmed) | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 入账 (confirmed→posted) | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 冲正 (posted→reversed) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 统计 | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| 导出 | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |

### 4.2 数据权限规则

```typescript
function canAccessSpendEvent(user: User, event: SpendEvent): boolean {
  // Admin 和 finance 可以访问所有
  if (['admin', 'finance', 'data_operator'].includes(user.role)) return true;

  // 投手只能访问自己负责账户的消耗
  if (user.role === 'media_buyer') {
    return event.buyer_id === user.id || isAccountOwner(user.id, event.ad_account_id);
  }

  // 项目负责人可以访问项目内消耗
  if (user.role === 'project_owner') {
    return isProjectOwner(user.id, event.project_id);
  }

  return false;
}
```

### 4.3 操作权限说明

| 操作 | 允许角色 | 业务逻辑 |
|------|----------|----------|
| 导入 | finance, data_operator, admin | 批量创建 raw 状态事件 |
| 验证 | finance, data_operator, admin | raw → pending，数据完整性检查 |
| 确认 | finance, admin | pending → confirmed，人工确认 |
| 入账 | finance, admin | confirmed → posted，生成账本分录 |
| 冲正 | admin | posted → reversed，生成反向分录 |

---

## §5 业务逻辑

### 5.1 状态机定义

**来源**: STATE_MACHINE.md v2.7 §6

```
┌───────────────────────────────────────────────────────────────────────────┐
│                       消耗事件状态机 (5 状态)                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌────────┐  validate   ┌──────────┐  confirm   ┌────────────┐            │
│  │  raw   │ ──────────→ │ pending  │ ─────────→ │ confirmed  │            │
│  └────────┘             └──────────┘            └─────┬──────┘            │
│     │                                                 │                   │
│     │ (Excel导入                                      │ post              │
│     │  或手动创建)                                    ▼                   │
│                                              ┌────────────┐               │
│                                              │   posted   │               │
│                                              └─────┬──────┘               │
│                                                    │                      │
│                                                    │ reverse              │
│                                                    ▼                      │
│                                              ┌────────────┐               │
│                                              │  reversed  │ (终态)        │
│                                              └────────────┘               │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

**状态转换表**:

| 当前状态 | 目标状态 | 触发条件 | 操作者 |
|----------|----------|----------|--------|
| raw | pending | 验证通过 | finance, data_operator, admin |
| pending | confirmed | 人工确认 | finance, admin |
| confirmed | posted | 入账（生成分录） | finance, admin |
| posted | reversed | 冲正（生成反向分录） | admin |
| reversed | - | 终态 | - |

### 5.2 幂等键规则

```python
# SPEND 事件幂等键格式
idempotency_key = f"SPEND:{ad_account_id}:{event_date}"

# 示例
# SPEND:12345:2024-12-23
```

**幂等性保证**:
- 同一账户同一日期只能有一条 SPEND 事件
- 重复导入自动跳过或报错

### 5.3 手续费计算

```python
# 手续费计算公式
fee_rate = supplier.fee_rate or Decimal("0")
fee_amount = amount * fee_rate
gross_amount = amount + fee_amount

# 示例: amount=1000, fee_rate=0.05
# fee_amount = 1000 × 0.05 = 50
# gross_amount = 1000 + 50 = 1050
```

### 5.4 账本分录规则

**来源**: LEDGER_SOT.md v1.2 §3

```yaml
入账 (post):
  生成分录:
    - SUPPLIER 借方: gross_amount (供应商成本)
    - ACCOUNT 借方: gross_amount (账户消耗)

冲正 (reverse):
  生成分录:
    - SUPPLIER 贷方: gross_amount (冲正供应商成本)
    - ACCOUNT 贷方: gross_amount (冲正账户消耗)

分录幂等键:
  - 入账: {event.idempotency_key}:SUPPLIER, {event.idempotency_key}:ACCOUNT
  - 冲正: {event.idempotency_key}:SUPPLIER:REV, {event.idempotency_key}:ACCOUNT:REV
```

### 5.5 Excel 导入规则

```yaml
支持的列名别名:
  account_id: [账户ID, 账户id, account_id, AccountID, 账户]
  account_name: [账户名称, 账户名, account_name]
  today_max: [今日最大消耗, 今日消耗, today_max, 当日累计]
  yesterday_max: [昨日最大消耗, 昨日消耗, yesterday_max, 前日累计]
  spend: [消耗, 消耗金额, spend, 花费]
  event_date: [日期, 消耗日期, event_date, 报告日期]

消耗计算:
  - 优先使用 spend 列
  - 如无 spend 列: spend = today_max - yesterday_max

日期推断优先级:
  1. 请求参数 event_date
  2. 文件名中的日期 (如 消耗_20241223.xlsx)
  3. 数据中的日期列
  4. 今天

跳过规则:
  - 空行
  - 消耗 ≤ 0
  - 重复记录 (skip_duplicates=true 时)
```

### 5.6 Phase 1 规则

```yaml
Phase 1 规则 (照亮阶段):
  ❌ 禁止: 自动阻断、自动拒绝导入
  ✅ 允许: 记录警告、标记异常、人工确认

  异常处理:
    - 未来日期: 警告但不阻断
    - 零消耗: 跳过（警告）
    - 账户不存在: 报错，该行失败
    - 重复记录: 根据 skip_duplicates 参数处理
```

---

## §6 前后端接口契约

### 6.1 字段映射

| 后端字段 (snake_case) | 前端字段 (camelCase) | 说明 |
|----------------------|---------------------|------|
| event_type | eventType | 固定 SPEND |
| event_status | eventStatus | 5 状态之一 |
| event_date | eventDate | YYYY-MM-DD |
| ad_account_id | adAccountId | 整数 |
| ad_account_name | adAccountName | 字符串 |
| supplier_id | supplierId | 整数 |
| supplier_name | supplierName | 字符串 |
| fee_amount | feeAmount | 数字 |
| gross_amount | grossAmount | 数字 |
| idempotency_key | idempotencyKey | 字符串 |
| source_type | sourceType | EXCEL_IMPORT/API |
| source_ref | sourceRef | 文件名等 |
| today_max | todayMax | 数字 |
| yesterday_max | yesterdayMax | 数字 |
| created_by | createdBy | UUID |
| created_by_name | createdByName | 字符串 |
| confirmed_by | confirmedBy | UUID |
| confirmed_at | confirmedAt | ISO 8601 |
| posted_at | postedAt | ISO 8601 |

### 6.2 枚举值对照

```typescript
// 事件状态
type EventStatus = 'raw' | 'pending' | 'confirmed' | 'posted' | 'reversed';

const EVENT_STATUS_LABELS: Record<EventStatus, string> = {
  raw: '原始',
  pending: '待确认',
  confirmed: '已确认',
  posted: '已入账',
  reversed: '已冲正',
};

const EVENT_STATUS_COLORS: Record<EventStatus, string> = {
  raw: 'gray',
  pending: 'orange',
  confirmed: 'blue',
  posted: 'green',
  reversed: 'red',
};

// 来源类型
type SourceType = 'EXCEL_IMPORT' | 'API' | 'SYSTEM';

// 团队代码
type TeamCode = 'SZ' | 'ZZ';
```

### 6.3 时区/格式约定

```yaml
时间格式:
  日期: YYYY-MM-DD
  时间戳: ISO 8601 (2024-12-23T10:00:00Z)

时区:
  存储: UTC
  传输: UTC
  显示: 前端转换

数字格式:
  金额: 数字，最多4位小数
  费率: 数字，如 0.05 表示 5%

导出格式:
  xlsx: Excel 2007+
  csv: UTF-8 with BOM
```

---

## §7 测试要点

### 7.1 单元测试

```python
describe('SpendImportService', () => {
    describe('import_from_excel', () => {
        it('应成功导入有效 Excel', async () => {
            result = service.import_from_excel(
                file_content, 'test.xlsx',
                SpendImportRequest(team_code='SZ'),
                user_id
            )
            assert result.imported_rows > 0
            assert result.total_amount > 0
        });

        it('应拒绝非 Excel 文件 (BIZ_500)', async () => {
            with pytest.raises(BusinessLogicError) as e:
                service.import_from_excel(pdf_content, 'test.pdf', ...)
            assert e.error_code == 'BIZ_500'
        });

        it('应跳过重复记录', async () => {
            # 第一次导入
            service.import_from_excel(...)
            # 第二次导入相同数据
            result = service.import_from_excel(...)
            assert result.duplicate_rows > 0
            assert result.imported_rows == 0
        });

        it('应处理账户不存在 (BIZ_504)', async () => {
            result = service.import_from_excel(invalid_account_excel, ...)
            assert len(result.errors) > 0
            assert result.errors[0].error_code == 'BIZ_504'
        });
    });

    describe('状态转换', () => {
        it('raw → pending 允许', async () => {
            result = service.validate_events([raw_event.id], user_id)
            assert result.success == True
            assert db.get(raw_event.id).event_status == 'pending'
        });

        it('pending → confirmed 允许', async () => {
            result = service.confirm_events([pending_event.id], user_id)
            assert result.success == True
        });

        it('posted 才能冲正 (STATE_405)', async () => {
            with pytest.raises(BusinessLogicError) as e:
                service.reverse_event(confirmed_event.id, 'reason', user_id)
            assert e.error_code == 'STATE_405'
        });
    });

    describe('入账分录', () => {
        it('应生成正确的账本分录', async () => {
            result = service.post_events([confirmed_event.id], user_id)
            assert result.ledger_entries_created == 2  # SUPPLIER + ACCOUNT
        });
    });
});
```

### 7.2 集成测试

```python
describe('POST /api/v1/spend/import', () => {
    it('finance 可以导入', async () => {
        response = await client.post(
            '/api/v1/spend/import',
            files={'file': ('test.xlsx', excel_content)},
            params={'team_code': 'SZ'},
            headers={'Authorization': f'Bearer {finance_token}'}
        )
        assert response.status_code == 200
        assert response.json()['data']['imported_rows'] > 0
    });

    it('pitcher 不能导入', async () => {
        response = await client.post(
            '/api/v1/spend/import',
            files={'file': ('test.xlsx', excel_content)},
            params={'team_code': 'SZ'},
            headers={'Authorization': f'Bearer {pitcher_token}'}
        )
        assert response.status_code == 403
    });
});

describe('POST /api/v1/spend/events/reverse', () => {
    it('仅 admin 可以冲正', async () => {
        # finance 尝试冲正
        response = await client.post(
            '/api/v1/spend/events/reverse',
            json={'event_id': posted_event.id, 'reason': 'test'},
            headers={'Authorization': f'Bearer {finance_token}'}
        )
        assert response.status_code == 403

        # admin 冲正
        response = await client.post(
            '/api/v1/spend/events/reverse',
            json={'event_id': posted_event.id, 'reason': 'test reversal'},
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
    });
});
```

### 7.3 权限测试矩阵

```python
test_cases = [
    # [角色, 操作, 预期结果]
    ('admin', 'import', 200),
    ('admin', 'validate', 200),
    ('admin', 'confirm', 200),
    ('admin', 'post', 200),
    ('admin', 'reverse', 200),
    ('finance', 'import', 200),
    ('finance', 'validate', 200),
    ('finance', 'confirm', 200),
    ('finance', 'post', 200),
    ('finance', 'reverse', 403),
    ('data_operator', 'import', 200),
    ('data_operator', 'validate', 200),
    ('data_operator', 'confirm', 403),
    ('data_operator', 'post', 403),
    ('media_buyer', 'import', 403),
    ('media_buyer', 'list_own', 200),
]

@pytest.mark.parametrize('role,action,expected', test_cases)
def test_permissions(role, action, expected):
    response = execute_action(role, action)
    assert response.status_code == expected
```

---

## §8 性能要求

### 8.1 响应时间要求

| API | 目标 | 最大容忍 |
|-----|------|----------|
| Excel 导入 (1000行) | < 5s | < 10s |
| 列表查询 | < 200ms | < 500ms |
| 详情查询 | < 100ms | < 300ms |
| 批量验证 (100条) | < 1s | < 3s |
| 批量入账 (100条) | < 2s | < 5s |
| 统计查询 | < 500ms | < 1s |
| 导出 (10000条) | < 10s | < 30s |

### 8.2 索引要求

必须建立的索引：
- 事件类型 + 状态复合索引
- 事件日期索引
- 账户ID索引
- 供应商ID索引
- 幂等键唯一索引

### 8.3 批量操作限制

| 操作 | 单次上限 | 说明 |
|------|----------|------|
| Excel 导入 | 10000 行 | 超出需分文件 |
| 批量验证/确认/入账 | 1000 条 | 超出需分批 |
| 批量冲正 | 100 条 | 高风险操作限制更严 |
| 导出 | 10000 条 | 超出走异步 |

---

## §9 安全规范

### 9.1 认证授权

- 所有 API 需要 JWT Token
- 每个 API 校验角色权限
- 冲正操作仅限 admin

### 9.2 输入验证

- [x] 使用 Pydantic 验证所有输入
- [x] 金额字段最多 4 位小数
- [x] 金额上限 10,000,000
- [x] 日期不能是未来日期
- [x] 文件类型验证 (.xlsx, .xls)
- [x] 文件大小限制 (建议 10MB)

### 9.3 审计日志

必须记录以下操作：

| 操作类型 | 记录内容 |
|----------|----------|
| 导入 | 操作人、时间、文件名、导入行数、金额统计 |
| 验证 | 操作人、时间、事件ID列表、成功/失败数 |
| 确认 | 操作人、时间、事件ID列表、备注 |
| 入账 | 操作人、时间、事件ID列表、分录数、金额 |
| 冲正 | 操作人、时间、事件ID、原金额、冲正原因 |

---

## 附录: AI 代码工厂禁止行为清单

### A.1 禁止行为

| 禁止行为 | 正确做法 | 检查方式 |
|---------|---------|---------|
| 自定义事件状态 | 使用 5 个标准状态 | 枚举检查 |
| 跳过状态机流转 | 按顺序 raw→pending→confirmed→posted | 代码审查 |
| 非 admin 执行冲正 | 权限检查 admin | 权限测试 |
| 直接修改账户余额 | 通过 ledger_entries | LEDGER_SOT 规则 |
| 自定义错误码 | 使用 BIZ_500-599 | grep 检查 |
| 跳过幂等键检查 | 必须生成并检查 | 代码审查 |
| Phase 1 自动阻断 | 仅记录警告 | 逻辑审查 |

### A.2 SoT 追溯验证 Checklist

生成代码后必须验证：
- [ ] 所有状态值来自 STATE_MACHINE.md (5 个)
- [ ] 所有错误码来自 ERROR_CODES_SOT.md (BIZ_500-599)
- [ ] 入账分录规则来自 LEDGER_SOT.md
- [ ] 幂等键格式正确: SPEND:{account_id}:{date}
- [ ] 金额使用 Decimal 类型
- [ ] 冲正仅限 admin

---

## 源码位置

| 层 | 文件路径 |
|----|---------|
| Model | `backend/models/finance/financial_event.py` |
| Service | `backend/services/spend_import_service.py` |
| Router | `backend/routers/spend.py` |
| Schema | `backend/schemas/spend.py` |
| Test | `backend/tests/services/test_spend_import_service.py` |
| Test | `backend/tests/routers/test_spend_router.py` |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-23 | 初始版本，基于现有代码提取规格 |

---

**维护者**: AI 广告代投系统开发团队
**关联文档**: C3-spend-detail.md (前端规格), LEDGER_SOT.md v1.2
