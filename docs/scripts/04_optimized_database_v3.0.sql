-- =====================================================
-- AI广告代投系统数据库结构 - 优化版 v3.0
-- 根据设计缺陷分析全面优化
-- 更新日期: 2025-01-11
-- =====================================================

-- 设置时区
SET TIME ZONE 'UTC';

-- 创建必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- 1. 删除所有现有表（按依赖关系倒序）
-- =====================================================

DO $$
DECLARE
    tbl RECORD;
BEGIN
    -- 禁用所有外键约束
    ALTER TABLE IF EXISTS ledgers DROP CONSTRAINT IF EXISTS ledgers_project_id_fkey;
    ALTER TABLE IF EXISTS ledgers DROP CONSTRAINT IF EXISTS ledgers_topup_id_fkey;
    ALTER TABLE IF EXISTS ledgers DROP CONSTRAINT IF EXISTS ledgers_ad_account_id_fkey;
    ALTER TABLE IF EXISTS reconciliations DROP CONSTRAINT IF EXISTS reconciliations_project_id_fkey;
    ALTER TABLE IF EXISTS ad_spend_daily DROP CONSTRAINT IF EXISTS ad_spend_daily_project_id_fkey;
    ALTER TABLE IF EXISTS ad_spend_daily DROP CONSTRAINT IF EXISTS ad_spend_daily_ad_account_id_fkey;
    ALTER TABLE IF EXISTS ad_spend_daily DROP CONSTRAINT IF EXISTS ad_spend_daily_user_id_fkey;
    ALTER TABLE IF EXISTS topups DROP CONSTRAINT IF EXISTS topups_project_id_fkey;
    ALTER TABLE IF EXISTS topups DROP CONSTRAINT IF EXISTS topups_ad_account_id_fkey;
    ALTER TABLE IF EXISTS topups DROP CONSTRAINT IF EXISTS topups_requested_by_fkey;
    ALTER TABLE IF EXISTS account_status_history DROP CONSTRAINT IF EXISTS account_status_history_account_id_fkey;
    ALTER TABLE IF EXISTS ad_accounts DROP CONSTRAINT IF EXISTS ad_accounts_project_id_fkey;
    ALTER TABLE IF EXISTS ad_accounts DROP CONSTRAINT IF EXISTS ad_accounts_channel_id_fkey;
    ALTER TABLE IF EXISTS ad_accounts DROP CONSTRAINT IF EXISTS ad_accounts_assigned_user_id_fkey;
    ALTER TABLE IF EXISTS projects DROP CONSTRAINT IF EXISTS projects_manager_id_fkey;
    ALTER TABLE IF EXISTS projects DROP CONSTRAINT IF EXISTS projects_created_by_fkey;
    ALTER TABLE IF EXISTS channels DROP CONSTRAINT IF EXISTS channels_created_by_fkey;

    -- 删除所有表
    FOR tbl IN
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY CASE table_name
            WHEN 'audit_logs' THEN 1
            WHEN 'import_jobs' THEN 2
            WHEN 'performance_metrics' THEN 3
            WHEN 'batch_operations' THEN 4
            WHEN 'data_versions' THEN 5
            WHEN 'status_history' THEN 6
            WHEN 'ledgers' THEN 7
            WHEN 'reconciliations' THEN 8
            WHEN 'ad_spend_daily' THEN 9
            WHEN 'topups' THEN 10
            WHEN 'account_status_history' THEN 11
            WHEN 'ad_accounts' THEN 12
            WHEN 'channels' THEN 13
            WHEN 'projects' THEN 14
            WHEN 'users' THEN 15
            ELSE 100
        END
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(tbl.table_name) || ' CASCADE';
        RAISE NOTICE '删除表: %', tbl.table_name;
    END LOOP;
END $$;

-- =====================================================
-- 2. 创建核心表结构（优化版）
-- =====================================================

