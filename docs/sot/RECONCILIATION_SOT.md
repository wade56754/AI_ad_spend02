# RECONCILIATION_SOT.md · 对账模块唯一真相源

> **版本**: v2.0
> **status**: active
> **owner**: wade
> **last_reviewed**: 2025-12-26
> **更新日期**: 2025-12-26
> **维护团队**: 系统架构团队
> **定位**: 对账模块（Channel Reconciliation）唯一真相源（Single Source of Truth），定义对账业务模型、核心流程、状态机、并发控制、账本影响等全部规则。
> **互锁 SoT**:
> - 角色定义 → `MASTER.md` v4.4 §2.4 (7 角色体系)
> - 数据结构 → `DATA_SCHEMA.md` v5.2
> - 状态机 → `STATE_MACHINE.md` v2.6
> - 业务规则 → `BUSINESS_RULES.md` v3.2 (BR-RECON)
> - 账本逻辑 → `LEDGER_SOT.md` v1.1
> - 错误码 → `ERROR_CODES_SOT.md` v2.1
> - 权限控制 → `AUTH_SPEC.md` v2.0
> - RLS策略 → `RLS_POLICIES_SOT.md` v2.1 (规划中未启用)
> - 架构方案 → `RECONCILIATION_CONTROL_CENTER_ARCHITECTURE.md` v2.1

---

## 1. 文档定位 (Document Scope)

### 1.1 本文档职责

本文档是**对账模块（Reconciliation）唯一真相源**，负责定义：

1. **对账业务模型**: 对账批次（Batch）→ 明细（Detail）→ 调整（Adjustment）的层次结构
2. **对账核心流程**: 创建批次 → 差异计算 → 审核确认 → 生成报告的完整流程
3. **状态机规则**: draft/pending_review/approved/needs_adjustment/completed 状态流转（引用 STATE_MACHINE.md v2.6）
4. **差异计算逻辑**: `difference = our_total_spend - supplier_total_spend`
5. **双账本影响**: 对账不直接修改 PROJECT/SUPPLIER 账本余额，但可生成 `manual_entry` 调整记录
6. **并发控制**: 基于 `expected_version` 的乐观锁机制
7. **幂等性保证**: `(supplier_id, channel_id, period_start, period_end)` 唯一性约束
8. **错误码映射**: E-RECON-001/002/003/004/005
9. **权限控制**: 7 角色权限矩阵与 RLS 策略引用（对齐 MASTER.md v4.4）
10. **事务边界**: 对账批次创建、明细计算、审批操作的事务范围

### 1.2 不属于本文档职责

❌ 数据库字段定义（查阅 DATA_SCHEMA.md）
❌ 通用业务规则（查阅 BUSINESS_RULES.md）
❌ 双账本记账规则（查阅 LEDGER_SOT.md）
❌ 错误码全局定义（查阅 ERROR_CODES_SOT.md）
❌ 角色与权限定义（查阅 AUTH_SPEC.md）
❌ RLS 策略 SQL（查阅 RLS_POLICIES_SOT.md）

---

## 2. 模块边界 (Module Boundary)

### 2.1 对账模块定义

**对账 (Reconciliation)** = 比较**我方记录的总消耗**（our_total_spend，来自 daily_reports.real_spend 汇总）与**供应商提供的总消耗**（supplier_total_spend，来自供应商对账单）之间的差异。

**核心业务目标**:
- 发现账务差异（正差/负差/零差）
- 识别差异原因（数据录入误差、供应商计费规则、漏记或重复记录）
- 生成调整建议（increase/decrease/writeoff）
- 通过审批流确认差异处理方案
- 生成对账报告供财务审计

**对账周期**: 通常按**月度**或**周期**进行，由 `period_start` 和 `period_end` 定义。

### 2.2 对账模块的输入与输出

| 维度 | 说明 |
|-----|------|
| **输入来源** | 1. 我方消耗数据: `daily_reports.real_spend` 按 `supplier_id + channel_id + period` 汇总<br>2. 供应商对账单: 外部导入的 `supplier_total_spend` 金额 |
| **计算结果** | `difference = our_total_spend - supplier_total_spend`<br>`difference_rate = (difference / supplier_total_spend) × 100%` |
| **输出结果** | 1. 对账批次记录 (reconciliation_batches)<br>2. 差异明细 (reconciliation_details)<br>3. 调整建议 (reconciliation_adjustments)<br>4. 对账报告 (reconciliation_reports) |
| **账本影响** | 不直接修改 `ledger_entries`，但经 finance/admin 审批后可能触发 `manual_entry` 类型的红冲或补录 |

### 2.3 与其他模块的关系

