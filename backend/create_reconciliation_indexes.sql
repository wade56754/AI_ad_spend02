-- 对账系统性能优化索引
-- 在现有数据库上执行这些SQL语句以提升查询性能

-- 广告消耗日报索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ad_spend_daily_account_date
ON ad_spend_daily(ad_account_id, date);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ad_spend_daily_date
ON ad_spend_daily(date);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ad_spend_daily_account_id
ON ad_spend_daily(ad_account_id);

-- 对账详情索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reconciliation_details_batch_id
ON reconciliation_details(batch_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reconciliation_details_account_id
ON reconciliation_details(ad_account_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reconciliation_details_match_status
ON reconciliation_details(match_status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reconciliation_details_is_matched
ON reconciliation_details(is_matched);

-- 广告账户索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ad_accounts_status
ON ad_accounts(status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ad_accounts_project_id
ON ad_accounts(project_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ad_accounts_channel_id
ON ad_accounts(channel_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ad_accounts_status_project
ON ad_accounts(status, project_id);

-- 对账批次索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reconciliation_batches_date
ON reconciliation_batches(reconciliation_date);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reconciliation_batches_status
ON reconciliation_batches(status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reconciliation_batches_created_at
ON reconciliation_batches(created_at);

-- 复合索引，用于复杂查询优化
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reconciliation_details_batch_account
ON reconciliation_details(batch_id, ad_account_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reconciliation_batches_date_status
ON reconciliation_batches(reconciliation_date, status);

-- 项目相关索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_status
ON projects(status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_created_at
ON projects(created_at);

-- 渠道相关索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_channels_status
ON channels(status);

-- 统计查询优化索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reconciliation_batches_stats
ON reconciliation_batches(status, reconciliation_date);

-- 定期维护建议（可选，用于PostgreSQL）
-- 这些索引可以显著提升对账查询的性能，特别是：
-- 1. 按日期范围查询对账批次
-- 2. 按项目筛选账户
-- 3. 批量查询账户的消耗数据
-- 4. 对账详情的分页查询

-- 定期分析索引使用情况
-- SELECT indexname, idx_tup_read, idx_scan FROM pg_stat_user_indexes WHERE schemaname = 'public';

-- 定期重建统计信息
-- ANALYZE ad_spend_daily;
-- ANALYZE reconciliation_details;
-- ANALYZE ad_accounts;
-- ANALYZE reconciliation_batches;