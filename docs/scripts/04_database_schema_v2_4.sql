-- =====================================================
-- AI广告代投系统数据库架构 v2.4（生产就绪版）
--
-- 修复内容（基于优化清单）：
-- - 1. 修复语法问题：RAISE NOTICE 包装到 DO 块
-- - 2. 移除 CONCURRENTLY 避免事务冲突
-- - 3. 修复业务逻辑错误（统计函数、视图字段）
-- - 4. 优化RLS安全策略
-- - 5. 统一主键生成方式为 gen_random_uuid()
-- - 6. 调整外键删除策略
-- =====================================================

-- 设置执行参数
SET statement_timeout = '1800s';
SET search_path = public;

-- 启用必要扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- =====================================================
-- 创建自定义枚举类型
-- =====================================================
DO $$
BEGIN
    -- 检查并创建枚举类型
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'project_status_enum') THEN
        CREATE TYPE project_status_enum AS ENUM ('draft', 'active', 'paused', 'completed', 'cancelled', 'archived');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'account_status_enum') THEN
        CREATE TYPE account_status_enum AS ENUM ('draft', 'new', 'testing', 'active', 'suspended', 'dead', 'archived');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role_enum') THEN
        CREATE TYPE user_role_enum AS ENUM ('admin', 'finance', 'data_operator', 'account_manager', 'media_buyer');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'report_status_enum') THEN
        CREATE TYPE report_status_enum AS ENUM ('draft', 'submitted', 'reviewed', 'approved', 'rejected', 'archived');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'topup_status_enum') THEN
        CREATE TYPE topup_status_enum AS ENUM ('draft', 'pending_review', 'reviewed', 'approved', 'rejected', 'paid', 'confirmed', 'cancelled', 'refunded');
    END IF;
END $$;

-- =====================================================
-- 核心表结构创建
-- =====================================================

-- 1. 用户表（增强安全版）
CREATE TABLE IF NOT EXISTS users (
    -- 主键（统一使用 gen_random_uuid()）
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 基本信息
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    password_salt VARCHAR(32) NOT NULL DEFAULT gen_salt('bf', 12),
    password_iterations INTEGER NOT NULL DEFAULT 12,
    full_name VARCHAR(100),

    -- 角色和权限
    role user_role_enum NOT NULL DEFAULT 'media_buyer',
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_superuser BOOLEAN NOT NULL DEFAULT false,
    email_verified BOOLEAN NOT NULL DEFAULT false,

    -- 安全字段
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    account_locked_until TIMESTAMPTZ,
    password_changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,

    -- 联系信息
    phone VARCHAR(20),
    avatar_url TEXT,

    -- 管理信息
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 约束
    CONSTRAINT users_email_check CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT users_username_check CHECK (username ~* '^[a-zA-Z0-9_]{3,50}$'),
    CONSTRAINT users_phone_check CHECK (phone IS NULL OR phone ~* '^\+?[1-9]\d{1,14}$')
);

-- 2. 用户配置表
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 组织信息
    department VARCHAR(50),
    position VARCHAR(50),

    -- 偏好设置
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'zh-CN',
    theme VARCHAR(20) DEFAULT 'light',
    preferences JSONB DEFAULT '{}',

    -- 个人信息
    bio TEXT,

    -- 管理信息
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(user_id)
);

-- 3. 会话表（增强安全版）
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 认证信息
    token_hash VARCHAR(255) NOT NULL,
    refresh_token_hash VARCHAR(255),
    session_token VARCHAR(255) UNIQUE NOT NULL DEFAULT encode(gen_random_bytes(32), 'hex'),

    -- 设备信息
    ip_address INET,
    user_agent TEXT,
    device_fingerprint TEXT,

    -- 状态信息
    is_active BOOLEAN NOT NULL DEFAULT true,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 使用统计
    access_count INTEGER NOT NULL DEFAULT 0,

    -- 安全约束
    CONSTRAINT sessions_expires_check CHECK (expires_at > created_at),
    CONSTRAINT sessions_access_count_check CHECK (access_count >= 0)
);

-- 4. 项目表（状态机增强版）
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 基本信息
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,

    -- 客户信息
    client_name VARCHAR(100) NOT NULL,
    client_email VARCHAR(255),
    client_phone VARCHAR(20),

    -- 业务模式
    pricing_model VARCHAR(20) NOT NULL DEFAULT 'per_lead',
    lead_price NUMERIC(10, 2) NOT NULL CHECK (lead_price > 0),
    setup_fee NUMERIC(12, 2) DEFAULT 0 CHECK (setup_fee >= 0),
    currency VARCHAR(3) DEFAULT 'CNY',

    -- 项目状态（状态机）
    status project_status_enum NOT NULL DEFAULT 'draft',
    status_reason TEXT,
    status_changed_at TIMESTAMPTZ,

    -- 时间管理
    start_date DATE,
    end_date DATE,

    -- 预算控制
    monthly_budget NUMERIC(12, 2),
    total_budget NUMERIC(15, 2),
    monthly_target_leads INTEGER DEFAULT 0,
    target_cpl NUMERIC(10, 2),

    -- 统计数据（自动更新）
    total_accounts INTEGER DEFAULT 0,
    active_accounts INTEGER DEFAULT 0,
    total_spend NUMERIC(15, 2) DEFAULT 0,
    total_leads INTEGER DEFAULT 0,
    avg_cpl NUMERIC(10, 2),

    -- 人员分配
    owner_id UUID NOT NULL REFERENCES users(id),
    account_manager_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- 管理信息
    created_by UUID NOT NULL REFERENCES users(id),
    updated_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 约束
    CONSTRAINT projects_pricing_check CHECK (pricing_model IN ('per_lead', 'fixed_fee', 'hybrid')),
    CONSTRAINT projects_currency_check CHECK (currency ~* '^[A-Z]{3}$'),
    CONSTRAINT projects_date_check CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date),
    CONSTRAINT projects_budget_check CHECK (total_budget IS NULL OR monthly_budget IS NULL OR monthly_budget <= total_budget),
    CONSTRAINT projects_name_check CHECK (length(trim(name)) >= 2)
);