```
reconciliation_batches (对账批次)
    ↓ 关联供应商
suppliers (供应商主数据)
    ↓ 关联渠道
channels (广告平台渠道)
    ↓ 关联消耗数据
daily_reports (日报表, real_spend汇总)
    ↓ 可能触发调整
ledger_entries (账本, manual_entry红冲/补录)
```

---

## 3. 数据模型 SoT (Data Model Mapping)

### 3.1 对账相关表映射

本模块涉及以下 4 张表（定义于 `DATA_SCHEMA.md` v5.1 第 3.5 节）:

#### 3.1.1 reconciliation_batches (对账批次表)

| 字段 | 类型 | 约束 | 说明 |
|-----|------|------|------|
| `id` | BIGSERIAL | PK | 批次ID |
| `batch_no` | VARCHAR(50) | UNIQUE, NOT NULL | 批次编号，格式如 `RECON-202501-001` |
| `supplier_id` | UUID | FK → suppliers.id, NOT NULL | 所属供应商ID |
| `channel_id` | UUID | FK → channels.id, 可空 | 所属渠道ID（可为空表示全渠道对账） |
| `status` | VARCHAR(20) | NOT NULL | 对账状态，参考STATE_MACHINE.md v2.6，合法值: `draft/pending_review/approved/needs_adjustment/completed` |
| `period_start` | DATE | NOT NULL | 对账周期开始日期 |
| `period_end` | DATE | NOT NULL | 对账周期结束日期 |
| `our_total_spend` | DECIMAL(15,2) | DEFAULT 0.00 | 我方记录的总消耗（real_spend汇总） |
| `supplier_total_spend` | DECIMAL(15,2) | DEFAULT 0.00 | 供应商提供的总消耗 |
| `difference` | DECIMAL(15,2) | DEFAULT 0.00 | 差异金额 = our_total_spend - supplier_total_spend |
| `difference_rate` | DECIMAL(12,4) | 可空 | 差异率 = (difference / supplier_total_spend) × 100% |
| `source` | VARCHAR(50) | 可空 | 数据来源（如 `manual`, `api_import`, `excel_import`） |
| `created_by` | UUID | FK → users.id | 创建人 |
| `approved_by` | UUID | FK → users.id, 可空 | 审批人（finance/admin） |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |
| `version` | INTEGER | DEFAULT 1 | 乐观锁版本号 |

**约束**:
- `UNIQUE (supplier_id, channel_id, period_start, period_end)` - 防止重复创建同周期对账
- `CHECK (period_end >= period_start)` - 周期合法性
- `CHECK (status IN ('draft', 'pending_review', 'approved', 'needs_adjustment', 'completed'))` - 状态枚举（引用STATE_MACHINE.md v2.6）

#### 3.1.2 reconciliation_details (对账明细表)

| 字段 | 类型 | 约束 | 说明 |
|-----|------|------|------|
| `id` | BIGSERIAL | PK | 明细ID |
| `batch_id` | BIGINT | FK → reconciliation_batches.id, ON DELETE CASCADE | 所属批次 |
| `ad_account_id` | BIGINT | FK → ad_accounts.id, 可空 | 关联广告账户（可空表示渠道级汇总） |
| `report_date` | DATE | 可空 | 对账日期（可空表示周期汇总） |
| `system_spend` | DECIMAL(15,2) | DEFAULT 0.00 | 系统记录的消耗（daily_reports.real_spend） |
| `external_spend` | DECIMAL(15,2) | DEFAULT 0.00 | 供应商提供的消耗 |
| `difference_amount` | DECIMAL(15,2) | DEFAULT 0.00 | 差异金额 = system_spend - external_spend |
| `status` | VARCHAR(20) | NOT NULL | 明细状态，参考STATE_MACHINE.md v2.6，合法值: `pending/confirmed/adjusted` |
| `notes` | TEXT | 可空 | 备注说明 |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |

#### 3.1.3 reconciliation_adjustments (对账调整表)

| 字段 | 类型 | 约束 | 说明 |
|-----|------|------|------|
| `id` | BIGSERIAL | PK | 调整ID |
| `detail_id` | BIGINT | FK → reconciliation_details.id, ON DELETE CASCADE | 关联明细 |
| `adjustment_type` | VARCHAR(20) | NOT NULL | 调整类型，固定枚举: `increase/decrease/writeoff` |
| `amount` | DECIMAL(15,2) | NOT NULL | 调整金额（绝对值） |
| `reason` | TEXT | NOT NULL | 调整原因说明 |
| `created_by` | UUID | FK → users.id | 创建人 |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |

**调整类型说明**:
- `increase`: 我方少计，需增加消耗记录
- `decrease`: 我方多计，需减少消耗记录
- `writeoff`: 差异金额较小（如 <10元），直接核销

