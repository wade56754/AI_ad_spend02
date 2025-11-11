-- =====================================================
-- 分区表实现脚本
-- 版本: v1.0
-- 日期: 2025-11-11
-- 说明: 为大数据量表实现分区，提高查询性能
-- =====================================================

BEGIN;

-- =====================================================
-- 1. 创建ad_spend_daily分区表
-- =====================================================

-- 1.1 创建分区表结构
CREATE TABLE ad_spend_daily_partitioned (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 关联信息
    project_id UUID NOT NULL,
    ad_account_id UUID NOT NULL,
    user_id UUID NOT NULL,

    -- 日期和基础数据
    date DATE NOT NULL,
    leads_submitted INTEGER DEFAULT 0 CHECK (leads_submitted >= 0),
    spend NUMERIC(15,2) NOT NULL CHECK (spend >= 0),
    impressions INTEGER DEFAULT 0 CHECK (impressions >= 0),
    clicks INTEGER DEFAULT 0 CHECK (clicks >= 0),

    -- 甲方确认数据
    leads_confirmed INTEGER,
    confirmed_by UUID,
    confirmed_at TIMESTAMP WITH TIME ZONE,

    -- 差异分析
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

    -- 唯一约束（需要包含分区键）
    CONSTRAINT uk_ad_spend_daily_partitioned_account_date UNIQUE (ad_account_id, date)
) PARTITION BY RANGE (date);

-- 1.2 创建历史分区（2024年）
DO $$
DECLARE
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
    month_date DATE;
BEGIN
    -- 创建2024年1-12月的分区
    month_date := DATE '2024-01-01';
    FOR i IN 0..11 LOOP
        start_date := month_date + (i || ' months')::INTERVAL;
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'ad_spend_daily_y2024m' || LPAD((i+1)::TEXT, 2, '0');

        EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %I
                          FOR VALUES FROM (%L) TO (%L)',
                         partition_name, 'ad_spend_daily_partitioned',
                         start_date, end_date);

        -- 创建索引
        EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (ad_account_id)',
                       'idx_' || partition_name || '_account', partition_name);
        EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (project_id)',
                       'idx_' || partition_name || '_project', partition_name);
        EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (user_id)',
                       'idx_' || partition_name || '_user', partition_name);
    END LOOP;
END $$;

-- 1.3 创建当前和未来分区（2025年）
DO $$
DECLARE
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
    month_date DATE;
BEGIN
    -- 创建2025年1-12月的分区
    month_date := DATE '2025-01-01';
    FOR i IN 0..11 LOOP
        start_date := month_date + (i || ' months')::INTERVAL;
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'ad_spend_daily_y2025m' || LPAD((i+1)::TEXT, 2, '0');

        EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %I
                          FOR VALUES FROM (%L) TO (%L)',
                         partition_name, 'ad_spend_daily_partitioned',
                         start_date, end_date);

        -- 创建索引
        EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (ad_account_id)',
                       'idx_' || partition_name || '_account', partition_name);
        EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (project_id)',
                       'idx_' || partition_name || '_project', partition_name);
        EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (user_id)',
                       'idx_' || partition_name || '_user', partition_name);
    END LOOP;
END $$;

-- =====================================================
-- 2. 创建自动分区维护函数
-- =====================================================

-- 2.1 创建未来分区函数
CREATE OR REPLACE FUNCTION create_future_partitions()
RETURNS void AS $$
DECLARE
    months_to_create INTEGER := 6; -- 创建未来6个月的分区
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
    partition_exists BOOLEAN;
    i INTEGER;