-- 5. 渠道表（质量评估版）
CREATE TABLE IF NOT EXISTS channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 基本信息
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    company_name VARCHAR(100) NOT NULL,

    -- 联系信息
    contact_person VARCHAR(100),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(20),
    contact_wechat VARCHAR(100),
    contact_qq VARCHAR(50),

    -- 费用结构
    service_fee_rate NUMERIC(5, 4) NOT NULL CHECK (service_fee_rate >= 0 AND service_fee_rate <= 1),
    account_setup_fee NUMERIC(10, 2) DEFAULT 0 CHECK (account_setup_fee >= 0),
    minimum_topup NUMERIC(10, 2) DEFAULT 0 CHECK (minimum_topup >= 0),

    -- 费用说明
    fee_structure JSONB DEFAULT '{}',
    payment_terms TEXT,

    -- 渠道状态
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    priority INTEGER DEFAULT 1 CHECK (priority BETWEEN 1 AND 10),

    -- 质量评估
    quality_score NUMERIC(3, 2) CHECK (quality_score >= 0 AND quality_score <= 10),
    reliability_score NUMERIC(3, 2) CHECK (reliability_score >= 0 AND reliability_score <= 10),
    price_competitiveness NUMERIC(3, 2) CHECK (price_competitiveness >= 0 AND price_competitiveness <= 10),

    -- 平台信息
    platform VARCHAR(50) NOT NULL,
    platform_account_id VARCHAR(100),

    -- 统计数据（自动更新）
    total_accounts INTEGER DEFAULT 0,
    active_accounts INTEGER DEFAULT 0,
    dead_accounts INTEGER DEFAULT 0,
    total_spend NUMERIC(15, 2) DEFAULT 0,

    -- 管理信息
    manager_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_by UUID NOT NULL REFERENCES users(id),
    updated_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 约束
    CONSTRAINT channels_status_check CHECK (status IN ('active', 'inactive', 'suspended', 'pending')),
    CONSTRAINT channels_platform_check CHECK (platform IN ('facebook', 'google', 'tiktok', 'bytedance', 'wechat', 'other'))
);

-- 6. 广告账户表（完整追溯版）
CREATE TABLE IF NOT EXISTS ad_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 基本信息
    account_id VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,

    -- 平台信息
    platform VARCHAR(50) NOT NULL,
    platform_account_id VARCHAR(100),
    platform_business_id VARCHAR(100),

    -- 关联信息（四层数据追溯核心）
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE RESTRICT,
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,  -- 修复：允许NULL，匹配ON DELETE SET NULL

    -- 账户状态（状态机）
    status account_status_enum NOT NULL DEFAULT 'new',
    status_reason TEXT,
    last_status_change TIMESTAMPTZ,

    -- 生命周期时间戳
    created_date DATE,
    activated_date DATE,
    suspended_date DATE,
    dead_date DATE,
    archived_date DATE,

    -- 预算管理
    daily_budget NUMERIC(10, 2),
    lifetime_budget NUMERIC(12, 2),
    remaining_budget NUMERIC(12, 2) DEFAULT 0,

    -- 账户配置
    currency VARCHAR(3) DEFAULT 'CNY',
    timezone VARCHAR(50) DEFAULT 'UTC',
    country VARCHAR(2),

    -- 性能数据（自动更新）
    total_spend NUMERIC(15, 2) DEFAULT 0,
    total_leads INTEGER DEFAULT 0,
    avg_cpl NUMERIC(10, 2),
    best_cpl NUMERIC(10, 2),
    today_spend NUMERIC(10, 2) DEFAULT 0,

    -- 开户费用
    setup_fee NUMERIC(10, 2) DEFAULT 0,
    setup_fee_paid BOOLEAN DEFAULT false,

    -- 账户类型和支付
    account_type VARCHAR(50),
    payment_method VARCHAR(50),
    billing_information JSONB DEFAULT '{}',

    -- 监控设置
    auto_monitoring BOOLEAN DEFAULT true,
    alert_thresholds JSONB DEFAULT '{}',

    -- 元数据
    notes TEXT,
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',

    -- 管理信息
    created_by UUID NOT NULL REFERENCES users(id),
    updated_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 约束
    CONSTRAINT ad_accounts_platform_check CHECK (platform IN ('facebook', 'google', 'tiktok', 'instagram', 'other')),
    CONSTRAINT ad_accounts_budget_check CHECK ((daily_budget IS NULL OR daily_budget > 0) AND (lifetime_budget IS NULL OR lifetime_budget > 0)),
    CONSTRAINT ad_accounts_spend_check CHECK (total_spend >= 0),
    CONSTRAINT ad_accounts_remaining_check CHECK (remaining_budget >= 0),
    CONSTRAINT ad_accounts_leads_check CHECK (total_leads >= 0),
    UNIQUE(platform, account_id)
);

-- 7. 项目成员表（权限管理版）
CREATE TABLE IF NOT EXISTS project_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 成员角色
    role VARCHAR(20) NOT NULL DEFAULT 'member',

    -- 权限配置
    permissions JSONB DEFAULT '{}',

    -- 加入信息
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    invited_by UUID REFERENCES users(id),

    -- 状态管理
    is_active BOOLEAN DEFAULT true,
    left_at TIMESTAMPTZ,
    leave_reason TEXT,

    -- 管理信息
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 约束
    CONSTRAINT project_members_role_check CHECK (role IN ('owner', 'manager', 'member', 'viewer')),
    UNIQUE(project_id, user_id)
);

-- 8. 日报表（数据质量版）
CREATE TABLE IF NOT EXISTS daily_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 关联信息（完整追溯）
    report_date DATE NOT NULL,
    account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    submitter_id UUID NOT NULL REFERENCES users(id),
    reviewer_id UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,

    -- 审核流程（状态机）
    status report_status_enum NOT NULL DEFAULT 'draft',
    rejection_reason TEXT,

    -- 基础数据
    spend NUMERIC(10, 2) NOT NULL DEFAULT 0,
    impressions INTEGER NOT NULL DEFAULT 0,
    clicks INTEGER NOT NULL DEFAULT 0,
    conversions INTEGER NOT NULL DEFAULT 0,
    revenue NUMERIC(10, 2) DEFAULT 0,

    -- 甲方确认数据
    leads_submitted INTEGER NOT NULL DEFAULT 0,
    leads_confirmed INTEGER,
    confirmed_at TIMESTAMPTZ,
    diff_reason TEXT,

    -- 计算字段（自动生成）
    cpm NUMERIC(10, 2) GENERATED ALWAYS AS (
        CASE WHEN impressions > 0 THEN ROUND((spend / impressions) * 1000, 2) ELSE NULL END
    ) STORED,
    cpc NUMERIC(10, 2) GENERATED ALWAYS AS (
        CASE WHEN clicks > 0 THEN ROUND(spend / clicks, 2) ELSE NULL END
    ) STORED,
    ctr NUMERIC(5, 2) GENERATED ALWAYS AS (
        CASE WHEN impressions > 0 THEN ROUND((clicks::FLOAT / impressions) * 100, 2) ELSE NULL END
    ) STORED,
    cpa NUMERIC(10, 2) GENERATED ALWAYS AS (
        CASE WHEN conversions > 0 THEN ROUND(spend / conversions, 2) ELSE NULL END
    ) STORED,
    roas NUMERIC(5, 2) GENERATED ALWAYS AS (
        CASE WHEN spend > 0 THEN ROUND(revenue / spend, 2) ELSE NULL END
    ) STORED,
    leads_diff INTEGER GENERATED ALWAYS AS (
        CASE WHEN leads_confirmed IS NOT NULL THEN leads_confirmed - leads_submitted ELSE NULL END
    ) STORED,

    -- 质量评估
    lead_quality_score NUMERIC(3, 2) CHECK (lead_quality_score >= 0 AND lead_quality_score <= 10),

    -- 审核时间戳
    submitted_at TIMESTAMPTZ,
    reviewed_at TIMESTAMPTZ,

    -- 附件和元数据
    attachments JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',

    -- 管理信息
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 约束
    CONSTRAINT daily_reports_spend_check CHECK (spend >= 0),
    CONSTRAINT daily_reports_impressions_check CHECK (impressions >= 0),
    CONSTRAINT daily_reports_clicks_check CHECK (clicks >= 0),
    CONSTRAINT daily_reports_conversions_check CHECK (conversions >= 0),
    CONSTRAINT daily_reports_revenue_check CHECK (revenue >= 0),
    CONSTRAINT daily_reports_leads_check CHECK (leads_submitted >= 0),
    CONSTRAINT daily_reports_date_check CHECK (report_date <= CURRENT_DATE),
    UNIQUE(report_date, account_id)
);

