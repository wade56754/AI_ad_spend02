# 数据库设计与RLS策略

> **文档目的**: 提供完整的数据库设计、字段约束、RLS策略和数据关系
> **目标读者**: 数据库管理员、后端开发工程师、架构师
> **更新日期**: 2025-11-10

---

## 1. 数据库设计原则

### 1.1 核心设计原则
- **数据完整性**: 使用外键约束确保数据关系完整性
- **追溯性**: 所有业务数据必须能追溯到"项目+渠道+账户+投手"
- **安全性**: 使用RLS行级安全策略保护敏感数据
- **性能优化**: 合理的索引设计和分区策略
- **一致性**: 统一的命名规范和字段类型

### 1.2 字段规范
```sql
-- 统一字段规范
- 主键: UUID (gen_random_uuid())
- 外键: UUID (关联其他表主键)
- 金额字段: NUMERIC(15,2) (支持最大999万亿，精度2位小数)
- 费率字段: NUMERIC(5,4) (支持0.01%-100%费率，精度4位小数)
- 状态字段: VARCHAR(20) (状态枚举值)
- 时间字段: TIMESTAMP WITH TIME ZONE (默认UTC)
- 布尔字段: BOOLEAN (true/false)
- JSON字段: JSONB (灵活的元数据存储)
- 文本字段: TEXT (大文本内容)

-- 统一约束规范
- 非空约束: 关键业务字段必须NOT NULL
- 唯一约束: 业务唯一标识必须UNIQUE
- 检查约束: 业务规则使用CHECK约束
- 外键约束: 明确删除策略(SET NULL/CASCADE)
- 默认值: 合理的默认值设置
```

### 1.3 命名规范
```sql
-- 表名: 小写复数，下划线分隔
projects, ad_accounts, topups, daily_reports

-- 字段名: 小写，下划线分隔
created_at, updated_at, user_id, account_name

-- 索引名: 表名_字段名_idx
idx_projects_status, idx_ad_accounts_user_id

-- 外键名: 表名_字段名_fk
fk_projects_manager_id, fk_topups_project_id

-- 约束名: 表名_字段名_约束类型
ck_projects_status, uq_accounts_account_id
```

---

## 2. 核心表结构

### 2.1 用户表 (users)
```sql
CREATE TABLE public.users (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 基本信息
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),

    -- 角色和权限
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'manager', 'data_clerk', 'finance', 'media_buyer')),
    is_active BOOLEAN DEFAULT true,

    -- 登录信息
    last_login TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0,

    -- 联系信息
    phone VARCHAR(50),
    avatar_url VARCHAR(500),

    -- 管理信息
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);

-- 约束
ALTER TABLE users ADD CONSTRAINT ck_users_role
    CHECK (role IN ('admin', 'manager', 'data_clerk', 'finance', 'media_buyer'));
```

### 2.2 项目表 (projects)
```sql
CREATE TABLE public.projects (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

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
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_client_name ON projects(client_name);
CREATE INDEX idx_projects_manager_id ON projects(manager_id);
CREATE INDEX idx_projects_created_by ON projects(created_by);
CREATE INDEX idx_projects_created_at ON projects(created_at);
CREATE INDEX idx_projects_pricing_model ON projects(pricing_model);

-- 唯一约束
ALTER TABLE projects ADD CONSTRAINT uq_projects_code UNIQUE (code);
```

### 2.3 渠道表 (channels)
```sql
CREATE TABLE public.channels (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

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
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_channels_status ON channels(status);
CREATE INDEX idx_channels_quality_score ON channels(quality_score);
CREATE INDEX idx_channels_code ON channels(code);
CREATE INDEX idx_channels_company_name ON channels(company_name);

-- 唯一约束
ALTER TABLE channels ADD CONSTRAINT uq_channels_code UNIQUE (code);
```

