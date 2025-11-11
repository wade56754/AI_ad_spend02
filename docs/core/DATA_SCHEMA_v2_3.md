# 数据库设计与RLS策略 v3.3（生产级优化版）

> **文档目的**: 提供完整的企业级数据库设计、增强安全策略、性能优化和数据关系
> **目标读者**: 数据库管理员、后端开发工程师、架构师
> **更新日期**: 2025-11-12
> **版本**: v3.3 - 生产级安全优化版

---

## 1. 数据库设计原则

### 1.1 核心设计原则
- **数据完整性**: 使用外键约束确保数据关系完整性
- **追溯性**: 所有业务数据必须能追溯到"项目→渠道→账户→投手"完整链路
- **安全性**: 多层安全策略（RLS + 加密 + 审计）
- **性能优化**: 智能索引设计和分区策略
- **一致性**: 统一的命名规范和字段类型
- **可扩展性**: 支持微服务架构和水平扩展

### 1.2 字段规范（v2.3增强）
```sql
-- 统一字段规范
- 主键: UUID PRIMARY KEY DEFAULT uuid_generate_v4()
- 外键: UUID (关联其他表主键) ON DELETE [RESTRICT|SET NULL|CASCADE]
- 金额字段: NUMERIC(15,2) (支持最大999万亿，精度2位小数)
- 费率字段: NUMERIC(5,4) (支持0.01%-100%费率，精度4位小数)
- 状态字段: VARCHAR(20) (状态枚举值)
- 时间字段: TIMESTAMPTZ (带时区，默认UTC)
- 布尔字段: BOOLEAN (true/false)
- JSON字段: JSONB (灵活的元数据存储)
- 文本字段: TEXT (大文本内容)
- 安全字段: TEXT/VARCHAR (加密存储)

-- 统一约束规范
- 非空约束: 关键业务字段必须NOT NULL
- 唯一约束: 业务唯一标识必须UNIQUE
- 检查约束: 业务规则使用CHECK约束
- 外键约束: 明确删除策略(RESTRICT优先)
- 默认值: 合理的默认值设置
- 触发器: 自动更新created_at/updated_at
```

### 1.3 命名规范
```sql
-- 表名: 小写复数，下划线分隔
users, user_profiles, projects, channels, ad_accounts, daily_reports, topups

-- 字段名: 小写，下划线分隔
created_at, updated_at, user_id, account_name, password_hash, password_salt

-- 索引名: idx_表名_字段名_类型
idx_users_email_active, idx_projects_status_created

-- 外键名: fk_表名_字段名
fk_projects_manager_id, fk_topups_project_id

-- 约束名: ck_表名_字段名_约束类型
ck_projects_status, ck_users_email_format, uq_accounts_account_id

-- 触发器名: trg_表名_动作
trg_users_updated_at, trg_accounts_status_change

-- 策略名: pl_表名_动作
pl_users_own_access, pl_projects_member_access
```

---

## 2. 核心表结构（v2.3优化）

### 2.1 用户表（增强安全版）
```sql
CREATE TABLE public.users (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 基本信息
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    password_salt VARCHAR(32) NOT NULL DEFAULT gen_salt('bf', 12),
    password_iterations INTEGER NOT NULL DEFAULT 12,
    full_name VARCHAR(100),

    -- 角色和权限
    role VARCHAR(20) NOT NULL DEFAULT 'media_buyer',
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
    CONSTRAINT users_role_check CHECK (role IN ('admin', 'finance', 'data_operator', 'account_manager', 'media_buyer')),
    CONSTRAINT users_email_check CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT users_username_check CHECK (username ~* '^[a-zA-Z0-9_]{3,50}$'),
    CONSTRAINT users_phone_check CHECK (phone IS NULL OR phone ~* '^\+?[1-9]\d{1,14}$')
);

-- 用户配置表（扩展信息）
CREATE TABLE public.user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
```

### 2.2 会话表（增强安全版）
```sql
CREATE TABLE public.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 关联用户
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 认证信息
    token_hash VARCHAR(255) NOT NULL,
    refresh_token_hash VARCHAR(255),
    session_token VARCHAR(255) UNIQUE NOT NULL DEFAULT encode(gen_random_bytes(32), 'hex'),

    -- 设备信息（移除PostGIS依赖，使用JSON存储位置）
    ip_address INET DEFAULT COALESCE(get_app_setting('app.client_ip'), '0.0.0.0')::INET,
    user_agent TEXT,
    device_fingerprint TEXT,
    location JSONB DEFAULT '{}',  -- 存储位置信息，避免PostGIS依赖

    -- 状态信息
    is_active BOOLEAN NOT NULL DEFAULT true,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '24 hours'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 使用统计
    access_count INTEGER NOT NULL DEFAULT 0,

    -- 安全约束
    CONSTRAINT sessions_expires_check CHECK (expires_at > created_at),
    CONSTRAINT sessions_access_count_check CHECK (access_count >= 0)
);
```

### 2.3 项目表（状态机增强版）
```sql
CREATE TABLE public.projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

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
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
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
    account_manager_id UUID REFERENCES users(id),

    -- 管理信息
    created_by UUID NOT NULL REFERENCES users(id),
    updated_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 约束
    CONSTRAINT projects_status_check CHECK (status IN ('draft', 'active', 'paused', 'completed', 'cancelled', 'archived')),
    CONSTRAINT projects_pricing_check CHECK (pricing_model IN ('per_lead', 'fixed_fee', 'hybrid')),
    CONSTRAINT projects_currency_check CHECK (currency ~* '^[A-Z]{3}$'),
    CONSTRAINT projects_date_check CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date),
    CONSTRAINT projects_budget_check CHECK (total_budget IS NULL OR monthly_budget IS NULL OR monthly_budget <= total_budget),
    CONSTRAINT projects_name_check CHECK (length(trim(name)) >= 2)
);
```

### 2.4 渠道表（质量评估版）
```sql
CREATE TABLE public.channels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

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
    survival_rate NUMERIC(5, 2) GENERATED ALWAYS AS (
        CASE
            WHEN total_accounts > 0 THEN ROUND((active_accounts::NUMERIC / total_accounts) * 100, 2)
            ELSE 0
        END
    ) STORED,

    -- 管理信息
    manager_id UUID REFERENCES users(id),
    created_by UUID NOT NULL REFERENCES users(id),
    updated_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 约束
    CONSTRAINT channels_status_check CHECK (status IN ('active', 'inactive', 'suspended', 'pending')),
    CONSTRAINT channels_platform_check CHECK (platform IN ('facebook', 'google', 'tiktok', 'bytedance', 'wechat', 'other')),
    UNIQUE(platform, platform_account_id) WHERE platform_account_id IS NOT NULL
);
```

### 2.5 广告账户表（完整追溯版）
```sql
CREATE TABLE public.ad_accounts (
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
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,  -- 允许NULL值

    -- 账户状态（状态机）
    status VARCHAR(20) NOT NULL DEFAULT 'new',
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
    CONSTRAINT ad_accounts_status_check CHECK (status IN ('draft', 'new', 'testing', 'active', 'suspended', 'dead', 'archived')),
    CONSTRAINT ad_accounts_platform_check CHECK (platform IN ('facebook', 'google', 'tiktok', 'instagram', 'other')),
    CONSTRAINT ad_accounts_budget_check CHECK ((daily_budget IS NULL OR daily_budget > 0) AND (lifetime_budget IS NULL OR lifetime_budget > 0)),
    CONSTRAINT ad_accounts_spend_check CHECK (total_spend >= 0),
    CONSTRAINT ad_accounts_remaining_check CHECK (remaining_budget >= 0),
    CONSTRAINT ad_accounts_leads_check CHECK (total_leads >= 0),
    UNIQUE(platform, account_id)
);
```

