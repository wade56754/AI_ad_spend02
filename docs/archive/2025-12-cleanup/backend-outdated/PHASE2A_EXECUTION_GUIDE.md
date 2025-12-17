# Phase 2A 执行指南

> **版本**: v1.0
> **创建日期**: 2025-11-18
> **执行环境**: Dev（开发环境）
> **预计执行时间**: 15 分钟（含验证）
> **停机时间**: < 5 分钟

---

## 📋 执行前检查清单

在执行迁移前，请确认以下条件：

- [ ] 1. **备份已完成**: 通过 Supabase Dashboard 创建数据库快照
- [ ] 2. **环境确认**: 当前 DATABASE_URL 指向 Dev 环境，**不是生产库**
- [ ] 3. **表存在性**: 确认 7 个目标表都存在并可访问
  ```sql
  SELECT tablename FROM pg_tables
  WHERE tablename IN (
      'projects', 'project_members', 'project_expenses',
      'topup_requests', 'topup_transactions', 'topup_approval_logs',
      'ledger_entries'
  )
  ORDER BY tablename;
  ```
  应返回 7 行记录

- [ ] 4. **Alembic 配置**: 确认 `alembic.ini` 和 `alembic/env.py` 配置正确
- [ ] 5. **依赖安装**: 确认已安装 `alembic`, `sqlalchemy`, `psycopg2`
- [ ] 6. **权限确认**: 数据库用户有 ALTER TABLE 权限

---

## 🚀 执行步骤

### 方式 1: 使用 Alembic（推荐）

#### Step 1: 检查 Alembic 版本状态

```bash
cd D:/git/1108/AI_ad_spend02/backend
alembic current
```

**预期输出**: 显示当前数据库的 revision ID

#### Step 2: 查看待执行的迁移

```bash
alembic history
```

**预期输出**: 应显示 phase2a_001, phase2a_002, phase2a_003

#### Step 3: 执行迁移（三个脚本一次性执行）

```bash
# 升级到 phase2a_003（会自动执行 001 → 002 → 003）
alembic upgrade phase2a_003
```

**预期输出**:
```
[Phase 2A-001] 正在修复 projects 表...
  [OK] projects 表完成（2 个字段）
[Phase 2A-001] 正在修复 project_members 表...
  [OK] project_members 表完成（1 个字段）
[Phase 2A-001] 正在修复 project_expenses 表...
  [OK] project_expenses 表完成（2 个字段）
[Phase 2A-001] 迁移完成！共修复 3 个表，5 个字段
[Phase 2A-001] 请执行 Gate #2A-001 验证

[Phase 2A-002] 正在修复 topup_requests 表...
  [OK] topup_requests 表完成（2 个字段）
[Phase 2A-002] 正在修复 topup_transactions 表...
  [OK] topup_transactions 表完成（2 个字段）
[Phase 2A-002] 正在修复 topup_approval_logs 表...
  [OK] topup_approval_logs 表完成（1 个字段）
[Phase 2A-002] 迁移完成！共修复 3 个表，5 个字段
[Phase 2A-002] 请执行 Gate #2A-002 验证

[Phase 2A-003] 正在修复 ledger_entries 表...
  [OK] ledger_entries 表完成（1 个字段）
[Phase 2A-003] 迁移完成！共修复 1 个表，1 个字段
[Phase 2A-003] 请执行 Gate #2A-003 验证
```

#### Step 4: 执行 Gate 验证

```bash
# 连接到数据库并执行验证脚本
psql $DATABASE_URL -f phase2a_gate_verification.sql
```

**或者手动连接**:
```bash
psql postgresql://postgres:BTsBIezNsDQF0UFp@db.jzmcoivxhiyidizncyaq.supabase.co:5432/postgres

# 然后执行
\i phase2a_gate_verification.sql
```

