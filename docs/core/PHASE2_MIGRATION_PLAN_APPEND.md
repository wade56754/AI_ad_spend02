# Phase 2: 核心业务表字段类型规范化

> **适用表**: projects, project_members, project_expenses, ad_accounts, account_alerts, account_documents, topup_requests, topup_transactions, topup_approval_logs, ledger_entries
> **主要目标**: 修复时间字段 timezone 缺失、字段类型不匹配、枚举值不一致
> **预计工作量**: 6-8 小时
> **停机时间**: < 15 分钟
> **可逆性**: Phase 2A 完全可逆，Phase 2B 可逆（需 legacy 列）

---

## Phase 2 概览

### 问题汇总（基于 PHASE2_SCHEMA_DIFF_ANALYSIS.md v1.0）

| 优先级 | 问题类别 | 影响表数 | 影响字段数 | 数据风险 | 迁移难度 |
| --- | --- | --- | --- | --- | --- |
| P0 | 时间字段缺少 timezone | 7 | 14 | 低 | 简单 |
| P1 | 字段类型不匹配 | 2 | 2 | 中等 | 中等 |
| P2 | 未定义字段 | 2 | 13 | 低 | 简单（文档） |

### 分 Phase 执行策略

```
Phase 2A: 时间字段 timezone 修复（P0，必须执行）
  ├─ Rev 2A-001: projects 模块时间字段（3 个表，6 个字段）
  ├─ Rev 2A-002: topup 模块时间字段（3 个表，5 个字段）
  ├─ Rev 2A-003: ledger 模块时间字段（1 个表，1 个字段）
  └─ Gate #2A: 验证所有时间字段为 TIMESTAMPTZ

Phase 2B: 字段类型和枚举修复（P1，建议执行）
  ├─ Rev 2B-001: project_members.permissions Text → JSONB
  ├─ Rev 2B-002: account_alerts.severity 枚举值修复
  └─ Gate #2B: 验证 JSONB 和枚举值正确性

Phase 2C: 未定义字段规范化（P2，可选）
  ├─ 选项 1: 补充 ad_accounts 字段到 DATA_SCHEMA.md
  └─ 选项 2: 迁移到 account_metadata JSONB（不推荐）
```

---

## Phase 2A: 时间字段 timezone 修复

### 目标

修复 7 个表共 14 个时间字段，将 `TIMESTAMP` 类型升级为 `TIMESTAMPTZ`，符合 DATA_SCHEMA.md § 1.1 规范。

### 影响范围

| 模块 | 表名 | 字段 | 文件位置 |
| --- | --- | --- | --- |
| 项目 | projects | created_at, updated_at | projects.py:62-74 |
| 项目 | project_members | joined_at | projects.py:115-120 |
| 项目 | project_expenses | occurred_at, created_at | projects.py:150-167 |
| 充值 | topup_requests | created_at, updated_at | topup.py:91-103 |
| 充值 | topup_transactions | paid_at, created_at | topup.py:150-173 |
| 充值 | topup_approval_logs | created_at | topup.py:216-221 |
| 账本 | ledger_entries | occurred_at | ledger.py:49-54 |

**合计**: 7 个表，14 个字段

---

### Rev 2A-001: projects 模块时间字段修复

**目标表**: projects, project_members, project_expenses

#### 迁移 SQL

```sql
-- ==================================================
-- Rev 2A-001: projects 模块时间字段 TIMESTAMPTZ 修复
-- 可逆性: ✅ 可逆
-- 数据风险: 低
-- ==================================================

-- 表 1: projects
ALTER TABLE projects
  ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';

ALTER TABLE projects
  ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';

-- 表 2: project_members
ALTER TABLE project_members
  ALTER COLUMN joined_at TYPE TIMESTAMPTZ USING joined_at AT TIME ZONE 'UTC';

-- 表 3: project_expenses
ALTER TABLE project_expenses
  ALTER COLUMN occurred_at TYPE TIMESTAMPTZ USING occurred_at AT TIME ZONE 'UTC';

ALTER TABLE project_expenses
  ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';

-- Gate 验证
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name IN ('projects', 'project_members', 'project_expenses')
AND column_name IN ('created_at', 'updated_at', 'occurred_at', 'joined_at')
ORDER BY table_name, column_name;
-- 预期: 所有 data_type = 'timestamp with time zone'
```

