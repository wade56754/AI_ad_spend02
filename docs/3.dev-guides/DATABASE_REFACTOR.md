# DATABASE_REFACTOR.md - 数据库重构方案

> **文档性质**: 数据库重构规划与实施指南
> **版本**: v1.0
> **status**: draft
> **基准**: CORE_MODULES.md v1.0, DATA_SCHEMA.md v5.2, PROJECT.md v1.3
> **owner**: wade
> **created**: 2025-12-22

---

## 第一章 重构概述

### 1.1 重构背景

基于 CORE_MODULES.md v1.0 定义的 4 大核心模块，现有数据库结构存在以下差异需要对齐：

| 模块 | CORE_MODULES 定义 | 现有 DATA_SCHEMA 状态 | 差异程度 |
|------|------------------|---------------------|---------|
| 投手管理 | pitchers 表 | 无独立表 (users.role) | **高** |
| 财务管理 | ledger + period_locks | 部分实现 | **中** |
| 账号管理 | account_ownership_history | 无历史表 | **中** |
| 项目管理 | clients + projects | 部分实现 | **低** |

### 1.2 重构目标

1. **投手管理**: 新增 `pitchers` 表，独立管理投手团队信息
2. **财务管理**: 新增 `period_locks` 表，完善期间锁机制
3. **账号管理**: 新增 `account_ownership_history` 表，记录账户归属历史
4. **项目管理**: 新增 `clients` 表，分离甲方与项目关系

### 1.3 重构原则

- **向后兼容**: 现有 API 不变，新增字段有默认值
- **渐进式迁移**: 分阶段实施，每阶段可独立回滚
- **数据不丢失**: 历史数据通过脚本迁移，保留审计链
- **SoT 对齐**: 所有变更同步更新 DATA_SCHEMA.md

---

## 第二章 新增表结构

### 2.1 pitchers 表 (投手信息)

**来源**: CORE_MODULES.md §1.3

```sql
CREATE TABLE pitchers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,              -- 投手名称(工号)
    real_name VARCHAR(50),                   -- 真实姓名
    team VARCHAR(30) NOT NULL,               -- 团队: 郑州/金边/深圳/外包
    type VARCHAR(20) NOT NULL DEFAULT 'internal', -- internal/outsource
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active/inactive
    join_date DATE,                          -- 入职日期
    user_id UUID REFERENCES users(id),       -- 关联用户ID
    supervisor_id INTEGER REFERENCES pitchers(id), -- 主管投手
    performance_score DECIMAL(5,2),          -- 绩效评分
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT chk_pitchers_team CHECK (team IN ('郑州', '金边', '深圳', '外包')),
    CONSTRAINT chk_pitchers_type CHECK (type IN ('internal', 'outsource')),
    CONSTRAINT chk_pitchers_status CHECK (status IN ('active', 'inactive'))
);

CREATE INDEX idx_pitchers_team ON pitchers(team);
CREATE INDEX idx_pitchers_status ON pitchers(status);
CREATE INDEX idx_pitchers_user ON pitchers(user_id);
```

**关联变更**:
- `daily_reports` 新增 `pitcher_id` 字段
- 从 `users` 表迁移投手信息

### 2.2 clients 表 (甲方信息)

**来源**: CORE_MODULES.md §4.3

```sql
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,              -- 甲方名称
    short_name VARCHAR(50),                  -- 简称
    contact_name VARCHAR(50),                -- 联系人
    contact_phone VARCHAR(20),               -- 联系电话
    contact_email VARCHAR(100),              -- 联系邮箱
    contact_info JSONB DEFAULT '{}',         -- 扩展联系方式
    payment_terms VARCHAR(200),              -- 付款条款
    credit_limit DECIMAL(15,2) DEFAULT 0,    -- 信用额度
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active/inactive/suspended
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id),

    CONSTRAINT chk_clients_status CHECK (status IN ('active', 'inactive', 'suspended'))
);

CREATE INDEX idx_clients_name ON clients(name);
CREATE INDEX idx_clients_status ON clients(status);
```

