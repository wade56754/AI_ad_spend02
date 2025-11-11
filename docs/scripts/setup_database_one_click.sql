-- =====================================================
-- AI广告代投系统 - 一键数据库初始化脚本
-- 版本: 2.1
--
-- 使用说明：
-- 1. 复制整个脚本内容
-- 2. 在Supabase SQL编辑器中粘贴并执行
-- 3. 等待执行完成
-- =====================================================

-- 设置执行参数
SET statement_timeout = '600s'; -- 10分钟超时
SET search_path = public;

-- =====================================================
-- 第一部分：创建基础结构
-- =====================================================

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
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
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT users_role_check CHECK (role IN ('admin', 'finance', 'data_operator', 'account_manager', 'media_buyer'))
);

-- 创建项目表
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    client_name VARCHAR(100) NOT NULL,
    client_email VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    budget DECIMAL(12, 2),
    currency VARCHAR(3) DEFAULT 'CNY',
    start_date DATE,
    end_date DATE,
    owner_id INTEGER NOT NULL REFERENCES users(id),
    created_by INTEGER NOT NULL REFERENCES users(id),
    updated_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT projects_status_check CHECK (status IN ('active', 'paused', 'completed', 'cancelled'))
);

-- 创建渠道表
CREATE TABLE IF NOT EXISTS channels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    account_id VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    manager_id INTEGER REFERENCES users(id),
    created_by INTEGER NOT NULL REFERENCES users(id),
    updated_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT channels_status_check CHECK (status IN ('active', 'inactive', 'suspended')),
    UNIQUE(platform, account_id)
);

-- 创建广告账户表
CREATE TABLE IF NOT EXISTS ad_accounts (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    channel_id INTEGER NOT NULL REFERENCES channels(id),
    project_id INTEGER REFERENCES projects(id),
    assigned_to INTEGER REFERENCES users(id),
    balance DECIMAL(12, 2) DEFAULT 0,
    spent DECIMAL(12, 2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'CNY',
    created_by INTEGER NOT NULL REFERENCES users(id),
    updated_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ad_accounts_status_check CHECK (status IN ('active', 'inactive', 'banned', 'pending', 'suspended')),
    UNIQUE(platform, account_id)
);

-- 创建日报表
CREATE TABLE IF NOT EXISTS daily_reports (
    id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL,
    account_id INTEGER NOT NULL REFERENCES ad_accounts(id),
    submitter_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    spend DECIMAL(10, 2) NOT NULL DEFAULT 0,
    impressions INTEGER NOT NULL DEFAULT 0,
    clicks INTEGER NOT NULL DEFAULT 0,
    conversions INTEGER NOT NULL DEFAULT 0,
    revenue DECIMAL(10, 2) DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT daily_reports_status_check CHECK (status IN ('draft', 'submitted', 'reviewed', 'approved', 'rejected')),
    UNIQUE(report_date, account_id)
);

-- 创建充值表
CREATE TABLE IF NOT EXISTS topups (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(50) UNIQUE NOT NULL DEFAULT concat('TP', EXTRACT(EPOCH FROM NOW())::bigint),
    account_id INTEGER NOT NULL REFERENCES ad_accounts(id),
    requester_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CNY',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT topups_status_check CHECK (status IN ('draft', 'pending_review', 'approved', 'rejected', 'paid', 'confirmed', 'cancelled'))
);

-- =====================================================
-- 第二部分：创建索引
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_channels_manager_id ON channels(manager_id);
CREATE INDEX IF NOT EXISTS idx_ad_accounts_channel_id ON ad_accounts(channel_id);
CREATE INDEX IF NOT EXISTS idx_ad_accounts_project_id ON ad_accounts(project_id);
CREATE INDEX IF NOT EXISTS idx_ad_accounts_assigned_to ON ad_accounts(assigned_to);
CREATE INDEX IF NOT EXISTS idx_daily_reports_account_id ON daily_reports(account_id);
CREATE INDEX IF NOT EXISTS idx_daily_reports_date ON daily_reports(report_date);
CREATE INDEX IF NOT EXISTS idx_topups_account_id ON topups(account_id);
CREATE INDEX IF NOT EXISTS idx_topups_status ON topups(status);

-- =====================================================
-- 第三部分：创建触发器和函数
-- =====================================================

-- 更新时间戳函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建触发器
DO $$
DECLARE
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY ARRAY['users', 'projects', 'channels', 'ad_accounts', 'daily_reports', 'topups']
    LOOP
        EXECUTE format('CREATE TRIGGER update_%I_updated_at BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()', table_name, table_name);
    END LOOP;
END $$;

-- 密码加密函数
CREATE OR REPLACE FUNCTION hash_password(password TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN crypt(password, gen_salt('bf'));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 第四部分：创建管理员用户
-- =====================================================

-- 插入默认管理员
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

-- =====================================================
-- 第五部分：启用RLS（基础策略）
-- =====================================================

-- 启用RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE topups ENABLE ROW LEVEL SECURITY;

-- 创建基础RLS策略
-- 用户只能查看自己的信息
CREATE POLICY "Users view own data" ON users
    FOR SELECT USING (email = current_setting('app.current_user_email', true));

-- 管理员可以查看所有用户
CREATE POLICY "Admins view all users" ON users
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = current_setting('app.current_user_id', true)::INTEGER
            AND role = 'admin'
        )
    );

-- 项目成员可以查看项目
CREATE POLICY "Project members view projects" ON projects
    FOR SELECT USING (
        owner_id = current_setting('app.current_user_id', true)::INTEGER
        OR EXISTS (
            SELECT 1 FROM users
            WHERE id = current_setting('app.current_user_id', true)::INTEGER
            AND role IN ('admin', 'data_operator', 'account_manager')
        )
    );

-- 账户负责人可以查看账户
CREATE POLICY "Account users view accounts" ON ad_accounts
    FOR SELECT USING (
        assigned_to = current_setting('app.current_user_id', true)::INTEGER
        OR EXISTS (
            SELECT 1 FROM users
            WHERE id = current_setting('app.current_user_id', true)::INTEGER
            AND role IN ('admin', 'data_operator', 'account_manager', 'media_buyer')
        )
    );

-- 用户可以提交日报
CREATE POLICY "Users submit own reports" ON daily_reports
    FOR ALL USING (
        submitter_id = current_setting('app.current_user_id', true)::INTEGER
    );

-- 用户可以申请充值
CREATE POLICY "Users request topups" ON topups
    FOR ALL USING (
        requester_id = current_setting('app.current_user_id', true)::INTEGER
    );

-- =====================================================
-- 完成！
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=====================================================';
    RAISE NOTICE 'AI广告代投系统数据库初始化完成！';
    RAISE NOTICE '=====================================================';
    RAISE NOTICE '';
    RAISE NOTICE '默认管理员账号：';
    RAISE NOTICE '  邮箱: admin@aiad.com';
    RAISE NOTICE '  密码: admin123!@#';
    RAISE NOTICE '';
    RAISE NOTICE '下一步操作：';
    RAISE NOTICE '1. 使用默认账号登录系统';
    RAISE NOTICE '2. 立即修改默认密码';
    RAISE NOTICE '3. 创建其他用户账号';
    RAISE NOTICE '4. 创建项目和渠道';
    RAISE NOTICE '';
    RAISE NOTICE '注意事项：';
    RAISE NOTICE '- 请在生产环境中修改默认密码';
    RAISE NOTICE '- 根据需要调整RLS策略';
    RAISE NOTICE '- 定期备份数据库';
    RAISE NOTICE '=====================================================';
END $$;