### 2.4 广告账户表 (ad_accounts)
```sql
CREATE TABLE public.ad_accounts (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

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
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_ad_accounts_project_id ON ad_accounts(project_id);
CREATE INDEX idx_ad_accounts_channel_id ON ad_accounts(channel_id);
CREATE INDEX idx_ad_accounts_assigned_user_id ON ad_accounts(assigned_user_id);
CREATE INDEX idx_ad_accounts_status ON ad_accounts(status);
CREATE INDEX idx_ad_accounts_platform ON ad_accounts(platform);
CREATE INDEX idx_ad_accounts_account_id ON ad_accounts(account_id);
CREATE INDEX idx_ad_accounts_created_date ON ad_accounts(created_date);

-- 唯一约束
ALTER TABLE ad_accounts ADD CONSTRAINT uq_ad_accounts_account_id UNIQUE (account_id);

-- 检查约束
ALTER TABLE ad_accounts ADD CONSTRAINT ck_ad_accounts_platform
    CHECK (platform IN ('facebook', 'instagram', 'google', 'tiktok'));
```

### 2.5 账户状态历史表 (account_status_history)
```sql
CREATE TABLE public.account_status_history (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

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

-- 索引
CREATE INDEX idx_account_status_history_account_id ON account_status_history(account_id);
CREATE INDEX idx_account_status_history_changed_at ON account_status_history(changed_at);
CREATE INDEX idx_account_status_history_changed_by ON account_status_history(changed_by);
```

### 2.6 充值表 (topups)
```sql
CREATE TABLE public.topups (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

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
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_topups_project_id ON topups(project_id);
CREATE INDEX idx_topups_ad_account_id ON topups(ad_account_id);
CREATE INDEX idx_topups_requested_by ON topups(requested_by);
CREATE INDEX idx_topups_status ON topups(status);
CREATE INDEX idx_topups_created_at ON topups(created_at);
CREATE INDEX idx_topups_paid_at ON topups(paid_at) WHERE paid_at IS NOT NULL;

-- 检查约束
ALTER TABLE topups ADD CONSTRAINT ck_topups_status
    CHECK (status IN ('draft', 'pending', 'clerk_approved', 'finance_approved', 'paid', 'posted', 'rejected'));
ALTER TABLE topups ADD CONSTRAINT ck_topups_urgency_level
    CHECK (urgency_level IN ('normal', 'urgent'));
```

### 2.7 日报表 (ad_spend_daily)
```sql
CREATE TABLE public.ad_spend_daily (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

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

-- 索引
CREATE INDEX idx_ad_spend_daily_project_id ON ad_spend_daily(project_id);
CREATE INDEX idx_ad_spend_daily_ad_account_id ON ad_spend_daily(ad_account_id);
CREATE INDEX idx_ad_spend_daily_user_id ON ad_spend_daily(user_id);
CREATE INDEX idx_ad_spend_daily_date ON ad_spend_daily(date);
CREATE INDEX idx_ad_spend_daily_leads_confirmed ON ad_spend_daily(leads_confirmed) WHERE leads_confirmed IS NOT NULL;
CREATE INDEX idx_ad_spend_daily_spend ON ad_spend_daily(spend) WHERE spend > 0;
```

### 2.8 对账表 (reconciliations)
```sql
CREATE TABLE public.reconciliations (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

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

-- 索引
CREATE INDEX idx_reconciliations_project_id ON reconciliations(project_id);
CREATE INDEX idx_reconciliations_period ON reconciliations(period_type, period_start, period_end);
CREATE INDEX idx_reconciliations_status ON reconciliations(status);
CREATE INDEX idx_reconciliations_created_at ON reconciliations(created_at);
```

### 2.9 财务流水表 (ledgers)
```sql
CREATE TABLE public.ledgers (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

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

-- 索引
CREATE INDEX idx_ledgers_project_id ON ledgers(project_id);
CREATE INDEX idx_ledgers_topup_id ON ledgers(topup_id);
CREATE INDEX idx_ledgers_transaction_type ON ledgers(transaction_type);
CREATE INDEX idx_ledgers_created_at ON ledgers(created_at);
```

### 2.10 操作日志表 (audit_logs)
```sql
CREATE TABLE public.audit_logs (
    -- 主键
    id BIGSERIAL PRIMARY KEY,

    -- 操作信息
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(255),
    record_id VARCHAR(255),

    -- 变更数据
    old_values JSONB,
    new_values JSONB,

    -- 请求信息
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(255),

    -- 严重程度
    level VARCHAR(20) DEFAULT 'medium'
        CHECK (level IN ('low', 'medium', 'high', 'critical')),

    -- 描述信息
    description TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_table_name ON audit_logs(table_name);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_level ON audit_logs(level);
```

