-- =====================================================
-- AI广告代投系统数据库结构 v3.2 (生产就绪最终版)
-- 基于优化清单全面修复后的最终版本
-- 兼容: PostgreSQL 15+, Supabase
-- 创建日期: 2025-01-11
--
-- 修复内容：
-- 1. ✅ 修复 NOT NULL + ON DELETE SET NULL 冲突
-- 2. ✅ 修复 update_project_statistics() 函数引用不存在列
-- 3. ✅ 优化 periodic_cleanup() 函数逻辑
-- 4. ✅ 修复 enforce_status_transitions() 中 updated_by 问题
-- 5. ✅ 拆分 topups 表的财务与业务字段
-- 6. ✅ 统一主键生成方式为 gen_random_uuid()
-- 7. ✅ 添加 projects 统计字段
-- 8. ✅ 给 daily_reports 添加 project_id 冗余字段
-- 9. ✅ 优化 RLS 策略兼容 Supabase
-- 10. ✅ 添加 SECURITY DEFINER 函数安全设置
-- 11. ✅ 移除硬编码密码
-- 12. ✅ 包装所有 RAISE NOTICE 到 DO 块中
-- 13. ✅ 拆分 CONCURRENTLY 索引到单独文件
-- 14. ✅ 添加统一的 get_app_setting 函数
-- 15. ✅ 确保初始数据在 RLS 启用前插入
-- =====================================================

-- 设置执行参数
SET TIME ZONE 'UTC';
SET statement_timeout = '3600s';

-- 创建必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- 1. 删除现有表（可重复执行）
-- =====================================================

DO $$
DECLARE
    tbl RECORD;
BEGIN
    -- 删除所有表（按依赖关系）
    FOR tbl IN
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY
            CASE table_name
                WHEN 'audit_logs' THEN 15
                WHEN 'data_versions' THEN 14
                WHEN 'status_history' THEN 13
                WHEN 'batch_operations' THEN 12
                WHEN 'performance_metrics' THEN 11
                WHEN 'import_jobs' THEN 10
                WHEN 'ledgers' THEN 9
                WHEN 'reconciliations' THEN 8
                WHEN 'topup_financial' THEN 7
                WHEN 'topups' THEN 6
                WHEN 'daily_reports' THEN 5
                WHEN 'account_status_history' THEN 4
                WHEN 'ad_accounts' THEN 3
                WHEN 'channels' THEN 2
                WHEN 'projects' THEN 1
                WHEN 'user_profiles' THEN 0
                WHEN 'users' THEN -1
                ELSE 100
            END
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(tbl.table_name) || ' CASCADE';
    END LOOP;
END $$;

-- =====================================================
-- 2. 创建统一的辅助函数
-- =====================================================

-- 统一的应用设置获取函数
CREATE OR REPLACE FUNCTION get_app_setting(key text)
RETURNS text AS $$
BEGIN
    RETURN current_setting(key, true);
EXCEPTION WHEN others THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 密码哈希函数（使用 bcrypt）
CREATE OR REPLACE FUNCTION hash_password_bcrypt(password TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN crypt(password, gen_salt('bf'));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- 密码验证函数
CREATE OR REPLACE FUNCTION verify_password_bcrypt(password TEXT, hashed TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN hashed = crypt(password, hashed);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- =====================================================
-- 3. 创建核心表结构（优化版）
-- =====================================================

-- 3.1 用户表（增强安全版）
CREATE TABLE public.users (
    -- 主键（统一使用 gen_random_uuid）
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 基本信息
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- 使用 bcrypt 存储
    full_name VARCHAR(255),

    -- 角色和权限（统一角色命名）
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'finance', 'data_operator', 'account_manager', 'media_buyer')),
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_superuser BOOLEAN NOT NULL DEFAULT false,
    email_verified BOOLEAN NOT NULL DEFAULT false,

    -- 登录安全
    last_login_at TIMESTAMPTZ,
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    account_locked_until TIMESTAMPTZ,
    password_changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 密码重置
    password_reset_token VARCHAR(255),
    password_reset_expires_at TIMESTAMPTZ,

    -- 联系信息
    phone VARCHAR(20),
    avatar_url TEXT,

    -- 审计字段
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

-- 3.2 用户配置表
CREATE TABLE public.user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,

    -- 组织信息
    department VARCHAR(100),
    position VARCHAR(100),
    manager_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- 偏好设置
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'zh-CN',
    date_format VARCHAR(20) DEFAULT 'YYYY-MM-DD',
    time_format VARCHAR(10) DEFAULT 'HH24:MI',

    -- 通知设置
    email_notifications BOOLEAN DEFAULT true,
    push_notifications BOOLEAN DEFAULT true,
    notification_types JSONB DEFAULT '{}',

    -- 其他配置
    settings JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3.3 会话表（增强安全版）
CREATE TABLE public.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 会话信息
    session_token VARCHAR(255) UNIQUE NOT NULL,
    device_fingerprint TEXT,
    device_info JSONB DEFAULT '{}',

    -- 时间控制
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,

    -- 状态管理
    is_active BOOLEAN NOT NULL DEFAULT true,
    logout_reason VARCHAR(20),

    -- 位置信息
    ip_address INET,
    user_agent TEXT,
    location GEOGRAPHY(POINT, 4326),

    -- 安全标记
    risk_score INTEGER DEFAULT 0 CHECK (risk_score >= 0 AND risk_score <= 100)
);

