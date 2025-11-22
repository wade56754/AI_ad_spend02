# RECONCILIATION_SOT.md · 对账模块唯一真相源

> **版本**: v1.0
> **更新日期**: 2025-01-22
> **维护团队**: 系统架构团队
> **定位**: 对账模块（Channel Reconciliation）唯一真相源（Single Source of Truth），定义对账业务模型、核心流程、状态机、并发控制、账本影响等全部规则。
> **互锁 SoT**:
> - 数据结构 → `docs/core/DATA_SCHEMA.md` v5.1
> - 业务规则 → `docs/core/BUSINESS_RULES.md` v3.1 (BR-RECON)
> - 账本逻辑 → `docs/core/LEDGER_SOT.md` v2.0
> - 错误码 → `docs/core/ERROR_CODES_SOT.md` v2.1
> - 权限控制 → `docs/core/AUTH_SPEC.md` v2.0
> - RLS策略 → `docs/core/RLS_POLICIES_SOT.md` v2.0
> - 状态机 → `docs/core/STATE_MACHINE.md` v2.6

---

## 1. 文档定位 (Document Scope)

### 1.1 本文档职责

本文档是**对账模块（Reconciliation）唯一真相源**，负责定义：

1. **对账业务模型**: 对账批次（Batch）→ 明细（Detail）→ 调整（Adjustment）的层次结构
2. **对账核心流程**: 创建批次 → 差异计算 → 审核确认 → 生成报告的完整流程
3. **状态机规则**: draft/pending_review/approved/needs_adjustment/completed 状态流转
4. **差异计算逻辑**: `difference = our_total_spend - supplier_total_spend`
5. **双账本影响**: 对账不直接修改 PROJECT/SUPPLIER 账本余额，但可生成 `manual_entry` 调整记录
6. **并发控制**: 基于 `expected_version` 的乐观锁机制
7. **幂等性保证**: `(supplier_id, channel_id, period_start, period_end)` 唯一性约束
8. **错误码映射**: E-RECON-001/002/003/004/005
9. **权限控制**: finance/data_operator/admin 角色权限与 RLS 策略引用
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
| `status` | VARCHAR(20) | NOT NULL | 对账状态，参考"对账批次状态机"（STATE_MACHINE.md），合法值: `draft/pending_review/approved/needs_adjustment/completed` |
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
- `CHECK (status IN ('draft', 'pending_review', 'approved', 'needs_adjustment', 'completed'))` - 状态枚举

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
| `status` | VARCHAR(20) | NOT NULL | 明细状态，参考"对账明细状态机"（STATE_MACHINE.md），合法值: `pending/confirmed/adjusted` |
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

### 4.2 流程角色权限

| 步骤 | 允许角色 | 操作 | 状态变化 |
|-----|---------|------|---------|
| 创建批次 | data_operator, finance | POST /reconciliations | `null → draft` |
| 编辑草稿 | data_operator, finance | PATCH /reconciliations/{id} | `draft → draft` |
| 提交审核 | data_operator, finance | POST /reconciliations/{id}/submit | `draft → pending_review` |
| 审批通过 | finance, admin | POST /reconciliations/{id}/approve | `pending_review → approved` |
| 需要调整 | finance, admin | POST /reconciliations/{id}/adjust | `pending_review → needs_adjustment` |
| 完成对账 | finance, admin | POST /reconciliations/{id}/complete | `approved → completed` |
| 取消对账 | admin | POST /reconciliations/{id}/cancel | `draft/pending_review → cancelled` |

### 4.3 API 端点映射

| 端点 | 方法 | 说明 | 引用文档 |
|-----|------|------|---------|
| `/api/v1/reconciliations` | POST | 创建对账批次 | [API_GUIDE.md](../modules/reconciliations/API_GUIDE.md) |
| `/api/v1/reconciliations/{id}` | GET | 获取批次详情 | 同上 |
| `/api/v1/reconciliations/{id}` | PATCH | 更新批次（仅draft状态） | 同上 |
| `/api/v1/reconciliations/{id}/submit` | POST | 提交审核 | 同上 |
| `/api/v1/reconciliations/{id}/approve` | POST | 审批通过 | 同上 |
| `/api/v1/reconciliations/{id}/adjust` | POST | 标记需调整 | 同上 |
| `/api/v1/reconciliations/{id}/complete` | POST | 完成对账 | 同上 |
| `/api/v1/reconciliations/{id}/details` | GET | 获取明细列表 | 同上 |
| `/api/v1/reconciliations/{id}/adjustments` | POST | 创建调整记录 | 同上 |
| `/api/v1/reconciliations/{id}/report` | GET | 生成对账报告 | 同上 |