### 2.11 导入任务表 (import_jobs)
```sql
CREATE TABLE public.import_jobs (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

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

-- 索引
CREATE INDEX idx_import_jobs_status ON import_jobs(status);
CREATE INDEX idx_import_jobs_job_type ON import_jobs(job_type);
CREATE INDEX idx_import_jobs_created_by ON import_jobs(created_by);
CREATE INDEX idx_import_jobs_created_at ON import_jobs(created_at);
```

---

## 3. RLS安全策略

### 3.1 RLS基础配置
```sql
-- 启用RLS的表
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE topups ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_spend_daily ENABLE ROW LEVEL SECURITY;
ALTER TABLE reconciliations ENABLE ROW LEVEL SECURITY;
ALTER TABLE ledgers ENABLE ROW LEVEL SECURITY;

-- 不启用RLS的表 (只读或系统表)
-- audit_logs (所有审计记录可查看，但敏感字段加密)
-- import_jobs (根据任务创建者过滤)
-- users (通过应用层权限控制)
```

### 3.2 项目表RLS策略
```sql
-- 项目访问策略
CREATE POLICY "项目访问策略" ON projects
    FOR ALL
    USING (
        -- 管理员全权限
        current_setting('app.current_role') = 'admin'
        OR
        -- 项目经理只能访问自己的项目
        manager_id = current_setting('app.current_user_id')::uuid
        OR
        -- 户管、财务可访问所有项目（业务需要）
        current_setting('app.current_role') IN ('data_clerk', 'finance')
        OR
        -- 投手只能访问分配给自己的项目
        EXISTS (
            SELECT 1 FROM ad_accounts
            WHERE ad_accounts.project_id = projects.id
            AND ad_accounts.assigned_user_id = current_setting('app.current_user_id')::uuid
        )
    );

-- 项目修改策略
CREATE POLICY "项目修改策略" ON projects
    FOR INSERT WITH CHECK (
        -- 管理员可以创建
        current_setting('app.current_role') = 'admin'
        OR
        -- 项目经理可以创建
        current_setting('app.current_role') = 'manager'
    );

CREATE POLICY "项目更新策略" ON projects
    FOR UPDATE
    USING (
        -- 管理员可以更新所有项目
        current_setting('app.current_role') = 'admin'
        OR
        -- 项目经理只能更新自己的项目
        manager_id = current_setting('app.current_user_id')::uuid
    );

-- 项目删除策略
CREATE POLICY "项目删除策略" ON projects
    FOR DELETE
    USING (
        -- 只有管理员可以删除项目
        current_setting('app.current_role') = 'admin'
    );
```

### 3.3 广告账户表RLS策略
```sql
-- 账户访问策略
CREATE POLICY "账户访问策略" ON ad_accounts
    FOR ALL
    USING (
        -- 管理员全权限
        current_setting('app.current_role') = 'admin'
        OR
        -- 户管可访问所有账户
        current_setting('app.current_role') = 'data_clerk'
        OR
        -- 财务可查看所有账户
        (current_setting('app.current_role') = 'finance' AND CURRENT_OPERATION IN ('SELECT', 'UPDATE'))
        OR
        -- 项目经理可访问项目下所有账户
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = ad_accounts.project_id
            AND projects.manager_id = current_setting('app.current_user_id')::uuid
        )
        OR
        -- 投手只能访问分配给自己的账户
        assigned_user_id = current_setting('app.current_user_id')::uuid
    );

-- 账户修改策略
CREATE POLICY "账户修改策略" ON ad_accounts
    FOR INSERT WITH CHECK (
        -- 管理员和户管可以创建账户
        current_setting('app.current_role') IN ('admin', 'data_clerk')
    );

CREATE POLICY "账户更新策略" ON ad_accounts
    FOR UPDATE
    USING (
        -- 管理员和户管可以更新所有账户
        current_setting('app.current_role') IN ('admin', 'data_clerk')
        OR
        -- 项目经理可以更新项目下账户的某些字段
        (current_setting('app.current_role') = 'manager'
         AND EXISTS (
             SELECT 1 FROM projects
             WHERE projects.id = ad_accounts.project_id
             AND projects.manager_id = current_setting('app.current_user_id')::uuid
         )
         AND CURRENT_COLUMN IN ('notes', 'tags', 'metadata'))
        OR
        -- 投手可以更新自己账户的某些字段
        (assigned_user_id = current_setting('app.current_user_id')::uuid
         AND CURRENT_COLUMN IN ('notes', 'metadata'))
    );
```

