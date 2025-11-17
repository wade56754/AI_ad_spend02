# Phase 2 数据库迁移主文档（最终版）

> **版本**: v2.0 (Final)
> **发布日期**: 2025-11-18
> **维护团队**: 数据库架构组
> **状态**: Ready for Execution
> **适用环境**: Dev → Staging → Prod（按序执行）

---

## 一、文档定位与 SoT 关系说明

### 1.1 本文档在 SoT 体系中的定位

本文档是 **执行层技术文档**，**不是规范源**。它的唯一作用是：

```
规范层（SoT）                执行层（本文档）
    ↓                            ↓
DATA_SCHEMA.md v5.0  ───→  Phase 2 差异分析
STATE_MACHINE.md v2.x ───→  Phase 2 迁移方案
MAIN_DOCUMENT v3.0    ───→  Phase 2 执行脚本
```

**权威关系**:
- **规范源（SoT）**: `DATA_SCHEMA.md` § 1.1, § 3.2, § 3.4
- **执行文档（本文档）**: 基于 SoT 生成，发现 SoT 冲突时必须以 SoT 为准
- **禁止行为**: 本文档不得定义新规范、不得与 SoT 冲突、不得私自扩展字段

### 1.2 与 MIGRATION_EXECUTION_GUIDE.md 的关系

```
DATABASE_SCHEMA_MIGRATION_PLAN.md  ← 总体路线图
    ├── Phase 1: reconciliation 表修复（已完成）
    ├── Phase 2: 核心业务表规范化 ← 本文档
    │   ├── Phase 2A: 时间字段 TIMESTAMPTZ 修复
    │   ├── Phase 2B: permissions JSONB + severity 枚举修复
    │   └── Phase 2C: 未定义字段文档补充
    └── Phase 3: （待规划）

MIGRATION_EXECUTION_GUIDE.md v1.2  ← 执行流程总指引
    ├── § 2: Gate 验证机制（本文档引用）
    ├── § 3: 回滚策略（本文档引用）
    └── § 6: 观察期要求（本文档引用）
```

**本文档角色**: Phase 2 的专项执行方案，必须遵循 `MIGRATION_EXECUTION_GUIDE.md` 的流程规范。

### 1.3 文档更新策略

**规则 1: SoT 优先更新**
```
发现问题 → 先更新 DATA_SCHEMA.md → 再更新本文档
```

**规则 2: 禁止现场扩展**
```
执行中发现新问题 → 记录到 PROJECT_RISKS.md → 不允许现场修改迁移范围
```

**规则 3: 版本锁定**
```
执行前锁定 SoT 版本 → 执行期间 SoT 冻结 → 执行后解锁
```

---

## 二、Phase 2 差异分析精简版

### 2.1 问题汇总

基于 **DATA_SCHEMA.md v5.0** 规范，发现以下与实际代码（`backend/models/*.py`）的差异：

| 优先级 | 类别 | 影响范围 | SoT 依据 | 解决方案 |
| --- | --- | --- | --- | --- |
| **P0** | 时间字段缺少 timezone | 7 表 14 字段 | DATA_SCHEMA § 1.1 | Phase 2A |
| **P1** | permissions 类型不匹配 | 1 表 1 字段 | DATA_SCHEMA § 3.2.2 | Phase 2B-001 |
| **P1** | severity 枚举值不一致 | 1 表 1 字段 | DATA_SCHEMA § 3.2.9 | Phase 2B-002 |
| **P2** | 未定义字段 | 2 表 13 字段 | DATA_SCHEMA § 5 | Phase 2C |

**总体评估**: 符合度 85% → 执行后可达 100%

### 2.2 P0 问题详情（必须修复）

#### 问题: 时间字段缺少 timezone 标记

**SoT 规范** (DATA_SCHEMA.md § 1.1):
> 时间字段：统一使用 TIMESTAMPTZ，默认 NOW()，应用层使用 UTC

**实际代码问题**:
```python
# backend/models/projects.py:62-74
created_at = Column(func.now(), ...)  # ❌ 缺少 timezone=True
```

**应修改为**:
```python
created_at = Column(DateTime(timezone=True), ...)  # ✅ 符合 SoT
```

**影响范围**:

| 模块 | 表名 | 字段 | 文件位置 |
| --- | --- | --- | --- |
| 项目 | projects | created_at, updated_at | projects.py:62-74 |
| 项目 | project_members | joined_at | projects.py:115-120 |
| 项目 | project_expenses | occurred_at, created_at | projects.py:150-167 |
| 充值 | topup_requests | created_at, updated_at | topup.py:91-103 |
| 充值 | topup_transactions | paid_at, created_at | topup.py:150-173 |
| 充值 | topup_approval_logs | created_at | topup.py:216-221 |
| 账本 | ledger_entries | occurred_at | ledger.py:49-54 |

**合计**: 7 表 × 14 字段

**解决方案**: Phase 2A（Rev 2A-001/002/003）

### 2.3 P1 问题详情（建议修复）

