# 数据库迁移指南：添加 UserScopeMixin/AssignableMixin 外键约束

## 📋 迁移概述

**迁移编号**: 002
**创建日期**: 2025-11-19
**影响范围**: 2 个表，2 个外键约束，2 个索引
**数据风险**: 低
**预计停机时间**: < 1 分钟

### 迁移目的

为 `backend/models/base.py` 中的 `UserScopeMixin` 和 `AssignableMixin` 添加数据库层面的外键约束。这些 Mixin 提供了 `created_by` 和 `assigned_to` 字段用于 RLS 权限控制，现在需要在数据库层面强制引用完整性。

### 影响的表

| 表名 | 字段 | Mixin | 目标表 | 删除策略 |
|------|------|-------|--------|----------|
| `projects` | `created_by` | UserScopeMixin | `users.id` | SET NULL |
| `ad_accounts` | `assigned_to` | AssignableMixin | `users.id` | SET NULL |

---

## 🚀 执行方式

### 方式 1: 使用纯 SQL（推荐用于 Supabase）

#### 步骤 1: 在 Supabase Dashboard 执行

1. 登录 Supabase Dashboard
2. 进入 SQL Editor
3. 复制 `002_add_user_foreign_keys.sql` 的全部内容
4. 点击 "Run" 执行
5. 检查执行结果，确认所有步骤都成功

#### 步骤 2: 使用 psql 执行（命令行方式）

```bash
# 方式 1: 直接执行 SQL 文件
psql -h <your-supabase-host> \
     -U postgres \
     -d postgres \
     -f backend/migrations/002_add_user_foreign_keys.sql

# 方式 2: 从标准输入执行
cat backend/migrations/002_add_user_foreign_keys.sql | \
psql -h <your-supabase-host> \
     -U postgres \
     -d postgres
```

**替换参数说明**:
- `<your-supabase-host>`: 你的 Supabase 数据库主机地址（在 Supabase Dashboard 的 Settings > Database > Connection string 中查看）
- 数据库密码会在执行时提示输入

---

### 方式 2: 使用 Alembic（推荐用于本地开发）

#### 前提条件

1. 确保已安装 Alembic：
   ```bash
   pip install alembic
   ```

2. 检查 Alembic 配置是否正确：
   ```bash
   cd backend
   alembic current
   ```

#### 执行迁移

```bash
cd backend

# 1. 查看待执行的迁移
alembic history

# 2. 查看当前版本
alembic current

# 3. 执行迁移（升级到最新版本）
alembic upgrade head

# 或者执行到指定版本
alembic upgrade 20251119_user_fks
```

#### 回滚迁移（如需要）

```bash
cd backend

# 回滚到上一个版本
alembic downgrade -1

# 或者回滚到指定版本
alembic downgrade <previous_revision_id>
```

---

## ✅ 迁移前检查清单

在执行迁移前，请确认以下事项：

- [ ] **备份数据库**（强烈推荐）
  ```sql
  -- 在 Supabase Dashboard 中：Settings > Database > Database Backups
  ```

- [ ] **检查数据完整性**
  ```sql
  -- 检查 projects 表中是否有孤立的 created_by
  SELECT COUNT(*) AS invalid_projects
  FROM projects p
  WHERE p.created_by IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = p.created_by);

  -- 检查 ad_accounts 表中是否有孤立的 assigned_to
  SELECT COUNT(*) AS invalid_accounts
  FROM ad_accounts a
  WHERE a.assigned_to IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = a.assigned_to);
  ```

  **预期结果**: 两个查询都应返回 0。如果不是 0，需要先修复数据。

- [ ] **检查是否在低峰期执行**
  - 建议在用户访问量较低的时段执行
  - 或者在维护窗口期执行

- [ ] **确认数据库连接正常**
  ```bash
  psql -h <your-supabase-host> -U postgres -d postgres -c "SELECT version();"
  ```

---

## 🔍 迁移后验证

### 验证步骤 1: 检查外键约束是否创建成功

```sql
SELECT
    tc.table_name,
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints rc
    ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_name IN ('fk_projects_created_by_users', 'fk_ad_accounts_assigned_to_users')
ORDER BY tc.table_name;
```

**预期结果**:
```
table_name   | constraint_name                    | column_name | foreign_table_name | foreign_column_name | delete_rule
-------------+-----------------------------------+-------------+--------------------+---------------------+-------------
projects     | fk_projects_created_by_users      | created_by  | users              | id                  | SET NULL
ad_accounts  | fk_ad_accounts_assigned_to_users  | assigned_to | users              | id                  | SET NULL
```

### 验证步骤 2: 检查索引是否创建成功

```sql
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE indexname IN ('idx_projects_created_by', 'idx_ad_accounts_assigned_to')
ORDER BY tablename;
```

**预期结果**:
```
tablename    | indexname                       | indexdef
-------------+---------------------------------+--------------------------------------------------------
ad_accounts  | idx_ad_accounts_assigned_to     | CREATE INDEX ... ON ad_accounts USING btree (assigned_to)
projects     | idx_projects_created_by         | CREATE INDEX ... ON projects USING btree (created_by)
```

### 验证步骤 3: 测试外键约束是否生效