### 3.4 充值表RLS策略
```sql
-- 充值访问策略
CREATE POLICY "充值访问策略" ON topups
    FOR ALL
    USING (
        -- 管理员全权限
        current_setting('app.current_role') = 'admin'
        OR
        -- 户管可访问所有充值申请
        current_setting('app.current_role') = 'data_clerk'
        OR
        -- 财务可访问所有充值申请
        current_setting('app.current_role') = 'finance'
        OR
        -- 项目经理可访问项目下充值
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = topups.project_id
            AND projects.manager_id = current_setting('app.current_user_id')::uuid
        )
        OR
        -- 投手只能访问自己的充值申请
        requested_by = current_setting('app.current_user_id')::uuid
    );

-- 充值创建策略
CREATE POLICY "充值创建策略" ON topups
    FOR INSERT WITH CHECK (
        -- 投手、户管、管理员可以创建充值申请
        current_setting('app.current_role') IN ('media_buyer', 'data_clerk', 'admin', 'manager')
    );

-- 充值更新策略
CREATE POLICY "充值更新策略" ON topups
    FOR UPDATE
    USING (
        -- 管理员可以更新所有字段
        current_setting('app.current_role') = 'admin'
        OR
        -- 户管只能审批或拒绝
        (current_setting('app.current_role') = 'data_clerk'
         AND CURRENT_COLUMN IN ('clerk_approval', 'status', 'rejection_reason'))
        OR
        -- 财务只能财务审批或执行
        (current_setting('app.current_role') = 'finance'
         AND CURRENT_COLUMN IN ('finance_approval', 'status', 'payment_method', 'transaction_id'))
        OR
        -- 投手只能修改草稿状态
        (requested_by = current_setting('app.current_user_id')::uuid
         AND status = 'draft'
         AND CURRENT_COLUMN IN ('amount', 'purpose', 'urgency_level'))
    );
```

### 3.5 日报表RLS策略
```sql
-- 日报访问策略
CREATE POLICY "日报访问策略" ON ad_spend_daily
    FOR ALL
    USING (
        -- 管理员全权限
        current_setting('app.current_role') = 'admin'
        OR
        -- 户管可访问所有日报
        current_setting('app.current_role') = 'data_clerk'
        OR
        -- 财务可查看所有日报
        current_setting('app.current_role') = 'finance'
        OR
        -- 项目经理可访问项目下日报
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = ad_spend_daily.project_id
            AND projects.manager_id = current_setting('app.current_user_id')::uuid
        )
        OR
        -- 投手只能访问自己的日报
        user_id = current_setting('app.current_user_id')::uuid
    );

-- 日报创建策略
CREATE POLICY "日报创建策略" ON ad_spend_daily
    FOR INSERT WITH CHECK (
        -- 投手、户管、管理员可以创建日报
        current_setting('app.current_role') IN ('media_buyer', 'data_clerk', 'admin', 'manager')
        -- 确保只能创建自己账户的日报
        AND ad_account_id IN (
            SELECT id FROM ad_accounts
            WHERE assigned_user_id = current_setting('app.current_user_id')::uuid
               OR current_setting('app.current_role') IN ('admin', 'data_clerk', 'manager')
        )
    );

-- 日报更新策略
CREATE POLICY "日报更新策略" ON ad_spend_daily
    FOR UPDATE
    USING (
        -- 管理员可以更新所有字段
        current_setting('app.current_role') = 'admin'
        OR
        -- 户管只能确认或拒绝
        (current_setting('app.current_role') = 'data_clerk'
         AND CURRENT_COLUMN IN ('leads_confirmed', 'confirmed_by', 'confirmed_at', 'diff_reason'))
        OR
        -- 投手只能更新草稿状态
        (user_id = current_setting('app.current_user_id')::uuid
         AND leads_confirmed IS NULL
         AND CURRENT_COLUMN IN ('leads_submitted', 'spend', 'impressions', 'clicks'))
    );
```

