-- =====================================================
-- 数据库设计修复脚本
-- 版本: v1.0
-- 日期: 2025-11-11
-- 说明: 修复DATA_SCHEMA.md中发现的严重问题
-- =====================================================

-- 开启事务，确保所有修改要么全部成功，要么全部回滚
BEGIN;

-- =====================================================
-- 1. 修复主键类型不一致问题
-- =====================================================

-- 1.1 创建新的audit_logs表（使用UUID主键）
CREATE TABLE audit_logs_new (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

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

-- 1.2 迁移数据（如果原表有数据）
INSERT INTO audit_logs_new (
    id, user_id, action, table_name, record_id,
    old_values, new_values, ip_address, user_agent,
    request_id, level, description, created_at
)
SELECT
    gen_random_uuid(),
    user_id, action, table_name, record_id,
    old_values, new_values, ip_address, user_agent,
    request_id, level, description, created_at
FROM audit_logs;

-- 1.3 删除旧表并重命名新表
DROP TABLE audit_logs CASCADE;
ALTER TABLE audit_logs_new RENAME TO audit_logs;

-- 1.4 重新创建索引
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_table_name ON audit_logs(table_name);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_level ON audit_logs(level);

-- =====================================================
-- 2. 完善外键约束和删除策略
-- =====================================================

-- 2.1 修复projects表的外键约束
-- 删除原有的外键约束（如果存在）
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'projects_manager_id_fkey'
        AND table_name = 'projects'
    ) THEN
        ALTER TABLE projects DROP CONSTRAINT projects_manager_id_fkey;
    END IF;
END $$;

-- 重新创建带正确删除策略的外键
ALTER TABLE projects
ADD CONSTRAINT projects_manager_id_fkey
FOREIGN KEY (manager_id) REFERENCES users(id) ON DELETE SET NULL;

-- 2.2 确保channels表的外键约束正确
ALTER TABLE channels
DROP CONSTRAINT IF EXISTS channels_created_by_fkey,
ADD CONSTRAINT channels_created_by_fkey
FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;

-- 2.3 修复users表的自引用外键
ALTER TABLE users
DROP CONSTRAINT IF EXISTS users_created_by_fkey,
ADD CONSTRAINT users_created_by_fkey
FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;

-- =====================================================
-- 3. 添加业务约束（CHECK约束）
-- =====================================================

-- 3.1 项目日期约束
ALTER TABLE projects
ADD CONSTRAINT ck_projects_date_logic
CHECK (end_date IS NULL OR start_date IS NULL OR end_date > start_date);

-- 3.2 预算金额非负约束
ALTER TABLE projects
ADD CONSTRAINT ck_projects_budget_positive
CHECK (
    monthly_budget IS NULL OR monthly_budget >= 0
);

ALTER TABLE projects
ADD CONSTRAINT ck_projects_total_budget_positive
CHECK (
    total_budget IS NULL OR total_budget >= 0
);

-- 3.3 账户预算约束
ALTER TABLE ad_accounts
ADD CONSTRAINT ck_ad_accounts_budget_logic
CHECK (
    -- 如果有总预算，日预算不能超过总预算
    total_budget IS NULL OR
    daily_budget IS NULL OR
    daily_budget <= total_budget
);

ALTER TABLE ad_accounts
ADD CONSTRAINT ck_ad_accounts_remaining_budget
CHECK (
    remaining_budget >= 0 AND
    (total_budget IS NULL OR remaining_budget <= total_budget)
);

-- 3.4 金额字段约束
ALTER TABLE topups
ADD CONSTRAINT ck_topups_amount_positive
CHECK (amount > 0);

ALTER TABLE topups
ADD CONSTRAINT ck_topups_fee_calculated
CHECK (fee_amount >= 0 AND total_amount >= amount);

ALTER TABLE ledgers
ADD CONSTRAINT ck_ledgers_amount_sign
CHECK (
    -- 收入为正，支出为负
    (transaction_type IN ('topup_payment', 'refund', 'adjustment') AND amount >= 0) OR
    (transaction_type = 'fee_charge' AND amount <= 0)
);

-- =====================================================
-- 4. 统一字段类型和精度
-- =====================================================

-- 4.1 统一金额字段精度为NUMERIC(15,2)
-- projects.lead_price已经是NUMERIC(10,2)，需要扩展
ALTER TABLE projects
ALTER COLUMN lead_price TYPE NUMERIC(15,2) USING lead_price::NUMERIC(15,2);

ALTER TABLE projects
ALTER COLUMN setup_fee TYPE NUMERIC(15,2) USING setup_fee::NUMERIC(15,2);

ALTER TABLE projects
ALTER COLUMN monthly_budget TYPE NUMERIC(15,2) USING monthly_budget::NUMERIC(15,2);

