# Migration #002: UserScopeMixin/AssignableMixin 外键约束 - 完整迁移指南

> **版本**: v1.1
> **创建日期**: 2025-11-19
> **迁移类型**: DDL - Schema Enhancement
> **数据风险**: 低
> **预计停机时间**: < 1 分钟
> **回滚复杂度**: 低（完全可逆）
>
> **SoT 参考**:
> - 数据结构定义: `docs/core/DATA_SCHEMA.md` § 1.1, § 3.1
> - ORM 模型: `backend/models/base.py` (UserScopeMixin, AssignableMixin)
> - 影响模型: `backend/models/core/project.py`, `backend/models/accounts/ad_account.py`

---

## 目录

1. [迁移概述](#1-迁移概述)
2. [技术背景](#2-技术背景)
3. [执行前准备](#3-执行前准备)
4. [执行方式详解](#4-执行方式详解)
5. [迁移后验证](#5-迁移后验证)
6. [回滚方案](#6-回滚方案)
7. [影响评估](#7-影响评估)
8. [常见问题](#8-常见问题)
9. [附录](#9-附录)

---

## 1. 迁移概述

### 1.1 业务目标

**问题**: SQLAlchemy ORM 模型中已定义外键关系，但数据库层面缺少对应的外键约束，导致：
1. 可以插入无效的用户引用（孤立记录）
2. 删除用户时需要应用层手动处理关联数据
3. 缺少数据库层面的引用完整性保证

**目标**: 为 `UserScopeMixin` 和 `AssignableMixin` 提供的字段添加数据库外键约束，实现 ORM 与数据库 schema 一致性。

### 1.2 变更范围

| 变更类型 | 对象 | 操作 | 说明 |
|---------|------|------|------|
| **外键约束** | `projects.created_by` | ADD CONSTRAINT | → users.id, ON DELETE SET NULL |
| **外键约束** | `ad_accounts.assigned_to` | ADD CONSTRAINT | → users.id, ON DELETE SET NULL |
| **索引** | `projects.created_by` | CREATE INDEX | btree 索引，提升查询性能 |
| **索引** | `ad_accounts.assigned_to` | CREATE INDEX | btree 索引，提升查询性能 |

**约束命名规范**:
```
fk_{源表名}_{源字段名}_{目标表名}
idx_{表名}_{字段名}
```

### 1.3 影响的模型

| ORM 模型 | 文件路径 | Mixin | 字段 | 关系定义 |
|---------|---------|-------|------|---------|
| `Project` | `backend/models/core/project.py` | UserScopeMixin | `created_by` | `creator = relationship("User", ...)` |
| `AdAccount` | `backend/models/accounts/ad_account.py` | AssignableMixin | `assigned_to` | `assigned_user = relationship("User", ...)` |

**注意**: `DailyReport` 和 `TopupRequest` 虽然有 `submitted_by`/`reviewed_by` 等字段，但它们**不使用 Mixin**，而是直接在模型中定义外键，因此不在本次迁移范围内。

---

## 2. 技术背景

### 2.1 UserScopeMixin 和 AssignableMixin

**定义位置**: `backend/models/base.py`

```python
class UserScopeMixin:
    """用户作用域 Mixin - 支持 RLS 权限控制"""

    @declared_attr
    def created_by(cls):
        """创建者 ID - 用于 RLS 权限过滤"""
        from sqlalchemy import ForeignKey
        return Column(
            PGUUID(as_uuid=True),
            ForeignKey("users.id", ondelete="SET NULL"),  # ← 本次迁移添加此行
            nullable=True,
            index=True,  # ← 本次迁移添加此行
            comment="创建者用户ID"
        )

class AssignableMixin:
    """可分配 Mixin - 用于账户/任务分配场景"""

    @declared_attr
    def assigned_to(cls):
        """负责人 ID - 用于 RLS 权限过滤"""
        from sqlalchemy import ForeignKey
        return Column(
            PGUUID(as_uuid=True),
            ForeignKey("users.id", ondelete="SET NULL"),  # ← 本次迁移添加此行
            nullable=True,
            index=True,  # ← 本次迁移添加此行
            comment="负责人用户ID"
        )
```

**迁移前状态**: ORM 模型已定义 ForeignKey，但**数据库层面没有约束**（执行 `\d projects` 不显示外键）

**迁移后状态**: 数据库 schema 与 ORM 定义完全一致

### 2.2 外键删除策略

```sql
ON DELETE SET NULL
```

**选择原因**:
1. ✅ **数据安全**: 删除用户时不会级联删除项目/账户
2. ✅ **审计友好**: 保留历史记录，仅将创建者/负责人设为 NULL
3. ✅ **业务合理**: 项目/账户的存在不依赖于创建者

**替代方案对比**:
| 策略 | 影响 | 适用场景 | 本项目 |
|------|------|---------|--------|
| `CASCADE` | 删除用户时删除所有关联记录 | 强依赖关系 | ❌ 不适用 |
| `SET NULL` | 删除用户时字段设为 NULL | 弱依赖关系 | ✅ **已选用** |
| `RESTRICT` | 有关联记录时禁止删除用户 | 严格引用完整性 | ❌ 影响用户删除 |
| `NO ACTION` | 与 RESTRICT 类似 | 同上 | ❌ 不适用 |

### 2.3 索引设计

**索引类型**: btree（PostgreSQL 默认）

**索引必要性分析**:
```sql
-- 常见查询模式 1: 按创建者查询项目
SELECT * FROM projects WHERE created_by = ?;

-- 常见查询模式 2: 按负责人查询账户
SELECT * FROM ad_accounts WHERE assigned_to = ?;

-- 常见查询模式 3: JOIN 查询
SELECT p.*, u.full_name
FROM projects p
JOIN users u ON p.created_by = u.id;
```

**性能提升预期**:
- 无索引: 全表扫描，O(n)
- 有索引: 索引扫描，O(log n)
- 数据量 10,000 条时，查询性能提升约 **100 倍**

---

## 3. 执行前准备

### 3.1 环境检查

#### 3.1.1 数据库连接验证

**Supabase 环境**:
```bash
# 从 Supabase Dashboard 获取连接信息
# Settings → Database → Connection string

# 测试连接（使用 Connection Pooler）
psql "postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:6543/postgres" \
  -c "SELECT version();"

# 或使用环境变量
export DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:6543/postgres"
psql "$DATABASE_URL" -c "SELECT current_database();"
```

**预期输出**:
```
     current_database
---------------------
 postgres
(1 row)
```

#### 3.1.2 权限检查

```sql
-- 检查当前用户权限（必须是 postgres 或 superuser）
SELECT
    current_user AS username,
    usesuper AS is_superuser
FROM pg_user
WHERE usename = current_user;
```

**要求**: `is_superuser = t` 或用户为 `postgres`

#### 3.1.3 表结构检查

```sql
-- 检查表是否存在
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('projects', 'ad_accounts', 'users')
ORDER BY table_name;
```

**预期结果**: 返回 3 行（ad_accounts, projects, users）

```sql
-- 检查字段是否存在
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND (
      (table_name = 'projects' AND column_name = 'created_by')
      OR (table_name = 'ad_accounts' AND column_name = 'assigned_to')
  )
ORDER BY table_name, column_name;
```

**预期结果**:
```
table_name   | column_name  | data_type | is_nullable
-------------+--------------+-----------+-------------
ad_accounts  | assigned_to  | uuid      | YES
projects     | created_by   | uuid      | YES
```

### 3.2 数据完整性检查（关键步骤）

#### 3.2.1 孤立记录检测

**目的**: 确保所有 `created_by`/`assigned_to` 值都指向有效的用户

```sql
-- 检查 projects 表
SELECT
    'projects' AS table_name,
    COUNT(*) AS total_records,
    COUNT(created_by) AS non_null_created_by,
    COUNT(*) FILTER (
        WHERE created_by IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM users WHERE id = projects.created_by)
    ) AS orphaned_records
FROM projects;

-- 检查 ad_accounts 表
SELECT
    'ad_accounts' AS table_name,
    COUNT(*) AS total_records,
    COUNT(assigned_to) AS non_null_assigned_to,
    COUNT(*) FILTER (
        WHERE assigned_to IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM users WHERE id = ad_accounts.assigned_to)
    ) AS orphaned_records
FROM ad_accounts;
```

**预期结果**: `orphaned_records = 0`

**如果 orphaned_records > 0**: 参见 [3.3 数据清理](#33-数据清理)

#### 3.2.2 NULL 值分布

```sql
-- 了解 NULL 值占比（影响索引效果）
SELECT
    'projects' AS table_name,
    COUNT(*) AS total,
    COUNT(created_by) AS non_null,
    ROUND(100.0 * COUNT(created_by) / NULLIF(COUNT(*), 0), 2) AS non_null_percentage
FROM projects

UNION ALL

SELECT
    'ad_accounts',
    COUNT(*),
    COUNT(assigned_to),
    ROUND(100.0 * COUNT(assigned_to) / NULLIF(COUNT(*), 0), 2)
FROM ad_accounts;
```

**建议**: 如果 `non_null_percentage < 10%`，索引收益可能较低，但仍建议创建（保证引用完整性）

### 3.3 数据清理

如果孤立记录检测失败（orphaned_records > 0），执行以下清理：

#### 方案 A: 设为 NULL（推荐）

```sql
BEGIN;

-- 清理 projects
UPDATE projects
SET created_by = NULL
WHERE created_by IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM users WHERE id = projects.created_by);

-- 清理 ad_accounts
UPDATE ad_accounts
SET assigned_to = NULL
WHERE assigned_to IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM users WHERE id = ad_accounts.assigned_to);

-- 验证清理结果
SELECT
    'projects' AS table_name,
    COUNT(*) FILTER (
        WHERE created_by IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM users WHERE id = projects.created_by)
    ) AS remaining_orphaned
FROM projects
UNION ALL
SELECT
    'ad_accounts',
    COUNT(*) FILTER (
        WHERE assigned_to IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM users WHERE id = ad_accounts.assigned_to)
    )
FROM ad_accounts;

-- 如果 remaining_orphaned = 0，则提交
COMMIT;
-- 否则 ROLLBACK;
```

#### 方案 B: 创建占位用户（慎用）

```sql
BEGIN;

-- 创建系统占位用户（如果不存在）
INSERT INTO users (id, username, full_name, role, is_active)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'system_deleted_user',
    'Deleted User',
    'viewer',
    false
)
ON CONFLICT (id) DO NOTHING;

-- 更新孤立记录
UPDATE projects
SET created_by = '00000000-0000-0000-0000-000000000001'
WHERE created_by IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM users WHERE id = projects.created_by);

UPDATE ad_accounts
SET assigned_to = '00000000-0000-0000-0000-000000000001'
WHERE assigned_to IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM users WHERE id = ad_accounts.assigned_to);

COMMIT;
```

### 3.4 备份策略

#### 3.4.1 Supabase 备份

1. **手动备份（推荐）**:
   - Supabase Dashboard → Settings → Database → Backups
   - 点击 "Create backup"
   - 备份类型: Full backup
   - 保留期限: 根据计划选择

2. **导出关键表（额外保险）**:
   ```bash
   # 导出 projects 表
   pg_dump "$DATABASE_URL" \
     --table=projects \
     --file=projects_backup_$(date +%Y%m%d_%H%M%S).sql

   # 导出 ad_accounts 表
   pg_dump "$DATABASE_URL" \
     --table=ad_accounts \
     --file=ad_accounts_backup_$(date +%Y%m%d_%H%M%S).sql
   ```

#### 3.4.2 验证备份

```bash
# 检查备份文件大小（不应为 0）
ls -lh *_backup_*.sql

# 检查备份内容（应包含 CREATE TABLE 和 COPY 语句）
head -n 50 projects_backup_*.sql
```

---

## 4. 执行方式详解

### 4.1 方式对比矩阵

| 维度 | Supabase SQL Editor | psql 命令行 | Alembic | 推荐场景 |
|------|-------------------|------------|---------|---------|
| **可视化** | ✅ 优秀 | ❌ 无 | ❌ 无 | 生产环境首选 |
| **版本管理** | ❌ 无 | ❌ 无 | ✅ 优秀 | 开发团队协作 |
| **回滚能力** | ⚠️ 手动 | ⚠️ 手动 | ✅ 自动 | 需要频繁回滚 |
| **CI/CD 集成** | ❌ 不支持 | ✅ 支持 | ✅ 支持 | 自动化部署 |
| **执行日志** | ✅ 详细 | ⚠️ 终端输出 | ✅ 详细 | 审计要求高 |
| **学习成本** | ✅ 低 | ⚠️ 中 | ⚠️ 高 | 快速执行 |

### 4.2 方式 1: Supabase SQL Editor（推荐 - 生产环境）

**优势**:
- ✅ 可视化界面，直观查看执行结果
- ✅ 自动保存查询历史
- ✅ 内置语法高亮和自动补全
- ✅ 执行日志详细，便于调试

**执行步骤**:

1. **登录 Supabase Dashboard**
   ```
   URL: https://supabase.com/dashboard/project/YOUR_PROJECT_ID
   ```

2. **进入 SQL Editor**
   - 左侧菜单: **Database** → **SQL Editor**
   - 点击 **New query** 创建新查询

3. **复制 SQL 脚本**
   ```bash
   # 在本地终端执行，复制输出
   cat backend/migrations/002_add_user_foreign_keys.sql
   ```

4. **粘贴并执行**
   - 粘贴到 SQL Editor
   - 点击 **Run** 或按 `Ctrl + Enter` (Windows/Linux) / `Cmd + Enter` (Mac)

5. **检查输出**
   - 查看 **Results** 面板
   - 应显示 `BEGIN`, `NOTICE`, `COMMIT` 等消息
   - **无 ERROR 提示**

**执行日志示例**:
```
BEGIN
NOTICE:  ✅ projects.created_by 数据完整性检查通过
NOTICE:  ✅ ad_accounts.assigned_to 数据完整性检查通过
NOTICE:  已创建索引 idx_projects_created_by
NOTICE:  已创建索引 idx_ad_accounts_assigned_to
NOTICE:  ✅ 所有外键约束创建成功！
NOTICE:  ✅ 所有索引创建成功！
NOTICE:  =================================================================
NOTICE:  迁移完成总结:
NOTICE:  - ✅ projects.created_by -> users.id (外键 + 索引)
NOTICE:  - ✅ ad_accounts.assigned_to -> users.id (外键 + 索引)
NOTICE:  - 外键策略: ON DELETE SET NULL
NOTICE:  - 所有操作已在事务中完成
NOTICE:  =================================================================
COMMIT
```

### 4.3 方式 2: psql 命令行

**前置准备**:

```bash
# 设置环境变量（从项目 .env 文件）
cd /path/to/AI_ad_spend02
source backend/.env

# 或手动设置
export DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:6543/postgres"

# 验证连接
psql "$DATABASE_URL" -c "SELECT current_database();"
```

**执行命令**:

```bash
# 方式 A: 直接执行文件
psql "$DATABASE_URL" -f backend/migrations/002_add_user_foreign_keys.sql

# 方式 B: 管道方式（适用于远程文件）
cat backend/migrations/002_add_user_foreign_keys.sql | psql "$DATABASE_URL"

# 方式 C: 交互式执行（逐行查看）
psql "$DATABASE_URL" < backend/migrations/002_add_user_foreign_keys.sql

# 方式 D: 生成执行日志
psql "$DATABASE_URL" \
  -f backend/migrations/002_add_user_foreign_keys.sql \
  > migration_002_$(date +%Y%m%d_%H%M%S).log 2>&1

# 查看日志
tail -f migration_002_*.log
```

**常见 psql 参数**:

| 参数 | 说明 | 示例 |
|------|------|------|
| `-f FILE` | 执行 SQL 文件 | `-f migration.sql` |
| `-c COMMAND` | 执行单个 SQL 命令 | `-c "SELECT version();"` |
| `-h HOST` | 数据库主机 | `-h db.xxx.supabase.co` |
| `-p PORT` | 端口 | `-p 6543` (Pooler) / `-p 5432` (Direct) |
| `-U USER` | 用户名 | `-U postgres` |
| `-d DATABASE` | 数据库名 | `-d postgres` |
| `-v` | 详细输出 | `-v ON_ERROR_STOP=1` |

**错误处理**:

```bash
# 启用错误时停止（推荐）
psql "$DATABASE_URL" \
  -v ON_ERROR_STOP=1 \
  -f backend/migrations/002_add_user_foreign_keys.sql

# 如果出错，事务会自动回滚
```

### 4.4 方式 3: Alembic（开发团队推荐）

**前置条件**:

```bash
# 1. 确认 Alembic 已安装
cd backend
python -c "import alembic; print('Alembic version:', alembic.__version__)"

# 2. 检查 Alembic 配置
cat alembic.ini | grep sqlalchemy.url

# 3. 查看当前迁移历史
alembic history

# 4. 查看当前版本
alembic current
```

**执行迁移**:

```bash
cd backend

# 方式 A: 升级到最新版本（推荐）
alembic upgrade head

# 方式 B: 升级到指定版本
alembic upgrade 20251119_user_fks

# 方式 C: 模拟执行（查看 SQL，不实际应用）
alembic upgrade 20251119_user_fks --sql > migration_002_preview.sql
cat migration_002_preview.sql

# 方式 D: 分步升级（逐个版本）
alembic upgrade +1
```

**验证执行**:

```bash
# 检查当前版本
alembic current
# 预期输出: 20251119_user_fks (head)

# 查看历史
alembic history --verbose
```

**Alembic 配置检查**:

```bash
# 检查 down_revision 是否正确
grep "down_revision" backend/alembic/versions/20251119_add_user_scope_foreign_keys.py
# 应该指向实际的前一个版本，而不是 None

# 如果 down_revision = None，需要手动修改
# 查看最新的 revision
alembic current
# 将输出的 revision ID 填入 down_revision
```

---

## 5. 迁移后验证

### 5.1 验证检查清单

**必须全部通过以下验证**:

- [ ] [验证 1: 外键约束存在](#51-验证-1-外键约束存在)
- [ ] [验证 2: 索引创建成功](#52-验证-2-索引创建成功)
- [ ] [验证 3: 外键约束功能测试](#53-验证-3-外键约束功能测试)
- [ ] [验证 4: 删除策略验证](#54-验证-4-删除策略验证)
- [ ] [验证 5: 索引使用验证](#55-验证-5-索引使用验证)
- [ ] [验证 6: ORM 模型同步](#56-验证-6-orm-模型同步)

### 5.1 验证 1: 外键约束存在

**目的**: 确认外键约束已创建，且配置正确

**SQL**:
```sql
SELECT
    tc.table_schema,
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule,
    rc.update_rule
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
JOIN information_schema.referential_constraints rc
    ON rc.constraint_name = tc.constraint_name
    AND rc.constraint_schema = tc.table_schema
WHERE tc.table_schema = 'public'
  AND tc.constraint_type = 'FOREIGN KEY'
  AND tc.constraint_name IN (
      'fk_projects_created_by_users',
      'fk_ad_accounts_assigned_to_users'
  )
ORDER BY tc.table_name;
```

**预期结果**:
```
table_schema | table_name   | constraint_name                   | constraint_type | column_name | foreign_table_name | foreign_column_name | delete_rule | update_rule
-------------+--------------+-----------------------------------+-----------------+-------------+--------------------+---------------------+-------------+-------------
public       | ad_accounts  | fk_ad_accounts_assigned_to_users  | FOREIGN KEY     | assigned_to | users              | id                  | SET NULL    | NO ACTION
public       | projects     | fk_projects_created_by_users      | FOREIGN KEY     | created_by  | users              | id                  | SET NULL    | NO ACTION
```

**验收标准**:
- ✅ 返回 2 行
- ✅ `delete_rule = 'SET NULL'`
- ✅ `foreign_table_name = 'users'`
- ✅ `foreign_column_name = 'id'`

### 5.2 验证 2: 索引创建成功

**目的**: 确认索引已创建，且类型正确

**SQL**:
```sql
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef,
    pg_size_pretty(pg_relation_size(indexname::regclass)) AS index_size
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN (
      'idx_projects_created_by',
      'idx_ad_accounts_assigned_to'
  )
ORDER BY tablename, indexname;
```

**预期结果**:
```
schemaname | tablename    | indexname                       | indexdef                                                      | index_size
-----------+--------------+---------------------------------+---------------------------------------------------------------+------------
public     | ad_accounts  | idx_ad_accounts_assigned_to     | CREATE INDEX ... ON public.ad_accounts USING btree (assigned_to) | 16 kB
public     | projects     | idx_projects_created_by         | CREATE INDEX ... ON public.projects USING btree (created_by)     | 16 kB
```

**验收标准**:
- ✅ 返回 2 行
- ✅ `indexdef` 包含 `USING btree`
- ✅ `index_size` 不为 0（具体大小取决于数据量）

### 5.3 验证 3: 外键约束功能测试

**目的**: 确认外键约束真正生效，拒绝无效插入

**SQL**:
```sql
-- 测试 1: 插入无效的 created_by（应失败）
BEGIN;

INSERT INTO projects (project_name, project_code, status, created_by)
VALUES (
    'Test Project FK',
    'TEST_FK_' || extract(epoch from now())::text,
    'draft',
    '00000000-0000-0000-0000-000000000000'  -- 不存在的用户
);

ROLLBACK;
```

**预期结果**: **必须失败**，错误信息：
```
ERROR:  insert or update on table "projects" violates foreign key constraint "fk_projects_created_by_users"
DETAIL:  Key (created_by)=(00000000-0000-0000-0000-000000000000) is not present in table "users".
```

```sql
-- 测试 2: 插入无效的 assigned_to（应失败）
BEGIN;

INSERT INTO ad_accounts (account_name, account_id_external, platform, status, assigned_to)
VALUES (
    'Test Account FK',
    'TEST_FK_' || extract(epoch from now())::text,
    'facebook',
    'new',
    '00000000-0000-0000-0000-000000000000'  -- 不存在的用户
);

ROLLBACK;
```

**预期结果**: **必须失败**

**验收标准**:
- ✅ 两个测试都抛出外键约束错误
- ✅ 事务已回滚（ROLLBACK 成功）

### 5.4 验证 4: 删除策略验证

**目的**: 确认 `ON DELETE SET NULL` 生效

**SQL**:
```sql
-- 准备测试数据
BEGIN;

-- 1. 创建测试用户
INSERT INTO users (id, username, full_name, role, is_active)
VALUES (
    'ffffffff-ffff-ffff-ffff-ffffffffffff',
    'test_delete_user',
    'Test Delete User',
    'viewer',
    true
);

-- 2. 创建关联的项目
INSERT INTO projects (project_name, project_code, status, created_by)
VALUES (
    'Test Delete Project',
    'TEST_DEL_' || extract(epoch from now())::text,
    'draft',
    'ffffffff-ffff-ffff-ffff-ffffffffffff'
);

-- 3. 删除用户
DELETE FROM users WHERE id = 'ffffffff-ffff-ffff-ffff-ffffffffffff';

-- 4. 检查项目的 created_by 是否被设为 NULL
SELECT
    project_name,
    created_by,
    CASE
        WHEN created_by IS NULL THEN '✅ PASS: created_by 已设为 NULL'
        ELSE '❌ FAIL: created_by 未设为 NULL'
    END AS test_result
FROM projects
WHERE project_name = 'Test Delete Project';

-- 5. 清理测试数据
DELETE FROM projects WHERE project_name = 'Test Delete Project';

ROLLBACK;
```

**预期结果**:
```
project_name          | created_by | test_result
----------------------+------------+----------------------------------
Test Delete Project   | NULL       | ✅ PASS: created_by 已设为 NULL
```

**验收标准**:
- ✅ `created_by` 字段为 NULL
- ✅ 项目记录未被删除（仅字段设为 NULL）

### 5.5 验证 5: 索引使用验证

**目的**: 确认查询真正使用了索引

**SQL**:
```sql
-- 测试 1: projects.created_by 索引
EXPLAIN (ANALYZE, BUFFERS, COSTS, VERBOSE)
SELECT * FROM projects
WHERE created_by = (SELECT id FROM users WHERE is_active = true LIMIT 1);
```

**预期结果** (关键部分):
```
Index Scan using idx_projects_created_by on public.projects
  Index Cond: (created_by = $0)
  Buffers: shared hit=...
```

**验收标准**:
- ✅ 执行计划包含 `Index Scan using idx_projects_created_by`
- ✅ **不是** `Seq Scan`（全表扫描）

```sql
-- 测试 2: ad_accounts.assigned_to 索引
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM ad_accounts
WHERE assigned_to = (SELECT id FROM users WHERE is_active = true LIMIT 1);
```

**预期结果**:
```
Index Scan using idx_ad_accounts_assigned_to on public.ad_accounts
  Index Cond: (assigned_to = $0)
```

**验收标准**: 同上

### 5.6 验证 6: ORM 模型同步

**目的**: 确认 SQLAlchemy 能正确识别外键

**Python 脚本**:
```python
# 在项目根目录执行
cd /path/to/AI_ad_spend02
python -c "
import sys
sys.path.insert(0, 'backend')

from backend.models import Project, AdAccount
from sqlalchemy.inspection import inspect

# 检查 Project 模型
project_mapper = inspect(Project)
fk_columns = [
    col.name for col in project_mapper.columns
    if col.foreign_keys
]
print(f'Project 外键列: {fk_columns}')

# 检查 AdAccount 模型
account_mapper = inspect(AdAccount)
fk_columns = [
    col.name for col in account_mapper.columns
    if col.foreign_keys
]
print(f'AdAccount 外键列: {fk_columns}')

# 验证 relationship 是否正常
assert hasattr(Project, 'creator'), 'Project.creator relationship 未定义'
assert hasattr(AdAccount, 'assigned_user'), 'AdAccount.assigned_user relationship 未定义'

print('✅ ORM 模型同步验证通过')
"
```

**预期输出**:
```
Project 外键列: ['created_by']
AdAccount 外键列: ['assigned_to']
✅ ORM 模型同步验证通过
```

---

## 6. 回滚方案

### 6.1 回滚决策树

```
是否需要回滚？
│
├─ 迁移执行失败 → 【无需回滚】（事务自动回滚）
│
├─ 验证失败
│  ├─ 外键约束缺失 → 【重新执行迁移】
│  ├─ 索引未创建 → 【手动创建索引】
│  └─ 功能测试失败 → 【检查数据完整性，修复后重新执行】
│
├─ 性能严重下降 → 【分析慢查询，优化后决定是否回滚】
│
└─ 应用程序错误 → 【分析代码兼容性，修复代码或回滚迁移】
```

### 6.2 回滚方式 1: 纯 SQL（快速）

**适用场景**: 紧急回滚，恢复到迁移前状态

```sql
BEGIN;

-- 步骤 1: 删除外键约束
ALTER TABLE projects DROP CONSTRAINT IF EXISTS fk_projects_created_by_users;
ALTER TABLE ad_accounts DROP CONSTRAINT IF EXISTS fk_ad_accounts_assigned_to_users;

-- 步骤 2: 删除索引
DROP INDEX IF EXISTS idx_projects_created_by;
DROP INDEX IF EXISTS idx_ad_accounts_assigned_to;

-- 步骤 3: 验证回滚结果
DO $$
DECLARE
    fk_count INTEGER;
    idx_count INTEGER;
BEGIN
    -- 检查外键约束（应为 0）
    SELECT COUNT(*) INTO fk_count
    FROM information_schema.table_constraints
    WHERE table_schema = 'public'
      AND constraint_name IN (
          'fk_projects_created_by_users',
          'fk_ad_accounts_assigned_to_users'
      );

    -- 检查索引（应为 0）
    SELECT COUNT(*) INTO idx_count
    FROM pg_indexes
    WHERE schemaname = 'public'
      AND indexname IN (
          'idx_projects_created_by',
          'idx_ad_accounts_assigned_to'
      );

    IF fk_count = 0 AND idx_count = 0 THEN
        RAISE NOTICE '✅ 回滚成功：所有约束和索引已删除';
    ELSE
        RAISE WARNING '⚠️  回滚不完整：外键 %, 索引 %', fk_count, idx_count;
    END IF;
END $$;

COMMIT;
```

**执行方式**:
```bash
# Supabase SQL Editor: 直接粘贴执行
# 或 psql:
psql "$DATABASE_URL" -c "$(cat <<'SQL'
BEGIN;
ALTER TABLE projects DROP CONSTRAINT IF EXISTS fk_projects_created_by_users;
ALTER TABLE ad_accounts DROP CONSTRAINT IF EXISTS fk_ad_accounts_assigned_to_users;
DROP INDEX IF EXISTS idx_projects_created_by;
DROP INDEX IF EXISTS idx_ad_accounts_assigned_to;
COMMIT;
SQL
)"
```

### 6.3 回滚方式 2: Alembic（版本管理）

**适用场景**: 团队协作，保持版本一致性

```bash
cd backend

# 方式 A: 回滚到上一个版本
alembic downgrade -1

# 方式 B: 回滚到指定版本（查看 alembic history 获取 revision）
alembic downgrade <previous_revision_id>

# 方式 C: 模拟回滚（查看 SQL，不实际执行）
alembic downgrade -1 --sql > rollback_002_preview.sql
cat rollback_002_preview.sql
```

**验证回滚**:
```bash
# 确认当前版本
alembic current
# 应该显示前一个版本，而不是 20251119_user_fks
```

### 6.4 回滚后验证

**验证检查清单**:

- [ ] 外键约束已删除
- [ ] 索引已删除
- [ ] 应用程序恢复正常
- [ ] 数据完整性未受影响

**SQL 验证**:
```sql
-- 验证 1: 外键约束已删除
SELECT COUNT(*) AS remaining_fk
FROM information_schema.table_constraints
WHERE table_schema = 'public'
  AND constraint_name IN (
      'fk_projects_created_by_users',
      'fk_ad_accounts_assigned_to_users'
  );
-- 预期: remaining_fk = 0

-- 验证 2: 索引已删除
SELECT COUNT(*) AS remaining_idx
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN (
      'idx_projects_created_by',
      'idx_ad_accounts_assigned_to'
  );
-- 预期: remaining_idx = 0

-- 验证 3: 数据未丢失
SELECT COUNT(*) AS projects_count FROM projects;
SELECT COUNT(*) AS accounts_count FROM ad_accounts;
-- 与回滚前对比，数量应一致
```

---

## 7. 影响评估

### 7.1 性能影响

#### 7.1.1 查询性能（正面影响）

**测试场景**: 查询某用户创建的所有项目

**Before（无索引）**:
```sql
EXPLAIN ANALYZE
SELECT * FROM projects WHERE created_by = '某个UUID';

-- 执行计划（无索引）
Seq Scan on projects  (cost=0.00..1234.56 rows=10 width=...)
  Filter: (created_by = '某个UUID')
  Rows Removed by Filter: 9990
Planning Time: 0.123 ms
Execution Time: 45.678 ms
```

**After（有索引）**:
```sql
EXPLAIN ANALYZE
SELECT * FROM projects WHERE created_by = '某个UUID';

-- 执行计划（有索引）
Index Scan using idx_projects_created_by on projects  (cost=0.29..12.34 rows=10 width=...)
  Index Cond: (created_by = '某个UUID')
Planning Time: 0.089 ms
Execution Time: 0.456 ms
```

**性能提升**: 约 **100 倍**（45.678 ms → 0.456 ms）

**提升原因**:
- 索引扫描 O(log n) vs 全表扫描 O(n)
- 减少磁盘 I/O
- 减少 CPU 过滤开销

#### 7.1.2 插入性能（负面影响）

**测试场景**: 插入新项目

**Before（无外键约束）**:
```sql
-- 插入 1000 条记录
INSERT INTO projects (project_name, project_code, status, created_by)
SELECT ...
-- 平均耗时: 0.5 ms/row
```

**After（有外键约束）**:
```sql
-- 插入 1000 条记录（需验证外键）
INSERT INTO projects (project_name, project_code, status, created_by)
SELECT ...
-- 平均耗时: 0.6 ms/row
```

**性能下降**: 约 **20%**（0.5 ms → 0.6 ms）

**影响评估**:
- ✅ **可接受**: 单次插入仅增加 ~0.1 ms
- ✅ **批量插入**: 使用 `COPY` 或批量 `INSERT` 性能影响更小
- ✅ **收益大于成本**: 数据完整性价值 >> 轻微性能损失

#### 7.1.3 存储空间

**索引大小估算**:

```sql
-- 查看索引实际大小
SELECT
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) AS index_size,
    pg_size_pretty(pg_table_size(tablename::regclass)) AS table_size,
    ROUND(
        100.0 * pg_relation_size(indexname::regclass) / NULLIF(pg_table_size(tablename::regclass), 0),
        2
    ) AS index_ratio_pct
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN ('idx_projects_created_by', 'idx_ad_accounts_assigned_to');
```

**预期结果** (基于 10,000 条记录):
```
indexname                       | index_size | table_size | index_ratio_pct
--------------------------------+------------+------------+-----------------
idx_projects_created_by         | 256 kB     | 2048 kB    | 12.50
idx_ad_accounts_assigned_to     | 128 kB     | 1024 kB    | 12.50
```

**影响评估**:
- ✅ **可接受**: 索引约占表大小的 10-15%
- ✅ **总增量**: < 1 MB（小型数据库），< 100 MB（大型数据库）

### 7.2 应用程序兼容性

| 影响维度 | Before | After | 兼容性 |
|---------|--------|-------|--------|
| **ORM 查询** | 正常 | 正常 | ✅ 100% 兼容 |
| **原生 SQL** | 可插入无效外键 | 拒绝无效外键 | ⚠️ 需处理外键错误 |
| **删除用户** | 需应用层处理 | 自动 SET NULL | ✅ 简化代码 |
| **JOIN 查询** | 性能一般 | 性能提升 | ✅ 正面影响 |

**代码修改需求**: ❌ **无需修改**（ORM 已定义外键）

**异常处理建议**:
```python
# 示例：捕获外键约束错误
try:
    db.session.add(new_project)
    db.session.commit()
except IntegrityError as e:
    if 'fk_projects_created_by_users' in str(e):
        raise ValueError("创建者用户不存在")
    raise
```

### 7.3 数据完整性提升

| 保护机制 | Before | After | 提升 |
|---------|--------|-------|------|
| **防止孤立记录** | ❌ 应用层检查 | ✅ 数据库强制 | 🔐 强制性提升 |
| **删除用户安全** | ⚠️ 手动处理 | ✅ 自动 SET NULL | 🔐 自动化保护 |
| **数据一致性** | ⚠️ 依赖代码 | ✅ 数据库约束 | 🔐 架构级保障 |

**风险降低**:
- ✅ **杜绝脏数据**: 无法插入无效用户引用
- ✅ **简化运维**: 删除用户不再需要手动清理关联
- ✅ **审计合规**: 数据库层面保证引用完整性

---

## 8. 常见问题

### Q1: 迁移执行失败，提示外键约束已存在

**现象**:
```
ERROR:  constraint "fk_projects_created_by_users" for relation "projects" already exists
```

**原因分析**:
1. 迁移已执行过（重复执行）
2. 手动创建过同名约束
3. 其他迁移脚本已创建约束

**解决方案**:

**方案 A: 检查现有约束**
```sql
-- 查看现有外键约束
SELECT
    constraint_name,
    table_name,
    constraint_type
FROM information_schema.table_constraints
WHERE table_schema = 'public'
  AND (
      constraint_name LIKE '%created_by%'
      OR constraint_name LIKE '%assigned_to%'
  )
  AND constraint_type = 'FOREIGN KEY';
```

如果约束名不同，修改迁移脚本中的约束名；
如果约束已存在且配置正确，跳过此迁移。

**方案 B: 删除现有约束后重新执行**
```sql
BEGIN;

-- 删除现有约束
ALTER TABLE projects DROP CONSTRAINT IF EXISTS fk_projects_created_by_users;
ALTER TABLE ad_accounts DROP CONSTRAINT IF EXISTS fk_ad_accounts_assigned_to_users;

-- 重新执行迁移脚本
-- ...

COMMIT;
```

**预防措施**: 迁移脚本已包含幂等性检查（`DROP CONSTRAINT IF EXISTS`），理论上不会出现此问题。

---

### Q2: 孤立记录导致迁移失败

**现象**:
```
ERROR:  insert or update on table "projects" violates foreign key constraint "fk_projects_created_by_users"
DETAIL:  Key (created_by)=(...) is not present in table "users".
```

**原因**: 表中存在 `created_by` 指向不存在用户的记录

**诊断**:
```sql
-- 查找孤立记录
SELECT
    id,
    project_name,
    project_code,
    created_by
FROM projects
WHERE created_by IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM users WHERE id = projects.created_by)
LIMIT 10;
```

**解决方案**:

**方案 A: 设为 NULL（推荐）**
```sql
UPDATE projects
SET created_by = NULL
WHERE created_by IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM users WHERE id = projects.created_by);
```

**方案 B: 创建占位用户**
```sql
-- 创建"已删除用户"占位
INSERT INTO users (id, username, full_name, role, is_active)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'system_deleted_user',
    '[Deleted User]',
    'viewer',
    false
)
ON CONFLICT DO NOTHING;

-- 更新孤立记录
UPDATE projects
SET created_by = '00000000-0000-0000-0000-000000000001'
WHERE created_by IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM users WHERE id = projects.created_by);
```

**方案 C: 删除孤立记录（谨慎使用）**
```sql
-- ⚠️ 慎用：会永久删除数据
DELETE FROM projects
WHERE created_by IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM users WHERE id = projects.created_by);
```

---

### Q3: 索引创建失败或性能不佳

**现象 1: 索引创建失败**
```
ERROR:  could not create unique index "..."
DETAIL:  Key (created_by)=(...) is duplicated.
```

**原因**: 误用 UNIQUE 索引（迁移脚本使用普通索引，不应出现）

**解决方案**: 检查迁移脚本，确保使用 `CREATE INDEX` 而非 `CREATE UNIQUE INDEX`

---

**现象 2: 查询未使用索引**

**诊断**:
```sql
EXPLAIN SELECT * FROM projects WHERE created_by = '某个UUID';

-- 如果显示 Seq Scan，说明未使用索引
```

**可能原因**:
1. 索引未创建成功
2. 表数据太少（< 1000 行），PostgreSQL 认为全表扫描更快
3. 查询条件不匹配（如使用了函数：`UPPER(created_by)`）

**解决方案**:
```sql
-- 1. 检查索引是否存在
SELECT * FROM pg_indexes WHERE indexname = 'idx_projects_created_by';

-- 2. 强制使用索引（仅用于测试）
SET enable_seqscan = OFF;
EXPLAIN SELECT * FROM projects WHERE created_by = '某个UUID';
SET enable_seqscan = ON;

-- 3. 重建索引
REINDEX INDEX idx_projects_created_by;
```

---

### Q4: 删除用户时出现外键错误

**现象**:
```
ERROR:  update or delete on table "users" violates foreign key constraint "..."
DETAIL:  Key (id)=(...) is still referenced from table "...".
```

**原因**: 配置错误，实际使用了 `ON DELETE RESTRICT` 而非 `ON DELETE SET NULL`

**诊断**:
```sql
SELECT delete_rule
FROM information_schema.referential_constraints
WHERE constraint_name = 'fk_projects_created_by_users';
-- 应该返回: SET NULL
```

**解决方案**: 重新执行迁移，确保约束定义正确

---

### Q5: Alembic 版本冲突

**现象**:
```
alembic.util.exc.CommandError: Target database is not up to date.
```

**原因**: 本地 Alembic 版本与数据库版本不一致

**解决方案**:
```bash
# 1. 查看数据库当前版本
alembic current

# 2. 查看所有版本历史
alembic history

# 3. 强制升级到最新版本
alembic upgrade head

# 4. 如果有多个分支，合并分支
alembic merge heads
```

---

## 9. 附录

### 9.1 相关文件清单

| 文件类型 | 路径 | 说明 |
|---------|------|------|
| **SQL 迁移脚本** | `backend/migrations/002_add_user_foreign_keys.sql` | 纯 SQL 版本，适用于 Supabase/psql |
| **Alembic 迁移** | `backend/alembic/versions/20251119_add_user_scope_foreign_keys.py` | Alembic 版本管理脚本 |
| **快速执行指南** | `docs/migrations/002_QUICK_START.md` | 快速参考和执行步骤 |
| **详细迁移指南** | `docs/migrations/002_MIGRATION_GUIDE.md` | 本文档 |
| **ORM 模型定义** | `backend/models/base.py` | UserScopeMixin, AssignableMixin 定义 |
| **影响的模型** | `backend/models/core/project.py` | Project 模型 |
| **影响的模型** | `backend/models/accounts/ad_account.py` | AdAccount 模型 |
| **数据库规范** | `docs/core/DATA_SCHEMA.md` | 数据库结构 SoT |

### 9.2 环境变量参考

**Supabase 连接配置** (来自 `backend/.env.example`):

```bash
# 数据库连接 URL (Connection Pooler 模式 - 推荐)
DATABASE_URL=postgresql://postgres.[PASSWORD]@db.[PROJECT-REF].supabase.co:6543/postgres

# Supabase 配置
SUPABASE_URL=https://[PROJECT-REF].supabase.co
SUPABASE_ANON_KEY=[YOUR_ANON_KEY]
SUPABASE_SERVICE_ROLE_KEY=[YOUR_SERVICE_ROLE_KEY]
```

**psql 环境变量**:
```bash
# 设置连接参数
export PGHOST="db.[PROJECT-REF].supabase.co"
export PGPORT="6543"  # Connection Pooler
export PGDATABASE="postgres"
export PGUSER="postgres"
export PGPASSWORD="[YOUR_PASSWORD]"
```

### 9.3 约束命名规范

根据项目 `DATA_SCHEMA.md` 规范：

| 对象类型 | 命名规则 | 示例 |
|---------|---------|------|
| **外键约束** | `fk_{源表}_{源字段}_{目标表}` | `fk_projects_created_by_users` |
| **主键约束** | `pk_{表名}` 或 `{表名}_pkey` | `projects_pkey` |
| **唯一约束** | `uq_{表名}_{字段}` | `uq_projects_project_code` |
| **检查约束** | `ck_{表名}_{字段}_{条件}` | `ck_projects_status_enum` |
| **索引** | `idx_{表名}_{字段}` | `idx_projects_created_by` |
| **部分索引** | `idx_{表名}_{字段}_{条件}` | `idx_projects_status_active` |

### 9.4 执行日志示例

**成功执行的完整日志**:

```
psql:002_add_user_foreign_keys.sql:20: BEGIN
psql:002_add_user_foreign_keys.sql:41: NOTICE:  ✅ projects.created_by 数据完整性检查通过
psql:002_add_user_foreign_keys.sql:58: NOTICE:  ✅ ad_accounts.assigned_to 数据完整性检查通过
psql:002_add_user_foreign_keys.sql:88: NOTICE:  (无旧约束，跳过删除)
ALTER TABLE
psql:002_add_user_foreign_keys.sql:103: COMMENT
psql:002_add_user_foreign_keys.sql:117: NOTICE:  已创建索引 idx_projects_created_by
ALTER TABLE
psql:002_add_user_foreign_keys.sql:132: COMMENT
psql:002_add_user_foreign_keys.sql:146: NOTICE:  已创建索引 idx_ad_accounts_assigned_to
psql:002_add_user_foreign_keys.sql:167: NOTICE:  ✅ 所有外键约束创建成功！
psql:002_add_user_foreign_keys.sql:183: NOTICE:  ✅ 所有索引创建成功！
psql:002_add_user_foreign_keys.sql:195: NOTICE:  =================================================================
psql:002_add_user_foreign_keys.sql:195: NOTICE:  迁移完成总结:
psql:002_add_user_foreign_keys.sql:195: NOTICE:  - ✅ projects.created_by -> users.id (外键 + 索引)
psql:002_add_user_foreign_keys.sql:195: NOTICE:  - ✅ ad_accounts.assigned_to -> users.id (外键 + 索引)
psql:002_add_user_foreign_keys.sql:195: NOTICE:  - 外键策略: ON DELETE SET NULL
psql:002_add_user_foreign_keys.sql:195: NOTICE:  - 所有操作已在事务中完成
psql:002_add_user_foreign_keys.sql:195: NOTICE:  =================================================================
COMMIT
```

### 9.5 PostgreSQL 版本兼容性

| PostgreSQL 版本 | 兼容性 | 说明 |
|----------------|--------|------|
| **15.x** (Supabase 默认) | ✅ 完全兼容 | 推荐版本 |
| **14.x** | ✅ 完全兼容 | 所有功能可用 |
| **13.x** | ✅ 兼容 | `ON DELETE SET NULL` 自 9.x 起支持 |
| **12.x 及更早** | ⚠️ 未测试 | 理论兼容，但建议升级 |

**最低要求**: PostgreSQL 9.1+ (支持 `IF EXISTS`, `DO` 块)

---

## 📞 技术支持

### 联系方式

| 角色 | 联系方式 | 响应时间 |
|------|---------|---------|
| **DBA 团队** | dba@company.com | P0: 15 分钟, P1: 1 小时 |
| **系统架构师** | architect@company.com | P0: 30 分钟, P1: 2 小时 |
| **开发团队** | dev@company.com | P2: 1 工作日 |

### 问题分类

| 优先级 | 定义 | 示例 |
|-------|------|------|
| **P0 - 紧急** | 生产环境故障 | 迁移导致应用崩溃 |
| **P1 - 高优先级** | 影响业务功能 | 性能严重下降 |
| **P2 - 中优先级** | 非关键问题 | 文档疑问，优化建议 |

### 提交问题时需提供的信息

1. **环境信息**:
   - PostgreSQL 版本: `SELECT version();`
   - Supabase Project ID
   - 执行方式: SQL Editor / psql / Alembic

2. **错误信息**:
   - 完整的错误日志
   - 执行的 SQL 语句
   - 相关表的结构: `\d projects`, `\d ad_accounts`

3. **数据状态**:
   - 表记录数: `SELECT COUNT(*) FROM projects;`
   - 孤立记录数: [见 3.2.1](#321-孤立记录检测)

---

## 📝 文档变更记录

| 日期 | 版本 | 变更内容 | 作者 |
|------|------|---------|------|
| 2025-11-19 | v1.0 | 初始版本 | 系统架构团队 |
| 2025-11-19 | v1.1 | 优化版本 - 完善执行步骤、验证流程、故障排查 | 系统架构团队 |

**v1.1 主要改进**:
1. ✅ 对齐项目环境变量规范（`DATABASE_URL`, `SUPABASE_*`）
2. ✅ 完善 Supabase Connection Pooler 说明
3. ✅ 添加完整的验证 SQL 和预期结果
4. ✅ 补充 ORM 模型同步验证
5. ✅ 扩展常见问题和解决方案
6. ✅ 添加约束命名规范引用 `DATA_SCHEMA.md`

---

✨ **最佳实践**: 首次执行请在开发/测试环境完整走完所有验证步骤，确认无误后再在生产环境执行。