#### 问题 1: project_members.permissions 类型不匹配

**SoT 规范** (DATA_SCHEMA.md § 3.2.2):
```markdown
| permissions | JSONB | DEFAULT `{}` | 扩展权限 |
```

**实际代码**:
```python
permissions = Column(Text, nullable=True, comment="扩展权限（JSONB）")  # ❌
```

**解决方案**: Phase 2B-001（Text → JSONB，Strategy B 置空 + legacy 备份）

---

#### 问题 2: account_alerts.severity 枚举值不一致

**SoT 规范** (DATA_SCHEMA.md § 3.2.9):
```markdown
severity VARCHAR(20) | 固定枚举 `info/warning/critical`
```

**实际代码**:
```python
CheckConstraint("severity IN ('low', 'medium', 'high', 'critical')", ...)  # ❌
```

**解决方案**: Phase 2B-002（枚举值映射: low→info, medium/high→warning）

### 2.4 P2 问题详情（可选处理）

#### 问题: ad_accounts 表存在 12 个未在 DATA_SCHEMA 中定义的字段

**SoT 规范** (DATA_SCHEMA.md § 5):
> 规划表：如需新增表/字段，必须先在本文件创建 `status: planned` 条目并描述字段，再提交迁移。未登记的变更不予实施。

**未定义字段清单** (backend/models/ad_account.py:81-102):
```python
total_spend, total_leads, avg_cpl, best_cpl,     # 统计字段
setup_fee, setup_fee_paid,                        # 开户费用
account_type, payment_method, billing_information, # 账户配置
auto_monitoring, alert_thresholds, tags           # 监控和标签
```

**解决方案**: Phase 2C（选项 1: 补充到 DATA_SCHEMA § 3.2.9）

**最终决议**: **选择选项 1**（理由见 § 3.3）

---

## 三、Phase 2 迁移执行方案

### 3.1 Phase 2A: 时间字段 TIMESTAMPTZ 修复

#### 3.1.1 Scope（范围）

**目标**: 修复 7 个表共 14 个时间字段，将 TIMESTAMP 升级为 TIMESTAMPTZ

**SoT 依据**: DATA_SCHEMA.md § 1.1
> 时间字段统一使用 TIMESTAMPTZ

**影响表清单**:
```
projects             (created_at, updated_at)
project_members      (joined_at)
project_expenses     (occurred_at, created_at)
topup_requests       (created_at, updated_at)
topup_transactions   (paid_at, created_at)
topup_approval_logs  (created_at)
ledger_entries       (occurred_at)
```

**可逆性**: ✅ 完全可逆（Alembic downgrade 或 SQL 回滚）
**数据风险**: 低（PostgreSQL 自动处理类型转换）
**停机时间**: < 5 分钟

---

#### 3.1.2 Alembic Revisions 拆分

**命名规范** (遵循 MIGRATION_EXECUTION_GUIDE § 4):
```
Rev ID 格式: phase2a_{序号}
文件名格式: YYYYMMDD_phase2a_{序号}_{模块}_timezone.py
```

**Revision 拆分策略**: 按模块拆分（便于回滚控制）

| Revision ID | 文件名 | 模块 | 影响表 | 影响字段 |
| --- | --- | --- | --- | --- |
| phase2a_001 | 20251118_phase2a_001_projects_timezone.py | 项目模块 | 3 | 5 |
| phase2a_002 | 20251118_phase2a_002_topup_timezone.py | 充值模块 | 3 | 5 |
| phase2a_003 | 20251118_phase2a_003_ledger_timezone.py | 账本模块 | 1 | 1 |

**依赖关系**:
```
phase2a_001 (independent, no depends_on)
    ↓
phase2a_002 (depends_on: phase2a_001)
    ↓
phase2a_003 (depends_on: phase2a_002)
```

**执行方式**:
```bash
# 方式 1: 一次性升级（推荐）
alembic upgrade phase2a_003

# 方式 2: 逐步升级（调试用）
alembic upgrade phase2a_001
alembic upgrade phase2a_002
alembic upgrade phase2a_003
```

---

#### 3.1.3 执行 SQL（Rev 2A-001: projects 模块）

**前置条件**:
- ✅ Supabase 快照已创建
- ✅ DATABASE_URL 指向 Dev 环境
- ✅ 表存在性验证通过

**SQL**:
```sql
-- ==================================================
-- Rev 2A-001: projects 模块时间字段 TIMESTAMPTZ 修复
-- SoT: DATA_SCHEMA.md v5.0 § 1.1
-- Reversible: YES
-- ==================================================

-- Table 1: projects
ALTER TABLE projects
  ALTER COLUMN created_at TYPE TIMESTAMPTZ
  USING created_at AT TIME ZONE 'UTC';

ALTER TABLE projects
  ALTER COLUMN updated_at TYPE TIMESTAMPTZ
  USING updated_at AT TIME ZONE 'UTC';

-- Table 2: project_members
ALTER TABLE project_members
  ALTER COLUMN joined_at TYPE TIMESTAMPTZ
  USING joined_at AT TIME ZONE 'UTC';

-- Table 3: project_expenses
ALTER TABLE project_expenses
  ALTER COLUMN occurred_at TYPE TIMESTAMPTZ
  USING occurred_at AT TIME ZONE 'UTC';

ALTER TABLE project_expenses
  ALTER COLUMN created_at TYPE TIMESTAMPTZ
  USING created_at AT TIME ZONE 'UTC';
```

