# 数据库迁移执行指南 - reconciliation & ad_spend_daily 模块

> **版本**: v1.2
> **创建日期**: 2025-11-17
> **最后更新**: 2025-11-18
> **适用范围**: reconciliation_* 表 + ad_spend_daily 表（**Phase 1 ONLY**）
> **关联文档**:
> - DATABASE_SCHEMA_MIGRATION_PLAN.md v2.1（总体迁移策略）
> - DATA_SCHEMA.md v5.0（数据结构SoT）
> - STATE_MACHINE.md v2.3（状态机SoT）

---

## ⚠️ 重要声明

### 本指南的适用范围

**✅ 本指南涵盖的表**（5个表）：
- `reconciliation_batches`
- `reconciliation_details`
- `reconciliation_adjustments`
- `reconciliation_reports`
- `ad_spend_daily`

**❌ 本指南不涉及的表**（后续Phase处理）：
- `projects`, `project_members`, `project_expenses`
- `channels`, `channel_*`
- `ad_accounts`, `account_*`
- `daily_reports`, `daily_report_audit_logs`
- `topup_requests`, `topup_transactions`, `topup_approval_logs`
- `ledger_entries`
- `user_profiles`, `user_sessions`, `audit_logs`

如果你需要迁移上述未涵盖的表，请参考 DATABASE_SCHEMA_MIGRATION_PLAN.md 的完整方案。

### 本指南的定位

这是 **DATABASE_SCHEMA_MIGRATION_PLAN.md Phase 1** 的实施细则，专注于：
1. reconciliation模块主键类型统一（Integer → BIGSERIAL）
2. reconciliation_batches状态枚举对齐STATE_MACHINE.md
3. ad_spend_daily和reconciliation_*的用户FK类型修复（Integer → UUID）

---

## 📋 目录