#### 3.1.4 reconciliation_reports (对账报告表)

| 字段 | 类型 | 约束 | 说明 |
|-----|------|------|------|
| `id` | BIGSERIAL | PK | 报告ID |
| `batch_id` | BIGINT | FK → reconciliation_batches.id, ON DELETE CASCADE | 关联批次 |
| `generated_at` | TIMESTAMPTZ | DEFAULT NOW() | 生成时间 |
| `generated_by` | UUID | FK → users.id | 生成人 |
| `report_url` | TEXT | 可空 | 报告文件URL（PDF/Excel） |
| `metrics` | JSONB | DEFAULT '{}' | 汇总指标（总差异金额、差异率、调整笔数等） |

### 3.2 关联表引用

对账模块还需引用以下表（无需修改）:

| 表名 | 引用关系 | 用途 |
|-----|---------|------|
| `suppliers` | `reconciliation_batches.supplier_id` FK | 获取供应商基本信息 |
| `channels` | `reconciliation_batches.channel_id` FK | 获取渠道信息 |
| `daily_reports` | 间接引用 | 汇总 `real_spend` 计算 `our_total_spend` |
| `ledger_entries` | 间接影响 | 对账审批后可能生成 `manual_entry` 调整 |
| `users` | FK 关联 | 创建人、审批人信息 |

---

## 4. 核心对账流程 (Core Reconciliation Flow)

### 4.1 标准对账流程

```
[1. 创建对账批次]
    ↓ (data_operator/finance)
    创建 reconciliation_batches 记录
    状态: draft
    自动计算: our_total_spend = SUM(daily_reports.real_spend WHERE supplier_id=X AND period IN [start, end])
    手动输入: supplier_total_spend (来自供应商对账单)
    自动计算: difference = our_total_spend - supplier_total_spend
    ↓
[2. 差异分析]
    ↓ (data_operator)
    创建 reconciliation_details 记录（按账户/日期拆分明细）
    system_spend vs external_spend 逐笔比对
    标记 difference_amount != 0 的明细为 pending
    ↓
[3. 提交审核]
    ↓ (data_operator)
    状态流转: draft → pending_review
    触发通知: 通知 finance/admin 审核
    ↓
[4. 财务审批]
    ↓ (finance/admin)
    审核差异明细
    - 若差异可接受 → approved
    - 若需调整 → needs_adjustment (创建 reconciliation_adjustments 记录)
    ↓
[5. 差异调整 (可选)]
    ↓ (finance/admin)
    基于 adjustment_type 生成账本调整:
    - increase: 生成 ledger_entries (entry_type=COST, 补录消耗)
    - decrease: 生成 ledger_entries (entry_type=REVERSAL, 红冲多计)
    - writeoff: 仅记录调整，不影响账本
    ↓
[6. 完成对账]
    ↓ (finance/admin)
    状态流转: approved → completed
    生成 reconciliation_reports 记录
    锁定批次，禁止修改
```

### 4.2 流程角色权限（对齐 MASTER.md v4.4 §2.4 七角色）

| 步骤 | 允许角色 | 操作 | 状态变化 |
|-----|---------|------|---------|
| 创建批次 | finance, account_manager, admin | POST /api/v1/reconciliation/batches | `null → draft` |
| 提交审核 | finance, account_manager, admin | POST /api/v1/reconciliation/batches/{id}/submit | `draft → pending_review` |
| 审批通过 | finance, admin | POST /api/v1/reconciliation/batches/{id}/approve | `pending_review → approved` |
| 打回调整 | finance, admin | POST /api/v1/reconciliation/batches/{id}/reject | `pending_review → needs_adjustment` |
| 重新审批 | finance, admin | POST /api/v1/reconciliation/batches/{id}/approve | `needs_adjustment → approved` |
| 完成对账 | finance, admin | POST /api/v1/reconciliation/batches/{id}/complete | `approved → completed` |

**角色说明**（7 角色体系）:
| 角色ID | 中文名 | 对账模块职责 |
|--------|-------|-------------|
| ceo | 老板 | 查看对账概览（只读） |
| project_owner | 项目负责人 | 查看自己项目的对账结果 |
| finance | 财务 | 创建/审批/完成对账，处理差异 |
| supervisor | 主管 | 查看团队对账状态 |
| pitcher | 投手 | 无对账模块权限 |
| account_manager | 户管 | 创建对账批次，录入快照 |
| admin | 管理员 | 全部权限 |

### 4.3 API 端点映射