**执行结果**: 5 个字段类型升级完成

---

#### 3.1.4 Gate 验证（Gate #2A-001）

**验证时机**: Rev 2A-001 执行后立即验证

**验证 SQL**:
```sql
-- Check 1: 字段类型验证
SELECT
    table_name,
    column_name,
    data_type,
    CASE
        WHEN data_type = 'timestamp with time zone' THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM information_schema.columns
WHERE table_name IN ('projects', 'project_members', 'project_expenses')
AND column_name IN ('created_at', 'updated_at', 'occurred_at', 'joined_at')
ORDER BY table_name, column_name;

-- 预期结果: 所有 status = 'PASS' (共 5 行)

-- Check 2: 数据完整性验证
SELECT
    'projects' AS table_name,
    COUNT(*) AS total,
    COUNT(created_at) AS created_at_count,
    COUNT(updated_at) AS updated_at_count
FROM projects;

-- 预期结果: created_at_count = total AND updated_at_count = total
```

**通过标准** (遵循 MIGRATION_EXECUTION_GUIDE § 2):
1. ✅ 所有字段 data_type = `timestamp with time zone`
2. ✅ 数据完整性 100%（count = total）
3. ✅ 无异常时间值（未来时间或 1970 年之前）

**如果 Gate 失败**: 立即停止，执行回滚（见 § 3.1.5）

---

#### 3.1.5 回滚 SQL（Rev 2A-001）

**回滚时机**: Gate 验证失败或观察期发现问题

**SQL**:
```sql
-- ==================================================
-- Rollback Rev 2A-001
-- ==================================================

-- 逆序回滚（先 project_expenses，后 project_members，最后 projects）
ALTER TABLE project_expenses
  ALTER COLUMN created_at TYPE TIMESTAMP USING created_at;

ALTER TABLE project_expenses
  ALTER COLUMN occurred_at TYPE TIMESTAMP USING occurred_at;

ALTER TABLE project_members
  ALTER COLUMN joined_at TYPE TIMESTAMP USING joined_at;

ALTER TABLE projects
  ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at;

ALTER TABLE projects
  ALTER COLUMN created_at TYPE TIMESTAMP USING created_at;
```

**验证回滚**:
```sql
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name IN ('projects', 'project_members', 'project_expenses')
AND column_name IN ('created_at', 'updated_at', 'occurred_at', 'joined_at');

-- 预期结果: 所有 data_type = 'timestamp without time zone'
```

---

#### 3.1.6 Rev 2A-002 和 Rev 2A-003

**Rev 2A-002** (topup 模块) 和 **Rev 2A-003** (ledger 模块) 的结构与 Rev 2A-001 完全相同：

```
Scope → SQL → Gate → Rollback
```

详细 SQL 见已生成的 Alembic 脚本：
- `backend/alembic/versions/20251118_phase2a_002_topup_timezone.py`
- `backend/alembic/versions/20251118_phase2a_003_ledger_timezone.py`

---

#### 3.1.7 Phase 2A 综合 Gate 验证

**执行时机**: Rev 2A-001/002/003 全部完成后

**验证脚本**: `backend/phase2a_gate_verification.sql`

**核心检查**:
```sql
-- 最终验证: 所有 14 个字段是否为 TIMESTAMPTZ
SELECT
    CASE
        WHEN (SELECT COUNT(*)
              FROM information_schema.columns
              WHERE table_name IN (
                  'projects', 'project_members', 'project_expenses',
                  'topup_requests', 'topup_transactions', 'topup_approval_logs',
                  'ledger_entries'
              )
              AND column_name IN ('created_at', 'updated_at', 'occurred_at', 'joined_at', 'paid_at')
              AND data_type = 'timestamp with time zone'
             ) = 14
        THEN '✅ Phase 2A Gate 验证通过！'
        ELSE '❌ Phase 2A Gate 验证失败！'
    END AS result;
```

---

#### 3.1.8 观察期（3 天）

**遵循**: MIGRATION_EXECUTION_GUIDE § 6

**观察时间**: 2025-11-18 至 2025-11-21

**每日监控任务**:
```sql
-- 任务 1: 检查异常时间值（每日执行）
SELECT
    table_name,
    COUNT(*) FILTER (WHERE time_field > NOW()) AS future_count,
    COUNT(*) FILTER (WHERE time_field < '2020-01-01'::TIMESTAMPTZ) AS too_early_count
FROM (
    SELECT 'projects' AS table_name, created_at AS time_field FROM projects
    UNION ALL
    SELECT 'projects', updated_at FROM projects
    -- ... 其他表
) t
GROUP BY table_name;

-- 预期结果: 所有 future_count = 0, too_early_count = 0
```

