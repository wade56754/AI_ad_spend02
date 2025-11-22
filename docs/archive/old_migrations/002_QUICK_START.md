# Migration #002: UserScopeMixin/AssignableMixin 外键约束 - 快速执行指南

> **版本**: v1.1
> **创建日期**: 2025-11-19
> **迁移类型**: DDL - 添加外键约束和索引
> **数据风险**: 低
> **预计执行时间**: < 1 分钟
> **SoT 参考**: `docs/core/DATA_SCHEMA.md` § 1.1

---

## 📋 迁移概要

### 业务背景

backend/models/base.py 中的 `UserScopeMixin` 和 `AssignableMixin` 为 ORM 模型提供了 RLS 权限控制字段（`created_by` 和 `assigned_to`），但数据库层面缺少外键约束。本次迁移将添加数据库外键约束，确保引用完整性。

### 影响范围

| 表名 | 字段 | Mixin 来源 | 外键目标 | 删除策略 | 索引名称 |
|------|------|-----------|---------|---------|---------|
| `projects` | `created_by` | UserScopeMixin | `users.id` (UUID) | SET NULL | `idx_projects_created_by` |
| `ad_accounts` | `assigned_to` | AssignableMixin | `users.id` (UUID) | SET NULL | `idx_ad_accounts_assigned_to` |

**约束名称**:
- `fk_projects_created_by_users`
- `fk_ad_accounts_assigned_to_users`

---

## ⚡ 执行方式选择矩阵

| 环境 | 推荐方式 | 命令/位置 | 优势 |
|------|---------|----------|------|
| **Supabase 生产环境** | SQL Editor | Supabase Dashboard | ✅ 可视化，自动事务，执行日志 |
| **本地开发（已配置 Alembic）** | Alembic | `alembic upgrade head` | ✅ 版本管理，可回滚，团队同步 |
| **CI/CD 自动化** | psql 脚本 | `psql -f migration.sql` | ✅ 脚本化，可集成管道 |

---

## 🚀 方式 1: Supabase Dashboard（推荐 - 生产环境）

### 执行步骤

1. **登录 Supabase Dashboard**
   - 访问: https://supabase.com/dashboard/project/YOUR_PROJECT_ID

2. **进入 SQL Editor**
   - 左侧菜单：Database → SQL Editor
   - 点击 "New query"

3. **复制并执行 SQL**
   ```bash
   # 复制 SQL 文件内容
   cat backend/migrations/002_add_user_foreign_keys.sql
   ```
   - 粘贴到 SQL Editor
   - 点击 "Run" 或按 `Ctrl+Enter`

4. **检查执行结果**
   - 查看 Output 面板，应显示：
     ```
     ✅ 所有外键约束创建成功！
     ✅ 所有索引创建成功！
     =================================================================
     迁移完成总结:
     - ✅ projects.created_by -> users.id (外键 + 索引)
     - ✅ ad_accounts.assigned_to -> users.id (外键 + 索引)
     - 外键策略: ON DELETE SET NULL
     - 所有操作已在事务中完成
     =================================================================
     ```

---

## 🖥️ 方式 2: psql 命令行（本地/CI/CD）

### 前置准备

从 Supabase Dashboard 获取数据库连接信息：

1. **获取连接字符串**
   - 路径: Settings → Database → Connection string
   - 选择 "Connection Pooler" 模式（推荐用于应用程序）

2. **设置环境变量**
   ```bash
   # 方式 A: 使用项目 .env 文件（推荐）
   source backend/.env  # 确保 DATABASE_URL 已配置

   # 方式 B: 手动设置（临时）
   export PGHOST="db.YOUR_PROJECT_REF.supabase.co"
   export PGDATABASE="postgres"
   export PGUSER="postgres"
   export PGPASSWORD="YOUR_DB_PASSWORD"
   export PGPORT="6543"  # Connection Pooler 端口

   # ⚠️ 生产环境必须使用 Connection Pooler（端口 6543）
   # Direct Connection（端口 5432）仅用于数据库管理工具
   ```

### 执行迁移

```bash
# 方式 A: 从项目根目录执行
psql "$DATABASE_URL" -f backend/migrations/002_add_user_foreign_keys.sql

# 方式 B: 使用环境变量（如已导出）
psql -f backend/migrations/002_add_user_foreign_keys.sql

# 方式 C: 管道方式
cat backend/migrations/002_add_user_foreign_keys.sql | psql "$DATABASE_URL"
```

**预期输出示例**:
```
BEGIN
NOTICE:  ✅ projects.created_by 数据完整性检查通过
NOTICE:  ✅ ad_accounts.assigned_to 数据完整性检查通过
NOTICE:  已创建索引 idx_projects_created_by
NOTICE:  已创建索引 idx_ad_accounts_assigned_to
NOTICE:  ✅ 所有外键约束创建成功！
NOTICE:  ✅ 所有索引创建成功！
COMMIT
```

---

## 🔧 方式 3: Alembic（本地开发 - 版本管理）

### 前置条件检查

