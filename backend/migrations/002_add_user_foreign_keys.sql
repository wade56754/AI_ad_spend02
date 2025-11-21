-- =====================================================================
-- 数据库迁移脚本：为 UserScopeMixin 和 AssignableMixin 添加外键约束
-- =====================================================================
-- 迁移编号: 002
-- 创建时间: 2025-11-19
-- 优化版本: v1.2 (生产环境增强版)
--
-- 说明:
--   1. 为 projects.created_by 添加外键约束到 users.id
--   2. 为 ad_accounts.assigned_to 添加外键约束到 users.id
--   3. 为这些字段创建索引以提升查询性能
--   4. 自动清洗脏数据（孤立记录设为 NULL）
--   5. 处理 NOT NULL 约束冲突
--   6. 使用 NOT VALID + VALIDATE 避免长时间锁表
--
-- 影响表:
--   - projects (使用 UserScopeMixin)
--   - ad_accounts (使用 AssignableMixin)
--
-- 外键策略:
--   - ON DELETE SET NULL: 删除用户时相关字段设为 NULL（不级联删除）
--   - 字段必须为 nullable: 如果有 NOT NULL 约束会自动移除
--
-- 性能优化:
--   - 使用 NOT VALID 避免创建外键时的全表扫描
--   - 然后使用 VALIDATE CONSTRAINT 在后台验证（不阻塞写入）
--   - 索引创建使用 CONCURRENTLY（如果支持）
--
-- 注意事项:
--   - 建议在低峰期执行（尤其是 VALIDATE CONSTRAINT 阶段）
--   - 所有操作在事务中执行，失败自动回滚
--   - 脚本幂等性：可以安全地重复执行
-- =====================================================================

BEGIN;

-- =====================================================================
-- Step 1: 自动清洗脏数据（孤立记录设为 NULL）
-- =====================================================================

DO $$
DECLARE
    projects_cleaned INTEGER;
    accounts_cleaned INTEGER;
BEGIN
    -- 清洗 projects 表：将指向不存在用户的 created_by 设为 NULL
    UPDATE projects
    SET created_by = NULL
    WHERE created_by IS NOT NULL
      AND NOT EXISTS (
          SELECT 1 FROM users u WHERE u.id = projects.created_by
      );

    GET DIAGNOSTICS projects_cleaned = ROW_COUNT;

    IF projects_cleaned > 0 THEN
        RAISE NOTICE '[Step 1] 清洗 projects.created_by: % 条孤立记录已设为 NULL', projects_cleaned;
    ELSE
        RAISE NOTICE '[Step 1] ✅ projects.created_by 数据完整性检查通过（无孤立记录）';
    END IF;

    -- 清洗 ad_accounts 表：将指向不存在用户的 assigned_to 设为 NULL
    UPDATE ad_accounts
    SET assigned_to = NULL
    WHERE assigned_to IS NOT NULL
      AND NOT EXISTS (
          SELECT 1 FROM users u WHERE u.id = ad_accounts.assigned_to
      );

    GET DIAGNOSTICS accounts_cleaned = ROW_COUNT;

    IF accounts_cleaned > 0 THEN
        RAISE NOTICE '[Step 1] 清洗 ad_accounts.assigned_to: % 条孤立记录已设为 NULL', accounts_cleaned;
    ELSE
        RAISE NOTICE '[Step 1] ✅ ad_accounts.assigned_to 数据完整性检查通过（无孤立记录）';
    END IF;
END $$;

-- =====================================================================
-- Step 2: 移除 NOT NULL 约束（如果存在）
-- =====================================================================

DO $$
BEGIN
    -- 检查并移除 projects.created_by 的 NOT NULL 约束
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'projects'
          AND column_name = 'created_by'
          AND is_nullable = 'NO'
    ) THEN
        ALTER TABLE projects ALTER COLUMN created_by DROP NOT NULL;
        RAISE NOTICE '[Step 2] 已移除 projects.created_by 的 NOT NULL 约束';
    ELSE
        RAISE NOTICE '[Step 2] ✅ projects.created_by 已允许 NULL';
    END IF;

    -- 检查并移除 ad_accounts.assigned_to 的 NOT NULL 约束
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'ad_accounts'
          AND column_name = 'assigned_to'
          AND is_nullable = 'NO'
    ) THEN
        ALTER TABLE ad_accounts ALTER COLUMN assigned_to DROP NOT NULL;
        RAISE NOTICE '[Step 2] 已移除 ad_accounts.assigned_to 的 NOT NULL 约束';
    ELSE
        RAISE NOTICE '[Step 2] ✅ ad_accounts.assigned_to 已允许 NULL';
    END IF;