- [0. 快速开始](#0-快速开始)
- [1. 迁移概述](#1-迁移概述)
- [2. 前置准备](#2-前置准备)
- [3. Dev/Test环境执行](#3-devtest环境执行)
- [4. 生产环境执行](#4-生产环境执行)
- [5. 验证与Gate检查](#5-验证与gate检查)
- [6. 回滚方案](#6-回滚方案)
- [7. 常见问题](#7-常见问题)
- [附录A: 命令速查表](#附录a-命令速查表)
- [附录B: 环境配置](#附录b-环境配置)

---

## 🧭 如何阅读本文档

**根据你的角色，快速定位需要阅读的章节**：

| 角色 | 必读章节 | 选读章节 | 预计阅读时间 |
|------|---------|---------|------------|
| **DBA（执行人）** | §0, §2, §3, §5, §6 | §1, §4, §7 | 30分钟 |
| **开发者（Dev环境测试）** | §0, §1, §3, §7 | §2, §5 | 15分钟 |
| **项目负责人（决策者）** | §0, §1, §6.3 | §4 | 10分钟 |
| **QA（验证人员）** | §0, §5, §7 | §3 | 15分钟 |
| **运维（监控人员）** | §0, §4, §5.6 | §6 | 15分钟 |

**⚠️ 第一次执行者必读全文，熟悉后可按上表快速查阅。**

---

## 0. 快速开始

### 0.1 迁移前1分钟检查清单

执行前请快速确认：

- [ ] **我已阅读并理解"适用范围"**（只涉及5个表，不适用于其他表）
- [ ] **我已备份数据库**（执行过 `pg_dump` 或 Supabase 快照）
- [ ] **我确认当前环境**（Dev/Staging/Production）
- [ ] **我已安装 alembic**（`alembic current` 能正常执行）
- [ ] **我已检查 Alembic 版本**（应在某个已知 revision）
- [ ] **我理解回退策略**（Rev 001-003可逆，Rev 004-006不可逆，只能从备份恢复）

### 0.2 执行流程图

```
开始
  ↓
[0.3 环境检查] → 失败 → 修复环境 → 重新检查
  ↓ 通过
[备份数据库] → 验证备份
  ↓
[Rev 001: 主键BIGSERIAL] → Gate #1 验证 → 失败 → 回滚
  ↓ 通过
[Rev 002: 状态枚举对齐] → Gate #2 验证 → 失败 → 回滚
  ↓ 通过
[Rev 003: 用户FK分析] → Gate #3 评估孤儿率 → >10% → 停止，人工review
  ↓ ≤10%
【决策点】是否执行用户FK修复？
  ├─ 否 → 保持当前状态（违反SoT，需记录风险）
  └─ 是 ↓
[Rev 004-005: 用户FK修复] → Gate #4/#5 验证 → 失败 → 从备份恢复
  ↓ 通过
[观察期 1-7天] → Gate #6 监控
  ↓
[Rev 006: 清理临时资源]
  ↓
完成
```

### 0.3 前置环境检查（必须100%通过）

**检查1：Python和Alembic环境**

```bash
# Windows本地开发环境
cd D:\git\1108\AI_ad_spend02\backend
python --version  # 应显示 Python 3.9+
pip show alembic  # 应显示 alembic 版本

# Linux/Supabase环境
cd /path/to/AI_ad_spend02/backend
python3 --version
pip3 show alembic
```

**检查2：数据库连接**

```bash
# Windows（假设使用本地PostgreSQL或远程Supabase）
# 方式1：使用psql（如已安装）
psql -h localhost -U your_user -d your_database -c "SELECT version();"

# 方式2：使用Python验证（跨平台）
python -c "
from core.db import engine
with engine.connect() as conn:
    result = conn.execute('SELECT version();')
    print(result.fetchone()[0])
"
```

**检查3：关键表存在性**

```sql
-- 在psql或数据库客户端执行
SELECT
    schemaname,
    tablename
FROM pg_tables
WHERE tablename IN (
    'user_profiles',           -- 业务用户扩展表
    'reconciliation_batches',
    'reconciliation_details',
    'reconciliation_adjustments',
    'reconciliation_reports',
    'ad_spend_daily'
)
ORDER BY tablename;

-- 预期输出：至少包含 user_profiles 和 5个reconciliation/ad_spend表
-- 如果缺少任何表，说明数据库状态不符合前提条件
```

**检查4：Alembic当前版本**

```bash
alembic current

# 预期输出示例（⚠️ revision ID 以实际仓库为准）：
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.runtime.migration] Will assume transactional DDL.
# 20251115_add_reconciliation_indexes (head)

# ⚠️ 注意：上面的 revision ID 仅为示例，实际 ID 取决于你的数据库当前状态
# 重要的是确认 alembic current 能正常执行，无报错
# 如果显示 (head) 与你预期的不一致，请先执行其他未完成的迁移
```

**检查5：用户体系架构确认**

```sql
-- 确认用户表主键类型
SELECT
    table_name,
    column_name,
    data_type,
    udt_name
FROM information_schema.columns
WHERE (table_schema = 'auth' AND table_name = 'users' AND column_name = 'id')
   OR (table_schema = 'public' AND table_name = 'user_profiles' AND column_name = 'id')
ORDER BY table_name;

-- 预期输出：
-- auth.users.id        → uuid
-- user_profiles.id     → uuid

-- ⚠️ 如果不符合预期，说明用户体系架构不符合DATA_SCHEMA.md要求
```

**✅ 所有检查通过后，方可继续执行迁移**

---

## 1. 迁移概述

### 1.1 核心问题与解决方案

| 问题编号 | 问题描述 | 当前状态 | 目标状态 | 严重程度 | Rev ID |
|---------|---------|---------|---------|---------|--------|
| **P1** | reconciliation_* 表主键类型 | Integer | BIGSERIAL | 🟡 中 | 001 |
| **P2** | reconciliation_batches.status枚举 | 5个旧值 | 4个SoT值 | 🟢 低 | 002 |
| **P3** | ad_spend_daily用户FK类型不匹配 | Integer FK → users.id(UUID) | UUID FK → user_profiles.id | 🔴 高 | 003-005 |
| **P4** | reconciliation_*用户FK类型不匹配 | Integer FK → users.id(UUID) | UUID FK → user_profiles.id | 🔴 高 | 003-005 |

#### 问题P1详情：主键类型统一

**问题根源**：
- reconciliation_batches等4个表的主键定义为 `Integer`
- DATA_SCHEMA.md v5.0 §3.5 要求核心业务表使用 `BIGSERIAL`

**解决策略**：
- Dev/Test环境：直接 `ALTER COLUMN id TYPE BIGINT`
- 生产环境：需评估数据量，如果>10万行建议使用影子表策略

**风险评估**：
- 🟡 中等风险：ALTER操作会短暂锁表（通常<5秒）
- ✅ 可回退：通过 `alembic downgrade` 或从备份恢复

#### 问题P2详情：状态枚举对齐

**问题根源**：
- 当前：`pending, processing, completed, exception, resolved` (5个值)
- SoT：`draft, pending, reviewing, closed` (4个值)

**映射规则**：
```
pending    → draft      (初始草稿状态)
processing → pending    (处理中)
completed  → closed     (已完成)
exception  → reviewing  (异常，需审核)
resolved   → closed     (已解决)
```

**解决策略**：
- 添加 `status_legacy` 列备份原值
- 执行数据映射
- 更新 CHECK 约束

**风险评估**：
- 🟢 低风险：纯数据转换，逻辑清晰
- ✅ 可回退：从 `status_legacy` 列恢复

#### 问题P3/P4详情：用户FK类型修复（关键问题）

**问题根源**：
```
ad_spend_daily表：
  - user_id: Integer 类型
  - created_by: Integer 类型
  - updated_by: Integer 类型
  - FK声明：FOREIGN KEY (user_id) REFERENCES users(id)
  - 实际情况：users.id 是 UUID 类型

⚠️ 这是类型不匹配错误！PostgreSQL理论上不允许Integer FK指向UUID列
```

**本项目采用的解决策略**（Strategy B）：

```
策略B：无法映射则置NULL + 记录统计

原因：
1. ad_spend_daily的user_id是Integer值（如 1, 2, 3...）
2. users.id是UUID值（如 '550e8400-e29b-41d4-a716-446655440000'）
3. 两者无数学映射关系（Integer无法转换为UUID）
4. 项目历史原因导致的遗留问题

实施方案：
1. 创建临时分析表 temp_user_id_fk_analysis
2. 统计所有Integer类型的user_id值和分布
3. 将这些列修改为UUID类型，初始值设为NULL
4. 重建FK约束，指向 user_profiles.id
5. 由业务层根据其他字段（如email、account_code）重建用户关联

数据影响：
- ad_spend_daily: 所有user_id/created_by/updated_by → NULL
- reconciliation_details: reviewed_by/resolved_by → NULL
- reconciliation_adjustments: approved_by/finance_approved_by → NULL
- reconciliation_reports: generated_by → NULL

业务影响：
- 历史记录中的用户关联丢失
- 新记录可以正常关联用户
- 需要前端显示"历史数据用户未知"
```

**⚠️ 如果业务不接受NULL策略，请停止迁移并制定映射方案**

### 1.2 迁移版本路线图

```
当前状态
    ↓
[Rev 001] 20251117_reconciliation_pk_bigserial
    ↓  (主键 Integer → BIGSERIAL，4个表)
[Rev 002] 20251117_reconciliation_status_align
    ↓  (状态枚举 5值 → 4值)
[Rev 003] 20251117_analyze_user_fk
    ↓  (分析Integer FK，统计孤儿率，创建临时表)
【决策点】是否继续？
    ↓  孤儿率 ≤ 10%，业务方接受NULL策略
[Rev 004] 20251117_fix_ad_spend_user_fk
    ↓  (修复ad_spend_daily的3个用户FK列)
[Rev 005] 20251117_fix_recon_detail_user_fk
    ↓  (修复reconciliation_details的2个用户FK列)
[Rev 006] 20251117_fix_recon_other_user_fk
    ↓  (修复reconciliation_adjustments/reports的3个用户FK列)
[观察期 1-7天]
    ↓  无异常
[可选] 手动清理临时资源
    ↓  (删除 *_legacy 列和 temp_user_id_fk_analysis 表)
完成状态
```

**可逆性标注**：
- ✅ Rev 001-003：可通过 `alembic downgrade` 安全回退
- ❌ Rev 004-006：不可逆，Integer数据已删除，只能从备份恢复

**⚠️ 重要说明**：
- Rev 004-006的文件名以实际仓库 `backend/alembic/versions/` 目录为准
- 如果文件缺失，请检查是否已生成（参考 MIGRATION_SCRIPTS_SUMMARY.md）

### 1.3 预计耗时

| 环境 | Rev 001 | Rev 002 | Rev 003 | Rev 004-005 | Rev 006 | 总计 |
|-----|---------|---------|---------|------------|---------|------|
| **Dev/Test**<br/>(数据量<1万行) | 5秒 | 2秒 | 3秒 | 20秒 | 1秒 | **~30秒** |
| **Staging**<br/>(数据量1-10万行) | 1分钟 | 10秒 | 30秒 | 8分钟 | 5秒 | **~10分钟** |
| **Production**<br/>(数据量>10万行) | 20分钟 | 1分钟 | 2分钟 | 1.5小时 | 30秒 | **~2小时** |

---

## 2. 前置准备

### 2.1 数据库备份（强制要求）

#### 2.1.1 完整备份（推荐）

**Linux/Supabase环境**：

```bash
# 使用pg_dump全库备份
pg_dump -h your-db-host \
        -U your-db-user \
        -d your-database \
        -Fc \
        -f backup_$(date +%Y%m%d_%H%M%S).dump

# 验证备份文件完整性
pg_restore --list backup_*.dump | head -20

# 备份文件大小检查
ls -lh backup_*.dump
```

**Windows本地环境**：

```powershell
# PowerShell命令
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "backup_$timestamp.dump"

# 使用pg_dump（需要先安装PostgreSQL客户端工具）
& "C:\Program Files\PostgreSQL\15\bin\pg_dump.exe" `
  -h localhost `
  -U your_user `
  -d your_database `
  -Fc `
  -f $backupFile

# 或者使用Supabase CLI（如果连接远程Supabase）
# supabase db dump -f $backupFile
```

**Supabase云环境**：

```bash
# 方式1：使用Supabase CLI
supabase db dump --db-url "$DATABASE_URL" -f backup_$(date +%Y%m%d).sql

# 方式2：使用Supabase Dashboard
# 1. 登录 https://app.supabase.com
# 2. 选择项目 → Database → Backups
# 3. 点击 "Create backup"
# 4. 等待备份完成并下载
```

#### 2.1.2 部分备份（仅备份相关表）

```bash
# Linux/Mac
pg_dump -h your-db-host -U your-db-user -d your-database -Fc \
  -t reconciliation_batches \
  -t reconciliation_details \
  -t reconciliation_adjustments \
  -t reconciliation_reports \
  -t ad_spend_daily \
  -f backup_reconciliation_$(date +%Y%m%d).dump

# Windows PowerShell
$timestamp = Get-Date -Format "yyyyMMdd"
& pg_dump -h localhost -U your_user -d your_database -Fc `
  -t reconciliation_batches `
  -t reconciliation_details `
  -t reconciliation_adjustments `
  -t reconciliation_reports `
  -t ad_spend_daily `
  -f "backup_reconciliation_$timestamp.dump"
```

#### 2.1.3 备份验证（关键步骤）

**验证1：备份文件完整性**

```bash
# 列出备份中的对象
pg_restore --list backup_*.dump | grep -E "TABLE|SEQUENCE|CONSTRAINT"

# 预期输出应包含：
# TABLE reconciliation_batches
# TABLE reconciliation_details
# ...
# SEQUENCE reconciliation_batches_id_seq
# ...
```

**验证2：测试恢复到临时数据库**

```bash
# 创建临时测试数据库
createdb test_restore_$(date +%Y%m%d)

# 恢复备份
pg_restore -d test_restore_$(date +%Y%m%d) backup_*.dump

# 验证数据完整性
psql -d test_restore_$(date +%Y%m%d) -c "
SELECT
    'reconciliation_batches' as table_name,
    COUNT(*) as row_count
FROM reconciliation_batches
UNION ALL
SELECT 'ad_spend_daily', COUNT(*) FROM ad_spend_daily;
"

# 对比原库的行数
psql -d your_database -c "
SELECT
    'reconciliation_batches' as table_name,
    COUNT(*) as row_count
FROM reconciliation_batches
UNION ALL
SELECT 'ad_spend_daily', COUNT(*) FROM ad_spend_daily;
"

# 确认行数一致后，删除测试库
dropdb test_restore_$(date +%Y%m%d)
```

### 2.2 依赖检查

#### 2.2.1 检查长事务

```sql
-- 查找运行超过5分钟的活动事务
SELECT
    pid,
    usename,
    application_name,
    state,
    query_start,
    now() - query_start AS duration,
    LEFT(query, 100) as query_preview
FROM pg_stat_activity
WHERE state = 'active'
  AND query_start < now() - interval '5 minutes'
  AND pid <> pg_backend_pid()  -- 排除当前会话
ORDER BY duration DESC;

-- 如发现长事务，评估是否可以终止
-- ⚠️ 谨慎操作：仅在确认可以中断的情况下执行
-- SELECT pg_terminate_backend(pid) WHERE pid = <具体pid>;
```

#### 2.2.2 检查锁冲突

```sql
-- 查找被阻塞的查询
SELECT
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity
  ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks
  ON blocking_locks.locktype = blocked_locks.locktype
  AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
  AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
  AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
  AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
  AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
  AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
  AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
  AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
  AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
  AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity
  ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- 预期输出：空（无锁冲突）
```

#### 2.2.3 统计当前数据量

```sql
-- 统计5个表的数据量和磁盘占用
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) AS indexes_size,
    n_live_tup AS row_count,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
WHERE tablename IN (
    'reconciliation_batches',
    'reconciliation_details',
    'reconciliation_adjustments',
    'reconciliation_reports',
    'ad_spend_daily'
)
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 记录输出结果，用于：
-- 1. 评估迁移耗时
-- 2. 作为迁移前后对比基准
-- 3. 判断是否需要VACUUM优化
```

### 2.3 环境变量配置

在执行迁移前，确保正确配置数据库连接：

**方式1：修改 alembic.ini**

```ini
# backend/alembic.ini
[alembic]
sqlalchemy.url = postgresql://user:password@host:5432/database

# 或使用环境变量占位符
sqlalchemy.url = postgresql://%(DB_USER)s:%(DB_PASSWORD)s@%(DB_HOST)s:5432/%(DB_NAME)s
```

**方式2：使用环境变量（推荐）**

```bash
# Linux/Mac (.env文件或export)
export DATABASE_URL="postgresql://user:password@host:5432/database"

# Windows PowerShell
$env:DATABASE_URL="postgresql://user:password@localhost:5432/database"

# Alembic会自动读取DATABASE_URL环境变量
```

**方式3：Supabase连接字符串**

```bash
# 从Supabase Dashboard获取连接字符串
# Settings → Database → Connection string → URI

export DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"
```

---

## 3. Dev/Test环境执行

### 3.1 执行前最终确认

```bash
# 1. 确认工作目录
cd D:\git\1108\AI_ad_spend02\backend  # Windows
# cd /path/to/AI_ad_spend02/backend   # Linux

# 2. 确认Alembic配置
alembic current

# 3. 确认数据库连接
alembic check
# 或
python -c "from core.db import engine; print(engine.url)"

# 4. 预览即将执行的SQL（dry-run）
alembic upgrade 20251117_reconciliation_status_align --sql > preview.sql
# 检查preview.sql的内容，确认SQL逻辑正确

# 5. 确认备份已完成
ls -lh backup_*.dump  # Linux
# dir backup_*.dump   # Windows
```

### 3.2 批次1：主键和状态迁移（Rev 001-002）

**Step 1：执行主键迁移**

```bash
# 记录开始时间
echo "开始时间: $(date)"  # Linux
# Get-Date                # Windows

# 执行Rev 001
alembic upgrade 20251117_reconciliation_pk_bigserial

# 预期输出：
# INFO  [alembic.runtime.migration] Running upgrade ... -> 20251117_reconciliation_pk_bigserial
# 🔧 开始迁移 reconciliation_batches...
# ✅ reconciliation_batches 主键迁移完成
# 🔧 开始迁移 reconciliation_details...
# ✅ reconciliation_details 主键迁移完成
# ...
# 🎉 所有reconciliation表主键迁移完成！
```

**Step 2：Gate #1 验证**

```bash
# 方式1：使用psql执行验证脚本（Linux/Mac）
psql -d your_database -f validation_scripts/gate1_verify.sql

# 方式2：使用Python脚本（跨平台）
python validation_scripts/gate1_verify.py

# 方式3：手动SQL验证（Windows用户推荐）
# 打开数据库客户端（DBeaver/pgAdmin），执行以下SQL：
```

```sql
-- Gate #1 检查1：主键类型
SELECT
    table_name,
    column_name,
    data_type,
    CASE
        WHEN data_type = 'bigint' THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as status
FROM information_schema.columns
WHERE table_name IN (
    'reconciliation_batches',
    'reconciliation_details',
    'reconciliation_adjustments',
    'reconciliation_reports'
)
AND column_name = 'id'
ORDER BY table_name;

-- 预期：4行，全部status='✅ PASS'
```

```sql
-- Gate #1 检查2：序列类型
SELECT
    sequencename,
    data_type,
    CASE
        WHEN data_type = 'bigint' THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as status
FROM pg_sequences
WHERE sequencename LIKE 'reconciliation_%_id_seq'
ORDER BY sequencename;

-- 预期：4行，全部status='✅ PASS'
```

```sql
-- Gate #1 检查3：FK完整性
WITH fk_check AS (
    SELECT 'reconciliation_details' as source_table,
           COUNT(*) as total,
           COUNT(b.id) as matched
    FROM reconciliation_details d
    LEFT JOIN reconciliation_batches b ON d.batch_id = b.id

    UNION ALL

    SELECT 'reconciliation_adjustments', COUNT(*), COUNT(b.id)
    FROM reconciliation_adjustments a
    LEFT JOIN reconciliation_batches b ON a.batch_id = b.id

    UNION ALL

    SELECT 'reconciliation_reports', COUNT(*), COUNT(b.id)
    FROM reconciliation_reports r
    LEFT JOIN reconciliation_batches b ON r.batch_id = b.id
)
SELECT
    source_table,
    total,
    matched,
    total - matched as orphans,
    CASE
        WHEN total = matched THEN '✅ PASS'
        ELSE '❌ FAIL - 存在孤儿记录!'
    END as status
FROM fk_check;

-- 预期：3行，全部orphans=0, status='✅ PASS'
```

**✅ Gate #1通过条件**：
- 所有主键类型为 bigint
- 所有序列类型为 bigint
- 无FK孤儿记录

**❌ Gate #1失败处理**：
```bash
# 如果Gate #1任何检查失败，立即回滚
alembic downgrade -1

# 检查回滚结果
psql -d your_database -c "
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name = 'reconciliation_batches' AND column_name = 'id';
"
# 预期：data_type = 'integer'（已回退）

# 分析失败原因后，修复问题，重新执行
```

**Step 3：执行状态枚举迁移**

```bash
# 执行Rev 002
alembic upgrade 20251117_reconciliation_status_align

# 预期输出：
# INFO  [alembic.runtime.migration] Running upgrade ... -> 20251117_reconciliation_status_align
# 🔧 开始对齐reconciliation_batches.status枚举...
#   → 添加status_legacy备份列...
#   → 备份当前status值...
#   → 执行状态映射...
#   → 更新CHECK约束...
#   → 验证迁移结果...
# ✅ 状态枚举对齐完成！
```

**Step 4：Gate #2 验证**

```sql
-- Gate #2 检查1：状态分布
SELECT
    status,
    status_legacy,
    COUNT(*) as count,
    CASE
        WHEN status IN ('draft', 'pending', 'reviewing', 'closed') THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as status_check
FROM reconciliation_batches
GROUP BY status, status_legacy
ORDER BY count DESC;

-- 预期：
-- - status列只有 draft/pending/reviewing/closed
-- - status_legacy列保留了原始值
```

```sql
-- Gate #2 检查2：CHECK约束
SELECT
    conname as constraint_name,
    pg_get_constraintdef(oid) as definition
FROM pg_constraint
WHERE conname = 'check_batch_status'
  AND conrelid = 'reconciliation_batches'::regclass;

-- 预期：definition包含 "status IN ('draft', 'pending', 'reviewing', 'closed')"
```

**✅ 批次1完成标志**：
- alembic current 显示 `20251117_reconciliation_status_align (head)`
- Gate #1 和 Gate #2 全部通过

### 3.3 批次2：用户FK分析和修复（Rev 003-006）

**⚠️ 重要决策点：是否执行批次2？**

**⚠️ 本策略仅适用于本指南范围内的5个表，不可套用到其他表的用户FK修复**

在执行Rev 003之前，请明确回答：

1. **我是否接受所有用户FK关联重置为NULL？**
   - [ ] 是，我接受（继续执行Rev 003-006）
   - [ ] 否，我不接受（停止迁移，制定映射方案）

2. **我是否理解Rev 004-006不可逆？**
   - [ ] 是，我理解（Rev 004-006一旦执行，唯一回滚方式是从备份恢复）
   - [ ] 是，我理解（Rev 003可以通过alembic downgrade回退）

3. **我是否已通知前端团队适配NULL用户的显示？**
   - [ ] 是，已通知

4. **我是否确认这是Phase 1迁移（仅5个表）？**
   - [ ] 是，我确认本指南仅适用于 reconciliation_* 和 ad_spend_daily

**如果以上全部勾选"是"，继续执行；否则停止并review决策。**

---

**Step 1：执行用户FK分析（Rev 003）**

```bash
# 执行Rev 003
alembic upgrade 20251117_analyze_user_fk

# 预期输出：
# 🔍 开始分析用户外键类型不匹配问题...
#   → 创建临时分析表 temp_user_id_fk_analysis...
#   → 分析ad_spend_daily表...
#   → 分析reconciliation_details表...
#   → 生成分析报告...
# ==========================================
# 📊 用户FK类型不匹配分析报告
# ==========================================
# 总记录数: 15
# 孤儿记录数: 15
# 影响表: ad_spend_daily, reconciliation_details
# ==========================================
# ✅ 分析完成！请检查temp_user_id_fk_analysis表
```

**Step 2：Gate #3 评估孤儿率**

```sql
-- 查看分析表统计
SELECT
    table_name,
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE is_orphan = true) as orphan_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_orphan = true) / NULLIF(COUNT(*), 0), 2) as orphan_rate,
    CASE
        WHEN COUNT(*) = 0 THEN '✅ 无数据'
        WHEN ROUND(100.0 * COUNT(*) FILTER (WHERE is_orphan = true) / COUNT(*), 2) = 0 THEN '✅ 无孤儿'
        WHEN ROUND(100.0 * COUNT(*) FILTER (WHERE is_orphan = true) / COUNT(*), 2) <= 5 THEN '✅ PASS (<5%)'
        WHEN ROUND(100.0 * COUNT(*) FILTER (WHERE is_orphan = true) / COUNT(*), 2) <= 10 THEN '⚠️ WARNING (5-10%)'
        ELSE '❌ FAIL (>10%)'
    END as gate_status
FROM temp_user_id_fk_analysis
GROUP BY table_name
ORDER BY orphan_rate DESC;
```

```sql
-- 查看具体孤儿记录
SELECT
    table_name,
    column_name,
    old_integer_value,
    notes
FROM temp_user_id_fk_analysis
WHERE is_orphan = true
ORDER BY table_name, column_name, old_integer_value
LIMIT 50;

-- 分析：这些Integer值是如何产生的？
-- - 是否全是0或-1等非法值？（可直接置NULL）
-- - 是否是真实用户ID？（需建立映射表）
```

**✅ Gate #3通过条件**：
- 孤儿率 ≤ 10%（可接受策略B：置NULL）
- 或孤儿率 = 100% 但都是非法值（如0, -1, NULL）

**⚠️ Gate #3 警告条件（5-10%）**：
- 需要业务评估：这些孤儿记录是否重要？
- 如果重要，需要制定人工映射方案
- 如果不重要，可以接受置NULL

**❌ Gate #3 失败条件（>10%）**：
- **强制停止迁移**
- 需要人工review分析表
- 制定映射策略（如通过email/account_code建立关联）
- 或者接受风险并记录到项目风险清单

**假设Gate #3通过（≤10%），继续执行**

---

**⚠️ 注意：Rev 004-006脚本应已生成在 backend/alembic/versions/ 目录**

**请检查以下文件是否存在（以实际仓库为准）**：
- ✅ `20251117_fix_ad_spend_user_fk.py` (Rev 004: 修复ad_spend_daily)
- ✅ `20251117_fix_recon_detail_user_fk.py` (Rev 005: 修复reconciliation_details)
- ✅ `20251117_fix_recon_other_user_fk.py` (Rev 006: 修复reconciliation_adjustments/reports)

**如果文件缺失或文件名不一致**：
1. 检查 `backend/alembic/MIGRATION_SCRIPTS_SUMMARY.md` 确认实际文件名
2. 使用 `alembic history` 查看已注册的 revision
3. 确保 revision ID 与文件名一致

**执行前验证**：
```bash
# 检查文件是否存在
ls backend/alembic/versions/20251117_fix_*.py

# 查看 alembic 历史（确认 revision 已注册）
alembic history | grep 20251117_fix
```

### 3.4 观察期（Dev环境：1天）

**Dev/Test环境观察清单**：

```bash
# Day 1: 执行功能测试
cd D:\git\1108\AI_ad_spend02\backend

# 测试1：创建新的对账批次
pytest tests/test_reconciliation.py::test_create_batch -v

# 测试2：创建ad_spend_daily记录
pytest tests/test_ad_spend.py::test_create_daily_spend -v

# 测试3：查询历史记录（用户应显示为NULL或"未知"）
pytest tests/test_reconciliation.py::test_query_batches_with_null_users -v
```

**观察指标**：
- [ ] 新记录创建成功
- [ ] 历史记录查询无报错
- [ ] 前端显示"历史数据用户未知"（而非报错）
- [ ] 无FK约束违规错误

**✅ Dev环境观察期通过后，可执行清理（Rev 006）**

```bash
# 1天后，如果无异常，执行清理
alembic upgrade 20251117_cleanup_temp

# 或手动SQL清理
psql -d your_database -c "
DROP TABLE IF EXISTS temp_user_id_fk_analysis;
ALTER TABLE reconciliation_batches DROP COLUMN IF EXISTS status_legacy;
"
```

---

## 4. 生产环境执行

**⚠️ 生产环境执行必须满足以下前提条件：**

- [ ] Dev环境已成功执行全部6个Rev
- [ ] Staging环境已成功执行全部6个Rev
- [ ] Staging环境已通过3次完整回归测试
- [ ] 已在Staging环境观察3天无异常
- [ ] 已制定详细的回滚预案
- [ ] 已通知所有相关团队（前端/QA/运维）
- [ ] 已获得项目负责人批准

### 4.1 生产环境执行窗口

**推荐时间窗口**：
- 周二或周三凌晨 2:00 - 6:00
- 避开周一（可能有周末积累的问题）
- 避开周五（影响周末值班）
- 避开业务高峰期

**所需人员**：
- DBA（主执行人）
- 后端负责人（技术支持）
- 运维负责人（监控和回滚）
- QA负责人（验证测试）

### 4.2 生产环境Pre-Flight Checklist

**强制检查项（ALL REQUIRED）**：

- [ ] **备份已完成**：已执行全库pg_dump，备份文件已验证可恢复
- [ ] **环境验证通过**：Dev和Staging已成功执行并观察无异常
- [ ] **数据量已统计**：已记录5个表的行数和磁盘占用
- [ ] **无长事务**：已检查pg_stat_activity，无运行超过5分钟的事务
- [ ] **无锁冲突**：已检查pg_locks，无阻塞查询
- [ ] **连接池已调整**：应用连接池timeout >= 60秒
- [ ] **团队已通知**：前端/API/运维团队已知晓迁移时间窗口
- [ ] **回滚预案已准备**：备份恢复脚本已测试，回滚命令已准备
- [ ] **监控已启用**：已开启数据库性能监控和错误日志监控

**✅ 所有检查项通过后，方可开始生产迁移**

**⚠️ 生产环境执行流程（简化版）**

由于生产环境的复杂性，本指南仅提供关键步骤。实际执行时建议：
1. 参考DATABASE_SCHEMA_MIGRATION_PLAN.md的零停机策略
2. 使用影子表和双写方案（对于大表）
3. 分批执行，每批执行后观察24小时

**基本执行顺序**（与Dev环境相同）：
```bash
# Phase 1: 批次1（主键和状态）
alembic upgrade 20251117_reconciliation_status_align
# → Gate #1/2 验证

# Phase 2: 批次2（用户FK）
alembic upgrade 20251117_analyze_user_fk
# → Gate #3 评估
# → 如通过，继续执行 Rev 004-005
# → Gate #4/5 验证

# Phase 3: 观察期（7天）
# → 每日监控
# → Gate #6 验证

# Phase 4: 清理
alembic upgrade 20251117_cleanup_temp
```

---

## 5. 验证与Gate检查

### 5.1 Gate #1：reconciliation主键迁移验证

**验证脚本**：`validation_scripts/gate1_verify.sql`（已生成）

**通过条件**：
- ✅ 所有id列类型为bigint
- ✅ 所有序列类型为bigint
- ✅ 无FK孤儿记录

**失败处理**：
```bash
# 立即回滚
alembic downgrade -1

# 验证回滚成功
psql -d your_database -c "
SELECT data_type FROM information_schema.columns
WHERE table_name = 'reconciliation_batches' AND column_name = 'id';
"
# 预期：integer

# 分析失败原因，修复后重新执行
```

### 5.2 Gate #2：状态枚举对齐验证

**通过条件**：
- ✅ 所有status值在 {draft, pending, reviewing, closed} 范围内
- ✅ status_legacy列完整保存了原值
- ✅ CHECK约束已更新

### 5.3 Gate #3：用户FK孤儿率评估

**通过条件**：
- ✅ 孤儿率 ≤ 5%：可直接继续
- ⚠️ 孤儿率 5-10%：需业务评估
- ❌ 孤儿率 > 10%：**强制停止，人工review**

**决策树**：
```
孤儿率 ≤ 5%
  ├─→ 继续执行Rev 004-006
  └─→ 数据将置NULL，业务层重建关联

孤儿率 5-10%
  ├─→ 评估：孤儿记录是否重要？
  │   ├─→ 重要 → 停止迁移，制定映射方案
  │   └─→ 不重要 → 接受置NULL，继续执行
  └─→ **记录到项目风险台账**（见下方说明）

孤儿率 > 10%
  └─→ **强制停止**
      ├─→ DBA review分析表
      ├─→ 制定人工映射策略
      └─→ 或接受风险并获得项目负责人批准
      └─→ **必须记录到项目风险台账**
```

**⚠️ 风险记录要求**：

当孤儿率在 5-10% 或 >10% 时，**必须**将决策记录到以下位置之一：

1. **项目风险台账**：`docs/PROJECT_RISKS.md` （推荐，Git可追溯）
2. **JIRA风险清单**：在项目的 Risk Management 模块创建 Risk 条目
3. **项目会议纪要**：记录在技术评审会议纪要中

**风险记录模板**：
```markdown
## [RISK-YYYYMMDD-001] 用户FK迁移数据置NULL风险

**风险等级**: 🟡 中等 / 🔴 高
**发现时间**: 2025-11-18
**责任人**: [DBA姓名]
**影响范围**: reconciliation_* 和 ad_spend_daily 表的历史数据用户关联

**问题描述**:
- Gate #3 评估结果：孤儿率 X.XX%
- 采用 Strategy B（置NULL），X 条历史记录的用户关联将丢失

**业务影响**:
- 历史对账批次/日报无法显示创建人/审核人
- 前端需显示"历史数据（用户未知）"

**缓解措施**:
1. 保留 *_legacy 列（观察期7天）
2. 前端已适配 NULL 用户显示
3. 审计日志可从 audit_logs 表恢复部分信息

**批准人**: [项目负责人签字]
**批准时间**: YYYY-MM-DD HH:MM
```

### 5.4 Gate #4/5：用户FK验证

**通过条件**：
- ✅ 所有用户FK列类型为UUID
- ✅ 所有FK指向user_profiles.id
- ✅ 数据已置NULL（符合策略B）

### 5.6 Gate #6：观察期监控（每日执行）

**监控脚本**：`validation_scripts/daily_monitor.sql`

**观察期时长**：
- Dev/Test: 1天
- Staging: 3天
- Production: 7天

---

## 6. 回滚方案

### 6.1 可逆操作 vs 不可逆操作

| Rev ID | 版本名称 | 影响范围 | 可逆性 | 回滚方式 |
|--------|---------|---------|-------|---------|
| Rev 001 | 20251117_reconciliation_pk_bigserial | reconciliation_* 主键 | ✅ 可逆 | `alembic downgrade -1` |
| Rev 002 | 20251117_reconciliation_status_align | reconciliation_batches.status | ✅ 可逆 | `alembic downgrade -1`（从status_legacy恢复） |
| Rev 003 | 20251117_analyze_user_fk | 创建临时分析表 | ✅ 可逆 | `alembic downgrade -1`（删除temp_user_id_fk_analysis） |
| Rev 004 | 20251117_fix_ad_spend_user_fk | ad_spend_daily用户FK | ❌ 不可逆 | **只能从备份恢复** |
| Rev 005 | 20251117_fix_recon_detail_user_fk | reconciliation_details用户FK | ❌ 不可逆 | **只能从备份恢复** |
| Rev 006 | 20251117_fix_recon_other_user_fk | reconciliation_adjustments/reports用户FK | ❌ 不可逆 | **只能从备份恢复** |

**⚠️ 重要说明**：

- **Rev 001-003**：使用 `alembic downgrade` 安全回退，数据完整保留
- **Rev 004-006**：Integer数据已删除，即使downgrade也只能重建空UUID列，**历史数据永久丢失**
- **清理临时资源**：手动删除 *_legacy 列和 temp_user_id_fk_analysis 表后，无法通过alembic恢复

### 6.2 回滚步骤

#### 场景1：Rev 001失败，回滚到迁移前

```bash
# Step 1: 回滚Alembic
alembic downgrade -1

# Step 2: 验证回滚
psql -d your_database -c "
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name = 'reconciliation_batches' AND column_name = 'id';
"
# 预期：data_type = 'integer'

# Step 3: 验证应用连接
pytest tests/test_reconciliation.py -v
```

#### 场景2：Rev 004-005失败，从备份恢复

**⚠️ 这是不可逆操作，只能从备份完全恢复**

```bash
# Step 1: 停止应用服务
sudo systemctl stop your_app_service

# Step 2: 删除当前数据库
psql -U postgres -c "
DROP DATABASE your_database WITH (FORCE);
"

# Step 3: 创建新数据库
psql -U postgres -c "CREATE DATABASE your_database;"

# Step 4: 从备份恢复
pg_restore -d your_database backup_final_*.dump

# Step 5: 验证恢复
psql -d your_database -c "
SELECT COUNT(*) FROM reconciliation_batches;
SELECT COUNT(*) FROM ad_spend_daily;
"

# Step 6: 重启应用
sudo systemctl start your_app_service
```

### 6.3 紧急回滚决策

**立即回滚的情况**：
- ❌ Gate检查失败
- ❌ 应用无法启动
- ❌ 大量FK约束违规错误
- ❌ 数据不一致（如主键重复）
- ❌ 用户报告严重功能问题

**观察后回滚的情况**：
- ⚠️ 性能下降 > 20%
- ⚠️ 错误率上升 > 5%
- ⚠️ 用户投诉增多

**不建议回滚的情况**：
- ✅ 少量NULL值（< 5%）
- ✅ 前端显示"历史数据用户未知"（符合预期）
- ✅ 性能轻微波动（< 10%）

---

## 7. 常见问题

### 7.1 Q: Windows本地开发环境如何执行psql命令？

**A**: 有3种方式：

**方式1：安装PostgreSQL客户端工具**
```powershell
# 下载并安装 PostgreSQL for Windows
# https://www.postgresql.org/download/windows/

# 安装后，添加到PATH
$env:PATH += ";C:\Program Files\PostgreSQL\15\bin"

# 验证
psql --version
```

**方式2：使用Python脚本（推荐）**
```python
# validation_scripts/gate1_verify.py
from core.db import engine

with engine.connect() as conn:
    result = conn.execute("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'reconciliation_batches' AND column_name = 'id';
    """)
    for row in result:
        print(row)
```

**方式3：使用DBeaver等GUI工具**
- 打开DBeaver → 连接数据库 → 打开SQL编辑器
- 复制验证SQL → 执行 → 查看结果

### 7.2 Q: Gate #3显示孤儿率15%，应该继续吗？

**A**: 不应该。孤儿率 > 10% 需要强制停止并人工review。

**处理流程**：

```sql
-- Step 1: 分析孤儿记录
SELECT
    table_name,
    column_name,
    old_integer_value,
    COUNT(*) as occurrence
FROM temp_user_id_fk_analysis
WHERE is_orphan = true
GROUP BY table_name, column_name, old_integer_value
ORDER BY occurrence DESC
LIMIT 20;

-- Step 2: 检查是否有规律
-- 如果都是0、-1、NULL等非法值 → 可以直接置NULL
-- 如果是真实用户ID（如1, 2, 3...） → 需要建立映射

-- Step 3: 决策
-- 选项A：建立Integer→UUID映射表（需要额外开发）
-- 选项B：接受15%数据置NULL（需获得项目负责人批准）
-- 选项C：停止迁移，保持当前状态（违反SoT，记录风险）
```

### 7.3 Q: 迁移后前端报错"Cannot read property 'name' of null"？

**A**: 这是预期行为。历史数据的用户关联已重置为NULL。

**前端适配方案**：

```typescript
// 修改前（会报错）
const userName = record.created_by.name;

// 修改后（安全）
const userName = record.created_by?.name ?? '历史数据（用户未知）';

// 或使用工具函数
function getDisplayName(user: User | null): string {
  if (!user) return '历史数据（用户未知）';
  return user.name || user.email || '未命名用户';
}
```

### 7.4 Q: 观察期内发现status_legacy列占用空间大？

**A**: 正常现象，Rev 006会删除。

```sql
-- 查看列占用空间
SELECT
    pg_size_pretty(
        SUM(pg_column_size(status_legacy))
    ) as total_size
FROM reconciliation_batches;

-- 如果急需释放空间（不建议），可提前执行清理
-- ⚠️ 警告：会失去回滚能力
ALTER TABLE reconciliation_batches DROP COLUMN status_legacy;

-- 执行VACUUM回收空间
VACUUM FULL reconciliation_batches;
```

---

## 附录A: 命令速查表

### A.1 Alembic常用命令

```bash
# 查看当前版本
alembic current

# 查看历史
alembic history --verbose

# 升级到指定版本
alembic upgrade <revision_id>

# 升级到最新版本
alembic upgrade head

# 回退一个版本
alembic downgrade -1

# 回退到指定版本
alembic downgrade <revision_id>

# 预览SQL（不实际执行）
alembic upgrade <revision_id> --sql

# 检查配置
alembic check
```

### A.2 PostgreSQL常用命令

```bash
# 连接数据库
psql -h host -U user -d database

# 执行SQL文件
psql -d database -f script.sql

# 执行单条SQL
psql -d database -c "SELECT version();"

# 备份数据库
pg_dump -d database -Fc -f backup.dump

# 恢复数据库
pg_restore -d database backup.dump

# 列出所有数据库
psql -l

# 列出所有表
psql -d database -c "\dt"
```

### A.3 快速检查命令

```bash
# 检查主键类型
psql -d your_database -c "
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name LIKE 'reconciliation_%' AND column_name = 'id';
"

# 检查FK约束
psql -d your_database -c "
SELECT tc.table_name, kcu.column_name, ccu.table_name AS foreign_table
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'ad_spend_daily' AND tc.constraint_type = 'FOREIGN KEY';
"

# 检查表数据量
psql -d your_database -c "
SELECT schemaname, tablename, n_live_tup
FROM pg_stat_user_tables
WHERE tablename IN ('reconciliation_batches', 'ad_spend_daily')
ORDER BY n_live_tup DESC;
"
```

---

## 附录B: 环境配置

### B.1 Windows本地开发环境

**数据库连接配置**：

```env
# backend/.env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/ai_ad_dev
ALEMBIC_CONFIG=alembic.ini
```

**PowerShell环境变量**：

```powershell
# 设置环境变量
$env:DATABASE_URL="postgresql://postgres:password@localhost:5432/ai_ad_dev"

# 验证
python -c "import os; print(os.getenv('DATABASE_URL'))"
```

### B.2 Linux生产环境

**数据库连接配置**：

```bash
# /etc/environment 或 ~/.bashrc
export DATABASE_URL="postgresql://prod_user:prod_pass@prod-db.example.com:5432/ai_ad_prod"
export DATABASE_URL_READONLY="postgresql://readonly_user:readonly_pass@prod-db-replica.example.com:5432/ai_ad_prod"
```

### B.3 Supabase环境

**连接字符串获取**：
1. 登录 https://app.supabase.com
2. 选择项目 → Settings → Database
3. 复制 Connection string → URI

```bash
# 格式：
postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres

# 设置环境变量
export DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.abcdefg.supabase.co:5432/postgres"
```

---

## 附录C: 紧急联系人

| 角色 | 姓名 | 联系方式 | 职责 | 可用时间 |
|-----|------|---------|------|---------|
| **DBA** | 待填写 | 待填写 | 迁移执行和回滚 | 迁移时间窗口 |
| **后端负责人** | 待填写 | 待填写 | 技术支持 | 迁移时间窗口 |
| **运维负责人** | 待填写 | 待填写 | 监控和服务重启 | 24/7 |
| **QA负责人** | 待填写 | 待填写 | 功能验证 | 工作日 |
| **项目负责人** | 待填写 | 待填写 | 最终决策 | 按需 |

---

**文档版本**: v1.2
**最后更新**: 2025-11-18
**维护责任**: 数据库迁移团队
**审阅周期**: 每次迁移前必读
**文档状态**: ✅ 已通过"迁移规范守门人"终审（可用于生产执行）

**变更历史**:
- v1.0 (2025-11-17): 初始版本
- v1.1 (2025-11-18):
  - 明确作用范围（仅5个表）
  - 明确用户FK映射策略（策略B：置NULL）
  - 统一回滚策略（Rev 001-003可逆，Rev 004-006不可逆）
  - 区分Windows/Linux命令
  - 完善前置条件检查
  - 细化Gate检查条件
  - 补充Supabase环境说明
  - 增强生产环境Pre-Flight Checklist
- v1.2 (2025-11-18) **【守门人终审版】**:
  - **修复P0错误**：第71/313行 Rev 003 可逆性标注错误（已改为 Rev 004-006 不可逆）
  - **修复P0错误**：第305-309行 Rev 路线图补充实际文件名（Rev 004/005/006 拆分）
  - **修复P0错误**：第886-891行 revision 文件名更新为实际生成的脚本名
  - **修复P0错误**：第1088-1090行 回滚表格拆分 Rev 004/005/006 并明确影响范围
  - **新增P0功能**：第1053行 补充 Gate #3 决策后的风险记录位置和模板
  - **新增P1功能**：第45行后 增加"如何阅读本文档"导航（按角色分类）
  - **新增P1功能**：第789行 决策点补充 Phase 1 限定警告
  - **增强P1说明**：第154-164行 revision ID 加注释说明"以实际仓库为准"
  - **强化范围限定**：标题、检查清单、决策点多处强调"Phase 1 ONLY"