---

## 5. 状态机 (State Machine)

### 5.1 对账批次状态机

**引用**: `STATE_MACHINE.md` v2.6 第 X 章 - 对账批次状态机

**状态枚举** (`reconciliation_batches.status`):

| 状态值 | 中文名称 | 说明 | 是否终态 |
|-------|---------|------|---------|
| `draft` | 草稿 | 初始状态，可编辑 | ❌ |
| `pending_review` | 待审核 | 已提交，等待 finance/admin 审核 | ❌ |
| `approved` | 已批准 | 差异已确认，可执行调整或直接完成 | ❌ |
| `needs_adjustment` | 需调整 | 存在差异需要创建调整记录 | ❌ |
| `completed` | 已完成 | 对账完成，批次锁定 | ✅ |
| `cancelled` | 已取消 | 批次取消（仅admin） | ✅ |

**状态流转白名单**:

```python
RECONCILIATION_STATUS_TRANSITIONS = {
    "draft": ["pending_review", "cancelled"],  # 草稿 → 提交审核 或 取消
    "pending_review": ["approved", "needs_adjustment", "draft"],  # 审核中 → 批准/需调整/退回草稿
    "approved": ["completed", "needs_adjustment"],  # 已批准 → 完成 或 发现新差异
    "needs_adjustment": ["approved"],  # 调整完成后 → 重新批准
    "completed": [],  # 终态，禁止流转
    "cancelled": []   # 终态，禁止流转
}
```

**禁止流转规则**:
- ❌ 终态回退: `completed/cancelled → 任何非终态`（仅 admin 可红冲后重建）
- ❌ 跳过审核: `draft → completed`（必须经过 pending_review → approved）
- ❌ 自动完成: 系统不可自动流转到 `completed`，必须 finance/admin 手动确认

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

```sql
-- 更新批次时检查版本号
UPDATE reconciliation_batches
SET
    status = :new_status,
    version = version + 1,
    updated_at = NOW()
WHERE id = :batch_id
  AND version = :expected_version;

-- 若 affected_rows = 0，抛出 STATE_409 并发冲突错误
```

**错误码**: `STATE_409` (并发冲突)

**处理逻辑**:
```python
from backend.exceptions import ConcurrencyConflictError
from backend.core.error_codes import StateErrorCodes

def approve_reconciliation(batch_id: int, expected_version: int):
    result = db.execute(
        text("""
            UPDATE reconciliation_batches
            SET status = 'approved', version = version + 1
            WHERE id = :id AND version = :ver
        """),
        {"id": batch_id, "ver": expected_version}
    )

    if result.rowcount == 0:
        raise ConcurrencyConflictError(
            message=f"对账批次 {batch_id} 已被其他用户修改",
            code=StateErrorCodes.CONCURRENCY_CONFLICT.code
        )
```

### 6.2 审批串行化

**规则**: 同一批次同时只能有一个审批操作进行，防止并发审批冲突。

**实现**: 使用 `FOR UPDATE` 行锁:

```sql
BEGIN;

-- 锁定批次记录
SELECT * FROM reconciliation_batches
WHERE id = :batch_id
FOR UPDATE;

-- 检查状态
IF status != 'pending_review' THEN
    RAISE EXCEPTION 'E-RECON-003';
END IF;

-- 更新状态
UPDATE reconciliation_batches
SET status = 'approved', approved_by = :user_id, version = version + 1
WHERE id = :batch_id;

COMMIT;
```

---

## 7. 业务规则 SoT (Business Rules)

### 7.1 核心业务规则

**引用**: `BUSINESS_RULES.md` v3.1 → `docs/core/rules/BR-RECON.md`

