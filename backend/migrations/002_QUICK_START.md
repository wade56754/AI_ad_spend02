# 🚀 快速开始：添加外键约束迁移

## 📦 已生成的文件

```
backend/
├── migrations/
│   ├── 002_add_user_foreign_keys.sql      # ✅ 纯 SQL 迁移脚本
│   ├── 002_MIGRATION_GUIDE.md             # ✅ 详细迁移指南
│   └── 002_QUICK_START.md                 # ✅ 本文件
└── alembic/
    └── versions/
        └── 20251119_add_user_scope_foreign_keys.py  # ✅ Alembic 迁移脚本
```

---

## ⚡ 一分钟执行指南

### 使用 Supabase Dashboard（最简单）

1. 登录 Supabase Dashboard
2. 进入 **SQL Editor**
3. 复制粘贴 `002_add_user_foreign_keys.sql` 的全部内容
4. 点击 **Run**
5. 检查执行结果 ✅

---

### 使用 psql（命令行）

```bash
# 1. 设置环境变量（从 .env 文件获取）
export DB_HOST="your-supabase-host.supabase.co"
export PGPASSWORD="your-database-password"

# 2. 执行迁移
psql -h $DB_HOST \
     -U postgres \
     -d postgres \
     -f backend/migrations/002_add_user_foreign_keys.sql

# 3. 验证结果
psql -h $DB_HOST -U postgres -d postgres -c "
SELECT constraint_name, table_name
FROM information_schema.table_constraints
WHERE constraint_name IN ('fk_projects_created_by_users', 'fk_ad_accounts_assigned_to_users');
"
```

**预期输出**:
```
            constraint_name            | table_name
---------------------------------------+-------------
 fk_projects_created_by_users          | projects
 fk_ad_accounts_assigned_to_users      | ad_accounts
```

---

### 使用 Alembic（本地开发）

```bash
cd backend

# 1. 检查当前版本
alembic current

# 2. 执行迁移
alembic upgrade head

# 3. 验证结果
alembic current
```

---

## ✅ 快速验证

执行完迁移后，运行以下 SQL 确认成功：

```sql
-- 验证外键约束
SELECT
    tc.table_name,
    tc.constraint_name,
    rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.referential_constraints rc
    ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_name IN (
    'fk_projects_created_by_users',
    'fk_ad_accounts_assigned_to_users'
)
ORDER BY tc.table_name;

-- 验证索引
SELECT tablename, indexname
FROM pg_indexes
WHERE indexname IN (
    'idx_projects_created_by',
    'idx_ad_accounts_assigned_to'
)
ORDER BY tablename;
```

**预期结果**:

外键约束:
```
table_name   | constraint_name                   | delete_rule
-------------+-----------------------------------+-------------
ad_accounts  | fk_ad_accounts_assigned_to_users  | SET NULL
projects     | fk_projects_created_by_users      | SET NULL
```

索引:
```
tablename    | indexname
-------------+--------------------------------
ad_accounts  | idx_ad_accounts_assigned_to
projects     | idx_projects_created_by
```

---

## 🔄 快速回滚（如需要）

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

---

## 📋 迁移内容总结

| 表名 | 字段 | 外键目标 | 删除策略 | 索引 |
|------|------|----------|----------|------|
| `projects` | `created_by` | `users.id` | SET NULL | ✅ |
| `ad_accounts` | `assigned_to` | `users.id` | SET NULL | ✅ |

**影响**:
- ✅ 强制引用完整性（不能插入无效的用户 ID）
- ✅ 查询性能提升（新增索引）
- ✅ 删除用户时自动设置相关字段为 NULL（不会级联删除）

---

## 📖 更多信息

详细说明请参考 `002_MIGRATION_GUIDE.md`

---

## ⚠️ 重要提醒

1. **执行前备份数据库**（Supabase Dashboard > Settings > Database > Backups）
2. **建议在低峰期执行**
3. **迁移是事务性的**，出错会自动回滚
4. **应用程序无需修改**，ORM 模型已经定义了外键

---

✨ Happy Migrating!