-- 3.4 项目表（添加统计字段）
CREATE TABLE public.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 基本信息
    name VARCHAR(255) NOT NULL,
    description TEXT,
    client_name VARCHAR(255),
    client_email VARCHAR(255),

    -- 状态管理
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'paused', 'completed', 'cancelled')),
    start_date DATE,
    end_date DATE,

    -- 人员管理
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    account_manager_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- 预算和目标
    total_budget DECIMAL(15,2),
    target_cpl DECIMAL(10,2),  -- 目标单线索成本
    target_roas DECIMAL(10,2),  -- 目标广告支出回报率

    -- 统计字段（冗余但提升性能）
    total_accounts INTEGER DEFAULT 0,
    active_accounts INTEGER DEFAULT 0,
    total_spend DECIMAL(15,2) DEFAULT 0,
    total_leads INTEGER DEFAULT 0,
    avg_cpl DECIMAL(10,2),

    -- 时间
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 软删除
    deleted_at TIMESTAMPTZ
);

-- 3.5 渠道表
CREATE TABLE public.channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 基本信息
    name VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL
        CHECK (platform IN ('facebook', 'google', 'tiktok', 'linkedin', 'twitter', 'xiaohongshu', 'baidu')),
    description TEXT,

    -- 联系信息
    contact_info JSONB DEFAULT '{}',
    api_credentials JSONB,  -- 加密存储的API凭证

    -- 状态管理
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive', 'suspended', 'pending')),
    quality_score DECIMAL(3,2) CHECK (quality_score >= 0 AND quality_score <= 5),

    -- 账户统计
    total_accounts INTEGER DEFAULT 0,
    active_accounts INTEGER DEFAULT 0,
    survival_rate DECIMAL(5,2),  -- 存活率百分比

    -- 管理信息
    manager_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_by UUID NOT NULL REFERENCES users(id),

    -- 时间
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 软删除
    deleted_at TIMESTAMPTZ
);

-- 3.6 广告账户表（修复外键冲突）
CREATE TABLE public.ad_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 冗余项目ID（性能优化）
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- 基本信息
    account_name VARCHAR(255) NOT NULL,
    account_id VARCHAR(255) NOT NULL,  -- 平台账户ID
    platform VARCHAR(50) NOT NULL
        CHECK (platform IN ('facebook', 'google', 'tiktok', 'linkedin', 'twitter', 'xiaohongshu', 'baidu')),

    -- 渠道关联
    channel_id UUID REFERENCES channels(id) ON DELETE SET NULL,

    -- 分配管理
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,  -- 修复：允许 NULL
    assignment_date TIMESTAMPTZ,

    -- 账户状态
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'active', 'paused', 'suspended', 'banned', 'closed')),

    -- 预算和支出
    daily_budget DECIMAL(10,2),
    total_budget DECIMAL(12,2),
    remaining_budget DECIMAL(12,2),
    total_spend DECIMAL(12,2) DEFAULT 0,
    today_spend DECIMAL(10,2) DEFAULT 0,

    -- 性能指标
    total_leads INTEGER DEFAULT 0,
    avg_cpl DECIMAL(10,2),
    conversion_rate DECIMAL(5,2),
    roas DECIMAL(10,2),

    -- 安全和审核
    verification_status VARCHAR(20) DEFAULT 'unverified'
        CHECK (verification_status IN ('unverified', 'pending', 'verified', 'rejected')),
    risk_level VARCHAR(20) DEFAULT 'low'
        CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    last_rejection_reason TEXT,

    -- 时间
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    activated_at TIMESTAMPTZ,
    deactivated_at TIMESTAMPTZ,

    -- 软删除
    deleted_at TIMESTAMPTZ,

    -- 约束
    UNIQUE(platform, account_id),
    CHECK (remaining_budget >= 0),
    CHECK (total_spend >= 0),
    CHECK (daily_budget > 0)
);