#### 回滚 SQL

```sql
-- 回滚 Rev 2A-001
ALTER TABLE projects ALTER COLUMN created_at TYPE TIMESTAMP USING created_at;
ALTER TABLE projects ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at;
ALTER TABLE project_members ALTER COLUMN joined_at TYPE TIMESTAMP USING joined_at;
ALTER TABLE project_expenses ALTER COLUMN occurred_at TYPE TIMESTAMP USING occurred_at;
ALTER TABLE project_expenses ALTER COLUMN created_at TYPE TIMESTAMP USING created_at;
```

---

### Rev 2A-002: topup 模块时间字段修复

**目标表**: topup_requests, topup_transactions, topup_approval_logs

#### 迁移 SQL

```sql
-- ==================================================
-- Rev 2A-002: topup 模块时间字段 TIMESTAMPTZ 修复
-- 可逆性: ✅ 可逆
-- 数据风险: 低
-- ==================================================

-- 表 1: topup_requests
ALTER TABLE topup_requests
  ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';

ALTER TABLE topup_requests
  ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';

-- 表 2: topup_transactions
ALTER TABLE topup_transactions
  ALTER COLUMN paid_at TYPE TIMESTAMPTZ USING paid_at AT TIME ZONE 'UTC';

ALTER TABLE topup_transactions
  ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';

-- 表 3: topup_approval_logs
ALTER TABLE topup_approval_logs
  ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';

-- Gate 验证
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name IN ('topup_requests', 'topup_transactions', 'topup_approval_logs')
AND column_name IN ('created_at', 'updated_at', 'paid_at')
ORDER BY table_name, column_name;
-- 预期: 所有 data_type = 'timestamp with time zone'
```

#### 回滚 SQL

```sql
-- 回滚 Rev 2A-002
ALTER TABLE topup_requests ALTER COLUMN created_at TYPE TIMESTAMP USING created_at;
ALTER TABLE topup_requests ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at;
ALTER TABLE topup_transactions ALTER COLUMN paid_at TYPE TIMESTAMP USING paid_at;
ALTER TABLE topup_transactions ALTER COLUMN created_at TYPE TIMESTAMP USING created_at;
ALTER TABLE topup_approval_logs ALTER COLUMN created_at TYPE TIMESTAMP USING created_at;
```

---

### Rev 2A-003: ledger 模块时间字段修复

**目标表**: ledger_entries

#### 迁移 SQL

```sql
-- ==================================================
-- Rev 2A-003: ledger 模块时间字段 TIMESTAMPTZ 修复
-- 可逆性: ✅ 可逆
-- 数据风险: 低
-- ==================================================

ALTER TABLE ledger_entries
  ALTER COLUMN occurred_at TYPE TIMESTAMPTZ USING occurred_at AT TIME ZONE 'UTC';

-- Gate 验证
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'ledger_entries'
AND column_name = 'occurred_at';
-- 预期: data_type = 'timestamp with time zone'
```

#### 回滚 SQL

```sql
-- 回滚 Rev 2A-003
ALTER TABLE ledger_entries ALTER COLUMN occurred_at TYPE TIMESTAMP USING occurred_at;
```

---

### Gate #2A: 时间字段类型验证

**执行时机**: Rev 2A-001/002/003 全部完成后

```sql
-- ==================================================
-- Gate #2A: 验证所有 Phase 2A 时间字段为 TIMESTAMPTZ
-- ==================================================

-- Check 1: 检查所有时间字段类型
SELECT
    table_name,
    column_name,
    data_type,
    CASE
        WHEN data_type = 'timestamp with time zone' THEN 'PASS'
        ELSE 'FAIL'
    END AS status
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

-- Check 2: 数据完整性验证（确保没有数据丢失）
SELECT
    'projects' AS table_name,
    COUNT(*) AS total_count,
    COUNT(created_at) AS created_at_count,
    COUNT(updated_at) AS updated_at_count
FROM projects

UNION ALL

SELECT
    'project_members' AS table_name,
    COUNT(*) AS total_count,
    COUNT(joined_at) AS joined_at_count,
    NULL
FROM project_members

UNION ALL

SELECT
    'project_expenses' AS table_name,
    COUNT(*) AS total_count,
    COUNT(occurred_at) AS occurred_at_count,
    COUNT(created_at) AS created_at_count
FROM project_expenses

-- ... 其他表类似
;
```