### 3.6 对账表RLS策略
```sql
-- 对账访问策略
CREATE POLICY "对账访问策略" ON reconciliations
    FOR ALL
    USING (
        -- 管理员全权限
        current_setting('app.current_role') = 'admin'
        OR
        -- 财务可访问所有对账
        current_setting('app.current_role') = 'finance'
        OR
        -- 项目经理可访问项目对账
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = reconciliations.project_id
            AND projects.manager_id = current_setting('app.current_user_id')::uuid
        )
    );

-- 对账创建策略
CREATE POLICY "对账创建策略" ON reconciliations
    FOR INSERT WITH CHECK (
        -- 财务和管理员可以创建对账
        current_setting('app.current_role') IN ('finance', 'admin')
    );
```

---

## 4. 触发器和函数

### 4.1 更新时间戳触发器
```sql
-- 创建更新时间戳函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为所有表添加触发器
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
```

### 4.2 账户状态变更触发器
```sql
-- 账户状态变更历史函数
CREATE OR REPLACE FUNCTION log_account_status_change()
RETURNS TRIGGER AS $$
DECLARE
    old_status TEXT;
BEGIN
    -- 获取旧状态
    SELECT status INTO old_status
    FROM ad_accounts
    WHERE id = NEW.id;

    -- 只有状态真正变化时才记录
    IF old_status IS DISTINCT FROM NEW.status THEN
        -- 记录状态变更历史
        INSERT INTO account_status_history (
            account_id,
            old_status,
            new_status,
            change_reason,
            changed_at,
            changed_by,
            change_source,
            performance_data
        ) VALUES (
            NEW.id,
            old_status,
            NEW.status,
            NEW.status_reason,
            CURRENT_TIMESTAMP,
            NEW.updated_by,
            'manual',
            jsonb_build_object(
                'total_spend', NEW.total_spend,
                'total_leads', NEW.total_leads,
                'avg_cpl', NEW.avg_cpl
            )
        );

        -- 更新状态时间戳
        NEW.last_status_change = CURRENT_TIMESTAMP;

        -- 根据新状态更新特定时间戳
        CASE NEW.status
            WHEN 'active' THEN
                NEW.activated_date = COALESCE(NEW.activated_date, CURRENT_TIMESTAMP);
            WHEN 'suspended' THEN
                NEW.suspended_date = CURRENT_TIMESTAMP;
            WHEN 'dead' THEN
                NEW.dead_date = CURRENT_TIMESTAMP;
            WHEN 'archived' THEN
                NEW.archived_date = CURRENT_TIMESTAMP;
        END CASE;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
CREATE TRIGGER account_status_change_trigger
    BEFORE UPDATE ON ad_accounts
    FOR EACH ROW
    WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION log_account_status_change();
```

### 4.3 余额更新触发器
```sql
-- 账户余额更新函数
CREATE OR REPLACE FUNCTION update_account_balance()
RETURNS TRIGGER AS $$
DECLARE
    account RECORD;
BEGIN
    -- 获取账户信息
    SELECT * INTO account
    FROM ad_accounts
    WHERE id = NEW.ad_account_id;

    -- 如果是充值到账
    IF TG_OP = 'INSERT' AND NEW.status = 'posted' THEN
        UPDATE ad_accounts
        SET remaining_budget = account.remaining_budget + NEW.amount
        WHERE id = NEW.ad_account_id;

        -- 记录余额变更日志
        INSERT INTO account_balance_history (
            account_id,
            change_amount,
            balance_before,
            balance_after,
            change_type,
            reference_id,
            changed_at,
            changed_by
        ) VALUES (
            NEW.ad_account_id,
            NEW.amount,
            account.remaining_budget,
            account.remaining_budget + NEW.amount,
            'topup',
            NEW.id,
            CURRENT_TIMESTAMP,
            NEW.created_by
        );
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
CREATE TRIGGER update_account_balance_trigger
    AFTER INSERT ON topups
    FOR EACH ROW
    WHEN (NEW.status = 'posted')
    EXECUTE FUNCTION update_account_balance();
```

### 4.4 自动统计更新触发器
```sql
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
            WHERE project_id = projects.id
        ),
        active_accounts = (
            SELECT COUNT(*) FROM ad_accounts
            WHERE project_id = projects.id AND status = 'active'
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

-- 创建触发器
CREATE TRIGGER update_project_statistics_trigger
    AFTER INSERT OR UPDATE OR DELETE ON ad_accounts
    FOR EACH STATEMENT EXECUTE FUNCTION update_project_statistics();

CREATE TRIGGER update_project_statistics_daily_trigger
    AFTER INSERT OR UPDATE ON ad_spend_daily
    FOR EACH STATEMENT EXECUTE FUNCTION update_project_statistics();
```