**通过标准**:
- ✅ 3 天无异常时间值
- ✅ 应用日志无时区相关错误
- ✅ 所有业务功能正常（项目创建、充值、账本）

**观察期结束**: 可进入 Phase 2B

---

### 3.2 Phase 2B: permissions JSONB + severity 枚举修复

#### 3.2.1 Rev 2B-001: project_members.permissions Text → JSONB

**Scope**:
- 表: project_members
- 字段: permissions
- 当前类型: Text
- 目标类型: JSONB
- SoT 依据: DATA_SCHEMA.md § 3.2.2

**策略**: Strategy B（置空 + legacy 备份）

**SQL**:
```sql
-- ==================================================
-- Rev 2B-001: project_members.permissions Text → JSONB
-- SoT: DATA_SCHEMA.md v5.0 § 3.2.2
-- Reversible: YES (保留 legacy 列)
-- ==================================================

-- Step 1: 添加备份列
ALTER TABLE project_members
  ADD COLUMN IF NOT EXISTS permissions_legacy TEXT;

-- Step 2: 备份当前值
UPDATE project_members
  SET permissions_legacy = permissions;

-- Step 3: 清理无效数据
UPDATE project_members
  SET permissions = '{}'
  WHERE permissions IS NULL OR permissions = '' OR permissions = 'null';

-- Step 4: 验证 JSON 有效性（PL/pgSQL）
DO $$
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN SELECT id, permissions FROM project_members WHERE permissions IS NOT NULL LOOP
        BEGIN
            PERFORM permissions::JSONB FROM project_members WHERE id = rec.id;
        EXCEPTION WHEN OTHERS THEN
            UPDATE project_members SET permissions = '{}' WHERE id = rec.id;
            RAISE NOTICE 'Invalid JSON in row %, set to {}', rec.id;
        END;
    END LOOP;
END $$;

-- Step 5: 转换列类型
ALTER TABLE project_members
  ALTER COLUMN permissions TYPE JSONB USING permissions::JSONB;

-- Step 6: 设置默认值
ALTER TABLE project_members
  ALTER COLUMN permissions SET DEFAULT '{}';
```

**Gate 验证**:
```sql
-- Check 1: 类型验证
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'project_members' AND column_name = 'permissions';
-- 预期: data_type = 'jsonb', column_default = '{}'::text

-- Check 2: JSONB 有效性
SELECT
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE jsonb_typeof(permissions) = 'object') AS valid_json_count,
    COUNT(permissions_legacy) AS legacy_backup_count
FROM project_members;
-- 预期: valid_json_count = total, legacy_backup_count = total
```

**回滚 SQL**:
```sql
ALTER TABLE project_members
  ALTER COLUMN permissions TYPE TEXT USING permissions::TEXT;
UPDATE project_members SET permissions = permissions_legacy;
ALTER TABLE project_members DROP COLUMN permissions_legacy;
```

---

#### 3.2.2 Rev 2B-002: account_alerts.severity 枚举值修复

**Scope**:
- 表: account_alerts
- 字段: severity
- 当前枚举: low/medium/high/critical
- 目标枚举: info/warning/critical
- SoT 依据: DATA_SCHEMA.md § 3.2.9

**策略**: 枚举值映射 + legacy 备份

**SQL**:
```sql
-- ==================================================
-- Rev 2B-002: account_alerts.severity 枚举值修复
-- SoT: DATA_SCHEMA.md v5.0 § 3.2.9
-- Reversible: YES (保留 legacy 列)
-- ==================================================

-- Step 1: 添加备份列
ALTER TABLE account_alerts
  ADD COLUMN IF NOT EXISTS severity_legacy VARCHAR(20);

-- Step 2: 备份当前值
UPDATE account_alerts
  SET severity_legacy = severity;

-- Step 3: 删除旧 CHECK 约束
ALTER TABLE account_alerts
  DROP CONSTRAINT IF EXISTS check_alert_severity;

-- Step 4: 映射枚举值
UPDATE account_alerts SET severity = CASE
    WHEN severity = 'low' THEN 'info'
    WHEN severity = 'medium' THEN 'warning'
    WHEN severity = 'high' THEN 'warning'
    WHEN severity = 'critical' THEN 'critical'
    WHEN severity IN ('info', 'warning') THEN severity  -- 已是新值，保持
    ELSE 'info'  -- 默认值
END;

-- Step 5: 添加新 CHECK 约束
ALTER TABLE account_alerts
  ADD CONSTRAINT check_alert_severity
  CHECK (severity IN ('info', 'warning', 'critical'));
```

**Gate 验证**:
```sql
-- Check 1: 枚举值验证
SELECT severity, COUNT(*)
FROM account_alerts
GROUP BY severity
ORDER BY severity;
-- 预期: 只有 'info', 'warning', 'critical'

-- Check 2: CHECK 约束验证
SELECT pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'account_alerts'::regclass
  AND conname = 'check_alert_severity';
-- 预期: 包含 info, warning, critical
```