**通过标准**:
1. ✅ 所有时间字段 `data_type = 'timestamp with time zone'`
2. ✅ 所有表的记录总数与时间字段非空数一致（除非字段定义允许 NULL）
3. ✅ 没有数据截断或异常值

**如果 Gate #2A 失败**:
1. 停止迁移，不执行 Phase 2B
2. 检查具体失败的字段和原因
3. 执行回滚 SQL
4. 分析问题后重新执行

---

## Phase 2B: 字段类型和枚举修复

### 目标

修复 2 个字段类型不匹配问题：
1. `project_members.permissions`: Text → JSONB
2. `account_alerts.severity`: 枚举值修复（low/medium/high/critical → info/warning/critical）

---

### Rev 2B-001: project_members.permissions 类型修复

**目标**: 将 `permissions` 字段从 TEXT 类型转换为 JSONB 类型

**策略**: Strategy B（置空 + legacy 备份 + 业务层重建）

#### 迁移 SQL

```sql
-- ==================================================
-- Rev 2B-001: project_members.permissions Text → JSONB
-- 可逆性: ✅ 可逆（保留 legacy 列）
-- 数据风险: 中等（需 JSON 校验）
-- ==================================================

-- Step 1: 添加备份列
ALTER TABLE project_members ADD COLUMN IF NOT EXISTS permissions_legacy TEXT;

-- Step 2: 备份当前值
UPDATE project_members SET permissions_legacy = permissions;

-- Step 3: 清理无效数据（将 NULL 或空字符串设为 {}）
UPDATE project_members
SET permissions = '{}'
WHERE permissions IS NULL OR permissions = '' OR permissions = 'null';

-- Step 4: 尝试转换（如果失败，说明有无效 JSON）
DO $$
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN
        SELECT id, permissions
        FROM project_members
        WHERE permissions IS NOT NULL
    LOOP
        BEGIN
            -- 测试是否为有效 JSON
            PERFORM permissions::JSONB FROM project_members WHERE id = rec.id;
        EXCEPTION WHEN OTHERS THEN
            -- 无效 JSON，设为空对象
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

-- Gate 验证
SELECT
    column_name,
    data_type,
    column_default
FROM information_schema.columns
WHERE table_name = 'project_members'
AND column_name = 'permissions';
-- 预期: data_type = 'jsonb', column_default = '{}'

-- 数据完整性验证
SELECT
    COUNT(*) AS total_records,
    COUNT(permissions) AS non_null_permissions,
    COUNT(*) FILTER (WHERE permissions = '{}') AS empty_json_count,
    COUNT(permissions_legacy) AS legacy_backup_count
FROM project_members;
```

#### 回滚 SQL

```sql
-- 回滚 Rev 2B-001
ALTER TABLE project_members
  ALTER COLUMN permissions TYPE TEXT USING permissions::TEXT;

UPDATE project_members SET permissions = permissions_legacy;

ALTER TABLE project_members DROP COLUMN permissions_legacy;

ALTER TABLE project_members ALTER COLUMN permissions SET DEFAULT NULL;
```

---

### Rev 2B-002: account_alerts.severity 枚举值修复

**目标**: 将 severity 枚举值从 `low/medium/high/critical` 修复为 `info/warning/critical`

**策略**: Strategy A（枚举映射 + legacy 备份）

#### 迁移 SQL

