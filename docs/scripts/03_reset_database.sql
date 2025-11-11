-- =====================================================
-- 数据库完全重置脚本
-- 警告：此脚本将删除所有现有表和数据！
-- =====================================================

-- 设置执行参数
SET session_replication_role = replica; -- 禁用触发器，提升删除速度
SET statement_timeout = '600s';
SET search_path = public;

-- 创建临时日志表记录操作
CREATE TEMP TABLE reset_log (
    step_number INTEGER,
    step_name TEXT,
    action TEXT,
    status TEXT,
    detail TEXT,
    executed_at TIMESTAMPTZ DEFAULT NOW()
);

-- 记录开始
INSERT INTO reset_log VALUES (1, '重置开始', 'WARNING', '即将删除所有表', '开始执行数据库重置');

-- =====================================================
-- 第一步：删除所有触发器
-- =====================================================

DO $$
DECLARE
    trigger_record RECORD;
    counter INTEGER := 0;
BEGIN
    FOR trigger_record IN
        SELECT trigger_name, event_object_table
        FROM information_schema.triggers
        WHERE trigger_schema = 'public'
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS %I ON %I', trigger_record.trigger_name, trigger_record.event_object_table);
        counter := counter + 1;
    END LOOP;

    INSERT INTO reset_log VALUES (2, '删除触发器', 'INFO', 'SUCCESS', format('已删除 %s 个触发器', counter));
END $$;

-- =====================================================
-- 第二步：删除所有函数（除了系统函数）
-- =====================================================

DO $$
DECLARE
    func_record RECORD;
    counter INTEGER := 0;
BEGIN
    -- 删除自定义函数
    FOR func_record IN
        SELECT proname
        FROM pg_proc
        WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
        AND proname NOT IN ('update_updated_at_column', 'hash_password')
        AND prosrc NOT LIKE '%system%'
    LOOP
        EXECUTE format('DROP FUNCTION IF EXISTS %I() CASCADE', func_record.proname);
        counter := counter + 1;
    END LOOP;

    INSERT INTO reset_log VALUES (3, '删除函数', 'INFO', 'SUCCESS', format('已删除 %s 个自定义函数', counter));
END $$;

-- =====================================================
-- 第三步：删除所有视图
-- =====================================================

DO $$
DECLARE
    view_record RECORD;
    counter INTEGER := 0;
BEGIN
    FOR view_record IN
        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = 'public'
    LOOP
        EXECUTE format('DROP VIEW IF EXISTS %I CASCADE', view_record.table_name);
        counter := counter + 1;
    END LOOP;

    INSERT INTO reset_log VALUES (4, '删除视图', 'INFO', 'SUCCESS', format('已删除 %s 个视图', counter));
END $$;

-- =====================================================
-- 第四步：删除所有表（按依赖关系排序）
-- =====================================================

-- 创建表删除顺序数组
DO $$
DECLARE
    tables_to_drop TEXT[] := ARRAY[
        -- 临时表最后删除
        'migration_diagnosis',
        'reset_log',

        -- 按依赖关系排序
        'audit_logs',
        'daily_reports',
        'topups',
        'reconciliations',
        'project_members',
        'ad_accounts',
        'channels',
        'projects',
        'user_profiles',
        'sessions',
        'users'
    ];

    table_name TEXT;
    counter INTEGER := 0;
BEGIN
    FOREACH table_name IN ARRAY tables_to_drop
    LOOP
        BEGIN
            EXECUTE format('DROP TABLE IF EXISTS %I CASCADE', table_name);
            counter := counter + 1;

            INSERT INTO reset_log VALUES (5, '删除表', 'INFO', 'SUCCESS', format('已删除表: %s', table_name));
        EXCEPTION
            WHEN OTHERS THEN
                INSERT INTO reset_log VALUES (5, '删除表', 'WARNING', 'FAILED', format('删除表 %s 失败: %s', table_name, SQLERRM));
        END;
    END LOOP;

    -- 删除任何遗漏的表
    FOR table_name IN
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name NOT IN (SELECT unnest(tables_to_drop))
    LOOP
        BEGIN
            EXECUTE format('DROP TABLE IF EXISTS %I CASCADE', table_name);
            counter := counter + 1;

            INSERT INTO reset_log VALUES (6, '删除剩余表', 'INFO', 'SUCCESS', format('已删除剩余表: %s', table_name));
        EXCEPTION
            WHEN OTHERS THEN
                NULL; -- 忽略错误
        END;
    END LOOP;
END $$;

-- =====================================================
-- 第五步：创建新的数据库结构
-- =====================================================

-- 创建必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

INSERT INTO reset_log VALUES (7, '创建扩展', 'INFO', 'SUCCESS', '已创建必要扩展');

-- =====================================================
-- 创建核心表
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

INSERT INTO reset_log VALUES (8, '创建用户表', 'INFO', 'SUCCESS', 'users表已创建');

-- 用户配置表
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

INSERT INTO reset_log VALUES (9, '创建用户配置表', 'INFO', 'SUCCESS', 'user_profiles表已创建');

-- 会话表
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

INSERT INTO reset_log VALUES (10, '创建会话表', 'INFO', 'SUCCESS', 'sessions表已创建');

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
    updated_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT projects_status_check CHECK (status IN ('active', 'paused', 'completed', 'cancelled')),
    CONSTRAINT projects_date_check CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
);