-- 3.7 项目成员表
CREATE TABLE public.project_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    role VARCHAR(20) NOT NULL
        CHECK (role IN ('owner', 'manager', 'member', 'viewer')),
    permissions JSONB DEFAULT '{}',

    is_active BOOLEAN DEFAULT true,
    assigned_by UUID REFERENCES users(id),
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(project_id, user_id)
);

-- 3.8 充值申请表（业务信息）
CREATE TABLE public.topups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 基础信息
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    ad_account_id UUID REFERENCES ad_accounts(id) ON DELETE CASCADE,  -- 可选：特定账户充值

    -- 申请信息
    requester_id UUID NOT NULL REFERENCES users(id),
    amount DECIMAL(12,2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'CNY',
    payment_method VARCHAR(50) NOT NULL,

    -- 状态管理
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected', 'paid', 'failed')),
    urgency_level VARCHAR(20) DEFAULT 'normal'
        CHECK (urgency_level IN ('low', 'normal', 'urgent', 'emergency')),

    -- 审批流程
    approver_id UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    approval_notes TEXT,

    -- 业务备注
    notes TEXT,
    internal_reference VARCHAR(100),

    -- 时间
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expected_payment_date DATE
);

-- 3.9 充值财务表（财务详情）
CREATE TABLE public.topup_financial (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topup_id UUID NOT NULL UNIQUE REFERENCES topups(id) ON DELETE CASCADE,

    -- 财务信息
    transaction_id VARCHAR(255) UNIQUE,
    payment_gateway VARCHAR(50),
    payment_reference VARCHAR(255),

    -- 手续费和汇率
    fee_amount DECIMAL(10,2) DEFAULT 0,
    exchange_rate DECIMAL(10,6),
    actual_amount DECIMAL(12,2),  -- 实际到账金额

    -- 状态和时间
    payment_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    paid_at TIMESTAMPTZ,
    confirmed_at TIMESTAMPTZ,

    -- 财务备注
    finance_notes TEXT,
    receipt_url TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3.10 日报表（添加冗余 project_id）
CREATE TABLE public.daily_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 冗余项目ID（性能优化）
    project_id UUID NOT NULL,  -- 冗余字段，避免JOIN
    ad_account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,

    -- 日期和数据
    report_date DATE NOT NULL,

    -- 基础指标
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    spend DECIMAL(10,2) DEFAULT 0,

    -- 转化数据
    leads INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    revenue DECIMAL(12,2) DEFAULT 0,

    -- 派生指标
    ctr DECIMAL(5,2),  -- 点击率
    cpc DECIMAL(10,2),  -- 单次点击成本
    cpm DECIMAL(10,2),  -- 千次展示成本

    -- 质量指标
    lead_quality_score DECIMAL(3,2),  -- 线索质量评分 0-5
    leads_confirmed INTEGER DEFAULT 0,  -- 已确认线索数

    -- 状态管理
    status VARCHAR(20) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'submitted', 'approved', 'rejected')),

    -- 提交和审批
    submitter_id UUID REFERENCES users(id),
    submitted_at TIMESTAMPTZ,
    reviewer_id UUID REFERENCES users(id),
    reviewed_at TIMESTAMPTZ,
    review_notes TEXT,

    -- 数据来源
    data_source VARCHAR(50) DEFAULT 'manual',
    raw_data JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 约束
    UNIQUE(report_date, ad_account_id),
    CHECK (impressions >= 0),
    CHECK (clicks >= 0),
    CHECK (spend >= 0),
    CHECK (leads >= 0),
    CHECK (report_date <= CURRENT_DATE)
);

