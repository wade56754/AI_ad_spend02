-- ============================================================
-- 创建 reconciliation 基础表（简化版，无RLS）
-- 用途: 为 Phase 1 迁移准备基础表结构
-- 执行环境: Dev
-- ============================================================

-- 表1: reconciliation_batches (对账批次表)
CREATE TABLE IF NOT EXISTS reconciliation_batches (
    id INTEGER PRIMARY KEY,
    batch_no VARCHAR(50) UNIQUE NOT NULL,
    reconciliation_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    total_accounts INTEGER NOT NULL DEFAULT 0,
    matched_accounts INTEGER NOT NULL DEFAULT 0,
    mismatched_accounts INTEGER NOT NULL DEFAULT 0,
    total_platform_spend NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    total_internal_spend NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    total_difference NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    auto_matched INTEGER,
    manual_reviewed INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT,
    CONSTRAINT check_batch_status
        CHECK (status IN ('pending', 'processing', 'completed', 'exception', 'resolved')),
    CONSTRAINT check_total_accounts_non_negative CHECK (total_accounts >= 0),
    CONSTRAINT check_matched_accounts_non_negative CHECK (matched_accounts >= 0),
    CONSTRAINT check_mismatched_accounts_non_negative CHECK (mismatched_accounts >= 0),
    CONSTRAINT check_auto_matched_non_negative CHECK (auto_matched >= 0),
    CONSTRAINT check_manual_reviewed_non_negative CHECK (manual_reviewed >= 0)
);

COMMENT ON TABLE reconciliation_batches IS '对账批次表';
COMMENT ON COLUMN reconciliation_batches.batch_no IS '对账批次号';
COMMENT ON COLUMN reconciliation_batches.reconciliation_date IS '对账日期';
COMMENT ON COLUMN reconciliation_batches.status IS '对账状态';

CREATE INDEX IF NOT EXISTS idx_reconciliation_batches_date ON reconciliation_batches(reconciliation_date);
CREATE INDEX IF NOT EXISTS idx_reconciliation_batches_status ON reconciliation_batches(status);
CREATE INDEX IF NOT EXISTS idx_reconciliation_batches_created_at ON reconciliation_batches(created_at);

-- 创建序列
CREATE SEQUENCE IF NOT EXISTS reconciliation_batches_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE reconciliation_batches ALTER COLUMN id SET DEFAULT nextval('reconciliation_batches_id_seq');
ALTER SEQUENCE reconciliation_batches_id_seq OWNED BY reconciliation_batches.id;

-- 表2: reconciliation_details (对账详情表)
CREATE TABLE IF NOT EXISTS reconciliation_details (
    id INTEGER PRIMARY KEY,
    batch_id INTEGER NOT NULL,
    ad_account_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    platform_spend NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    platform_currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    platform_data_date DATE,
    internal_spend NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    internal_currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    internal_data_date DATE,
    spend_difference NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    exchange_rate NUMERIC(10, 4) NOT NULL DEFAULT 1.0000,
    is_matched BOOLEAN NOT NULL DEFAULT false,
    match_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    difference_type VARCHAR(50),
    difference_reason TEXT,
    auto_confidence NUMERIC(3, 2) NOT NULL DEFAULT 0.00,
    reviewed_by INTEGER,
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    resolved_by INTEGER,
    resolved_at TIMESTAMP,
    resolution_method VARCHAR(50),
    resolution_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_batch FOREIGN KEY (batch_id) REFERENCES reconciliation_batches(id) ON DELETE CASCADE,
    CONSTRAINT check_match_status
        CHECK (match_status IN ('pending', 'matched', 'auto_matched', 'manual_review', 'exception', 'resolved')),
    CONSTRAINT check_auto_confidence_range
        CHECK (auto_confidence >= 0 AND auto_confidence <= 1)
);

COMMENT ON TABLE reconciliation_details IS '对账详情表';

CREATE INDEX IF NOT EXISTS idx_reconciliation_details_batch ON reconciliation_details(batch_id);
CREATE INDEX IF NOT EXISTS idx_reconciliation_details_account ON reconciliation_details(ad_account_id);
CREATE INDEX IF NOT EXISTS idx_reconciliation_details_status ON reconciliation_details(match_status);
CREATE INDEX IF NOT EXISTS idx_reconciliation_details_date ON reconciliation_details(platform_data_date);