**回滚 SQL**:
```sql
UPDATE account_alerts SET severity = severity_legacy;
ALTER TABLE account_alerts DROP CONSTRAINT check_alert_severity;
ALTER TABLE account_alerts ADD CONSTRAINT check_alert_severity
  CHECK (severity IN ('low', 'medium', 'high', 'critical'));
ALTER TABLE account_alerts DROP COLUMN severity_legacy;
```

---

#### 3.2.3 Phase 2B 观察期（7 天）

**观察时间**: Phase 2B 执行后 7 天

**监控指标**:
```sql
-- 每日检查: permissions JSONB 异常
SELECT id, permissions, permissions_legacy
FROM project_members
WHERE jsonb_typeof(permissions) IS NULL
   OR jsonb_typeof(permissions) NOT IN ('null', 'object')
LIMIT 10;

-- 每日检查: severity 非法值
SELECT severity, COUNT(*)
FROM account_alerts
WHERE severity NOT IN ('info', 'warning', 'critical')
GROUP BY severity;
```

**通过标准**: 7 天无异常值，应用功能正常

**观察期结束**: 可进入 Phase 2C（或删除 legacy 列）

---

### 3.3 Phase 2C: 未定义字段处理（最终决议）

#### 3.3.1 问题描述

**发现**: ad_accounts 表存在 12 个字段未在 DATA_SCHEMA.md 中定义

**字段清单** (backend/models/ad_account.py:81-102):
```python
# 统计字段
total_spend       = Column(DECIMAL(15, 2), default=0, comment="总消耗")
total_leads       = Column(Integer, default=0, comment="总潜在客户数")
avg_cpl           = Column(DECIMAL(10, 2), nullable=True, comment="平均单粉成本")
best_cpl          = Column(DECIMAL(10, 2), nullable=True, comment="最佳单粉成本")

# 开户费用
setup_fee         = Column(DECIMAL(10, 2), default=0, comment="开户费")
setup_fee_paid    = Column(Boolean, default=False, comment="开户费是否已支付")

# 账户配置
account_type      = Column(String(50), nullable=True, comment="账户类型")
payment_method    = Column(String(50), nullable=True, comment="支付方式")
billing_information = Column(JSON, nullable=True, comment="账单信息")

# 监控和标签
auto_monitoring   = Column(Boolean, default=True, comment="自动监控")
alert_thresholds  = Column(JSON, nullable=True, comment="预警阈值设置")
tags              = Column(JSON, nullable=True, comment="标签")
```

**另外**: account_documents 表存在 1 个未定义的 status 字段

---

#### 3.3.2 可选方案对比

| 方案 | 优点 | 缺点 | 风险 |
| --- | --- | --- | --- |
| **选项 1: 补充到 DATA_SCHEMA** | 无需迁移代码<br/>保留类型安全<br/>查询性能最优 | 增加文档维护负担 | 低 |
| 选项 2: 迁移到 JSONB | 表结构更简洁<br/>完全符合原始 SoT | 大规模代码重构<br/>失去类型安全<br/>查询性能下降 | 高 |

---

#### 3.3.3 最终决议：选择选项 1

**决策理由**:

1. **最小化风险原则**
   - 这些字段已在生产环境使用
   - 迁移到 JSONB 需要重写所有相关业务代码
   - 回归测试范围过大

2. **性能考虑**
   - 原生字段查询性能 > JSONB 查询
   - 统计字段（total_spend, total_leads）频繁被聚合查询

3. **类型安全**
   - 原生字段有 PostgreSQL 类型约束
   - JSONB 失去编译时类型检查

4. **符合 SoT 补充机制**
   - DATA_SCHEMA.md § 5 允许规划表登记
   - 补充文档是合规的扩展方式

---

#### 3.3.4 执行方案：更新 DATA_SCHEMA.md

**目标文件**: `docs/core/DATA_SCHEMA.md`

**修改位置**: § 3.2.9 `ad_accounts` 表定义

**新增内容**:
```markdown
#### 3.2.9 `ad_accounts` - 扩展字段（Phase 2C 补充）

以下字段为业务功能扩展字段，不属于核心字段：

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `total_spend` | DECIMAL(15,2) | DEFAULT 0.00 | 总消耗（统计字段，由定时任务更新） |
| `total_leads` | INTEGER | DEFAULT 0 | 总潜在客户数（统计字段） |
| `avg_cpl` | DECIMAL(10,2) | 可空 | 平均单粉成本（统计字段） |
| `best_cpl` | DECIMAL(10,2) | 可空 | 最佳单粉成本（统计字段） |
| `setup_fee` | DECIMAL(10,2) | DEFAULT 0.00 | 开户费 |
| `setup_fee_paid` | BOOLEAN | DEFAULT false | 开户费是否已支付 |
| `account_type` | VARCHAR(50) | 可空 | 账户类型（如个人/企业） |
| `payment_method` | VARCHAR(50) | 可空 | 支付方式 |
| `billing_information` | JSONB | 可空 | 账单信息 |
| `auto_monitoring` | BOOLEAN | DEFAULT true | 自动监控开关 |
| `alert_thresholds` | JSONB | 可空 | 预警阈值设置 |
| `tags` | JSONB | 可空 | 标签（用于分类和筛选） |

**说明**:
- 统计字段由 `backend/services/account_statistics.py` 定时更新
- billing_information 和 alert_thresholds 的 JSONB schema 待补充
- 这些字段保留以支持现有业务逻辑，不属于 Phase 2 迁移范围
```