BEGIN
    RAISE NOTICE '开始创建未来分区...';

    FOR i IN 0..months_to_create LOOP
        start_date := date_trunc('month', CURRENT_DATE) + (i || ' months')::INTERVAL;
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'ad_spend_daily_y' || to_char(start_date, 'YYYY') || 'm' || to_char(start_date, 'MM');

        -- 检查分区是否已存在
        SELECT EXISTS (
            SELECT 1 FROM pg_tables
            WHERE tablename = partition_name
        ) INTO partition_exists;

        IF NOT partition_exists THEN
            EXECUTE format('CREATE TABLE %I PARTITION OF %I
                             FOR VALUES FROM (%L) TO (%L)',
                         partition_name, 'ad_spend_daily_partitioned',
                         start_date, end_date);

            -- 创建索引
            EXECUTE format('CREATE INDEX %I ON %I (ad_account_id)',
                           'idx_' || partition_name || '_account', partition_name);
            EXECUTE format('CREATE INDEX %I ON %I (project_id)',
                           'idx_' || partition_name || '_project', partition_name);
            EXECUTE format('CREATE INDEX %I ON %I (user_id)',
                           'idx_' || partition_name || '_user', partition_name);

            RAISE NOTICE '创建分区: %', partition_name;
        END IF;
    END LOOP;

    RAISE NOTICE '未来分区创建完成';
END;
$$ LANGUAGE plpgsql;

-- 2.2 清理旧分区函数
CREATE OR REPLACE FUNCTION cleanup_old_partitions()
RETURNS void AS $$
DECLARE
    months_to_keep INTEGER := 12; -- 保留12个月的分区
    cutoff_date DATE;
    partition_name TEXT;
    partition_to_drop RECORD;
BEGIN
    cutoff_date := date_trunc('month', CURRENT_DATE) - (months_to_keep || ' months')::INTERVAL;
    RAISE NOTICE '开始清理 % 之前的分区...', cutoff_date;

    -- 查找需要删除的分区
    FOR partition_to_drop IN
        SELECT
            schemaname,
            tablename
        FROM pg_tables
        WHERE tablename LIKE 'ad_spend_daily_y%'
        AND tablename < ('ad_spend_daily_y' || to_char(cutoff_date, 'YYYY') || 'm' || to_char(cutoff_date, 'MM'))
    LOOP
        -- 先归档数据（可选）
        -- EXECUTE format('CREATE TABLE IF NOT EXISTS archive_%I AS SELECT * FROM %I',
        --                partition_to_drop.tablename, partition_to_drop.tablename);

        -- 删除分区
        EXECUTE format('DROP TABLE IF EXISTS %I.%I CASCADE',
                       partition_to_drop.schemaname, partition_to_drop.tablename);

        RAISE NOTICE '删除分区: %.%', partition_to_drop.schemaname, partition_to_drop.tablename;
    END LOOP;

    RAISE NOTICE '旧分区清理完成';
END;
$$ LANGUAGE plpgsql;

-- 2.3 自动维护主函数
CREATE OR REPLACE FUNCTION maintain_partitions()
RETURNS void AS $$
BEGIN
    -- 创建未来分区
    PERFORM create_future_partitions();

    -- 清理旧分区（根据需要启用）
    -- PERFORM cleanup_old_partitions();
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 3. 创建分区表迁移脚本
-- =====================================================

-- 3.1 迁移现有数据到分区表
CREATE OR REPLACE FUNCTION migrate_to_partitioned_table()
RETURNS void AS $$
DECLARE
    total_rows BIGINT;
    batch_size INTEGER := 10000;
    offset_val INTEGER := 0;
    migrated_rows BIGINT;
BEGIN
    -- 获取原表总行数
    SELECT COUNT(*) INTO total_rows FROM ad_spend_daily;
    RAISE NOTICE '原表总行数: %', total_rows;

    -- 分批迁移数据
    LOOP
        INSERT INTO ad_spend_daily_partitioned
        SELECT * FROM ad_spend_daily
        LIMIT batch_size OFFSET offset_val;

        GET DIAGNOSTICS migrated_rows = ROW_COUNT;
        RAISE NOTICE '已迁移 % 行，进度: %/%',
                    offset_val + migrated_rows,
                    offset_val + migrated_rows, total_rows;

        EXIT WHEN migrated_rows < batch_size;
        offset_val := offset_val + batch_size;

        -- 提交批次，避免长事务
        COMMIT;
    END LOOP;

    RAISE NOTICE '数据迁移完成';
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 4. 创建分区监控视图
-- =====================================================