| 端点 | 方法 | 说明 | 引用文档 |
|-----|------|------|---------|
| `/api/v1/reconciliation/batches` | GET | 获取对账批次列表 | 由API_SOT.md定义 |
| `/api/v1/reconciliation/batches` | POST | 创建对账批次 | 由API_SOT.md定义 |
| `/api/v1/reconciliation/batches/{batch_id}` | GET | 获取批次详情 | 由API_SOT.md定义 |
| `/api/v1/reconciliation/batches/{batch_id}/confirm` | POST | 确认对账结果 | 由API_SOT.md定义 |

---

## 5. 状态机 (State Machine)

### 5.1 对账批次状态机

**引用**: `STATE_MACHINE.md` v2.6 - reconciliation_batches.status

**状态枚举** (`reconciliation_batches.status`):

| 状态值 | 中文名称 | 说明 | 是否终态 |
|-------|---------|------|---------|
| `draft` | 草稿 | 初始状态，可编辑 | ❌ |
| `pending_review` | 待审核 | 已提交，等待 finance/admin 审核 | ❌ |
| `approved` | 已批准 | 审核通过，准备完成 | ❌ |
| `needs_adjustment` | 需调整 | 发现差异需调整 | ❌ |
| `completed` | 已完成 | 对账完成，批次锁定 | ✅ |

**状态流转规则**:
```
draft → pending_review → approved → completed
                        ↓
                   needs_adjustment → approved → completed
```

- 按STATE_MACHINE.md v2.6定义执行
- 终态 `completed` 禁止回退（仅 admin 可红冲后重建）

### 5.2 对账明细状态机

**状态枚举** (`reconciliation_details.status`):

| 状态值 | 中文名称 | 说明 |
|-------|---------|------|
| `pending` | 待确认 | 初始状态，差异待审核 |
| `confirmed` | 已确认 | 差异已确认，无需调整 |
| `adjusted` | 已调整 | 已创建调整记录并执行 |

**流转规则**:
```python
DETAIL_STATUS_TRANSITIONS = {
    "pending": ["confirmed", "adjusted"],
    "confirmed": ["adjusted"],  # 后续发现需调整
    "adjusted": []  # 终态
}
```

---

## 6. 并发控制 (Concurrency Control)

### 6.1 乐观锁机制

对账批次修改采用**乐观锁**（Optimistic Locking），基于 `version` 字段:

**更新逻辑**:
1. 更新批次时检查 `version = expected_version`
2. 若版本号匹配,则更新 `status`, `version = version + 1`, `updated_at = NOW()`
3. 若版本号不匹配(affected_rows = 0),抛出 `STATE_409` 并发冲突错误

**错误码**: `STATE_409` (并发冲突)

### 6.2 审批串行化

**规则**: 同一批次同时只能有一个审批操作进行，防止并发审批冲突。

**实现**: 使用 `SELECT FOR UPDATE` 行锁

**审批流程**:
1. 开始事务
2. 使用 `FOR UPDATE` 锁定批次记录
3. 检查状态是否为 `pending` (若不是则抛出 `E-RECON-003`)
4. 更新状态为 `reviewing` 或 `closed`, 设置 `approved_by`, `version = version + 1`
5. 提交事务

---

## 7. 业务规则 SoT (Business Rules)

### 7.1 核心业务规则

**引用**: `BUSINESS_RULES.md` v3.1 - BR-RECON规则

| 规则编号 | 规则名称 | 详细约束 |
|---------|---------|---------|
| **BR-RECON-001** | 对账批次创建约束 | 1. `(supplier_id, channel_id, period_start, period_end)` 必须唯一<br>2. `period_end >= period_start`<br>3. 创建人必须是 data_operator/finance/admin |
| **BR-RECON-002** | 对账周期合法性 | 1. period_end 不得晚于当前日期<br>2. 周期范围不得超过 365 天 |
| **BR-RECON-003** | 差异处理规则 | 1. `difference` 绝对值 < 10元 → 建议 writeoff<br>2. `difference` > 0 → 我方多计，建议 decrease<br>3. `difference` < 0 → 我方少计，建议 increase |
| **BR-RECON-004** | 审批职责分离 | 1. approved_by 必须是 finance/admin<br>2. approved_by != created_by（SOD原则） |
| **BR-RECON-005** | 终态保护规则 | 1. `completed` 状态批次禁止修改（仅 admin 可红冲重建）<br>2. `completed` 状态批次禁止删除 |

### 7.2 业务计算公式

**差异计算**:
```
difference = our_total_spend - supplier_total_spend
```

**差异率计算**:
```
difference_rate = (difference / supplier_total_spend) × 100%  (当supplier_total_spend ≠ 0时)
```

**我方总消耗计算**:
- 从 `daily_reports` 表汇总 `real_spend`
- 筛选条件: `supplier_id` 匹配, `channel_id` 匹配(可选), 日期在 `[period_start, period_end]` 内
- **关键约束**: 仅计入 `status = 'final_locked'` 的日报消耗（确保计费数据稳定）

