-- Phase 1: Financial SoT 核心表结构
-- 根据 FINANCIAL_SOT_DESIGN.md v1.0 和 FINANCIAL_REFACTOR_PLAN.md Phase 1 要求
--
-- 执行顺序：
-- 1. 创建 teams 表
-- 2. 创建 buyers 表 (依赖 teams)
-- 3. 创建 financial_events 表
-- 4. 创建 balance_snapshots 表
-- 5. 扩展 suppliers 表
-- 6. 扩展 ad_accounts 表
-- 7. 扩展 ledger_entries 表

-- ========== 1. 创建 teams 表 ==========
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100),
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_teams_status CHECK (status IN ('active', 'inactive'))
);

COMMENT ON COLUMN teams.id IS '团队ID';
COMMENT ON COLUMN teams.code IS '团队代码 (SZ/ZZ)';
COMMENT ON COLUMN teams.name IS '团队名称';
COMMENT ON COLUMN teams.description IS '团队描述';
COMMENT ON COLUMN teams.status IS '状态';

CREATE INDEX IF NOT EXISTS idx_teams_code ON teams(code);
CREATE INDEX IF NOT EXISTS idx_teams_status ON teams(status);

-- ========== 2. 创建 buyers 表 ==========
CREATE TABLE IF NOT EXISTS buyers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100),
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_buyers_status CHECK (status IN ('active', 'inactive'))
);

COMMENT ON COLUMN buyers.id IS '投手ID';
COMMENT ON COLUMN buyers.code IS '投手代码';
COMMENT ON COLUMN buyers.name IS '投手姓名';
COMMENT ON COLUMN buyers.team_id IS '所属团队';
COMMENT ON COLUMN buyers.user_id IS '关联用户';
COMMENT ON COLUMN buyers.status IS '状态';

CREATE INDEX IF NOT EXISTS idx_buyers_code ON buyers(code);
CREATE INDEX IF NOT EXISTS idx_buyers_team_id ON buyers(team_id);
CREATE INDEX IF NOT EXISTS idx_buyers_user_id ON buyers(user_id);
CREATE INDEX IF NOT EXISTS idx_buyers_status ON buyers(status);

-- ========== 3. 创建 financial_events 表 ==========
CREATE TABLE IF NOT EXISTS financial_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 事件类型和状态
    event_type VARCHAR(20) NOT NULL,
    event_status VARCHAR(20) NOT NULL DEFAULT 'raw',

    -- 来源追溯
    source_type VARCHAR(50),
    source_ref VARCHAR(255),
    idempotency_key VARCHAR(255) UNIQUE NOT NULL,

    -- 金额字段
    amount NUMERIC(18, 4) NOT NULL,
    fee_amount NUMERIC(18, 4) NOT NULL DEFAULT 0,
    gross_amount NUMERIC(18, 4),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    event_date DATE NOT NULL,

    -- 关联实体
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    buyer_id UUID REFERENCES buyers(id) ON DELETE SET NULL,
    supplier_id UUID REFERENCES suppliers(id) ON DELETE SET NULL,
    ad_account_id BIGINT REFERENCES ad_accounts(id) ON DELETE SET NULL,
    project_id BIGINT REFERENCES projects(id) ON DELETE SET NULL,

    -- 扩展数据
    payload JSONB NOT NULL DEFAULT '{}',

    -- 审计字段
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    confirmed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    confirmed_at TIMESTAMPTZ,
    posted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 约束
    CONSTRAINT chk_financial_events_event_type CHECK (
        event_type IN ('TOPUP', 'SPEND', 'PAYMENT', 'TRANSFER', 'ADJUSTMENT', 'FEE', 'REFUND')
    ),
    CONSTRAINT chk_financial_events_event_status CHECK (
        event_status IN ('raw', 'pending', 'confirmed', 'posted', 'reversed')
    )
);

COMMENT ON COLUMN financial_events.id IS '事件ID';
COMMENT ON COLUMN financial_events.event_type IS '事件类型';
COMMENT ON COLUMN financial_events.event_status IS '事件状态';
COMMENT ON COLUMN financial_events.source_type IS '来源类型 (excel_import/api/manual)';
COMMENT ON COLUMN financial_events.source_ref IS '来源引用 (文件名/API调用ID)';
COMMENT ON COLUMN financial_events.idempotency_key IS '幂等键';
COMMENT ON COLUMN financial_events.amount IS '金额';
COMMENT ON COLUMN financial_events.fee_amount IS '手续费';
COMMENT ON COLUMN financial_events.gross_amount IS '含费金额';
COMMENT ON COLUMN financial_events.currency IS '币种';
COMMENT ON COLUMN financial_events.event_date IS '事件日期';
COMMENT ON COLUMN financial_events.team_id IS '团队ID';
COMMENT ON COLUMN financial_events.buyer_id IS '投手ID';
COMMENT ON COLUMN financial_events.supplier_id IS '供应商ID';
COMMENT ON COLUMN financial_events.ad_account_id IS '广告账户ID';
COMMENT ON COLUMN financial_events.project_id IS '项目ID';
COMMENT ON COLUMN financial_events.payload IS '扩展数据';
COMMENT ON COLUMN financial_events.created_by IS '创建者';
COMMENT ON COLUMN financial_events.confirmed_by IS '确认者';
COMMENT ON COLUMN financial_events.confirmed_at IS '确认时间';
COMMENT ON COLUMN financial_events.posted_at IS '入账时间';