**关联变更**:
- `projects` 新增 `client_id` 字段，替代 `client_name`/`client_company`

### 2.3 agencies 表 (代理商信息)

**来源**: CORE_MODULES.md §3.3

```sql
CREATE TABLE agencies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,              -- 代理商名称
    short_name VARCHAR(50),                  -- 简称
    platform VARCHAR(20) NOT NULL,           -- FB/TK/Google
    fee_rate DECIMAL(5,4) NOT NULL DEFAULT 0.0800, -- 默认手续费率 8%
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    contact_info JSONB DEFAULT '{}',         -- 联系方式
    bank_info JSONB DEFAULT '{}',            -- 收款信息
    settlement_cycle VARCHAR(20) DEFAULT 'monthly', -- 结算周期
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT chk_agencies_platform CHECK (platform IN ('FB', 'TK', 'Google', 'Other')),
    CONSTRAINT chk_agencies_status CHECK (status IN ('active', 'inactive', 'suspended'))
);

CREATE INDEX idx_agencies_platform ON agencies(platform);
CREATE INDEX idx_agencies_status ON agencies(status);
```

**关联变更**:
- `ad_accounts` 新增 `agency_id` 字段

### 2.4 account_ownership_history 表 (账户归属历史)

**来源**: CORE_MODULES.md §3.3

```sql
CREATE TABLE account_ownership_history (
    id SERIAL PRIMARY KEY,
    account_id BIGINT NOT NULL REFERENCES ad_accounts(id),
    pitcher_id INTEGER NOT NULL REFERENCES pitchers(id),
    project_id BIGINT REFERENCES projects(id),
    region VARCHAR(50),                      -- 地区
    effective_from DATE NOT NULL,            -- 生效开始日期
    effective_to DATE,                       -- 生效结束日期 (NULL=当前)
    change_type VARCHAR(20) NOT NULL,        -- ASSIGN/TRANSFER/RECALL
    change_reason TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT chk_ownership_change_type CHECK (change_type IN ('ASSIGN', 'TRANSFER', 'RECALL'))
);

CREATE INDEX idx_ownership_account ON account_ownership_history(account_id);
CREATE INDEX idx_ownership_pitcher ON account_ownership_history(pitcher_id);
CREATE INDEX idx_ownership_project ON account_ownership_history(project_id);
CREATE INDEX idx_ownership_effective ON account_ownership_history(effective_from, effective_to);
```

**归因查询函数**:
```sql
CREATE OR REPLACE FUNCTION get_account_attribution(
    p_account_id BIGINT,
    p_date DATE
) RETURNS TABLE (
    pitcher_id INTEGER,
    project_id BIGINT,
    region VARCHAR(50)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        aoh.pitcher_id,
        aoh.project_id,
        aoh.region
    FROM account_ownership_history aoh
    WHERE aoh.account_id = p_account_id
      AND aoh.effective_from <= p_date
      AND (aoh.effective_to IS NULL OR aoh.effective_to >= p_date)
    ORDER BY aoh.effective_from DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;
```

### 2.5 period_locks 表 (期间锁)

**来源**: CORE_MODULES.md §2.7

```sql
CREATE TABLE period_locks (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(30) NOT NULL,        -- ledger/daily_report
    period_start DATE NOT NULL,              -- 期间开始
    period_end DATE NOT NULL,                -- 期间结束
    lock_status VARCHAR(20) NOT NULL DEFAULT 'UNLOCKED', -- UNLOCKED/LOCKED/FROZEN
    locked_by UUID REFERENCES users(id),
    locked_at TIMESTAMPTZ,
    unlock_reason TEXT,                      -- 解锁原因(特批)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT chk_period_locks_entity CHECK (entity_type IN ('ledger', 'daily_report')),
    CONSTRAINT chk_period_locks_status CHECK (lock_status IN ('UNLOCKED', 'LOCKED', 'FROZEN')),
    CONSTRAINT chk_period_dates CHECK (period_end >= period_start)
);

CREATE UNIQUE INDEX idx_period_locks_unique ON period_locks(entity_type, period_start, period_end);
CREATE INDEX idx_period_locks_status ON period_locks(lock_status);
```