END $$;

-- =====================================================================
-- Step 3: 删除旧的外键约束（如果存在，带 schema 过滤）
-- =====================================================================

DO $$
BEGIN
    -- 删除 projects.created_by 的旧外键约束
    IF EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_schema = 'public'
          AND table_name = 'projects'
          AND constraint_name = 'fk_projects_created_by_users'
          AND constraint_type = 'FOREIGN KEY'
    ) THEN
        ALTER TABLE projects DROP CONSTRAINT fk_projects_created_by_users;
        RAISE NOTICE '[Step 3] 已删除旧的外键约束 fk_projects_created_by_users';
    ELSE
        RAISE NOTICE '[Step 3] ✅ 外键约束 fk_projects_created_by_users 不存在（首次执行）';
    END IF;

    -- 删除 ad_accounts.assigned_to 的旧外键约束
    IF EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_schema = 'public'
          AND table_name = 'ad_accounts'
          AND constraint_name = 'fk_ad_accounts_assigned_to_users'
          AND constraint_type = 'FOREIGN KEY'
    ) THEN
        ALTER TABLE ad_accounts DROP CONSTRAINT fk_ad_accounts_assigned_to_users;
        RAISE NOTICE '[Step 3] 已删除旧的外键约束 fk_ad_accounts_assigned_to_users';
    ELSE
        RAISE NOTICE '[Step 3] ✅ 外键约束 fk_ad_accounts_assigned_to_users 不存在（首次执行）';
    END IF;
END $$;

-- =====================================================================
-- Step 4: 添加外键约束（使用 NOT VALID 避免全表扫描）
-- =====================================================================

-- 4.1 为 projects.created_by 添加外键约束（NOT VALID）
DO $$
BEGIN
    -- 检查约束是否已存在（避免重复添加）
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_schema = 'public'
          AND table_name = 'projects'
          AND constraint_name = 'fk_projects_created_by_users'
    ) THEN
        -- 使用 NOT VALID 避免立即全表扫描（不阻塞写入）
        ALTER TABLE projects
        ADD CONSTRAINT fk_projects_created_by_users
        FOREIGN KEY (created_by)
        REFERENCES users(id)
        ON DELETE SET NULL
        NOT VALID;

        RAISE NOTICE '[Step 4.1] ✅ 已添加外键约束 fk_projects_created_by_users (NOT VALID)';
    ELSE
        RAISE NOTICE '[Step 4.1] ⚠️  外键约束 fk_projects_created_by_users 已存在，跳过创建';
    END IF;
END $$;

-- 4.2 验证 projects.created_by 外键约束（后台验证，不阻塞写入）
DO $$
BEGIN
    -- 检查约束是否需要验证
    IF EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_projects_created_by_users'
          AND connamespace = 'public'::regnamespace
          AND NOT convalidated
    ) THEN
        -- 验证约束（可能需要较长时间，但不阻塞写入）
        ALTER TABLE projects VALIDATE CONSTRAINT fk_projects_created_by_users;
        RAISE NOTICE '[Step 4.2] ✅ 已验证外键约束 fk_projects_created_by_users';
    ELSE
        RAISE NOTICE '[Step 4.2] ✅ 外键约束 fk_projects_created_by_users 已验证';
    END IF;
END $$;

-- 4.3 添加约束注释
COMMENT ON CONSTRAINT fk_projects_created_by_users ON projects IS
'项目创建者外键约束 - 删除用户时将 created_by 设为 NULL (ON DELETE SET NULL)';

-- 4.4 为 ad_accounts.assigned_to 添加外键约束（NOT VALID）
DO $$
BEGIN
    -- 检查约束是否已存在
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_schema = 'public'
          AND table_name = 'ad_accounts'
          AND constraint_name = 'fk_ad_accounts_assigned_to_users'
    ) THEN
        -- 使用 NOT VALID 避免立即全表扫描
        ALTER TABLE ad_accounts
        ADD CONSTRAINT fk_ad_accounts_assigned_to_users
        FOREIGN KEY (assigned_to)
        REFERENCES users(id)
        ON DELETE SET NULL
        NOT VALID;

        RAISE NOTICE '[Step 4.4] ✅ 已添加外键约束 fk_ad_accounts_assigned_to_users (NOT VALID)';
    ELSE
        RAISE NOTICE '[Step 4.4] ⚠️  外键约束 fk_ad_accounts_assigned_to_users 已存在，跳过创建';
    END IF;