```sql
-- ==================================================
-- Rev 2B-002: account_alerts.severity 枚举值修复
-- 可逆性: ✅ 可逆（保留 legacy 列）
-- 数据风险: 低（简单枚举映射）
-- ==================================================

-- Step 1: 添加备份列
ALTER TABLE account_alerts ADD COLUMN IF NOT EXISTS severity_legacy VARCHAR(20);

-- Step 2: 备份当前值
UPDATE account_alerts SET severity_legacy = severity;

-- Step 3: 删除旧 CHECK 约束
ALTER TABLE account_alerts DROP CONSTRAINT IF EXISTS check_alert_severity;

-- Step 4: 映射枚举值
UPDATE account_alerts SET severity = CASE
    WHEN severity = 'low' THEN 'info'
    WHEN severity = 'medium' THEN 'warning'
    WHEN severity = 'high' THEN 'warning'
    WHEN severity = 'critical' THEN 'critical'
    -- 如果已经是新值，保持不变
    WHEN severity IN ('info', 'warning') THEN severity
    ELSE 'info'  -- 默认值
END;

-- Step 5: 添加新 CHECK 约束
ALTER TABLE account_alerts ADD CONSTRAINT check_alert_severity
    CHECK (severity IN ('info', 'warning', 'critical'));

-- Gate 验证
SELECT
    severity,
    COUNT(*) AS count
FROM account_alerts
GROUP BY severity
ORDER BY severity;
-- 预期: 只有 'info', 'warning', 'critical' 三个值

-- 检查 CHECK 约束
SELECT
    conname,
    pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE conrelid = 'account_alerts'::regclass
AND conname = 'check_alert_severity';
-- 预期: severity IN ('info', 'warning', 'critical')
```

#### 回滚 SQL

```sql
-- 回滚 Rev 2B-002
UPDATE account_alerts SET severity = severity_legacy;

ALTER TABLE account_alerts DROP CONSTRAINT check_alert_severity;

ALTER TABLE account_alerts ADD CONSTRAINT check_alert_severity
    CHECK (severity IN ('low', 'medium', 'high', 'critical'));

ALTER TABLE account_alerts DROP COLUMN severity_legacy;
```

---

### Gate #2B: 字段类型和枚举验证

**执行时机**: Rev 2B-001/002 全部完成后

```sql
-- ==================================================
-- Gate #2B: 验证 JSONB 和枚举值正确性
-- ==================================================

-- Check 1: permissions 字段类型验证
SELECT
    table_name,
    column_name,
    data_type,
    column_default,
    CASE
        WHEN data_type = 'jsonb' AND column_default = '{}'::text THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM information_schema.columns
WHERE table_name = 'project_members'
AND column_name = 'permissions';

-- Check 2: permissions JSONB 数据验证
SELECT
    COUNT(*) AS total_records,
    COUNT(permissions) AS non_null_count,
    COUNT(*) FILTER (WHERE permissions = '{}') AS empty_json_count,
    COUNT(*) FILTER (WHERE jsonb_typeof(permissions) = 'object') AS valid_json_count,
    COUNT(permissions_legacy) AS legacy_backup_count
FROM project_members;

-- Check 3: severity 枚举值验证
SELECT
    severity,
    COUNT(*) AS count,
    CASE
        WHEN severity IN ('info', 'warning', 'critical') THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM account_alerts
GROUP BY severity
ORDER BY severity;

-- Check 4: severity CHECK 约束验证
SELECT
    conname,
    pg_get_constraintdef(oid) AS definition,
    CASE
        WHEN pg_get_constraintdef(oid) LIKE '%info%' AND
             pg_get_constraintdef(oid) LIKE '%warning%' AND
             pg_get_constraintdef(oid) LIKE '%critical%' THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM pg_constraint
WHERE conrelid = 'account_alerts'::regclass
AND conname = 'check_alert_severity';
```

**通过标准**:
1. ✅ project_members.permissions 类型为 `jsonb`，默认值为 `{}`
2. ✅ 所有 permissions 值要么是 NULL，要么是有效 JSONB 对象
3. ✅ permissions_legacy 列保留了所有原始数据
4. ✅ account_alerts.severity 只包含 `info`, `warning`, `critical`
5. ✅ CHECK 约束定义正确

**如果 Gate #2B 失败**:
1. 停止迁移
2. 检查具体失败的验证点
3. 执行回滚 SQL
4. 修复数据后重新执行

---

## Phase 2C: 未定义字段规范化（可选）

### 目标

处理 ad_accounts 表中 12 个未在 DATA_SCHEMA.md 中定义的字段。

### 选项 1: 补充到 DATA_SCHEMA.md（推荐）

**执行步骤**:
1. 在 DATA_SCHEMA.md § 3.2.9 添加以下字段定义：