**期间锁检查函数**:
```sql
CREATE OR REPLACE FUNCTION is_period_locked(
    p_entity_type VARCHAR(30),
    p_date DATE
) RETURNS BOOLEAN AS $$
DECLARE
    v_locked BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1 FROM period_locks
        WHERE entity_type = p_entity_type
          AND lock_status IN ('LOCKED', 'FROZEN')
          AND period_start <= p_date
          AND period_end >= p_date
    ) INTO v_locked;

    RETURN v_locked;
END;
$$ LANGUAGE plpgsql;
```

---

## 第三章 现有表变更

### 3.1 daily_reports 表变更

**新增字段**:

```sql
ALTER TABLE daily_reports
ADD COLUMN pitcher_id INTEGER REFERENCES pitchers(id),
ADD COLUMN region VARCHAR(50),
ADD COLUMN platform VARCHAR(20);

-- 添加约束
ALTER TABLE daily_reports
ADD CONSTRAINT chk_daily_reports_platform CHECK (
    platform IN ('FB', 'TK', 'Google', 'Other')
);

-- 创建幂等键索引
CREATE UNIQUE INDEX idx_daily_reports_idempotent
ON daily_reports(report_date, pitcher_id, region, platform)
WHERE pitcher_id IS NOT NULL;
```

**字段对照表**:

| CORE_MODULES 字段 | DATA_SCHEMA 字段 | 状态 | 变更 |
|------------------|-----------------|------|------|
| pitcher_id | 无 | **新增** | 关联 pitchers 表 |
| region | 无 | **新增** | 投放地区 |
| platform | 无 | **新增** | 广告平台 |
| reported_spend | raw_spend | **已有** | 字段名保持 |
| reported_results | conversions_raw | **已有** | 字段名保持 |
| confirmed_spend | real_spend | **已有** | 字段名保持 |
| confirmed_leads | conversions_final | **已有** | 字段名保持 |

### 3.2 projects 表变更

**新增字段**:

```sql
ALTER TABLE projects
ADD COLUMN client_id INTEGER REFERENCES clients(id),
ADD COLUMN region VARCHAR(50),
ADD COLUMN platform VARCHAR(20),
ADD COLUMN price_rules JSONB DEFAULT '{}',
ADD COLUMN start_date DATE,
ADD COLUMN end_date DATE;

-- 迁移现有数据
UPDATE projects p
SET client_id = c.id
FROM clients c
WHERE c.name = p.client_name;

-- 添加约束 (迁移完成后)
-- ALTER TABLE projects ALTER COLUMN client_id SET NOT NULL;
```

**阶梯价格规则 (price_rules) 结构**:

```json
{
    "type": "tiered",
    "tiers": [
        {"min": 0, "max": 1000, "price": 50},
        {"min": 1001, "max": 5000, "price": 45},
        {"min": 5001, "max": null, "price": 40}
    ]
}
```

### 3.3 ad_accounts 表变更

**新增字段**:

```sql
ALTER TABLE ad_accounts
ADD COLUMN agency_id INTEGER REFERENCES agencies(id),
ADD COLUMN account_type VARCHAR(50),
ADD COLUMN fee_rate DECIMAL(5,4),
ADD COLUMN current_pitcher_id INTEGER REFERENCES pitchers(id);

-- 添加约束
ALTER TABLE ad_accounts
ADD CONSTRAINT chk_ad_accounts_type CHECK (
    account_type IN ('二不限', '美金户', '绑卡户', 'Other')
);
```

### 3.4 ledger 表变更 (重命名字段)

**字段对照**:

| CORE_MODULES 字段 | 现有字段 | 变更 |
|------------------|---------|------|
| txn_id | 无 | **新增** 幂等键 |
| txn_type | entry_type | **保留** 使用 entry_type |
| txn_status | 无 | **新增** 交易状态 |
| agency_id | 无 | **新增** 代理商ID |
| pitcher_id | 无 | **新增** 投手ID |
| is_reversal | 无 | **新增** 冲正标记 |
| reversal_of | reference_id | **使用现有** |
| business_date | occurred_at | **保留** 使用 occurred_at |

```sql
ALTER TABLE ledger_entries
ADD COLUMN txn_id VARCHAR(64) UNIQUE,
ADD COLUMN txn_status VARCHAR(20) DEFAULT 'PENDING',
ADD COLUMN agency_id INTEGER REFERENCES agencies(id),
ADD COLUMN pitcher_id INTEGER REFERENCES pitchers(id),
ADD COLUMN is_reversal BOOLEAN DEFAULT FALSE,
ADD COLUMN fx_rate DECIMAL(12,6),
ADD COLUMN fx_status VARCHAR(20) DEFAULT 'PENDING';

-- 添加约束
ALTER TABLE ledger_entries
ADD CONSTRAINT chk_ledger_txn_status CHECK (
    txn_status IN ('PENDING', 'APPROVED', 'EXECUTED', 'CONFIRMED')
),
ADD CONSTRAINT chk_ledger_fx_status CHECK (
    fx_status IN ('PENDING', 'LOCKED', 'ADJUSTED')
);
```

---

## 第四章 迁移策略

### 4.1 迁移阶段

| 阶段 | 内容 | 依赖 | 风险等级 |
|------|------|------|---------|
| Phase 1 | 新增基础表 (pitchers, clients, agencies) | 无 | **低** |
| Phase 2 | 新增关联表 (account_ownership_history, period_locks) | Phase 1 | **低** |
| Phase 3 | 现有表新增字段 | Phase 1, 2 | **中** |
| Phase 4 | 数据迁移脚本 | Phase 3 | **中** |
| Phase 5 | 业务逻辑切换 | Phase 4 | **高** |

### 4.2 Phase 1: 新增基础表

```bash
# 1. 创建迁移文件
alembic revision -m "add_pitchers_clients_agencies_tables"

# 2. 执行迁移
alembic upgrade head

# 3. 验证表结构
python -c "from backend.models import *; print('OK')"
```

**迁移脚本 (Alembic)**:

```python
# backend/alembic/versions/20251222_add_core_module_tables.py

def upgrade():
    # 1. pitchers 表
    op.create_table('pitchers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('real_name', sa.String(50), nullable=True),
        sa.Column('team', sa.String(30), nullable=False),
        sa.Column('type', sa.String(20), nullable=False, server_default='internal'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('join_date', sa.Date(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('supervisor_id', sa.Integer(), nullable=True),
        sa.Column('performance_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['supervisor_id'], ['pitchers.id']),
        sa.CheckConstraint("team IN ('郑州', '金边', '深圳', '外包')", name='chk_pitchers_team'),
        sa.CheckConstraint("type IN ('internal', 'outsource')", name='chk_pitchers_type'),
        sa.CheckConstraint("status IN ('active', 'inactive')", name='chk_pitchers_status')
    )
    op.create_index('idx_pitchers_team', 'pitchers', ['team'])
    op.create_index('idx_pitchers_status', 'pitchers', ['status'])
    op.create_index('idx_pitchers_user', 'pitchers', ['user_id'])

    # 2. clients 表
    op.create_table('clients', ...)

    # 3. agencies 表
    op.create_table('agencies', ...)

def downgrade():
    op.drop_table('agencies')
    op.drop_table('clients')
    op.drop_table('pitchers')
```

### 4.3 Phase 4: 数据迁移脚本