**预期输出**:
- Check 1: 所有 14 个字段状态为 '✅ PASS'
- Check 2: 所有 7 个表数据完整性 '✅ PASS'
- Check 3: 所有时间范围合理性 '✅ PASS'
- 最终结论: '✅ Phase 2A Gate 验证通过！'

---

### 方式 2: 直接执行 SQL（不推荐）

如果 Alembic 配置有问题，可以直接执行 SQL：

```bash
psql $DATABASE_URL << 'EOF'

-- Rev 2A-001: projects 模块
ALTER TABLE projects ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE projects ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';
ALTER TABLE project_members ALTER COLUMN joined_at TYPE TIMESTAMPTZ USING joined_at AT TIME ZONE 'UTC';
ALTER TABLE project_expenses ALTER COLUMN occurred_at TYPE TIMESTAMPTZ USING occurred_at AT TIME ZONE 'UTC';
ALTER TABLE project_expenses ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';

-- Rev 2A-002: topup 模块
ALTER TABLE topup_requests ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE topup_requests ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC';
ALTER TABLE topup_transactions ALTER COLUMN paid_at TYPE TIMESTAMPTZ USING paid_at AT TIME ZONE 'UTC';
ALTER TABLE topup_transactions ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';
ALTER TABLE topup_approval_logs ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';

-- Rev 2A-003: ledger 模块
ALTER TABLE ledger_entries ALTER COLUMN occurred_at TYPE TIMESTAMPTZ USING occurred_at AT TIME ZONE 'UTC';

EOF
```

然后执行验证脚本（同 Step 4）。

---

## ✅ Gate 验证通过标准

Gate #2A 必须满足以下所有条件才算通过：

| 检查项 | 验证内容 | 通过标准 |
| --- | --- | --- |
| Check 1 | 字段类型验证 | 所有 14 个字段 data_type = 'timestamp with time zone' |
| Check 2 | 数据完整性验证 | 所有 7 个表的时间字段 count = total_count |
| Check 3 | 时间范围合理性 | 所有时间值在 2020-01-01 至当前时间之间 |
| Check 4 | Timezone 设置 | 数据库 timezone = 'UTC' 或应用层标准时区 |
| Check 5 | 综合统计 | verified_fields 总计 = 14 |

**如果任何检查失败**:
1. ❌ **立即停止**，不要继续后续步骤
2. 📋 记录失败的具体内容
3. 🔄 执行回滚步骤（见下文）
4. 🔍 分析问题原因后重新执行

---

## 🔄 回滚步骤

如果 Gate 验证失败或发现问题，执行回滚：

### 使用 Alembic 回滚

```bash
# 回滚所有 Phase 2A 迁移
alembic downgrade <前一个revision>
```

**注意**: 将 `<前一个revision>` 替换为 phase2a_001 之前的 revision ID

### 手动回滚 SQL

```bash
psql $DATABASE_URL << 'EOF'

-- 回滚 Rev 2A-003
ALTER TABLE ledger_entries ALTER COLUMN occurred_at TYPE TIMESTAMP USING occurred_at;

-- 回滚 Rev 2A-002
ALTER TABLE topup_approval_logs ALTER COLUMN created_at TYPE TIMESTAMP USING created_at;
ALTER TABLE topup_transactions ALTER COLUMN created_at TYPE TIMESTAMP USING created_at;
ALTER TABLE topup_transactions ALTER COLUMN paid_at TYPE TIMESTAMP USING paid_at;
ALTER TABLE topup_requests ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at;
ALTER TABLE topup_requests ALTER COLUMN created_at TYPE TIMESTAMP USING created_at;

-- 回滚 Rev 2A-001
ALTER TABLE project_expenses ALTER COLUMN created_at TYPE TIMESTAMP USING created_at;
ALTER TABLE project_expenses ALTER COLUMN occurred_at TYPE TIMESTAMP USING occurred_at;
ALTER TABLE project_members ALTER COLUMN joined_at TYPE TIMESTAMP USING joined_at;
ALTER TABLE projects ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at;
ALTER TABLE projects ALTER COLUMN created_at TYPE TIMESTAMP USING created_at;

EOF
```