**account_documents.status** 同理补充：
```markdown
#### 3.2.9 `account_documents` - 扩展字段

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `status` | VARCHAR(20) | DEFAULT 'active' | 文档状态（active/archived/deleted） |
```

---

#### 3.3.5 Phase 2C 执行步骤

**无需数据库迁移**，仅需文档更新：

1. **更新 DATA_SCHEMA.md**
   - 在 § 3.2.9 添加上述字段定义
   - 更新文档版本：v5.0 → v5.1

2. **更新代码注释**
   - `backend/models/ad_account.py` 添加注释标注字段已合规

3. **更新本文档**
   - 将 Phase 2C 标记为 "Completed"

**预计工作量**: 2 小时（纯文档工作）

**风险**: 无（无代码变更）

---

## 四、环境与审批流程

### 4.1 环境执行顺序

```
Dev 环境 → 观察 3-7 天 → Staging 环境 → 观察 7 天 → Prod 环境（可选）
```

### 4.2 Dev 环境执行流程

**前置条件**:
- [ ] Supabase Dashboard 快照已创建
- [ ] DATABASE_URL 确认指向 Dev
- [ ] 7 个目标表存在性验证通过
- [ ] Alembic 配置正确

**执行权限**: DBA 或系统架构师

**执行步骤**:
```bash
# Step 1: 执行 Phase 2A
cd backend
alembic upgrade phase2a_003

# Step 2: Gate 验证
psql $DATABASE_URL -f phase2a_gate_verification.sql

# Step 3: 观察期（3 天）
# 每日执行监控 SQL

# Step 4: 如果 Phase 2A 通过，执行 Phase 2B
# （创建 Phase 2B 的 Alembic 脚本并执行）

# Step 5: Phase 2B 观察期（7 天）

# Step 6: 执行 Phase 2C（文档更新）
```

**回滚条件**:
- Gate 验证失败
- 观察期发现异常时间值或 JSONB 错误
- 应用功能测试失败

**回滚方式**:
```bash
# Alembic 回滚
alembic downgrade <phase2a之前的revision>

# 或 Supabase 快照恢复
```

---

### 4.3 Staging 环境执行流程

**前置条件**:
- [ ] Dev 环境 Phase 2A/2B 观察期通过（至少 7 天）
- [ ] 所有 Gate 验证通过
- [ ] SQLAlchemy 模型代码已更新并测试
- [ ] 业务团队审批通过

**执行权限**: 需要 **DBA + 项目经理** 双重审批

**执行步骤**: 同 Dev 环境，但要求：
- 快照保留期延长到 30 天
- 观察期延长到 14 天
- 每日提交观察报告

**禁止操作**:
- ❌ 在 Staging 发现新问题时现场修改迁移范围
- ❌ 跳过任何 Gate 验证
- ❌ 缩短观察期

---

### 4.4 Prod 环境执行流程（如需要）

**说明**: Phase 2 主要针对 Dev 环境的 Schema 规范化，通常**不需要**在 Prod 执行。

**如果 Prod 需要执行**（如 Staging → Prod 同步），必须满足：

**前置条件**:
- [ ] Staging 环境运行 30 天以上无问题
- [ ] 业务团队、CTO、DBA 团队三方审批
- [ ] 选择业务低峰期时间窗口（如凌晨 2-4 点）
- [ ] 准备回滚预案和应急联系人

**执行权限**: 需要 **CTO 书面审批**

**时间窗口**: 必须在业务低峰期，预留 4 小时执行时间

**监控要求**:
- 实时监控数据库 CPU、内存、连接数
- 实时监控应用错误率
- 准备 DBA on-call

**紧急回滚**: 发现任何异常立即回滚，不等待分析

---

### 4.5 审批流程图

```
Dev 环境
├── 执行权限: DBA
├── 审批要求: 无（技术决策）
└── 回滚决策: DBA 决定

Staging 环境
├── 执行权限: DBA + 项目经理审批
├── 审批要求: 邮件 + JIRA 工单
└── 回滚决策: 项目经理 + DBA 共同决定

Prod 环境
├── 执行权限: CTO 书面审批
├── 审批要求: 正式变更申请（提前 7 天）
└── 回滚决策: CTO 授权
```

---

## 五、禁止事项与后续变更策略

### 5.1 迁移期间禁止事项

**规则 1: 禁止扩展迁移范围**
```
❌ 禁止: 执行中发现新问题立即添加到当前 Phase
✅ 正确: 记录到 PROJECT_RISKS.md，纳入下一个 Phase
```