CREATE SEQUENCE IF NOT EXISTS reconciliation_details_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE reconciliation_details ALTER COLUMN id SET DEFAULT nextval('reconciliation_details_id_seq');
ALTER SEQUENCE reconciliation_details_id_seq OWNED BY reconciliation_details.id;

-- 表3: reconciliation_adjustments (对账调整记录表)
CREATE TABLE IF NOT EXISTS reconciliation_adjustments (
    id INTEGER PRIMARY KEY,
    detail_id INTEGER NOT NULL,
    batch_id INTEGER NOT NULL,
    adjustment_type VARCHAR(50) NOT NULL,
    original_amount NUMERIC(15, 2) NOT NULL,
    adjustment_amount NUMERIC(15, 2) NOT NULL,
    adjusted_amount NUMERIC(15, 2) NOT NULL,
    adjustment_reason VARCHAR(100) NOT NULL,
    detailed_reason TEXT NOT NULL,
    evidence_url VARCHAR(500),
    approved_by INTEGER NOT NULL,
    approved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finance_approve BOOLEAN NOT NULL DEFAULT false,
    finance_approved_by INTEGER,
    finance_approved_at TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT,
    CONSTRAINT fk_detail FOREIGN KEY (detail_id) REFERENCES reconciliation_details(id) ON DELETE CASCADE,
    CONSTRAINT fk_batch_adj FOREIGN KEY (batch_id) REFERENCES reconciliation_batches(id) ON DELETE CASCADE,
    CONSTRAINT check_adjustment_type
        CHECK (adjustment_type IN ('spend_adjustment', 'date_adjustment'))
);

COMMENT ON TABLE reconciliation_adjustments IS '对账调整记录表';

CREATE INDEX IF NOT EXISTS idx_reconciliation_adjustments_detail ON reconciliation_adjustments(detail_id);
CREATE INDEX IF NOT EXISTS idx_reconciliation_adjustments_batch ON reconciliation_adjustments(batch_id);
CREATE INDEX IF NOT EXISTS idx_reconciliation_adjustments_type ON reconciliation_adjustments(adjustment_type);

CREATE SEQUENCE IF NOT EXISTS reconciliation_adjustments_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE reconciliation_adjustments ALTER COLUMN id SET DEFAULT nextval('reconciliation_adjustments_id_seq');
ALTER SEQUENCE reconciliation_adjustments_id_seq OWNED BY reconciliation_adjustments.id;

-- 表4: reconciliation_reports (对账报告表)
CREATE TABLE IF NOT EXISTS reconciliation_reports (
    id INTEGER PRIMARY KEY,
    batch_id INTEGER,
    report_type VARCHAR(50) NOT NULL,
    report_period_start DATE NOT NULL,
    report_period_end DATE NOT NULL,
    report_data JSON NOT NULL,
    chart_data JSON,
    summary_data JSON NOT NULL,
    generated_by INTEGER NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    file_path VARCHAR(500),
    file_size INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_batch_report FOREIGN KEY (batch_id) REFERENCES reconciliation_batches(id),
    CONSTRAINT check_report_type
        CHECK (report_type IN ('daily', 'weekly', 'monthly')),
    CONSTRAINT check_report_period_valid
        CHECK (report_period_end >= report_period_start)
);

COMMENT ON TABLE reconciliation_reports IS '对账报告表';

CREATE INDEX IF NOT EXISTS idx_reconciliation_reports_batch ON reconciliation_reports(batch_id);
CREATE INDEX IF NOT EXISTS idx_reconciliation_reports_type ON reconciliation_reports(report_type);
CREATE INDEX IF NOT EXISTS idx_reconciliation_reports_period ON reconciliation_reports(report_period_start);

CREATE SEQUENCE IF NOT EXISTS reconciliation_reports_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE reconciliation_reports ALTER COLUMN id SET DEFAULT nextval('reconciliation_reports_id_seq');
ALTER SEQUENCE reconciliation_reports_id_seq OWNED BY reconciliation_reports.id;

-- 验证创建结果
SELECT
    tablename,
    schemaname
FROM pg_tables
WHERE tablename LIKE 'reconciliation_%'
ORDER BY tablename;
