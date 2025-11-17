-- =====================================================
-- Supabase User Data Migration
-- Version: 1.0
-- Date: 2025-11-16
-- Description: 将现有 users 表数据迁移到 user_profiles
-- =====================================================

-- =====================================================
-- 重要提示
-- =====================================================
-- 此脚本假设：
-- 1. 现有 users 表使用 UUID 主键
-- 2. 所有现有用户都已在 Supabase Auth (auth.users) 中创建
-- 3. 如果还未在 auth.users 中创建，需要先手动导入或通过 API 批量创建

-- =====================================================
-- 1. 数据迁移前检查
-- =====================================================

-- 检查现有 users 表是否存在
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'users'
    ) THEN
        RAISE NOTICE 'users 表不存在，跳过数据迁移';
    END IF;
END
$$;

-- =====================================================
-- 2. 迁移现有用户数据到 user_profiles
-- =====================================================

-- 方案 A：如果现有 users 表的 ID 已经与 auth.users.id 匹配
-- 直接迁移数据
INSERT INTO public.user_profiles (
    id,
    username,
    full_name,
    phone,
    avatar_url,
    role,
    department,
    position,
    account_manager_id,
    is_active,
    is_verified,
    last_login_at,
    last_login_ip,
    preferences,
    timezone,
    language,
    notification_settings,
    profile_metadata,
    created_at,
    updated_at,
    created_by,
    updated_by
)
SELECT
    u.id,
    u.username,
    u.name,  -- 将 name 映射到 full_name
    NULL,    -- phone (现有 users 表可能没有此字段)
    NULL,    -- avatar_url
    COALESCE(u.role, 'media_buyer'),
    NULL,    -- department
    NULL,    -- position
    NULL,    -- account_manager_id
    COALESCE(u.is_active, true),
    false,   -- is_verified (默认未验证)
    NULL,    -- last_login_at
    NULL,    -- last_login_ip
    '{}'::jsonb,  -- preferences
    'UTC',   -- timezone
    'zh-CN', -- language
    '{}'::jsonb,  -- notification_settings
    '{}'::jsonb,  -- profile_metadata
    COALESCE(u.created_at, NOW()),
    COALESCE(u.updated_at, NOW()),
    NULL,    -- created_by
    NULL     -- updated_by
FROM public.users u
WHERE EXISTS (
    SELECT 1 FROM auth.users au WHERE au.id = u.id
)
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- 3. 更新业务表的外键引用
-- =====================================================

-- 注意：由于 user_profiles.id 与 users.id 相同，
-- 现有外键引用无需修改，可以无缝切换

-- 但如果需要明确引用 user_profiles，可以添加外键约束：

-- 3.1 projects 表
ALTER TABLE public.projects
    DROP CONSTRAINT IF EXISTS fk_projects_account_manager,
    ADD CONSTRAINT fk_projects_account_manager
        FOREIGN KEY (account_manager_id)
        REFERENCES public.user_profiles(id)
        ON DELETE SET NULL;

ALTER TABLE public.projects
    DROP CONSTRAINT IF EXISTS fk_projects_created_by,
    ADD CONSTRAINT fk_projects_created_by
        FOREIGN KEY (created_by)
        REFERENCES public.user_profiles(id)
        ON DELETE SET NULL;

ALTER TABLE public.projects
    DROP CONSTRAINT IF EXISTS fk_projects_updated_by,
    ADD CONSTRAINT fk_projects_updated_by
        FOREIGN KEY (updated_by)
        REFERENCES public.user_profiles(id)
        ON DELETE SET NULL;

-- 3.2 ad_accounts 表
ALTER TABLE public.ad_accounts
    DROP CONSTRAINT IF EXISTS fk_ad_accounts_created_by,
    ADD CONSTRAINT fk_ad_accounts_created_by
        FOREIGN KEY (created_by)
        REFERENCES public.user_profiles(id)
        ON DELETE SET NULL;

ALTER TABLE public.ad_accounts
    DROP CONSTRAINT IF EXISTS fk_ad_accounts_updated_by,
    ADD CONSTRAINT fk_ad_accounts_updated_by
        FOREIGN KEY (updated_by)
        REFERENCES public.user_profiles(id)
        ON DELETE SET NULL;