-- 索引
CREATE INDEX IF NOT EXISTS idx_fin_events_type_status ON financial_events(event_type, event_status);
CREATE INDEX IF NOT EXISTS idx_fin_events_event_date ON financial_events(event_date);
CREATE INDEX IF NOT EXISTS idx_fin_events_supplier_id ON financial_events(supplier_id);
CREATE INDEX IF NOT EXISTS idx_fin_events_ad_account_id ON financial_events(ad_account_id);
CREATE INDEX IF NOT EXISTS idx_fin_events_project_id ON financial_events(project_id);
CREATE INDEX IF NOT EXISTS idx_fin_events_team_id ON financial_events(team_id);
CREATE INDEX IF NOT EXISTS idx_fin_events_buyer_id ON financial_events(buyer_id);
CREATE INDEX IF NOT EXISTS idx_fin_events_idempotency_key ON financial_events(idempotency_key);
CREATE INDEX IF NOT EXISTS idx_fin_events_created_at ON financial_events(created_at);

-- ========== 4. 创建 balance_snapshots 表 ==========
CREATE TABLE IF NOT EXISTS balance_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(20) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    snapshot_date DATE NOT NULL,

    -- 余额数据
    balance NUMERIC(18, 4) NOT NULL,
    total_debit NUMERIC(18, 4) NOT NULL DEFAULT 0,
    total_credit NUMERIC(18, 4) NOT NULL DEFAULT 0,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',

    -- 计算时间
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 约束
    CONSTRAINT chk_balance_snapshots_entity_type CHECK (
        entity_type IN ('SUPPLIER', 'PROJECT', 'ACCOUNT', 'TEAM')
    ),
    CONSTRAINT uq_balance_snapshots_entity_date UNIQUE (entity_type, entity_id, snapshot_date)
);

COMMENT ON COLUMN balance_snapshots.id IS '快照ID';
COMMENT ON COLUMN balance_snapshots.entity_type IS '实体类型';
COMMENT ON COLUMN balance_snapshots.entity_id IS '实体ID';
COMMENT ON COLUMN balance_snapshots.snapshot_date IS '快照日期';
COMMENT ON COLUMN balance_snapshots.balance IS '当前余额';
COMMENT ON COLUMN balance_snapshots.total_debit IS '累计借方';
COMMENT ON COLUMN balance_snapshots.total_credit IS '累计贷方';
COMMENT ON COLUMN balance_snapshots.currency IS '币种';
COMMENT ON COLUMN balance_snapshots.calculated_at IS '计算时间';

CREATE INDEX IF NOT EXISTS idx_balance_snapshots_entity ON balance_snapshots(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_balance_snapshots_date ON balance_snapshots(snapshot_date);

-- ========== 5. 扩展 suppliers 表 ==========
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS fee_rate NUMERIC(5, 4) DEFAULT 0.1000;
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS fee_type VARCHAR(20) DEFAULT 'PERCENTAGE';
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS platform VARCHAR(20);

COMMENT ON COLUMN suppliers.fee_rate IS '手续费率 (0.01-0.15)';
COMMENT ON COLUMN suppliers.fee_type IS '费率类型';
COMMENT ON COLUMN suppliers.platform IS '平台 (FB/TK/Google)';

-- 添加约束 (使用 DO 块来避免重复添加约束的错误)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_suppliers_fee_type'
    ) THEN
        ALTER TABLE suppliers ADD CONSTRAINT chk_suppliers_fee_type
            CHECK (fee_type IN ('PERCENTAGE', 'FIXED') OR fee_type IS NULL);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_suppliers_fee_rate_range'
    ) THEN
        ALTER TABLE suppliers ADD CONSTRAINT chk_suppliers_fee_rate_range
            CHECK ((fee_rate >= 0 AND fee_rate <= 1) OR fee_rate IS NULL);
    END IF;
END $$;