-- 2.1 用户表 (优化版)
CREATE TABLE public.users (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 基本信息
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,  -- 使用 bcrypt，包含 salt 和 rounds
    full_name VARCHAR(255),

    -- 角色和权限
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'manager', 'data_clerk', 'finance', 'media_buyer')),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,

    -- 登录信息
    last_login TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,

    -- 密码安全
    last_password_change TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    password_reset_token TEXT,
    password_reset_expires TIMESTAMP WITH TIME ZONE,

    -- 联系信息
    phone VARCHAR(50),
    avatar_url VARCHAR(500),

    -- 软删除支持
    deleted_at TIMESTAMP WITH TIME ZONE,

    -- 管理信息
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2.2 项目表 (优化版)
CREATE TABLE public.projects (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 基本信息
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,

    -- 客户信息
    client_name VARCHAR(255) NOT NULL,
    client_contact VARCHAR(255),
    client_email VARCHAR(255),
    client_phone VARCHAR(50),

    -- 收费模式
    pricing_model VARCHAR(50) NOT NULL DEFAULT 'per_lead'
        CHECK (pricing_model IN ('per_lead', 'fixed_fee', 'hybrid')),
    lead_price NUMERIC(10,2) NOT NULL CHECK (lead_price > 0),
    setup_fee NUMERIC(10,2) DEFAULT 0 CHECK (setup_fee >= 0),
    currency VARCHAR(3) DEFAULT 'USD' CHECK (currency ~ '^[A-Z]{3}$'),

    -- 项目状态
    status VARCHAR(20) NOT NULL DEFAULT 'planning'
        CHECK (status IN ('planning', 'active', 'paused', 'completed', 'cancelled')),
    status_reason TEXT,

    -- 时间信息
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,

    -- 预算信息
    monthly_budget NUMERIC(12,2),
    total_budget NUMERIC(15,2),
    monthly_target_leads INTEGER DEFAULT 0,
    target_cpl NUMERIC(10,2),

    -- 管理信息
    manager_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 软删除支持
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- 2.3 渠道表 (优化版)
CREATE TABLE public.channels (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 基本信息
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,

    -- 联系信息
    contact_person VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    contact_wechat VARCHAR(100),
    contact_qq VARCHAR(50),

    -- 费用结构
    service_fee_rate NUMERIC(5,4) NOT NULL CHECK (service_fee_rate >= 0 AND service_fee_rate <= 1),
    account_setup_fee NUMERIC(10,2) DEFAULT 0 CHECK (account_setup_fee >= 0),
    minimum_topup NUMERIC(10,2) DEFAULT 0 CHECK (minimum_topup >= 0),

    -- 费用说明
    fee_structure JSONB,
    payment_terms TEXT,

    -- 渠道状态和质量
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive', 'suspended')),
    priority INTEGER DEFAULT 1,

    -- 质量评估
    quality_score NUMERIC(3,2) CHECK (quality_score >= 0 AND quality_score <= 10),
    reliability_score NUMERIC(3,2) CHECK (reliability_score >= 0 AND reliability_score <= 10),
    price_competitiveness NUMERIC(3,2) CHECK (price_competitiveness >= 0 AND price_competitiveness <= 10),

    -- 统计数据
    total_accounts INTEGER DEFAULT 0,
    active_accounts INTEGER DEFAULT 0,
    dead_accounts INTEGER DEFAULT 0,
    total_spend NUMERIC(15,2) DEFAULT 0,

    -- 管理信息
    notes TEXT,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 软删除支持
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- 2.4 广告账户表 (优化版)
CREATE TABLE public.ad_accounts (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 基本信息
    account_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,

    -- 平台信息
    platform VARCHAR(50) DEFAULT 'facebook'
        CHECK (platform IN ('facebook', 'instagram', 'google', 'tiktok')),
    platform_account_id VARCHAR(255),
    platform_business_id VARCHAR(255),

    -- 关联信息 (四层数据关系核心)
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE RESTRICT,
    assigned_user_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,

    -- 账户状态 (状态机)
    status VARCHAR(20) NOT NULL DEFAULT 'new'
        CHECK (status IN ('new', 'testing', 'active', 'suspended', 'dead', 'archived')),
    status_reason TEXT,
    last_status_change TIMESTAMP WITH TIME ZONE,

    -- 生命周期时间戳
    created_date TIMESTAMP WITH TIME ZONE,
    activated_date TIMESTAMP WITH TIME ZONE,
    suspended_date TIMESTAMP WITH TIME ZONE,
    dead_date TIMESTAMP WITH TIME ZONE,
    archived_date TIMESTAMP WITH TIME ZONE,

    -- 预算信息
    daily_budget NUMERIC(10,2),
    total_budget NUMERIC(12,2),
    remaining_budget NUMERIC(12,2),

    -- 账户配置
    currency VARCHAR(3) DEFAULT 'USD',
    timezone VARCHAR(50),
    country VARCHAR(2),

    -- 性能数据
    total_spend NUMERIC(15,2) DEFAULT 0,
    total_leads INTEGER DEFAULT 0,
    avg_cpl NUMERIC(10,2),
    best_cpl NUMERIC(10,2),

    -- 开户费用
    setup_fee NUMERIC(10,2) DEFAULT 0,
    setup_fee_paid BOOLEAN DEFAULT false,

    -- 账户类型和支付
    account_type VARCHAR(50),
    payment_method VARCHAR(50),
    billing_information JSONB,

    -- 监控设置
    auto_monitoring BOOLEAN DEFAULT true,
    alert_thresholds JSONB,

    -- 管理信息
    notes TEXT,
    tags JSONB,
    metadata JSONB,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 软删除支持
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- 业务规则约束
ALTER TABLE ad_accounts ADD CONSTRAINT ck_ad_accounts_project_required
    CHECK (project_id IS NOT NULL);
ALTER TABLE ad_accounts ADD CONSTRAINT ck_ad_accounts_channel_required
    CHECK (channel_id IS NOT NULL);

-- 2.5 账户状态历史表
CREATE TABLE public.account_status_history (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 关联信息
    account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,

    -- 状态变更信息
    old_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    change_reason TEXT,

    -- 变更时间和人员
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    changed_by UUID NOT NULL REFERENCES users(id),
    change_source VARCHAR(50) DEFAULT 'manual'
        CHECK (change_source IN ('manual', 'automatic', 'system', 'api')),

    -- 变更时的性能数据
    performance_data JSONB,

    -- 审计信息
    ip_address INET,
    user_agent TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2.6 状态历史表 (新增)
CREATE TABLE public.status_history (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 资源信息
    resource_type VARCHAR(50) NOT NULL,  -- 表名
    resource_id UUID NOT NULL,          -- 记录ID

    -- 状态变更
    old_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    changed_by UUID NOT NULL REFERENCES users(id),
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- 变更详情
    reason TEXT,
    change_source VARCHAR(50) DEFAULT 'manual'
        CHECK (change_source IN ('manual', 'automatic', 'system', 'api')),

    -- 元数据
    metadata JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT
);

-- 2.7 数据版本表 (新增)
CREATE TABLE public.data_versions (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 资源信息
    table_name VARCHAR(50) NOT NULL,
    record_id UUID NOT NULL,
    version INTEGER NOT NULL,

    -- 变更信息
    operation VARCHAR(20) NOT NULL
        CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE', 'SOFT_DELETE')),

    -- 数据快照
    old_data JSONB,
    new_data JSONB,
    diff_data JSONB,  -- 变更差异

    -- 审计信息
    changed_by UUID NOT NULL REFERENCES users(id),
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- 审批流程（可选）
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    is_approved BOOLEAN DEFAULT false,

    -- 元数据
    metadata JSONB DEFAULT '{}',

    -- 唯一约束
    UNIQUE(table_name, record_id, version)
);

-- 2.8 充值表 (优化版)
CREATE TABLE public.topups (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 关联信息 (外键追溯核心)
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    ad_account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    requested_by UUID NOT NULL REFERENCES users(id),

    -- 申请信息
    amount NUMERIC(15,2) NOT NULL CHECK (amount > 0),
    purpose TEXT,
    urgency_level VARCHAR(20) DEFAULT 'normal'
        CHECK (urgency_level IN ('normal', 'urgent')),

    -- 审批流程 (状态机)
    status VARCHAR(20) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'pending', 'clerk_approved', 'finance_approved', 'paid', 'posted', 'rejected')),

    -- 审批信息
    clerk_approval JSONB,
    finance_approval JSONB,

    -- 费用计算
    fee_rate NUMERIC(5,4) NOT NULL CHECK (fee_rate >= 0 AND fee_rate <= 1),
    fee_amount NUMERIC(15,2) NOT NULL,
    total_amount NUMERIC(15,2) NOT NULL,

    -- 执行信息
    payment_method VARCHAR(50),
    transaction_id VARCHAR(255),
    paid_at TIMESTAMP WITH TIME ZONE,
    posted_at TIMESTAMP WITH TIME ZONE,

    -- 拒绝信息
    rejection_reason TEXT,
    rejected_by UUID REFERENCES users(id),
    rejected_at TIMESTAMP WITH TIME ZONE,

    -- 管理信息
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 软删除支持
    deleted_at TIMESTAMP WITH TIME ZONE,

    -- 批量操作支持
    batch_id UUID
);

-- 2.9 日报表 (优化版)
CREATE TABLE public.ad_spend_daily (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 关联信息 (外键追溯核心)
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    ad_account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),

    -- 日期和基础数据
    date DATE NOT NULL,
    leads_submitted INTEGER DEFAULT 0 CHECK (leads_submitted >= 0),
    spend NUMERIC(15,2) NOT NULL CHECK (spend >= 0),
    impressions INTEGER DEFAULT 0 CHECK (impressions >= 0),
    clicks INTEGER DEFAULT 0 CHECK (clicks >= 0),

    -- 甲方确认数据
    leads_confirmed INTEGER,
    confirmed_by UUID REFERENCES users(id),
    confirmed_at TIMESTAMP WITH TIME ZONE,

    -- 差异分析 (自动计算)
    leads_diff INTEGER GENERATED ALWAYS AS (
        CASE
            WHEN leads_confirmed IS NOT NULL THEN leads_confirmed - leads_submitted
            ELSE NULL
        END
    ) STORED,
    diff_reason TEXT,

    -- 质量评估
    lead_quality_score NUMERIC(3,2) CHECK (lead_quality_score >= 0 AND lead_quality_score <= 10),

    -- 元数据
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 唯一约束
    CONSTRAINT uk_ad_spend_daily_account_date UNIQUE (ad_account_id, date)
);

-- 业务规则约束
ALTER TABLE ad_spend_daily ADD CONSTRAINT ck_ad_spend_daily_future_check
    CHECK (date <= CURRENT_DATE + INTERVAL '1 day'); -- 允许录入今天的数据

-- 2.10 对账表 (优化版)
CREATE TABLE public.reconciliations (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 关联信息
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- 对账周期
    period_type VARCHAR(20) NOT NULL DEFAULT 'monthly'
        CHECK (period_type IN ('daily', 'weekly', 'monthly', 'quarterly')),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- 财务数据
    total_topups NUMERIC(15,2) DEFAULT 0,
    total_spend NUMERIC(15,2) DEFAULT 0,
    difference NUMERIC(15,2) DEFAULT 0,

    -- 费用分析
    total_fees NUMERIC(15,2) DEFAULT 0,
    variance_analysis JSONB,

    -- 对账状态
    status VARCHAR(20) DEFAULT 'pending'
        CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),

    -- 审计信息
    reconciled_by UUID REFERENCES users(id),
    reconciled_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2.11 财务流水表 (优化版)
CREATE TABLE public.ledgers (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 关联信息
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    topup_id UUID REFERENCES topups(id) ON DELETE SET NULL,
    ad_account_id UUID REFERENCES ad_accounts(id) ON DELETE SET NULL,

    -- 交易信息
    transaction_type VARCHAR(50) NOT NULL
        CHECK (transaction_type IN ('topup_payment', 'fee_charge', 'refund', 'adjustment')),
    amount NUMERIC(15,2) NOT NULL,
    fee_amount NUMERIC(15,2) DEFAULT 0,
    net_amount NUMERIC(15,2) GENERATED ALWAYS AS (amount - fee_amount) STORED,

    -- 关联信息
    reference_id VARCHAR(255),
    reference_type VARCHAR(50),

    -- 交易详情
    description TEXT,
    metadata JSONB,

    -- 状态信息
    status VARCHAR(20) DEFAULT 'completed'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),

    -- 审计信息
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2.12 操作日志表 (增强版)
CREATE TABLE public.audit_logs (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 操作信息
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(255),
    record_id UUID,

    -- 变更数据
    old_values JSONB,
    new_values JSONB,

    -- 请求信息
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(255),

    -- API调用信息
    api_endpoint TEXT,
    request_method VARCHAR(10),
    response_status INTEGER,
    session_id TEXT,

    -- 批量操作
    batch_id UUID,

    -- 性能信息
    affected_rows INTEGER DEFAULT 0,
    duration_ms INTEGER,
    query_plan JSONB,

    -- 严重程度
    level VARCHAR(20) DEFAULT 'medium'
        CHECK (level IN ('low', 'medium', 'high', 'critical')),

    -- 会话快照
    session_data JSONB,

    -- 错误信息
    error_message TEXT,
    stack_trace TEXT,

    -- 描述信息
    description TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- 创建月度分区
CREATE TABLE audit_logs_y2025m01 PARTITION OF audit_logs
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE audit_logs_y2025m02 PARTITION OF audit_logs
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- 2.13 导入任务表 (优化版)
CREATE TABLE public.import_jobs (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 任务信息
    job_type VARCHAR(50) NOT NULL
        CHECK (job_type IN ('daily_report', 'account_data', 'transaction_data')),
    source_type VARCHAR(50) NOT NULL
        CHECK (source_type IN ('csv', 'excel', 'api', 'manual')),
    source_file VARCHAR(500),

    -- 处理状态
    status VARCHAR(20) DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),

    -- 处理结果
    total_rows INTEGER DEFAULT 0,
    success_rows INTEGER DEFAULT 0,
    failed_rows INTEGER DEFAULT 0,
    skipped_rows INTEGER DEFAULT 0,

    -- 错误信息
    error_message TEXT,
    error_details JSONB,

    -- 处理配置
    mapping_config JSONB,
    validation_rules JSONB,

    -- 审计信息
    created_by UUID NOT NULL REFERENCES users(id),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2.14 性能监控表 (新增)
CREATE TABLE public.performance_metrics (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 查询标识
    query_hash VARCHAR(64) NOT NULL,
    query_type VARCHAR(50) NOT NULL,
    table_name VARCHAR(50),

    -- 性能指标
    execution_time_ms INTEGER,
    rows_examined INTEGER,
    rows_returned INTEGER,
    cpu_time_ms INTEGER,
    io_time_ms INTEGER,

    -- 索引使用
    index_scans INTEGER,
    heap_scans INTEGER,
    indexes_used JSONB,

    -- 执行信息
    query_plan JSONB,
    query_sample TEXT,

    -- 时间信息
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 唯一约束
    UNIQUE(query_hash, created_at)
);

-- 2.15 批量操作表 (新增)
CREATE TABLE public.batch_operations (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 批次信息
    batch_type VARCHAR(50) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),

    -- 操作统计
    total_records INTEGER DEFAULT 0,
    processed_records INTEGER DEFAULT 0,
    success_records INTEGER DEFAULT 0,
    failed_records INTEGER DEFAULT 0,

    -- 执行信息
    started_by UUID NOT NULL REFERENCES users(id),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,

    -- 错误处理
    error_message TEXT,
    error_details JSONB,

    -- 配置
    config JSONB DEFAULT '{}',

    -- 元数据
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 3. 创建索引 (40+ 个索引)
-- =====================================================

-- 用户表索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NOT NULL;
CREATE INDEX idx_users_password_reset ON users(password_reset_token) WHERE password_reset_token IS NOT NULL;

-- 项目表索引
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_client_name ON projects(client_name);
CREATE INDEX idx_projects_manager_id ON projects(manager_id);
CREATE INDEX idx_projects_created_by ON projects(created_by);
CREATE INDEX idx_projects_created_at ON projects(created_at);
CREATE INDEX idx_projects_pricing_model ON projects(pricing_model);
CREATE INDEX idx_projects_deleted_at ON projects(deleted_at) WHERE deleted_at IS NOT NULL;

-- 渠道表索引
CREATE INDEX idx_channels_status ON channels(status);
CREATE INDEX idx_channels_quality_score ON channels(quality_score);
CREATE INDEX idx_channels_code ON channels(code);
CREATE INDEX idx_channels_company_name ON channels(company_name);
CREATE INDEX idx_channels_deleted_at ON channels(deleted_at) WHERE deleted_at IS NOT NULL;

-- 广告账户表索引
CREATE INDEX idx_ad_accounts_project_id ON ad_accounts(project_id);
CREATE INDEX idx_ad_accounts_channel_id ON ad_accounts(channel_id);
CREATE INDEX idx_ad_accounts_assigned_user_id ON ad_accounts(assigned_user_id);
CREATE INDEX idx_ad_accounts_status ON ad_accounts(status);
CREATE INDEX idx_ad_accounts_platform ON ad_accounts(platform);
CREATE INDEX idx_ad_accounts_account_id ON ad_accounts(account_id);
CREATE INDEX idx_ad_accounts_created_date ON ad_accounts(created_date);
CREATE INDEX idx_ad_accounts_deleted_at ON ad_accounts(deleted_at) WHERE deleted_at IS NOT NULL;

-- 状态历史索引
CREATE INDEX idx_account_status_history_account_id ON account_status_history(account_id);
CREATE INDEX idx_account_status_history_changed_at ON account_status_history(changed_at);
CREATE INDEX idx_account_status_history_changed_by ON account_status_history(changed_by);

CREATE INDEX idx_status_history_resource ON status_history(resource_type, resource_id);
CREATE INDEX idx_status_history_changed_at ON status_history(changed_at);
CREATE INDEX idx_status_history_changed_by ON status_history(changed_by);

-- 数据版本索引
CREATE INDEX idx_data_versions_record ON data_versions(table_name, record_id);
CREATE INDEX idx_data_versions_changed_at ON data_versions(changed_at);
CREATE INDEX idx_data_versions_changed_by ON data_versions(changed_by);

-- 充值表索引
CREATE INDEX idx_topups_project_id ON topups(project_id);
CREATE INDEX idx_topups_ad_account_id ON topups(ad_account_id);
CREATE INDEX idx_topups_requested_by ON topups(requested_by);
CREATE INDEX idx_topups_status ON topups(status);
CREATE INDEX idx_topups_created_at ON topups(created_at);
CREATE INDEX idx_topups_paid_at ON topups(paid_at) WHERE paid_at IS NOT NULL;
CREATE INDEX idx_topups_deleted_at ON topups(deleted_at) WHERE deleted_at IS NOT NULL;
CREATE INDEX idx_topups_batch_id ON topups(batch_id) WHERE batch_id IS NOT NULL;

-- 日报表索引
CREATE INDEX idx_ad_spend_daily_project_id ON ad_spend_daily(project_id);
CREATE INDEX idx_ad_spend_daily_ad_account_id ON ad_spend_daily(ad_account_id);
CREATE INDEX idx_ad_spend_daily_user_id ON ad_spend_daily(user_id);
CREATE INDEX idx_ad_spend_daily_date ON ad_spend_daily(date);
CREATE INDEX idx_ad_spend_daily_leads_confirmed ON ad_spend_daily(leads_confirmed) WHERE leads_confirmed IS NOT NULL;
CREATE INDEX idx_ad_spend_daily_spend ON ad_spend_daily(spend) WHERE spend > 0;

-- 对账表索引
CREATE INDEX idx_reconciliations_project_id ON reconciliations(project_id);
CREATE INDEX idx_reconciliations_period ON reconciliations(period_type, period_start, period_end);
CREATE INDEX idx_reconciliations_status ON reconciliations(status);
CREATE INDEX idx_reconciliations_created_at ON reconciliations(created_at);

-- 财务流水表索引
CREATE INDEX idx_ledgers_project_id ON ledgers(project_id);
CREATE INDEX idx_ledgers_topup_id ON ledgers(topup_id);
CREATE INDEX idx_ledgers_transaction_type ON ledgers(transaction_type);
CREATE INDEX idx_ledgers_created_at ON ledgers(created_at);

-- 审计日志表索引
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_table_name ON audit_logs(table_name);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_level ON audit_logs(level);
CREATE INDEX idx_audit_logs_request_id ON audit_logs(request_id) WHERE request_id IS NOT NULL;
CREATE INDEX idx_audit_logs_batch_id ON audit_logs(batch_id) WHERE batch_id IS NOT NULL;

-- 导入任务表索引
CREATE INDEX idx_import_jobs_status ON import_jobs(status);
CREATE INDEX idx_import_jobs_job_type ON import_jobs(job_type);
CREATE INDEX idx_import_jobs_created_by ON import_jobs(created_by);
CREATE INDEX idx_import_jobs_created_at ON import_jobs(created_at);

-- 性能监控表索引
CREATE INDEX idx_performance_metrics_query_hash ON performance_metrics(query_hash);
CREATE INDEX idx_performance_metrics_query_type ON performance_metrics(query_type);
CREATE INDEX idx_performance_metrics_table_name ON performance_metrics(table_name);
CREATE INDEX idx_performance_metrics_execution_time ON performance_metrics(execution_time_ms);
CREATE INDEX idx_performance_metrics_created_at ON performance_metrics(created_at);

-- 批量操作表索引
CREATE INDEX idx_batch_operations_status ON batch_operations(status);
CREATE INDEX idx_batch_operations_type ON batch_operations(batch_type);
CREATE INDEX idx_batch_operations_started_by ON batch_operations(started_by);
CREATE INDEX idx_batch_operations_created_at ON batch_operations(created_at);

-- 复合索引
CREATE INDEX idx_ad_accounts_project_status ON ad_accounts(project_id, status);
CREATE INDEX idx_topups_project_status ON topups(project_id, status);
CREATE INDEX idx_ad_spend_daily_account_date ON ad_spend_daily(ad_account_id, date);
CREATE INDEX idx_ledgers_project_type ON ledgers(project_id, transaction_type);

-- 部分索引 (WHERE条件索引)
CREATE INDEX idx_ad_accounts_active ON ad_accounts(status) WHERE status = 'active';
CREATE INDEX idx_topups_pending ON topups(status) WHERE status = 'pending';

-- =====================================================
-- 4. 创建触发器和函数
-- =====================================================

-- 4.1 更新时间戳触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 应用更新时间戳触发器
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_channels_updated_at
    BEFORE UPDATE ON channels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ad_accounts_updated_at
    BEFORE UPDATE ON ad_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_topups_updated_at
    BEFORE UPDATE ON topups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ad_spend_daily_updated_at
    BEFORE UPDATE ON ad_spend_daily
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reconciliations_updated_at
    BEFORE UPDATE ON reconciliations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ledgers_updated_at
    BEFORE UPDATE ON ledgers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_import_jobs_updated_at
    BEFORE UPDATE ON import_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_batch_operations_updated_at
    BEFORE UPDATE ON batch_operations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 4.2 状态转换触发器函数
CREATE OR REPLACE FUNCTION enforce_status_transitions()
RETURNS TRIGGER AS $$
BEGIN
    -- 调用具体的状态验证函数
    CASE TG_TABLE_NAME
        WHEN 'projects' THEN
            PERFORM validate_project_status_transition(OLD.status, NEW.status);
        WHEN 'ad_accounts' THEN
            PERFORM validate_account_status_transition(OLD.status, NEW.status);
        WHEN 'topups' THEN
            PERFORM validate_topup_status_transition(OLD.status, NEW.status);
    END CASE;

    -- 记录状态历史
    INSERT INTO status_history (
        resource_type,
        resource_id,
        old_status,
        new_status,
        changed_by,
        changed_at,
        reason,
        change_source,
        ip_address,
        user_agent
    ) VALUES (
        TG_TABLE_NAME,
        NEW.id,
        OLD.status,
        NEW.status,
        COALESCE(NEW.updated_by, current_setting('app.current_user_id', true)::UUID),
        CURRENT_TIMESTAMP,
        NEW.status_reason,
        'manual',
        inet_client_addr(),
        current_setting('request.user_agent', true)
    );

    RETURN NEW;
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION '状态转换失败: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- 项目状态验证函数
CREATE OR REPLACE FUNCTION validate_project_status_transition(old_status TEXT, new_status TEXT)
RETURNS VOID AS $$
BEGIN
    -- 定义允许的状态转换
    IF old_status = 'planning' AND new_status NOT IN ('active', 'cancelled') THEN
        RAISE EXCEPTION '规划状态只能转换为活跃或取消';
    ELSIF old_status = 'active' AND new_status NOT IN ('paused', 'completed', 'cancelled') THEN
        RAISE EXCEPTION '活跃状态只能转换为暂停、完成或取消';
    ELSIF old_status = 'paused' AND new_status NOT IN ('active', 'cancelled') THEN
        RAISE EXCEPTION '暂停状态只能转换为活跃或取消';
    ELSIF old_status IN ('completed', 'cancelled') THEN
        RAISE EXCEPTION '完成或取消状态不能再次变更';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 账户状态验证函数
CREATE OR REPLACE FUNCTION validate_account_status_transition(old_status TEXT, new_status TEXT)
RETURNS VOID AS $$
BEGIN
    -- 定义允许的状态转换
    IF old_status = 'new' AND new_status NOT IN ('testing', 'active', 'archived') THEN
        RAISE EXCEPTION '新账户只能转换为测试、活跃或归档';
    ELSIF old_status = 'testing' AND new_status NOT IN ('active', 'suspended', 'dead', 'archived') THEN
        RAISE EXCEPTION '测试账户只能转换为活跃、暂停、死亡或归档';
    ELSIF old_status = 'active' AND new_status NOT IN ('suspended', 'dead', 'archived') THEN
        RAISE EXCEPTION '活跃账户只能转换为暂停、死亡或归档';
    ELSIF old_status = 'suspended' AND new_status NOT IN ('active', 'dead', 'archived') THEN
        RAISE EXCEPTION '暂停账户只能转换为活跃、死亡或归档';
    ELSIF old_status IN ('dead', 'archived') THEN
        RAISE EXCEPTION '死亡或归档账户不能再次变更';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 充值状态验证函数
CREATE OR REPLACE FUNCTION validate_topup_status_transition(old_status TEXT, new_status TEXT)
RETURNS VOID AS $$
BEGIN
    -- 定义允许的状态转换
    IF old_status = 'draft' AND new_status NOT IN ('pending', 'rejected') THEN
        RAISE EXCEPTION '草稿只能转换为待处理或拒绝';
    ELSIF old_status = 'pending' AND new_status NOT IN ('clerk_approved', 'rejected') THEN
        RAISE EXCEPTION '待处理只能转换为户管批准或拒绝';
    ELSIF old_status = 'clerk_approved' AND new_status NOT IN ('finance_approved', 'rejected') THEN
        RAISE EXCEPTION '户管批准只能转换为财务批准或拒绝';
    ELSIF old_status = 'finance_approved' AND new_status NOT IN ('paid', 'rejected') THEN
        RAISE EXCEPTION '财务批准只能转换为已支付或拒绝';
    ELSIF old_status = 'paid' AND new_status NOT IN ('posted', 'rejected') THEN
        RAISE EXCEPTION '已支付只能转换为已到账或拒绝';
    ELSIF old_status IN ('posted', 'rejected') THEN
        RAISE EXCEPTION '已到账或拒绝状态不能再次变更';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 应用状态转换触发器
CREATE TRIGGER projects_status_transition_trigger
    BEFORE UPDATE OF status ON projects
    FOR EACH ROW
    WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION enforce_status_transitions();

CREATE TRIGGER ad_accounts_status_transition_trigger
    BEFORE UPDATE OF status ON ad_accounts
    FOR EACH ROW
    WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION enforce_status_transitions();

CREATE TRIGGER topups_status_transition_trigger
    BEFORE UPDATE OF status ON topups
    FOR EACH ROW
    WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION enforce_status_transitions();

-- 4.3 业务规则约束触发器

-- 账户余额检查函数
CREATE OR REPLACE FUNCTION check_account_balance()
RETURNS TRIGGER AS $$
DECLARE
    daily_budget DECIMAL;
    daily_spend DECIMAL;
BEGIN
    -- 获取账户信息
    SELECT COALESCE(daily_budget, 0)
    INTO daily_budget
    FROM ad_accounts
    WHERE id = NEW.ad_account_id;

    -- 检查日预算
    IF daily_budget > 0 THEN
        SELECT COALESCE(SUM(spend), 0)
        INTO daily_spend
        FROM ad_spend_daily
        WHERE ad_account_id = NEW.ad_account_id
        AND date = CURRENT_DATE;

        IF daily_spend + NEW.spend > daily_budget THEN
            RAISE EXCEPTION '超出日预算：预算 %，已花费 %，尝试添加 %',
                         daily_budget, daily_spend, NEW.spend;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 应用余额检查触发器
CREATE TRIGGER check_account_balance_trigger
    BEFORE INSERT OR UPDATE ON ad_spend_daily
    FOR EACH ROW EXECUTE FUNCTION check_account_balance();

-- 4.4 自动统计更新触发器

-- 项目统计更新函数
CREATE OR REPLACE FUNCTION update_project_statistics()
RETURNS TRIGGER AS $$
DECLARE
    project_id UUID;
BEGIN
    -- 获取项目ID
    IF TG_OP = 'INSERT' THEN
        project_id := NEW.project_id;
    ELSIF TG_OP = 'UPDATE' THEN
        project_id := COALESCE(NEW.project_id, OLD.project_id);
    END IF;

    -- 更新项目统计信息
    UPDATE projects SET
        total_accounts = (
            SELECT COUNT(*) FROM ad_accounts
            WHERE project_id = projects.id AND deleted_at IS NULL
        ),
        active_accounts = (
            SELECT COUNT(*) FROM ad_accounts
            WHERE project_id = projects.id AND status = 'active' AND deleted_at IS NULL
        ),
        total_spend = COALESCE((
            SELECT SUM(spend) FROM ad_spend_daily
            WHERE project_id = projects.id
        ), 0),
        total_leads = COALESCE((
            SELECT SUM(leads_confirmed) FROM ad_spend_daily
            WHERE project_id = projects.id AND leads_confirmed IS NOT NULL
        ), 0)
    WHERE id = project_id;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 渠道统计更新函数
CREATE OR REPLACE FUNCTION update_channel_statistics()
RETURNS TRIGGER AS $$
DECLARE
    channel_id UUID;
BEGIN
    -- 获取渠道ID
    IF TG_OP = 'INSERT' THEN
        channel_id := NEW.channel_id;
    ELSIF TG_OP = 'UPDATE' THEN
        channel_id := COALESCE(NEW.channel_id, OLD.channel_id);
    END IF;

    -- 更新渠道统计信息
    UPDATE channels SET
        total_accounts = (
            SELECT COUNT(*) FROM ad_accounts
            WHERE channel_id = channels.id AND deleted_at IS NULL
        ),
        active_accounts = (
            SELECT COUNT(*) FROM ad_accounts
            WHERE channel_id = channels.id AND status = 'active' AND deleted_at IS NULL
        ),
        dead_accounts = (
            SELECT COUNT(*) FROM ad_accounts
            WHERE channel_id = channels.id AND status = 'dead' AND deleted_at IS NULL
        ),
        total_spend = COALESCE((
            SELECT SUM(total_spend) FROM ad_accounts
            WHERE channel_id = channels.id AND deleted_at IS NULL
        ), 0)
    WHERE id = channel_id;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 应用统计更新触发器
CREATE TRIGGER update_project_statistics_trigger
    AFTER INSERT OR UPDATE OR DELETE ON ad_accounts
    FOR EACH STATEMENT EXECUTE FUNCTION update_project_statistics();

CREATE TRIGGER update_project_statistics_daily_trigger
    AFTER INSERT OR UPDATE ON ad_spend_daily
    FOR EACH STATEMENT EXECUTE FUNCTION update_project_statistics();

CREATE TRIGGER update_channel_statistics_trigger
    AFTER INSERT OR UPDATE OR DELETE ON ad_accounts
    FOR EACH STATEMENT EXECUTE FUNCTION update_channel_statistics();

-- =====================================================
-- 5. 创建视图
-- =====================================================

-- 5.1 项目统计视图
CREATE OR REPLACE VIEW project_statistics AS
SELECT
    p.id,
    p.name,
    p.client_name,
    p.status,
    p.pricing_model,
    p.lead_price,
    p.setup_fee,

    -- 账户统计
    COUNT(DISTINCT a.id) as total_accounts,
    COUNT(DISTINCT CASE WHEN a.status = 'active' THEN a.id END) as active_accounts,

    -- 消耗统计
    COALESCE(SUM(dr.spend), 0) as total_spend,
    COALESCE(SUM(dr.leads_confirmed), 0) as total_leads,
    CASE
        WHEN COALESCE(SUM(dr.leads_confirmed), 0) > 0
        THEN COALESCE(SUM(dr.spend), 0) / COALESCE(SUM(dr.leads_confirmed), 0)
        ELSE NULL
    END as avg_cpl,

    -- 收入统计
    p.setup_fee + (COALESCE(SUM(dr.leads_confirmed), 0) * p.lead_price) as total_revenue,
    (p.setup_fee + (COALESCE(SUM(dr.leads_confirmed), 0) * p.lead_price)) - COALESCE(SUM(dr.spend), 0) as profit,

    -- 时间信息
    p.created_at,
    p.updated_at

FROM projects p
LEFT JOIN ad_accounts a ON p.id = a.project_id AND a.deleted_at IS NULL
LEFT JOIN ad_spend_daily dr ON a.id = dr.ad_account_id
WHERE p.deleted_at IS NULL
GROUP BY p.id, p.name, p.client_name, p.status, p.pricing_model, p.lead_price, p.setup_fee, p.created_at, p.updated_at;

-- 5.2 渠道表现视图
CREATE OR REPLACE VIEW channel_performance AS
SELECT
    c.id,
    c.name,
    c.company_name,
    c.service_fee_rate,
    c.status,

    -- 账户统计
    COUNT(DISTINCT a.id) as total_accounts,
    COUNT(DISTINCT CASE WHEN a.status = 'active' THEN a.id END) as active_accounts,
    COUNT(DISTINCT CASE WHEN a.status = 'dead' THEN a.id END) as dead_accounts,

    -- 生存期统计
    ROUND(AVG(
        CASE
            WHEN a.dead_date IS NOT NULL AND a.created_date IS NOT NULL
            THEN EXTRACT(DAYS FROM (a.dead_date - a.created_date))
            ELSE NULL
        END
    )) as avg_lifetime_days,

    -- 消耗统计
    COALESCE(SUM(a.total_spend), 0) as total_spend,
    COALESCE(SUM(t.fee_amount), 0) as total_fees,
    COALESCE(SUM(t.total_amount), 0) as total_topups,

    -- 质量指标
    ROUND(
        (COUNT(DISTINCT CASE WHEN a.status = 'active' THEN a.id END)::NUMERIC /
         NULLIF(COUNT(DISTINCT a.id), 0)) * 100, 2
    ) as survival_rate_percent,

    -- 时间信息
    c.created_at,
    c.updated_at

FROM channels c
LEFT JOIN ad_accounts a ON c.id = a.channel_id AND a.deleted_at IS NULL
LEFT JOIN topups t ON a.id = t.ad_account_id AND t.status = 'posted' AND t.deleted_at IS NULL
WHERE c.deleted_at IS NULL
GROUP BY c.id, c.name, c.company_name, c.service_fee_rate, c.status, c.created_at, c.updated_at;

-- 5.3 用户工作统计视图
CREATE OR REPLACE VIEW user_work_statistics AS
SELECT
    u.id,
    u.full_name,
    u.email,
    u.role,

    -- 分配的账户
    COUNT(DISTINCT a.id) as assigned_accounts,
    COUNT(DISTINCT CASE WHEN a.status = 'active' THEN a.id END) as active_accounts,

    -- 工作天数
    COUNT(DISTINCT dr.date) as work_days,

    -- 业绩统计
    COALESCE(SUM(dr.spend), 0) as total_spend,
    COALESCE(SUM(dr.leads_submitted), 0) as total_submitted_leads,
    COALESCE(SUM(dr.leads_confirmed), 0) as total_confirmed_leads,

    -- 效率指标
    COALESCE(AVG(dr.spend), 0) as avg_daily_spend,
    COALESCE(AVG(dr.leads_confirmed), 0) as avg_daily_leads,
    CASE
        WHEN COALESCE(SUM(dr.leads_confirmed), 0) > 0
        THEN COALESCE(SUM(dr.spend), 0) / COALESCE(SUM(dr.leads_confirmed), 0)
        ELSE NULL
    END as avg_cpl,

    -- 充值统计
    COUNT(DISTINCT t.id) as topup_requests,
    COALESCE(SUM(t.amount), 0) as total_topup_amount,
    COUNT(DISTINCT CASE WHEN t.status = 'posted' THEN t.id END) as approved_topups,

    -- 时间范围
    MIN(dr.date) as first_work_date,
    MAX(dr.date) as last_work_date,
    u.last_login

FROM users u
LEFT JOIN ad_accounts a ON u.id = a.assigned_user_id AND a.deleted_at IS NULL
LEFT JOIN ad_spend_daily dr ON a.id = dr.ad_account_id
LEFT JOIN topups t ON u.id = t.requested_by AND t.deleted_at IS NULL
WHERE u.deleted_at IS NULL
GROUP BY u.id, u.full_name, u.email, u.role, u.last_login;

-- =====================================================
-- 6. 创建维护函数
-- =====================================================

-- 6.1 自动分区维护函数
CREATE OR REPLACE FUNCTION monthly_partition_maintenance()
RETURNS TEXT AS $$
DECLARE
    result TEXT := '';
    tbl_name TEXT;
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
BEGIN
    -- 为audit_logs创建未来3个月的分区
    FOR i IN 0..2 LOOP
        start_date := date_trunc('month', CURRENT_DATE) + (i || ' months')::INTERVAL;
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'audit_logs_y' || to_char(start_date, 'YYYY') || 'm' || to_char(start_date, 'MM');

        EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %I
                        FOR VALUES FROM (%L) TO (%L)',
                        partition_name, 'audit_logs', start_date, end_date);

        result := result || 'Created partition: ' || partition_name || E'\n';
    END LOOP;

    -- 清理旧分区（保留6个月）
    FOR tbl_name IN SELECT table_name FROM information_schema.tables
                   WHERE table_name LIKE 'audit_logs_y%'
                   AND table_name < 'audit_logs_y' || to_char(CURRENT_DATE - INTERVAL '6 months', 'YYYYm')
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || tbl_name;
        result := result || 'Dropped old partition: ' || tbl_name || E'\n';
    END LOOP;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- 6.2 定期清理函数
CREATE OR REPLACE FUNCTION periodic_cleanup()
RETURNS TEXT AS $$
DECLARE
    result TEXT := '';
    deleted_count INTEGER;
BEGIN
    -- 清理过期的密码重置令牌
    DELETE FROM users
    WHERE password_reset_expires < CURRENT_TIMESTAMP;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    result := 'Cleaned up ' || deleted_count || ' expired password reset tokens\n';

    -- 清理90天前的性能指标
    DELETE FROM performance_metrics
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '90 days';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    result := result || 'Cleaned up ' || deleted_count || ' old performance metrics\n';

    -- 清理180天前的状态历史（保留重要历史）
    DELETE FROM status_history
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '180 days'
    AND resource_type NOT IN ('projects', 'users');
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    result := result || 'Cleaned up ' || deleted_count || ' old status history entries\n';

    -- 更新表统计信息
    ANALYZE;
    result := result || 'Updated table statistics\n';

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 7. 插入初始数据
-- =====================================================

-- 插入默认管理员用户
INSERT INTO public.users (id, email, username, hashed_password, full_name, role, is_active, is_superuser, created_at, updated_at) VALUES
('00000000-0000-0000-0000-000000000001',
 'admin@aiad.com',
 'admin',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uO.G', -- 密码: admin123!@#
 '系统管理员',
 'admin',
 true,
 true,
 NOW(),
 NOW());

-- 插入示例渠道
INSERT INTO public.channels (id, name, code, company_name, service_fee_rate, contact_person, contact_email, created_by, created_at, updated_at) VALUES
('00000000-0000-0000-0000-000000000010',
 'Facebook Ads',
 'facebook',
 'Meta Platforms, Inc.',
 0.0000, -- Facebook 不收取服务费
 '平台自动',
 'support@meta.com',
 '00000000-0000-0000-0000-000000000001',
 NOW(),
 NOW()),
('00000000-0000-0000-0000-000000000011',
 'Google Ads',
 'google',
 'Google LLC',
 0.0000, -- Google 不收取服务费
 '平台自动',
 'support@google.com',
 '00000000-0000-0000-0000-000000000001',
 NOW(),
 NOW());

-- 插入示例项目
INSERT INTO public.projects (id, name, code, client_name, pricing_model, lead_price, setup_fee, manager_id, created_by, created_at, updated_at) VALUES
('00000000-0000-0000-0000-000000000020',
 '测试项目',
 'TEST001',
 '测试客户有限公司',
 'per_lead',
 15.00,
 0.00,
 '00000000-0000-0000-0000-000000000001',
 '00000000-0000-0000-0000-000000000001',
 NOW(),
 NOW());

-- =====================================================
-- 8. 验证数据库结构
-- =====================================================

DO $$
DECLARE
    table_count INTEGER;
    index_count INTEGER;
    trigger_count INTEGER;
    view_count INTEGER;
    function_count INTEGER;
BEGIN
    -- 统计数据库对象数量
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE schemaname = 'public';

    SELECT COUNT(*) INTO trigger_count
    FROM information_schema.triggers
    WHERE trigger_schema = 'public';

    SELECT COUNT(*) INTO view_count
    FROM information_schema.views
    WHERE table_schema = 'public';

    SELECT COUNT(*) INTO function_count
    FROM information_schema.routines
    WHERE routine_schema = 'public' AND routine_type = 'FUNCTION';

    -- 输出创建结果
    RAISE NOTICE '=================================';
    RAISE NOTICE '数据库结构创建完成！';
    RAISE NOTICE '=================================';
    RAISE NOTICE '表数量: %', table_count;
    RAISE NOTICE '索引数量: %', index_count;
    RAISE NOTICE '触发器数量: %', trigger_count;
    RAISE NOTICE '视图数量: %', view_count;
    RAISE NOTICE '函数数量: %', function_count;
    RAISE NOTICE '=================================';

    -- 验证关键表是否存在
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        RAISE NOTICE '✓ 用户表创建成功';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'projects') THEN
        RAISE NOTICE '✓ 项目表创建成功';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ad_accounts') THEN
        RAISE NOTICE '✓ 广告账户表创建成功';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'status_history') THEN
        RAISE NOTICE '✓ 状态历史表创建成功';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'data_versions') THEN
        RAISE NOTICE '✓ 数据版本表创建成功';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'performance_metrics') THEN
        RAISE NOTICE '✓ 性能监控表创建成功';
    END IF;

    RAISE NOTICE '=================================';
    RAISE NOTICE '默认管理员账号:';
    RAISE NOTICE '邮箱: admin@aiad.com';
    RAISE NOTICE '用户名: admin';
    RAISE NOTICE '密码: admin123!@#';
    RAISE NOTICE '=================================';
END $$;

-- =====================================================
-- 完成信息
-- =====================================================

-- 输出完成日志
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================================';
    RAISE NOTICE 'AI广告代投系统数据库结构 v3.0 优化完成！';
    RAISE NOTICE '========================================================';
    RAISE NOTICE '';
    RAISE NOTICE '主要优化内容:';
    RAISE NOTICE '1. 统一使用 UUID 主键';
    RAISE NOTICE '2. 简化密码存储（使用 bcrypt）';
    RAISE NOTICE '3. 添加软删除支持';
    RAISE NOTICE '4. 实现状态转换触发器和验证';
    RAISE NOTICE '5. 增强审计日志功能';
    RAISE NOTICE '6. 实现数据版本控制';
    RAISE NOTICE '7. 添加性能监控表';
    RAISE NOTICE '8. 实现表分区策略';
    RAISE NOTICE '9. 添加批量操作支持';
    RAISE NOTICE '10. 完善40+个性能索引';
    RAISE NOTICE '';
    RAISE NOTICE '数据库已准备就绪，可以开始使用！';
    RAISE NOTICE '========================================================';
END $$;