ALTER TABLE public.ad_accounts
    DROP CONSTRAINT IF EXISTS fk_ad_accounts_current_operator,
    ADD CONSTRAINT fk_ad_accounts_current_operator
        FOREIGN KEY (current_operator_id)
        REFERENCES public.user_profiles(id)
        ON DELETE SET NULL;

-- 3.3 topup_requests 表
ALTER TABLE public.topup_requests
    DROP CONSTRAINT IF EXISTS fk_topup_requests_created_by,
    ADD CONSTRAINT fk_topup_requests_created_by
        FOREIGN KEY (created_by)
        REFERENCES public.user_profiles(id)
        ON DELETE SET NULL;

ALTER TABLE public.topup_requests
    DROP CONSTRAINT IF EXISTS fk_topup_requests_data_reviewed_by,
    ADD CONSTRAINT fk_topup_requests_data_reviewed_by
        FOREIGN KEY (data_reviewed_by)
        REFERENCES public.user_profiles(id)
        ON DELETE SET NULL;

ALTER TABLE public.topup_requests
    DROP CONSTRAINT IF EXISTS fk_topup_requests_finance_approved_by,
    ADD CONSTRAINT fk_topup_requests_finance_approved_by
        FOREIGN KEY (finance_approved_by)
        REFERENCES public.user_profiles(id)
        ON DELETE SET NULL;

-- 3.4 daily_reports 表
ALTER TABLE public.daily_reports
    DROP CONSTRAINT IF EXISTS fk_daily_reports_created_by,
    ADD CONSTRAINT fk_daily_reports_created_by
        FOREIGN KEY (created_by)
        REFERENCES public.user_profiles(id)
        ON DELETE SET NULL;

ALTER TABLE public.daily_reports
    DROP CONSTRAINT IF EXISTS fk_daily_reports_reviewed_by,
    ADD CONSTRAINT fk_daily_reports_reviewed_by
        FOREIGN KEY (reviewed_by)
        REFERENCES public.user_profiles(id)
        ON DELETE SET NULL;

-- 3.5 reconciliation_batches 表
ALTER TABLE public.reconciliation_batches
    DROP CONSTRAINT IF EXISTS fk_reconciliation_batches_created_by,
    ADD CONSTRAINT fk_reconciliation_batches_created_by
        FOREIGN KEY (created_by)
        REFERENCES public.user_profiles(id)
        ON DELETE SET NULL;

-- 3.6 project_members 表
ALTER TABLE public.project_members
    DROP CONSTRAINT IF EXISTS fk_project_members_user_id,
    ADD CONSTRAINT fk_project_members_user_id
        FOREIGN KEY (user_id)
        REFERENCES public.user_profiles(id)
        ON DELETE CASCADE;

-- =====================================================
-- 4. 创建视图：兼容旧代码
-- =====================================================

-- 创建视图以兼容现有查询 users 表的代码
CREATE OR REPLACE VIEW public.users AS
SELECT
    id,
    email,
    name,
    role,
    is_active,
    created_at,
    updated_at
FROM public.user_profiles;

-- 授权
GRANT SELECT ON public.users TO authenticated;

-- =====================================================
-- 5. 数据迁移验证
-- =====================================================

-- 验证迁移结果
DO $$
DECLARE
    old_count INTEGER;
    new_count INTEGER;
BEGIN
    -- 统计原 users 表记录数
    SELECT COUNT(*) INTO old_count FROM public.users;

    -- 统计 user_profiles 表记录数
    SELECT COUNT(*) INTO new_count FROM public.user_profiles;

    RAISE NOTICE '原 users 表记录数: %', old_count;
    RAISE NOTICE 'user_profiles 表记录数: %', new_count;

    IF new_count < old_count THEN
        RAISE WARNING '迁移后记录数减少，请检查 auth.users 中是否包含所有用户';
    END IF;
END
$$;

-- =====================================================
-- 6. 清理说明
-- =====================================================

-- 注意：不建议立即删除原 users 表
-- 建议保留一段时间（如 1 个月）作为备份
-- 确认系统稳定后，可以执行：
-- DROP TABLE IF EXISTS public.users_backup;
-- ALTER TABLE public.users RENAME TO users_backup;

COMMENT ON VIEW public.users IS '兼容视图：映射到 user_profiles 表，用于平滑迁移';
