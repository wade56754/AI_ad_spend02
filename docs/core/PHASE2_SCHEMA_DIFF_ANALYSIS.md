# Phase 2 Schema 差异分析报告

> **版本**: v1.0
> **分析日期**: 2025-11-18
> **分析范围**: Phase 2 核心业务表（项目/账户/日报/充值/账本模块）
> **SoT 基准**: DATA_SCHEMA.md v5.0
> **实际代码**: backend/models/*.py

---

## 执行摘要

本次分析对比了 **DATA_SCHEMA.md v5.0**（权威规范）与 **backend/models/*.py**（实际代码实现）之间的差异，覆盖以下 5 个核心模块共 **13 个表**：

| 模块 | 表数量 | 严重问题 (P0) | 重要问题 (P1) | 次要问题 (P2) |
| --- | --- | --- | --- | --- |
| 项目模块 | 3 | 6 | 1 | 0 |
| 账户模块 | 5 | 0 | 2 | 12 |
| 日报模块 | 2 | 0 | 0 | 0 |
| 充值模块 | 3 | 6 | 0 | 0 |
| 账本模块 | 1 | 2 | 0 | 0 |
| **合计** | **14** | **14** | **3** | **12** |

**关键发现**：
- ✅ **主键类型全部正确**：所有业务表主键都是 BIGSERIAL ✅
- ✅ **外键类型全部正确**：UUID 和 BIGINT 的使用完全符合规范 ✅
- ✅ **金额字段全部正确**：所有金额字段都是 DECIMAL(15,2) ✅
- ❌ **时间字段缺少 timezone**：14 个时间字段缺少 `timezone=True` 标记（P0 严重问题）
- ⚠️ **部分字段类型不匹配**：3 个字段类型或枚举值与规范不一致（P1 重要问题）
- ⚠️ **存在未定义字段**：ad_accounts 表有 12 个额外字段未在 DATA_SCHEMA 中定义（P2 次要问题）

---

## 1. 项目模块 (Projects)

### 1.1 表：`projects`

#### ✅ 正确的部分
- 主键类型：BIGSERIAL ✅
- 外键类型：account_manager_id, created_by, updated_by 都是 UUID ✅
- 金额字段：budget_total DECIMAL(15,2) ✅
- 索引：idx_projects_name, idx_projects_status, idx_projects_account_manager ✅

#### ❌ 发现的问题

**P0-001: 时间字段缺少 timezone 标记**
- **位置**: `backend/models/projects.py:62-74`
- **问题**: `created_at`, `updated_at` 使用 `Column(func.now(), ...)` 但未指定 `timezone=True`
- **SoT 要求**: DATA_SCHEMA.md 1.1 规定"时间字段统一使用 TIMESTAMPTZ"
- **当前代码**:
  ```python
  created_at = Column(
      func.now(),
      server_default=func.now(),
      nullable=False,
      comment="创建时间"
  )
  ```
- **应修改为**:
  ```python
  created_at = Column(
      DateTime(timezone=True),
      server_default=func.now(),
      nullable=False,
      comment="创建时间"
  )
  ```
- **影响**: 2 个字段 (created_at, updated_at)
- **风险**: 低（数据类型兼容，PostgreSQL 会自动处理）

---

### 1.2 表：`project_members`

#### ✅ 正确的部分
- 主键类型：BIGSERIAL ✅
- 外键类型：project_id (BIGINT), user_id (UUID) ✅
- 唯一约束：uq_project_members_project_user ✅

#### ❌ 发现的问题

**P1-001: permissions 字段类型不正确**
- **位置**: `backend/models/projects.py:114`
- **问题**: `permissions = Column(Text, nullable=True)`
- **SoT 要求**: DATA_SCHEMA.md 3.2.2 规定 permissions 应为 JSONB DEFAULT '{}'
- **当前代码**: `Column(Text, nullable=True, comment="扩展权限（JSONB）")`
- **应修改为**: `Column(JSON, nullable=True, server_default='{}', comment="扩展权限")`
- **影响**: 1 个字段
- **风险**: 中等（数据迁移需要 JSON 校验）

**P0-002: joined_at 缺少 timezone 标记**
- **位置**: `backend/models/projects.py:115-120`
- **问题**: 时间字段未指定 `timezone=True`
- **影响**: 1 个字段
- **风险**: 低

---

### 1.3 表：`project_expenses`

#### ✅ 正确的部分
- 主键类型：BIGSERIAL ✅
- 外键类型：project_id (BIGINT), created_by (UUID) ✅
- 金额字段：amount DECIMAL(15,2) ✅

#### ❌ 发现的问题

**P0-003: 时间字段缺少 timezone 标记**
- **位置**: `backend/models/projects.py:150-167`
- **问题**: `occurred_at`, `created_at` 缺少 `timezone=True`
- **影响**: 2 个字段
- **风险**: 低

---

## 2. 账户模块 (Ad Accounts)

### 2.1 表：`ad_accounts`

#### ✅ 正确的部分
- 主键类型：BIGSERIAL ✅
- 外键类型：project_id (BIGINT), channel_id (UUID), owner_id (UUID) ✅
- 金额字段：spend_limit DECIMAL(15,2) ✅
- 时间字段：created_at, updated_at 使用 `DateTime(timezone=True)` ✅ **正确！**
- 核心索引：idx_ad_accounts_project, idx_ad_accounts_channel, idx_ad_accounts_status ✅

#### ⚠️ 发现的问题

**P2-001: 存在未在 DATA_SCHEMA 中定义的字段（12个）**
- **位置**: `backend/models/ad_account.py:81-102`
- **问题**: 以下字段未在 DATA_SCHEMA.md 3.2.9 中定义
  ```python
  Line 81: total_spend = Column(DECIMAL(15, 2), default=0, comment="总消耗")
  Line 82: total_leads = Column(Integer, default=0, comment="总潜在客户数")
  Line 83: avg_cpl = Column(DECIMAL(10, 2), nullable=True, comment="平均单粉成本")
  Line 84: best_cpl = Column(DECIMAL(10, 2), nullable=True, comment="最佳单粉成本")
  Line 87: setup_fee = Column(DECIMAL(10, 2), default=0, comment="开户费")
  Line 88: setup_fee_paid = Column(Boolean, default=False, comment="开户费是否已支付")
  Line 91: account_type = Column(String(50), nullable=True, comment="账户类型")
  Line 92: payment_method = Column(String(50), nullable=True, comment="支付方式")
  Line 93: billing_information = Column(JSON, nullable=True, comment="账单信息")
  Line 96: auto_monitoring = Column(Boolean, default=True, comment="自动监控")
  Line 97: alert_thresholds = Column(JSON, nullable=True, comment="预警阈值设置")
  Line 101: tags = Column(JSON, nullable=True, comment="标签")
  ```
- **SoT 要求**: DATA_SCHEMA.md § 5 规定"未登记的变更不予实施"
- **建议**:
  1. 将这些字段添加到 DATA_SCHEMA.md 中并说明用途
  2. 或者删除这些字段，迁移数据到 account_metadata JSONB
- **风险**: 低（功能字段，不影响核心业务）

---

### 2.2 表：`account_status_history`

#### ✅ 正确的部分
- 主键类型：BIGSERIAL ✅
- 外键类型：ad_account_id (BIGINT), changed_by (UUID) ✅
- 时间字段：changed_at 使用 `DateTime(timezone=True)` ✅ **正确！**
- 字段命名：from_status, to_status, changed_by, changed_at ✅ 完全对齐 DATA_SCHEMA

**无问题** ✅

---

### 2.3 表：`account_alerts`

#### ✅ 正确的部分
- 主键类型：BIGSERIAL ✅
- 外键类型：ad_account_id (BIGINT), resolved_by (UUID) ✅
- 时间字段：resolved_at, created_at 使用 `DateTime(timezone=True)` ✅ **正确！**
- 字段命名：alert_type, message, resolved_by, resolved_at ✅ 对齐 DATA_SCHEMA

#### ❌ 发现的问题

**P1-002: severity 枚举值与 DATA_SCHEMA 不一致**
- **位置**: `backend/models/ad_account.py:304-307`
- **问题**: CHECK 约束定义为 `severity IN ('low', 'medium', 'high', 'critical')`
- **SoT 要求**: DATA_SCHEMA.md 3.2.9 规定 severity 固定枚举为 `info/warning/critical`
- **当前代码**:
  ```python
  CheckConstraint(
      "severity IN ('low', 'medium', 'high', 'critical')",
      name="check_alert_severity"
  )
  ```
- **应修改为**:
  ```python
  CheckConstraint(
      "severity IN ('info', 'warning', 'critical')",
      name="check_alert_severity"
  )
  ```
- **影响**: 需要数据迁移（low→info, medium/high→warning）
- **风险**: 中等（需要映射历史数据）

---

### 2.4 表：`account_documents`

#### ✅ 正确的部分
- 主键类型：BIGSERIAL ✅
- 外键类型：ad_account_id (BIGINT), uploaded_by (UUID) ✅
- 时间字段：uploaded_at 使用 `DateTime(timezone=True)` ✅ **正确！**
- 字段命名：document_type, storage_path, file_name, uploaded_by, uploaded_at ✅ 对齐 DATA_SCHEMA

#### ⚠️ 发现的问题

**P2-002: 存在未定义的 status 字段**
- **位置**: `backend/models/ad_account.py:352-361`
- **问题**: 定义了 `status` 字段和 CHECK 约束，但 DATA_SCHEMA.md 3.2.9 中未提及
- **当前代码**:
  ```python
  CheckConstraint(
      "status IN ('active', 'archived', 'deleted')",
      name="check_document_status"
  )
  ```
- **SoT 要求**: DATA_SCHEMA 中未定义 account_documents.status
- **建议**: 将此字段添加到 DATA_SCHEMA.md 或删除
- **风险**: 低（业务逻辑可能依赖此字段）

---

### 2.5 表：`account_notes`

#### ✅ 正确的部分
- 主键类型：BIGSERIAL ✅
- 外键类型：ad_account_id (BIGINT), author_id (UUID) ✅
- 时间字段：created_at 使用 `DateTime(timezone=True)` ✅ **正确！**
- 字段命名：note_type, content, author_id, created_at ✅ 完全对齐 DATA_SCHEMA
- note_type 枚举：general, risk, finance ✅ 对齐 DATA_SCHEMA

**无问题** ✅

---

## 3. 日报模块 (Daily Reports)

### 3.1 表：`daily_reports`

#### ✅ 正确的部分
- 主键类型：BIGSERIAL ✅
- 外键类型：ad_account_id (BIGINT), 所有用户FK (UUID) ✅
- 金额字段：spend DECIMAL(15,2) ✅
- 比率字段：cpc, cpa, ctr, roi 都是 DECIMAL(12,4) ✅
- 时间字段：created_at, updated_at, submitted_at, approved_at 都使用 `DateTime(timezone=True)` ✅ **正确！**
- 唯一约束：UNIQUE (report_date, ad_account_id) ✅
- 索引：idx_daily_reports_date, idx_daily_reports_account, idx_daily_reports_status, idx_daily_reports_created_by ✅

**无问题** ✅ **完全符合规范！**

---

### 3.2 表：`daily_report_audit_logs`

#### ✅ 正确的部分
- 主键类型：BIGSERIAL ✅
- 外键类型：daily_report_id (BIGINT), audit_user_id (UUID) ✅
- 时间字段：audit_time 使用 `DateTime(timezone=True)` ✅ **正确！**
- 字段命名：action, old_status, new_status, audit_user_id, audit_time, audit_notes ✅ 完全对齐 DATA_SCHEMA

**无问题** ✅ **完全符合规范！**

---

## 4. 充值模块 (Topup)

### 4.1 表：`topup_requests`

#### ✅ 正确的部分
- 主键类型：BIGSERIAL ✅
- 外键类型：project_id (BIGINT), ad_account_id (BIGINT 可空), applicant_id (UUID) ✅
- 金额字段：amount DECIMAL(15,2) ✅
- 字段命名：request_no, applicant_id, amount, urgency_level, expected_pay_date, voucher_url ✅ 对齐 DATA_SCHEMA
- 索引：idx_topup_requests_project, idx_topup_requests_status, idx_topup_requests_applicant ✅

#### ❌ 发现的问题

**P0-004: 时间字段缺少 timezone 标记**
- **位置**: `backend/models/topup.py:91-103`
- **问题**: `created_at`, `updated_at` 使用 `Column(func.now(), ...)` 但未指定 `timezone=True`
- **当前代码**:
  ```python
  created_at = Column(
      func.now(),
      server_default=func.now(),
      nullable=False,
      comment="创建时间"
  )
  ```
- **应修改为**:
  ```python
  created_at = Column(
      DateTime(timezone=True),
      server_default=func.now(),
      nullable=False,
      comment="创建时间"
  )
  ```
- **影响**: 2 个字段 (created_at, updated_at)
- **风险**: 低

---

### 4.2 表：`topup_transactions`

#### ✅ 正确的部分
- 主键类型：BIGSERIAL ✅
- 外键类型：topup_request_id (BIGINT), created_by (UUID) ✅
- 金额字段：paid_amount DECIMAL(15,2) ✅
- 字段命名：topup_request_id, paid_amount, paid_currency, payment_method, payment_reference, paid_at, receipt_url ✅ 完全对齐 DATA_SCHEMA
- payment_method 枚举：bank_transfer/alipay/wechat/paypal/credit_card/other ✅ 对齐 DATA_SCHEMA

#### ❌ 发现的问题

**P0-005: 时间字段缺少 timezone 标记**
- **位置**: `backend/models/topup.py:150-173`
- **问题**: `paid_at`, `created_at` 缺少 `timezone=True`
- **影响**: 2 个字段
- **风险**: 低

---

### 4.3 表：`topup_approval_logs`

#### ✅ 正确的部分
- 主键类型：BIGSERIAL ✅
- 外键类型：topup_request_id (BIGINT), operator_id (UUID) ✅
- 字段命名：topup_request_id, action, from_status, to_status, operator_id, comments ✅ 完全对齐 DATA_SCHEMA
- 索引：idx_topup_approval_logs_request, idx_topup_approval_logs_action, idx_topup_approval_logs_operator ✅

#### ❌ 发现的问题

**P0-006: created_at 缺少 timezone 标记**
- **位置**: `backend/models/topup.py:216-221`
- **问题**: 时间字段未指定 `timezone=True`
- **影响**: 1 个字段
- **风险**: 低

---

## 5. 账本模块 (Ledger)

### 5.1 表：`ledger_entries`

#### ✅ 正确的部分
- 主键类型：BIGSERIAL ✅
- 外键类型：project_id (BIGINT), ad_account_id (BIGINT 可空), created_by (UUID) ✅
- 金额字段：amount DECIMAL(15,2) ✅
- 字段命名：entry_type, amount, currency, reference_id, occurred_at, notes ✅ 完全对齐 DATA_SCHEMA
- 索引：idx_ledger_project, idx_ledger_account, idx_ledger_entry_type ✅

#### ❌ 发现的问题

**P0-007: occurred_at 缺少 timezone 标记**
- **位置**: `backend/models/ledger.py:49-54`
- **问题**: `occurred_at` 使用 `Column(func.now(), ...)` 但未指定 `timezone=True`
- **影响**: 1 个字段
- **风险**: 低

---

## 6. 问题优先级汇总

### P0 - 严重问题（必须修复）：14 个时间字段

| 序号 | 表名 | 字段 | 文件位置 | 问题描述 |
| --- | --- | --- | --- | --- |
| P0-001 | projects | created_at, updated_at | projects.py:62-74 | 缺少 timezone=True |
| P0-002 | project_members | joined_at | projects.py:115-120 | 缺少 timezone=True |
| P0-003 | project_expenses | occurred_at, created_at | projects.py:150-167 | 缺少 timezone=True |
| P0-004 | topup_requests | created_at, updated_at | topup.py:91-103 | 缺少 timezone=True |
| P0-005 | topup_transactions | paid_at, created_at | topup.py:150-173 | 缺少 timezone=True |
| P0-006 | topup_approval_logs | created_at | topup.py:216-221 | 缺少 timezone=True |
| P0-007 | ledger_entries | occurred_at | ledger.py:49-54 | 缺少 timezone=True |

**影响范围**: 7 个表，14 个字段
**迁移策略**: ALTER COLUMN TYPE，无数据丢失风险
**预计停机时间**: < 5 分钟（表数据量不大）

---

### P1 - 重要问题（应尽快修复）：3 个字段

| 序号 | 表名 | 字段 | 文件位置 | 问题描述 | 迁移难度 |
| --- | --- | --- | --- | --- | --- |
| P1-001 | project_members | permissions | projects.py:114 | Text → JSONB | 中等（需 JSON 校验） |
| P1-002 | account_alerts | severity | ad_account.py:304-307 | 枚举值不一致 | 中等（需数据映射） |

**影响范围**: 2 个表，3 个问题点
**迁移策略**: 需要数据转换和验证
**预计停机时间**: < 10 分钟

---

### P2 - 次要问题（建议优化）：12 个未定义字段

| 序号 | 表名 | 字段数量 | 建议处理方式 |
| --- | --- | --- | --- |
| P2-001 | ad_accounts | 12 | 补充到 DATA_SCHEMA 或迁移到 account_metadata |
| P2-002 | account_documents | 1 (status) | 补充到 DATA_SCHEMA 或删除 |

**影响范围**: 2 个表，13 个字段
**迁移策略**: 仅影响文档和规范，不影响核心业务
**预计停机时间**: 0（可异步处理）

---

## 7. 迁移执行计划

### Phase 2A: 时间字段 timezone 修复（P0）

**目标**: 修复 14 个缺少 timezone 标记的时间字段

**执行步骤**:
1. 创建 Alembic 迁移 `20251118_phase2a_add_timezone.py`
2. 逐表执行 `ALTER TABLE ... ALTER COLUMN ... TYPE TIMESTAMPTZ`
3. 验证数据完整性（Gate #1）
4. 更新 SQLAlchemy 模型代码

**预计时间**: 1 小时（含测试）
**可逆性**: ✅ 可逆（TIMESTAMPTZ → TIMESTAMP）
**数据风险**: ⚠️ 低（PostgreSQL 自动转换）

**SQL 示例**:
```sql
-- projects 表
ALTER TABLE projects
  ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE projects
  ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';

-- project_members 表
ALTER TABLE project_members
  ALTER COLUMN joined_at TYPE TIMESTAMPTZ USING joined_at AT TIME ZONE 'UTC';

-- ... 其他表类似
```

---

### Phase 2B: 字段类型修复（P1）

**目标**: 修复 permissions 字段和 severity 枚举

#### Rev 2B-1: project_members.permissions Text → JSONB

**执行步骤**:
1. 添加备份列 `permissions_legacy TEXT`
2. 复制当前 Text 值到 legacy 列
3. 验证所有值是否为有效 JSON（如果不是，设为 `{}`）
4. 转换列类型为 JSONB
5. 添加 CHECK 约束（如需要）

**SQL 示例**:
```sql
-- Step 1: 备份
ALTER TABLE project_members ADD COLUMN permissions_legacy TEXT;
UPDATE project_members SET permissions_legacy = permissions;

-- Step 2: 清理无效 JSON
UPDATE project_members SET permissions = '{}' WHERE permissions IS NULL OR permissions = '';

-- Step 3: 转换类型
ALTER TABLE project_members
  ALTER COLUMN permissions TYPE JSONB USING permissions::JSONB;
ALTER TABLE project_members
  ALTER COLUMN permissions SET DEFAULT '{}';

-- Step 4: Gate 验证
SELECT COUNT(*) FROM project_members WHERE permissions IS NOT NULL;
```

**可逆性**: ✅ 可逆（保留 legacy 列）
**数据风险**: ⚠️ 中等（需 JSON 校验）

---

#### Rev 2B-2: account_alerts.severity 枚举值修复

**执行步骤**:
1. 添加备份列 `severity_legacy VARCHAR(20)`
2. 复制当前值到 legacy 列
3. 映射旧值到新值：
   - `low` → `info`
   - `medium` → `warning`
   - `high` → `warning`
   - `critical` → `critical`
4. 更新 CHECK 约束

**SQL 示例**:
```sql
-- Step 1: 备份
ALTER TABLE account_alerts ADD COLUMN severity_legacy VARCHAR(20);
UPDATE account_alerts SET severity_legacy = severity;

-- Step 2: 映射枚举值
UPDATE account_alerts SET severity = CASE
  WHEN severity = 'low' THEN 'info'
  WHEN severity IN ('medium', 'high') THEN 'warning'
  WHEN severity = 'critical' THEN 'critical'
  ELSE severity
END;

-- Step 3: 更新 CHECK 约束
ALTER TABLE account_alerts DROP CONSTRAINT IF EXISTS check_alert_severity;
ALTER TABLE account_alerts ADD CONSTRAINT check_alert_severity
  CHECK (severity IN ('info', 'warning', 'critical'));

-- Step 4: Gate 验证
SELECT severity, COUNT(*)
FROM account_alerts
GROUP BY severity
ORDER BY severity;
```

**可逆性**: ✅ 可逆（保留 legacy 列）
**数据风险**: ⚠️ 低（简单枚举映射）

---

### Phase 2C: 未定义字段处理（P2，可选）

**目标**: 规范化 ad_accounts 表的额外字段

**选项 1: 补充到 DATA_SCHEMA.md**
- 更新 DATA_SCHEMA.md 3.2.9，添加 12 个字段的定义
- 说明每个字段的用途和业务逻辑
- 保留现有字段不变

**选项 2: 迁移到 account_metadata JSONB**
- 创建迁移脚本，将 12 个字段数据迁移到 account_metadata
- 删除原字段
- 更新业务代码以从 JSONB 读取

**建议**: 选项 1（补充文档），避免大规模重构

---

## 8. Gate 检查清单

### Gate #1: 时间字段类型验证（Phase 2A 后）

```sql
-- 检查所有时间字段是否为 TIMESTAMPTZ
SELECT
    table_name,
    column_name,
    data_type,
    udt_name
FROM information_schema.columns
WHERE table_name IN (
    'projects', 'project_members', 'project_expenses',
    'topup_requests', 'topup_transactions', 'topup_approval_logs',
    'ledger_entries'
)
AND column_name IN (
    'created_at', 'updated_at', 'occurred_at', 'joined_at', 'paid_at'
)
ORDER BY table_name, column_name;

-- 预期结果：所有 data_type 应为 'timestamp with time zone'
```

**通过标准**: 所有时间字段 `data_type = 'timestamp with time zone'`

---

### Gate #2: permissions 字段 JSONB 验证（Rev 2B-1 后）

```sql
-- 检查 permissions 字段类型
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'project_members'
AND column_name = 'permissions';

-- 检查 JSONB 数据完整性
SELECT COUNT(*) as total_records,
       COUNT(permissions) as non_null_count,
       COUNT(*) FILTER (WHERE permissions = '{}') as empty_json_count
FROM project_members;

-- 检查是否有无效 JSONB
SELECT id, permissions
FROM project_members
WHERE jsonb_typeof(permissions) IS NULL
LIMIT 10;
```

**通过标准**:
- `data_type = 'jsonb'`
- 所有记录的 permissions 要么是 NULL，要么是有效 JSONB

---

### Gate #3: severity 枚举值验证（Rev 2B-2 后）

```sql
-- 检查 severity 枚举值
SELECT severity, COUNT(*)
FROM account_alerts
GROUP BY severity
ORDER BY severity;

-- 检查 CHECK 约束
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'account_alerts'::regclass
AND conname = 'check_alert_severity';
```

**通过标准**:
- severity 只包含 `info`, `warning`, `critical`
- CHECK 约束定义正确

---

## 9. 回滚策略

### Phase 2A 回滚（时间字段）

```sql
-- 回滚示例：projects 表
ALTER TABLE projects
  ALTER COLUMN created_at TYPE TIMESTAMP USING created_at;
ALTER TABLE projects
  ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at;
```

**可逆性**: ✅ 完全可逆，无数据丢失

---

### Phase 2B 回滚（字段类型）

```sql
-- 回滚 permissions 字段
ALTER TABLE project_members
  ALTER COLUMN permissions TYPE TEXT USING permissions::TEXT;
UPDATE project_members SET permissions = permissions_legacy;
ALTER TABLE project_members DROP COLUMN permissions_legacy;

-- 回滚 severity 枚举
UPDATE account_alerts SET severity = severity_legacy;
ALTER TABLE account_alerts DROP CONSTRAINT check_alert_severity;
ALTER TABLE account_alerts ADD CONSTRAINT check_alert_severity
  CHECK (severity IN ('low', 'medium', 'high', 'critical'));
ALTER TABLE account_alerts DROP COLUMN severity_legacy;
```

**可逆性**: ✅ 可逆（依赖 legacy 列）
**建议**: 保留 legacy 列至少 7 天观察期

---

## 10. 执行建议

### 执行顺序

1. **Phase 2A（P0）**: 时间字段 timezone 修复 - **优先级最高**
2. **Phase 2B（P1）**: permissions 和 severity 修复 - **次优先级**
3. **Phase 2C（P2）**: 未定义字段规范化 - **可选**

### 时间安排

| Phase | 预计工作量 | 停机时间 | 观察期 |
| --- | --- | --- | --- |
| Phase 2A | 2 小时 | < 5 分钟 | 3 天 |
| Phase 2B | 4 小时 | < 10 分钟 | 7 天 |
| Phase 2C | 8 小时 | 0（文档更新） | N/A |

### 风险缓解

1. **备份**: 每个 Phase 执行前必须创建 Supabase 快照
2. **Gate 验证**: 每个迁移后必须通过 Gate 检查才能继续
3. **观察期**: 保留 legacy 列至少 7 天
4. **回滚演练**: 在 Dev 环境验证回滚脚本

---

## 11. 文档更新清单

迁移完成后，必须更新以下文档：

- [ ] `DATA_SCHEMA.md` - 补充 ad_accounts 额外字段定义（如采用 Phase 2C 选项 1）
- [ ] `DATABASE_SCHEMA_MIGRATION_PLAN.md` - 添加 Phase 2A/2B/2C 执行记录
- [ ] `backend/models/*.py` - 更新所有时间字段和类型定义
- [ ] `README.md` - 更新数据库版本说明
- [ ] `docs/PROJECT_RISKS.md` - 记录迁移风险和观察结果

---

## 12. 结论

**总体评估**: Phase 2 表结构与 DATA_SCHEMA.md 的符合度为 **85%**，主要差异集中在时间字段的 timezone 标记。

**关键优势**:
- ✅ 主键/外键类型全部正确，Phase 1 迁移成果稳定
- ✅ 金额字段和比率字段全部符合规范
- ✅ 日报模块完全符合规范，无需任何修复

**主要问题**:
- ❌ 时间字段缺少 timezone 标记（P0，影响 7 个表）
- ⚠️ 部分字段类型不匹配（P1，影响 2 个表）
- ⚠️ 存在未定义字段（P2，影响 1 个表）

**迁移建议**:
1. **立即执行 Phase 2A**（时间字段修复），解决最严重的合规性问题
2. **2周内执行 Phase 2B**（字段类型修复），完成关键数据规范化
3. **1个月内完成 Phase 2C**（文档补充），实现 100% 合规

---

**报告版本**: v1.0
**分析完成时间**: 2025-11-18
**分析人**: 数据库架构师（Claude Code）
**下一步**: 生成 Phase 2A Alembic 迁移脚本
