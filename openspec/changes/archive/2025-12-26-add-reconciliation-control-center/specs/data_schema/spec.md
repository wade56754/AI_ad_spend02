# Spec Delta: Data Schema Extension

**Change-ID**: `add-reconciliation-control-center`
**Capability**: `data_schema`
**Affected SoT**: DATA_SCHEMA.md v5.2 → v5.3

---

## ADDED Requirements

### Requirement: balance_snapshots Table

系统 SHALL 维护广告账户的每日余额/押款快照表。

#### Scenario: Table structure
- **GIVEN** balance_snapshots 表
- **THEN** 包含以下字段:
  | 字段 | 类型 | 约束 | 说明 |
  |------|------|------|------|
  | id | UUID | PK, DEFAULT gen_random_uuid() | 主键 |
  | ad_account_id | UUID | FK → ad_accounts.id, NOT NULL | 关联账户 |
  | snapshot_date | DATE | NOT NULL | 快照日期 |
  | balance | DECIMAL(15,2) | NOT NULL | 当日余额 |
  | deposit | DECIMAL(15,2) | NOT NULL, DEFAULT 0 | 当日押款 |
  | remaining_balance | DECIMAL(15,2) | NOT NULL | 当日剩余可用 |
  | source | VARCHAR(20) | NOT NULL, DEFAULT 'manual' | 数据来源 |
  | created_by | UUID | FK → users.id, NOT NULL | 创建人 |
  | created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
  | notes | TEXT | | 备注 |
- **AND** UNIQUE 约束: (ad_account_id, snapshot_date)
- **AND** CHECK 约束: source IN ('manual', 'api', 'import')
- **AND** 索引: idx_balance_snapshots_date, idx_balance_snapshots_account

---

### Requirement: reconciliation_issues Table

系统 SHALL 维护对账差异单表。

#### Scenario: Table structure
- **GIVEN** reconciliation_issues 表
- **THEN** 包含以下字段:
  | 字段 | 类型 | 约束 | 说明 |
  |------|------|------|------|
  | id | UUID | PK, DEFAULT gen_random_uuid() | 主键 |
  | reconciliation_batch_id | UUID | FK → reconciliation_batches.id | 关联批次 |
  | ad_account_id | UUID | FK → ad_accounts.id | 关联账户 |
  | issue_date | DATE | NOT NULL | 差异日期 |
  | issue_type | VARCHAR(30) | NOT NULL, CHECK | 差异类型 |
  | expected_amount | DECIMAL(15,2) | | 预期金额 |
  | actual_amount | DECIMAL(15,2) | | 实际金额 |
  | difference_amount | DECIMAL(15,2) | GENERATED | 差异金额 |
  | status | VARCHAR(20) | NOT NULL, DEFAULT 'open' | 状态 |
  | assigned_to | UUID | FK → users.id | 责任人 |
  | assigned_at | TIMESTAMP WITH TIME ZONE | | 分配时间 |
  | resolution_type | VARCHAR(30) | CHECK | 处理类型 |
  | resolution_note | TEXT | | 处理说明 |
  | resolved_at | TIMESTAMP WITH TIME ZONE | | 处理时间 |
  | resolved_by | UUID | FK → users.id | 处理人 |
  | attachments | JSONB | DEFAULT '[]'::jsonb | 附件 |
  | created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
  | created_by | UUID | FK → users.id, NOT NULL | 创建人 |
  | updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |
  | sla_deadline | TIMESTAMP WITH TIME ZONE | | SLA 截止 |
  | sla_breached | BOOLEAN | DEFAULT FALSE | SLA 超时标记 |

#### Scenario: issue_type enum values
- **GIVEN** reconciliation_issues.issue_type 字段
- **THEN** CHECK 约束限定值:
  - 'topup_mismatch' - 充值差异
  - 'spend_mismatch' - 消耗差异
  - 'deposit_change' - 押款变化
  - 'balance_anomaly' - 余额异常
  - 'snapshot_missing' - 快照缺失
  - 'conservation_failed' - 守恒校验失败
  - 'other' - 其他

#### Scenario: status enum values
- **GIVEN** reconciliation_issues.status 字段
- **THEN** CHECK 约束限定值:
  - 'open' - 待处理（初始态）
  - 'assigned' - 已分配
  - 'investigating' - 调查中
  - 'resolved' - 已处理
  - 'closed' - 已关闭（终态）

#### Scenario: resolution_type enum values
- **GIVEN** reconciliation_issues.resolution_type 字段
- **THEN** CHECK 约束限定值:
  - 'data_correction' - 数据修正
  - 'ledger_adjustment' - 账本调整
  - 'external_confirm' - 外部确认
  - 'write_off' - 核销
  - 'false_positive' - 误报

---

### Requirement: settlement_rules Table

系统 SHALL 维护结算规则配置表。