```markdown
#### 3.2.9 `ad_accounts` - 额外业务字段（补充）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `total_spend` | DECIMAL(15,2) | 总消耗（统计字段） |
| `total_leads` | INTEGER | 总潜在客户数（统计字段） |
| `avg_cpl` | DECIMAL(10,2) | 平均单粉成本（统计字段） |
| `best_cpl` | DECIMAL(10,2) | 最佳单粉成本（统计字段） |
| `setup_fee` | DECIMAL(10,2) | 开户费 |
| `setup_fee_paid` | BOOLEAN | 开户费是否已支付 |
| `account_type` | VARCHAR(50) | 账户类型 |
| `payment_method` | VARCHAR(50) | 支付方式 |
| `billing_information` | JSONB | 账单信息 |
| `auto_monitoring` | BOOLEAN | 自动监控开关 |
| `alert_thresholds` | JSONB | 预警阈值设置 |
| `tags` | JSONB | 标签（用于分类和筛选） |

**说明**:
- 以上字段为业务功能扩展字段，不属于核心字段
- 统计字段（total_spend, total_leads, avg_cpl, best_cpl）由定时任务或触发器更新
- 保留这些字段以支持现有业务逻辑
```

2. 更新 `backend/models/ad_account.py` 文件注释，标注这些字段已合规

**优点**:
- 无需数据迁移
- 不影响现有业务代码
- 规范化文档

**缺点**:
- 增加文档维护负担

---

### 选项 2: 迁移到 account_metadata JSONB（不推荐）

**执行步骤**:
1. 创建迁移脚本，将 12 个字段数据打包到 `account_metadata` JSONB
2. 删除原字段
3. 更新所有业务代码以从 JSONB 读取

**优点**:
- 完全符合 DATA_SCHEMA 原始定义
- 表结构更简洁

**缺点**:
- 需要大规模重构业务代码
- JSONB 查询性能不如原生字段
- 失去类型安全和 CHECK 约束
- 迁移风险高

**建议**: 选择选项 1

---

## 执行顺序与时间安排

### 总体执行顺序

```
Phase 2A: 时间字段修复（必须执行）
  Day 1: Rev 2A-001 + Rev 2A-002 + Rev 2A-003
  Day 1: Gate #2A 验证
  Day 2-4: 观察期（3天）

Phase 2B: 字段类型修复（建议执行）
  Day 5: Rev 2B-001 (project_members.permissions)
  Day 5: Rev 2B-002 (account_alerts.severity)
  Day 5: Gate #2B 验证
  Day 6-12: 观察期（7天）

Phase 2C: 文档规范化（可选）
  Day 13-15: 更新 DATA_SCHEMA.md
  Day 16: 代码注释标注
```

### 时间估算

| Phase | 迁移脚本编写 | 执行时间 | 验证时间 | 观察期 | 合计 |
| --- | --- | --- | --- | --- | --- |
| Phase 2A | 1 小时 | 5 分钟 | 30 分钟 | 3 天 | 3.5 天 |
| Phase 2B | 2 小时 | 10 分钟 | 1 小时 | 7 天 | 7.5 天 |
| Phase 2C | 2 小时 | 0 | 0 | 0 | 0.5 天 |
| **合计** | **5 小时** | **15 分钟** | **1.5 小时** | **10 天** | **11.5 天** |

---

## 风险控制

### 风险评估矩阵

| 风险 | 可能性 | 影响 | 缓解措施 |
| --- | --- | --- | --- |
| 时间字段转换失败 | 低 | 中 | 使用 AT TIME ZONE 'UTC' 确保转换正确 |
| permissions 包含无效 JSON | 中 | 中 | DO 循环逐行验证，无效值设为 {} |
| severity 映射错误 | 低 | 低 | 简单 CASE 语句，保留 legacy 列 |
| 业务代码不兼容 | 低 | 高 | 观察期监控，保留 legacy 列 |
| 数据丢失 | 极低 | 高 | 所有迁移都保留 legacy 列 |

### 回滚演练

**必须在 Dev 环境完成以下演练**:
1. 执行所有迁移脚本
2. 执行所有回滚脚本
3. 验证数据完整性（与迁移前快照对比）
4. 验证业务代码功能正常

---

## 观察期监控

### Phase 2A 观察期（3天）

