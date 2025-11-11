-- =====================================================
-- AI广告代投系统数据库结构优化脚本
-- 版本: 2.1
-- 更新日期: 2025-01-11
--
-- 说明: 此脚本用于优化Supabase数据库结构
-- 包含表结构、索引、RLS策略、函数和触发器
-- =====================================================

-- 设置搜索路径
SET search_path = public, extensions;

-- 创建必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- 1. 删除已存在的表（按依赖关系倒序）
-- =====================================================

DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS daily_reports CASCADE;
DROP TABLE IF EXISTS topups CASCADE;
DROP TABLE IF EXISTS reconciliations CASCADE;
DROP TABLE IF EXISTS ad_accounts CASCADE;
DROP TABLE IF EXISTS channels CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- =====================================================
-- 2. 创建用户相关表
-- =====================================================

-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    avatar_url TEXT,
    role VARCHAR(20) NOT NULL DEFAULT 'media_buyer',
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_superuser BOOLEAN NOT NULL DEFAULT false,
    email_verified BOOLEAN NOT NULL DEFAULT false,
    phone VARCHAR(20),
    last_login_at TIMESTAMPTZ,
    password_changed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT users_role_check CHECK (role IN ('admin', 'finance', 'data_operator', 'account_manager', 'media_buyer')),
    CONSTRAINT users_email_check CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- 用户配置表（扩展字段）
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    department VARCHAR(50),
    position VARCHAR(50),
    bio TEXT,
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'zh-CN',
    theme VARCHAR(20) DEFAULT 'light',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(user_id)
);

-- 会话表（JWT会话管理）
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    refresh_token_hash VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =====================================================
-- 3. 创建核心业务表
-- =====================================================

-- 项目表
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    client_name VARCHAR(100) NOT NULL,
    client_email VARCHAR(255),
    client_phone VARCHAR(20),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    budget DECIMAL(12, 2),
    currency VARCHAR(3) DEFAULT 'CNY',
    start_date DATE,
    end_date DATE,
    owner_id INTEGER NOT NULL REFERENCES users(id),
    account_manager_id INTEGER REFERENCES users(id),
    created_by INTEGER NOT NULL REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT projects_status_check CHECK (status IN ('active', 'paused', 'completed', 'cancelled')),
    CONSTRAINT projects_date_check CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date),
    CONSTRAINT projects_budget_check CHECK (budget IS NULL OR budget >= 0)
);

-- 渠道表
CREATE TABLE channels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    account_id VARCHAR(100) NOT NULL,
    account_name VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    daily_budget DECIMAL(10, 2),
    monthly_budget DECIMAL(12, 2),
    currency VARCHAR(3) DEFAULT 'CNY',
    timezone VARCHAR(50) DEFAULT 'UTC',
    manager_id INTEGER REFERENCES users(id),
    config JSONB DEFAULT '{}',
    created_by INTEGER NOT NULL REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT channels_status_check CHECK (status IN ('active', 'inactive', 'suspended')),
    CONSTRAINT channels_budget_check CHECK (
        (daily_budget IS NULL OR daily_budget >= 0) AND
        (monthly_budget IS NULL OR monthly_budget >= 0)
    ),
    UNIQUE(platform, account_id)
);

