-- ========================================
-- 索引创建脚本 v3.3
-- PostgreSQL 15 + Supabase 兼容版
-- 说明: 使用 CONCURRENTLY 创建索引，避免锁表
-- 使用方法: 在主脚本执行后单独运行此脚本
-- ========================================

-- 设置事务隔离级别（CONCURRENTLY需要在事务外执行，所以每个索引独立执行）
SET client_min_messages TO WARNING;

-- ========================================
-- 1. 用户相关索引
-- ========================================

-- 用户表索引（优化）
CREATE INDEX CONCURRENTLY idx_users_email_active ON users(email) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_users_role_active ON users(role, is_active) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_users_login_fields ON users(username, email, is_active);
CREATE INDEX CONCURRENTLY idx_users_last_login ON users(last_login_at DESC) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_users_account_locked ON users(account_locked_until) WHERE account_locked_until IS NOT NULL;

-- 用户配置索引
CREATE INDEX CONCURRENTLY idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX CONCURRENTLY idx_user_profiles_department ON user_profiles(department) WHERE department IS NOT NULL;

-- ========================================
-- 2. 会话索引
-- ========================================

-- 会话表索引（安全优化）
CREATE INDEX CONCURRENTLY idx_sessions_user_active ON sessions(user_id, is_active) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_sessions_expires_active ON sessions(expires_at, is_active) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_sessions_token_lookup ON sessions(token_hash) WHERE token_hash IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_sessions_device_fingerprint ON sessions(device_fingerprint) WHERE device_fingerprint IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_sessions_created_at ON sessions(created_at DESC);

-- ========================================
-- 3. 项目相关索引
-- ========================================

-- 项目表索引（性能优化）
CREATE INDEX CONCURRENTLY idx_projects_owner_status ON projects(owner_id, status) WHERE status IN ('active', 'paused');
CREATE INDEX CONCURRENTLY idx_projects_account_manager ON projects(account_manager_id) WHERE account_manager_id IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_projects_created_at ON projects(created_at DESC);
CREATE INDEX CONCURRENTLY idx_projects_client_email ON projects(client_email) WHERE client_email IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_projects_status_created ON projects(status, created_at DESC);
CREATE INDEX CONCURRENTLY idx_projects_budget_spend ON projects(total_budget, total_spend) WHERE total_budget IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_projects_code ON projects(code);

-- 项目成员索引
CREATE INDEX CONCURRENTLY idx_project_members_user_role ON project_members(user_id, role) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_project_members_project_active ON project_members(project_id, is_active) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_project_members_joined_at ON project_members(joined_at DESC);

-- ========================================
-- 4. 渠道和账户索引
-- ========================================

-- 渠道表索引
CREATE INDEX CONCURRENTLY idx_channels_platform_status ON channels(platform, status) WHERE status = 'active';
CREATE INDEX CONCURRENTLY idx_channels_quality_score ON channels(quality_score DESC) WHERE quality_score IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_channels_manager ON channels(manager_id) WHERE manager_id IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_channels_code ON channels(code);

-- 广告账户索引（核心性能）
CREATE INDEX CONCURRENTLY idx_ad_accounts_project_status ON ad_accounts(project_id, status) WHERE status IN ('active', 'testing');
CREATE INDEX CONCURRENTLY idx_ad_accounts_channel_assigned ON ad_accounts(channel_id, assigned_to) WHERE assigned_to IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_ad_accounts_platform_status ON ad_accounts(platform, status) WHERE status IN ('active', 'testing');
CREATE INDEX CONCURRENTLY idx_ad_accounts_balance ON ad_accounts(remaining_budget DESC) WHERE remaining_budget > 0;
CREATE INDEX CONCURRENTLY idx_ad_accounts_spend_leads ON ad_accounts(total_spend DESC, total_leads DESC);
CREATE INDEX CONCURRENTLY idx_ad_accounts_assigned_active ON ad_accounts(assigned_to, status) WHERE status = 'active';
CREATE INDEX CONCURRENTLY idx_ad_accounts_account_id ON ad_accounts(account_id);
CREATE INDEX CONCURRENTLY idx_ad_accounts_last_status_change ON ad_accounts(last_status_change DESC);

-- ========================================
-- 5. 日报和充值索引
-- ========================================