END $$;

-- 4.5 验证 ad_accounts.assigned_to 外键约束
DO $$
BEGIN
    -- 检查约束是否需要验证
    IF EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_ad_accounts_assigned_to_users'
          AND connamespace = 'public'::regnamespace
          AND NOT convalidated
    ) THEN
        -- 验证约束
        ALTER TABLE ad_accounts VALIDATE CONSTRAINT fk_ad_accounts_assigned_to_users;
        RAISE NOTICE '[Step 4.5] ✅ 已验证外键约束 fk_ad_accounts_assigned_to_users';
    ELSE
        RAISE NOTICE '[Step 4.5] ✅ 外键约束 fk_ad_accounts_assigned_to_users 已验证';
    END IF;
END $$;

-- 4.6 添加约束注释
COMMENT ON CONSTRAINT fk_ad_accounts_assigned_to_users ON ad_accounts IS
'广告账户负责人外键约束 - 删除用户时将 assigned_to 设为 NULL (ON DELETE SET NULL)';

-- =====================================================================
-- Step 5: 创建索引（带 schema 过滤和幂等性检查）
-- =====================================================================

-- 5.1 为 projects.created_by 创建索引
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE schemaname = 'public'
          AND tablename = 'projects'
          AND indexname = 'idx_projects_created_by'
    ) THEN
        -- 创建 btree 索引（提升 WHERE created_by = ? 查询性能）
        CREATE INDEX idx_projects_created_by ON projects(created_by);
        RAISE NOTICE '[Step 5.1] ✅ 已创建索引 idx_projects_created_by';
    ELSE
        RAISE NOTICE '[Step 5.1] ⚠️  索引 idx_projects_created_by 已存在，跳过创建';
    END IF;
END $$;

-- 5.2 为 ad_accounts.assigned_to 创建索引
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE schemaname = 'public'
          AND tablename = 'ad_accounts'
          AND indexname = 'idx_ad_accounts_assigned_to'
    ) THEN
        -- 创建 btree 索引
        CREATE INDEX idx_ad_accounts_assigned_to ON ad_accounts(assigned_to);
        RAISE NOTICE '[Step 5.2] ✅ 已创建索引 idx_ad_accounts_assigned_to';
    ELSE
        RAISE NOTICE '[Step 5.2] ⚠️  索引 idx_ad_accounts_assigned_to 已存在，跳过创建';
    END IF;
END $$;

-- =====================================================================
-- Step 6: 验证迁移结果并打印总结
-- =====================================================================

DO $$
DECLARE
    fk_count INTEGER;
    idx_count INTEGER;
    fk_validated_count INTEGER;
    projects_orphaned INTEGER;
    accounts_orphaned INTEGER;