### 2.6 项目成员表（权限管理版）
```sql
CREATE TABLE public.project_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
```

### 2.7 日报表（数据质量版）
```sql
CREATE TABLE public.daily_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 关联信息（完整追溯）
    report_date DATE NOT NULL,
    account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    submitter_id UUID NOT NULL REFERENCES users(id),
    reviewer_id UUID REFERENCES users(id),
    approved_by UUID REFERENCES users(id),

    -- 审核流程（状态机）
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
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
    CONSTRAINT daily_reports_status_check CHECK (status IN ('draft', 'submitted', 'reviewed', 'approved', 'rejected', 'archived')),
    CONSTRAINT daily_reports_spend_check CHECK (spend >= 0),
    CONSTRAINT daily_reports_impressions_check CHECK (impressions >= 0),
    CONSTRAINT daily_reports_clicks_check CHECK (clicks >= 0),
    CONSTRAINT daily_reports_conversions_check CHECK (conversions >= 0),
    CONSTRAINT daily_reports_revenue_check CHECK (revenue >= 0),
    CONSTRAINT daily_reports_leads_check CHECK (leads_submitted >= 0),
    CONSTRAINT daily_reports_date_check CHECK (report_date <= CURRENT_DATE),
    UNIQUE(report_date, account_id)
);
```

### 2.8 充值业务表
```sql
CREATE TABLE public.topups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id VARCHAR(50) UNIQUE NOT NULL DEFAULT concat('TP', EXTRACT(EPOCH FROM NOW())::bigint),

    -- 关联信息（完整追溯）
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    account_id UUID REFERENCES ad_accounts(id) ON DELETE SET NULL,  -- 修改为SET NULL避免级联删除
    requester_id UUID NOT NULL REFERENCES users(id),
    reviewer_id UUID REFERENCES users(id),
    approver_id UUID REFERENCES users(id),

    -- 审批流程（状态机）
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
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
    CONSTRAINT topups_status_check CHECK (status IN ('draft', 'pending_review', 'reviewed', 'approved', 'rejected', 'paid', 'confirmed', 'cancelled', 'refunded')),
    CONSTRAINT topups_urgency_check CHECK (urgency_level IN ('normal', 'urgent', 'emergency'))
);
```

### 2.9 充值财务表（财务记录分离）
```sql
CREATE TABLE public.topup_financial (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topup_id UUID NOT NULL REFERENCES topups(id) ON DELETE CASCADE,

    -- 财务信息
    payment_method VARCHAR(50),
    payment_reference VARCHAR(100),
    bank_account VARCHAR(50),
    transaction_id VARCHAR(100),
    transaction_fee NUMERIC(10, 2) DEFAULT 0 CHECK (transaction_fee >= 0 AND transaction_fee <= 1000),

    -- 确认信息
    paid_at TIMESTAMPTZ,
    confirmed_at TIMESTAMPTZ,
    financial_notes TEXT,

    -- 管理字段
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 创建触发器更新财务表
CREATE TRIGGER trg_topup_financial_updated_at
    BEFORE UPDATE ON topup_financial
    FOR EACH ROW EXECUTE FUNCTION trg_update_updated_at();
```

### 2.11 对账表（财务审计版）
```sql
CREATE TABLE public.reconciliations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reconciliation_id VARCHAR(50) UNIQUE NOT NULL DEFAULT concat('RC', EXTRACT(EPOCH FROM NOW())::bigint),

    -- 关联信息
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

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
    reconciled_by UUID REFERENCES users(id),
    disputed_by UUID REFERENCES users(id),
    approved_by UUID REFERENCES users(id),

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
```

### 2.10 审计日志表（增强追踪版）
```sql
-- 创建分区表
CREATE TABLE public.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 操作信息
    event_type VARCHAR(50) NOT NULL,
    user_id UUID REFERENCES users(id),
    user_email VARCHAR(255),
    session_id UUID REFERENCES sessions(id),

    -- 资源信息
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    action VARCHAR(20) NOT NULL,

    -- 请求信息（使用默认值避免空值错误）
    ip_address INET DEFAULT COALESCE(get_app_setting('app.client_ip'), '0.0.0.0')::INET,
    user_agent TEXT DEFAULT COALESCE(get_app_setting('app.user_agent'), ''),
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
    parent_log_id UUID REFERENCES audit_logs(id),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 约束
    CONSTRAINT audit_logs_action_check CHECK (action IN ('CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'VIEW', 'EXPORT', 'IMPORT', 'APPROVE', 'REJECT')),
    CONSTRAINT audit_logs_level_check CHECK (level IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT audit_logs_execution_time_check CHECK (execution_time_ms >= 0),
    CONSTRAINT audit_logs_affected_rows_check CHECK (affected_rows >= 0)
) PARTITION BY RANGE (created_at);

-- 创建当前月份分区
CREATE TABLE audit_logs_y2025m11 PARTITION OF audit_logs
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

-- 创建自动分区管理函数
CREATE OR REPLACE FUNCTION create_audit_log_partition(target_month DATE DEFAULT date_trunc('month', CURRENT_DATE))
RETURNS void AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    start_date := date_trunc('month', target_month);
    end_date := start_date + INTERVAL '1 month';
    -- 修正分区命名格式
    partition_name := 'audit_logs_y' || to_char(start_date, 'YYYY"m"MM');

    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %I
                   FOR VALUES FROM (%L) TO (%L)',
                   partition_name, 'audit_logs', start_date, end_date);
END;
$$ LANGUAGE plpgsql;

-- 创建未来6个月的分区
SELECT create_audit_log_partition(date_trunc('month', CURRENT_DATE) + (n || ' months')::INTERVAL)
FROM generate_series(0, 5) n;
```

### 2.12 账户状态历史表（状态追踪版）
```sql
CREATE TABLE public.account_status_history (
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
```

---

## 3. 增强索引策略（v2.3）

### 3.1 用户相关索引
```sql
-- 用户表索引（优化）
CREATE INDEX CONCURRENTLY idx_users_email_active ON users(email) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_users_role_active ON users(role, is_active) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_users_login_fields ON users(username, email, is_active);
CREATE INDEX CONCURRENTLY idx_users_last_login ON users(last_login_at DESC) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_users_account_locked ON users(account_locked_until) WHERE account_locked_until IS NOT NULL;

-- 用户配置索引
CREATE INDEX CONCURRENTLY idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX CONCURRENTLY idx_user_profiles_department ON user_profiles(department);
```

### 3.2 会话索引
```sql
-- 会话表索引（安全优化）
CREATE INDEX CONCURRENTLY idx_sessions_user_active ON sessions(user_id, is_active) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_sessions_expires_active ON sessions(expires_at, is_active) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_sessions_token_lookup ON sessions(token_hash) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_sessions_device_fingerprint ON sessions(device_fingerprint) WHERE device_fingerprint IS NOT NULL;
```