-- 4.1 分区状态监控视图
CREATE OR REPLACE VIEW partition_status AS
SELECT
    schemaname,
    tablename,
    tableowner,
    hasindexes,
    hasrules,
    hastriggers
FROM pg_tables
WHERE tablename LIKE 'ad_spend_daily_%'
ORDER BY tablename DESC;

-- 4.2 分区数据统计视图
CREATE OR REPLACE VIEW partition_statistics AS
SELECT
    c.relname as partition_name,
    pg_size_pretty(pg_total_relation_size(c.oid)) as size,
    s.n_tup_ins as inserts,
    s.n_tup_upd as updates,
    s.n_tup_del as deletes,
    s.n_live_tup as live_tuples,
    s.n_dead_tup as dead_tuples,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_stat_user_tables s ON s.relid = c.oid
WHERE c.relname LIKE 'ad_spend_daily_%'
AND c.relkind = 'r'
ORDER BY c.relname;

-- =====================================================
-- 5. 创建定时任务（需要pg_cron扩展）
-- =====================================================

-- 5.1 安装pg_cron扩展（如果未安装）
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- 5.2 定时任务配置
-- 每月1号创建新分区
SELECT cron.schedule(
    'create-monthly-partition',
    '0 3 1 * *',  -- 每月1号凌晨3点
    'SELECT maintain_partitions();'
);

-- 每天凌晨2点检查分区状态
SELECT cron.schedule(
    'check-partition-status',
    '0 2 * * *',  -- 每天凌晨2点
    'SELECT tablename FROM partition_status WHERE tablename NOT LIKE ''%' || to_char(date_trunc(''month'', CURRENT_DATE), ''YYYYmMM'') || ''%'''
);

-- =====================================================
-- 6. 创建切换到分区表的脚本
-- =====================================================

-- 6.1 备份原表
CREATE OR REPLACE FUNCTION backup_original_table()
RETURNS void AS $$
BEGIN
    -- 重命名原表
    ALTER TABLE ad_spend_daily RENAME TO ad_spend_daily_backup;

    -- 将分区表重命名为正式表名
    ALTER TABLE ad_spend_daily_partitioned RENAME TO ad_spend_daily;

    -- 重建外键约束（因为原表被删除）
    ALTER TABLE ad_spend_daily
    ADD CONSTRAINT ad_spend_daily_project_id_fkey
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;

    ALTER TABLE ad_spend_daily
    ADD CONSTRAINT ad_spend_daily_ad_account_id_fkey
    FOREIGN KEY (ad_account_id) REFERENCES ad_accounts(id) ON DELETE CASCADE;

    ALTER TABLE ad_spend_daily
    ADD CONSTRAINT ad_spend_daily_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

    -- 重建RLS策略
    ALTER TABLE ad_spend_daily ENABLE ROW LEVEL SECURITY;

    -- 重建其他索引
    CREATE INDEX idx_ad_spend_daily_leads_confirmed
    ON ad_spend_daily(leads_confirmed) WHERE leads_confirmed IS NOT NULL;

    CREATE INDEX idx_ad_spend_daily_spend
    ON ad_spend_daily(spend) WHERE spend > 0;

    RAISE NOTICE '已切换到分区表，原表备份为 ad_spend_daily_backup';
END;
$$ LANGUAGE plpgsql;

COMMIT;

-- =====================================================
-- 使用说明
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '===========================================';
    RAISE NOTICE '分区表创建脚本执行完成！';
    RAISE NOTICE '===========================================';
    RAISE NOTICE '后续步骤：';
    RAISE NOTICE '1. 执行 SELECT migrate_to_partitioned_table(); 迁移数据';
    RAISE NOTICE '2. 验证数据迁移结果';
    RAISE NOTICE '3. 执行 SELECT backup_original_table(); 切换到分区表';
    RAISE NOTICE '4. 运行 SELECT maintain_partitions(); 创建定期任务';
    RAISE NOTICE '===========================================';
END $$;