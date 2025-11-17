-- =====================================================
-- Supabase User Sessions and Login History Tables
-- Version: 1.0
-- Date: 2025-11-16
-- Description: 创建用户会话和登录历史表
-- =====================================================

-- =====================================================
-- 1. 创建 user_login_history 表
-- =====================================================
CREATE TABLE IF NOT EXISTS public.user_login_history (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 关联用户
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255),  -- 用于记录未注册用户

    -- 登录信息
    login_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    logout_time TIMESTAMPTZ,

    -- 设备信息
    ip_address VARCHAR(45),
    user_agent TEXT,
    device_info JSONB,

    -- 登录类型和状态
    login_type VARCHAR(20) NOT NULL DEFAULT 'password',
    status VARCHAR(20) NOT NULL DEFAULT 'success',
    failure_reason VARCHAR(255),

    -- 位置信息
    country VARCHAR(50),
    city VARCHAR(100)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_login_history_user ON public.user_login_history(user_id);
CREATE INDEX IF NOT EXISTS idx_login_history_time ON public.user_login_history(login_time);
CREATE INDEX IF NOT EXISTS idx_login_history_status ON public.user_login_history(status);
CREATE INDEX IF NOT EXISTS idx_login_history_ip ON public.user_login_history(ip_address);

-- =====================================================
-- 2. 创建 user_sessions 表
-- =====================================================
CREATE TABLE IF NOT EXISTS public.user_sessions (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 关联用户
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- 会话信息
    session_token VARCHAR(500) UNIQUE NOT NULL,
    device_info JSONB,

    -- 状态和时间
    is_active BOOLEAN NOT NULL DEFAULT true,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_sessions_user ON public.user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON public.user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON public.user_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON public.user_sessions(expires_at);

-- =====================================================
-- 3. 启用 RLS
-- =====================================================
ALTER TABLE public.user_login_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_sessions ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- 4. 创建 RLS 策略
-- =====================================================

-- 登录历史策略
CREATE POLICY "Users can view own login history"
ON public.user_login_history
FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Admins can view all login history"
ON public.user_login_history
FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM public.user_profiles
        WHERE id = auth.uid() AND role = 'admin'
    )
);

-- 会话策略
CREATE POLICY "Users can view own sessions"
ON public.user_sessions
FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Admins can view all sessions"
ON public.user_sessions
FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM public.user_profiles
        WHERE id = auth.uid() AND role = 'admin'
    )
);

CREATE POLICY "Users can manage own sessions"
ON public.user_sessions
FOR UPDATE
USING (auth.uid() = user_id);

CREATE POLICY "Admins can manage all sessions"
ON public.user_sessions
FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM public.user_profiles
        WHERE id = auth.uid() AND role = 'admin'
    )
);

-- =====================================================
-- 5. 授权
-- =====================================================
GRANT SELECT, INSERT, UPDATE ON public.user_login_history TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.user_sessions TO authenticated;
GRANT USAGE ON SCHEMA public TO authenticated;

-- =====================================================
-- 6. 注释
-- =====================================================
COMMENT ON TABLE public.user_login_history IS '用户登录历史表';
COMMENT ON COLUMN public.user_login_history.user_id IS '关联的用户ID';
COMMENT ON COLUMN public.user_login_history.login_type IS '登录类型：password, oauth, otp 等';
COMMENT ON COLUMN public.user_login_history.status IS '登录状态：success, failed';

COMMENT ON TABLE public.user_sessions IS '用户会话表';
COMMENT ON COLUMN public.user_sessions.session_token IS 'Supabase 会话令牌';
COMMENT ON COLUMN public.user_sessions.is_active IS '会话是否活跃';