-- 广告账户表
CREATE TABLE ad_accounts (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    channel_id INTEGER NOT NULL REFERENCES channels(id),
    project_id INTEGER REFERENCES projects(id),
    assigned_to INTEGER REFERENCES users(id),
    daily_budget DECIMAL(10, 2),
    lifetime_budget DECIMAL(12, 2),
    spent DECIMAL(12, 2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'CNY',
    timezone VARCHAR(50) DEFAULT 'UTC',
    balance DECIMAL(12, 2) DEFAULT 0,
    metrics JSONB DEFAULT '{}',
    created_by INTEGER NOT NULL REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ad_accounts_status_check CHECK (status IN ('active', 'inactive', 'banned', 'pending', 'suspended')),
    CONSTRAINT ad_accounts_budget_check CHECK (
        (daily_budget IS NULL OR daily_budget >= 0) AND
        (lifetime_budget IS NULL OR lifetime_budget >= 0) AND
        spent >= 0 AND balance >= 0
    ),
    UNIQUE(platform, account_id)
);

-- 项目成员关联表
CREATE TABLE project_members (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'member',
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT project_members_role_check CHECK (role IN ('owner', 'manager', 'member')),
    UNIQUE(project_id, user_id)
);

-- =====================================================
-- 4. 创建业务流程表
-- =====================================================

-- 日报表
CREATE TABLE daily_reports (
    id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL,
    account_id INTEGER NOT NULL REFERENCES ad_accounts(id),
    submitter_id INTEGER NOT NULL REFERENCES users(id),
    reviewer_id INTEGER REFERENCES users(id),
    status VARCHAR(20) NOT NULL DEFAULT 'draft',

    -- 基础数据
    spend DECIMAL(10, 2) NOT NULL DEFAULT 0,
    impressions INTEGER NOT NULL DEFAULT 0,
    clicks INTEGER NOT NULL DEFAULT 0,
    conversions INTEGER NOT NULL DEFAULT 0,
    revenue DECIMAL(10, 2) DEFAULT 0,

    -- 计算字段
    cpm DECIMAL(10, 2) GENERATED ALWAYS AS (
        CASE WHEN impressions > 0 THEN ROUND((spend / impressions) * 1000, 2) ELSE NULL END
    ) STORED,
    cpc DECIMAL(10, 2) GENERATED ALWAYS AS (
        CASE WHEN clicks > 0 THEN ROUND(spend / clicks, 2) ELSE NULL END
    ) STORED,
    ctr DECIMAL(5, 2) GENERATED ALWAYS AS (
        CASE WHEN impressions > 0 THEN ROUND((clicks::FLOAT / impressions) * 100, 2) ELSE NULL END
    ) STORED,
    cpa DECIMAL(10, 2) GENERATED ALWAYS AS (
        CASE WHEN conversions > 0 THEN ROUND(spend / conversions, 2) ELSE NULL END
    ) STORED,
    roas DECIMAL(5, 2) GENERATED ALWAYS AS (
        CASE WHEN spend > 0 THEN ROUND(revenue / spend, 2) ELSE NULL END
    ) STORED,

    -- 附加信息
    notes TEXT,
    attachments JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',

    -- 审核相关
    submitted_at TIMESTAMPTZ,
    reviewed_at TIMESTAMPTZ,
    rejection_reason TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT daily_reports_status_check CHECK (status IN ('draft', 'submitted', 'reviewed', 'approved', 'rejected')),
    CONSTRAINT daily_reports_spend_check CHECK (spend >= 0),
    CONSTRAINT daily_reports_impressions_check CHECK (impressions >= 0),
    CONSTRAINT daily_reports_clicks_check CHECK (clicks >= 0),
    CONSTRAINT daily_reports_conversions_check CHECK (conversions >= 0),
    CONSTRAINT daily_reports_revenue_check CHECK (revenue >= 0),
    UNIQUE(report_date, account_id)
);

-- 充值表
CREATE TABLE topups (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(50) UNIQUE NOT NULL DEFAULT concat('TP', EXTRACT(EPOCH FROM NOW())::bigint, RANDOM()),
    account_id INTEGER NOT NULL REFERENCES ad_accounts(id),
    requester_id INTEGER NOT NULL REFERENCES users(id),
    reviewer_id INTEGER REFERENCES users(id),
    approver_id INTEGER REFERENCES users(id),
    status VARCHAR(20) NOT NULL DEFAULT 'draft',

    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CNY',
    payment_method VARCHAR(50),
    payment_reference VARCHAR(100),
    bank_account VARCHAR(50),

    notes TEXT,
    attachments JSONB DEFAULT '[]',

    -- 时间戳
    requested_at TIMESTAMPTZ,
    reviewed_at TIMESTAMPTZ,
    approved_at TIMESTAMPTZ,
    paid_at TIMESTAMPTZ,
    confirmed_at TIMESTAMPTZ,

    created_by INTEGER NOT NULL REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT topups_status_check CHECK (status IN ('draft', 'pending_review', 'approved', 'rejected', 'paid', 'confirmed', 'cancelled')),
    CONSTRAINT topups_amount_check CHECK (amount > 0)
);

-- 对账表
CREATE TABLE reconciliations (
    id SERIAL PRIMARY KEY,
    reconciliation_id VARCHAR(50) UNIQUE NOT NULL DEFAULT concat('RC', EXTRACT(EPOCH FROM NOW())::bigint, RANDOM()),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    account_id INTEGER NOT NULL REFERENCES ad_accounts(id),

    -- 金额汇总
    total_spend DECIMAL(12, 2) NOT NULL DEFAULT 0,
    total_charges DECIMAL(12, 2) NOT NULL DEFAULT 0,
    total_adjustments DECIMAL(12, 2) NOT NULL DEFAULT 0,
    final_amount DECIMAL(12, 2) NOT NULL DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'CNY',

    status VARCHAR(20) NOT NULL DEFAULT 'draft',

    notes TEXT,
    attachments JSONB DEFAULT '[]',
    breakdown JSONB DEFAULT '{}',

    reconciled_by INTEGER REFERENCES users(id),
    completed_at TIMESTAMPTZ,

    created_by INTEGER NOT NULL REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT reconciliations_status_check CHECK (status IN ('draft', 'pending', 'completed', 'disputed')),
    CONSTRAINT reconciliations_period_check CHECK (period_end >= period_start),
    CONSTRAINT reconciliations_amount_check CHECK (
        total_spend >= 0 AND total_charges >= 0 AND final_amount >= 0
    )
);

-- =====================================================
-- 5. 创建审计日志表
-- =====================================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    user_email VARCHAR(255),
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    action VARCHAR(20) NOT NULL,

    -- 请求信息
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),

    -- 变更数据
    old_values JSONB,
    new_values JSONB,
    details JSONB DEFAULT '{}',

    -- 结果
    success BOOLEAN NOT NULL DEFAULT true,
    error_message TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =====================================================
