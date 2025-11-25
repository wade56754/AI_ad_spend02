-- =============================================================================
-- AI 广告代投系统 - 数据库初始化脚本 (最终版)
-- 基于: DATA_SCHEMA.md v5.2, STATE_MACHINE.md v2.6, MASTER.md v3.4, PATTERNS.md v1.0
-- 生成日期: 2025-11-25
-- =============================================================================

BEGIN;

-- =============================================================================
-- 0. 辅助函数与触发器
-- =============================================================================

-- 0.1 updated_at 自动更新函数
CREATE OR REPLACE FUNCTION fn_update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 0.2 ledger_entries 不可变性保护函数 (MASTER.md INV-001, PATTERNS.md AP-LED-001)
CREATE OR REPLACE FUNCTION fn_ledger_immutable()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'LEDGER_IMMUTABLE: ledger_entries 禁止 UPDATE/DELETE 操作，修正请使用 REVERSAL 机制 (参考: MASTER.md INV-001)';
END;
$$ LANGUAGE plpgsql;

-- 0.3 suppliers.balance 只读保护函数 (PATTERNS.md AP-LED-002)
CREATE OR REPLACE FUNCTION fn_suppliers_balance_readonly()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.balance IS DISTINCT FROM NEW.balance THEN
        RAISE EXCEPTION 'BALANCE_READONLY: suppliers.balance 禁止直接修改，必须通过 ledger_entries 流程更新 (参考: MASTER.md INV-001)';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 1. 用户与权限表
-- =============================================================================

-- 1.1 users (业务用户表) - DATA_SCHEMA.md §3.1.1
-- 角色枚举: AUTH_SPEC.md §2.2 定义 5 个合法角色
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    full_name VARCHAR(100),
    email VARCHAR(255),
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'finance', 'data_operator', 'account_manager', 'media_buyer')),
    department VARCHAR(100),
    position VARCHAR(100),
    account_manager_id UUID REFERENCES users(id) ON DELETE SET NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    last_login_at TIMESTAMPTZ,
    last_login_ip VARCHAR(45),
    preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    notification_settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    profile_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    language VARCHAR(10) NOT NULL DEFAULT 'zh-CN',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_account_manager ON users(account_manager_id);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login_at);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();

-- 1.2 roles (历史兼容表 - legacy) - DATA_SCHEMA.md §3.1.2
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 1.3 user_sessions (登录会话) - DATA_SCHEMA.md §3.1.3
CREATE TABLE IF NOT EXISTS user_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    invalidated_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id);