```python
# scripts/migrate_core_modules_data.py
"""
核心模块数据迁移脚本
基于: CORE_MODULES.md v1.0
"""

from sqlalchemy import create_engine, text
from datetime import date

def migrate_pitchers():
    """从 users 表迁移投手数据到 pitchers 表"""

    # 查询现有投手用户
    sql = """
    INSERT INTO pitchers (name, real_name, team, type, status, user_id, created_at)
    SELECT
        u.username as name,
        u.full_name as real_name,
        COALESCE(u.department, '郑州') as team,
        'internal' as type,
        CASE WHEN u.is_active THEN 'active' ELSE 'inactive' END as status,
        u.id as user_id,
        u.created_at
    FROM users u
    WHERE u.role = 'media_buyer'
    ON CONFLICT DO NOTHING;
    """

    engine.execute(text(sql))
    print("✓ 投手数据迁移完成")

def migrate_clients():
    """从 projects 表提取甲方数据"""

    sql = """
    INSERT INTO clients (name, short_name, status, created_at)
    SELECT DISTINCT
        p.client_name as name,
        p.client_company as short_name,
        'active' as status,
        MIN(p.created_at) as created_at
    FROM projects p
    WHERE p.client_name IS NOT NULL
    GROUP BY p.client_name, p.client_company
    ON CONFLICT DO NOTHING;
    """

    engine.execute(text(sql))
    print("✓ 甲方数据迁移完成")

def migrate_project_client_links():
    """关联 projects 和 clients"""

    sql = """
    UPDATE projects p
    SET client_id = c.id
    FROM clients c
    WHERE c.name = p.client_name;
    """

    engine.execute(text(sql))
    print("✓ 项目-甲方关联完成")

def migrate_account_ownership():
    """从现有账户创建初始归属记录"""

    sql = """
    INSERT INTO account_ownership_history
        (account_id, pitcher_id, project_id, effective_from, change_type)
    SELECT
        a.id as account_id,
        p.id as pitcher_id,
        a.project_id,
        a.created_at::date as effective_from,
        'ASSIGN' as change_type
    FROM ad_accounts a
    JOIN pitchers p ON p.user_id = a.owner_id
    WHERE a.owner_id IS NOT NULL;
    """

    engine.execute(text(sql))
    print("✓ 账户归属历史初始化完成")

if __name__ == '__main__':
    migrate_pitchers()
    migrate_clients()
    migrate_project_client_links()
    migrate_account_ownership()
    print("✅ 数据迁移全部完成")
```

---

## 第五章 验证计划

### 5.1 数据完整性验证

```sql
-- 1. 验证投手数据
SELECT
    (SELECT COUNT(*) FROM users WHERE role = 'media_buyer') as users_count,
    (SELECT COUNT(*) FROM pitchers) as pitchers_count;

-- 2. 验证甲方数据
SELECT
    (SELECT COUNT(DISTINCT client_name) FROM projects WHERE client_name IS NOT NULL) as project_clients,
    (SELECT COUNT(*) FROM clients) as clients_count;

-- 3. 验证账户归属
SELECT
    (SELECT COUNT(*) FROM ad_accounts WHERE owner_id IS NOT NULL) as accounts_with_owner,
    (SELECT COUNT(DISTINCT account_id) FROM account_ownership_history) as history_accounts;
```

### 5.2 业务规则验证

```python
# tests/integration/test_migration.py

def test_pitcher_attribution():
    """验证投手归因功能"""
    # 创建测试数据
    account = create_test_account()
    pitcher = create_test_pitcher()

    # 分配账户
    assign_account_to_pitcher(account.id, pitcher.id, date.today())

    # 验证归因
    attribution = get_account_attribution(account.id, date.today())
    assert attribution.pitcher_id == pitcher.id

def test_period_lock():
    """验证期间锁功能"""
    # 锁定上月
    lock_period('ledger', date(2025, 11, 1), date(2025, 11, 30))

    # 验证锁定状态
    assert is_period_locked('ledger', date(2025, 11, 15)) == True
    assert is_period_locked('ledger', date(2025, 12, 1)) == False
```