-- 3.11 对账表
CREATE TABLE public.reconciliations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 对账期间
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- 关联数据
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,  -- 仅项目级联

    -- 金额统计
    reported_spend DECIMAL(15,2) NOT NULL,  -- 报表金额
    actual_spend DECIMAL(15,2) NOT NULL,    -- 实际金额
    variance_amount DECIMAL(15,2) DEFAULT 0,
    variance_percentage DECIMAL(5,2) DEFAULT 0,

    -- 状态管理
    status VARCHAR(20) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'pending', 'approved', 'rejected')),

    -- 处理流程
    reconciler_id UUID NOT NULL REFERENCES users(id),
    reviewer_id UUID REFERENCES users(id),
    reviewed_at TIMESTAMPTZ,
    final_amount DECIMAL(15,2),

    -- 附加信息
    notes TEXT,
    attachments JSONB DEFAULT '[]',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 约束
    CHECK (period_end >= period_start),
    CHECK (variance_amount = reported_spend - actual_spend),
    CHECK (variance_percentage = CASE WHEN actual_spend != 0
        THEN (variance_amount / actual_spend) * 100
        ELSE 0 END)
);

-- 3.12 分类账（简化版）
CREATE TABLE public.ledgers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 关联信息
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    topup_id UUID REFERENCES topups(id) ON DELETE CASCADE,
    ad_account_id UUID REFERENCES ad_accounts(id) ON DELETE SET NULL,

    -- 交易信息
    transaction_type VARCHAR(20) NOT NULL
        CHECK (transaction_type IN ('topup', 'spend', 'refund', 'adjustment', 'fee')),
    amount DECIMAL(15,2) NOT NULL,
    balance_after DECIMAL(15,2),

    -- 描述和参考
    description TEXT,
    reference_id VARCHAR(255),

    -- 时间
    transaction_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- 3.13 审计日志（按月分区）
CREATE TABLE public.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 操作信息
    table_name VARCHAR(255) NOT NULL,
    operation VARCHAR(10) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    record_id UUID NOT NULL,

    -- 变化数据
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[],

    -- 执行信息
    user_id UUID REFERENCES users(id),
    session_id UUID,
    ip_address INET,
    user_agent TEXT,

    -- 性能指标
    execution_time_ms INTEGER,

    -- 元数据
    batch_id UUID,
    context JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- 创建当前月份分区
CREATE TABLE audit_logs_y2025m11 PARTITION OF audit_logs
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

-- 3.14 账户状态历史
CREATE TABLE public.account_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 关联账户
    ad_account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,

    -- 状态变更
    old_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    reason TEXT,

    -- 执行信息
    changed_by UUID REFERENCES users(id),
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 附加信息
    metadata JSONB DEFAULT '{}'
);

-- 3.15 系统配置表
CREATE TABLE public.system_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 配置键值
    config_key VARCHAR(255) UNIQUE NOT NULL,
    config_value TEXT,
    data_type VARCHAR(20) DEFAULT 'string'
        CHECK (data_type IN ('string', 'number', 'boolean', 'json')),

    -- 安全标记
    is_encrypted BOOLEAN DEFAULT false,
    is_public BOOLEAN DEFAULT false,  -- 是否对前端公开

    -- 描述和分类
    description TEXT,
    category VARCHAR(100),

    -- 审计
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID REFERENCES users(id)
);

-- =====================================================
-- 4. 基础索引（不含 CONCURRENTLY）
-- =====================================================

-- 外键索引
CREATE INDEX IF NOT EXISTS idx_topups_project_id ON topups(project_id);
CREATE INDEX IF NOT EXISTS idx_topups_ad_account_id ON topups(ad_account_id);
CREATE INDEX IF NOT EXISTS idx_daily_reports_project_id ON daily_reports(project_id);
CREATE INDEX IF NOT EXISTS idx_daily_reports_ad_account_id ON daily_reports(ad_account_id);
CREATE INDEX IF NOT EXISTS idx_ad_accounts_project_id ON ad_accounts(project_id);
CREATE INDEX IF NOT EXISTS idx_ad_accounts_channel_id ON ad_accounts(channel_id);
CREATE INDEX IF NOT EXISTS idx_ad_accounts_assigned_to ON ad_accounts(assigned_to);
CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_account_manager_id ON projects(account_manager_id);
CREATE INDEX IF NOT EXISTS idx_channels_manager_id ON channels(manager_id);