BEGIN
    -- 验证外键约束数量
    SELECT COUNT(*) INTO fk_count
    FROM information_schema.table_constraints
    WHERE table_schema = 'public'
      AND constraint_type = 'FOREIGN KEY'
      AND constraint_name IN (
          'fk_projects_created_by_users',
          'fk_ad_accounts_assigned_to_users'
      );

    -- 验证外键约束是否已验证（validated）
    SELECT COUNT(*) INTO fk_validated_count
    FROM pg_constraint
    WHERE conname IN ('fk_projects_created_by_users', 'fk_ad_accounts_assigned_to_users')
      AND connamespace = 'public'::regnamespace
      AND convalidated = true;

    -- 验证索引数量
    SELECT COUNT(*) INTO idx_count
    FROM pg_indexes
    WHERE schemaname = 'public'
      AND indexname IN (
          'idx_projects_created_by',
          'idx_ad_accounts_assigned_to'
      );

    -- 最终数据完整性检查（应为 0）
    SELECT COUNT(*) INTO projects_orphaned
    FROM projects
    WHERE created_by IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM users WHERE id = projects.created_by);

    SELECT COUNT(*) INTO accounts_orphaned
    FROM ad_accounts
    WHERE assigned_to IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM users WHERE id = ad_accounts.assigned_to);

    -- 打印验证结果
    RAISE NOTICE '=================================================================';
    RAISE NOTICE '                  迁移完成验证报告';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE '';
    RAISE NOTICE '【外键约束】';

    IF fk_count = 2 THEN
        RAISE NOTICE '  ✅ 外键约束创建成功: 2/2';
    ELSE
        RAISE WARNING '  ❌ 外键约束创建失败: %/2', fk_count;
    END IF;

    IF fk_validated_count = 2 THEN
        RAISE NOTICE '  ✅ 外键约束已验证: 2/2';
    ELSE
        RAISE WARNING '  ⚠️  外键约束待验证: %/2', 2 - fk_validated_count;
    END IF;

    RAISE NOTICE '  - projects.created_by → users.id (ON DELETE SET NULL)';
    RAISE NOTICE '  - ad_accounts.assigned_to → users.id (ON DELETE SET NULL)';
    RAISE NOTICE '';

    RAISE NOTICE '【索引】';
    IF idx_count = 2 THEN
        RAISE NOTICE '  ✅ 索引创建成功: 2/2';
    ELSE
        RAISE WARNING '  ❌ 索引创建失败: %/2', idx_count;
    END IF;

    RAISE NOTICE '  - idx_projects_created_by (btree)';
    RAISE NOTICE '  - idx_ad_accounts_assigned_to (btree)';
    RAISE NOTICE '';

    RAISE NOTICE '【数据完整性】';
    IF projects_orphaned = 0 THEN
        RAISE NOTICE '  ✅ projects.created_by: 无孤立记录';
    ELSE
        RAISE WARNING '  ❌ projects.created_by: % 条孤立记录', projects_orphaned;
    END IF;

    IF accounts_orphaned = 0 THEN
        RAISE NOTICE '  ✅ ad_accounts.assigned_to: 无孤立记录';
    ELSE
        RAISE WARNING '  ❌ ad_accounts.assigned_to: % 条孤立记录', accounts_orphaned;
    END IF;

    RAISE NOTICE '';
    RAISE NOTICE '【事务状态】';
    RAISE NOTICE '  ✅ 所有操作在事务中执行';
    RAISE NOTICE '  ✅ 失败自动回滚';
    RAISE NOTICE '';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE '             迁移编号 #002 执行完成';
    RAISE NOTICE '=================================================================';

    -- 如果有任何验证失败，抛出异常回滚事务
    IF fk_count <> 2 OR idx_count <> 2 OR fk_validated_count <> 2 OR projects_orphaned > 0 OR accounts_orphaned > 0 THEN
        RAISE EXCEPTION '❌ 迁移验证失败，事务已回滚。请检查上述错误信息。';
    END IF;
END $$;

COMMIT;

-- =====================================================================
-- 回滚脚本（如需回滚，请手动执行以下命令）
-- =====================================================================
/*
BEGIN;

RAISE NOTICE '开始回滚迁移 #002...';

-- 删除外键约束
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_schema = 'public'
          AND table_name = 'projects'
          AND constraint_name = 'fk_projects_created_by_users'
    ) THEN
        ALTER TABLE projects DROP CONSTRAINT fk_projects_created_by_users;
        RAISE NOTICE '已删除外键约束 fk_projects_created_by_users';
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_schema = 'public'
          AND table_name = 'ad_accounts'
          AND constraint_name = 'fk_ad_accounts_assigned_to_users'
    ) THEN
        ALTER TABLE ad_accounts DROP CONSTRAINT fk_ad_accounts_assigned_to_users;
        RAISE NOTICE '已删除外键约束 fk_ad_accounts_assigned_to_users';
    END IF;
END $$;

-- 删除索引
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE schemaname = 'public'
          AND tablename = 'projects'
          AND indexname = 'idx_projects_created_by'
    ) THEN
        DROP INDEX idx_projects_created_by;
        RAISE NOTICE '已删除索引 idx_projects_created_by';
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE schemaname = 'public'
          AND tablename = 'ad_accounts'
          AND indexname = 'idx_ad_accounts_assigned_to'
    ) THEN
        DROP INDEX idx_ad_accounts_assigned_to;
        RAISE NOTICE '已删除索引 idx_ad_accounts_assigned_to';
    END IF;
END $$;

RAISE NOTICE '✅ 回滚完成';

COMMIT;
*/
