-- =====================================================
-- Add Constraints: Daily Reports Unique & Suppliers Status Check
-- Version: P2-001, P2-002
-- Date: 2025-11-28
-- Description: 
--   P2-001: 添加日报唯一约束 (report_date, ad_account_id)
--   P2-002: 添加供应商状态 CHECK 约束
-- =====================================================

-- =====================================================
-- P2-001: 添加日报唯一约束
-- =====================================================
-- 确保同一账户在同一天只能有一条日报记录
-- 如果约束已存在，则跳过（使用 DO 块处理）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_constraint 
        WHERE conname = 'uq_daily_reports_date_account'
    ) THEN
        ALTER TABLE daily_reports 
        ADD CONSTRAINT uq_daily_reports_date_account 
        UNIQUE (report_date, ad_account_id);
        
        RAISE NOTICE 'Constraint uq_daily_reports_date_account created successfully';
    ELSE
        RAISE NOTICE 'Constraint uq_daily_reports_date_account already exists, skipping';
    END IF;
END $$;

-- =====================================================
-- P2-002: 添加供应商状态 CHECK 约束
-- =====================================================
-- 确保供应商状态只能是 active, inactive, suspended
-- 如果约束已存在，则跳过（使用 DO 块处理）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_constraint 
        WHERE conname = 'chk_suppliers_status'
    ) THEN
        ALTER TABLE suppliers 
        ADD CONSTRAINT chk_suppliers_status 
        CHECK (status IN ('active', 'inactive', 'suspended'));
        
        RAISE NOTICE 'Constraint chk_suppliers_status created successfully';
    ELSE
        RAISE NOTICE 'Constraint chk_suppliers_status already exists, skipping';
    END IF;
END $$;

-- =====================================================
-- 注释
-- =====================================================
COMMENT ON CONSTRAINT uq_daily_reports_date_account ON daily_reports IS 
    '确保同一广告账户在同一天只能有一条日报记录，防止重复提交';

COMMENT ON CONSTRAINT chk_suppliers_status ON suppliers IS 
    '限制供应商状态只能是 active, inactive, suspended 三个值之一';