### 验证回滚成功

```sql
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name IN (
    'projects', 'project_members', 'project_expenses',
    'topup_requests', 'topup_transactions', 'topup_approval_logs',
    'ledger_entries'
)
AND column_name IN ('created_at', 'updated_at', 'occurred_at', 'joined_at', 'paid_at')
ORDER BY table_name, column_name;
```

**预期结果**: 所有 data_type 应为 'timestamp without time zone'

---

## 📊 观察期（3天）

Gate 验证通过后，进入 **3 天观察期**（2025-11-18 至 2025-11-21）。

### 每日监控任务

#### 任务 1: 时间字段异常值检查（每日执行）

```sql
-- 检查是否有未来时间或异常早的时间
SELECT
    'projects' AS table_name,
    COUNT(*) FILTER (WHERE created_at > NOW()) AS future_count,
    COUNT(*) FILTER (WHERE created_at < '2020-01-01'::TIMESTAMPTZ) AS too_early_count
FROM projects

UNION ALL

SELECT
    'project_members' AS table_name,
    COUNT(*) FILTER (WHERE joined_at > NOW()) AS future_count,
    COUNT(*) FILTER (WHERE joined_at < '2020-01-01'::TIMESTAMPTZ) AS too_early_count
FROM project_members

-- ... 其他表类似
;
```

**异常标准**:
- future_count > 0（出现未来时间）
- too_early_count > 0（出现过早时间）

#### 任务 2: 应用日志监控

检查应用日志中是否有时区相关错误：
```bash
# 查看最近 1 小时的错误日志
grep -i "timezone\|timestamp" /path/to/app/logs/error.log | tail -100
```

#### 任务 3: 业务功能测试

测试以下功能是否正常：
- [ ] 项目创建和编辑
- [ ] 项目成员添加
- [ ] 项目费用记录
- [ ] 充值申请提交
- [ ] 充值审批流程
- [ ] 账本条目查询

### 观察期结束

**Day 3 (2025-11-21) 结束时**，如果：
- ✅ 无异常时间值
- ✅ 无应用错误
- ✅ 所有业务功能正常

则可以进入 **Phase 2B**（字段类型修复）。

如果发现问题，立即回滚并重新评估迁移策略。

---

## 📝 SQLAlchemy 模型更新

**重要**: 执行 Phase 2A 后，必须更新 SQLAlchemy 模型代码。

### 修改文件清单

#### 1. backend/models/projects.py

**Line 62-74: projects.created_at, updated_at**
```python
# 修改前
created_at = Column(
    func.now(),
    server_default=func.now(),
    nullable=False,
    comment="创建时间"
)
updated_at = Column(
    func.now(),
    server_default=func.now(),
    onupdate=func.now(),
    nullable=False,
    comment="更新时间"
)

# 修改后
from sqlalchemy import DateTime

created_at = Column(
    DateTime(timezone=True),
    server_default=func.now(),
    nullable=False,
    comment="创建时间"
)
updated_at = Column(
    DateTime(timezone=True),
    server_default=func.now(),
    onupdate=func.now(),
    nullable=False,
    comment="更新时间"
)
```

**Line 115-120: project_members.joined_at**
```python
# 修改前
joined_at = Column(
    func.now(),
    server_default=func.now(),
    nullable=False,
    comment="加入时间"
)

# 修改后
joined_at = Column(
    DateTime(timezone=True),
    server_default=func.now(),
    nullable=False,
    comment="加入时间"
)
```