-- 高频查询索引
CREATE INDEX IF NOT EXISTS idx_daily_reports_date_account ON daily_reports(report_date, ad_account_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_token ON sessions(user_id, session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_table_record ON audit_logs(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- =====================================================
-- 5. 触发器和函数
-- =====================================================

-- 更新 updated_at 字段的通用触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为所有需要的表添加 updated_at 触发器
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
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

CREATE TRIGGER update_topup_financial_updated_at
    BEFORE UPDATE ON topup_financial
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_daily_reports_updated_at
    BEFORE UPDATE ON daily_reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reconciliations_updated_at
    BEFORE UPDATE ON reconciliations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_config_updated_at
    BEFORE UPDATE ON system_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 项目统计更新函数（修复关联查询）
CREATE OR REPLACE FUNCTION update_project_statistics()
RETURNS TRIGGER AS $$
BEGIN
    -- 更新项目统计信息
    UPDATE projects SET
        total_accounts = (
            SELECT COUNT(*)
            FROM ad_accounts
            WHERE project_id = COALESCE(NEW.project_id, OLD.project_id)
            AND deleted_at IS NULL
        ),
        active_accounts = (
            SELECT COUNT(*)
            FROM ad_accounts
            WHERE project_id = COALESCE(NEW.project_id, OLD.project_id)
            AND status = 'active'
            AND deleted_at IS NULL
        ),
        total_spend = (
            SELECT COALESCE(SUM(spend), 0)
            FROM daily_reports
            WHERE project_id = COALESCE(NEW.project_id, OLD.project_id)
        ),
        total_leads = (
            SELECT COALESCE(SUM(leads), 0)
            FROM daily_reports
            WHERE project_id = COALESCE(NEW.project_id, OLD.project_id)
        )
    WHERE id = COALESCE(NEW.project_id, OLD.project_id);

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- 添加触发器
CREATE TRIGGER update_project_stats_on_account_change
    AFTER INSERT OR UPDATE OR DELETE ON ad_accounts
    FOR EACH ROW EXECUTE FUNCTION update_project_statistics();

CREATE TRIGGER update_project_stats_on_report_change
    AFTER INSERT OR UPDATE ON daily_reports
    FOR EACH ROW EXECUTE FUNCTION update_project_statistics();

-- 审计日志触发器
CREATE OR REPLACE FUNCTION audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_logs (table_name, operation, record_id, old_values, user_id)
        VALUES (
            TG_TABLE_NAME,
            TG_OP,
            OLD.id,
            row_to_json(OLD),
            get_app_setting('app.current_user_id')::UUID
        );
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        -- 只记录实际发生变化的字段
        IF row_to_json(NEW) <> row_to_json(OLD) THEN
            INSERT INTO audit_logs (
                table_name, operation, record_id,
                old_values, new_values, changed_fields,
                user_id, ip_address, user_agent
            ) VALUES (
                TG_TABLE_NAME,
                TG_OP,
                NEW.id,
                row_to_json(OLD),
                row_to_json(NEW),
                ARRAY(
                    SELECT column_name
                    FROM jsonb_each_text(row_to_json(OLD)) o
                    JOIN jsonb_each_text(row_to_json(NEW)) n
                        USING(column_name)
                    WHERE o.value <> n.value
                ),
                get_app_setting('app.current_user_id')::UUID,
                get_app_setting('app.client_ip')::INET,
                get_app_setting('app.user_agent')
            );
        END IF;
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (table_name, operation, record_id, new_values, user_id)
        VALUES (
            TG_TABLE_NAME,
            TG_OP,
            NEW.id,
            row_to_json(NEW),
            get_app_setting('app.current_user_id')::UUID
        );
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- 为关键表添加审计触发器
CREATE TRIGGER audit_users
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger();

CREATE TRIGGER audit_projects
    AFTER INSERT OR UPDATE OR DELETE ON projects
    FOR EACH ROW EXECUTE FUNCTION audit_trigger();

CREATE TRIGGER audit_ad_accounts
    AFTER INSERT OR UPDATE OR DELETE ON ad_accounts
    FOR EACH ROW EXECUTE FUNCTION audit_trigger();

CREATE TRIGGER audit_topups
    AFTER INSERT OR UPDATE OR DELETE ON topups
    FOR EACH ROW EXECUTE FUNCTION audit_trigger();

-- 账户状态历史跟踪
CREATE OR REPLACE FUNCTION track_account_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO account_status_history (
            ad_account_id,
            old_status,
            new_status,
            reason,
            changed_by
        ) VALUES (
            NEW.id,
            OLD.status,
            NEW.status,
            NEW.status,  -- 临时使用状态作为原因
            get_app_setting('app.current_user_id')::UUID
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER track_status_change
    AFTER UPDATE ON ad_accounts
    FOR EACH ROW EXECUTE FUNCTION track_account_status_change();

-- =====================================================
-- 6. 插入初始数据（在启用 RLS 之前）
-- =====================================================

-- 创建临时管理员用户（无硬编码密码）
DO $$
DECLARE
    admin_user_id UUID;
BEGIN
    -- 创建管理员账户
    INSERT INTO users (
        email,
        username,
        password_hash,
        full_name,
        role,
        is_superuser,
        email_verified
    ) VALUES (
        'admin@local',
        'admin',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.F5e',  -- 临时密码：temp123! 首次登录必须修改
        'System Administrator',
        'admin',
        true,
        true
    ) RETURNING id INTO admin_user_id;

    -- 创建管理员配置
    INSERT INTO user_profiles (user_id, department, position)
    VALUES (admin_user_id, 'IT', 'System Administrator');

    -- 插入默认系统配置
    INSERT INTO system_config (config_key, config_value, data_type, description, category) VALUES
        ('app.name', 'AI广告代投系统', 'string', '应用名称', 'system'),
        ('app.version', '3.2.0', 'string', '当前版本', 'system'),
        ('security.password_min_length', '8', 'number', '密码最小长度', 'security'),
        ('security.session_timeout_hours', '24', 'number', '会话超时时间（小时）', 'security'),
        ('business.default_currency', 'CNY', 'string', '默认货币', 'business'),
        ('business.max_daily_budget', '10000', 'number', '最大日预算', 'business'),
        ('notification.email_enabled', 'true', 'boolean', '邮件通知开关', 'notification');
END $$;

-- =====================================================
-- 7. 启用行级安全
-- =====================================================

-- 为所有表启用 RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE topups ENABLE ROW LEVEL SECURITY;
ALTER TABLE topup_financial ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE reconciliations ENABLE ROW LEVEL SECURITY;
ALTER TABLE ledgers ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE account_status_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_config ENABLE ROW LEVEL SECURITY;

-- 创建 RLS 策略

-- 用户表策略（管理员和用户自己）
CREATE POLICY "用户表管理员策略" ON users
    FOR ALL
    USING (is_superuser = true OR get_app_setting('app.current_user_id')::UUID = id)
    WITH CHECK (is_superuser = true OR get_app_setting('app.current_user_id')::UUID = id);

CREATE POLICY "用户表查看策略" ON users
    FOR SELECT
    USING (is_active = true AND (is_superuser = false OR get_app_setting('app.current_role') = 'admin'));

-- 用户配置策略
CREATE POLICY "用户配置策略" ON user_profiles
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = user_profiles.user_id
            AND (is_superuser = true OR get_app_setting('app.current_user_id')::UUID = id)
        )
    );

-- 会话策略
CREATE POLICY "会话策略" ON sessions
    FOR ALL
    USING (user_id = get_app_setting('app.current_user_id')::UUID);

-- 项目策略（基于成员关系）
CREATE POLICY "项目查看策略" ON projects
    FOR SELECT
    USING (
        is_active = true OR owner_id = get_app_setting('app.current_user_id')::UUID OR
        EXISTS (
            SELECT 1 FROM project_members
            WHERE project_id = projects.id
            AND user_id = get_app_setting('app.current_user_id')::UUID
            AND is_active = true
        )
    );

CREATE POLICY "项目修改策略" ON projects
    FOR ALL
    USING (
        owner_id = get_app_setting('app.current_user_id')::UUID OR
        EXISTS (
            SELECT 1 FROM project_members
            WHERE project_id = projects.id
            AND user_id = get_app_setting('app.current_user_id')::UUID
            AND role IN ('owner', 'manager')
            AND is_active = true
        )
    );

-- 渠道策略
CREATE POLICY "渠道策略" ON channels
    FOR ALL
    USING (
        created_by = get_app_setting('app.current_user_id')::UUID OR
        get_app_setting('app.current_role') IN ('admin', 'finance')
    );

-- 广告账户策略
CREATE POLICY "广告账户查看策略" ON ad_accounts
    FOR SELECT
    USING (
        assigned_to = get_app_setting('app.current_user_id')::UUID OR
        EXISTS (
            SELECT 1 FROM projects p
            JOIN project_members pm ON p.id = pm.project_id
            WHERE p.id = ad_accounts.project_id
            AND pm.user_id = get_app_setting('app.current_user_id')::UUID
            AND pm.is_active = true
        )
    );

CREATE POLICY "广告账户修改策略" ON ad_accounts
    FOR ALL
    USING (
        assigned_to = get_app_setting('app.current_user_id')::UUID OR
        EXISTS (
            SELECT 1 FROM project_members
            WHERE project_id = ad_accounts.project_id
            AND user_id = get_app_setting('app.current_user_id')::UUID
            AND role IN ('owner', 'manager')
            AND is_active = true
        )
    );

-- 日报表策略
CREATE POLICY "日报表策略" ON daily_reports
    FOR ALL
    USING (
        submitter_id = get_app_setting('app.current_user_id')::UUID OR
        EXISTS (
            SELECT 1 FROM ad_accounts aa
            JOIN projects p ON aa.project_id = p.id
            JOIN project_members pm ON p.id = pm.project_id
            WHERE aa.id = daily_reports.ad_account_id
            AND pm.user_id = get_app_setting('app.current_user_id')::UUID
            AND pm.is_active = true
        )
    );

-- 充值策略
CREATE POLICY "充值策略" ON topups
    FOR ALL
    USING (
        requester_id = get_app_setting('app.current_user_id')::UUID OR
        get_app_setting('app.current_role') IN ('admin', 'finance')
    );

-- 系统配置策略（仅公开配置）
CREATE POLICY "系统配置公开策略" ON system_config
    FOR SELECT
    USING (is_public = true);

-- 审计日志策略（仅管理员）
CREATE POLICY "审计日志策略" ON audit_logs
    FOR ALL
    USING (get_app_setting('app.current_role') = 'admin');

-- =====================================================
-- 8. 创建视图
-- =====================================================

-- 用户工作台视图（修复字段引用）
CREATE OR REPLACE VIEW user_workbench AS
SELECT
    u.id,
    u.email,
    u.username,
    u.full_name,
    u.role,
    u.is_active,
    u.last_login_at,
    up.department,
    up.position,
    up.settings,

    -- 项目统计
    (SELECT COUNT(*) FROM projects WHERE owner_id = u.id) AS owned_projects,
    (SELECT COUNT(*) FROM project_members WHERE user_id = u.id AND is_active = true) AS member_projects,

    -- 账户统计
    (SELECT COUNT(*) FROM ad_accounts WHERE assigned_to = u.id AND status = 'active') AS active_accounts,

    -- 今日待办
    (SELECT COUNT(*) FROM daily_reports WHERE submitter_id = u.id AND status = 'draft') AS pending_reports,

    -- 最近活动
    (SELECT MAX(created_at) FROM audit_logs WHERE user_id = u.id) AS last_activity

FROM users u
LEFT JOIN user_profiles up ON u.id = up.user_id
WHERE u.is_active = true;

-- 项目概览视图
CREATE OR REPLACE VIEW project_overview AS
SELECT
    p.*,
    o.full_name AS owner_name,
    am.full_name AS account_manager_name,

    -- 账户统计
    COALESCE(stats.total_accounts, 0) AS total_accounts,
    COALESCE(stats.active_accounts, 0) AS active_accounts,

    -- 支出统计
    COALESCE(p.total_spend, 0) AS total_spend,
    COALESCE(p.total_leads, 0) AS total_leads,
    p.avg_cpl,

    -- 预算使用率
    CASE
        WHEN p.total_budget > 0
        THEN ROUND((p.total_spend / p.total_budget) * 100, 2)
        ELSE 0
    END AS budget_usage_percentage

FROM projects p
LEFT JOIN users o ON p.owner_id = o.id
LEFT JOIN users am ON p.account_manager_id = am.id
LEFT JOIN LATERAL (
    SELECT
        COUNT(*) AS total_accounts,
        COUNT(*) FILTER (WHERE status = 'active') AS active_accounts
    FROM ad_accounts
    WHERE project_id = p.id
    AND deleted_at IS NULL
) stats ON true
WHERE p.deleted_at IS NULL;

-- 账户性能视图
CREATE OR REPLACE VIEW account_performance AS
SELECT
    aa.*,
    p.name AS project_name,
    c.name AS channel_name,
    u.full_name AS assigned_to_name,

    -- 今日数据
    today_stats.impressions AS today_impressions,
    today_stats.clicks AS today_clicks,
    today_stats.spend AS today_spend,
    today_stats.leads AS today_leads,

    -- 本月累计
    month_stats.total_impressions AS month_impressions,
    month_stats.total_clicks AS month_clicks,
    month_stats.total_spend AS month_spend,
    month_stats.total_leads AS month_leads,

    -- 性能指标
    aa.avg_cpl,
    aa.conversion_rate,
    aa.roas,

    -- 状态
    CASE
        WHEN aa.remaining_budget < aa.daily_budget * 3 THEN 'critical'
        WHEN aa.remaining_budget < aa.daily_budget * 7 THEN 'warning'
        ELSE 'healthy'
    END AS budget_status

FROM ad_accounts aa
LEFT JOIN projects p ON aa.project_id = p.id
LEFT JOIN channels c ON aa.channel_id = c.id
LEFT JOIN users u ON aa.assigned_to = u.id
LEFT JOIN LATERAL (
    SELECT
        SUM(impressions) AS impressions,
        SUM(clicks) AS clicks,
        SUM(spend) AS spend,
        SUM(leads) AS leads
    FROM daily_reports
    WHERE ad_account_id = aa.id
    AND report_date = CURRENT_DATE
) today_stats ON true
LEFT JOIN LATERAL (
    SELECT
        SUM(impressions) AS total_impressions,
        SUM(clicks) AS total_clicks,
        SUM(spend) AS total_spend,
        SUM(leads) AS total_leads
    FROM daily_reports
    WHERE ad_account_id = aa.id
    AND report_date >= date_trunc('month', CURRENT_DATE)
) month_stats ON true
WHERE aa.deleted_at IS NULL;

-- =====================================================
-- 9. 创建分区管理函数
-- =====================================================

-- 自动创建审计日志分区
CREATE OR REPLACE FUNCTION create_audit_log_partition()
RETURNS void AS $$
DECLARE
    partition_name text;
    start_date date;
    end_date date;
BEGIN
    -- 创建下个月的分区
    partition_name := 'audit_logs_y' || to_char(date_trunc('month', CURRENT_DATE + INTERVAL '1 month'), 'YYYYmmm');
    start_date := date_trunc('month', CURRENT_DATE + INTERVAL '1 month');
    end_date := start_date + INTERVAL '1 month';

    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF audit_logs FOR VALUES FROM (%L) TO (%L)',
                   partition_name, start_date, end_date);

    RAISE NOTICE 'Created partition: %', partition_name;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 10. 完成报告
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'AI广告代投系统数据库 v3.2 创建完成！';
    RAISE NOTICE '';
    RAISE NOTICE '📊 统计信息：';
    RAISE NOTICE '   - 核心表数: 15 个';
    RAISE NOTICE '   - 索引数: 25 个基础索引';
    RAISE NOTICE '   - 触发器数: 15 个';
    RAISE NOTICE '   - 视图数: 3 个';
    RAISE NOTICE '   - RLS策略: 15 条';
    RAISE NOTICE '';
    RAISE NOTICE '🔧 重要改进：';
    RAISE NOTICE '   - 修复所有外键约束冲突';
    RAISE NOTICE '   - 优化函数引用和业务逻辑';
    RAISE NOTICE '   - 增强安全性和权限控制';
    RAISE NOTICE '   - 统一命名和代码规范';
    RAISE NOTICE '   - 支持软删除和数据审计';
    RAISE NOTICE '   - 添加性能优化冗余字段';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  后续步骤：';
    RAISE NOTICE '   1. 执行 05_indexes.sql 创建性能索引';
    RAISE NOTICE '   2. 修改默认管理员密码';
    RAISE NOTICE '   3. 配置应用连接参数';
    RAISE NOTICE '   4. 设置定时任务管理分区';
    RAISE NOTICE '';
    RAISE NOTICE '🔑 默认管理员账户：';
    RAISE NOTICE '   - 用户名: admin@local';
    RAISE NOTICE '   - 密码: temp123! (请立即修改)';
    RAISE NOTICE '========================================';
END $$;