```bash
# 1. 确认 Alembic 已安装
cd backend
python -c "import alembic; print(alembic.__version__)"

# 2. 检查当前迁移版本
alembic current

# 3. 查看待执行的迁移
alembic history | grep 20251119_user_fks
```

### 执行迁移

```bash
cd backend

# 方式 A: 升级到最新版本（推荐）
alembic upgrade head

# 方式 B: 升级到指定版本
alembic upgrade 20251119_user_fks

# 方式 C: 模拟执行（不实际应用，仅查看 SQL）
alembic upgrade 20251119_user_fks --sql
```

### 验证迁移结果

```bash
# 确认当前版本
alembic current
# 预期输出: 20251119_user_fks (head)
```

---

## ✅ 迁移后验证（必须执行）

### 验证 1: 外键约束检查

```sql
-- 在 Supabase SQL Editor 或 psql 中执行
SELECT
    tc.table_name,
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name AS foreign_table,
    ccu.column_name AS foreign_column,
    rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu USING (constraint_name, table_schema)
JOIN information_schema.constraint_column_usage ccu USING (constraint_name, table_schema)
JOIN information_schema.referential_constraints rc USING (constraint_name, constraint_schema)
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
table_name   | constraint_name                   | column_name | foreign_table | foreign_column | delete_rule
-------------+-----------------------------------+-------------+---------------+----------------+-------------
ad_accounts  | fk_ad_accounts_assigned_to_users  | assigned_to | users         | id             | SET NULL
projects     | fk_projects_created_by_users      | created_by  | users         | id             | SET NULL
```

✅ **验收标准**: 返回 2 行，delete_rule 均为 `SET NULL`

---

### 验证 2: 索引检查

```sql
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN (
      'idx_projects_created_by',
      'idx_ad_accounts_assigned_to'
  )
ORDER BY tablename;
```

**预期结果**:
```
schemaname | tablename    | indexname                       | indexdef
-----------+--------------+---------------------------------+---------------------------------------------
public     | ad_accounts  | idx_ad_accounts_assigned_to     | CREATE INDEX ... ON public.ad_accounts USING btree (assigned_to)
public     | projects     | idx_projects_created_by         | CREATE INDEX ... ON public.projects USING btree (created_by)
```

✅ **验收标准**: 返回 2 行，索引类型为 btree

---

### 验证 3: 外键约束功能测试

```sql
-- 测试插入无效外键（应该失败）
BEGIN;

INSERT INTO projects (project_name, project_code, status, created_by)
VALUES ('Test Project', 'TEST_FK_001', 'draft', '00000000-0000-0000-0000-000000000000');

ROLLBACK;
```

**预期结果**:
```
ERROR:  insert or update on table "projects" violates foreign key constraint "fk_projects_created_by_users"
DETAIL:  Key (created_by)=(00000000-0000-0000-0000-000000000000) is not present in table "users".
```

✅ **验收标准**: 抛出外键约束错误，事务已回滚

---

### 验证 4: 性能验证（索引使用）

```sql
-- 查看查询计划，确认使用索引
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM projects
WHERE created_by = (SELECT id FROM users LIMIT 1);
```

**预期结果** (执行计划中应包含):
```
-> Index Scan using idx_projects_created_by on projects
   Index Cond: (created_by = $0)
```

✅ **验收标准**: 执行计划显示使用了 `idx_projects_created_by` 索引

---

## 🔄 回滚方案

### 何时需要回滚？

- ✅ 迁移执行失败（事务会自动回滚，无需手动处理）
- ✅ 验证失败，需要撤销更改
- ✅ 发现性能问题或数据完整性问题

### 回滚方式 1: SQL（快速回滚）

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

### 回滚方式 2: Alembic（推荐 - 版本管理）

```bash
cd backend

# 回滚到上一个版本
alembic downgrade -1

# 或回滚到指定版本
alembic downgrade <previous_revision_id>
```

### 验证回滚成功

```sql
-- 检查外键约束是否已删除（应返回 0 行）
SELECT constraint_name
FROM information_schema.table_constraints
WHERE table_schema = 'public'
  AND constraint_name IN (
      'fk_projects_created_by_users',
      'fk_ad_accounts_assigned_to_users'
  );

-- 检查索引是否已删除（应返回 0 行）
SELECT indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN (
      'idx_projects_created_by',
      'idx_ad_accounts_assigned_to'
  );
```

---

## 📊 迁移影响评估

### 性能影响

| 方面 | 影响 | 说明 |
|------|------|------|
| **查询性能** | ✅ **提升** | 新增索引加速 WHERE created_by/assigned_to 查询 |
| **插入性能** | ⚠️ **轻微下降** | 外键验证增加 ~5-10ms 延迟（单次操作） |
| **存储空间** | ⚠️ **增加** | 每个索引预计 < 1MB（取决于数据量） |
| **锁定时间** | ✅ **< 1s** | DDL 操作短暂锁表，事务性执行 |

### 数据完整性提升