| 规则编号 | 规则名称 | 详细约束 |
|---------|---------|---------|
| **BR-RECON-001** | 对账批次创建约束 | 1. `(supplier_id, channel_id, period_start, period_end)` 必须唯一<br>2. `period_end >= period_start`<br>3. 创建人必须是 data_operator/finance/admin |
| **BR-RECON-002** | 对账周期合法性 | 1. period_end 不得晚于当前日期<br>2. 周期范围不得超过 365 天 |
| **BR-RECON-003** | 差异处理规则 | 1. `difference` 绝对值 < 10元 → 建议 writeoff<br>2. `difference` > 0 → 我方多计，建议 decrease<br>3. `difference` < 0 → 我方少计，建议 increase |
| **BR-RECON-004** | 审批职责分离 | 1. approved_by 必须是 finance/admin<br>2. approved_by != created_by（SOD原则） |
| **BR-RECON-005** | 终态保护规则 | 1. `completed` 状态批次禁止修改（仅 admin 可红冲重建）<br>2. `completed` 状态批次禁止删除 |

### 7.2 业务计算公式

```python
# 差异计算
difference = our_total_spend - supplier_total_spend

# 差异率计算
difference_rate = (difference / supplier_total_spend) * 100 if supplier_total_spend != 0 else None

# 我方总消耗计算
our_total_spend = db.execute(
    """
    SELECT COALESCE(SUM(real_spend), 0.00) AS total
    FROM daily_reports dr
    JOIN ad_accounts aa ON dr.ad_account_id = aa.id
    WHERE aa.supplier_id = :supplier_id
      AND (:channel_id IS NULL OR aa.channel_id = :channel_id)
      AND dr.report_date BETWEEN :period_start AND :period_end
      AND dr.status = 'final_locked'  -- 仅计入已锁定的消耗
    """
).scalar()
```

**关键约束**:
- 仅计入 `status = final_locked` 的日报消耗（确保计费数据稳定）
- `supplier_total_spend` 手动输入时必须 > 0（防止除零错误）
- `difference` 可为正（我方多计）、负（我方少计）、零（完全一致）

---

## 8. 差异计算 (Difference Calculation)

### 8.1 差异计算逻辑

```python
from decimal import Decimal

def calculate_difference(our_spend: Decimal, supplier_spend: Decimal) -> dict:
    """
    计算对账差异

    Args:
        our_spend: 我方记录的总消耗
        supplier_spend: 供应商提供的总消耗

    Returns:
        {
            "difference": Decimal,  # 差异金额
            "difference_rate": Decimal,  # 差异率（百分比）
            "recommendation": str  # 调整建议
        }
    """
    difference = our_spend - supplier_spend

    # 计算差异率
    if supplier_spend != 0:
        difference_rate = (difference / supplier_spend * 100).quantize(Decimal("0.01"))
    else:
        difference_rate = None

    # 生成调整建议
    if abs(difference) < Decimal("10.00"):
        recommendation = "writeoff"  # 差异小于10元，建议核销
    elif difference > 0:
        recommendation = "decrease"  # 我方多计，建议减少
    else:
        recommendation = "increase"  # 我方少计，建议增加

    return {
        "difference": difference,
        "difference_rate": difference_rate,
        "recommendation": recommendation
    }
```

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
    :external_spend / :days_count AS external_spend,  -- 平均分摊
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
- `external_spend`: 供应商总消耗按天数平均分摊（简化处理，实际可更精细）
- `difference_amount`: 逐笔计算差异

---

## 9. 双账本影响 (Dual Ledger Impact)

### 9.1 对账与账本的关系

**引用**: `LEDGER_SOT.md` v2.0 第 5 章 - Ledger Entry Types

**关键原则**:
1. 对账模块**不直接修改** `ledger_entries` 表
2. 对账模块只**生成调整建议**（`reconciliation_adjustments`）
3. 经 finance/admin 审批后，**间接触发** `manual_entry` 类型的账本记录

### 9.2 调整类型与账本映射

| adjustment_type | 账本影响 | ledger_entries 记录 |
|----------------|---------|-------------------|
| `increase` | 补录消耗（我方少计） | `entry_type=COST`, `amount=调整金额`, `notes="对账补录"` |
| `decrease` | 红冲消耗（我方多计） | `entry_type=REVERSAL`, `amount=-调整金额`, `notes="对账红冲"` |
| `writeoff` | 无账本影响 | 不生成 ledger_entries，仅记录调整 |

### 9.3 调整执行流程

