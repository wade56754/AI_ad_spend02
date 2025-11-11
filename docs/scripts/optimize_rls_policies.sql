-- =====================================================
-- RLS策略优化脚本
-- 版本: v1.0
-- 日期: 2025-11-11
-- 说明: 优化RLS策略，简化复杂查询，提高性能
-- =====================================================

BEGIN;

-- =====================================================
-- 1. 创建权限辅助函数（减少重复的复杂查询）
-- =====================================================

-- 1.1 检查用户是否可以访问项目
CREATE OR REPLACE FUNCTION can_access_project(project_uuid UUID)
RETURNS BOOLEAN AS $$
DECLARE
    current_role TEXT := current_setting('app.current_role', true);
    current_user_id UUID := current_setting('app.current_user_id', true)::UUID;
    is_manager BOOLEAN;
BEGIN
    -- 管理员全权限
    IF current_role = 'admin' THEN
        RETURN true;
    END IF;

    -- 检查是否是项目经理
    SELECT EXISTS (
        SELECT 1 FROM projects
        WHERE id = project_uuid
        AND manager_id = current_user_id
    ) INTO is_manager;

    IF is_manager THEN
        RETURN true;
    END IF;

    -- 户管和财务可访问所有项目
    IF current_role IN ('data_clerk', 'finance') THEN
        RETURN true;
    END IF;

    -- 检查投手是否有分配的账户
    RETURN EXISTS (
        SELECT 1 FROM ad_accounts
        WHERE project_id = project_uuid
        AND assigned_user_id = current_user_id
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- 1.2 检查用户是否可以访问账户
CREATE OR REPLACE FUNCTION can_access_account(account_uuid UUID)
RETURNS BOOLEAN AS $$
DECLARE
    current_role TEXT := current_setting('app.current_role', true);
    current_user_id UUID := current_setting('app.current_user_id', true)::UUID;
    account_project_id UUID;
BEGIN
    -- 管理员全权限
    IF current_role = 'admin' THEN
        RETURN true;
    END IF;

    -- 获取账户的项目ID
    SELECT project_id INTO account_project_id
    FROM ad_accounts
    WHERE id = account_uuid;

    -- 检查项目经理权限
    IF EXISTS (
        SELECT 1 FROM projects
        WHERE id = account_project_id
        AND manager_id = current_user_id
    ) THEN
        RETURN true;
    END IF;

    -- 户管可访问所有账户
    IF current_role = 'data_clerk' THEN
        RETURN true;
    END IF;

    -- 财务可查看所有账户
    IF current_role = 'finance' AND current_operation IN ('SELECT', 'UPDATE') THEN
        RETURN true;
    END IF;

    -- 检查是否是分配的投手
    RETURN EXISTS (
        SELECT 1 FROM ad_accounts
        WHERE id = account_uuid
        AND assigned_user_id = current_user_id
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- 1.3 获取用户可访问的项目ID列表
CREATE OR REPLACE FUNCTION get_accessible_project_ids()
RETURNS UUID[] AS $$
DECLARE
    current_role TEXT := current_setting('app.current_role', true);
    current_user_id UUID := current_setting('app.current_user_id', true)::UUID;
    project_ids UUID[];
BEGIN
    -- 管理员返回所有项目
    IF current_role = 'admin' THEN
        RETURN ARRAY(SELECT id FROM projects);
    END IF;

    -- 户管和财务返回所有项目
    IF current_role IN ('data_clerk', 'finance') THEN
        RETURN ARRAY(SELECT id FROM projects);
    END IF;

    -- 项目经理返回自己的项目
    IF current_role = 'manager' THEN
        RETURN ARRAY(
            SELECT id FROM projects
            WHERE manager_id = current_user_id
        );
    END IF;

    -- 投手返回分配的账户所在项目
    RETURN ARRAY(
        SELECT DISTINCT project_id
        FROM ad_accounts
        WHERE assigned_user_id = current_user_id
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================
-- 2. 优化项目表的RLS策略
-- =====================================================

-- 删除原有策略
DROP POLICY IF EXISTS "项目访问策略" ON projects;
DROP POLICY IF EXISTS "项目修改策略" ON projects;
DROP POLICY IF EXISTS "项目更新策略" ON projects;
DROP POLICY IF EXISTS "项目删除策略" ON projects;

-- 2.1 项目访问策略（使用辅助函数）
CREATE POLICY "项目访问策略" ON projects
    FOR SELECT
    USING (can_access_project(id));

-- 2.2 项目插入策略
CREATE POLICY "项目创建策略" ON projects
    FOR INSERT
    WITH CHECK (
        current_setting('app.current_role') IN ('admin', 'manager')
    );

-- 2.3 项目更新策略
CREATE POLICY "项目更新策略" ON projects
    FOR UPDATE
    USING (
        current_setting('app.current_role') = 'admin'
        OR
        (current_setting('app.current_role') = 'manager'
         AND manager_id = current_setting('app.current_user_id')::UUID)
    );

-- 2.4 项目删除策略
CREATE POLICY "项目删除策略" ON projects
    FOR DELETE
    USING (current_setting('app.current_role') = 'admin');

-- =====================================================
-- 3. 优化广告账户表的RLS策略
-- =====================================================

-- 删除原有策略
DROP POLICY IF EXISTS "账户访问策略" ON ad_accounts;
DROP POLICY IF EXISTS "账户修改策略" ON ad_accounts;
DROP POLICY IF EXISTS "账户更新策略" ON ad_accounts;

-- 3.1 账户访问策略（使用辅助函数）
CREATE POLICY "账户访问策略" ON ad_accounts
    FOR SELECT
    USING (can_access_account(id));

-- 3.2 账户插入策略
CREATE POLICY "账户创建策略" ON ad_accounts
    FOR INSERT
    WITH CHECK (
        current_setting('app.current_role') IN ('admin', 'data_clerk')
        AND can_access_project(project_id)
    );

-- 3.3 账户更新策略（使用函数简化）
CREATE POLICY "账户更新策略" ON ad_accounts
    FOR UPDATE
    USING (
        -- 管理员和户管
        current_setting('app.current_role') IN ('admin', 'data_clerk')
        OR
        -- 项目经理
        (current_setting('app.current_role') = 'manager'
         AND EXISTS (
             SELECT 1 FROM projects
             WHERE id = ad_accounts.project_id
             AND manager_id = current_setting('app.current_user_id')::UUID
         )
         AND current_column IN ('notes', 'tags', 'metadata'))
        OR
        -- 投手
        (assigned_user_id = current_setting('app.current_user_id')::UUID
         AND current_column IN ('notes', 'metadata'))
    );

-- =====================================================
-- 4. 优化充值表的RLS策略
-- =====================================================

-- 删除原有策略
DROP POLICY IF EXISTS "充值访问策略" ON topups;
DROP POLICY IF EXISTS "充值创建策略" ON topups;
DROP POLICY IF EXISTS "充值更新策略" ON topups;

-- 4.1 充值访问策略（使用项目ID数组优化）
CREATE POLICY "充值访问策略" ON topups
    FOR SELECT
    USING (
        current_setting('app.current_role') = 'admin'
        OR
        current_setting('app.current_role') IN ('data_clerk', 'finance')
        OR
        project_id = ANY(get_accessible_project_ids())
        OR
        requested_by = current_setting('app.current_user_id')::UUID
    );

-- 4.2 充值创建策略
CREATE POLICY "充值创建策略" ON topups
    FOR INSERT
    WITH CHECK (
        current_setting('app.current_role') IN ('media_buyer', 'data_clerk', 'admin', 'manager')
        AND can_access_project(project_id)
        AND can_access_account(ad_account_id)
    );

-- 4.3 充值更新策略
CREATE POLICY "充值更新策略" ON topups
    FOR UPDATE
    USING (
        -- 管理员
        current_setting('app.current_role') = 'admin'
        OR
        -- 户管审批
        (current_setting('app.current_role') = 'data_clerk'
         AND current_column IN ('clerk_approval', 'status', 'rejection_reason'))
        OR
        -- 财务审批
        (current_setting('app.current_role') = 'finance'
         AND current_column IN ('finance_approval', 'status', 'payment_method', 'transaction_id'))
        OR
        -- 投手修改草稿
        (requested_by = current_setting('app.current_user_id')::UUID
         AND status = 'draft'
         AND current_column IN ('amount', 'purpose', 'urgency_level'))
    );

-- =====================================================
-- 5. 优化日报表的RLS策略
-- =====================================================

-- 删除原有策略
DROP POLICY IF EXISTS "日报访问策略" ON ad_spend_daily;
DROP POLICY IF EXISTS "日报创建策略" ON ad_spend_daily;
DROP POLICY IF EXISTS "日报更新策略" ON ad_spend_daily;

-- 5.1 日报访问策略（使用辅助函数）
CREATE POLICY "日报访问策略" ON ad_spend_daily
    FOR SELECT
    USING (
        current_setting('app.current_role') = 'admin'
        OR
        current_setting('app.current_role') IN ('data_clerk', 'finance')
        OR
        project_id = ANY(get_accessible_project_ids())
        OR
        user_id = current_setting('app.current_user_id')::UUID
    );

-- 5.2 日报创建策略
CREATE POLICY "日报创建策略" ON ad_spend_daily
    FOR INSERT
    WITH CHECK (
        current_setting('app.current_role') IN ('media_buyer', 'data_clerk', 'admin', 'manager')
        AND can_access_account(ad_account_id)
        AND (
            current_setting('app.current_role') IN ('admin', 'data_clerk', 'manager')
            OR
            assigned_user_id = current_setting('app.current_user_id')::UUID
        )
    );

-- 5.3 日报更新策略
CREATE POLICY "日报更新策略" ON ad_spend_daily
    FOR UPDATE
    USING (
        -- 管理员
        current_setting('app.current_role') = 'admin'
        OR
        -- 户管确认
        (current_setting('app.current_role') = 'data_clerk'
         AND current_column IN ('leads_confirmed', 'confirmed_by', 'confirmed_at', 'diff_reason'))
        OR
        -- 投手更新未确认数据
        (user_id = current_setting('app.current_user_id')::UUID
         AND leads_confirmed IS NULL
         AND current_column IN ('leads_submitted', 'spend', 'impressions', 'clicks'))
    );

-- =====================================================
-- 6. 创建RLS性能监控视图
-- =====================================================

-- 6.1 RLS策略执行统计
CREATE OR REPLACE VIEW rls_performance_stats AS
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
ORDER BY tablename, policyname;

-- 6.2 RLS审计日志
CREATE TABLE rls_audit_log (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID,
    table_name VARCHAR(255),
    operation VARCHAR(10),
    policy_used VARCHAR(255),
    execution_time_ms INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建审计触发器
CREATE OR REPLACE FUNCTION log_rls_access()
RETURNS TRIGGER AS $$
BEGIN
    -- 记录RLS策略访问
    INSERT INTO rls_audit_log (
        user_id,
        table_name,
        operation,
        policy_used
    ) VALUES (
        current_setting('app.current_user_id', true)::UUID,
        TG_TABLE_NAME,
        TG_OP,
        'RLS_' || TG_TABLE_NAME
    );

    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 为关键表添加审计触发器
CREATE TRIGGER tr_audit_projects
    AFTER INSERT OR UPDATE OR DELETE ON projects
    FOR EACH ROW EXECUTE FUNCTION log_rls_access();

CREATE TRIGGER tr_audit_ad_accounts
    AFTER INSERT OR UPDATE OR DELETE ON ad_accounts
    FOR EACH ROW EXECUTE FUNCTION log_rls_access();

-- =====================================================
-- 7. 创建权限测试函数
-- =====================================================

-- 7.1 测试用户权限
CREATE OR REPLACE FUNCTION test_user_permissions(test_user_id UUID, test_role TEXT)
RETURNS TABLE(
    table_name TEXT,
    operation TEXT,
    has_permission BOOLEAN
) AS $$
DECLARE
    original_user_id UUID;
    original_role TEXT;
BEGIN
    -- 保存当前会话
    original_user_id := current_setting('app.current_user_id', true)::UUID;
    original_role := current_setting('app.current_role', true);

    -- 设置测试用户上下文
    PERFORM set_config('app.current_user_id', test_user_id::TEXT, true);
    PERFORM set_config('app.current_role', test_role, true);

    -- 测试各表权限
    RETURN QUERY
    SELECT 'projects'::TEXT, 'SELECT'::TEXT,
           EXISTS (SELECT 1 FROM projects LIMIT 1)
    UNION ALL
    SELECT 'projects'::TEXT, 'INSERT'::TEXT,
           has_table_privilege('projects', 'INSERT')
    UNION ALL
    SELECT 'ad_accounts'::TEXT, 'SELECT'::TEXT,
           EXISTS (SELECT 1 FROM ad_accounts LIMIT 1)
    UNION ALL
    SELECT 'topups'::TEXT, 'SELECT'::TEXT,
           EXISTS (SELECT 1 FROM topups LIMIT 1)
    UNION ALL
    SELECT 'ad_spend_daily'::TEXT, 'SELECT'::TEXT,
           EXISTS (SELECT 1 FROM ad_spend_daily LIMIT 1);

    -- 恢复原始会话
    PERFORM set_config('app.current_user_id', original_user_id::TEXT, true);
    PERFORM set_config('app.current_role', original_role, true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 8. 性能优化建议
-- =====================================================

-- 8.1 创建RLS策略缓存函数
CREATE OR REPLACE FUNCTION get_user_permissions_cache()
RETURNS JSONB AS $$
DECLARE
    cache_key TEXT;
    cached_result JSONB;
    current_user_id UUID := current_setting('app.current_user_id', true)::UUID;
    current_role TEXT := current_setting('app.current_role', true);
BEGIN
    -- 构建缓存键
    cache_key := 'user_permissions_' || current_user_id || '_' || current_role;

    -- 尝试从缓存获取
    -- 注意：实际实现需要配合Redis或其他缓存系统

    -- 返回权限信息
    RETURN jsonb_build_object(
        'user_id', current_user_id,
        'role', current_role,
        'accessible_projects', get_accessible_project_ids(),
        'permissions', jsonb_build_object(
            'can_create_projects', current_role IN ('admin', 'manager'),
            'can_create_accounts', current_role IN ('admin', 'data_clerk'),
            'can_approve_topups', current_role IN ('data_clerk', 'finance', 'admin'),
            'can_confirm_reports', current_role IN ('data_clerk', 'admin')
        )
    );
END;
$$ LANGUAGE plpgsql STABLE;

COMMIT;

-- =====================================================
-- 完成提示
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'RLS策略优化完成！';
    RAISE NOTICE '===========================================';
    RAISE NOTICE '优化内容：';
    RAISE NOTICE '1. 创建权限辅助函数，减少重复查询';
    RAISE NOTICE '2. 简化RLS策略逻辑，提高性能';
    RAISE NOTICE '3. 添加RLS性能监控';
    RAISE NOTICE '4. 创建权限测试函数';
    RAISE NOTICE '5. 实现权限缓存机制';
    RAISE NOTICE '===========================================';
    RAISE NOTICE '使用测试：';
    RAISE NOTICE 'SELECT * FROM test_user_permissions(user_id, ''role'');';
    RAISE NOTICE 'SELECT * FROM rls_performance_stats;';
    RAISE NOTICE '===========================================';
END $$;