### 3.3 项目相关索引
```sql
-- 项目表索引（性能优化）
CREATE INDEX CONCURRENTLY idx_projects_owner_status ON projects(owner_id, status) WHERE status IN ('active', 'paused');
CREATE INDEX CONCURRENTLY idx_projects_account_manager ON projects(account_manager_id) WHERE account_manager_id IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_projects_created_at ON projects(created_at DESC);
CREATE INDEX CONCURRENTLY idx_projects_client_email ON projects(client_email) WHERE client_email IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_projects_status_created ON projects(status, created_at DESC);
CREATE INDEX CONCURRENTLY idx_projects_budget_spend ON projects(total_budget, total_spend) WHERE total_budget IS NOT NULL;

-- 项目成员索引
CREATE INDEX CONCURRENTLY idx_project_members_user_role ON project_members(user_id, role) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_project_members_project_active ON project_members(project_id, is_active) WHERE is_active = true;
```

### 3.4 渠道和账户索引
```sql
-- 渠道表索引
CREATE INDEX CONCURRENTLY idx_channels_platform_status ON channels(platform, status) WHERE status = 'active';
CREATE INDEX CONCURRENTLY idx_channels_quality_score ON channels(quality_score DESC) WHERE quality_score IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_channels_manager ON channels(manager_id) WHERE manager_id IS NOT NULL;

-- 广告账户索引（核心性能）
CREATE INDEX CONCURRENTLY idx_ad_accounts_project_status ON ad_accounts(project_id, status) WHERE status IN ('active', 'testing');
CREATE INDEX CONCURRENTLY idx_ad_accounts_channel_assigned ON ad_accounts(channel_id, assigned_to) WHERE assigned_to IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_ad_accounts_platform_status ON ad_accounts(platform, status) WHERE status IN ('active', 'testing');
CREATE INDEX CONCURRENTLY idx_ad_accounts_balance ON ad_accounts(remaining_budget DESC) WHERE remaining_budget > 0;
CREATE INDEX CONCURRENTLY idx_ad_accounts_spend_leads ON ad_accounts(total_spend DESC, total_leads DESC);
CREATE INDEX CONCURRENTLY idx_ad_accounts_assigned_active ON ad_accounts(assigned_to, status) WHERE status = 'active';
```

### 3.5 日报和充值索引
```sql
-- 日报表索引（查询优化）
CREATE INDEX CONCURRENTLY idx_daily_reports_date_account ON daily_reports(report_date DESC, account_id);
CREATE INDEX CONCURRENTLY idx_daily_reports_status_date ON daily_reports(status, report_date DESC) WHERE status IN ('draft', 'submitted');
CREATE INDEX CONCURRENTLY idx_daily_reports_submitter_date ON daily_reports(submitter_id, report_date DESC);
CREATE INDEX CONCURRENTLY idx_daily_reports_reviewer_status ON daily_reports(reviewer_id, status) WHERE reviewer_id IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_daily_reports_spend ON daily_reports(spend DESC) WHERE spend > 0;
CREATE INDEX CONCURRENTLY idx_daily_reports_confirmed ON daily_reports(leads_confirmed DESC) WHERE leads_confirmed IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_daily_reports_quality_score ON daily_reports(lead_quality_score DESC) WHERE lead_quality_score IS NOT NULL;

-- 充值表索引（流程优化）
CREATE INDEX CONCURRENTLY idx_topups_status_created ON topups(status, created_at DESC) WHERE status IN ('draft', 'pending_review', 'approved');
CREATE INDEX CONCURRENTLY idx_topups_account_status ON topups(account_id, status) WHERE status IN ('draft', 'pending_review', 'approved');
CREATE INDEX CONCURRENTLY idx_topups_amount_range ON topups(amount DESC) WHERE status IN ('approved', 'paid');
CREATE INDEX CONCURRENTLY idx_topups_requester_created ON topups(requester_id, created_at DESC);
CREATE INDEX CONCURRENTLY idx_topups_urgency_status ON topups(urgency_level, status) WHERE urgency_level IN ('urgent', 'emergency');
```

### 3.6 审计和历史索引
```sql
-- 审计日志索引（追踪优化）
CREATE INDEX CONCURRENTLY idx_audit_logs_user_created ON audit_logs(user_id, created_at DESC);
CREATE INDEX CONCURRENTLY idx_audit_logs_resource_action ON audit_logs(resource_type, resource_id, action);
CREATE INDEX CONCURRENTLY idx_audit_logs_event_type ON audit_logs(event_type, created_at DESC);
CREATE INDEX CONCURRENTLY idx_audit_logs_ip_address ON audit_logs(ip_address, created_at DESC) WHERE ip_address IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_audit_logs_level_created ON audit_logs(level, created_at DESC) WHERE level IN ('high', 'critical');
CREATE INDEX CONCURRENTLY idx_audit_logs_batch_id ON audit_logs(batch_id, created_at) WHERE batch_id IS NOT NULL;

-- 账户状态历史索引
CREATE INDEX CONCURRENTLY idx_account_status_history_account ON account_status_history(account_id, changed_at DESC);
CREATE INDEX CONCURRENTLY idx_account_status_history_changed_by ON account_status_history(changed_by, changed_at DESC);
CREATE INDEX CONCURRENTLY idx_account_status_history_source ON account_status_history(change_source, changed_at DESC);
```

---

## 4. RLS安全策略（v2.3增强版）

### 4.1 RLS基础配置
```sql
-- 创建认证用户角色
CREATE ROLE authenticated_user;
GRANT USAGE ON SCHEMA public TO authenticated_user;

-- 创建安全上下文函数（修复类型转换错误）
CREATE OR REPLACE FUNCTION get_current_user_context()
RETURNS TABLE(user_id UUID, role TEXT, session_valid BOOLEAN) AS $$
DECLARE
    v_user_id UUID;
    v_role TEXT;
    v_session_valid BOOLEAN := FALSE;
BEGIN
    -- 获取当前用户ID（使用COALESCE防止空值）
    v_user_id := COALESCE(
        NULLIF(current_setting('app.current_user_id', true), ''),
        '00000000-0000-0000-0000-000000000000'
    )::UUID;

    -- 验证会话有效性
    SELECT u.role, s.is_valid
    INTO v_role, v_session_valid
    FROM users u
    JOIN (
        SELECT user_id,
               CASE WHEN expires_at > NOW() AND is_active = true THEN true ELSE false END as is_valid
        FROM sessions
        WHERE token_hash = current_setting('app.session_token', true)
        ORDER BY created_at DESC LIMIT 1
    ) s ON u.id = s.user_id
    WHERE u.id = v_user_id AND u.is_active = true;

    RETURN QUERY SELECT v_user_id, v_role, COALESCE(v_session_valid, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 启用RLS的表
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE topups ENABLE ROW LEVEL SECURITY;
ALTER TABLE topup_financial ENABLE ROW LEVEL SECURITY;
ALTER TABLE reconciliations ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE account_status_history ENABLE ROW LEVEL SECURITY;
-- system_config 表建议关闭 RLS 以便运维访问
-- ALTER TABLE system_config ENABLE ROW LEVEL SECURITY;
```

### 4.2 用户表RLS策略
```sql
-- 用户个人信息访问
CREATE POLICY pl_users_own_profile ON users
    FOR ALL
    TO authenticated_user
    USING (
        id = (SELECT user_id FROM get_current_user_context())
        OR is_superuser = true
    );

-- 用户基本信息公开访问
CREATE POLICY pl_users_public_read ON users
    FOR SELECT
    TO authenticated_user
    USING (true);

-- 用户配置访问
CREATE POLICY pl_user_profiles_own ON user_profiles
    FOR ALL
    TO authenticated_user
    USING (
        user_id = (SELECT user_id FROM get_current_user_context())
        OR EXISTS (
            SELECT 1 FROM get_current_user_context()
            WHERE role IN ('admin', 'account_manager')
        )
    );
```