-- 6. 创建索引
-- =====================================================

-- 用户表索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);

-- 会话表索引
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token_hash ON sessions(token_hash);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX idx_sessions_is_active ON sessions(is_active);

-- 项目表索引
CREATE INDEX idx_projects_owner_id ON projects(owner_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_created_at ON projects(created_at);
CREATE INDEX idx_projects_client_email ON projects(client_email);

-- 渠道表索引
CREATE INDEX idx_channels_platform ON channels(platform);
CREATE INDEX idx_channels_manager_id ON channels(manager_id);
CREATE INDEX idx_channels_status ON channels(status);

-- 广告账户表索引
CREATE INDEX idx_ad_accounts_channel_id ON ad_accounts(channel_id);
CREATE INDEX idx_ad_accounts_project_id ON ad_accounts(project_id);
CREATE INDEX idx_ad_accounts_assigned_to ON ad_accounts(assigned_to);
CREATE INDEX idx_ad_accounts_status ON ad_accounts(status);
CREATE INDEX idx_ad_accounts_platform ON ad_accounts(platform);

-- 日报表索引
CREATE INDEX idx_daily_reports_report_date ON daily_reports(report_date);
CREATE INDEX idx_daily_reports_account_id ON daily_reports(account_id);
CREATE INDEX idx_daily_reports_submitter_id ON daily_reports(submitter_id);
CREATE INDEX idx_daily_reports_status ON daily_reports(status);
CREATE INDEX idx_daily_reports_created_at ON daily_reports(created_at);
CREATE INDEX idx_daily_reports_date_account ON daily_reports(report_date, account_id);

-- 充值表索引
CREATE INDEX idx_topups_account_id ON topups(account_id);
CREATE INDEX idx_topups_requester_id ON topups(requester_id);
CREATE INDEX idx_topups_status ON topups(status);
CREATE INDEX idx_topups_created_at ON topups(created_at);
CREATE INDEX idx_topups_amount ON topups(amount);

-- 对账表索引
CREATE INDEX idx_reconciliations_account_id ON reconciliations(account_id);
CREATE INDEX idx_reconciliations_period ON reconciliations(period_start, period_end);
CREATE INDEX idx_reconciliations_status ON reconciliations(status);
CREATE INDEX idx_reconciliations_created_at ON reconciliations(created_at);

-- 审计日志索引
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_ip_address ON audit_logs(ip_address);

-- 复合索引
CREATE INDEX idx_projects_status_owner ON projects(status, owner_id);
CREATE INDEX idx_ad_accounts_project_status ON ad_accounts(project_id, status);
CREATE INDEX idx_daily_reports_account_status ON daily_reports(account_id, status);
CREATE INDEX idx_topups_account_status ON topups(account_id, status);

-- =====================================================
-- 7. 创建触发器和函数
-- =====================================================

-- 更新updated_at字段的函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为所有需要的表添加updated_at触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_channels_updated_at BEFORE UPDATE ON channels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ad_accounts_updated_at BEFORE UPDATE ON ad_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_daily_reports_updated_at BEFORE UPDATE ON daily_reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_topups_updated_at BEFORE UPDATE ON topups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reconciliations_updated_at BEFORE UPDATE ON reconciliations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 审计日志触发器函数
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (
        event_type,
        user_id,
        user_email,
        resource_type,
        resource_id,
        action,
        old_values,
        new_values,
        details,
        success
    ) VALUES (
        TG_TABLE_NAME,
        COALESCE(NEW.created_by, OLD.created_by, NULL),
        COALESCE(
            (SELECT email FROM users WHERE id = COALESCE(NEW.created_by, OLD.created_by)),
            NULL
        ),
        TG_TABLE_NAME,
        COALESCE(NEW.id::TEXT, OLD.id::TEXT),
        TG_OP,
        CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW) ELSE NULL END,
        jsonb_build_object(
            'operation', TG_OP,
            'table', TG_TABLE_NAME,
            'user_id', current_setting('app.current_user_id', true)::INTEGER
        ),
        true
    );

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 为重要表添加审计触发器
CREATE TRIGGER audit_projects_trigger
    AFTER INSERT OR UPDATE OR DELETE ON projects
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_ad_accounts_trigger
    AFTER INSERT OR UPDATE OR DELETE ON ad_accounts
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_daily_reports_trigger
    AFTER INSERT OR UPDATE OR DELETE ON daily_reports
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_topups_trigger
    AFTER INSERT OR UPDATE OR DELETE ON topups
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- 密码加密函数
CREATE OR REPLACE FUNCTION hash_password(password TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN crypt(password, gen_salt('bf', 10));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 密码验证函数
CREATE OR REPLACE FUNCTION verify_password(password TEXT, hashed TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN (hashed = crypt(password, hashed));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 生成请求ID函数
CREATE OR REPLACE FUNCTION generate_request_id(prefix TEXT DEFAULT 'REQ')
RETURNS TEXT AS $$
BEGIN
    RETURN prefix || EXTRACT(EPOCH FROM NOW())::bigint || RANDOM();
END;
$$ LANGUAGE plpgsql;

-- 计算项目ROI函数
CREATE OR REPLACE FUNCTION calculate_project_roi(project_id_param INTEGER)
RETURNS DECIMAL(5, 2) AS $$
DECLARE
    total_revenue DECIMAL(12, 2);
    total_spend DECIMAL(12, 2);
    roi DECIMAL(5, 2);
BEGIN
    -- 计算总收入
    SELECT COALESCE(SUM(revenue), 0)
    INTO total_revenue
    FROM daily_reports dr
    JOIN ad_accounts aa ON dr.account_id = aa.id
    WHERE aa.project_id = project_id_param;

    -- 计算总支出
    SELECT COALESCE(SUM(spend), 0)
    INTO total_spend
    FROM daily_reports dr
    JOIN ad_accounts aa ON dr.account_id = aa.id
    WHERE aa.project_id = project_id_param;

    -- 计算ROI
    IF total_spend > 0 THEN
        roi := ROUND((total_revenue - total_spend) / total_spend * 100, 2);
    ELSE
        roi := 0;
    END IF;

    RETURN roi;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 8. 创建视图
-- =====================================================

-- 用户详情视图
CREATE VIEW user_details AS
SELECT
    u.id,
    u.email,
    u.username,
    u.full_name,
    u.role,
    u.is_active,
    u.avatar_url,
    u.last_login_at,
    u.created_at,
    up.department,
    up.position,
    up.timezone,
    up.preferences
FROM users u
LEFT JOIN user_profiles up ON u.id = up.user_id;

-- 项目统计视图
CREATE VIEW project_statistics AS
SELECT
    p.id,
    p.name,
    p.status,
    p.owner_id,
    COUNT(DISTINCT aa.id) as account_count,
    COUNT(DISTINCT pm.user_id) as member_count,
    COALESCE(SUM(dr.spend), 0) as total_spend,
    COALESCE(SUM(dr.revenue), 0) as total_revenue,
    calculate_project_roi(p.id) as roi,
    MIN(dr.report_date) as first_report_date,
    MAX(dr.report_date) as last_report_date
FROM projects p
LEFT JOIN ad_accounts aa ON p.id = aa.project_id
LEFT JOIN project_members pm ON p.id = pm.project_id
LEFT JOIN daily_reports dr ON aa.id = dr.account_id
GROUP BY p.id, p.name, p.status, p.owner_id;

-- 账户余额视图
CREATE VIEW account_balance_view AS
SELECT
    aa.id,
    aa.account_id,
    aa.name,
    aa.platform,
    aa.currency,
    aa.balance,
    aa.spent,
    aa.lifetime_budget,
    CASE
        WHEN aa.lifetime_budget > 0
        THEN ROUND((aa.spent / aa.lifetime_budget) * 100, 2)
        ELSE 0
    END as budget_usage_percent,
    p.name as project_name,
    c.name as channel_name
FROM ad_accounts aa
LEFT JOIN projects p ON aa.project_id = p.id
LEFT JOIN channels c ON aa.channel_id = c.id;

-- =====================================================
-- 9. 插入初始数据
-- =====================================================

-- 创建默认管理员用户
INSERT INTO users (
    email,
    username,
    password_hash,
    full_name,
    role,
    is_active,
    is_superuser,
    email_verified
) VALUES (
    'admin@aiad.com',
    'admin',
    hash_password('admin123!@#'),
    '系统管理员',
    'admin',
    true,
    true,
    true
) ON CONFLICT (email) DO NOTHING;

-- 创建用户配置
INSERT INTO user_profiles (user_id, department, position)
SELECT id, 'IT', '系统管理员'
FROM users
WHERE username = 'admin'
ON CONFLICT (user_id) DO NOTHING;

-- =====================================================
-- 10. 完成提示
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '=====================================================';
    RAISE NOTICE '数据库结构优化完成！';
    RAISE NOTICE '';
    RAISE NOTICE '已创建的表:';
    RAISE NOTICE '- users (用户表)';
    RAISE NOTICE '- user_profiles (用户配置表)';
    RAISE NOTICE '- sessions (会话表)';
    RAISE NOTICE '- projects (项目表)';
    RAISE NOTICE '- channels (渠道表)';
    RAISE NOTICE '- ad_accounts (广告账户表)';
    RAISE NOTICE '- project_members (项目成员表)';
    RAISE NOTICE '- daily_reports (日报表)';
    RAISE NOTICE '- topups (充值表)';
    RAISE NOTICE '- reconciliations (对账表)';
    RAISE NOTICE '- audit_logs (审计日志表)';
    RAISE NOTICE '';
    RAISE NOTICE '已创建的视图:';
    RAISE NOTICE '- user_details (用户详情视图)';
    RAISE NOTICE '- project_statistics (项目统计视图)';
    RAISE NOTICE '- account_balance_view (账户余额视图)';
    RAISE NOTICE '';
    RAISE NOTICE '默认管理员账号:';
    RAISE NOTICE '- 邮箱: admin@aiad.com';
    RAISE NOTICE '- 密码: admin123!@#';
    RAISE NOTICE '=====================================================';
END $$;