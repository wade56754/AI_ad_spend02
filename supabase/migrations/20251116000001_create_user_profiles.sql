-- =====================================================
-- Supabase User Profiles Migration
-- Version: 1.0
-- Date: 2025-11-16
-- Description: 创建 user_profiles 表，与 Supabase Auth 集成
-- =====================================================

-- =====================================================
-- 1. 创建 user_profiles 表
-- =====================================================
-- 注意：此表结构与 backend/models/user_profile.py 保持一致
CREATE TABLE IF NOT EXISTS public.user_profiles (
    -- 主键：直接使用 auth.users.id（无需单独的 user_id）
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,

    -- 基础信息
    username VARCHAR(50) UNIQUE,
    full_name VARCHAR(100),
    phone VARCHAR(20),
    avatar_url VARCHAR(500),

    -- 角色权限（5个角色）
    role VARCHAR(20) NOT NULL DEFAULT 'media_buyer' CHECK (
        role IN ('admin', 'finance', 'data_operator', 'account_manager', 'media_buyer')
    ),

    -- 业务信息
    department VARCHAR(100),
    position VARCHAR(100),

    -- 组织结构
    account_manager_id UUID REFERENCES public.user_profiles(id),

    -- 状态控制
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    last_login_at TIMESTAMPTZ,
    last_login_ip VARCHAR(45),

    -- 偏好设置
    preferences JSONB DEFAULT '{}'::jsonb,
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'zh-CN',

    -- 通知设置
    notification_settings JSONB DEFAULT '{}'::jsonb,

    -- 元数据
    profile_metadata JSONB DEFAULT '{}'::jsonb,

    -- 审计字段
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES public.user_profiles(id),
    updated_by UUID REFERENCES public.user_profiles(id)
);

-- =====================================================
-- 2. 创建索引
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_user_profiles_username ON public.user_profiles(username);
CREATE INDEX IF NOT EXISTS idx_user_profiles_role ON public.user_profiles(role);
CREATE INDEX IF NOT EXISTS idx_user_profiles_is_active ON public.user_profiles(is_active);
CREATE INDEX IF NOT EXISTS idx_user_profiles_account_manager ON public.user_profiles(account_manager_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_created_at ON public.user_profiles(created_at);
CREATE INDEX IF NOT EXISTS idx_user_profiles_last_login ON public.user_profiles(last_login_at);
CREATE INDEX IF NOT EXISTS idx_user_profiles_department ON public.user_profiles(department);
CREATE INDEX IF NOT EXISTS idx_user_profiles_position ON public.user_profiles(position);

-- =====================================================
-- 3. 启用 RLS（Row Level Security）
-- =====================================================
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- 4. 创建 RLS 策略
-- =====================================================

-- 策略 1：用户可以查看自己的 profile
CREATE POLICY "Users can view own profile"
ON public.user_profiles
FOR SELECT
USING (auth.uid() = id);

-- 策略 2：管理员可以查看所有 profiles
CREATE POLICY "Admins can view all profiles"
ON public.user_profiles
FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM public.user_profiles
        WHERE id = auth.uid() AND role = 'admin'
    )
);

-- 策略 3：用户可以更新自己的 profile（除了 role）
CREATE POLICY "Users can update own profile"
ON public.user_profiles
FOR UPDATE
USING (auth.uid() = id)
WITH CHECK (
    auth.uid() = id
    AND role = (SELECT role FROM public.user_profiles WHERE id = auth.uid())
);

-- 策略 4：管理员可以更新所有 profiles
CREATE POLICY "Admins can update all profiles"
ON public.user_profiles
FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM public.user_profiles
        WHERE id = auth.uid() AND role = 'admin'
    )
);

-- 策略 5：管理员可以插入新 profiles
CREATE POLICY "Admins can insert profiles"
ON public.user_profiles
FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.user_profiles
        WHERE id = auth.uid() AND role = 'admin'
    )
);

-- 策略 6：管理员可以删除 profiles
CREATE POLICY "Admins can delete profiles"
ON public.user_profiles
FOR DELETE
USING (
    EXISTS (
        SELECT 1 FROM public.user_profiles
        WHERE id = auth.uid() AND role = 'admin'
    )
);

-- =====================================================
-- 5. 创建触发器：自动更新 updated_at
-- =====================================================
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- =====================================================
-- 6. 创建函数：自动创建 user_profile
-- =====================================================
-- 当 auth.users 创建新用户时，自动在 user_profiles 创建对应记录
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (
        id,
        username,
        full_name,
        role,
        account_manager_id,
        preferences,
        notification_settings,
        profile_metadata
    )
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'username', NULL),
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', NEW.email),
        COALESCE(NEW.raw_user_meta_data->>'role', 'media_buyer'),
        COALESCE((NEW.raw_user_meta_data->>'account_manager_id')::uuid, NULL),
        COALESCE((NEW.raw_user_meta_data->'preferences')::jsonb, '{}'::jsonb),
        COALESCE((NEW.raw_user_meta_data->'notification_settings')::jsonb, '{}'::jsonb),
        COALESCE((NEW.raw_user_meta_data->'profile_metadata')::jsonb, '{}'::jsonb)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 在 auth.users 表上创建触发器
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- =====================================================
-- 7. 授权
-- =====================================================
-- 允许认证用户访问 user_profiles
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_profiles TO authenticated;
GRANT USAGE ON SCHEMA public TO authenticated;

-- =====================================================
-- 8. 注释
-- =====================================================
COMMENT ON TABLE public.user_profiles IS '用户业务信息表，与 Supabase Auth 集成';
COMMENT ON COLUMN public.user_profiles.id IS '主键，直接引用 auth.users.id';
COMMENT ON COLUMN public.user_profiles.username IS '用户名';
COMMENT ON COLUMN public.user_profiles.role IS '用户角色：admin, finance, data_operator, account_manager, media_buyer';
COMMENT ON COLUMN public.user_profiles.is_active IS '账户是否激活';
COMMENT ON COLUMN public.user_profiles.last_login_at IS '最后登录时间';