**其他约束**:
- `supplier_total_spend` 必须 > 0（防止除零错误）
- `difference` 可为正（我方多计）、负（我方少计）、零（完全一致）

---

## 8. 差异计算 (Difference Calculation)

### 8.1 差异计算逻辑

**输入参数**:
- `our_spend`: 我方记录的总消耗
- `supplier_spend`: 供应商提供的总消耗

**计算步骤**:
1. 计算差异: `difference = our_spend - supplier_spend`
2. 计算差异率: `difference_rate = (difference / supplier_spend) × 100%` (当supplier_spend ≠ 0时)
3. 生成调整建议:
   - `|difference| < 10.00` → `recommendation = "writeoff"`
   - `difference > 0` → `recommendation = "decrease"` (我方多计)
   - `difference < 0` → `recommendation = "increase"` (我方少计)

**返回结果**:
- `difference`: 差异金额 (DECIMAL)
- `difference_rate`: 差异率百分比 (DECIMAL, 保留2位小数)
- `recommendation`: 调整建议 (writeoff/decrease/increase)

### 8.2 明细级差异计算

对于明细表 `reconciliation_details`，差异按**账户+日期**维度拆分:

```sql
-- 创建明细记录（按账户拆分）
INSERT INTO reconciliation_details (batch_id, ad_account_id, report_date, system_spend, external_spend, difference_amount, status)
SELECT
    :batch_id,
    dr.ad_account_id,
    dr.report_date,
    dr.real_spend AS system_spend,
    :external_spend / :days_count AS external_spend,  -- 引用BUSINESS_RULES.md定义的分摊规则
    dr.real_spend - (:external_spend / :days_count) AS difference_amount,
    'pending' AS status
FROM daily_reports dr
JOIN ad_accounts aa ON dr.ad_account_id = aa.id
WHERE aa.supplier_id = :supplier_id
  AND dr.report_date BETWEEN :period_start AND :period_end
  AND dr.status = 'final_locked';
```

**说明**:
- `system_spend`: 直接取 `daily_reports.real_spend`
- `external_spend`: 供应商总消耗按天数平均分摊（具体规则由BUSINESS_RULES.md定义）
- `difference_amount`: 逐笔计算差异

---

## 9. 双账本影响 (Dual Ledger Impact)

### 9.1 对账与账本的关系

**引用**: `LEDGER_SOT.md` v1.1 - Ledger Entry Types章节

**关键原则**:
1. 对账模块**不直接修改** `ledger_entries` 表
2. 对账模块只**生成调整建议**（`reconciliation_adjustments`）
3. 经 finance/admin 审批后，**间接触发**账本调整记录

### 9.2 调整类型与账本映射

| adjustment_type | 账本影响 | ledger_entries 记录 |
|----------------|---------|-------------------|
| `increase` | 补录消耗（我方少计） | `ledger_type=SUPPLIER`, `entry_type=COST`, `amount=正数`, `notes="对账补录"` |
| `decrease` | 红冲消耗（我方多计） | `ledger_type=SUPPLIER`, `entry_type=REVERSAL`, `amount=负数`, `notes="对账红冲"` |
| `writeoff` | 无账本影响 | 不生成 ledger_entries，仅记录调整 |

### 9.3 调整执行逻辑

**执行流程**:
1. **writeoff 类型**: 不影响账本,仅更新明细状态为 `adjusted`
2. **increase 类型**: 创建 `ledger_type=SUPPLIER`, `entry_type=COST` 的正数记录
3. **decrease 类型**: 创建 `ledger_type=SUPPLIER`, `entry_type=REVERSAL` 的负数记录
4. **批量执行**: 同一批次的所有调整在同一事务内完成
5. **状态更新**: 所有调整执行完成后,批次状态更新为 `completed`

**事务边界**: 由LEDGER_SOT.md和本文档第13章定义

---

## 10. 幂等性保证 (Idempotency)

### 10.1 批次唯一性约束

**数据库约束**:
```sql
ALTER TABLE reconciliation_batches
ADD CONSTRAINT uq_reconciliation_batch_unique
UNIQUE (supplier_id, channel_id, period_start, period_end);
```

**业务逻辑校验**:
- 检查是否存在相同 `(supplier_id, channel_id, period_start, period_end)` 的批次
- 若存在则抛出 `BIZ_003` 错误码 (资源已存在)
- 若不存在则创建新批次

### 10.2 调整记录幂等性

**规则**: 同一明细不允许重复创建相同类型的调整记录。

**幂等逻辑**:
- 检查是否存在相同 `(detail_id, adjustment_type)` 的调整
- 若存在则返回已有记录(幂等)
- 若不存在则创建新调整