-- 9. 充值表（完整流程版）
CREATE TABLE IF NOT EXISTS topups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id VARCHAR(50) UNIQUE NOT NULL DEFAULT concat('TP', EXTRACT(EPOCH FROM NOW())::bigint),

    -- 关联信息（完整追溯）
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,  -- 保持CASCADE，业务需要
    channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE SET NULL,  -- 改为SET NULL
    account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE SET NULL,  -- 改为SET NULL
    requester_id UUID NOT NULL REFERENCES users(id),
    reviewer_id UUID REFERENCES users(id) ON DELETE SET NULL,
    approver_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- 审批流程（状态机）
    status topup_status_enum NOT NULL DEFAULT 'draft',
    urgency_level VARCHAR(20) DEFAULT 'normal',

    -- 金额信息
    amount NUMERIC(10, 2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(3) DEFAULT 'CNY',
    fee_rate NUMERIC(5, 4) NOT NULL DEFAULT 0.08 CHECK (fee_rate >= 0 AND fee_rate <= 1),
    fee_amount NUMERIC(10, 2) GENERATED ALWAYS AS (amount * fee_rate) STORED,
    total_amount NUMERIC(10, 2) GENERATED ALWAYS AS (amount + (amount * fee_rate)) STORED,

    -- 支付信息
    payment_method VARCHAR(50),
    payment_reference VARCHAR(100),
    bank_account VARCHAR(50),
    transaction_id VARCHAR(100),
    transaction_fee NUMERIC(10, 2) DEFAULT 0 CHECK (transaction_fee >= 0 AND transaction_fee <= amount * 0.1),

    -- 审批信息
    clerk_approval JSONB DEFAULT '{}',
    finance_approval JSONB DEFAULT '{}',
    rejection_reason TEXT,

    -- 时间戳（完整流程）
    requested_at TIMESTAMPTZ,
    reviewed_at TIMESTAMPTZ,
    approved_at TIMESTAMPTZ,
    paid_at TIMESTAMPTZ,
    confirmed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,

    -- 附件和说明
    attachments JSONB DEFAULT '[]',
    notes TEXT,
    metadata JSONB DEFAULT '{}',

    -- 管理信息
    created_by UUID NOT NULL REFERENCES users(id),
    updated_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 约束
    CONSTRAINT topups_urgency_check CHECK (urgency_level IN ('normal', 'urgent', 'emergency'))
);

-- 10. 对账表（财务审计版）
CREATE TABLE IF NOT EXISTS reconciliations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reconciliation_id VARCHAR(50) UNIQUE NOT NULL DEFAULT concat('RC', EXTRACT(EPOCH FROM NOW())::bigint),

    -- 关联信息
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,  -- 保持CASCADE，业务需要
    channel_id UUID REFERENCES channels(id) ON DELETE SET NULL,  -- 改为SET NULL
    account_id UUID REFERENCES ad_accounts(id) ON DELETE SET NULL,  -- 改为SET NULL

    -- 对账周期
    period_type VARCHAR(20) NOT NULL DEFAULT 'monthly',
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- 金额汇总
    total_spend NUMERIC(12, 2) NOT NULL DEFAULT 0,
    total_charges NUMERIC(12, 2) NOT NULL DEFAULT 0,
    total_adjustments NUMERIC(12, 2) NOT NULL DEFAULT 0,
    final_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'CNY',

    -- 费用分析
    service_fees NUMERIC(12, 2) DEFAULT 0,
    transaction_fees NUMERIC(12, 2) DEFAULT 0,
    other_fees NUMERIC(12, 2) DEFAULT 0,

    -- 对账状态（状态机）
    status VARCHAR(20) NOT NULL DEFAULT 'draft',

    -- 差异分析
    variance_amount NUMERIC(12, 2) DEFAULT 0,
    variance_percentage NUMERIC(5, 2) DEFAULT 0,
    variance_analysis JSONB DEFAULT '{}',
    dispute_reason TEXT,

    -- 审核信息
    reconciled_by UUID REFERENCES users(id) ON DELETE SET NULL,
    disputed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,

    -- 时间戳
    completed_at TIMESTAMPTZ,
    disputed_at TIMESTAMPTZ,
    approved_at TIMESTAMPTZ,

    -- 附件和明细
    attachments JSONB DEFAULT '[]',
    breakdown JSONB DEFAULT '{}',
    notes TEXT,

    -- 管理信息
    created_by UUID NOT NULL REFERENCES users(id),
    updated_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 约束
    CONSTRAINT reconciliations_status_check CHECK (status IN ('draft', 'pending', 'in_progress', 'completed', 'disputed', 'approved', 'archived')),
    CONSTRAINT reconciliations_period_check CHECK (period_end >= period_start),
    CONSTRAINT reconciliations_type_check CHECK (period_type IN ('daily', 'weekly', 'monthly', 'quarterly', 'yearly'))
);

-- 11. 审计日志表（增强追踪版）
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 操作信息
    event_type VARCHAR(50) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    user_email VARCHAR(255),
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,

    -- 资源信息
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    action VARCHAR(20) NOT NULL,

    -- 请求信息
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    endpoint TEXT,

    -- 变更数据
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[],
    details JSONB DEFAULT '{}',

    -- 执行结果
    success BOOLEAN NOT NULL DEFAULT true,
    error_message TEXT,
    error_code VARCHAR(50),

    -- 性能指标
    execution_time_ms INTEGER,
    affected_rows INTEGER DEFAULT 0,

    -- 严重程度
    level VARCHAR(20) DEFAULT 'medium',

    -- 审计信息
    batch_id UUID,
    parent_log_id UUID REFERENCES audit_logs(id) ON DELETE SET NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 约束
    CONSTRAINT audit_logs_action_check CHECK (action IN ('CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'VIEW', 'EXPORT', 'IMPORT', 'APPROVE', 'REJECT')),
    CONSTRAINT audit_logs_level_check CHECK (level IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT audit_logs_execution_time_check CHECK (execution_time_ms >= 0),
    CONSTRAINT audit_logs_affected_rows_check CHECK (affected_rows >= 0)
);

-- 12. 账户状态历史表（状态追踪版）
CREATE TABLE IF NOT EXISTS account_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 关联信息
    account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,

    -- 状态变更
    old_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    change_reason TEXT,

    -- 变更信息
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    changed_by UUID NOT NULL REFERENCES users(id),
    change_source VARCHAR(50) DEFAULT 'manual',
    ip_address INET,
    user_agent TEXT,

    -- 变更时快照
    performance_snapshot JSONB DEFAULT '{}',
    budget_snapshot JSONB DEFAULT '{}',
    metrics_snapshot JSONB DEFAULT '{}',

    -- 管理信息
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 约束
    CONSTRAINT account_status_change_source_check CHECK (change_source IN ('manual', 'automatic', 'system', 'api', 'batch'))
);

-- 13. 系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    is_encrypted BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 创建基础索引（高频查询必需）
-- =====================================================

-- 用户表基础索引
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- 用户配置索引
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);