**规则 2: 禁止跳过 Gate 验证**
```
❌ 禁止: "Gate 验证失败但问题不大，继续执行"
✅ 正确: Gate 失败立即停止，分析原因后重新执行
```

**规则 3: 禁止修改 SoT**
```
❌ 禁止: 执行期间修改 DATA_SCHEMA.md
✅ 正确: 执行前锁定 SoT 版本，执行后再更新
```

**规则 4: 禁止删除 legacy 列（观察期内）**
```
❌ 禁止: Phase 2B 执行后立即删除 permissions_legacy, severity_legacy
✅ 正确: 保留至少 7 天观察期，确认无问题后再删除
```

---

### 5.2 新发现问题的处理方式

**场景 1: 执行中发现额外的时间字段缺少 timezone**

**错误做法**:
```
❌ 立即添加到 Phase 2A，扩展迁移范围
```

**正确做法**:
```
✅ Step 1: 记录到 docs/PROJECT_RISKS.md
✅ Step 2: 创建 JIRA issue（标记为 Phase 2.1 或 Phase 3）
✅ Step 3: 完成当前 Phase 2A 后，再规划下一轮迁移
```

---

**场景 2: Gate 验证发现数据异常**

**错误做法**:
```
❌ 修改 Gate 验证标准以通过验证
```

**正确做法**:
```
✅ Step 1: 立即停止迁移
✅ Step 2: 回滚到迁移前状态
✅ Step 3: 分析数据异常原因（可能是数据质量问题）
✅ Step 4: 修复数据后重新执行迁移
```

---

**场景 3: 观察期发现业务功能异常**

**错误做法**:
```
❌ "暂时忽略，等观察期结束再说"
```

**正确做法**:
```
✅ Step 1: 立即执行紧急回滚
✅ Step 2: 分析功能异常与迁移的因果关系
✅ Step 3: 修复业务代码（如时区处理逻辑）
✅ Step 4: 重新评估迁移方案
```

---

### 5.3 紧急回滚流程

**触发条件**:
- Gate 验证失败
- 观察期发现数据异常
- 应用功能异常
- 数据库性能严重下降

**回滚步骤**:

**方式 1: Alembic 回滚（推荐）**
```bash
# 1. 确认当前 revision
alembic current

# 2. 回滚到 Phase 2 之前的 revision
alembic downgrade <phase2之前的revision>

# 3. 验证回滚成功
psql $DATABASE_URL -f verify_rollback.sql
```

**方式 2: SQL 手动回滚**
```bash
# 执行回滚 SQL（参考各 Rev 的 Rollback SQL）
psql $DATABASE_URL -f rollback_phase2a.sql
```

**方式 3: Supabase 快照恢复（最后手段）**
```
1. 登录 Supabase Dashboard
2. Settings → Database → Backups
3. 选择 Phase 2 执行前的快照
4. 点击 Restore（不可逆操作，慎重！）
```

**回滚后必须执行**:
```bash
# 1. 验证数据完整性
SELECT COUNT(*) FROM projects;
# ... 检查所有相关表

# 2. 重启应用服务
# 3. 通知业务团队
# 4. 记录回滚原因到 PROJECT_RISKS.md
```

---

### 5.4 文档更新清单

**Phase 2 完成后，必须更新以下文档**:

#### 规范层（SoT）
- [ ] `DATA_SCHEMA.md` - 补充 Phase 2C 的字段定义（v5.0 → v5.1）
- [ ] `DATABASE_SCHEMA_MIGRATION_PLAN.md` - 标记 Phase 2 为 "Completed"
- [ ] `MIGRATION_EXECUTION_GUIDE.md` - 添加 Phase 2 执行经验总结

#### 执行层
- [ ] `backend/models/projects.py` - 更新时间字段类型注释
- [ ] `backend/models/topup.py` - 更新所有时间字段
- [ ] `backend/models/ledger.py` - 更新 occurred_at
- [ ] `backend/models/ad_account.py` - 添加字段合规注释

#### 记录层
- [ ] `CHANGELOG.md` - 记录 Phase 2 变更历史
- [ ] `docs/PROJECT_RISKS.md` - 记录 Phase 2 观察期结果
- [ ] `docs/dev/MIGRATION_LOG.md` - 记录详细执行日志

#### Alembic
- [ ] `backend/alembic/README.md` - 更新 revision 历史

**更新时间**: Phase 2 完成后 3 个工作日内

**责任人**: DBA 或数据库架构师

---

### 5.5 Phase 2 后续演进策略

**Phase 2 完成标志**:
- ✅ Phase 2A/2B/2C 全部执行完成
- ✅ 所有 Gate 验证通过
- ✅ 观察期无问题
- ✅ 文档更新完成
- ✅ DATA_SCHEMA.md 符合度 = 100%

**下一步（Phase 3 规划）**:
```
可能的 Phase 3 内容（待确认）:
- channels 表的字段规范化
- user_profiles 表的扩展字段补充
- 索引优化（基于生产查询分析）
- RLS 策略启用（如果业务需要）
```