| 改进项 | Before | After |
|--------|--------|-------|
| **孤立记录检测** | ❌ 应用层检查 | ✅ 数据库层强制 |
| **删除用户安全性** | ❌ 需手动处理关联 | ✅ 自动 SET NULL |
| **插入数据验证** | ⚠️ 可插入无效 UUID | ✅ 拒绝无效外键 |

### 应用程序兼容性

- ✅ **无需修改代码**: ORM 模型已定义外键，此次仅同步数据库
- ✅ **向后兼容**: 现有查询和业务逻辑无影响
- ✅ **RLS 策略**: 不影响现有 RLS 权限控制逻辑

---

## ⚠️ 执行前检查清单

**在执行迁移前，请确认以下所有项目**:

- [ ] **数据库备份已完成**
      → Supabase: Settings → Database → Backups → Create backup

- [ ] **数据完整性检查通过**（执行以下 SQL）:
      ```sql
      -- 检查孤立记录（必须返回 0）
      SELECT 'projects' AS table_name, COUNT(*) AS orphaned_count
      FROM projects
      WHERE created_by IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM users WHERE id = projects.created_by)
      UNION ALL
      SELECT 'ad_accounts', COUNT(*)
      FROM ad_accounts
      WHERE assigned_to IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM users WHERE id = ad_accounts.assigned_to);
      ```
      **预期结果**: 所有行的 `orphaned_count` = 0

- [ ] **执行环境确认**
      - [ ] 生产环境在低峰期执行（建议 02:00-05:00）
      - [ ] 开发/测试环境可随时执行

- [ ] **数据库连接正常**（执行以下命令）:
      ```bash
      psql "$DATABASE_URL" -c "SELECT version();"
      ```

- [ ] **相关文件已准备**:
      - [ ] `backend/migrations/002_add_user_foreign_keys.sql` 已存在
      - [ ] `backend/alembic/versions/20251119_add_user_scope_foreign_keys.py` 已存在（如使用 Alembic）

---

## 🐛 故障排查

### 问题 1: 数据完整性检查失败

**症状**:
```
ERROR:  insert or update on table "projects" violates foreign key constraint...
```

**原因**: 存在孤立记录（created_by/assigned_to 指向不存在的用户）

**解决方案**:
```sql
-- 方案 A: 将孤立值设为 NULL（推荐）
UPDATE projects
SET created_by = NULL
WHERE created_by IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM users WHERE id = projects.created_by);

UPDATE ad_accounts
SET assigned_to = NULL
WHERE assigned_to IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM users WHERE id = ad_accounts.assigned_to);

-- 重新执行迁移
```

---

### 问题 2: 外键约束已存在

**症状**:
```
ERROR:  constraint "fk_projects_created_by_users" for relation "projects" already exists
```

**原因**: 约束已被手动创建或迁移重复执行

**解决方案**: 迁移脚本已包含幂等性检查，理论上不会出现。如仍然出现：
```sql
-- 手动删除旧约束后重新执行
ALTER TABLE projects DROP CONSTRAINT IF EXISTS fk_projects_created_by_users;
ALTER TABLE ad_accounts DROP CONSTRAINT IF EXISTS fk_ad_accounts_assigned_to_users;
```

---

### 问题 3: 索引创建失败

**症状**:
```
ERROR:  relation "idx_projects_created_by" already exists
```

**原因**: 索引已存在

**解决方案**: 迁移脚本已包含检查逻辑，会自动跳过。如手动执行：
```sql
-- 删除后重新创建
DROP INDEX IF EXISTS idx_projects_created_by;
DROP INDEX IF EXISTS idx_ad_accounts_assigned_to;
```

---

## 📞 技术支持

### 联系方式

- **紧急故障**: 联系 DBA 团队或系统架构师
- **迁移失败**: 提供完整错误日志和执行环境信息
- **性能问题**: 提供 `EXPLAIN ANALYZE` 输出和查询语句

### 相关文档

| 文档 | 路径 | 说明 |
|------|------|------|
| **详细迁移指南** | `docs/migrations/002_MIGRATION_GUIDE.md` | 完整的迁移说明、验证步骤、常见问题 |
| **SQL 迁移脚本** | `backend/migrations/002_add_user_foreign_keys.sql` | 纯 SQL 迁移脚本 |
| **Alembic 迁移** | `backend/alembic/versions/20251119_add_user_scope_foreign_keys.py` | Alembic 版本管理脚本 |
| **数据库规范** | `docs/core/DATA_SCHEMA.md` | 数据库结构 SoT |
| **ORM 模型** | `backend/models/base.py` | UserScopeMixin, AssignableMixin 定义 |

---

## 📝 变更记录

| 日期 | 版本 | 变更内容 | 作者 |
|------|------|---------|------|
| 2025-11-19 | v1.0 | 初始版本 | 系统架构团队 |
| 2025-11-19 | v1.1 | 优化执行步骤、添加环境变量说明、完善验证步骤 | 系统架构团队 |

---

✨ **执行建议**: 首次执行建议在开发环境完整测试验证流程，确认无误后再在生产环境执行。