---

## 第六章 回滚方案

### 6.1 Phase 级回滚

```bash
# 回滚 Phase 3 (现有表变更)
alembic downgrade -1

# 回滚 Phase 2 (关联表)
alembic downgrade -1

# 回滚 Phase 1 (基础表)
alembic downgrade -1
```

### 6.2 紧急回滚脚本

```sql
-- 紧急回滚: 恢复到迁移前状态

-- 1. 删除新增外键约束
ALTER TABLE daily_reports DROP CONSTRAINT IF EXISTS daily_reports_pitcher_id_fkey;
ALTER TABLE projects DROP CONSTRAINT IF EXISTS projects_client_id_fkey;
ALTER TABLE ad_accounts DROP CONSTRAINT IF EXISTS ad_accounts_agency_id_fkey;

-- 2. 删除新增字段
ALTER TABLE daily_reports DROP COLUMN IF EXISTS pitcher_id;
ALTER TABLE daily_reports DROP COLUMN IF EXISTS region;
ALTER TABLE daily_reports DROP COLUMN IF EXISTS platform;
ALTER TABLE projects DROP COLUMN IF EXISTS client_id;
ALTER TABLE projects DROP COLUMN IF EXISTS price_rules;
ALTER TABLE ad_accounts DROP COLUMN IF EXISTS agency_id;

-- 3. 删除新表 (按依赖顺序)
DROP TABLE IF EXISTS account_ownership_history CASCADE;
DROP TABLE IF EXISTS period_locks CASCADE;
DROP TABLE IF EXISTS agencies CASCADE;
DROP TABLE IF EXISTS clients CASCADE;
DROP TABLE IF EXISTS pitchers CASCADE;

-- 4. 删除函数
DROP FUNCTION IF EXISTS get_account_attribution;
DROP FUNCTION IF EXISTS is_period_locked;
```

---

## 第七章 6 角色权限对照

### 7.1 新表权限矩阵

| 表 | pitcher | account_manager | supervisor | finance | ceo | admin |
|----|---------|-----------------|------------|---------|-----|-------|
| pitchers | R (自己) | R | RW | R | R | CRUD |
| clients | - | R | R | R | R | CRUD |
| agencies | - | R | R | R | R | CRUD |
| account_ownership_history | R | CRUD | R | R | R | CRUD |
| period_locks | - | - | - | CRU | R | CRUD |

### 7.2 Service 层权限检查

```python
# backend/services/pitcher_service.py

from backend.core.auth import require_roles

class PitcherService:

    @require_roles(['admin'])
    def create_pitcher(self, data: PitcherCreate) -> Pitcher:
        """创建投手 - 仅 admin"""
        pass

    @require_roles(['admin', 'supervisor', 'account_manager'])
    def list_pitchers(self, filters: PitcherFilter) -> List[Pitcher]:
        """查询投手列表"""
        pass

    @require_roles(['admin', 'supervisor'])
    def update_pitcher(self, pitcher_id: int, data: PitcherUpdate) -> Pitcher:
        """更新投手信息"""
        pass
```

---

## 附录 A: SoT 同步清单

迁移完成后需同步更新以下文档:

| 文档 | 更新内容 |
|------|---------|
| DATA_SCHEMA.md | 新增 5 张表定义，更新 3 张表字段 |
| STATE_MACHINE.md | 无变更 |
| BUSINESS_RULES.md | 新增 BR-ACC-003/004 归因规则 |
| API_SOT.md | 新增 /pitchers, /clients, /agencies 端点 |
| CORE_MODULES.md | 标记为 implemented |

---

## 附录 B: 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2025-12-22 | 初始版本，基于 CORE_MODULES.md v1.0 | AI Code Factory |

---

**文档版本**: v1.0
**创建日期**: 2025-12-22
**基准文档**: CORE_MODULES.md v1.0, DATA_SCHEMA.md v5.2
**维护者**: 系统架构师