---

## 5. 视图定义

### 5.1 项目统计视图
```sql
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
LEFT JOIN ad_accounts a ON p.id = a.project_id
LEFT JOIN ad_spend_daily dr ON a.id = dr.ad_account_id
GROUP BY p.id, p.name, p.client_name, p.status, p.pricing_model, p.lead_price, p.setup_fee, p.created_at, p.updated_at;
```

### 5.2 渠道表现视图
```sql
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
LEFT JOIN ad_accounts a ON c.id = a.channel_id
LEFT JOIN topups t ON a.id = t.ad_account_id AND t.status = 'posted'
GROUP BY c.id, c.name, c.company_name, c.service_fee_rate, c.status, c.created_at, c.updated_at;
```

### 5.3 用户工作统计视图
```sql
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
LEFT JOIN ad_accounts a ON u.id = a.assigned_user_id
LEFT JOIN ad_spend_daily dr ON a.id = dr.ad_account_id
LEFT JOIN topups t ON u.id = t.requested_by
GROUP BY u.id, u.full_name, u.email, u.role, u.last_login;
```

---

## 6. 数据迁移脚本

### 6.1 初始化脚本
```sql
-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- 创建自定义类型
CREATE TYPE project_status AS ENUM ('planning', 'active', 'paused', 'completed', 'cancelled');
CREATE TYPE pricing_model AS ENUM ('per_lead', 'fixed_fee', 'hybrid');
CREATE TYPE account_status AS ENUM ('new', 'testing', 'active', 'suspended', 'dead', 'archived');
CREATE TYPE topup_status AS ENUM ('draft', 'pending', 'clerk_approved', 'finance_approved', 'paid', 'posted', 'rejected');
CREATE TYPE user_role AS ENUM ('admin', 'manager', 'data_clerk', 'finance', 'media_buyer');

-- 创建枚举约束函数
CREATE OR REPLACE FUNCTION validate_project_status(status TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN status IN ('planning', 'active', 'paused', 'completed', 'cancelled');
END;
$$ LANGUAGE plpgsql;

-- 创建检查约束
ALTER TABLE projects ADD CONSTRAINT ck_projects_status
    CHECK (validate_project_status(status::text));
```

### 6.2 示例数据插入
```sql
-- 插入示例用户
INSERT INTO users (id, email, hashed_password, full_name, role, is_active) VALUES
('550e8400-e29b-41d4-a716-446655440000', 'admin@example.com', '$2b$12$...', '系统管理员', 'admin', true),
('550e8400-e29b-41d4-a716-446655440001', 'manager@example.com', '$2b$12$...', '项目经理', 'manager', true),
('550e8400-e29b-41d4-a716-446655440002', 'data_clerk@example.com', '$2b$12$...', '数据员', 'data_clerk', true),
('550e8400-e29b-41d4-a716-446655440003', 'finance@example.com', '$2b$12$...', '财务', 'finance', true),
('550e8400-e29b-41d4-a716-446655440004', 'buyer@example.com', '$2b$12$...', '投手', 'media_buyer', true);

-- 插入示例渠道
INSERT INTO channels (id, name, code, company_name, service_fee_rate, contact_person, contact_email) VALUES
('660f9500-f39c-52e5-b827-557755550000', '优质渠道A', 'channel_a', '优质广告有限公司', 0.08, '张经理', 'contact@channela.com'),
('660f9500-f39c-52e5-b827-557755550001', '标准渠道B', 'channel_b', '标准广告代理', 0.10, '李经理', 'contact@channelb.com');

-- 插入示例项目
INSERT INTO projects (id, name, code, client_name, pricing_model, lead_price, setup_fee, manager_id, created_by) VALUES
('770f0600-g40d-63f6-c938-668866660000', '测试项目A', 'proj_a', '测试客户A', 'per_lead', 15.00, 5000.00, '550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440000');

-- 插入示例账户
INSERT INTO ad_accounts (id, account_id, name, project_id, channel_id, assigned_user_id, status, daily_budget) VALUES
('880f1700-h51e-74f7-da49-779977770000', 'act_1234567890', 'Facebook账户A', '770f0600-g40d-63f6-c938-668866660000', '660f9500-f39c-52e5-b827-557755550000', '550e8400-e29b-41d4-a716-446655440004', 'new', 500.00);
```

