-- AI广告代投系统数据库初始化脚本

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 创建用户角色枚举
CREATE TYPE user_role AS ENUM ('admin', 'manager', 'media_buyer', 'account_manager', 'finance');

-- 创建项目状态枚举
CREATE TYPE project_status AS ENUM ('planning', 'active', 'paused', 'completed', 'archived');

-- 创建账户状态枚举
CREATE TYPE account_status AS ENUM ('active', 'paused', 'banned', 'pending');

-- 创建充值申请状态枚举
CREATE TYPE topup_status AS ENUM ('pending', 'approved', 'rejected', 'completed');

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role user_role NOT NULL DEFAULT 'media_buyer',
    phone VARCHAR(20),
    department VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- 创建客户表
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact_person VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    company VARCHAR(100),
    address TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建项目表
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    client_id INTEGER REFERENCES clients(id),
    description TEXT,
    budget DECIMAL(12,2) NOT NULL DEFAULT 0,
    current_spend DECIMAL(12,2) NOT NULL DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'CNY',
    status project_status DEFAULT 'planning',
    priority VARCHAR(10) DEFAULT 'medium',
    start_date DATE,
    end_date DATE,
    team_lead_id INTEGER REFERENCES users(id),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建广告平台表
CREATE TABLE IF NOT EXISTS ad_platforms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    display_name VARCHAR(50) NOT NULL,
    api_endpoint VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 插入默认广告平台
INSERT INTO ad_platforms (name, display_name) VALUES
('facebook', 'Facebook Ads'),
('tiktok', 'TikTok Ads'),
('google', 'Google Ads'),
('twitter', 'Twitter Ads')
ON CONFLICT DO NOTHING;

-- 创建广告账户表
CREATE TABLE IF NOT EXISTS ad_accounts (
    id SERIAL PRIMARY KEY,
    account_name VARCHAR(100) NOT NULL,
    platform_id INTEGER REFERENCES ad_platforms(id),
    account_id VARCHAR(100) NOT NULL,
    account_type VARCHAR(20) DEFAULT 'business',
    status account_status DEFAULT 'active',
    currency VARCHAR(3) DEFAULT 'CNY',
    timezone VARCHAR(50) DEFAULT 'UTC',
    spending_limit DECIMAL(12,2),
    current_spend DECIMAL(12,2) NOT NULL DEFAULT 0,
    balance DECIMAL(12,2) NOT NULL DEFAULT 0,
    assigned_user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(platform_id, account_id)
);

-- 创建项目账户关联表
CREATE TABLE IF NOT EXISTS project_accounts (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    account_id INTEGER REFERENCES ad_accounts(id),
    is_active BOOLEAN DEFAULT true,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by INTEGER REFERENCES users(id),
    UNIQUE(project_id, account_id)
);

-- 创建日报表
CREATE TABLE IF NOT EXISTS daily_reports (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES ad_accounts(id),
    report_date DATE NOT NULL,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    spend DECIMAL(10,2) DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    new_follows INTEGER DEFAULT 0,
    revenue DECIMAL(10,2) DEFAULT 0,
    submitted_by INTEGER REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'pending',
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(account_id, report_date)
);

-- 创建充值申请表
CREATE TABLE IF NOT EXISTS topup_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    account_id INTEGER REFERENCES ad_accounts(id),
    project_id INTEGER REFERENCES projects(id),
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CNY',
    reason TEXT NOT NULL,
    urgency_level VARCHAR(20) DEFAULT 'normal',
    status topup_status DEFAULT 'pending',
    requested_amount DECIMAL(10,2) NOT NULL,
    approved_amount DECIMAL(10,2),
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_comment TEXT,
    receipt_url VARCHAR(255),
    transaction_id VARCHAR(100),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表添加更新时间触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ad_accounts_updated_at BEFORE UPDATE ON ad_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_daily_reports_updated_at BEFORE UPDATE ON daily_reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_topup_requests_updated_at BEFORE UPDATE ON topup_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入默认管理员用户（密码：admin123）
INSERT INTO users (username, email, hashed_password, full_name, role)
VALUES (
    'admin',
    'admin@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYxXm9xp2mu4htW', -- admin123
    '系统管理员',
    'admin'
) ON CONFLICT (username) DO NOTHING;

-- 插入测试数据
INSERT INTO clients (name, contact_person, email, phone, company) VALUES
('雅诗兰黛', '张经理', 'zhang@estee.com', '13800138001', '雅诗兰黛中国'),
('京东商城', '李总监', 'li@jd.com', '13800138002', '京东集团'),
('腾讯游戏', '王主管', 'wang@tencent.com', '13800138003', '腾讯科技有限公司')
ON CONFLICT DO NOTHING;

-- 插入测试用户
INSERT INTO users (username, email, hashed_password, full_name, role, phone, department) VALUES
('zhangsan', 'zhangsan@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYxXm9xp2mu4htW', '张三', 'media_buyer', '13800138004', '投放部'),
('lisi', 'lisi@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYxXm9xp2mu4htW', '李四', 'account_manager', '13800138005', '账户部'),
('wangwu', 'wangwu@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYxXm9xp2mu4htW', '王五', 'finance', '13800138006', '财务部'),
('zhaoliu', 'zhaoliu@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYxXm9xp2mu4htW', '赵六', 'media_buyer', '13800138007', '投放部')
ON CONFLICT (username) DO NOTHING;

-- 插入测试项目
INSERT INTO projects (name, client_id, description, budget, current_spend, status, start_date, end_date, team_lead_id, progress) VALUES
('美妆品牌推广项目', 1, '雅诗兰黛新产品线推广', 200000, 85000, 'active', '2025-01-01', '2025-02-28', 1, 42),
('电商大促活动', 2, '京东618大促活动', 500000, 320000, 'active', '2025-01-15', '2025-06-30', 2, 64),
('游戏发行推广', 3, '新游戏上市推广', 150000, 45000, 'planning', '2025-02-01', '2025-05-31', 3, 30)
ON CONFLICT DO NOTHING;

-- 插入测试广告账户
INSERT INTO ad_accounts (account_name, platform_id, account_id, account_type, status, currency, spending_limit, current_spend, balance, assigned_user_id) VALUES
('Facebook广告账户01', 1, 'act_1234567890', 'business', 'active', 'CNY', 100000, 25000, 75000, 1),
('TikTok广告账户02', 2, 'adv_0987654321', 'business', 'active', 'CNY', 80000, 18000, 62000, 2),
('Google Ads账户03', 3, '123-456-7890', 'business', 'active', 'CNY', 120000, 30000, 90000, 1),
('Twitter广告账户04', 4, 'tw_account_001', 'business', 'paused', 'CNY', 50000, 8000, 42000, 4)
ON CONFLICT DO NOTHING;

-- 建立项目和账户的关联
INSERT INTO project_accounts (project_id, account_id, assigned_by) VALUES
(1, 1, 1),
(1, 3, 1),
(2, 2, 2),
(3, 1, 3)
ON CONFLICT DO NOTHING;

COMMIT;