---

## 11. 错误码引用 (Error Code Reference)

**引用**: `ERROR_CODES_SOT.md` v2.1

### 11.1 对账模块错误码

| 错误码 | 消息 | HTTP | 触发场景 |
|--------|------|------|----------|
| `E-RECON-001` | 对账批次已存在 | 409 | 违反 `(supplier_id, channel_id, period)` 唯一约束 |
| `E-RECON-002` | 对账周期无效 | 400 | `period_end < period_start` 或超过365天 |
| `E-RECON-003` | 非法状态流转 | 400 | 不在白名单的状态流转（如 `draft → completed`） |
| `E-RECON-004` | 审批人与创建人相同 | 403 | 违反职责分离原则（SOD） |
| `E-RECON-005` | 终态批次禁止修改 | 403 | 尝试修改 `completed` 状态的批次 |

### 11.2 通用错误码引用

| 错误码 | 说明 | 使用场景 |
|--------|------|----------|
| `BIZ_002` | 资源不存在 | 查询不存在的批次/明细 |
| `BIZ_100` | 金额无效 | `supplier_total_spend <= 0` |
| `AUTH_500` | 权限不足 | 非 finance/admin 尝试审批 |
| `STATE_400` | 非法状态流转 | 违反状态机规则 |
| `STATE_402` | 终态非法回退 | 尝试从 `completed` 回退到 `draft` |
| `STATE_409` | 并发冲突 | 乐观锁版本号不匹配 |

---

## 12. 权限与 RLS (Permissions & RLS)

### 12.1 角色权限矩阵（7 角色体系）

**引用**: `MASTER.md` v4.4 §2.4 + `AUTH_SPEC.md` v2.0 第 3 章

| 操作 | ceo | project_owner | finance | supervisor | pitcher | account_manager | admin |
|-----|-----|--------------|---------|------------|---------|-----------------|-------|
| 查看对账批次 | ✅全局 | ✅自己项目 | ✅全局 | ✅团队 | ❌ | ✅全局 | ✅全局 |
| 创建对账批次 | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ |
| 编辑草稿 | ❌ | ❌ | ✅ | ❌ | ❌ | ✅自己创建 | ✅ |
| 提交审核 | ❌ | ❌ | ✅ | ❌ | ❌ | ✅自己创建 | ✅ |
| 审批/拒绝 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 创建调整 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 执行调整 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 完成对账 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 删除批次 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅仅draft |

**废弃角色说明**:
- `data_operator`: 职责已合并到 `finance` 和 `account_manager`
- `media_buyer`: 已重命名为 `pitcher`，对账模块无权限

### 12.2 RLS 策略引用（7 角色版本）

**引用**: `RLS_POLICIES_SOT.md` v2.0 第 4 章 - 对账模块 RLS

**策略示例** (仅供参考，具体 SQL 查阅 RLS_POLICIES_SOT.md):

```sql
-- reconciliation_batches 查询策略 (7 角色版本)
CREATE POLICY policy_reconciliation_batches_select_role
ON reconciliation_batches FOR SELECT
USING (
    -- admin/finance/account_manager 可查看所有
    fn_current_user_role() IN ('admin', 'finance', 'account_manager')
    OR (
        -- ceo 可查看所有
        fn_current_user_role() = 'ceo'
    )
    OR (
        -- project_owner 仅查看自己项目关联的批次
        fn_current_user_role() = 'project_owner'
        AND EXISTS (
            SELECT 1 FROM projects p
            WHERE p.pm_user_id = fn_current_user_id()
            AND p.supplier_id = reconciliation_batches.supplier_id
        )
    )
    OR (
        -- supervisor 仅查看团队关联的批次
        fn_current_user_role() = 'supervisor'
        AND EXISTS (
            SELECT 1 FROM users u
            WHERE u.supervisor_id = fn_current_user_id()
            AND u.id = reconciliation_batches.created_by
        )
    )
);

-- reconciliation_batches 更新策略 (7 角色版本)
CREATE POLICY policy_reconciliation_batches_update_role
ON reconciliation_batches FOR UPDATE
USING (
    fn_current_user_role() IN ('admin', 'finance')  -- admin/finance 可更新所有
    OR (
        fn_current_user_role() = 'account_manager'
        AND created_by = fn_current_user_id()
        AND status = 'draft'  -- account_manager 仅可更新自己的草稿
    )
);
```

**关键原则** (7 角色体系):
- **admin/finance**: 全局可见、可操作
- **ceo**: 全局可见（只读）
- **project_owner**: 仅查看自己负责项目关联的批次
- **supervisor**: 仅查看团队成员创建的批次
- **account_manager**: 全局可见，仅可操作自己创建的草稿
- **pitcher**: 无对账模块权限