```sql
BEGIN;

-- 尝试插入一条指向不存在用户的记录（应该失败）
INSERT INTO projects (project_name, project_code, status, created_by)
VALUES ('Test Project', 'TEST001', 'draft', '00000000-0000-0000-0000-000000000000');

ROLLBACK;
```

**预期结果**: 应该收到外键约束错误：
```
ERROR:  insert or update on table "projects" violates foreign key constraint "fk_projects_created_by_users"
DETAIL:  Key (created_by)=(00000000-0000-0000-0000-000000000000) is not present in table "users".
```

### 验证步骤 4: 性能验证

```sql
-- 检查查询是否使用了新创建的索引
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM projects
WHERE created_by = (SELECT id FROM users LIMIT 1);

EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM ad_accounts
WHERE assigned_to = (SELECT id FROM users LIMIT 1);
```

**预期结果**: 执行计划中应该显示 `Index Scan using idx_projects_created_by` 或 `Index Scan using idx_ad_accounts_assigned_to`

---

## 🔄 回滚方案

如果迁移出现问题，可以使用以下方式回滚：

### 方式 1: 使用纯 SQL 回滚

在 SQL 文件末尾已经提供了回滚脚本（注释部分）：

```sql
BEGIN;

-- 删除外键约束
ALTER TABLE projects DROP CONSTRAINT IF EXISTS fk_projects_created_by_users;
ALTER TABLE ad_accounts DROP CONSTRAINT IF EXISTS fk_ad_accounts_assigned_to_users;

-- 删除索引
DROP INDEX IF EXISTS idx_projects_created_by;
DROP INDEX IF EXISTS idx_ad_accounts_assigned_to;

COMMIT;
```

### 方式 2: 使用 Alembic 回滚

```bash
cd backend

# 回滚到上一个版本
alembic downgrade -1
```

---

## 📊 预期影响

### 性能影响

- **正面影响**:
  - 新增的索引会提升 `WHERE created_by = ?` 和 `WHERE assigned_to = ?` 查询的性能
  - 外键约束会防止数据不一致

- **负面影响**:
  - 插入/更新操作会有轻微的性能开销（需要验证外键）
  - 索引会占用额外的存储空间（预计每个索引 < 1MB）

### 应用程序影响

- **无影响**: 这是数据库层面的改动，应用程序代码不需要修改
- **ORM 同步**: SQLAlchemy 模型 (backend/models/base.py) 已经定义了外键，这次迁移只是让数据库schema 与 ORM 定义保持一致

### 数据完整性提升

- 插入/更新操作时会自动验证 `created_by` 和 `assigned_to` 是否指向有效的用户
- 删除用户时，相关记录的 `created_by`/`assigned_to` 会被自动设为 `NULL`（而不是级联删除）

---

## 🐛 常见问题

### Q1: 迁移失败，提示外键约束已存在

**原因**: 外键约束可能已经存在（手动创建过或之前的迁移创建过）

**解决方案**: 迁移脚本已经包含了检查和删除旧约束的逻辑，应该不会出现此问题。如果仍然出现，可以手动删除后重新执行：

```sql
ALTER TABLE projects DROP CONSTRAINT IF EXISTS fk_projects_created_by_users;
ALTER TABLE ad_accounts DROP CONSTRAINT IF EXISTS fk_ad_accounts_assigned_to_users;
```

### Q2: 迁移失败，提示数据完整性错误

**原因**: 存在孤立记录（`created_by` 或 `assigned_to` 指向不存在的用户）

**解决方案**:

```sql
-- 方案 1: 将孤立值设为 NULL
UPDATE projects SET created_by = NULL
WHERE created_by IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = projects.created_by);

UPDATE ad_accounts SET assigned_to = NULL
WHERE assigned_to IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = ad_accounts.assigned_to);

-- 方案 2: 删除孤立记录（谨慎使用！）
-- DELETE FROM projects WHERE ...
```

### Q3: 索引创建失败，提示索引已存在

**原因**: 索引可能已经存在

**解决方案**: 迁移脚本已经包含了检查逻辑，会跳过已存在的索引。如果仍然出现问题：

```sql
DROP INDEX IF EXISTS idx_projects_created_by;
DROP INDEX IF EXISTS idx_ad_accounts_assigned_to;
```

然后重新执行迁移。

---

## 📞 支持

如果在迁移过程中遇到问题，请：

1. 检查迁移日志，找出具体的错误信息
2. 参考"常见问题"部分
3. 联系数据库管理员或开发团队

---

## 📝 变更记录

| 日期 | 版本 | 说明 | 作者 |
|------|------|------|------|
| 2025-11-19 | v1.0 | 初始版本 - 添加 UserScopeMixin/AssignableMixin 外键约束 | Claude |

---

## 🔗 相关文件

- SQL 迁移脚本: `backend/migrations/002_add_user_foreign_keys.sql`
- Alembic 迁移脚本: `backend/alembic/versions/20251119_add_user_scope_foreign_keys.py`
- ORM 模型定义: `backend/models/base.py`
- 影响的模型:
  - `backend/models/core/project.py`
  - `backend/models/accounts/ad_account.py`