-- 会话表基础索引
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_is_active ON sessions(is_active);

-- 项目表基础索引
CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at);
CREATE INDEX IF NOT EXISTS idx_projects_account_manager_id ON projects(account_manager_id);

-- 渠道表基础索引
CREATE INDEX IF NOT EXISTS idx_channels_code ON channels(code);
CREATE INDEX IF NOT EXISTS idx_channels_platform ON channels(platform);
CREATE INDEX IF NOT EXISTS idx_channels_status ON channels(status);

-- 广告账户表基础索引
CREATE INDEX IF NOT EXISTS idx_ad_accounts_project_id ON ad_accounts(project_id);
CREATE INDEX IF NOT EXISTS idx_ad_accounts_channel_id ON ad_accounts(channel_id);
CREATE INDEX IF NOT EXISTS idx_ad_accounts_assigned_to ON ad_accounts(assigned_to);
CREATE INDEX IF NOT EXISTS idx_ad_accounts_status ON ad_accounts(status);
CREATE INDEX IF NOT EXISTS idx_ad_accounts_platform ON ad_accounts(platform);
CREATE INDEX IF NOT EXISTS idx_ad_accounts_account_id ON ad_accounts(account_id);

-- 项目成员表索引
CREATE INDEX IF NOT EXISTS idx_project_members_project_id ON project_members(project_id);
CREATE INDEX IF NOT EXISTS idx_project_members_user_id ON project_members(user_id);
CREATE INDEX IF NOT EXISTS idx_project_members_role ON project_members(role);

-- 日报表基础索引（高频查询）
CREATE INDEX IF NOT EXISTS idx_daily_reports_account_id ON daily_reports(account_id);
CREATE INDEX IF NOT EXISTS idx_daily_reports_report_date ON daily_reports(report_date);
CREATE INDEX IF NOT EXISTS idx_daily_reports_status ON daily_reports(status);
CREATE INDEX IF NOT EXISTS idx_daily_reports_submitter_id ON daily_reports(submitter_id);
CREATE INDEX IF NOT EXISTS idx_daily_reports_reviewer_id ON daily_reports(reviewer_id);
-- 复合索引（核心查询）
CREATE INDEX IF NOT EXISTS idx_daily_reports_account_date ON daily_reports(account_id, report_date);

-- 充值表基础索引
CREATE INDEX IF NOT EXISTS idx_topups_project_id ON topups(project_id);
CREATE INDEX IF NOT EXISTS idx_topups_account_id ON topups(account_id);
CREATE INDEX IF NOT EXISTS idx_topups_requester_id ON topups(requester_id);
CREATE INDEX IF NOT EXISTS idx_topups_status ON topups(status);
CREATE INDEX IF NOT EXISTS idx_topups_created_at ON topups(created_at);
-- 复合索引（核心查询）
CREATE INDEX IF NOT EXISTS idx_topups_project_account_status ON topups(project_id, account_id, status);

-- 对账表基础索引
CREATE INDEX IF NOT EXISTS idx_reconciliations_project_id ON reconciliations(project_id);
CREATE INDEX IF NOT EXISTS idx_reconciliations_period ON reconciliations(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_reconciliations_status ON reconciliations(status);
CREATE INDEX IF NOT EXISTS idx_reconciliations_created_at ON reconciliations(created_at);

-- 审计日志基础索引
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);

-- 账户状态历史索引
CREATE INDEX IF NOT EXISTS idx_account_status_history_account_id ON account_status_history(account_id);
CREATE INDEX IF NOT EXISTS idx_account_status_history_changed_at ON account_status_history(changed_at);
CREATE INDEX IF NOT EXISTS idx_account_status_history_changed_by ON account_status_history(changed_by);

-- =====================================================
-- 创建函数和触发器
-- =====================================================

-- 1. 统一应用设置读取函数
CREATE OR REPLACE FUNCTION get_app_setting(key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN current_setting(key, true);
EXCEPTION WHEN others THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 2. 时间戳更新触发器
CREATE OR REPLACE FUNCTION trg_update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 批量创建更新触发器
DO $$
DECLARE
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'users', 'user_profiles', 'sessions', 'projects', 'channels',
        'ad_accounts', 'project_members', 'daily_reports', 'topups',
        'reconciliations', 'system_config'
    ]
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS trg_%I_updated_at ON %I', table_name, table_name);
        EXECUTE format('CREATE TRIGGER trg_%I_updated_at
                        BEFORE UPDATE ON %I
                        FOR EACH ROW EXECUTE FUNCTION trg_update_updated_at()',
                       table_name, table_name);
    END LOOP;
END $$;