**Line 150-167: project_expenses.occurred_at, created_at**
```python
# 修改前
occurred_at = Column(
    func.now(),
    server_default=func.now(),
    nullable=False,
    comment="发生时间"
)
created_at = Column(
    func.now(),
    server_default=func.now(),
    nullable=False,
    comment="创建时间"
)

# 修改后
occurred_at = Column(
    DateTime(timezone=True),
    server_default=func.now(),
    nullable=False,
    comment="发生时间"
)
created_at = Column(
    DateTime(timezone=True),
    server_default=func.now(),
    nullable=False,
    comment="创建时间"
)
```

#### 2. backend/models/topup.py

**Line 91-103: topup_requests.created_at, updated_at**
```python
# 所有 Column(func.now(), ...) 改为 Column(DateTime(timezone=True), ...)
```

**Line 150-173: topup_transactions.paid_at, created_at**
```python
# 同上
```

**Line 216-221: topup_approval_logs.created_at**
```python
# 同上
```

#### 3. backend/models/ledger.py

**Line 49-54: ledger_entries.occurred_at**
```python
# 修改前
occurred_at = Column(
    func.now(),
    server_default=func.now(),
    nullable=False,
    comment="发生时间"
)

# 修改后
occurred_at = Column(
    DateTime(timezone=True),
    server_default=func.now(),
    nullable=False,
    comment="发生时间"
)
```

### 验证模型更新

```bash
# 运行 Python 检查语法
python -m py_compile backend/models/projects.py
python -m py_compile backend/models/topup.py
python -m py_compile backend/models/ledger.py

# 测试模型导入
python -c "from models.projects import Project, ProjectMember, ProjectExpense; print('✅ projects.py OK')"
python -c "from models.topup import TopupRequest, TopupTransaction, TopupApprovalLog; print('✅ topup.py OK')"
python -c "from models.ledger import LedgerEntry; print('✅ ledger.py OK')"
```

---

## 📄 文档更新清单

Phase 2A 完成后，更新以下文档：

- [ ] `DATABASE_SCHEMA_MIGRATION_PLAN.md` - 添加 Phase 2A 执行记录
- [ ] `backend/models/projects.py` - 更新时间字段类型注释
- [ ] `backend/models/topup.py` - 更新所有时间字段
- [ ] `backend/models/ledger.py` - 更新 occurred_at
- [ ] `docs/PROJECT_RISKS.md` - 记录 Phase 2A 观察期结果
- [ ] `CHANGELOG.md` - 记录 Phase 2A 变更历史

---

## 🆘 故障排查

### 问题 1: Alembic 找不到 revision

**症状**:
```
ERROR: Can't locate revision identified by 'phase2a_001'
```

**解决方案**:
1. 检查迁移脚本是否在 `alembic/versions/` 目录下
2. 检查脚本文件名是否正确
3. 执行 `alembic history` 查看可用 revision

### 问题 2: 数据类型转换失败

**症状**:
```
ERROR: cannot cast type timestamp without time zone to timestamp with time zone
```

**解决方案**:
确保 SQL 使用 `USING ... AT TIME ZONE 'UTC'`，不要直接 ALTER COLUMN TYPE

### 问题 3: Gate 验证部分 FAIL

**症状**: Check 1 显示部分字段类型不正确

**解决方案**:
1. 检查具体哪些字段失败
2. 手动执行该字段的 ALTER 语句
3. 重新运行 Gate 验证

### 问题 4: 观察期发现异常时间值

**症状**: 出现未来时间或 1970 年之前的时间

**解决方案**:
1. 立即停止业务操作
2. 检查数据来源（可能是应用层 bug）
3. 修复数据后重新验证
4. 如果无法修复，执行回滚

---

## 📞 联系支持

如果遇到无法解决的问题：

1. 📋 记录详细错误信息（SQL、日志、截图）
2. 🔄 执行回滚确保系统可用
3. 📧 联系 DBA 团队或系统架构团队

---

**执行指南版本**: v1.0
**编写日期**: 2025-11-18
**编写人**: 数据库架构师（Claude Code）
**下一步**: 执行 Phase 2A → 观察 3 天 → Phase 2B