### 4.3 项目表RLS策略
```sql
-- 项目访问策略（基于角色和成员关系）
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

-- 项目创建策略
CREATE POLICY pl_projects_insert ON projects
    FOR INSERT
    TO authenticated_user
    WITH CHECK (
        (SELECT role FROM get_current_user_context()) IN ('admin', 'account_manager')
        AND owner_id = (SELECT user_id FROM get_current_user_context())
    );
```

### 4.4 广告账户表RLS策略
```sql
-- 账户访问策略（四层数据追溯）
CREATE POLICY pl_ad_accounts_access ON ad_accounts
    FOR ALL
    TO authenticated_user
    USING (
        -- 管理员全权限
        (SELECT role FROM get_current_user_context()) = 'admin'
        OR
        -- 数据操作员
        (SELECT role FROM get_current_user_context()) = 'data_operator'
        OR
        -- 财务（只读）
        ((SELECT role FROM get_current_user_context()) = 'finance' AND CURRENT_OPERATION = 'SELECT')
        OR
        -- 项目经理（项目下所有账户）
        EXISTS (
            SELECT 1 FROM projects
            WHERE id = ad_accounts.project_id
            AND owner_id = (SELECT user_id FROM get_current_user_context())
        )
        OR
        -- 客户经理
        EXISTS (
            SELECT 1 FROM projects
            WHERE id = ad_accounts.project_id
            AND account_manager_id = (SELECT user_id FROM get_current_user_context())
        )
        OR
        -- 分配给自己的投手
        assigned_to = (SELECT user_id FROM get_current_user_context())
    );

-- 账户创建策略
CREATE POLICY pl_ad_accounts_insert ON ad_accounts
    FOR INSERT
    TO authenticated_user
    WITH CHECK (
        (SELECT role FROM get_current_user_context()) IN ('admin', 'data_operator')
        AND assigned_to IS NOT NULL
    );
```

### 4.5 日报表RLS策略
```sql
-- 日报访问策略（多层级权限）
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
        -- 项目经理
        EXISTS (
            SELECT 1 FROM projects
            WHERE id = daily_reports.project_id
            AND owner_id = (SELECT user_id FROM get_current_user_context())
        )
        OR
        -- 客户经理
        EXISTS (
            SELECT 1 FROM projects
            WHERE id = daily_reports.project_id
            AND account_manager_id = (SELECT user_id FROM get_current_user_context())
        )
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

-- 日报更新策略（字段级权限）
CREATE POLICY pl_daily_reports_update ON daily_reports
    FOR UPDATE
    TO authenticated_user
    USING (
        -- 管理员和数据操作员
        (SELECT role FROM get_current_user_context()) IN ('admin', 'data_operator')
        OR
        -- 提交者（草稿状态）
        (submitter_id = (SELECT user_id FROM get_current_user_context()) AND status = 'draft')
        OR
        -- 审核者
        (reviewer_id = (SELECT user_id FROM get_current_user_context()) AND status IN ('submitted', 'reviewed'))
    );
```

### 4.6 充值表RLS策略
```sql
-- 充值访问策略（完整流程控制）
CREATE POLICY pl_topups_access ON topups
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
        -- 项目经理（项目下充值）
        EXISTS (
            SELECT 1 FROM projects
            WHERE id = topups.project_id
            AND owner_id = (SELECT user_id FROM get_current_user_context())
        )
        OR
        -- 自己申请的充值
        requester_id = (SELECT user_id FROM get_current_user_context())
        OR
        -- 分配给自己的账户
        EXISTS (
            SELECT 1 FROM ad_accounts
            WHERE id = topups.account_id
            AND assigned_to = (SELECT user_id FROM get_current_user_context())
        )
    );

-- 充值状态更新策略（基于审批流程）
CREATE POLICY pl_topups_status_update ON topups
    FOR UPDATE
    TO authenticated_user
    USING (
        -- 管理员全权限
        (SELECT role FROM get_current_user_context()) = 'admin'
        OR
        -- 数据操作员（初步审核）
        ((SELECT role FROM get_current_user_context()) = 'data_operator'
         AND status IN ('draft', 'pending_review')
         AND CURRENT_COLUMN IN ('clerk_approval', 'status', 'rejection_reason'))
        OR
        -- 财务（财务审核和支付）
        ((SELECT role FROM get_current_user_context()) = 'finance'
         AND status IN ('reviewed', 'approved')
         AND CURRENT_COLUMN IN ('finance_approval', 'status', 'payment_method', 'transaction_id', 'paid_at'))
        OR
        -- 申请人（草稿状态修改）
        (requester_id = (SELECT user_id FROM get_current_user_context())
         AND status = 'draft'
         AND CURRENT_COLUMN IN ('amount', 'urgency_level', 'notes'))
    );
```

---

## 5. 触发器和函数（v2.3增强）

### 5.1 时间戳更新触发器
```sql
-- 通用updated_at更新函数
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
        'reconciliations'
    ]
    LOOP
        EXECUTE format('CREATE TRIGGER trg_%I_updated_at
                        BEFORE UPDATE ON %I
                        FOR EACH ROW EXECUTE FUNCTION trg_update_updated_at()',
                       table_name, table_name);
    END LOOP;
END $$;
```

### 5.2 密码安全函数
```sql
-- 密码强度验证（OWASP标准）
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
```

### 5.3 状态机验证函数
```sql
-- 项目状态转换验证
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

-- 日报状态转换验证
CREATE OR REPLACE FUNCTION validate_daily_report_status_transition(
    current_status TEXT,
    new_status TEXT,
    user_role TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
BEGIN
    -- 基础状态转换规则
    CASE
        WHEN current_status = 'draft' THEN
            RETURN new_status IN ('submitted', 'archived');
        WHEN current_status = 'submitted' THEN
            RETURN new_status IN ('reviewed', 'rejected');
        WHEN current_status = 'reviewed' THEN
            RETURN new_status IN ('approved', 'rejected');
        WHEN current_status = 'approved' THEN
            RETURN new_status IN ('archived');
        WHEN current_status = 'rejected' THEN
            RETURN new_status IN ('draft', 'archived');
        WHEN current_status = 'archived' THEN
            RETURN FALSE;
        ELSE
            RETURN FALSE;
    END CASE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
```