-- 1.4 audit_logs (系统级审计日志) - DATA_SCHEMA.md §3.1.4
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    module VARCHAR(100),
    action VARCHAR(50),
    entity_id VARCHAR(64),
    performed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    role VARCHAR(20),
    ip_address INET,
    user_agent TEXT,
    payload_before JSONB,
    payload_after JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_module ON audit_logs(module);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity_id ON audit_logs(entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_performed_by ON audit_logs(performed_by);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- =============================================================================
-- 2. 项目表
-- =============================================================================

-- 2.1 projects (项目主表) - DATA_SCHEMA.md §3.2.1
-- 状态枚举: STATE_MACHINE.md §5 projects.status
CREATE TABLE IF NOT EXISTS projects (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    client_name VARCHAR(200) NOT NULL,
    client_company VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) CHECK (status IN ('draft', 'active', 'suspended', 'archived')),
    account_manager_id UUID REFERENCES users(id) ON DELETE SET NULL,
    budget_total DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    budget_currency VARCHAR(10) NOT NULL DEFAULT 'CNY',
    unit_price DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    start_date DATE,
    end_date DATE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_account_manager ON projects(account_manager_id);

CREATE TRIGGER trg_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();

-- 2.2 project_members (项目成员) - DATA_SCHEMA.md §3.2.2
-- 角色枚举: 与全局角色一致 (AUTH_SPEC.md §2.2)
CREATE TABLE IF NOT EXISTS project_members (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) CHECK (role IN ('admin', 'finance', 'data_operator', 'account_manager', 'media_buyer')),
    permissions JSONB NOT NULL DEFAULT '{}'::jsonb,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT,
    CONSTRAINT uq_project_members_project_user UNIQUE (project_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_project_members_project_id ON project_members(project_id);
CREATE INDEX IF NOT EXISTS idx_project_members_user_id ON project_members(user_id);

-- 2.3 project_expenses (项目费用记录) - DATA_SCHEMA.md §3.2.3
CREATE TABLE IF NOT EXISTS project_expenses (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
    expense_type VARCHAR(50),
    amount DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(10) NOT NULL DEFAULT 'CNY',
    occurred_at TIMESTAMPTZ,
    description TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_expenses_project_id ON project_expenses(project_id);

-- =============================================================================
-- 3. 渠道表
-- =============================================================================

-- 3.1 channels (渠道主数据) - DATA_SCHEMA.md §3.2.4
-- 状态枚举: STATE_MACHINE.md §6.1 channels.status
CREATE TABLE IF NOT EXISTS channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    platform VARCHAR(50),
    status VARCHAR(20) CHECK (status IN ('active', 'inactive')),
    risk_level VARCHAR(20) CHECK (risk_level IN ('low', 'medium', 'high')),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_channels_name ON channels(name);
CREATE INDEX IF NOT EXISTS idx_channels_status ON channels(status);

CREATE TRIGGER trg_channels_updated_at BEFORE UPDATE ON channels
    FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();

-- 3.2 channel_contacts (渠道联系人) - DATA_SCHEMA.md §3.2.5
CREATE TABLE IF NOT EXISTS channel_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    full_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    contact_role VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_channel_contacts_channel_id ON channel_contacts(channel_id);

CREATE TRIGGER trg_channel_contacts_updated_at BEFORE UPDATE ON channel_contacts
    FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();

-- 3.3 channel_reviews (渠道评审记录) - DATA_SCHEMA.md §3.2.6
-- 状态枚举: STATE_MACHINE.md §6.2 channel_reviews.review_status
CREATE TABLE IF NOT EXISTS channel_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE RESTRICT,
    reviewer_id UUID REFERENCES users(id) ON DELETE SET NULL,
    review_status VARCHAR(20) CHECK (review_status IN ('draft', 'pending', 'approved', 'rejected')),
    score JSONB,
    comments TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_channel_reviews_channel_id ON channel_reviews(channel_id);
CREATE INDEX IF NOT EXISTS idx_channel_reviews_status ON channel_reviews(review_status);

CREATE TRIGGER trg_channel_reviews_updated_at BEFORE UPDATE ON channel_reviews
    FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();

-- 3.4 channel_account_requests (渠道开户申请) - DATA_SCHEMA.md §3.2.7
-- 状态枚举: STATE_MACHINE.md §6.3 channel_account_requests.status
CREATE TABLE IF NOT EXISTS channel_account_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE RESTRICT,
    requested_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(20) CHECK (status IN ('draft', 'pending', 'approved', 'rejected')),
    request_payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_channel_account_requests_channel_id ON channel_account_requests(channel_id);
CREATE INDEX IF NOT EXISTS idx_channel_account_requests_status ON channel_account_requests(status);

CREATE TRIGGER trg_channel_account_requests_updated_at BEFORE UPDATE ON channel_account_requests
    FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();

-- 3.5 channel_performance (渠道表现统计) - DATA_SCHEMA.md §3.2.8
-- 注意: DATA_SCHEMA 明确定义 impressions/clicks 为 DECIMAL(15,2)，保持 SoT 一致
CREATE TABLE IF NOT EXISTS channel_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    impressions DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    clicks DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    spend DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    conversion_rate DECIMAL(12,4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_channel_performance_channel_id ON channel_performance(channel_id);
CREATE INDEX IF NOT EXISTS idx_channel_performance_metric_date ON channel_performance(metric_date);

-- =============================================================================
-- 4. 供应商表
-- =============================================================================

-- 4.1 suppliers (供应商主表) - DATA_SCHEMA.md §3.4.5
-- 状态: STATE_MACHINE.md 未定义 suppliers.status 具体枚举，使用弱约束 NOT NULL
CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    code TEXT UNIQUE NOT NULL,
    balance DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_suppliers_code ON suppliers(code);
CREATE INDEX IF NOT EXISTS idx_suppliers_status ON suppliers(status);

CREATE TRIGGER trg_suppliers_updated_at BEFORE UPDATE ON suppliers
    FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();

-- suppliers.balance 只读保护 (PATTERNS.md AP-LED-002)
CREATE TRIGGER trg_suppliers_balance_readonly BEFORE UPDATE ON suppliers
    FOR EACH ROW EXECUTE FUNCTION fn_suppliers_balance_readonly();

-- =============================================================================
-- 5. 广告账户表
-- =============================================================================

-- 5.1 ad_accounts (广告账户) - DATA_SCHEMA.md §3.2.9
-- 状态枚举: STATE_MACHINE.md §7.1 ad_accounts.status
CREATE TABLE IF NOT EXISTS ad_accounts (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
    channel_id UUID REFERENCES channels(id) ON DELETE SET NULL,
    supplier_id UUID REFERENCES suppliers(id) ON DELETE SET NULL,
    owner_id UUID REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(200),
    account_code VARCHAR(100) UNIQUE,
    status VARCHAR(20) CHECK (status IN ('new', 'testing', 'active', 'suspended', 'dead', 'archived')),
    status_reason TEXT,
    spend_limit DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(10) NOT NULL DEFAULT 'CNY',
    timezone VARCHAR(50) NOT NULL DEFAULT 'Asia/Shanghai',
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ad_accounts_project ON ad_accounts(project_id);
CREATE INDEX IF NOT EXISTS idx_ad_accounts_channel ON ad_accounts(channel_id);
CREATE INDEX IF NOT EXISTS idx_ad_accounts_status ON ad_accounts(status);
CREATE INDEX IF NOT EXISTS idx_ad_accounts_supplier ON ad_accounts(supplier_id);

CREATE TRIGGER trg_ad_accounts_updated_at BEFORE UPDATE ON ad_accounts
    FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();

-- 5.2 account_status_history (账户状态流水) - DATA_SCHEMA.md §3.2.9
CREATE TABLE IF NOT EXISTS account_status_history (
    id BIGSERIAL PRIMARY KEY,
    ad_account_id BIGINT NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    from_status VARCHAR(20),
    to_status VARCHAR(20),
    changed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_account_status_history_ad_account ON account_status_history(ad_account_id);

-- 5.3 account_alerts (账户预警) - DATA_SCHEMA.md §3.2.9
-- 状态枚举: STATE_MACHINE.md §7.3 account_alerts.status
-- severity 枚举: DATA_SCHEMA.md 固定 info/warning/critical
CREATE TABLE IF NOT EXISTS account_alerts (
    id BIGSERIAL PRIMARY KEY,
    ad_account_id BIGINT NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    alert_type VARCHAR(50),
    severity VARCHAR(20) CHECK (severity IN ('info', 'warning', 'critical')),
    status VARCHAR(20) CHECK (status IN ('open', 'ack', 'resolved')),
    message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolved_by UUID REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_account_alerts_ad_account ON account_alerts(ad_account_id);
CREATE INDEX IF NOT EXISTS idx_account_alerts_status ON account_alerts(status);

-- 5.4 account_documents (账户附件/凭证) - DATA_SCHEMA.md §3.2.9
CREATE TABLE IF NOT EXISTS account_documents (
    id BIGSERIAL PRIMARY KEY,
    ad_account_id BIGINT NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    document_type VARCHAR(50),
    storage_path TEXT,
    file_name VARCHAR(255),
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_account_documents_ad_account ON account_documents(ad_account_id);

-- 5.5 account_notes (账户备注) - DATA_SCHEMA.md §3.2.9
-- note_type 枚举: DATA_SCHEMA.md 固定 general/risk/finance
CREATE TABLE IF NOT EXISTS account_notes (
    id BIGSERIAL PRIMARY KEY,
    ad_account_id BIGINT NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    author_id UUID REFERENCES users(id) ON DELETE SET NULL,
    note_type VARCHAR(20) CHECK (note_type IN ('general', 'risk', 'finance')),
    content TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_account_notes_ad_account ON account_notes(ad_account_id);

-- =============================================================================
-- 6. 日报与投放数据表
-- =============================================================================

-- 6.1 daily_reports (日报 - 8状态机) - DATA_SCHEMA.md §3.3.1
-- 状态枚举: STATE_MACHINE.md §8 daily_reports.status (8状态)
-- trend_flag 枚举: DATA_SCHEMA.md 固定 normal/flagged/resolved
-- 计数字段: DATA_SCHEMA.md 明确定义为 INTEGER
CREATE TABLE IF NOT EXISTS daily_reports (
    id BIGSERIAL PRIMARY KEY,
    report_date DATE NOT NULL,
    ad_account_id BIGINT NOT NULL REFERENCES ad_accounts(id) ON DELETE RESTRICT,
    campaign_name VARCHAR(200),
    ad_group_name VARCHAR(200),
    ad_creative_name VARCHAR(200),
    impressions INTEGER NOT NULL DEFAULT 0,
    clicks INTEGER NOT NULL DEFAULT 0,
    conversions INTEGER NOT NULL DEFAULT 0,
    new_follows INTEGER NOT NULL DEFAULT 0,
    conversions_raw INTEGER NOT NULL DEFAULT 0,
    conversions_final INTEGER NOT NULL DEFAULT 0,
    raw_spend DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    real_spend DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    unit_price DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    cpc DECIMAL(12,4),
    cpa DECIMAL(12,4),
    ctr DECIMAL(12,4),
    roi DECIMAL(12,4),
    status VARCHAR(20) NOT NULL DEFAULT 'raw_submitted' CHECK (status IN (
        'raw_submitted', 'trend_pending', 'trend_ok', 'trend_flagged',
        'trend_resolved', 'final_pending', 'final_confirmed', 'final_locked'
    )),
    trend_flag VARCHAR(20) NOT NULL DEFAULT 'normal' CHECK (trend_flag IN ('normal', 'flagged', 'resolved')),
    trend_flag_reason TEXT,
    trend_resolution_note TEXT,
    final_locked_at TIMESTAMPTZ,
    notes TEXT,
    attachments JSONB,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    submitted_by UUID REFERENCES users(id) ON DELETE SET NULL,
    audit_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    submitted_at TIMESTAMPTZ,
    approved_at TIMESTAMPTZ,
    CONSTRAINT uq_daily_reports_date_account UNIQUE (report_date, ad_account_id)
);

CREATE INDEX IF NOT EXISTS idx_daily_reports_date ON daily_reports(report_date);
CREATE INDEX IF NOT EXISTS idx_daily_reports_account ON daily_reports(ad_account_id);
CREATE INDEX IF NOT EXISTS idx_daily_reports_status ON daily_reports(status);
CREATE INDEX IF NOT EXISTS idx_daily_reports_created_by ON daily_reports(created_by);
CREATE INDEX IF NOT EXISTS idx_daily_reports_date_status ON daily_reports(report_date, status);

CREATE TRIGGER trg_daily_reports_updated_at BEFORE UPDATE ON daily_reports
    FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();

-- 6.2 daily_report_audit_logs (日报审计日志) - DATA_SCHEMA.md §3.3.2
CREATE TABLE IF NOT EXISTS daily_report_audit_logs (
    id BIGSERIAL PRIMARY KEY,
    daily_report_id BIGINT NOT NULL REFERENCES daily_reports(id) ON DELETE CASCADE,
    action VARCHAR(50),
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    audit_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    audit_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    audit_notes TEXT,
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX IF NOT EXISTS idx_daily_report_audit_logs_report ON daily_report_audit_logs(daily_report_id);

-- 6.3 ad_spend_daily (外部导入日消耗) - DATA_SCHEMA.md §3.3.3
CREATE TABLE IF NOT EXISTS ad_spend_daily (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_platform VARCHAR(50),
    ad_account_code VARCHAR(100),
    spend_date DATE,
    spend_amount DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(10) NOT NULL DEFAULT 'CNY',
    raw_payload JSONB,
    imported_by UUID REFERENCES users(id) ON DELETE SET NULL,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ad_spend_daily_account_code ON ad_spend_daily(ad_account_code);
CREATE INDEX IF NOT EXISTS idx_ad_spend_daily_spend_date ON ad_spend_daily(spend_date);

-- =============================================================================
-- 7. 充值与资金表
-- =============================================================================

-- 7.1 topup_requests (充值申请) - DATA_SCHEMA.md §3.4.1
-- 状态枚举: STATE_MACHINE.md §9 topup_requests.status
-- urgency_level 枚举: DATA_SCHEMA.md 固定 low/normal/high/urgent
CREATE TABLE IF NOT EXISTS topup_requests (
    id BIGSERIAL PRIMARY KEY,
    request_no VARCHAR(50) UNIQUE NOT NULL,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
    ad_account_id BIGINT REFERENCES ad_accounts(id) ON DELETE SET NULL,
    applicant_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'CNY',
    urgency_level VARCHAR(20) CHECK (urgency_level IN ('low', 'normal', 'high', 'urgent')),
    status VARCHAR(20) CHECK (status IN (
        'draft', 'pending_review', 'finance_approve', 'paid', 'completed', 'rejected', 'cancelled'
    )),
    status_reason TEXT,
    expected_pay_date DATE,
    voucher_url TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_topup_requests_project ON topup_requests(project_id);
CREATE INDEX IF NOT EXISTS idx_topup_requests_status ON topup_requests(status);
CREATE INDEX IF NOT EXISTS idx_topup_requests_applicant ON topup_requests(applicant_id);
CREATE INDEX IF NOT EXISTS idx_topup_requests_request_no ON topup_requests(request_no);
CREATE INDEX IF NOT EXISTS idx_topup_requests_project_status ON topup_requests(project_id, status);

CREATE TRIGGER trg_topup_requests_updated_at BEFORE UPDATE ON topup_requests
    FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();

-- 7.2 topup_transactions (充值到账流水) - DATA_SCHEMA.md §3.4.2
-- payment_method 枚举: DATA_SCHEMA.md 固定 bank_transfer/alipay/wechat/paypal/credit_card/other
CREATE TABLE IF NOT EXISTS topup_transactions (
    id BIGSERIAL PRIMARY KEY,
    topup_request_id BIGINT NOT NULL REFERENCES topup_requests(id) ON DELETE RESTRICT,
    paid_amount DECIMAL(15,2) NOT NULL,
    paid_currency VARCHAR(10) NOT NULL DEFAULT 'CNY',
    payment_method VARCHAR(50) CHECK (payment_method IN (
        'bank_transfer', 'alipay', 'wechat', 'paypal', 'credit_card', 'other'
    )),
    payment_reference VARCHAR(100),
    paid_at TIMESTAMPTZ,
    receipt_url TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_topup_transactions_request ON topup_transactions(topup_request_id);

-- 7.3 topup_approval_logs (充值审批操作记录) - DATA_SCHEMA.md §3.4.3
CREATE TABLE IF NOT EXISTS topup_approval_logs (
    id BIGSERIAL PRIMARY KEY,
    topup_request_id BIGINT NOT NULL REFERENCES topup_requests(id) ON DELETE CASCADE,
    action VARCHAR(50),
    from_status VARCHAR(20),
    to_status VARCHAR(20),
    operator_id UUID REFERENCES users(id) ON DELETE SET NULL,
    comments TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_topup_approval_logs_request ON topup_approval_logs(topup_request_id);

-- 7.4 ledger_entries (资金总账 - 双账本) - DATA_SCHEMA.md §3.4.4
-- 核心约束: 禁止 UPDATE/DELETE (MASTER.md INV-001, PATTERNS.md AP-LED-001)
-- 双账本隔离: PROJECT 账本 project_id 必填且 supplier_id 为空; SUPPLIER 账本 supplier_id 必填且 project_id 为空
CREATE TABLE IF NOT EXISTS ledger_entries (
    id BIGSERIAL PRIMARY KEY,
    ledger_type VARCHAR(20) NOT NULL CHECK (ledger_type IN ('PROJECT', 'SUPPLIER')),
    project_id BIGINT REFERENCES projects(id) ON DELETE RESTRICT,
    supplier_id UUID REFERENCES suppliers(id) ON DELETE RESTRICT,
    ad_account_id BIGINT REFERENCES ad_accounts(id) ON DELETE SET NULL,
    entry_type VARCHAR(20) NOT NULL CHECK (entry_type IN (
        'REVENUE', 'COST', 'TOPUP', 'TRANSFER_OUT', 'TRANSFER_IN', 'REVERSAL'
    )),
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'CNY',
    reference_id BIGINT,
    occurred_at TIMESTAMPTZ NOT NULL,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 双账本隔离约束 (MASTER.md INV-001: 禁止账本混用)
    -- PROJECT: project_id 必填, supplier_id 必须为空
    -- SUPPLIER: supplier_id 必填, project_id 必须为空
    CONSTRAINT chk_ledger_type_entity CHECK (
        (ledger_type = 'PROJECT' AND project_id IS NOT NULL AND supplier_id IS NULL) OR
        (ledger_type = 'SUPPLIER' AND supplier_id IS NOT NULL AND project_id IS NULL)
    ),

    -- entry_type 与 ledger_type 对应约束 (DATA_SCHEMA.md §3.4.4)
    -- PROJECT 账本: REVENUE/TOPUP/REVERSAL
    -- SUPPLIER 账本: COST/TOPUP/TRANSFER_OUT/TRANSFER_IN/REVERSAL
    CONSTRAINT chk_ledger_entry_type_by_ledger CHECK (
        (ledger_type = 'PROJECT' AND entry_type IN ('REVENUE', 'TOPUP', 'REVERSAL')) OR
        (ledger_type = 'SUPPLIER' AND entry_type IN ('COST', 'TOPUP', 'TRANSFER_OUT', 'TRANSFER_IN', 'REVERSAL'))
    )
);

CREATE INDEX IF NOT EXISTS idx_ledger_project ON ledger_entries(project_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_ledger_supplier ON ledger_entries(supplier_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_ledger_entry_type ON ledger_entries(entry_type);
CREATE INDEX IF NOT EXISTS idx_ledger_type ON ledger_entries(ledger_type);

-- ledger_entries 不可变性保护触发器 (MASTER.md INV-001, PATTERNS.md AP-LED-001)
CREATE TRIGGER trg_ledger_immutable_update BEFORE UPDATE ON ledger_entries
    FOR EACH ROW EXECUTE FUNCTION fn_ledger_immutable();

CREATE TRIGGER trg_ledger_immutable_delete BEFORE DELETE ON ledger_entries
    FOR EACH ROW EXECUTE FUNCTION fn_ledger_immutable();

-- =============================================================================
-- 8. 死号余额迁移表
-- =============================================================================

-- 8.1 transfer_requests (死号余额迁移申请) - DATA_SCHEMA.md §3.4.6
-- 状态枚举: STATE_MACHINE.md §12 transfer_requests.status
CREATE TABLE IF NOT EXISTS transfer_requests (
    id BIGSERIAL PRIMARY KEY,
    request_no VARCHAR(50) UNIQUE NOT NULL,
    source_ad_account_id BIGINT NOT NULL REFERENCES ad_accounts(id) ON DELETE RESTRICT,
    target_ad_account_id BIGINT NOT NULL REFERENCES ad_accounts(id) ON DELETE RESTRICT,
    transfer_amount DECIMAL(15,2) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN (
        'draft', 'pending_approval', 'approved', 'rejected', 'completed'
    )),
    version INTEGER NOT NULL DEFAULT 1,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    approved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_transfer_requests_request_no ON transfer_requests(request_no);
CREATE INDEX IF NOT EXISTS idx_transfer_requests_source_account ON transfer_requests(source_ad_account_id);
CREATE INDEX IF NOT EXISTS idx_transfer_requests_target_account ON transfer_requests(target_ad_account_id);
CREATE INDEX IF NOT EXISTS idx_transfer_requests_status ON transfer_requests(status);

CREATE TRIGGER trg_transfer_requests_updated_at BEFORE UPDATE ON transfer_requests
    FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();

-- =============================================================================
-- 9. 对账模块表
-- =============================================================================

-- 9.1 reconciliation_batches (对账批次) - DATA_SCHEMA.md §3.5.1
-- 状态枚举: STATE_MACHINE.md §11.1 reconciliation_batches.status
CREATE TABLE IF NOT EXISTS reconciliation_batches (
    id BIGSERIAL PRIMARY KEY,
    batch_no VARCHAR(50) UNIQUE NOT NULL,
    project_id BIGINT REFERENCES projects(id) ON DELETE SET NULL,
    status VARCHAR(20) CHECK (status IN (
        'draft', 'pending_review', 'approved', 'needs_adjustment', 'completed'
    )),
    source VARCHAR(50),
    period_start DATE,
    period_end DATE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reconciliation_batches_batch_no ON reconciliation_batches(batch_no);
CREATE INDEX IF NOT EXISTS idx_reconciliation_batches_project ON reconciliation_batches(project_id);
CREATE INDEX IF NOT EXISTS idx_reconciliation_batches_status ON reconciliation_batches(status);

CREATE TRIGGER trg_reconciliation_batches_updated_at BEFORE UPDATE ON reconciliation_batches
    FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();

-- 9.2 reconciliation_details (对账明细) - DATA_SCHEMA.md §3.5.2
-- 状态枚举: STATE_MACHINE.md §11.2 reconciliation_details.status
CREATE TABLE IF NOT EXISTS reconciliation_details (
    id BIGSERIAL PRIMARY KEY,
    batch_id BIGINT NOT NULL REFERENCES reconciliation_batches(id) ON DELETE CASCADE,
    ad_account_id BIGINT REFERENCES ad_accounts(id) ON DELETE SET NULL,
    report_date DATE,
    system_spend DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    external_spend DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    difference_amount DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) CHECK (status IN ('pending', 'confirmed', 'adjusted')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reconciliation_details_batch ON reconciliation_details(batch_id);
CREATE INDEX IF NOT EXISTS idx_reconciliation_details_account ON reconciliation_details(ad_account_id);

-- 9.3 reconciliation_adjustments (对账调整) - DATA_SCHEMA.md §3.5.3
-- adjustment_type 枚举: DATA_SCHEMA.md 固定 increase/decrease/writeoff
CREATE TABLE IF NOT EXISTS reconciliation_adjustments (
    id BIGSERIAL PRIMARY KEY,
    detail_id BIGINT NOT NULL REFERENCES reconciliation_details(id) ON DELETE CASCADE,
    adjustment_type VARCHAR(20) CHECK (adjustment_type IN ('increase', 'decrease', 'writeoff')),
    amount DECIMAL(15,2) NOT NULL,
    reason TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reconciliation_adjustments_detail ON reconciliation_adjustments(detail_id);

-- 9.4 reconciliation_reports (对账报告) - DATA_SCHEMA.md §3.5.4
CREATE TABLE IF NOT EXISTS reconciliation_reports (
    id BIGSERIAL PRIMARY KEY,
    batch_id BIGINT NOT NULL REFERENCES reconciliation_batches(id) ON DELETE CASCADE,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    generated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    report_url TEXT,
    metrics JSONB
);

CREATE INDEX IF NOT EXISTS idx_reconciliation_reports_batch ON reconciliation_reports(batch_id);

-- =============================================================================
-- 10. 辅助视图 (可选)
-- =============================================================================

-- 10.1 项目余额视图 (余额 = SUM(ledger_entries.amount) WHERE ledger_type = 'PROJECT')
-- 注意: 此为只读视图，符合 MASTER.md INV-001 "余额 = SUM(entries)" 原则
CREATE OR REPLACE VIEW v_project_balance AS
SELECT
    p.id AS project_id,
    p.name AS project_name,
    COALESCE(SUM(le.amount), 0.00) AS balance
FROM projects p
LEFT JOIN ledger_entries le ON le.project_id = p.id AND le.ledger_type = 'PROJECT'
GROUP BY p.id, p.name;

-- 10.2 供应商余额视图 (验证用，实际余额以 suppliers.balance 为准)
CREATE OR REPLACE VIEW v_supplier_balance AS
SELECT
    s.id AS supplier_id,
    s.name AS supplier_name,
    s.balance AS current_balance,
    COALESCE(SUM(le.amount), 0.00) AS calculated_balance
FROM suppliers s
LEFT JOIN ledger_entries le ON le.supplier_id = s.id AND le.ledger_type = 'SUPPLIER'
GROUP BY s.id, s.name, s.balance;

COMMIT;