---

## 13. 事务边界 (Transaction Boundary)

### 13.1 批次创建事务

**事务边界**:
1. 校验唯一性
2. 计算 `our_total_spend` (汇总daily_reports.real_spend)
3. 计算 `difference` 和 `difference_rate`
4. 创建 batch 记录
5. 创建 details 记录（可选）
6. 提交事务

**事务超时**: 5秒

**状态初始化**: `status = "draft"`

### 13.2 审批流转事务

**事务边界**:
1. 使用 `SELECT FOR UPDATE` 锁定批次记录
2. 校验状态是否为 `pending`
3. 校验版本号 (乐观锁, `version = expected_version`)
4. 校验审批人权限 (SOD: `approved_by ≠ created_by`)
5. 更新状态为 `reviewing` 或 `closed`
6. 更新 `approved_by`, `version = version + 1`, `updated_at`
7. 提交事务

**事务超时**: 3秒

**错误码**:
- `BIZ_002`: 批次不存在
- `E-RECON-003`: 状态不允许审批
- `STATE_409`: 并发冲突 (版本号不匹配)
- `E-RECON-004`: 审批人与创建人相同 (违反SOD)

### 13.3 调整执行事务

**事务边界**:
1. 使用 `SELECT FOR UPDATE` 锁定批次记录
2. 校验状态必须为 `reviewing`
3. 获取所有未执行的调整 (status = "pending")
4. 逐个执行调整:
   - `writeoff`: 仅更新明细状态
   - `increase`/`decrease`: 创建 `ledger_entries` 记录
5. 更新批次状态为 `closed`
6. 更新 `version = version + 1`, `updated_at`
7. 生成对账报告
8. 提交事务

**事务超时**: 10秒 (涉及账本写入)

**性能约束**:
- 批次创建: < 5秒
- 审批流转: < 3秒
- 调整执行: < 10秒 (取决于调整笔数)
- 行锁持有时间: < 2秒

---

## 14. 测试范围 (Test Scope)

### 14.1 单元测试

| 测试类别 | 测试用例 | 断言条件 |
|---------|---------|---------|
| 差异计算 | `test_calculate_difference_positive()` | `difference > 0` 时 `recommendation = decrease` |
| 差异计算 | `test_calculate_difference_negative()` | `difference < 0` 时 `recommendation = increase` |
| 差异计算 | `test_calculate_difference_zero()` | `difference = 0` 时 `recommendation = writeoff` |
| 唯一性约束 | `test_duplicate_batch_creation()` | 抛出 `ConflictException (BIZ_003)` |
| 状态流转 | `test_forbidden_transition()` | `draft → completed` 抛出 `STATE_400` |
| 并发控制 | `test_concurrent_approval()` | 第二个审批抛出 `STATE_409` |
| SOD 校验 | `test_self_approval()` | 自己审批抛出 `E-RECON-004` |

### 14.2 集成测试

| 测试场景 | 测试步骤 | 预期结果 |
|---------|---------|---------|
| 完整对账流程 | 1. 创建批次<br>2. 提交审核<br>3. 审批通过<br>4. 执行调整<br>5. 完成对账 | 状态依次流转: `draft → pending_review → approved → completed`<br>账本生成 `manual_entry` 记录 |
| 差异调整 | 1. 创建批次（存在差异）<br>2. 创建调整记录<br>3. 执行调整 | `adjustment_type=increase` 生成 `COST` 类型账本记录<br>`adjustment_type=decrease` 生成 `REVERSAL` 类型账本记录 |
| 权限隔离 | 1. data_operator 创建批次<br>2. data_operator 尝试审批 | 审批操作抛出 `AUTH_500` |
| 乐观锁 | 1. 用户A获取批次（version=1）<br>2. 用户B审批批次（version=2）<br>3. 用户A尝试审批（version=1） | 用户A操作抛出 `STATE_409` |

### 14.3 端到端测试

**测试场景**: 完整对账流程

**测试步骤**:
1. data_operator 创建批次 → 验证 `status = "draft"`, `difference ≠ 0`
2. data_operator 提交审核 → 验证 `status = "pending"`
3. finance 审批通过 → 验证 `status = "reviewing"`
4. finance 创建调整 (adjustment_type="increase", amount=100.00)
5. finance 执行调整并完成对账 → 验证 `status = "closed"`
6. 验证账本记录: `ledger_type=SUPPLIER`, `entry_type=COST`, `amount=100.00`
7. 验证报告生成: `report.report_url` 存在

---

## 15. 版本控制规则 (Version Control)

### 15.1 文档版本管理

**引用**: `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` 第 8 章 - 文档版本管理