### 5.4 业务逻辑触发器
```sql
-- 审计日志触发器（修复JSON类型转换）
CREATE OR REPLACE FUNCTION trg_audit_log()
RETURNS TRIGGER AS $$
DECLARE
    v_old JSONB;
    v_new JSONB;
    v_changed_fields TEXT[];
BEGIN
    -- 转换为JSONB类型
    v_old := COALESCE(row_to_json(OLD)::JSONB, '{}'::JSONB);
    v_new := row_to_json(NEW)::JSONB;

    -- 查找变更的字段（仅记录敏感字段）
    SELECT array_agg(key)
    INTO v_changed_fields
    FROM (
        SELECT key
        FROM jsonb_each_text(v_new)
        FULL OUTER JOIN jsonb_each_text(v_old) USING (key)
        WHERE v_old->>key IS DISTINCT FROM v_new->>key
        AND key IN ('status', 'amount', 'approved_by', 'paid_at', 'total_spend', 'total_leads', 'assigned_to')
    ) t;

    -- 如果有变更，记录审计日志
    IF array_length(v_changed_fields, 1) > 0 THEN
        INSERT INTO audit_logs (
            event_type,
            user_id,
            resource_type,
            resource_id,
            action,
            old_values,
            new_values,
            changed_fields,
            ip_address,
            user_agent
        ) VALUES (
            TG_TABLE_NAME || '_update',
            COALESCE(
                NULLIF(current_setting('app.current_user_id', true), ''),
                '00000000-0000-0000-0000-000000000000'
            )::UUID,
            TG_TABLE_NAME,
            COALESCE(NEW.id::TEXT, OLD.id::TEXT),
            CASE TG_OP
                WHEN 'INSERT' THEN 'CREATE'
                WHEN 'UPDATE' THEN 'UPDATE'
                WHEN 'DELETE' THEN 'DELETE'
            END,
            v_old,
            v_new,
            v_changed_fields,
            COALESCE(get_app_setting('app.client_ip'), '0.0.0.0')::INET,
            get_app_setting('app.user_agent')
        );
    END IF;

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 账户状态变更触发器（记录历史）
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
            WHEN 'activated' THEN
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

-- 创建触发器
CREATE TRIGGER trg_ad_accounts_status_change
    BEFORE UPDATE ON ad_accounts
    FOR EACH ROW
    WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION trg_account_status_change();

-- 批量创建审计触发器
DO $$
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'users', 'projects', 'ad_accounts', 'daily_reports', 'topups', 'topup_financial'
    ]
    LOOP
        EXECUTE format('CREATE TRIGGER trg_%I_audit
                        AFTER INSERT OR UPDATE OR DELETE ON %I
                        FOR EACH ROW EXECUTE FUNCTION trg_audit_log()',
                       table_name, table_name);
    END LOOP;
END $$;
```

### 5.5 统计更新触发器
```sql
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
            SELECT SUM(spend) FROM daily_reports
            WHERE project_id = COALESCE(NEW.project_id, OLD.project_id)
        ), 0),
        total_leads = COALESCE((
            SELECT SUM(leads_confirmed) FROM daily_reports
            WHERE project_id = COALESCE(NEW.project_id, OLD.project_id)
            AND leads_confirmed IS NOT NULL
        ), 0),
        avg_cpl = CASE
            WHEN COALESCE((
                SELECT SUM(leads_confirmed) FROM daily_reports
                WHERE project_id = COALESCE(NEW.project_id, OLD.project_id)
                AND leads_confirmed IS NOT NULL
            ), 0) > 0
            THEN COALESCE((
                SELECT SUM(spend) FROM daily_reports
                WHERE project_id = COALESCE(NEW.project_id, OLD.project_id)
            ), 0) / (
                SELECT SUM(leads_confirmed) FROM daily_reports
                WHERE project_id = COALESCE(NEW.project_id, OLD.project_id)
                AND leads_confirmed IS NOT NULL
            )
            ELSE NULL
        END
    WHERE id = COALESCE(NEW.project_id, OLD.project_id);

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
CREATE TRIGGER trg_update_project_stats_on_account
    AFTER INSERT OR UPDATE OR DELETE ON ad_accounts
    FOR EACH STATEMENT
    EXECUTE FUNCTION update_project_statistics();

CREATE TRIGGER trg_update_project_stats_on_daily_report
    AFTER INSERT OR UPDATE ON daily_reports
    FOR EACH STATEMENT
    EXECUTE FUNCTION update_project_statistics();
```

---

## 6. 视图定义（v2.3优化）

### 6.1 项目统计视图（增强版）
```sql
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
```

### 6.2 账户绩效视图（实时版）
```sql
CREATE OR REPLACE VIEW account_performance AS
SELECT
    a.id,
    a.account_id,
    a.name,
    a.platform,
    a.status,

    -- 项目和渠道信息
    p.name as project_name,
    p.client_name,
    c.name as channel_name,
    c.company_name as channel_company,

    -- 分配信息
    assigned_user.full_name as assigned_to,
    assigned_user.email as assigned_email,

    -- 预算信息
    a.daily_budget,
    a.lifetime_budget,
    a.remaining_budget,
    a.currency,

    -- 性能数据
    a.total_spend,
    a.total_leads,
    a.avg_cpl,
    a.best_cpl,
    a.today_spend,

    -- 今日数据
    COALESCE(dr.today_spend, 0) as today_actual_spend,
    COALESCE(dr.today_leads, 0) as today_leads,
    COALESCE(dr.today_cpl, 0) as today_cpl,

    -- 生存期
    CASE
        WHEN a.created_date IS NOT NULL AND a.dead_date IS NOT NULL
        THEN EXTRACT(DAYS FROM (a.dead_date - a.created_date))
        WHEN a.created_date IS NOT NULL
        THEN EXTRACT(DAYS FROM (CURRENT_DATE - a.created_date))
        ELSE NULL
    END as lifetime_days,

    -- ROI计算
    CASE
        WHEN a.total_leads > 0 AND p.lead_price > 0
        THEN ROUND((a.total_leads * p.lead_price) / a.total_spend, 2)
        ELSE 0
    END as roi,

    -- 状态持续时间
    EXTRACT(DAYS FROM (CURRENT_DATE - a.last_status_change)) as days_in_current_status,

    -- 质量评分
    a.total_spend / NULLIF(a.total_leads, 0) as actual_cpl,
    c.quality_score as channel_quality,
    c.reliability_score as channel_reliability,

    -- 预警指标
    CASE
        WHEN a.remaining_budget < a.daily_budget * 3 THEN 'critical'
        WHEN a.remaining_budget < a.daily_budget * 7 THEN 'warning'
        ELSE 'normal'
    END as budget_status,

    -- 时间信息
    a.created_at,
    a.updated_at

FROM ad_accounts a
LEFT JOIN projects p ON a.project_id = p.id
LEFT JOIN channels c ON a.channel_id = c.id
LEFT JOIN users assigned_user ON a.assigned_to = assigned_user.id
LEFT JOIN (
    SELECT
        account_id,
        SUM(spend) as today_spend,
        SUM(leads_submitted) as today_leads,
        CASE
            WHEN SUM(leads_submitted) > 0
            THEN ROUND(SUM(spend) / SUM(leads_submitted), 2)
            ELSE 0
        END as today_cpl,
        ROUND(AVG(lead_quality_score), 2) as avg_quality_score
    FROM daily_reports
    WHERE report_date = CURRENT_DATE
    GROUP BY account_id
) dr ON a.id = dr.account_id;
```

