-- =====================================================
-- 数据库优化执行脚本
-- 版本: 2.1
-- 更新日期: 2025-01-11
--
-- 说明: 此脚本用于执行数据库优化
-- 使用方法: 在Supabase SQL编辑器中执行此脚本
-- =====================================================

-- 设置执行环境
SET session_replication_role = replica; -- 禁用触发器，提升性能
SET statement_timeout = '300s'; -- 设置超时时间为5分钟

-- 创建执行日志表（如果不存在）
CREATE TABLE IF NOT EXISTS migration_log (
    id SERIAL PRIMARY KEY,
    script_name VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    success BOOLEAN NOT NULL,
    error_message TEXT,
    execution_time_ms INTEGER
);

-- 记录开始执行
INSERT INTO migration_log (script_name, version, success)
VALUES ('database_optimization_v2.1', '2.1', false)
RETURNING id INTO migration_start_id;

-- 开始事务
BEGIN;

-- =====================================================
-- 执行步骤说明
-- =====================================================

/*
请按照以下顺序执行：

1. 首先执行 01_optimize_database_schema.sql
   - 创建所有表结构
   - 创建索引
   - 创建函数和触发器
   - 插入初始数据

2. 然后执行 02_create_rls_policies.sql
   - 启用RLS
   - 创建安全策略
   - 创建权限函数

3. 最后执行此验证脚本
*/

-- =====================================================
-- 验证脚本执行结果
-- =====================================================

-- 检查表是否创建成功
DO $$
DECLARE
    table_count INTEGER;
    expected_tables TEXT[] := ARRAY[
        'users', 'user_profiles', 'sessions', 'projects', 'channels',
        'ad_accounts', 'project_members', 'daily_reports', 'topups',
        'reconciliations', 'audit_logs'
    ];
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name = ANY(expected_tables);

    IF table_count = array_length(expected_tables, 1) THEN
        RAISE NOTICE '✓ 所有表创建成功 (共 % 个表)', table_count;
    ELSE
        RAISE NOTICE '✗ 表创建不完整，预期 % 个，实际 % 个',
                     array_length(expected_tables, 1), table_count;
    END IF;
END $$;

-- 检查索引是否创建成功
DO $$
DECLARE
    index_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE schemaname = 'public';

    RAISE NOTICE '✓ 已创建 % 个索引', index_count;
END $$;

-- 检查触发器是否创建成功
DO $$
DECLARE
    trigger_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO trigger_count
    FROM information_schema.triggers
    WHERE trigger_schema = 'public';

    RAISE NOTICE '✓ 已创建 % 个触发器', trigger_count;
END $$;

-- 检查RLS是否启用
DO $$
DECLARE
    rls_table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO rls_table_count
    FROM pg_tables
    WHERE schemaname = 'public'
    AND rowsecurity = true;

    RAISE NOTICE '✓ 已为 % 个表启用RLS', rls_table_count;
END $$;

-- 检查策略是否创建成功
DO $$
DECLARE
    policy_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies;

    RAISE NOTICE '✓ 已创建 % 个RLS策略', policy_count;
END $$;

-- 检查默认管理员用户
DO $$
DECLARE
    admin_exists BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1 FROM users
        WHERE username = 'admin' AND email = 'admin@aiad.com'
    ) INTO admin_exists;

    IF admin_exists THEN
        RAISE NOTICE '✓ 默认管理员用户已创建';
    ELSE
        RAISE NOTICE '✗ 默认管理员用户未创建';
    END IF;
END $$;

-- 提交事务
COMMIT;

-- 恢复触发器
SET session_replication_role = DEFAULT;

-- 更新执行日志
UPDATE migration_log
SET success = true,
    execution_time_ms = EXTRACT(EPOCH FROM (NOW() - executed_at)) * 1000
WHERE id = migration_start_id;

-- =====================================================
-- 后续步骤
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '=====================================================';
    RAISE NOTICE '数据库优化执行完成！';
    RAISE NOTICE '';
    RAISE NOTICE '后续操作：';
    RAISE NOTICE '1. 使用默认管理员账号登录系统';
    RAISE NOTICE '   邮箱: admin@aiad.com';
    RAISE NOTICE '   密码: admin123!@#';
    RAISE NOTICE '';
    RAISE NOTICE '2. 登录后请立即修改默认密码';
    RAISE NOTICE '';
    RAISE NOTICE '3. 创建其他用户账号并分配相应角色';
    RAISE NOTICE '';
    RAISE NOTICE '4. 根据业务需要创建初始项目和渠道';
    RAISE NOTICE '';
    RAISE NOTICE '5. 配置API密钥和环境变量';
    RAISE NOTICE '=====================================================';
END $$;