**版本号格式**: `vX.Y`
- **X (主版本)**: 重大业务逻辑变更（如状态机重构、计算公式调整）
- **Y (次版本)**: 字段新增、错误码补充、流程优化

**变更日志**:

| 版本 | 日期 | 变更内容 | 影响范围 |
|-----|------|----------|---------|
| v1.0 | 2025-01-22 | 初始版本，定义对账模块完整 SoT | - |

### 15.2 代码版本对齐

**Service 层要求**:
- 引用文档: `docs/2.sot/RECONCILIATION_SOT.md v1.0`
- 实现模块: `backend/services/reconciliation_service.py`
- 核心功能: 对账批次创建、差异计算、审批流转、调整执行
- 业务规则遵循: RECONCILIATION_SOT.md 定义

**API Router 要求**:
- 引用文档: `docs/2.sot/API_SOT.md` (对账端点章节)
- 实现模块: `backend/routers/reconciliations.py`
- 业务规则遵循: RECONCILIATION_SOT.md v1.0

---

## 16. 附录

### 16.1 术语表

| 术语 | 英文 | 说明 |
|-----|------|------|
| 对账 | Reconciliation | 比较我方消耗与供应商消耗的差异分析流程 |
| 对账批次 | Reconciliation Batch | 按供应商+渠道+周期维度创建的对账单元 |
| 对账明细 | Reconciliation Detail | 批次下按账户+日期拆分的差异明细 |
| 对账调整 | Reconciliation Adjustment | 针对差异的处理方案（增加/减少/核销） |
| 我方消耗 | Our Total Spend | 系统记录的 `real_spend` 汇总 |
| 供应商消耗 | Supplier Total Spend | 供应商对账单提供的消耗金额 |
| 差异 | Difference | `our_total_spend - supplier_total_spend` |
| 差异率 | Difference Rate | `(difference / supplier_total_spend) × 100%` |
| 红冲 | Reversal | 账本记录的负数调整（冲销多计） |
| 补录 | Manual Entry | 账本记录的正数调整（补充少计） |
| 核销 | Writeoff | 差异较小直接确认，不影响账本 |

### 16.2 常见问题 (FAQ)

**Q1: 对账差异为负数是什么意思？**

A: `difference < 0` 表示我方记录的消耗**少于**供应商提供的消耗，可能原因:
- 有日报未提交或未 final_locked
- 供应商多计费用
- 数据录入遗漏

**Q2: 对账调整会立即影响账本余额吗？**

A: 不会。调整记录创建后，需要 finance/admin **手动执行**调整操作，才会生成 `ledger_entries` 记录并影响余额。

**Q3: 如果对账完成后发现错误怎么办？**

A: `completed` 状态为终态，禁止修改。若发现错误，需要 admin 角色:
1. 创建新的对账批次（纠正周期）
2. 使用 `adjustment_type=decrease/increase` 红冲错误记录
3. 在新批次中重新计算正确差异

**Q4: 为什么差异计算只统计 final_locked 状态的日报？**

A: 确保计费数据稳定。`final_locked` 表示日报已通过粉数确认流程锁定，不会再修改。若统计未锁定的日报，可能导致对账后日报数据变化，差异计算失效。

**Q5: 对账模块支持多币种吗？**

A: 当前版本仅支持单一币种（CNY）。若需多币种支持，需扩展DATA_SCHEMA.md和RECONCILIATION_SOT.md相关章节。

---

## 17. 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|-----|------|----------|------|
| v2.0 | 2025-12-26 | **重大更新：7 角色体系对齐**<br>- 对齐 MASTER.md v4.4 §2.4 七角色定义<br>- 废弃 `data_operator`（合并到 finance/account_manager）<br>- 废弃 `media_buyer`（重命名为 pitcher）<br>- 新增角色：ceo、project_owner、supervisor、pitcher<br>- 重写 §4.2 流程角色权限表<br>- 重写 §12.1 角色权限矩阵（5→7 角色）<br>- 重写 §12.2 RLS 策略示例 | 系统架构团队 |
| v1.0 | 2025-01-22 | 初始版本，定义对账模块完整 SoT，包含 13 章节:<br>1. 文档定位<br>2. 模块边界<br>3. 数据模型<br>4. 核心流程<br>5. 状态机<br>6. 并发控制<br>7. 业务规则<br>8. 差异计算<br>9. 双账本影响<br>10. 幂等性<br>11. 错误码<br>12. 权限与RLS<br>13. 事务边界<br>14. 测试范围<br>15. 版本控制 | 系统架构团队 |

---

**文档维护者**: 系统架构团队
**最后审核**: 2025-12-26
**下次审核**: 对账模块重大变更时或季度性审核