### 6.3 用户工作台视图（综合版）
```sql
CREATE OR REPLACE VIEW user_workbench AS
SELECT
    u.id,
    u.full_name,
    u.email,
    u.role,
    u.department,
    u.position,
    u.last_login_at,

    -- 账户管理
    COUNT(DISTINCT a.id) as total_accounts,
    COUNT(DISTINCT CASE WHEN a.status = 'active' THEN a.id END) as active_accounts,
    COUNT(DISTINCT CASE WHEN a.status IN ('new', 'testing') THEN a.id END) as pending_accounts,
    COUNT(DISTINCT CASE WHEN a.status = 'suspended' THEN a.id END) as suspended_accounts,

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

    -- 绩效排名
    RANK() OVER (ORDER BY COALESCE(SUM(CASE WHEN dr.report_date >= date_trunc('month', CURRENT_DATE) THEN dr.leads_submitted END), 0) DESC) as leads_rank,
    RANK() OVER (ORDER BY COALESCE(SUM(CASE WHEN dr.report_date >= date_trunc('month', CURRENT_DATE) THEN dr.spend END), 0) DESC) as spend_rank,

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
LEFT JOIN user_profiles up ON u.id = up.user_id
LEFT JOIN ad_accounts a ON u.id = a.assigned_to
LEFT JOIN daily_reports dr ON a.id = dr.account_id
LEFT JOIN topups t ON u.id = t.requester_id
WHERE u.is_active = true
GROUP BY u.id, u.full_name, u.email, u.role, up.department, up.position, u.last_login_at, u.created_at;
```

---

## 7. 数据初始化和迁移

### 7.1 扩展和类型创建
```sql
-- 创建必要的扩展（移除PostGIS依赖）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
-- 注意：如需地理位置功能，可启用 CREATE EXTENSION IF NOT EXISTS postgis;
-- 当前使用JSONB存储位置信息，避免PostGIS依赖

-- 创建自定义枚举类型
CREATE TYPE project_status_enum AS ENUM ('draft', 'active', 'paused', 'completed', 'cancelled', 'archived');
CREATE TYPE account_status_enum AS ENUM ('draft', 'new', 'testing', 'active', 'suspended', 'dead', 'archived');
CREATE TYPE user_role_enum AS ENUM ('admin', 'finance', 'data_operator', 'account_manager', 'media_buyer');
CREATE TYPE report_status_enum AS ENUM ('draft', 'submitted', 'reviewed', 'approved', 'rejected', 'archived');
CREATE TYPE topup_status_enum AS ENUM ('draft', 'pending_review', 'reviewed', 'approved', 'rejected', 'paid', 'confirmed', 'cancelled', 'refunded');
```

### 7.2 系统配置表
```sql
-- 系统配置表
CREATE TABLE system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    is_encrypted BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 插入默认配置
INSERT INTO system_config (config_key, config_value, description) VALUES
('password_policy', '{"min_length": 12, "require_special": true, "require_numbers": true, "require_mixed_case": true, "max_failed_attempts": 5, "lockout_duration": 1800}', '密码安全策略'),
('session_settings', '{"timeout_hours": 24, "max_concurrent": 3, "require_ip_verification": false}', '会话管理设置'),
('file_upload', '{"max_size_mb": 10, "allowed_types": ["jpg", "png", "pdf", "xlsx", "csv"], "virus_scan": true}', '文件上传限制'),
('notification_settings', '{"email_enabled": true, "sms_enabled": false, "slack_webhook": null}', '通知系统配置'),
('backup_settings', '{"auto_backup": true, "retention_days": 30, "backup_time": "02:00"}', '数据备份设置');
```

### 7.3 初始数据插入（v3.3）
```sql
-- 注意：初始管理员密码应在应用层生成，避免硬编码
-- 以下为示例结构，实际部署时应通过应用接口创建

-- 创建系统配置表（无需RLS，便于运维）
CREATE TABLE system_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    is_encrypted BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 插入默认配置
INSERT INTO system_config (config_key, config_value, description) VALUES
('password_policy', '{"min_length": 12, "require_special": true, "require_numbers": true, "require_mixed_case": true, "max_failed_attempts": 5, "lockout_duration": 1800}', '密码安全策略'),
('session_settings', '{"timeout_hours": 24, "max_concurrent": 3, "require_ip_verification": false}', '会话管理设置'),
('file_upload', '{"max_size_mb": 10, "allowed_types": ["jpg", "png", "pdf", "xlsx", "csv"], "virus_scan": true}', '文件上传限制'),
('notification_settings', '{"email_enabled": true, "sms_enabled": false, "slack_webhook": null}', '通知系统配置'),
('backup_settings', '{"auto_backup": true, "retention_days": 30, "backup_time": "02:00"}', '数据备份设置'),
('app.current_user_id', '"00000000-0000-0000-0000-000000000000"', '当前登录用户ID（由应用层设置）'),
('app.client_ip', '"127.0.0.1"', '客户端IP地址（由应用层设置）'),
('app.user_agent', '""', '用户代理（由应用层设置）');

-- 创建get_app_setting函数
CREATE OR REPLACE FUNCTION get_app_setting(key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN COALESCE(config_value::TEXT, '')
    FROM system_config
    WHERE config_key = 'app.' || key;
END;
$$ LANGUAGE plpgsql;

-- 创建默认管理员用户（密码应在应用层生成）
-- 以下为创建用户的存储过程，实际密码应由应用传入
CREATE OR REPLACE PROCEDURE create_initial_admin()
LANGUAGE plpgsql AS $$
DECLARE
    v_user_id UUID;
BEGIN
    -- 检查是否已有管理员
    IF EXISTS (SELECT 1 FROM users WHERE role = 'admin' AND is_superuser = true) THEN
        RAISE NOTICE '管理员用户已存在，跳过初始化';
        RETURN;
    END IF;

    -- 创建管理员（密码需要通过应用层设置）
    v_user_id := gen_random_uuid();
    INSERT INTO users (
        id, email, username, full_name, role,
        is_active, is_superuser, email_verified,
        password_changed_at
    ) VALUES (
        v_user_id,
        'admin@aiad.com',
        'admin',
        '系统管理员',
        'admin',
        true,
        true,
        true,
        NOW()
    );

    -- 创建用户配置
    INSERT INTO user_profiles (user_id, department, position, preferences)
    VALUES (
        v_user_id,
        'IT',
        '系统管理员',
        '{"theme": "light", "notifications": {"email": true, "browser": true}, "dashboard": {"widgets": ["stats", "charts", "alerts"]}}'
    );

    RAISE NOTICE '管理员用户已创建，请立即通过应用设置密码';
END;
$$;

-- 创建示例数据（在管理员创建之后）
-- 注意：这些数据应该在系统初始化时通过seed脚本插入

-- 创建示例渠道（需要先有管理员）
DO $$
DECLARE
    v_admin_id UUID;
BEGIN
    -- 获取管理员ID
    SELECT id INTO v_admin_id FROM users WHERE role = 'admin' AND is_superuser = true LIMIT 1;

    IF v_admin_id IS NULL THEN
        RAISE NOTICE '未找到管理员用户，跳过示例数据创建';
        RETURN;
    END IF;

    -- 创建示例渠道
    INSERT INTO channels (id, name, code, company_name, platform, service_fee_rate, contact_person, contact_email, status, created_by, updated_by)
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
        v_admin_id,
        v_admin_id
    ON CONFLICT (code) DO NOTHING;

    -- 创建示例项目
    INSERT INTO projects (id, name, code, client_name, client_email, pricing_model, lead_price, setup_fee, status, owner_id, created_by, updated_by)
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
        v_admin_id,
        v_admin_id,
        v_admin_id
    ON CONFLICT (code) DO NOTHING;

    RAISE NOTICE '示例数据创建完成';
END $$;
```

---

## 8. 性能优化和维护