-- ========== 6. 扩展 ad_accounts 表 ==========
ALTER TABLE ad_accounts ADD COLUMN IF NOT EXISTS buyer_id UUID;
ALTER TABLE ad_accounts ADD COLUMN IF NOT EXISTS team_id UUID;
-- supplier_id already exists as UUID in ad_accounts
ALTER TABLE ad_accounts ADD COLUMN IF NOT EXISTS account_type VARCHAR(50);
ALTER TABLE ad_accounts ADD COLUMN IF NOT EXISTS platform VARCHAR(20);
ALTER TABLE ad_accounts ADD COLUMN IF NOT EXISTS region VARCHAR(50);

COMMENT ON COLUMN ad_accounts.buyer_id IS '投手ID';
COMMENT ON COLUMN ad_accounts.team_id IS '团队ID';
COMMENT ON COLUMN ad_accounts.supplier_id IS '供应商ID';
COMMENT ON COLUMN ad_accounts.account_type IS '账户类型 (美金户/越南盾户/企业户...)';
COMMENT ON COLUMN ad_accounts.platform IS '平台 (FB/TK/Google)';
COMMENT ON COLUMN ad_accounts.region IS '地区';

-- 添加外键 (使用 DO 块来避免重复)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_ad_accounts_buyer_id'
    ) THEN
        ALTER TABLE ad_accounts ADD CONSTRAINT fk_ad_accounts_buyer_id
            FOREIGN KEY (buyer_id) REFERENCES buyers(id) ON DELETE SET NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_ad_accounts_team_id'
    ) THEN
        ALTER TABLE ad_accounts ADD CONSTRAINT fk_ad_accounts_team_id
            FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL;
    END IF;
END $$;

-- supplier_id FK already exists in ad_accounts

CREATE INDEX IF NOT EXISTS idx_ad_accounts_buyer_id ON ad_accounts(buyer_id);
CREATE INDEX IF NOT EXISTS idx_ad_accounts_team_id ON ad_accounts(team_id);
-- idx_ad_accounts_supplier_id may already exist
CREATE INDEX IF NOT EXISTS idx_ad_accounts_platform ON ad_accounts(platform);

-- ========== 7. 扩展 ledger_entries 表 ==========
ALTER TABLE ledger_entries ADD COLUMN IF NOT EXISTS entity_type VARCHAR(20);
ALTER TABLE ledger_entries ADD COLUMN IF NOT EXISTS entity_id VARCHAR(100);
ALTER TABLE ledger_entries ADD COLUMN IF NOT EXISTS event_id UUID;
ALTER TABLE ledger_entries ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(255);
ALTER TABLE ledger_entries ADD COLUMN IF NOT EXISTS direction VARCHAR(10);

COMMENT ON COLUMN ledger_entries.entity_type IS '实体类型 (SUPPLIER/PROJECT/ACCOUNT/TEAM)';
COMMENT ON COLUMN ledger_entries.entity_id IS '实体ID';
COMMENT ON COLUMN ledger_entries.event_id IS '财务事件ID';
COMMENT ON COLUMN ledger_entries.idempotency_key IS '幂等键';
COMMENT ON COLUMN ledger_entries.direction IS '方向 (DEBIT/CREDIT)';

-- 添加外键
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_ledger_entries_event_id'
    ) THEN
        ALTER TABLE ledger_entries ADD CONSTRAINT fk_ledger_entries_event_id
            FOREIGN KEY (event_id) REFERENCES financial_events(id) ON DELETE SET NULL;
    END IF;
END $$;

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_ledger_entries_entity ON ledger_entries(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_event_id ON ledger_entries(event_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_ledger_entries_idempotency_key
    ON ledger_entries(idempotency_key) WHERE idempotency_key IS NOT NULL;

-- 添加约束
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_ledger_entries_entity_type'
    ) THEN
        ALTER TABLE ledger_entries ADD CONSTRAINT chk_ledger_entries_entity_type
            CHECK (entity_type IN ('SUPPLIER', 'PROJECT', 'ACCOUNT', 'TEAM') OR entity_type IS NULL);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_ledger_entries_direction'
    ) THEN
        ALTER TABLE ledger_entries ADD CONSTRAINT chk_ledger_entries_direction
            CHECK (direction IN ('DEBIT', 'CREDIT') OR direction IS NULL);
    END IF;
END $$;

-- ========== 8. 回填现有数据的 entity_type ==========
UPDATE ledger_entries
SET entity_type = 'ACCOUNT',
    entity_id = ad_account_id::varchar
WHERE entity_type IS NULL AND ad_account_id IS NOT NULL;

-- ========== 9. 插入初始团队数据 ==========
INSERT INTO teams (code, name, description) VALUES
('SZ', '深圳团队', '深圳运营团队'),
('ZZ', 'ZZ团队', 'ZZ运营团队')
ON CONFLICT (code) DO NOTHING;
