-- ====================================================================
-- 数据库 Schema 修复：将指定表的主键从 BIGINT 改为 UUID
-- 
-- 修复的表：
-- 1. channels - 渠道主表
-- 2. channel_reviews - 渠道评审记录
-- 3. channel_performance - 渠道表现统计
-- 4. channel_account_requests - 渠道开户申请
-- 5. ad_spend_daily - 外部导入日消耗
--
-- 同时修复所有引用这些表的外键列类型为 UUID
--
-- 版本: 1.0
-- 创建日期: 2025-01-XX
-- 对齐文档: docs/core/DATA_SCHEMA.md
-- ====================================================================

-- 启用 UUID 扩展（如果尚未启用）
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ====================================================================
-- 注意：本脚本适用于开发/测试环境
-- 如果数据库中有数据，需要先导出数据，然后重建表，再导入数据
-- 生产环境请参考迁移说明文档进行安全迁移
-- ====================================================================

-- ====================================================================
-- 1. 创建 channels 表（UUID 主键）
-- ====================================================================

-- 如果表已存在，先删除（仅开发环境，生产环境请使用 ALTER TABLE）
-- DROP TABLE IF EXISTS channel_performance CASCADE;
-- DROP TABLE IF EXISTS channel_reviews CASCADE;
-- DROP TABLE IF EXISTS channel_account_requests CASCADE;
-- DROP TABLE IF EXISTS channel_contacts CASCADE;
-- DROP TABLE IF EXISTS ad_accounts CASCADE;  -- 注意：需要先处理外键依赖
-- DROP TABLE IF EXISTS channels CASCADE;

CREATE TABLE IF NOT EXISTS channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL,
    channel_code VARCHAR(20) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'inactive')),
    country VARCHAR(10),
    notes TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_channels_code ON channels(channel_code);
CREATE INDEX IF NOT EXISTS idx_channels_status ON channels(status);
CREATE INDEX IF NOT EXISTS idx_channels_created_at ON channels(created_at);

-- ====================================================================
-- 2. 创建 channel_reviews 表（UUID 主键）
-- ====================================================================

CREATE TABLE IF NOT EXISTS channel_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    reviewer_id UUID REFERENCES users(id) ON DELETE SET NULL,
    review_status VARCHAR(20) NOT NULL CHECK (review_status IN ('draft', 'pending', 'approved', 'rejected')),
    review_notes TEXT,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_channel_reviews_channel_id ON channel_reviews(channel_id);
CREATE INDEX IF NOT EXISTS idx_channel_reviews_reviewer_id ON channel_reviews(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_channel_reviews_status ON channel_reviews(review_status);

-- ====================================================================
-- 3. 创建 channel_performance 表（UUID 主键）
-- ====================================================================

CREATE TABLE IF NOT EXISTS channel_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    stat_date DATE NOT NULL,
    total_accounts INTEGER NOT NULL DEFAULT 0,
    active_accounts INTEGER NOT NULL DEFAULT 0,
    dead_accounts INTEGER NOT NULL DEFAULT 0,
    total_spend DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    avg_account_lifespan DECIMAL(12,2),
    death_rate DECIMAL(12,4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(channel_id, stat_date)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_channel_performance_channel_id ON channel_performance(channel_id);
CREATE INDEX IF NOT EXISTS idx_channel_performance_stat_date ON channel_performance(stat_date);

-- ====================================================================
-- 4. 创建 channel_account_requests 表（UUID 主键）
-- ====================================================================

CREATE TABLE IF NOT EXISTS channel_account_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    requested_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL,
    request_notes TEXT,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_channel_account_requests_project_id ON channel_account_requests(project_id);
CREATE INDEX IF NOT EXISTS idx_channel_account_requests_channel_id ON channel_account_requests(channel_id);
CREATE INDEX IF NOT EXISTS idx_channel_account_requests_requested_by ON channel_account_requests(requested_by);
CREATE INDEX IF NOT EXISTS idx_channel_account_requests_status ON channel_account_requests(status);

-- ====================================================================
-- 5. 创建 ad_spend_daily 表（UUID 主键）
-- ====================================================================

CREATE TABLE IF NOT EXISTS ad_spend_daily (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ad_account_code VARCHAR(50) NOT NULL,
    spend_date DATE NOT NULL,
    impressions BIGINT,
    clicks BIGINT,
    conversions INTEGER,
    cost DECIMAL(15,2),
    revenue DECIMAL(15,2),
    roi DECIMAL(12,4),
    imported_by UUID REFERENCES users(id) ON DELETE SET NULL,
    imported_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(ad_account_code, spend_date)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_ad_spend_daily_account_code ON ad_spend_daily(ad_account_code);
CREATE INDEX IF NOT EXISTS idx_ad_spend_daily_spend_date ON ad_spend_daily(spend_date);
CREATE INDEX IF NOT EXISTS idx_ad_spend_daily_imported_by ON ad_spend_daily(imported_by);

-- ====================================================================
-- 6. 修复 ad_accounts 表的 channel_id 外键类型为 UUID
-- ====================================================================

-- 注意：如果 ad_accounts 表已存在且有数据，需要先备份数据，然后：
-- 1. 添加新的 UUID 列 channel_id_new
-- 2. 根据旧 channel_id (BIGINT) 映射到新的 UUID
-- 3. 删除旧列 channel_id，重命名 channel_id_new 为 channel_id
-- 
-- 这里仅提供开发环境的重建脚本，生产环境请参考迁移说明文档

-- ALTER TABLE ad_accounts DROP CONSTRAINT IF EXISTS ad_accounts_channel_id_fkey;
-- ALTER TABLE ad_accounts ADD COLUMN channel_id_new UUID;
-- -- 这里需要根据实际数据映射逻辑填充 channel_id_new
-- ALTER TABLE ad_accounts DROP COLUMN channel_id;
-- ALTER TABLE ad_accounts RENAME COLUMN channel_id_new TO channel_id;
-- ALTER TABLE ad_accounts ALTER COLUMN channel_id SET NOT NULL;
-- ALTER TABLE ad_accounts ADD CONSTRAINT ad_accounts_channel_id_fkey 
--     FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE;

-- ====================================================================
-- 完成
-- ====================================================================

-- 验证脚本：检查主键类型
-- SELECT 
--     table_name,
--     column_name,
--     data_type,
--     column_default
-- FROM information_schema.columns
-- WHERE table_name IN ('channels', 'channel_reviews', 'channel_performance', 
--                      'channel_account_requests', 'ad_spend_daily')
--   AND column_name = 'id'
-- ORDER BY table_name;