```python
from backend.services.ledger_service import LedgerService

def execute_adjustment(adjustment_id: int, user_id: str):
    """
    执行对账调整（finance/admin角色）
    """
    adjustment = get_adjustment(adjustment_id)
    detail = get_detail(adjustment.detail_id)
    batch = get_batch(detail.batch_id)

    if adjustment.adjustment_type == "writeoff":
        # 核销类型不影响账本
        detail.status = "adjusted"
        db.commit()
        return

    # 创建账本记录
    ledger_service = LedgerService()

    if adjustment.adjustment_type == "increase":
        # 补录消耗
        ledger_service.create_entry(
            ledger_type="SUPPLIER",
            supplier_id=batch.supplier_id,
            entry_type="COST",
            amount=adjustment.amount,
            reference_id=detail.id,
            notes=f"对账补录: {adjustment.reason}",
            created_by=user_id
        )
    elif adjustment.adjustment_type == "decrease":
        # 红冲多计
        ledger_service.create_entry(
            ledger_type="SUPPLIER",
            supplier_id=batch.supplier_id,
            entry_type="REVERSAL",
            amount=-adjustment.amount,  # 负数
            reference_id=detail.id,
            notes=f"对账红冲: {adjustment.reason}",
            created_by=user_id
        )

    # 更新明细状态
    detail.status = "adjusted"
    db.commit()
```

**事务边界**:
```python
@transactional
def execute_adjustments(batch_id: int, user_id: str):
    """
    批量执行对账调整（同一批次的所有调整在一个事务内完成）
    """
    adjustments = get_pending_adjustments(batch_id)

    for adj in adjustments:
        execute_adjustment(adj.id, user_id)

    # 更新批次状态
    batch = get_batch(batch_id)
    batch.status = "completed"
    batch.version += 1
    db.commit()
```

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
```python
from backend.exceptions import ConflictException
from backend.core.error_codes import BusinessErrorCodes

def create_reconciliation_batch(data: dict):
    # 检查是否已存在
    existing = db.query(ReconciliationBatch).filter(
        ReconciliationBatch.supplier_id == data["supplier_id"],
        ReconciliationBatch.channel_id == data.get("channel_id"),
        ReconciliationBatch.period_start == data["period_start"],
        ReconciliationBatch.period_end == data["period_end"]
    ).first()

    if existing:
        raise ConflictException(
            message=f"对账批次已存在: {existing.batch_no}",
            code=BusinessErrorCodes.RESOURCE_ALREADY_EXISTS.code  # BIZ_003
        )

    # 创建新批次
    batch = ReconciliationBatch(**data)
    db.add(batch)
    db.commit()
    return batch
```

### 10.2 调整记录幂等性

**规则**: 同一明细不允许重复创建相同类型的调整记录。

```python
def create_adjustment(detail_id: int, adjustment_type: str, amount: Decimal, reason: str):
    # 检查是否已存在相同类型调整
    existing = db.query(ReconciliationAdjustment).filter(
        ReconciliationAdjustment.detail_id == detail_id,
        ReconciliationAdjustment.adjustment_type == adjustment_type
    ).first()

    if existing:
        # 幂等返回已有记录
        return existing

    # 创建新调整
    adj = ReconciliationAdjustment(
        detail_id=detail_id,
        adjustment_type=adjustment_type,
        amount=amount,
        reason=reason
    )
    db.add(adj)
    db.commit()
    return adj
```

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

### 12.1 角色权限矩阵

**引用**: `AUTH_SPEC.md` v2.0 第 3 章 - 角色权限定义

| 操作 | admin | finance | data_operator | account_manager | media_buyer |
|-----|-------|---------|--------------|----------------|-------------|
| 创建对账批次 | ✅ | ✅ | ✅ | ❌ | ❌ |
| 查看对账批次 | ✅ | ✅ | ✅ | ✅ (仅自己创建) | ❌ |
| 编辑草稿 | ✅ | ✅ | ✅ (仅自己创建) | ❌ | ❌ |
| 提交审核 | ✅ | ✅ | ✅ (仅自己创建) | ❌ | ❌ |
| 审批/拒绝 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 创建调整 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 执行调整 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 完成对账 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 删除批次 | ✅ (仅draft) | ❌ | ❌ | ❌ | ❌ |

### 12.2 RLS 策略引用

**引用**: `RLS_POLICIES_SOT.md` v2.0 第 4 章 - 对账模块 RLS