#### Scenario: Table structure
- **GIVEN** settlement_rules 表
- **THEN** 包含以下字段:
  | 字段 | 类型 | 约束 | 说明 |
  |------|------|------|------|
  | id | UUID | PK, DEFAULT gen_random_uuid() | 主键 |
  | name | VARCHAR(100) | NOT NULL | 规则名称 |
  | rule_type | VARCHAR(20) | NOT NULL, CHECK | 规则类型 |
  | config | JSONB | NOT NULL | 规则配置 |
  | effective_from | DATE | NOT NULL | 生效开始日 |
  | effective_to | DATE | | 生效结束日 |
  | created_by | UUID | FK → users.id, NOT NULL | 创建人 |
  | created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 创建时间 |
  | updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 更新时间 |
- **AND** CHECK 约束: rule_type IN ('tiered', 'markup')
- **AND** CHECK 约束: effective_to IS NULL OR effective_to > effective_from

---

## MODIFIED Requirements

### Requirement: projects Table Extension

修改现有 projects 表，新增结算相关字段。

#### Scenario: New fields
- **GIVEN** projects 表
- **THEN** 新增字段:
  | 字段 | 类型 | 约束 | 说明 |
  |------|------|------|------|
  | settlement_type | VARCHAR(20) | DEFAULT 'fixed', CHECK | 结算类型 |
  | settlement_rules_id | UUID | FK → settlement_rules.id | 结算规则 |
- **AND** CHECK 约束: settlement_type IN ('fixed', 'tiered', 'markup')
- **AND** 现有项目 settlement_type 默认为 'fixed'

#### Scenario: Settlement type validation
- **GIVEN** 项目 settlement_type = 'tiered' 或 'markup'
- **WHEN** settlement_rules_id IS NULL
- **AND** 尝试计算收入
- **THEN** 返回错误 SET-004

---

### Requirement: ad_accounts Table Extension

修改现有 ad_accounts 表，新增押款相关字段。

#### Scenario: New fields
- **GIVEN** ad_accounts 表
- **THEN** 新增字段:
  | 字段 | 类型 | 约束 | 说明 |
  |------|------|------|------|
  | deposit | DECIMAL(15,2) | DEFAULT 0.00, CHECK (deposit >= 0) | 押款金额 |
  | deposit_updated_at | TIMESTAMP WITH TIME ZONE | | 押款更新时间 |
- **AND** 现有账户 deposit 默认为 0.00

---

## Migration Script Reference

```sql
-- Phase 1: Create new tables
CREATE TABLE settlement_rules ( ... );
CREATE TABLE balance_snapshots ( ... );
CREATE TABLE reconciliation_issues ( ... );

-- Phase 2: Alter existing tables
ALTER TABLE projects 
  ADD COLUMN settlement_type VARCHAR(20) DEFAULT 'fixed',
  ADD COLUMN settlement_rules_id UUID REFERENCES settlement_rules(id);

ALTER TABLE ad_accounts
  ADD COLUMN deposit DECIMAL(15,2) DEFAULT 0.00,
  ADD COLUMN deposit_updated_at TIMESTAMP WITH TIME ZONE;

-- Phase 3: Add constraints
ALTER TABLE projects
  ADD CONSTRAINT chk_projects_settlement_type 
  CHECK (settlement_type IN ('fixed', 'tiered', 'markup'));

ALTER TABLE ad_accounts
  ADD CONSTRAINT chk_ad_accounts_deposit 
  CHECK (deposit >= 0);

-- Phase 4: Create indexes
CREATE INDEX idx_balance_snapshots_date ON balance_snapshots(snapshot_date);
CREATE INDEX idx_balance_snapshots_account ON balance_snapshots(ad_account_id);
CREATE INDEX idx_rec_issues_status ON reconciliation_issues(status);
CREATE INDEX idx_rec_issues_date ON reconciliation_issues(issue_date);
CREATE INDEX idx_rec_issues_assigned ON reconciliation_issues(assigned_to) 
  WHERE assigned_to IS NOT NULL;
CREATE INDEX idx_rec_issues_batch ON reconciliation_issues(reconciliation_batch_id);
```

---

## Rollback Script Reference

```sql
-- Reverse order
DROP INDEX IF EXISTS idx_rec_issues_batch;
DROP INDEX IF EXISTS idx_rec_issues_assigned;
DROP INDEX IF EXISTS idx_rec_issues_date;
DROP INDEX IF EXISTS idx_rec_issues_status;
DROP INDEX IF EXISTS idx_balance_snapshots_account;
DROP INDEX IF EXISTS idx_balance_snapshots_date;

ALTER TABLE ad_accounts DROP COLUMN IF EXISTS deposit_updated_at;
ALTER TABLE ad_accounts DROP COLUMN IF EXISTS deposit;
ALTER TABLE projects DROP COLUMN IF EXISTS settlement_rules_id;
ALTER TABLE projects DROP COLUMN IF EXISTS settlement_type;

DROP TABLE IF EXISTS reconciliation_issues;
DROP TABLE IF EXISTS balance_snapshots;
DROP TABLE IF EXISTS settlement_rules;
```

---

**END OF SPEC**