ALTER TABLE projects
ALTER COLUMN total_budget TYPE NUMERIC(15,2) USING total_budget::NUMERIC(15,2);

ALTER TABLE projects
ALTER COLUMN target_cpl TYPE NUMERIC(15,2) USING target_cpl::NUMERIC(15,2);

-- 4.2 统一费率字段为NUMERIC(5,4) - 支持到9999%
ALTER TABLE channels
ALTER COLUMN service_fee_rate TYPE NUMERIC(5,4) USING service_fee_rate::NUMERIC(5,4);

-- =====================================================
-- 5. 创建枚举类型（提高类型安全）
-- =====================================================

-- 5.1 创建用户角色枚举
DO $$ BEGIN
    CREATE TYPE user_role_enum AS ENUM (
        'admin', 'manager', 'data_clerk', 'finance', 'media_buyer'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 5.2 创建项目状态枚举
DO $$ BEGIN
    CREATE TYPE project_status_enum AS ENUM (
        'planning', 'active', 'paused', 'completed', 'cancelled'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 5.3 创建账户状态枚举
DO $$ BEGIN
    CREATE TYPE account_status_enum AS ENUM (
        'new', 'testing', 'active', 'suspended', 'dead', 'archived'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 5.4 创建充值状态枚举
DO $$ BEGIN
    CREATE TYPE topup_status_enum AS ENUM (
        'draft', 'pending', 'clerk_approved', 'finance_approved',
        'paid', 'posted', 'rejected'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 5.5 创建定价模型枚举
DO $$ BEGIN
    CREATE TYPE pricing_model_enum AS ENUM (
        'per_lead', 'fixed_fee', 'hybrid'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- =====================================================
-- 6. 添加缺失的关键索引
-- =====================================================

-- 6.1 复合索引 - 优化常用查询
CREATE INDEX idx_ad_accounts_project_status
ON ad_accounts(project_id, status);

CREATE INDEX idx_topups_project_status
ON topups(project_id, status);

CREATE INDEX idx_ad_spend_daily_project_date
ON ad_spend_daily(project_id, date);

CREATE INDEX idx_ad_spend_daily_account_date
ON ad_spend_daily(ad_account_id, date);

CREATE INDEX idx_ledgers_project_type
ON ledgers(project_id, transaction_type);

-- 6.2 部分索引 - 优化特定条件查询
CREATE INDEX idx_ad_accounts_active
ON ad_accounts(status) WHERE status = 'active';

CREATE INDEX idx_topups_pending
ON topups(status) WHERE status = 'pending';

CREATE INDEX idx_ad_spend_daily_confirmed
ON ad_spend_daily(leads_confirmed) WHERE leads_confirmed IS NOT NULL;

CREATE INDEX idx_projects_active
ON projects(status) WHERE status = 'active';

-- 6.3 外键索引 - 确保外键性能
CREATE INDEX idx_users_created_by
ON users(created_by);

-- =====================================================
-- 7. 余额更新触发器优化
-- =====================================================

-- 7.1 创建余额更新函数（事务安全）
CREATE OR REPLACE FUNCTION update_account_balance_safe()
RETURNS TRIGGER AS $$
DECLARE
    account_record ad_accounts%ROWTYPE;
    new_balance NUMERIC(15,2);
BEGIN
    -- 获取账户当前余额（加锁防止并发）
    SELECT * INTO account_record
    FROM ad_accounts
    WHERE id = NEW.ad_account_id
    FOR UPDATE;

    -- 只有状态为posted时才更新余额
    IF TG_OP = 'INSERT' AND NEW.status = 'posted' THEN
        new_balance := account_record.remaining_budget + NEW.amount;

        -- 验证余额合理性
        IF new_balance < 0 THEN
            RAISE EXCEPTION '余额不能为负数: 账户ID=%, 当前余额=%, 充值金额=%',
                NEW.ad_account_id, account_record.remaining_budget, NEW.amount;
        END IF;

        -- 更新余额
        UPDATE ad_accounts
        SET remaining_budget = new_balance,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.ad_account_id;

        -- 记录余额变更历史
        INSERT INTO account_balance_history (
            account_id, change_amount, balance_before, balance_after,
            change_type, reference_id, changed_at, changed_by
        ) VALUES (
            NEW.ad_account_id, NEW.amount, account_record.remaining_budget,
            new_balance, 'topup', NEW.id, CURRENT_TIMESTAMP, NEW.created_by
        );
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 7.2 替换原有触发器
DROP TRIGGER IF EXISTS update_account_balance_trigger ON topups;
CREATE TRIGGER update_account_balance_trigger
    AFTER INSERT ON topups
    FOR EACH ROW
    WHEN (NEW.status = 'posted')
    EXECUTE FUNCTION update_account_balance_safe();

-- =====================================================
-- 8. 创建数据验证函数
-- =====================================================

-- 8.1 验证邮箱格式
CREATE OR REPLACE FUNCTION is_valid_email(email TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 8.2 添加邮箱格式约束
ALTER TABLE users
ADD CONSTRAINT ck_users_email_format
CHECK (is_valid_email(email));

-- =====================================================
-- 9. 创建性能监控视图
-- =====================================================

-- 9.1 项目统计优化视图
CREATE OR REPLACE VIEW project_statistics_optimized AS
WITH account_stats AS (
    SELECT
        project_id,
        COUNT(*) as total_accounts,
        COUNT(*) FILTER (WHERE status = 'active') as active_accounts,
        COALESCE(SUM(total_spend), 0) as total_spend
    FROM ad_accounts
    GROUP BY project_id
),
daily_stats AS (
    SELECT
        p.id as project_id,
        COALESCE(SUM(dr.spend), 0) as total_daily_spend,
        COALESCE(SUM(dr.leads_confirmed), 0) as total_leads
    FROM projects p
    LEFT JOIN ad_accounts a ON p.id = a.project_id
    LEFT JOIN ad_spend_daily dr ON a.id = dr.ad_account_id
    GROUP BY p.id
)
SELECT
    p.id,
    p.name,
    p.client_name,
    p.status,
    p.pricing_model,
    p.lead_price,
    p.setup_fee,

    -- 账户统计
    COALESCE(ast.total_accounts, 0) as total_accounts,
    COALESCE(ast.active_accounts, 0) as active_accounts,

    -- 消耗统计
    COALESCE(ast.total_spend, 0) + COALESCE(ds.total_daily_spend, 0) as total_spend,
    COALESCE(ds.total_leads, 0) as total_leads,

    -- 收入统计
    p.setup_fee + (COALESCE(ds.total_leads, 0) * p.lead_price) as total_revenue,
    (p.setup_fee + (COALESCE(ds.total_leads, 0) * p.lead_price)) -
    (COALESCE(ast.total_spend, 0) + COALESCE(ds.total_daily_spend, 0)) as profit,

    -- 时间信息
    p.created_at,
    p.updated_at

FROM projects p
LEFT JOIN account_stats ast ON p.id = ast.project_id
LEFT JOIN daily_stats ds ON p.id = ds.project_id;

-- =====================================================
-- 10. 数据完整性验证
-- =====================================================

-- 10.1 创建验证函数
CREATE OR REPLACE FUNCTION validate_data_integrity()
RETURNS TABLE(
    error_type TEXT,
    error_count BIGINT,
    description TEXT
) AS $$
BEGIN
    -- 检查孤立记录
    RETURN QUERY
    SELECT
        'Orphaned account records'::TEXT,
        COUNT(*)::BIGINT,
        'ad_accounts记录指向不存在projects'::TEXT
    FROM ad_accounts a
    LEFT JOIN projects p ON a.project_id = p.id
    WHERE p.id IS NULL

    UNION ALL

    SELECT
        'Negative balances'::TEXT,
        COUNT(*)::BIGINT,
        '账户余额为负数'::TEXT
    FROM ad_accounts
    WHERE remaining_budget < 0

    UNION ALL

    SELECT
        'Invalid date ranges'::TEXT,
        COUNT(*)::BIGINT,
        '项目结束日期早于开始日期'::TEXT
    FROM projects
    WHERE end_date IS NOT NULL
    AND start_date IS NOT NULL
    AND end_date <= start_date;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 提交事务
-- =====================================================

-- 显示验证结果
SELECT * FROM validate_data_integrity();

COMMIT;

-- =====================================================
-- 修复完成提示
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '===========================================';
    RAISE NOTICE '数据库修复脚本执行完成！';
    RAISE NOTICE '===========================================';
    RAISE NOTICE '已完成修复内容：';
    RAISE NOTICE '1. 统一主键类型为UUID';
    RAISE NOTICE '2. 完善外键约束和删除策略';
    RAISE NOTICE '3. 添加业务约束和验证';
    RAISE NOTICE '4. 统一字段类型和精度';
    RAISE NOTICE '5. 创建枚举类型提高类型安全';
    RAISE NOTICE '6. 添加关键索引优化查询性能';
    RAISE NOTICE '7. 优化余额更新逻辑';
    RAISE NOTICE '8. 添加数据验证函数';
    RAISE NOTICE '9. 创建优化统计视图';
    RAISE NOTICE '10. 创建数据完整性验证函数';
    RAISE NOTICE '===========================================';
END $$;