**Phase 3 启动条件**:
- Phase 2 在 Staging 环境运行 30 天以上
- 发现新的 Schema 差异（需要新的差异分析报告）
- 业务需求驱动（如新功能需要新表结构）

---

## 六、附录

### 6.1 文件清单

**Phase 2 相关文件（本次生成）**:

| 文件路径 | 类型 | 用途 |
| --- | --- | --- |
| `docs/core/PHASE2_MIGRATION_MASTER.md` | 主文档 | 本文档（最终版） |
| `docs/core/PHASE2_SCHEMA_DIFF_ANALYSIS.md` | 分析报告 | 原始差异分析（归档） |
| `docs/core/PHASE2_MIGRATION_PLAN_APPEND.md` | 执行方案 | 原始迁移方案（归档） |
| `backend/alembic/versions/20251118_phase2a_001_*.py` | Alembic | Phase 2A-001 脚本 |
| `backend/alembic/versions/20251118_phase2a_002_*.py` | Alembic | Phase 2A-002 脚本 |
| `backend/alembic/versions/20251118_phase2a_003_*.py` | Alembic | Phase 2A-003 脚本 |
| `backend/phase2a_gate_verification.sql` | SQL | Phase 2A Gate 验证 |
| `backend/PHASE2A_EXECUTION_GUIDE.md` | 指南 | Phase 2A 执行指南 |
| `backend/execute_phase2a.py` | Python | Phase 2A 备用执行脚本 |

**SoT 文件（需要引用）**:

| 文件路径 | 版本 | 相关章节 |
| --- | --- | --- |
| `docs/core/DATA_SCHEMA.md` | v5.0 | § 1.1, § 3.2, § 3.4 |
| `docs/core/STATE_MACHINE.md` | v2.x | （本次未涉及） |
| `docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md` | v3.0 | 实现规范 |
| `docs/core/MIGRATION_EXECUTION_GUIDE.md` | v1.2 | § 2, § 3, § 6 |
| `docs/core/DATABASE_SCHEMA_MIGRATION_PLAN.md` | - | Phase 总体规划 |

---

### 6.2 术语表

| 术语 | 定义 |
| --- | --- |
| **SoT (Single Source of Truth)** | 唯一事实来源，指 DATA_SCHEMA.md 等规范文档 |
| **Phase** | 数据库迁移的大阶段（如 Phase 1, Phase 2） |
| **Rev (Revision)** | Alembic 迁移的具体版本（如 Rev 2A-001） |
| **Gate** | 验证检查点，用于确保迁移成功 |
| **Strategy B** | 数据迁移策略：置 NULL + legacy 备份 |
| **Legacy 列** | 备份列，用于保留迁移前的原始数据 |
| **观察期** | 迁移后的监控期，通常 3-7 天 |
| **可逆 (Reversible)** | 可以通过 `alembic downgrade` 回滚 |
| **不可逆 (Irreversible)** | 只能通过快照恢复回滚 |

---

### 6.3 常见问题（FAQ）

**Q1: Phase 2 是否会影响生产环境？**
A: 不会。Phase 2 主要针对 Dev 环境的 Schema 规范化。只有在 Staging 环境验证 30 天后，且业务明确需要，才会考虑在 Prod 执行。

**Q2: 为什么选择选项 1（补充文档）而不是选项 2（迁移到 JSONB）？**
A: 选项 1 风险最低，无需重构业务代码，且保留了类型安全和查询性能。

**Q3: 观察期可以缩短吗？**
A: 不建议。MIGRATION_EXECUTION_GUIDE § 6 规定观察期为 3-7 天，这是基于历史经验的最小安全期。

**Q4: 如果 Gate 验证失败怎么办？**
A: 立即停止，不要继续执行后续步骤。回滚到迁移前状态，分析失败原因后重新执行。

**Q5: Phase 2 完成后，legacy 列可以删除吗？**
A: 建议至少保留 30 天。如果业务团队确认无需回溯历史数据，可以在 Phase 2 完成后的下一个维护窗口删除。

**Q6: 如何确保 Phase 2 不会引入新的 Schema 差异？**
A: 所有字段定义必须严格引用 DATA_SCHEMA.md。如果发现 DATA_SCHEMA 缺失，先更新 DATA_SCHEMA，再执行迁移。

---

### 6.4 联系方式

| 角色 | 联系方式 | 职责 |
| --- | --- | --- |
| DBA 团队 | dba@example.com | 迁移执行、Gate 验证、紧急回滚 |
| 数据库架构师 | architect@example.com | Schema 设计、SoT 维护、技术决策 |
| 项目经理 | pm@example.com | Staging/Prod 审批、业务协调 |
| CTO | cto@example.com | Prod 环境最终审批 |

---

**文档版本**: v2.0 (Final)
**发布日期**: 2025-11-18
**下一步**: 执行 Phase 2A（Dev 环境）
**预计完成**: 2025-12-01（包含观察期）