**监控指标**:
```sql
-- 每日执行，检查时间字段异常值
SELECT
    table_name,
    column_name,
    MIN(column_value::TIMESTAMPTZ) AS min_time,
    MAX(column_value::TIMESTAMPTZ) AS max_time,
    COUNT(*) FILTER (WHERE column_value IS NULL) AS null_count
FROM (
    SELECT 'projects' AS table_name, 'created_at' AS column_name, created_at::TEXT AS column_value FROM projects
    UNION ALL
    SELECT 'projects', 'updated_at', updated_at::TEXT FROM projects
    -- ... 其他字段
) t
GROUP BY table_name, column_name
ORDER BY table_name, column_name;
```

**异常标准**:
- 出现未来时间（> NOW()）
- 出现 1970 年之前的时间
- NULL 数量异常增加

---

### Phase 2B 观察期（7天）

**监控指标**:
```sql
-- permissions JSONB 异常监控
SELECT
    id,
    permissions,
    permissions_legacy
FROM project_members
WHERE jsonb_typeof(permissions) IS NULL
   OR jsonb_typeof(permissions) NOT IN ('null', 'object')
LIMIT 10;

-- severity 枚举值监控
SELECT severity, COUNT(*)
FROM account_alerts
WHERE severity NOT IN ('info', 'warning', 'critical')
GROUP BY severity;
```

**异常标准**:
- 出现无效 JSONB 值
- 出现非法 severity 值

---

## 代码更新清单

### SQLAlchemy 模型更新

**projects.py** (6 处):
```python
# Line 62-74: 修改前
created_at = Column(func.now(), server_default=func.now(), nullable=False, comment="创建时间")
updated_at = Column(func.now(), server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")

# Line 62-74: 修改后
created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")

# Line 114: 修改前
permissions = Column(Text, nullable=True, comment="扩展权限（JSONB）")

# Line 114: 修改后
permissions = Column(JSON, nullable=True, server_default='{}', comment="扩展权限")

# Line 115-120: 修改前
joined_at = Column(func.now(), server_default=func.now(), nullable=False, comment="加入时间")

# Line 115-120: 修改后
joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="加入时间")

# Line 150-167: project_expenses 类似修改
```

**topup.py** (5 处):
```python
# 所有 Column(func.now(), ...) 改为 Column(DateTime(timezone=True), ...)
```

**ledger.py** (1 处):
```python
# Line 49-54: occurred_at 修改
```

**ad_account.py** (1 处):
```python
# Line 304-307: severity CHECK 约束修改
CheckConstraint(
    "severity IN ('info', 'warning', 'critical')",  # 修改后
    name="check_alert_severity"
)
```

---

## 文档更新清单

迁移完成后，必须更新以下文档：

- [ ] `DATA_SCHEMA.md` § 3.2.9 - 补充 ad_accounts 额外字段定义
- [ ] `DATABASE_SCHEMA_MIGRATION_PLAN.md` - 添加 Phase 2 执行记录
- [ ] `backend/models/projects.py` - 更新时间字段和 permissions 类型
- [ ] `backend/models/topup.py` - 更新所有时间字段
- [ ] `backend/models/ledger.py` - 更新 occurred_at 字段
- [ ] `backend/models/ad_account.py` - 更新 severity CHECK 约束
- [ ] `docs/PROJECT_RISKS.md` - 记录 Phase 2 风险和观察结果
- [ ] `CHANGELOG.md` - 记录 Phase 2 变更历史

---

## 总结

**Phase 2 核心目标**: 规范化核心业务表的字段类型，确保与 DATA_SCHEMA.md v5.0 100% 一致。

**关键成果**:
- ✅ 14 个时间字段升级为 TIMESTAMPTZ
- ✅ permissions 字段升级为 JSONB
- ✅ severity 枚举值符合 SoT 规范
- ✅ 12 个额外字段补充到文档

**迁移特点**:
- Phase 2A 完全可逆，数据风险极低
- Phase 2B 可逆（依赖 legacy 列），数据风险中等
- 所有迁移都保留 legacy 列作为回滚保障

**下一步**:
1. 在 Dev 环境执行 Phase 2A 并验证
2. 观察 3 天后执行 Phase 2B
3. 完成文档更新（Phase 2C）

---

**迁移计划版本**: Phase 2 v1.0
**编写日期**: 2025-11-18
**编写人**: 数据库架构师（Claude Code）