**策略示例** (仅供参考，具体 SQL 查阅 RLS_POLICIES_SOT.md):

```sql
-- reconciliation_batches 查询策略
CREATE POLICY policy_reconciliation_batches_select_role
ON reconciliation_batches FOR SELECT
USING (
    fn_current_user_role() IN ('admin', 'finance')  -- admin/finance 可查看所有
    OR (
        fn_current_user_role() = 'data_operator'
        AND created_by = fn_current_user_id()  -- data_operator 只能查看自己创建的
    )
);

-- reconciliation_batches 更新策略
CREATE POLICY policy_reconciliation_batches_update_role
ON reconciliation_batches FOR UPDATE
USING (
    fn_current_user_role() IN ('admin', 'finance')  -- admin/finance 可更新所有
    OR (
        fn_current_user_role() = 'data_operator'
        AND created_by = fn_current_user_id()
        AND status = 'draft'  -- data_operator 仅可更新自己的草稿
    )
);
```

**关键原则**:
- **admin/finance**: 全局可见、可操作
- **data_operator**: 仅可见/操作自己创建的批次（draft 状态）
- **account_manager/media_buyer**: 无对账模块权限（查询接口需额外 RLS 策略支持特定场景）

---

## 13. 事务边界 (Transaction Boundary)

### 13.1 批次创建事务

```python
@transactional(timeout=5000)  # 5秒超时
def create_reconciliation_batch(data: dict, user_id: str):
    """
    创建对账批次（原子事务）

    事务边界:
    1. 校验唯一性
    2. 计算 our_total_spend
    3. 计算 difference
    4. 创建 batch 记录
    5. 创建 details 记录（可选）
    """
    # 1. 唯一性检查
    validate_uniqueness(data)

    # 2. 计算我方消耗
    our_spend = calculate_our_total_spend(
        supplier_id=data["supplier_id"],
        channel_id=data.get("channel_id"),
        period_start=data["period_start"],
        period_end=data["period_end"]
    )

    # 3. 计算差异
    supplier_spend = Decimal(data["supplier_total_spend"])
    diff_result = calculate_difference(our_spend, supplier_spend)

    # 4. 创建批次
    batch = ReconciliationBatch(
        batch_no=generate_batch_no(),
        supplier_id=data["supplier_id"],
        channel_id=data.get("channel_id"),
        period_start=data["period_start"],
        period_end=data["period_end"],
        our_total_spend=our_spend,
        supplier_total_spend=supplier_spend,
        difference=diff_result["difference"],
        difference_rate=diff_result["difference_rate"],
        status="draft",
        created_by=user_id
    )
    db.add(batch)
    db.flush()  # 获取 batch.id

    # 5. 创建明细（可选）
    if data.get("create_details", False):
        create_details(batch.id, data)

    db.commit()
    return batch
```

### 13.2 审批流转事务

```python
@transactional(timeout=3000)  # 3秒超时
def approve_reconciliation(batch_id: int, user_id: str, expected_version: int):
    """
    审批对账批次（原子事务）

    事务边界:
    1. 行锁批次记录
    2. 校验状态
    3. 校验版本号（乐观锁）
    4. 校验审批人权限（SOD）
    5. 更新状态
    """
    # 1. 锁定记录
    batch = db.query(ReconciliationBatch).filter(
        ReconciliationBatch.id == batch_id
    ).with_for_update().first()

    if not batch:
        raise ResourceNotFoundException(code="BIZ_002")

    # 2. 校验状态
    if batch.status != "pending_review":
        raise BusinessRuleException(
            message=f"批次状态为 {batch.status}，无法审批",
            code="E-RECON-003"
        )

    # 3. 乐观锁
    if batch.version != expected_version:
        raise ConcurrencyConflictError(code="STATE_409")

    # 4. SOD 校验
    if batch.created_by == user_id:
        raise BusinessRuleException(
            message="审批人不能是创建人",
            code="E-RECON-004"
        )

    # 5. 更新状态
    batch.status = "approved"
    batch.approved_by = user_id
    batch.version += 1
    batch.updated_at = datetime.now(timezone.utc)

    db.commit()
    return batch
```

### 13.3 调整执行事务