### 6.3 数据验证脚本
```sql
-- 验证数据完整性
DO $$
DECLARE
    error_count INTEGER := 0;
    error_message TEXT;
BEGIN
    -- 检查外键完整性
    IF EXISTS (SELECT 1 FROM ad_accounts a LEFT JOIN projects p ON a.project_id = p.id WHERE p.id IS NULL) THEN
        error_count := error_count + 1;
        RAISE NOTICE '发现孤立的项目账户记录';
    END IF;

    IF EXISTS (SELECT 1 FROM topups t LEFT JOIN ad_accounts a ON t.ad_account_id = a.id WHERE a.id IS NULL) THEN
        error_count := error_count + 1;
        RAISE NOTICE '发现孤立的充值记录';
    END IF;

    -- 检查业务规则
    IF EXISTS (SELECT 1 FROM ad_accounts a WHERE a.assigned_user_id IS NULL AND a.status = 'active') THEN
        error_count := error_count + 1;
        RAISE NOTICE '发现未分配的活跃账户';
    END IF;

    -- 输出验证结果
    IF error_count = 0 THEN
        RAISE NOTICE '数据完整性验证通过';
    ELSE
        RAISE NOTICE '数据完整性验证发现问题，请检查上述记录';
    END IF;
END;
$$;
```

---

## 7. 性能优化

### 7.1 索引策略
```sql
-- 复合索引
CREATE INDEX idx_ad_accounts_project_status ON ad_accounts(project_id, status);
CREATE INDEX idx_topups_project_status ON topups(project_id, status);
CREATE INDEX idx_ad_spend_daily_account_date ON ad_spend_daily(ad_account_id, date);
CREATE INDEX idx_ledgers_project_type ON ledgers(project_id, transaction_type);

-- 部分索引 (WHERE条件索引)
CREATE INDEX idx_ad_accounts_active ON ad_accounts(status) WHERE status = 'active';
CREATE INDEX idx_topups_pending ON topups(status) WHERE status = 'pending';
CREATE INDEX idx_ad_spend_daily_confirmed ON ad_spend_daily(leads_confirmed) WHERE leads_confirmed IS NOT NULL;

-- 表达式索引
CREATE INDEX idx_ad_spend_daily_cpl ON ad_spend_daily((spend / NULLIF(leads_confirmed, 0))) WHERE leads_confirmed > 0;
CREATE INDEX idx_projects_profit ON projects((setup_fee + (lead_price * NULLIF(total_leads, 0)) - NULLIF(total_spend, 0)));
```

### 7.2 分区表设计
```sql
-- 日报表按月分区
CREATE TABLE ad_spend_daily_partitioned (
    LIKE ad_spend_daily INCLUDING ALL
) PARTITION BY RANGE (date);

-- 创建分区
CREATE TABLE ad_spend_daily_y2024m01 PARTITION OF ad_spend_daily_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE ad_spend_daily_y2024m02 PARTITION OF ad_spend_daily_partitioned
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- 自动创建未来分区的函数
CREATE OR REPLACE FUNCTION create_monthly_partitions(table_name TEXT, months_ahead INTEGER)
RETURNS VOID AS $$
DECLARE
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
    i INTEGER;
BEGIN
    FOR i IN 0..months_ahead LOOP
        start_date := date_trunc('month', CURRENT_DATE) + (i || ' months')::INTERVAL;
        end_date := start_date + INTERVAL '1 month';

        partition_name := table_name || '_y' || to_char(start_date, 'YYYY') || 'm' || to_char(start_date, 'MM');

        EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %I
                          FOR VALUES FROM (%L) TO (%L)',
                         partition_name, table_name, start_date, end_date);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 定期维护任务
CREATE OR REPLACE FUNCTION maintain_partitions()
RETURNS void AS $$
BEGIN
    -- 删除3个月前的分区
    -- (需要根据实际情况调整)

    -- 创建未来6个月的分区
    PERFORM create_monthly_partitions('ad_spend_daily_partitioned', 6);
END;
$$ LANGUAGE plpgsql;
```