### 8.1 分区策略（报表和日志）
```sql
-- 日报表分区
CREATE TABLE daily_reports (
    LIKE daily_reports INCLUDING ALL
) PARTITION BY RANGE (report_date);

-- 创建自动分区函数（统一命名格式）
CREATE OR REPLACE FUNCTION create_monthly_partition(
    table_name TEXT,
    base_date DATE DEFAULT date_trunc('month', CURRENT_DATE)
)
RETURNS void AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    start_date := date_trunc('month', base_date);
    end_date := start_date + INTERVAL '1 month';
    -- 统一命名格式: YYYYmMM
    partition_name := table_name || '_y' || to_char(start_date, 'YYYY"m"MM');

    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %I
                   FOR VALUES FROM (%L) TO (%L)',
                   partition_name, table_name, start_date, end_date);
END;
$$ LANGUAGE plpgsql;

-- 创建日报表分区
CREATE OR REPLACE FUNCTION create_daily_report_partitions()
RETURNS void AS $$
DECLARE
    i INTEGER;
BEGIN
    -- 创建过去3个月和未来12个月的分区
    FOR i IN -3..12 LOOP
        PERFORM create_monthly_partition('daily_reports', date_trunc('month', CURRENT_DATE) + (i || ' months')::INTERVAL);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 数据迁移函数
CREATE OR REPLACE FUNCTION migrate_to_partitioned_table()
RETURNS void AS $$
BEGIN
    -- 将现有数据迁移到分区表
    INSERT INTO daily_reports_partitioned
    SELECT * FROM daily_reports;

    -- 验证数据一致性
    PERFORM assert_data_consistency();

    -- 重命名表
    ALTER TABLE daily_reports RENAME TO daily_reports_old;
    ALTER TABLE daily_reports_partitioned RENAME TO daily_reports;
END;
$$ LANGUAGE plpgsql;
```

### 8.2 索引维护
```sql
-- 索引使用情况分析
CREATE OR REPLACE VIEW index_usage_analysis AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    CASE
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_scan < 100 THEN 'LOW USAGE'
        WHEN idx_scan < 1000 THEN 'MEDIUM USAGE'
        ELSE 'HIGH USAGE'
    END as usage_level
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- 创建索引优化建议
CREATE OR REPLACE FUNCTION index_optimization_recommendations()
RETURNS TABLE(recommendation TEXT, priority TEXT) AS $$
BEGIN
    RETURN QUERY
    -- 未使用的索引
    SELECT
        'DROP INDEX ' || indexname || ' (unused index)',
        'HIGH'
    FROM index_usage_analysis
    WHERE usage_level = 'UNUSED'

    UNION ALL

    -- 建议的新索引
    SELECT
        'CREATE INDEX CONCURRENTLY idx_daily_reports_monthly ON daily_reports(date_trunc(''month'', report_date), status)',
        'MEDIUM'

    UNION ALL

    -- 需要重建的索引
    SELECT
        'REINDEX INDEX CONCURRENTLY ' || indexname || ' (fragmented)',
        'LOW'
    FROM pg_stat_user_indexes
    WHERE idx_scan > 10000
    ORDER BY idx_scan DESC
    LIMIT 5;
END;
$$ LANGUAGE plpgsql;
```

### 8.3 数据清理和归档
```sql
-- 数据清理策略
CREATE OR REPLACE FUNCTION data_cleanup_policy()
RETURNS void AS $$
DECLARE
    v_rows_deleted INTEGER;
BEGIN
    -- 清理过期会话（超过30天）
    DELETE FROM sessions
    WHERE expires_at < NOW() - INTERVAL '30 days';
    GET DIAGNOSTICS v_rows_deleted = ROW_COUNT;
    RAISE NOTICE '清理过期会话: % 条', v_rows_deleted;

    -- 审计日志分区管理（直接删除旧分区，归档可选）
    -- 注意：分区表直接DROP PARTITION比DELETE更高效
    -- 保留1年的分区
    PERFORM drop_old_partitions('audit_logs', 12);

    -- 清理已拒绝的充值申请（超过90天）
    DELETE FROM topups
    WHERE status = 'rejected'
    AND updated_at < NOW() - INTERVAL '90 days';
    GET DIAGNOSTICS v_rows_deleted = ROW_COUNT;
    RAISE NOTICE '清理拒绝的充值申请: % 条', v_rows_deleted;

    -- 清理过期的临时文件记录
    DELETE FROM temp_files
    WHERE created_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- 删除旧分区函数
CREATE OR REPLACE FUNCTION drop_old_partitions(
    table_name TEXT,
    months_to_keep INTEGER DEFAULT 12
)
RETURNS void AS $$
DECLARE
    cutoff_date DATE := date_trunc('month', CURRENT_DATE) - (months_to_keep || ' months')::INTERVAL;
    partition_name TEXT;
    v_sql TEXT;
BEGIN
    -- 获取需要删除的分区
    FOR partition_name IN
        SELECT inhrelid::regclass::text
        FROM pg_inherits
        WHERE inhparent = table_name::regclass
        AND inhrelid::regclass::text LIKE table_name || '_y%'
    LOOP
        -- 检查分区日期
        IF TO_DATE(SUBSTRING(partition_name FROM '[0-9]{4}'), 'YYYY') < cutoff_date THEN
            v_sql := 'DROP TABLE IF EXISTS ' || partition_name;
            EXECUTE v_sql;
            RAISE NOTICE '删除旧分区: %', partition_name;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 自动维护任务调度
CREATE OR REPLACE FUNCTION schedule_maintenance_tasks()
RETURNS void AS $$
BEGIN
    -- 每日任务
    PERFORM pg_cron.schedule('daily-cleanup', '0 2 * * *', 'SELECT data_cleanup_policy();');

    -- 每周任务
    PERFORM pg_cron.schedule('weekly-analyze', '0 3 * * 0', 'ANALYZE;');

    -- 每月任务
    PERFORM pg_cron.schedule('monthly-reindex', '0 4 1 * *', 'SELECT reindex_needed_indexes();');

    -- 分区维护
    PERFORM pg_cron.schedule('monthly-partitions', '0 5 1 * *', 'SELECT create_daily_report_partitions();');
END;
$$ LANGUAGE plpgsql;
```

---

## 9. 监控和告警

### 9.1 性能监控视图
```sql
-- 查询性能监控
CREATE OR REPLACE VIEW query_performance_dashboard AS
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 20;

-- 表增长监控
CREATE OR REPLACE VIEW table_growth_monitor AS
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS index_size,
    pg_stat_get_tuples_inserted(c.oid) - pg_stat_get_tuples_deleted(c.oid) AS row_growth
FROM pg_tables t
JOIN pg_class c ON c.relname = t.tablename
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 9.2 业务监控视图
```sql
-- 业务健康度仪表板
CREATE OR REPLACE VIEW business_health_dashboard AS
SELECT
    -- 用户活跃度
    (SELECT COUNT(*) FROM users WHERE is_active = true AND last_login_at > NOW() - INTERVAL '7 days') as active_users_week,
    (SELECT COUNT(*) FROM users WHERE is_active = true) as total_active_users,

    -- 账户健康度
    (SELECT COUNT(*) FROM ad_accounts WHERE status = 'active') as active_accounts,
    (SELECT COUNT(*) FROM ad_accounts WHERE remaining_budget < daily_budget * 3) as low_budget_accounts,
    (SELECT COUNT(*) FROM ad_accounts WHERE status = 'suspended') as suspended_accounts,

    -- 日报完成率
    (SELECT COUNT(*) FROM daily_reports WHERE report_date = CURRENT_DATE) as total_reports_today,
    (SELECT COUNT(*) FROM daily_reports WHERE report_date = CURRENT_DATE AND status = 'approved') as approved_reports_today,

    -- 充值状态
    (SELECT COUNT(*) FROM topups WHERE status = 'pending_review') as pending_topups,
    (SELECT SUM(amount) FROM topups WHERE status = 'pending_review') as pending_topup_amount,

    -- 系统负载
    (SELECT COUNT(*) FROM sessions WHERE is_active = true) as active_sessions,

    -- 异常指标
    (SELECT COUNT(*) FROM audit_logs WHERE level = 'high' AND created_at > NOW() - INTERVAL '24 hours') as high_risk_events_24h,
    (SELECT COUNT(*) FROM audit_logs WHERE success = false AND created_at > NOW() - INTERVAL '24 hours') as failed_operations_24h,

    CURRENT_TIMESTAMP as last_updated;