INSERT INTO reset_log VALUES (11, '创建项目表', 'INFO', 'SUCCESS', 'projects表已创建');

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
    updated_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT channels_status_check CHECK (status IN ('active', 'inactive', 'suspended')),
    UNIQUE(platform, account_id)
);

INSERT INTO reset_log VALUES (12, '创建渠道表', 'INFO', 'SUCCESS', 'channels表已创建');

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
    updated_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ad_accounts_status_check CHECK (status IN ('active', 'inactive', 'banned', 'pending', 'suspended')),
    UNIQUE(platform, account_id)
);

INSERT INTO reset_log VALUES (13, '创建广告账户表', 'INFO', 'SUCCESS', 'ad_accounts表已创建');

-- 项目成员表
CREATE TABLE project_members (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'member',
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT project_members_role_check CHECK (role IN ('owner', 'manager', 'member')),
    UNIQUE(project_id, user_id)
);

INSERT INTO reset_log VALUES (14, '创建项目成员表', 'INFO', 'SUCCESS', 'project_members表已创建');

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
    UNIQUE(report_date, account_id)
);

INSERT INTO reset_log VALUES (15, '创建日报表', 'INFO', 'SUCCESS', 'daily_reports表已创建');

-- 充值表
CREATE TABLE topups (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(50) UNIQUE NOT NULL DEFAULT concat('TP', EXTRACT(EPOCH FROM NOW())::bigint),
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
    updated_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT topups_status_check CHECK (status IN ('draft', 'pending_review', 'approved', 'rejected', 'paid', 'confirmed', 'cancelled'))
);

INSERT INTO reset_log VALUES (16, '创建充值表', 'INFO', 'SUCCESS', 'topups表已创建');

-- 对账表
CREATE TABLE reconciliations (
    id SERIAL PRIMARY KEY,
    reconciliation_id VARCHAR(50) UNIQUE NOT NULL DEFAULT concat('RC', EXTRACT(EPOCH FROM NOW())::bigint),
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
    updated_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT reconciliations_status_check CHECK (status IN ('draft', 'pending', 'completed', 'disputed'))
);

INSERT INTO reset_log VALUES (17, '创建对账表', 'INFO', 'SUCCESS', 'reconciliations表已创建');

-- 审计日志表
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

INSERT INTO reset_log VALUES (18, '创建审计日志表', 'INFO', 'SUCCESS', 'audit_logs表已创建');

-- =====================================================
-- 第六步：创建索引
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

-- 充值表索引
CREATE INDEX idx_topups_account_id ON topups(account_id);
CREATE INDEX idx_topups_requester_id ON topups(requester_id);
CREATE INDEX idx_topups_status ON topups(status);
CREATE INDEX idx_topups_created_at ON topups(created_at);

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

INSERT INTO reset_log VALUES (19, '创建索引', 'INFO', 'SUCCESS', '所有索引已创建');

-- =====================================================
-- 第七步：创建触发器和函数
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
DO $$
DECLARE
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'users', 'user_profiles', 'projects', 'channels',
        'ad_accounts', 'daily_reports', 'topups', 'reconciliations'
    ]
    LOOP
        EXECUTE format('CREATE TRIGGER update_%I_updated_at BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()', table_name, table_name);
    END LOOP;
END $$;

INSERT INTO reset_log VALUES (20, '创建触发器', 'INFO', 'SUCCESS', 'updated_at触发器已创建');

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

INSERT INTO reset_log VALUES (21, '创建函数', 'INFO', 'SUCCESS', '密码相关函数已创建');

-- =====================================================
-- 第八步：创建视图
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

INSERT INTO reset_log VALUES (22, '创建视图', 'INFO', 'SUCCESS', 'user_details视图已创建');

-- =====================================================
-- 第九步：插入初始数据
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
);

-- 创建用户配置
INSERT INTO user_profiles (user_id, department, position)
SELECT id, 'IT', '系统管理员'
FROM users
WHERE username = 'admin';

INSERT INTO reset_log VALUES (23, '插入初始数据', 'INFO', 'SUCCESS', '默认管理员用户已创建');

-- 恢复触发器
SET session_replication_role = DEFAULT;

-- =====================================================
-- 第十步：显示重置结果
-- =====================================================

-- 显示操作日志
SELECT * FROM reset_log ORDER BY step_number;

-- 显示最终的表列表
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- 显示默认管理员信息
SELECT id, email, username, full_name, role, created_at
FROM users
WHERE username = 'admin';

-- 完成提示
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '数据库重置完成！';
    RAISE NOTICE '';
    RAISE NOTICE '新创建的表数量: %s', (
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    );
    RAISE NOTICE '';
    RAISE NOTICE '默认管理员账号：';
    RAISE NOTICE '  邮箱: admin@aiad.com';
    RAISE NOTICE '  密码: admin123!@#';
    RAISE NOTICE '  用户名: admin';
    RAISE NOTICE '';
    RAISE NOTICE '下一步：';
    RAISE NOTICE '1. 使用默认账号登录系统';
    RAISE NOTICE '2. 立即修改默认密码';
    RAISE NOTICE '3. 创建其他用户账号';
    RAISE NOTICE '4. 配置应用环境变量';
    RAISE NOTICE '========================================';
END $$;

-- 清理临时表
DROP TABLE IF EXISTS reset_log;