### 7.3 查询优化示例
```sql
-- 优化的统计查询
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    p.name,
    COUNT(DISTINCT a.id) as account_count,
    COALESCE(SUM(dr.spend), 0) as total_spend
FROM projects p
LEFT JOIN ad_accounts a ON p.id = a.project_id
LEFT JOIN ad_spend_daily dr ON a.id = dr.ad_account_id
WHERE p.status = 'active'
GROUP BY p.id, p.name
ORDER BY total_spend DESC;

-- 使用CTE优化复杂查询
WITH project_stats AS (
    SELECT
        p.id,
        p.name,
        COUNT(DISTINCT a.id) as account_count,
        COALESCE(SUM(dr.spend), 0) as total_spend
    FROM projects p
    LEFT JOIN ad_accounts a ON p.id = a.project_id
    LEFT JOIN ad_spend_daily dr ON a.id = dr.ad_account_id
    WHERE p.status = 'active'
    GROUP BY p.id, p.name
),
channel_stats AS (
    SELECT
        c.id,
        c.name,
        COUNT(DISTINCT a.id) as account_count,
        AVG(a.total_spend) as avg_spend_per_account
    FROM channels c
    JOIN ad_accounts a ON c.id = a.channel_id
    GROUP BY c.id, c.name
)
SELECT
    ps.name as project_name,
    ps.account_count,
    ps.total_spend,
    cs.name as channel_name
FROM project_stats ps
JOIN ad_accounts a ON ps.id = a.project_id
JOIN channels cs ON a.channel_id = cs.id
WHERE ps.total_spend > 1000
ORDER BY ps.total_spend DESC;
```

---

## 8. 备份和恢复

### 8.1 备份策略
```bash
#!/bin/bash
# 数据库备份脚本

# 配置
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="ad_spend_system"
DB_USER="postgres"
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 全量备份
echo "开始全量备份..."
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
    --format=custom \
    --compress=9 \
    --verbose \
    --file="$BACKUP_DIR/full_backup_$DATE.dump"

if [ $? -eq 0 ]; then
    echo "全量备份成功: $BACKUP_DIR/full_backup_$DATE.dump"
else
    echo "全量备份失败!"
    exit 1
fi

# 增量备份 (使用WAL归档)
echo "开始增量备份..."
pg_receivectl --create-slot slot_replica --host $DB_HOST --port $DB_PORT --dbname $DB_NAME --slot-name slot_replica --output $BACKUP_DIR/incremental_$DATE.backup

# 验证备份文件
echo "验证备份文件..."
if [ -f "$BACKUP_DIR/full_backup_$DATE.dump" ]; then
    pg_restore --list "$BACKUP_DIR/full_backup_$DATE.dump" > /dev/null
    if [ $? -eq 0 ]; then
        echo "备份文件验证通过"
    else
        echo "备份文件验证失败!"
        exit 1
    fi
fi

# 清理旧备份 (保留30天)
find $BACKUP_DIR -name "*.dump" -mtime +30 -delete
find $BACKUP_DIR -name "*.backup" -mtime +30 -delete

echo "备份完成!"
```

### 8.2 恢复脚本
```bash
#!/bin/bash
# 数据库恢复脚本

DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="ad_spend_system"
DB_USER="postgres"
BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "用法: $0 <backup_file>"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "备份文件不存在: $BACKUP_FILE"
    exit 1
fi

# 停止应用服务
echo "停止应用服务..."
sudo systemctl stop postgresql

# 备份当前数据库
echo "备份当前数据库..."
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
    --format=custom \
    --compress=9 \
    --file="/tmp/current_backup_$(date +%Y%m%d_%H%M%S).dump"

# 恢复数据库
echo "恢复数据库..."
dropdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME
createdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME

pg_restore -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
    --verbose \
    --clean --if-exists \
    $BACKUP_FILE

if [ $? -eq 0 ]; then
    echo "数据库恢复成功"
else
    echo "数据库恢复失败!"
    exit 1
fi

# 启动应用服务
echo "启动应用服务..."
sudo systemctl start postgresql

echo "恢复完成!"
```

---

**文档版本**: v2.0
**最后更新**: 2025-11-10
**负责人**: 数据库架构师
**审核人**: 系统架构师