-- 3. 密码安全函数
CREATE OR REPLACE FUNCTION validate_password_strength(password TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    -- 至少12个字符
    IF length(password) < 12 THEN
        RETURN FALSE;
    END IF;

    -- 包含大小写字母
    IF NOT (password ~* '[a-z]' AND password ~* '[A-Z]') THEN
        RETURN FALSE;
    END IF;

    -- 包含数字
    IF NOT (password ~* '[0-9]') THEN
        RETURN FALSE;
    END IF;

    -- 包含特殊字符
    IF NOT (password ~* '[!@#$%^&*(),.?":{}|<>]') THEN
        RETURN FALSE;
    END IF;

    -- 不包含连续重复字符
    IF password ~* '(.)\1{2,}' THEN
        RETURN FALSE;
    END IF;

    -- 不包含常见弱密码
    IF password ~* '^(password|123456|qwerty|admin|letmein)' THEN
        RETURN FALSE;
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 增强密码哈希（PBKDF2）
CREATE OR REPLACE FUNCTION hash_password_secure(password TEXT)
RETURNS TABLE(password_hash TEXT, password_salt TEXT, iterations INTEGER) AS $$
DECLARE
    v_salt TEXT := encode(gen_random_bytes(32), 'hex');
    v_iterations INTEGER := 100000;
    v_hash TEXT;
BEGIN
    v_hash := encode(pbkdf2_hmac('sha256', password::bytea, v_salt::bytea, v_iterations), 'hex');
    RETURN QUERY SELECT v_hash, v_salt, v_iterations;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 密码验证
CREATE OR REPLACE FUNCTION verify_password_secure(password TEXT, stored_hash TEXT, salt TEXT, iterations INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    computed_hash TEXT;
BEGIN
    computed_hash := encode(pbkdf2_hmac('sha256', password::bytea, salt::bytea, iterations), 'hex');
    RETURN (computed_hash = stored_hash);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 4. 状态机验证函数
CREATE OR REPLACE FUNCTION validate_project_status_transition(
    current_status TEXT,
    new_status TEXT,
    user_role TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
BEGIN
    CASE
        WHEN current_status = 'draft' THEN
            RETURN new_status IN ('active', 'cancelled');
        WHEN current_status = 'active' THEN
            RETURN new_status IN ('paused', 'completed', 'cancelled');
        WHEN current_status = 'paused' THEN
            RETURN new_status IN ('active', 'completed', 'cancelled');
        WHEN current_status = 'completed' THEN
            RETURN new_status IN ('archived');
        WHEN current_status = 'cancelled' THEN
            RETURN new_status IN ('draft', 'archived');
        ELSE
            RETURN FALSE;
    END CASE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 账户状态转换验证
CREATE OR REPLACE FUNCTION validate_account_status_transition(
    current_status TEXT,
    new_status TEXT,
    user_role TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
BEGIN
    CASE
        WHEN current_status = 'draft' THEN
            RETURN new_status IN ('new', 'cancelled');
        WHEN current_status = 'new' THEN
            RETURN new_status IN ('testing', 'cancelled');
        WHEN current_status = 'testing' THEN
            RETURN new_status IN ('active', 'suspended', 'dead');
        WHEN current_status = 'active' THEN
            RETURN new_status IN ('paused', 'suspended', 'dead');
        WHEN current_status = 'suspended' THEN
            RETURN new_status IN ('active', 'dead');
        WHEN current_status = 'dead' THEN
            RETURN new_status IN ('archived');
        WHEN current_status = 'archived' THEN
            RETURN FALSE;
        ELSE
            RETURN FALSE;
    END CASE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 5. 业务逻辑触发器
-- 账户状态变更触发器
CREATE OR REPLACE FUNCTION trg_account_status_change()
RETURNS TRIGGER AS $$
BEGIN
    -- 记录状态变更历史
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        -- 验证状态转换
        IF NOT validate_account_status_transition(OLD.status, NEW.status) THEN
            RAISE EXCEPTION 'Invalid status transition from % to %', OLD.status, NEW.status;
        END IF;

        -- 记录历史
        INSERT INTO account_status_history (
            account_id,
            old_status,
            new_status,
            change_reason,
            changed_by,
            performance_snapshot,
            budget_snapshot
        ) VALUES (
            NEW.id,
            OLD.status,
            NEW.status,
            NEW.status_reason,
            NEW.updated_by,
            jsonb_build_object(
                'total_spend', NEW.total_spend,
                'total_leads', NEW.total_leads,
                'avg_cpl', NEW.avg_cpl
            ),
            jsonb_build_object(
                'daily_budget', NEW.daily_budget,
                'remaining_budget', NEW.remaining_budget
            )
        );

        -- 更新状态时间戳
        NEW.last_status_change = NOW();

        -- 更新特定状态时间戳
        CASE NEW.status
            WHEN 'active' THEN
                NEW.activated_date = CURRENT_DATE;
            WHEN 'suspended' THEN
                NEW.suspended_date = CURRENT_DATE;
            WHEN 'dead' THEN
                NEW.dead_date = CURRENT_DATE;
            WHEN 'archived' THEN
                NEW.archived_date = CURRENT_DATE;
        END CASE;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建账户状态触发器
DROP TRIGGER IF EXISTS trg_ad_accounts_status_change ON ad_accounts;
CREATE TRIGGER trg_ad_accounts_status_change
    BEFORE UPDATE ON ad_accounts
    FOR EACH ROW
    WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION trg_account_status_change();

-- 6. 统计更新触发器（修复业务逻辑错误）
-- 项目统计自动更新函数
CREATE OR REPLACE FUNCTION update_project_statistics()
RETURNS TRIGGER AS $$
BEGIN
    -- 更新账户统计
    UPDATE projects SET
        total_accounts = (
            SELECT COUNT(*) FROM ad_accounts
            WHERE project_id = COALESCE(NEW.project_id, OLD.project_id)
        ),
        active_accounts = (
            SELECT COUNT(*) FROM ad_accounts
            WHERE project_id = COALESCE(NEW.project_id, OLD.project_id)
            AND status IN ('active', 'testing')
        ),
        total_spend = COALESCE((
            -- 修复：通过账户关联查询日报表
            SELECT SUM(dr.spend) FROM daily_reports dr
            JOIN ad_accounts a ON dr.account_id = a.id
            WHERE a.project_id = COALESCE(NEW.project_id, OLD.project_id)
        ), 0),
        total_leads = COALESCE((
            -- 修复：通过账户关联查询日报表
            SELECT SUM(dr.leads_confirmed) FROM daily_reports dr
            JOIN ad_accounts a ON dr.account_id = a.id
            WHERE a.project_id = COALESCE(NEW.project_id, OLD.project_id)
            AND dr.leads_confirmed IS NOT NULL
        ), 0),
        avg_cpl = CASE
            WHEN COALESCE((
                SELECT SUM(dr.leads_confirmed) FROM daily_reports dr
                JOIN ad_accounts a ON dr.account_id = a.id
                WHERE a.project_id = COALESCE(NEW.project_id, OLD.project_id)
                AND dr.leads_confirmed IS NOT NULL
            ), 0) > 0
            THEN COALESCE((
                SELECT SUM(dr.spend) FROM daily_reports dr
                JOIN ad_accounts a ON dr.account_id = a.id
                WHERE a.project_id = COALESCE(NEW.project_id, OLD.project_id)
            ), 0) / (
                SELECT SUM(dr.leads_confirmed) FROM daily_reports dr
                JOIN ad_accounts a ON dr.account_id = a.id
                WHERE a.project_id = COALESCE(NEW.project_id, OLD.project_id)
                AND dr.leads_confirmed IS NOT NULL
            )
            ELSE NULL
        END
    WHERE id = COALESCE(NEW.project_id, OLD.project_id);

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 创建统计更新触发器
DROP TRIGGER IF EXISTS trg_update_project_stats_on_account ON ad_accounts;
CREATE TRIGGER trg_update_project_stats_on_account
    AFTER INSERT OR UPDATE OR DELETE ON ad_accounts
    FOR EACH STATEMENT
    EXECUTE FUNCTION update_project_statistics();

DROP TRIGGER IF EXISTS trg_update_project_stats_on_daily_report ON daily_reports;
CREATE TRIGGER trg_update_project_stats_on_daily_report
    AFTER INSERT OR UPDATE ON daily_reports
    FOR EACH STATEMENT
    EXECUTE FUNCTION update_project_statistics();

-- =====================================================
-- 创建视图（修复字段引用错误）
-- =====================================================

-- 项目仪表板视图
CREATE OR REPLACE VIEW project_dashboard AS
SELECT
    p.id,
    p.name,
    p.client_name,
    p.status,
    p.pricing_model,
    p.lead_price,
    p.currency,

    -- 账户统计
    p.total_accounts,
    p.active_accounts,
    ROUND(
        (p.active_accounts::NUMERIC / NULLIF(p.total_accounts, 0)) * 100, 2
    ) as account_activation_rate,

    -- 财务统计
    p.total_spend,
    p.total_leads,
    p.avg_cpl,
    p.setup_fee + (p.total_leads * p.lead_price) as total_revenue,
    (p.setup_fee + (p.total_leads * p.lead_price)) - p.total_spend as profit,
    CASE
        WHEN p.total_spend > 0 THEN
            ROUND(((p.setup_fee + (p.total_leads * p.lead_price)) - p.total_spend) / p.total_spend * 100, 2)
        ELSE 0
    END as profit_margin,

    -- 预算控制
    p.monthly_budget,
    p.total_budget,
    CASE
        WHEN p.monthly_budget > 0 THEN
            ROUND(p.total_spend / p.monthly_budget * 100, 2)
        ELSE 0
    END as budget_utilization,

    -- 时间信息
    p.start_date,
    p.end_date,
    p.created_at,
    p.updated_at,

    -- 人员信息
    owner.full_name as owner_name,
    manager.full_name as manager_name,

    -- 性能评级
    CASE
        WHEN p.avg_cpl <= p.target_cpl * 0.9 THEN 'excellent'
        WHEN p.avg_cpl <= p.target_cpl THEN 'good'
        WHEN p.avg_cpl <= p.target_cpl * 1.2 THEN 'average'
        ELSE 'poor'
    END as performance_rating

FROM projects p
LEFT JOIN users owner ON p.owner_id = owner.id
LEFT JOIN users manager ON p.account_manager_id = manager.id;

-- 用户工作台视图（修复字段引用错误）
CREATE OR REPLACE VIEW user_workbench AS
SELECT
    u.id,
    u.full_name,
    u.email,
    u.role,
    up.department,  -- 修复：从user_profiles表获取
    up.position,    -- 修复：从user_profiles表获取
    u.last_login_at,

    -- 账户管理
    COUNT(DISTINCT a.id) as total_accounts,
    COUNT(DISTINCT CASE WHEN a.status = 'active' THEN a.id END) as active_accounts,
    COUNT(DISTINCT CASE WHEN a.status IN ('new', 'testing') THEN a.id END) as pending_accounts,

    -- 今日工作量
    COUNT(DISTINCT CASE WHEN dr.report_date = CURRENT_DATE THEN dr.id END) as today_reports,
    COALESCE(SUM(CASE WHEN dr.report_date = CURRENT_DATE THEN dr.spend END), 0) as today_spend,
    COALESCE(SUM(CASE WHEN dr.report_date = CURRENT_DATE THEN dr.leads_submitted END), 0) as today_leads,

    -- 本月统计
    COALESCE(SUM(CASE WHEN dr.report_date >= date_trunc('month', CURRENT_DATE) THEN dr.spend END), 0) as month_spend,
    COALESCE(SUM(CASE WHEN dr.report_date >= date_trunc('month', CURRENT_DATE) THEN dr.leads_submitted END), 0) as month_leads,
    CASE
        WHEN COALESCE(SUM(CASE WHEN dr.report_date >= date_trunc('month', CURRENT_DATE) THEN dr.leads_submitted END), 0) > 0
        THEN ROUND(
            COALESCE(SUM(CASE WHEN dr.report_date >= date_trunc('month', CURRENT_DATE) THEN dr.spend END), 0) /
            SUM(CASE WHEN dr.report_date >= date_trunc('month', CURRENT_DATE) THEN dr.leads_submitted END), 2
        )
        ELSE 0
    END as month_cpl,

    -- 充值统计
    COUNT(DISTINCT t.id) as total_topups,
    COALESCE(SUM(t.amount), 0) as total_topup_amount,
    COUNT(DISTINCT CASE WHEN t.status = 'pending_review' THEN t.id END) as pending_topups,
    COUNT(DISTINCT CASE WHEN t.status = 'confirmed' THEN t.id END) as completed_topups,

    -- 审核任务
    COUNT(DISTINCT CASE WHEN dr.status = 'submitted' AND dr.reviewer_id = u.id THEN dr.id END) as pending_reviews,
    COUNT(DISTINCT CASE WHEN t.status = 'pending_review' AND t.reviewer_id = u.id THEN t.id END) as pending_approvals,

    -- 效率指标
    ROUND(AVG(CASE WHEN dr.report_date >= date_trunc('month', CURRENT_DATE) THEN dr.lead_quality_score END), 2) as avg_quality_score,
    CASE
        WHEN COUNT(DISTINCT CASE WHEN dr.report_date >= date_trunc('month', CURRENT_DATE) THEN dr.id END) > 0
        THEN COUNT(DISTINCT CASE WHEN dr.report_date >= date_trunc('month', CURRENT_DATE) AND dr.status = 'approved' THEN dr.id END) /
             COUNT(DISTINCT CASE WHEN dr.report_date >= date_trunc('month', CURRENT_DATE) THEN dr.id END) * 100
        ELSE 0
    END as approval_rate,

    -- 活跃度
    COUNT(DISTINCT DATE(dr.report_date)) as active_days,
    EXTRACT(DAYS FROM (CURRENT_DATE - MIN(dr.report_date))) as tracking_days,

    -- 工作负载
    CASE
        WHEN COUNT(DISTINCT a.id) > 20 THEN 'high'
        WHEN COUNT(DISTINCT a.id) > 10 THEN 'medium'
        ELSE 'low'
    END as workload_level,

    -- 时间范围
    MIN(dr.report_date) as first_report_date,
    MAX(dr.report_date) as last_report_date,
    u.created_at as join_date

FROM users u
LEFT JOIN user_profiles up ON u.id = up.user_id  -- 修复：添加JOIN获取department和position
LEFT JOIN ad_accounts a ON u.id = a.assigned_to
LEFT JOIN daily_reports dr ON a.id = dr.account_id
LEFT JOIN topups t ON u.id = t.requester_id
WHERE u.is_active = true
GROUP BY u.id, u.full_name, u.email, u.role, up.department, up.position, u.last_login_at, u.created_at;

-- =====================================================
-- 插入初始数据（在开启RLS之前）
-- =====================================================

-- 插入系统配置
INSERT INTO system_config (config_key, config_value, description) VALUES
('password_policy', '{"min_length": 12, "require_special": true, "require_numbers": true, "require_mixed_case": true, "max_failed_attempts": 5, "lockout_duration": 1800}', '密码安全策略'),
('session_settings', '{"timeout_hours": 24, "max_concurrent": 3, "require_ip_verification": false}', '会话管理设置'),
('file_upload', '{"max_size_mb": 10, "allowed_types": ["jpg", "png", "pdf", "xlsx", "csv"], "virus_scan": true}', '文件上传限制'),
('notification_settings', '{"email_enabled": true, "sms_enabled": false, "slack_webhook": null}', '通知系统配置'),
('backup_settings', '{"auto_backup": true, "retention_days": 30, "backup_time": "02:00"}', '数据备份设置')
ON CONFLICT (config_key) DO NOTHING;

-- 创建默认管理员用户（使用增强密码安全）
WITH secure_admin_password AS (
    SELECT * FROM hash_password_secure('Admin@2024!SecurePass')
)
INSERT INTO users (
    id,
    email,
    username,
    password_hash,
    password_salt,
    password_iterations,
    full_name,
    role,
    is_active,
    is_superuser,
    email_verified
)
SELECT
    gen_random_uuid(),
    'admin@aiad.com',
    'admin',
    password_hash,
    password_salt,
    iterations,
    '系统管理员',
    'admin',
    true,
    true,
    true
FROM secure_admin_password
ON CONFLICT (email) DO NOTHING;

-- 创建管理员配置
INSERT INTO user_profiles (user_id, department, position, preferences)
SELECT
    u.id,
    'IT',
    '系统管理员',
    '{"theme": "light", "notifications": {"email": true, "browser": true}, "dashboard": {"widgets": ["stats", "charts", "alerts"]}}'
FROM users u
WHERE u.username = 'admin'
ON CONFLICT (user_id) DO NOTHING;

-- 创建示例角色用户
INSERT INTO users (id, email, username, password_hash, password_salt, password_iterations, full_name, role, is_active, email_verified)
SELECT
    gen_random_uuid(),
    'finance@aiad.com',
    'finance_demo',
    (SELECT password_hash FROM hash_password_secure('Finance@2024!Demo') LIMIT 1),
    (SELECT password_salt FROM hash_password_secure('Finance@2024!Demo') LIMIT 1),
    100000,
    '财务专员',
    'finance',
    true,
    true
ON CONFLICT (email) DO NOTHING;

INSERT INTO users (id, email, username, password_hash, password_salt, password_iterations, full_name, role, is_active, email_verified)
SELECT
    gen_random_uuid(),
    'operator@aiad.com',
    'operator_demo',
    (SELECT password_hash FROM hash_password_secure('Operator@2024!Demo') LIMIT 1),
    (SELECT password_salt FROM hash_password_secure('Operator@2024!Demo') LIMIT 1),
    100000,
    '数据操作员',
    'data_operator',
    true,
    true
ON CONFLICT (email) DO NOTHING;

INSERT INTO users (id, email, username, password_hash, password_salt, password_iterations, full_name, role, is_active, email_verified)
SELECT
    gen_random_uuid(),
    'manager@aiad.com',
    'manager_demo',
    (SELECT password_hash FROM hash_password_secure('Manager@2024!Demo') LIMIT 1),
    (SELECT password_salt FROM hash_password_secure('Manager@2024!Demo') LIMIT 1),
    100000,
    '项目经理',
    'account_manager',
    true,
    true
ON CONFLICT (email) DO NOTHING;

INSERT INTO users (id, email, username, password_hash, password_salt, password_iterations, full_name, role, is_active, email_verified)
SELECT
    gen_random_uuid(),
    'buyer@aiad.com',
    'buyer_demo',
    (SELECT password_hash FROM hash_password_secure('Buyer@2024!Demo') LIMIT 1),
    (SELECT password_salt FROM hash_password_secure('Buyer@2024!Demo') LIMIT 1),
    100000,
    '广告投手',
    'media_buyer',
    true,
    true
ON CONFLICT (email) DO NOTHING;

-- 创建示例渠道
INSERT INTO channels (id, name, code, company_name, platform, service_fee_rate, contact_person, contact_email, status, created_by)
SELECT
    gen_random_uuid(),
    'Facebook广告渠道',
    'fb_channel_001',
    '优质广告有限公司',
    'facebook',
    0.08,
    '张经理',
    'contact@channel-a.com',
    'active',
    u.id
FROM users u
WHERE u.username = 'admin'
ON CONFLICT (code) DO NOTHING;

INSERT INTO channels (id, name, code, company_name, platform, service_fee_rate, contact_person, contact_email, status, created_by)
SELECT
    gen_random_uuid(),
    'Google Ads渠道',
    'google_channel_001',
    'Google广告代理',
    'google',
    0.10,
    '李经理',
    'contact@channel-b.com',
    'active',
    u.id
FROM users u
WHERE u.username = 'admin'
ON CONFLICT (code) DO NOTHING;

-- 创建示例项目
INSERT INTO projects (id, name, code, client_name, client_email, pricing_model, lead_price, setup_fee, status, owner_id, created_by)
SELECT
    gen_random_uuid(),
    'AI广告代投演示项目',
    'DEMO_PROJ_001',
    '演示客户公司',
    'demo@client.com',
    'per_lead',
    50.00,
    5000.00,
    'active',
    u.id,
    u.id
FROM users u
WHERE u.username = 'admin'
ON CONFLICT (code) DO NOTHING;

-- =====================================================
-- RLS安全策略配置
-- =====================================================

-- 创建认证用户角色
CREATE ROLE IF NOT EXISTS authenticated_user;
GRANT USAGE ON SCHEMA public TO authenticated_user;

-- 创建安全上下文函数（使用统一的get_app_setting）
CREATE OR REPLACE FUNCTION get_current_user_context()
RETURNS TABLE(user_id UUID, role TEXT, session_valid BOOLEAN) AS $$
DECLARE
    v_user_id TEXT;
    v_role TEXT;
    v_session_valid BOOLEAN := FALSE;
BEGIN
    -- 获取当前用户ID
    v_user_id := get_app_setting('app.current_user_id');

    -- 验证会话有效性
    IF v_user_id IS NOT NULL THEN
        SELECT u.role, s.is_valid
        INTO v_role, v_session_valid
        FROM users u
        JOIN (
            SELECT user_id,
                   CASE WHEN expires_at > NOW() AND is_active = true THEN true ELSE false END as is_valid
            FROM sessions
            WHERE token_hash = get_app_setting('app.session_token')
            ORDER BY created_at DESC LIMIT 1
        ) s ON u.id = s.user_id
        WHERE u.id = v_user_id::UUID AND u.is_active = true;
    END IF;

    RETURN QUERY SELECT v_user_id::UUID, v_role, COALESCE(v_session_valid, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 启用所有表的RLS
DO $$
DECLARE
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'users', 'user_profiles', 'sessions', 'projects', 'channels',
        'ad_accounts', 'project_members', 'daily_reports', 'topups',
        'reconciliations', 'audit_logs', 'account_status_history'
    ]
    LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', table_name);
    END LOOP;
END $$;

-- 用户表RLS策略（优化：普通用户不能看到所有管理员）
DROP POLICY IF EXISTS pl_users_own_profile ON users;
CREATE POLICY pl_users_own_profile ON users
    FOR ALL
    TO authenticated_user
    USING (
        id = (SELECT user_id FROM get_current_user_context())
        OR (SELECT role FROM get_current_user_context()) = 'admin' AND is_superuser = true
    );

DROP POLICY IF EXISTS pl_users_public_read ON users;
CREATE POLICY pl_users_public_read ON users
    FOR SELECT
    TO authenticated_user
    USING (
        -- 只有管理员才能看到所有用户
        (SELECT role FROM get_current_user_context()) = 'admin'
    );

-- 用户配置访问策略
DROP POLICY IF EXISTS pl_user_profiles_own ON user_profiles;
CREATE POLICY pl_user_profiles_own ON user_profiles
    FOR ALL
    TO authenticated_user
    USING (
        user_id = (SELECT user_id FROM get_current_user_context())
        OR (SELECT role FROM get_current_user_context()) IN ('admin', 'account_manager')
    );

-- 项目表RLS策略
DROP POLICY IF EXISTS pl_projects_access ON projects;
CREATE POLICY pl_projects_access ON projects
    FOR ALL
    TO authenticated_user
    USING (
        -- 管理员全权限
        (SELECT role FROM get_current_user_context()) = 'admin'
        OR
        -- 项目经理
        owner_id = (SELECT user_id FROM get_current_user_context())
        OR
        -- 客户经理
        account_manager_id = (SELECT user_id FROM get_current_user_context())
        OR
        -- 项目成员
        EXISTS (
            SELECT 1 FROM project_members
            WHERE project_id = projects.id
            AND user_id = (SELECT user_id FROM get_current_user_context())
            AND is_active = true
        )
        OR
        -- 分配了账户的投手
        EXISTS (
            SELECT 1 FROM ad_accounts
            WHERE project_id = projects.id
            AND assigned_to = (SELECT user_id FROM get_current_user_context())
            AND status IN ('active', 'testing')
        )
    );

-- 日报表RLS策略
DROP POLICY IF EXISTS pl_daily_reports_access ON daily_reports;
CREATE POLICY pl_daily_reports_access ON daily_reports
    FOR ALL
    TO authenticated_user
    USING (
        -- 管理员
        (SELECT role FROM get_current_user_context()) = 'admin'
        OR
        -- 数据操作员
        (SELECT role FROM get_current_user_context()) = 'data_operator'
        OR
        -- 财务
        (SELECT role FROM get_current_user_context()) = 'finance'
        OR
        -- 自己提交的日报
        submitter_id = (SELECT user_id FROM get_current_user_context())
        OR
        -- 分配给自己的账户
        EXISTS (
            SELECT 1 FROM ad_accounts
            WHERE id = daily_reports.account_id
            AND assigned_to = (SELECT user_id FROM get_current_user_context())
        )
    );

-- 授予认证用户基本权限
DO $$
DECLARE
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'users', 'user_profiles', 'sessions', 'projects', 'channels',
        'ad_accounts', 'project_members', 'daily_reports', 'topups',
        'reconciliations', 'audit_logs', 'account_status_history', 'system_config'
    ]
    LOOP
        EXECUTE format('GRANT SELECT ON TABLE %I TO authenticated_user', table_name);
        EXECUTE format('GRANT INSERT ON TABLE %I TO authenticated_user', table_name);
        EXECUTE format('GRANT UPDATE ON TABLE %I TO authenticated_user', table_name);
        EXECUTE format('GRANT DELETE ON TABLE %I TO authenticated_user', table_name);
    END LOOP;
END $$;

-- =====================================================
-- 创建完成报告
-- =====================================================

DO $$
DECLARE
    table_count INTEGER;
    index_count INTEGER;
    policy_count INTEGER;
    trigger_count INTEGER;
    function_count INTEGER;
    view_count INTEGER;
    user_count INTEGER;
    project_count INTEGER;
    channel_count INTEGER;
BEGIN
    -- 统计创建的对象数量
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE schemaname = 'public' AND indexname LIKE 'idx_%';

    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public';

    SELECT COUNT(*) INTO trigger_count
    FROM information_schema.triggers
    WHERE trigger_schema = 'public';

    SELECT COUNT(*) INTO function_count
    FROM pg_proc
    WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
    AND NOT proname LIKE 'pg_%';

    SELECT COUNT(*) INTO view_count
    FROM information_schema.views
    WHERE table_schema = 'public';

    SELECT COUNT(*) INTO user_count FROM users;
    SELECT COUNT(*) INTO project_count FROM projects;
    SELECT COUNT(*) INTO channel_count FROM channels;

    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'AI广告代投系统数据库 v2.4 创建完成！';
    RAISE NOTICE '';
    RAISE NOTICE '📊 数据库对象统计：';
    RAISE NOTICE '   - 数据表: % 个', table_count;
    RAISE NOTICE '   - 索引: % 个（核心索引）', index_count;
    RAISE NOTICE '   - RLS策略: % 个', policy_count;
    RAISE NOTICE '   - 触发器: % 个', trigger_count;
    RAISE NOTICE '   - 函数: % 个', function_count;
    RAISE NOTICE '   - 视图: % 个', view_count;
    RAISE NOTICE '';
    RAISE NOTICE '🎯 初始数据统计：';
    RAISE NOTICE '   - 用户数: % 个', user_count;
    RAISE NOTICE '   - 项目数: % 个', project_count;
    RAISE NOTICE '   - 渠道数: % 个', channel_count;
    RAISE NOTICE '';
    RAISE NOTICE '🔧 v2.4 优化内容：';
    RAISE NOTICE '   ✅ 修复语法问题（RAISE NOTICE包装）';
    RAISE NOTICE '   ✅ 移除CONCURRENTLY避免事务冲突';
    RAISE NOTICE '   ✅ 修复业务逻辑错误（统计函数、视图）';
    RAISE NOTICE '   ✅ 优化RLS安全策略（会话验证）';
    RAISE NOTICE '   ✅ 统一主键生成（gen_random_uuid）';
    RAISE NOTICE '   ✅ 调整外键删除策略（财务数据保护）';
    RAISE NOTICE '';
    RAISE NOTICE '👤 默认管理员账号：';
    RAISE NOTICE '   邮箱: admin@aiad.com';
    RAISE NOTICE '   密码: Admin@2024!SecurePass';
    RAISE NOTICE '   用户名: admin';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 测试账号：';
    RAISE NOTICE '   - finance_demo / Finance@2024!Demo (财务)';
    RAISE NOTICE '   - operator_demo / Operator@2024!Demo (数据员)';
    RAISE NOTICE '   - manager_demo / Manager@2024!Demo (项目经理)';
    RAISE NOTICE '   - buyer_demo / Buyer@2024!Demo (投手)';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  重要提示：';
    RAISE NOTICE '   1. 请立即修改默认密码！';
    RAISE NOTICE '   2. 分析型索引请运行 05_indexes.sql';
    RAISE NOTICE '   3. 生产环境请使用05_indexes.sql中的CONCURRENTLY索引';
    RAISE NOTICE '========================================';
END $$;