```

---

## 10. 备份和恢复策略

### 10.1 备份脚本（企业版）
```bash
#!/bin/bash
# enterprise_backup.sh - 企业级备份脚本

# 配置参数
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-ad_spend_system}"
DB_USER="${DB_USER:-postgres}"
BACKUP_DIR="${BACKUP_DIR:-/data/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
COMPRESSION_LEVEL="${COMPRESSION_LEVEL:-9}"
S3_BUCKET="${S3_BUCKET:-ad-spend-backups}"

# 创建备份目录
mkdir -p "$BACKUP_DIR"/{daily,weekly,monthly}
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/daily/ad_spend_system_$DATE.dump"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$BACKUP_DIR/backup.log"
}

# 错误处理
set -e
trap 'log "ERROR: Backup failed at line $LINENO"' ERR

# 开始备份
log "开始全量备份..."

# 1. 全量备份
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --format=custom \
    --compress="$COMPRESSION_LEVEL" \
    --verbose \
    --exclude-table-data='audit_logs' \
    --exclude-table-data='sessions' \
    --file="$BACKUP_FILE"

# 2. 压缩备份
gzip -f "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"

# 3. 验证备份
log "验证备份文件..."
pg_restore --list "$BACKUP_FILE" > /dev/null
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

# 4. 上传到S3（如果配置了）
if [ ! -z "$S3_BUCKET" ]; then
    log "上传备份到S3..."
    aws s3 cp "$BACKUP_FILE" "s3://$S3_BUCKET/daily/ad_spend_system_$DATE.dump.gz"
    log "备份已上传到S3"
fi

# 5. 清理旧备份
find "$BACKUP_DIR/daily" -name "*.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR/weekly" -name "*.gz" -mtime +$((RETENTION_DAYS * 4)) -delete
find "$BACKUP_DIR/monthly" -name "*.gz" -mtime +$((RETENTION_DAYS * 12)) -delete

log "备份完成: $BACKUP_FILE (大小: $BACKUP_SIZE)"

# 6. 发送通知
if [ ! -z "$WEBHOOK_URL" ]; then
    curl -X POST "$WEBHOOK_URL" \
        -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ 数据库备份完成\\n文件: $BACKUP_FILE\\n大小: $BACKUP_SIZE\"}"
fi
```

### 10.2 恢复脚本（企业版）
```bash
#!/bin/bash
# enterprise_restore.sh - 企业级恢复脚本

# 参数检查
if [ $# -lt 1 ]; then
    echo "用法: $0 <backup_file> [target_database]"
    echo "示例: $0 /backups/daily/ad_spend_system_20241111_020000.dump.gz restored_db"
    exit 1
fi

BACKUP_FILE="$1"
TARGET_DB="${2:-ad_spend_system_restored}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"

# 验证备份文件
if [ ! -f "$BACKUP_FILE" ]; then
    echo "错误: 备份文件不存在: $BACKUP_FILE"
    exit 1
fi

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "开始数据库恢复..."
log "备份文件: $BACKUP_FILE"
log "目标数据库: $TARGET_DB"

# 1. 停止应用服务
log "停止应用服务..."
systemctl stop your-app-service || true

# 2. 备份当前数据库
log "备份当前数据库..."
BACKUP_CURRENT="$BACKUP_DIR/emergency_backup_$(date +%Y%m%d_%H%M%S).dump"
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$TARGET_DB" \
    --format=custom \
    --file="$BACKUP_CURRENT" || true

# 3. 删除并重建数据库
log "重建目标数据库..."
dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$TARGET_DB" || true
createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$TARGET_DB"

# 4. 恢复数据
log "恢复数据中..."
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | pg_restore \
        -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
        -d "$TARGET_DB" \
        --verbose \
        --clean --if-exists \
        --disable-triggers \
        --no-data-for-failed-tables
else
    pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
        -d "$TARGET_DB" \
        --verbose \
        --clean --if-exists \
        --disable-triggers \
        --no-data-for-failed-tables \
        "$BACKUP_FILE"
fi

# 5. 启用约束和触发器
log "启用约束和触发器..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$TARGET_DB" -c "
    ALTER TABLE users ENABLE TRIGGER ALL;
    ALTER TABLE ad_accounts ENABLE TRIGGER ALL;
    -- 其他表...
"

# 6. 更新统计信息
log "更新数据库统计信息..."
ANALYZE;

# 7. 验证恢复结果
log "验证恢复结果..."
TABLE_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$TARGET_DB" -t -c "
    SELECT COUNT(*) FROM information_schema.tables
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
")

USER_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$TARGET_DB" -t -c "
    SELECT COUNT(*) FROM users;
")

log "恢复验证结果:"
log "  - 表数量: $TABLE_COUNT"
log "  - 用户数量: $USER_COUNT"

# 8. 启动应用服务
log "启动应用服务..."
systemctl start your-app-service

log "数据库恢复完成！"

# 9. 发送通知
if [ ! -z "$WEBHOOK_URL" ]; then
    curl -X POST "$WEBHOOK_URL" \
        -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ 数据库恢复完成\\n目标: $TARGET_DB\\n表数: $TABLE_COUNT\\n用户数: $USER_COUNT\"}"
fi
```

---

## 11. v3.3版本优化总结

### 11.1 已修复的P0级别问题
1. **PostGIS依赖问题** - 移除地理位置字段，改用JSONB存储
2. **分区命名不一致** - 统一使用 `YYYYmMM` 格式
3. **RLS类型转换风险** - 使用COALESCE防止空值错误

### 11.2 已修复的P1级别问题
1. **审计触发器JSON类型** - 修复JSONB转换问题
2. **财务表删除策略** - topups外键改为SET NULL
3. **密码初始化安全** - 移除硬编码，使用应用层生成

### 11.3 已修复的P2级别问题
1. **IP/UA字段安全** - 添加默认值防止转换错误
2. **审计日志优化** - 仅记录敏感字段变更
3. **系统配置管理** - 集中配置，system_config表不启用RLS

### 11.4 新增功能
1. **充值业务和财务分离** - 新增topup_financial表
2. **自动分区管理** - 统一的分区创建和管理函数
3. **数据清理优化** - 使用DROP PARTITION替代DELETE

### 11.5 部署建议
1. 在启用RLS之前插入初始数据
2. 使用gen_random_uuid()替代uuid_generate_v4()（PostgreSQL 12+）
3. 初始管理员密码通过应用接口设置
4. 定期执行分区创建和数据清理任务

---

**文档版本**: v3.3
**最后更新**: 2025-11-12
**负责人**: 数据库架构师
**审核人**: 系统架构师
**状态**: 生产就绪