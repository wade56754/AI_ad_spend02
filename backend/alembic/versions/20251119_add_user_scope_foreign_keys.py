"""为 UserScopeMixin 和 AssignableMixin 添加外键约束

Revision ID: 20251119_user_fks
Revises:
Create Date: 2025-11-19

Description:
    为使用 UserScopeMixin 和 AssignableMixin 的表添加外键约束和索引。
    这些 Mixin 提供了 created_by 和 assigned_to 字段用于 RLS 权限控制，
    现在添加数据库层面的外键约束以确保引用完整性。

Tables affected:
    - projects: created_by → users.id (UserScopeMixin)
    - ad_accounts: assigned_to → users.id (AssignableMixin)

Changes:
    1. 添加外键约束 (ON DELETE SET NULL)
    2. 创建索引以提升查询性能

Migration Strategy:
    - 先检查现有数据完整性
    - 删除旧的外键约束（如果存在）
    - 添加新的外键约束
    - 创建索引
    - 完全可逆

Data Risk: 低
    - 所有字段都是 nullable
    - ON DELETE SET NULL 不会导致级联删除
    - 只影响引用完整性约束

SoT References:
    - backend/models/base.py: UserScopeMixin, AssignableMixin
    - backend/models/core/project.py: Project 模型
    - backend/models/accounts/ad_account.py: AdAccount 模型
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20251119_user_fks'
down_revision = None  # TODO: 根据实际情况填写前一个 revision
branch_labels = None
depends_on = None


def upgrade():
    """
    升级函数：为 UserScopeMixin 和 AssignableMixin 添加外键约束
    """

    print("[20251119] 开始添加 UserScopeMixin/AssignableMixin 外键约束...")

    # =====================================================================
    # 第一步：检查现有数据完整性
    # =====================================================================

    print("[20251119] 检查 projects.created_by 数据完整性...")
    op.execute("""
        DO $$
        DECLARE
            invalid_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO invalid_count
            FROM projects p
            WHERE p.created_by IS NOT NULL
              AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = p.created_by);

            IF invalid_count > 0 THEN
                RAISE WARNING '发现 % 条 projects 记录的 created_by 指向不存在的用户', invalid_count;
            ELSE
                RAISE NOTICE '✅ projects.created_by 数据完整性检查通过';
            END IF;
        END $$;
    """)

    print("[20251119] 检查 ad_accounts.assigned_to 数据完整性...")
    op.execute("""
        DO $$
        DECLARE
            invalid_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO invalid_count
            FROM ad_accounts a
            WHERE a.assigned_to IS NOT NULL
              AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = a.assigned_to);

            IF invalid_count > 0 THEN
                RAISE WARNING '发现 % 条 ad_accounts 记录的 assigned_to 指向不存在的用户', invalid_count;
            ELSE
                RAISE NOTICE '✅ ad_accounts.assigned_to 数据完整性检查通过';
            END IF;
        END $$;
    """)

    # =====================================================================
    # 第二步：删除旧的外键约束（如果存在）
    # =====================================================================

    print("[20251119] 删除旧的外键约束（如果存在）...")

    # 删除 projects.created_by 的旧外键约束
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'fk_projects_created_by_users'
                AND table_name = 'projects'
            ) THEN
                ALTER TABLE projects DROP CONSTRAINT fk_projects_created_by_users;
                RAISE NOTICE '已删除旧的外键约束 fk_projects_created_by_users';
            END IF;
        END $$;
    """)

    # 删除 ad_accounts.assigned_to 的旧外键约束
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'fk_ad_accounts_assigned_to_users'
                AND table_name = 'ad_accounts'
            ) THEN
                ALTER TABLE ad_accounts DROP CONSTRAINT fk_ad_accounts_assigned_to_users;
                RAISE NOTICE '已删除旧的外键约束 fk_ad_accounts_assigned_to_users';
            END IF;
        END $$;
    """)

    # =====================================================================
    # 第三步：为 projects 表添加外键约束
    # =====================================================================

    print("[20251119] 为 projects.created_by 添加外键约束...")

    # 添加外键约束
    op.create_foreign_key(
        'fk_projects_created_by_users',  # 约束名称
        'projects',                       # 源表
        'users',                          # 目标表
        ['created_by'],                   # 源列
        ['id'],                           # 目标列
        ondelete='SET NULL'               # 删除策略
    )

    # 添加注释
    op.execute("""
        COMMENT ON CONSTRAINT fk_projects_created_by_users ON projects IS
        '项目创建者外键约束 - 删除用户时将 created_by 设为 NULL'
    """)

    # =====================================================================
    # 第四步：为 projects 创建索引
    # =====================================================================

    print("[20251119] 为 projects.created_by 创建索引...")

    # 创建索引（如果不存在）
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'projects'
                AND indexname = 'idx_projects_created_by'
            ) THEN
                CREATE INDEX idx_projects_created_by ON projects(created_by);
                RAISE NOTICE '已创建索引 idx_projects_created_by';
            ELSE
                RAISE NOTICE '索引 idx_projects_created_by 已存在，跳过创建';
            END IF;
        END $$;
    """)

    # =====================================================================
    # 第五步：为 ad_accounts 表添加外键约束
    # =====================================================================

    print("[20251119] 为 ad_accounts.assigned_to 添加外键约束...")

    # 添加外键约束
    op.create_foreign_key(
        'fk_ad_accounts_assigned_to_users',  # 约束名称
        'ad_accounts',                        # 源表
        'users',                              # 目标表
        ['assigned_to'],                      # 源列
        ['id'],                               # 目标列
        ondelete='SET NULL'                   # 删除策略
    )

    # 添加注释
    op.execute("""
        COMMENT ON CONSTRAINT fk_ad_accounts_assigned_to_users ON ad_accounts IS
        '广告账户负责人外键约束 - 删除用户时将 assigned_to 设为 NULL'
    """)

    # =====================================================================
    # 第六步：为 ad_accounts 创建索引
    # =====================================================================

    print("[20251119] 为 ad_accounts.assigned_to 创建索引...")

    # 创建索引（如果不存在）
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'ad_accounts'
                AND indexname = 'idx_ad_accounts_assigned_to'
            ) THEN
                CREATE INDEX idx_ad_accounts_assigned_to ON ad_accounts(assigned_to);
                RAISE NOTICE '已创建索引 idx_ad_accounts_assigned_to';
            ELSE
                RAISE NOTICE '索引 idx_ad_accounts_assigned_to 已存在，跳过创建';
            END IF;
        END $$;
    """)

    # =====================================================================
    # 第七步：验证迁移结果
    # =====================================================================

    print("[20251119] 验证迁移结果...")

    # 验证外键约束
    op.execute("""
        DO $$
        DECLARE
            fk_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO fk_count
            FROM information_schema.table_constraints
            WHERE constraint_name IN ('fk_projects_created_by_users', 'fk_ad_accounts_assigned_to_users')
              AND constraint_type = 'FOREIGN KEY';

            IF fk_count = 2 THEN
                RAISE NOTICE '✅ 所有外键约束创建成功！';
            ELSE
                RAISE WARNING '⚠️  只创建了 % 个外键约束，预期为 2 个', fk_count;
            END IF;
        END $$;
    """)

    # 验证索引
    op.execute("""
        DO $$
        DECLARE
            idx_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO idx_count
            FROM pg_indexes
            WHERE indexname IN ('idx_projects_created_by', 'idx_ad_accounts_assigned_to');

            IF idx_count = 2 THEN
                RAISE NOTICE '✅ 所有索引创建成功！';
            ELSE
                RAISE WARNING '⚠️  只创建了 % 个索引，预期为 2 个', idx_count;
            END IF;
        END $$;
    """)

    print("[20251119] 迁移完成！")
    print("  ✅ projects.created_by → users.id (外键 + 索引)")
    print("  ✅ ad_accounts.assigned_to → users.id (外键 + 索引)")
    print("  ✅ 外键策略: ON DELETE SET NULL")
    print("[20251119] 请执行 Gate #20251119 验证")


def downgrade():
    """
    降级函数：删除外键约束和索引
    """

    print("[20251119 ROLLBACK] 开始回滚外键约束...")

    # =====================================================================
    # 删除索引（逆序）
    # =====================================================================

    print("[20251119 ROLLBACK] 删除索引...")

    op.execute("DROP INDEX IF EXISTS idx_ad_accounts_assigned_to")
    op.execute("DROP INDEX IF EXISTS idx_projects_created_by")

    # =====================================================================
    # 删除外键约束
    # =====================================================================

    print("[20251119 ROLLBACK] 删除外键约束...")

    # 删除 ad_accounts.assigned_to 外键
    op.drop_constraint(
        'fk_ad_accounts_assigned_to_users',
        'ad_accounts',
        type_='foreignkey'
    )

    # 删除 projects.created_by 外键
    op.drop_constraint(
        'fk_projects_created_by_users',
        'projects',
        type_='foreignkey'
    )

    print("[20251119 ROLLBACK] 回滚完成")


# =====================================================================
# Gate #20251119: 验证脚本
# =====================================================================
"""
Gate #20251119: 验证 UserScopeMixin/AssignableMixin 外键约束