```python
@transactional(timeout=10000)  # 10秒超时（涉及账本写入）
def execute_batch_adjustments(batch_id: int, user_id: str):
    """
    批量执行调整并完成对账（原子事务）

    事务边界:
    1. 锁定批次
    2. 校验状态（必须是 approved）
    3. 获取所有未执行的调整
    4. 逐个执行调整（创建 ledger_entries）
    5. 更新批次状态为 completed
    6. 生成对账报告
    """
    # 1. 锁定批次
    batch = db.query(ReconciliationBatch).filter(
        ReconciliationBatch.id == batch_id
    ).with_for_update().first()

    # 2. 校验状态
    if batch.status != "approved":
        raise BusinessRuleException(code="E-RECON-003")

    # 3. 获取待执行调整
    adjustments = db.query(ReconciliationAdjustment).join(
        ReconciliationDetail
    ).filter(
        ReconciliationDetail.batch_id == batch_id,
        ReconciliationDetail.status == "pending"
    ).all()

    # 4. 执行调整
    for adj in adjustments:
        execute_adjustment(adj.id, user_id)

    # 5. 更新批次状态
    batch.status = "completed"
    batch.version += 1
    batch.updated_at = datetime.now(timezone.utc)

    # 6. 生成报告
    report = create_reconciliation_report(batch_id, user_id)

    db.commit()
    return {"batch": batch, "report": report}
```

**性能约束**:
- 批次创建: < 5 秒
- 审批流转: < 3 秒
- 调整执行: < 10 秒（取决于调整笔数）
- 行锁持有时间: < 2 秒

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

```python
def test_reconciliation_full_workflow():
    """
    端到端测试: 完整对账流程
    """
    # 1. data_operator 创建批次
    batch = create_batch(
        supplier_id="supplier-001",
        channel_id="channel-001",
        period_start="2025-01-01",
        period_end="2025-01-31",
        supplier_total_spend=10000.00,
        user_role="data_operator"
    )
    assert batch.status == "draft"
    assert batch.difference != 0  # 存在差异

    # 2. data_operator 提交审核
    submit_batch(batch.id, user_role="data_operator")
    assert batch.status == "pending_review"

    # 3. finance 审批通过
    approve_batch(batch.id, user_role="finance")
    assert batch.status == "approved"

    # 4. finance 创建调整
    adj = create_adjustment(
        batch_id=batch.id,
        adjustment_type="increase",
        amount=100.00,
        reason="补录消耗",
        user_role="finance"
    )

    # 5. finance 执行调整并完成对账
    complete_batch(batch.id, user_role="finance")
    assert batch.status == "completed"

    # 6. 验证账本记录
    ledger = get_ledger_entries(reference_id=adj.detail_id)
    assert ledger.entry_type == "COST"
    assert ledger.amount == 100.00

    # 7. 验证报告生成
    report = get_report(batch_id=batch.id)
    assert report.report_url is not None
```

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

**Service 层引用**:
```python
# backend/services/reconciliation_service.py

"""
对账模块业务逻辑层

**引用文档**: docs/core/RECONCILIATION_SOT.md v1.0
**最后更新**: 2025-01-22

本模块实现对账批次创建、差异计算、审批流转、调整执行等核心功能。
所有业务规则必须遵循 RECONCILIATION_SOT.md 定义。
"""
```

**API Router 引用**:
```python
# backend/routers/reconciliations.py

"""
对账模块 API 路由

**API 文档**: docs/modules/reconciliations/API_GUIDE.md
**业务规则**: docs/core/RECONCILIATION_SOT.md v1.0
"""
```

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

A: 当前版本仅支持单一币种（CNY）。若需多币种，需扩展以下字段:
- `reconciliation_batches.currency`
- 差异计算需汇率转换
- 账本调整需指定币种

---

## 17. 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|-----|------|----------|------|
| v1.0 | 2025-01-22 | 初始版本，定义对账模块完整 SoT，包含 13 章节:<br>1. 文档定位<br>2. 模块边界<br>3. 数据模型<br>4. 核心流程<br>5. 状态机<br>6. 并发控制<br>7. 业务规则<br>8. 差异计算<br>9. 双账本影响<br>10. 幂等性<br>11. 错误码<br>12. 权限与RLS<br>13. 事务边界<br>14. 测试范围<br>15. 版本控制 | 系统架构团队 |

---

**文档维护者**: 系统架构团队
**最后审核**: 2025-01-22
**下次审核**: 对账模块重大变更时或季度性审核