-- 日报表索引（查询优化）
CREATE INDEX CONCURRENTLY idx_daily_reports_date_account ON daily_reports(report_date DESC, account_id);
CREATE INDEX CONCURRENTLY idx_daily_reports_status_date ON daily_reports(status, report_date DESC) WHERE status IN ('draft', 'submitted');
CREATE INDEX CONCURRENTLY idx_daily_reports_submitter_date ON daily_reports(submitter_id, report_date DESC);
CREATE INDEX CONCURRENTLY idx_daily_reports_reviewer_status ON daily_reports(reviewer_id, status) WHERE reviewer_id IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_daily_reports_spend ON daily_reports(spend DESC) WHERE spend > 0;
CREATE INDEX CONCURRENTLY idx_daily_reports_confirmed ON daily_reports(leads_confirmed DESC) WHERE leads_confirmed IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_daily_reports_quality_score ON daily_reports(lead_quality_score DESC) WHERE lead_quality_score IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_daily_reports_project_date ON daily_reports(project_id, report_date DESC);
CREATE INDEX CONCURRENTLY idx_daily_reports_created_at ON daily_reports(created_at DESC);

-- 充值表索引（流程优化）
CREATE INDEX CONCURRENTLY idx_topups_status_created ON topups(status, created_at DESC) WHERE status IN ('draft', 'pending_review', 'approved');
CREATE INDEX CONCURRENTLY idx_topups_account_status ON topups(account_id, status) WHERE status IN ('draft', 'pending_review', 'approved');
CREATE INDEX CONCURRENTLY idx_topups_amount_range ON topups(amount DESC) WHERE status IN ('approved', 'paid');
CREATE INDEX CONCURRENTLY idx_topups_requester_created ON topups(requester_id, created_at DESC);
CREATE INDEX CONCURRENTLY idx_topups_urgency_status ON topups(urgency_level, status) WHERE urgency_level IN ('urgent', 'emergency');
CREATE INDEX CONCURRENTLY idx_topups_project_id ON topups(project_id);
CREATE INDEX CONCURRENTLY idx_topups_request_id ON topups(request_id);

-- 充值财务表索引
CREATE INDEX CONCURRENTLY idx_topup_financial_topup_id ON topup_financial(topup_id);
CREATE INDEX CONCURRENTLY idx_topup_financial_paid_at ON topup_financial(paid_at DESC) WHERE paid_at IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_topup_financial_transaction_id ON topup_financial(transaction_id) WHERE transaction_id IS NOT NULL;

-- ========================================
-- 6. 审计和历史索引
-- ========================================

-- 审计日志索引（追踪优化）
CREATE INDEX CONCURRENTLY idx_audit_logs_user_created ON audit_logs(user_id, created_at DESC);
CREATE INDEX CONCURRENTLY idx_audit_logs_resource_action ON audit_logs(resource_type, resource_id, action);
CREATE INDEX CONCURRENTLY idx_audit_logs_event_type ON audit_logs(event_type, created_at DESC);
CREATE INDEX CONCURRENTLY idx_audit_logs_ip_address ON audit_logs(ip_address, created_at DESC) WHERE ip_address IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_audit_logs_level_created ON audit_logs(level, created_at DESC) WHERE level IN ('high', 'critical');
CREATE INDEX CONCURRENTLY idx_audit_logs_batch_id ON audit_logs(batch_id, created_at) WHERE batch_id IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX CONCURRENTLY idx_audit_logs_success ON audit_logs(success, created_at DESC) WHERE success = false;

-- 账户状态历史索引
CREATE INDEX CONCURRENTLY idx_account_status_history_account ON account_status_history(account_id, changed_at DESC);
CREATE INDEX CONCURRENTLY idx_account_status_history_changed_by ON account_status_history(changed_by, changed_at DESC);
CREATE INDEX CONCURRENTLY idx_account_status_history_source ON account_status_history(change_source, changed_at DESC);
CREATE INDEX CONCURRENTLY idx_account_status_history_new_status ON account_status_history(new_status, changed_at DESC);

-- ========================================
-- 7. 对账表索引
-- ========================================

CREATE INDEX CONCURRENTLY idx_reconciliations_project_id ON reconciliations(project_id);
CREATE INDEX CONCURRENTLY idx_reconciliations_period ON reconciliations(period_start, period_end);
CREATE INDEX CONCURRENTLY idx_reconciliations_status ON reconciliations(status, created_at DESC);
CREATE INDEX CONCURRENTLY idx_reconciliations_reconciliation_id ON reconciliations(reconciliation_id);
CREATE INDEX CONCURRENTLY idx_reconciliations_completed_at ON reconciliations(completed_at DESC) WHERE completed_at IS NOT NULL;

-- ========================================
-- 8. 系统配置索引
-- ========================================

CREATE INDEX CONCURRENTLY idx_system_config_key ON system_config(config_key);
CREATE INDEX CONCURRENTLY idx_system_config_updated_at ON system_config(updated_at DESC);

-- ========================================
-- 完成提示
-- ========================================

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '索引创建完成 v3.3';
    RAISE NOTICE '========================================';
    RAISE NOTICE '所有索引已使用 CONCURRENTLY 创建';
    RAISE NOTICE '========================================';
END $$;