执行以下 SQL 验证迁移结果：

-- 1. 验证外键约束是否存在
SELECT
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
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
WHERE tc.constraint_name IN ('fk_projects_created_by_users', 'fk_ad_accounts_assigned_to_users')
ORDER BY tc.table_name;

预期结果：
- projects.created_by → users.id [ON DELETE SET NULL]
- ad_accounts.assigned_to → users.id [ON DELETE SET NULL]

-- 2. 验证索引是否存在
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE indexname IN ('idx_projects_created_by', 'idx_ad_accounts_assigned_to')
ORDER BY tablename;

预期结果：
- idx_projects_created_by: CREATE INDEX ... ON projects USING btree (created_by)
- idx_ad_accounts_assigned_to: CREATE INDEX ... ON ad_accounts USING btree (assigned_to)

-- 3. 验证数据完整性（确认外键约束可以正常工作）
-- 检查是否有孤立记录（理论上不应该有）
SELECT 'projects' AS table_name, COUNT(*) AS orphaned_records
FROM projects p
WHERE p.created_by IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = p.created_by)
UNION ALL
SELECT 'ad_accounts' AS table_name, COUNT(*) AS orphaned_records
FROM ad_accounts a
WHERE a.assigned_to IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = a.assigned_to);

预期结果：所有 orphaned_records 应为 0

-- 4. 测试外键约束是否生效
-- 尝试插入一条指向不存在用户的记录（应该失败）
-- 注意：仅用于测试，测试后需要回滚
BEGIN;

-- 应该失败：插入不存在的 created_by
INSERT INTO projects (project_name, project_code, status, created_by)
VALUES ('Test Project', 'TEST001', 'draft', '00000000-0000-0000-0000-000000000000');

ROLLBACK;

预期结果：外键约束错误
ERROR:  insert or update on table "projects" violates foreign key constraint "fk_projects_created_by_users"
DETAIL:  Key (created_by)=(00000000-0000-0000-0000-000000000000) is not present in table "users".

-- 5. 性能验证：检查索引是否被使用
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM projects WHERE created_by = '某个实际存在的UUID';

预期结果：执行计划中应该显示 "Index Scan using idx_projects_created_by"

EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM ad_accounts WHERE assigned_to = '某个实际存在的UUID';

预期结果：执行计划中应该显示 "Index Scan using idx_ad_accounts_assigned_to"
"""
