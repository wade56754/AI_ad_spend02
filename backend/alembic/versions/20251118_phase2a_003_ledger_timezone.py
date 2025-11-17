"""Phase 2A-003: ledger 模块时间字段 timezone 修复

Revision ID: phase2a_003
Revises: phase2a_002
Create Date: 2025-11-18

Description:
    修复 ledger_entries 表的时间字段，
    将 TIMESTAMP 类型升级为 TIMESTAMPTZ，符合 DATA_SCHEMA.md § 1.1 规范。

Tables affected:
    - ledger_entries: occurred_at

Migration Strategy:
    - ALTER COLUMN TYPE TIMESTAMPTZ USING ... AT TIME ZONE 'UTC'
    - 完全可逆
    - 数据风险：低（PostgreSQL 自动处理转换）

SoT References:
    - DATA_SCHEMA.md v5.0 § 1.1: "时间字段统一使用 TIMESTAMPTZ"
    - DATA_SCHEMA.md v5.0 § 3.4.4
    - PHASE2_MIGRATION_PLAN_APPEND.md § Rev 2A-003
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'phase2a_003'
down_revision = 'phase2a_002'
branch_labels = None
depends_on = None


def upgrade():
    """
    升级函数：将 ledger_entries 表时间字段升级为 TIMESTAMPTZ
    """

    # ========== 表: ledger_entries ==========
    print("[Phase 2A-003] 正在修复 ledger_entries 表...")

    # occurred_at: TIMESTAMP → TIMESTAMPTZ
    op.execute("""
        ALTER TABLE ledger_entries
        ALTER COLUMN occurred_at TYPE TIMESTAMPTZ
        USING occurred_at AT TIME ZONE 'UTC'
    """)

    print("  [OK] ledger_entries 表完成（1 个字段）")

    print("[Phase 2A-003] 迁移完成！共修复 1 个表，1 个字段")
    print("[Phase 2A-003] 请执行 Gate #2A-003 验证")


def downgrade():
    """
    降级函数：将时间字段回滚为 TIMESTAMP（无 timezone）
    """

    print("[Phase 2A-003 ROLLBACK] 正在回滚 ledger_entries 时间字段...")

    # ========== 表: ledger_entries ==========
    op.execute("""
        ALTER TABLE ledger_entries
        ALTER COLUMN occurred_at TYPE TIMESTAMP
        USING occurred_at
    """)

    print("[Phase 2A-003 ROLLBACK] 回滚完成")


# ========== Gate #2A-003: 验证脚本 ==========
"""
Gate #2A-003: 验证 ledger_entries 表时间字段类型

执行以下 SQL 验证迁移结果：

SELECT
    table_name,
    column_name,
    data_type,
    CASE
        WHEN data_type = 'timestamp with time zone' THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM information_schema.columns
WHERE table_name = 'ledger_entries'
AND column_name = 'occurred_at';

预期结果：
- ledger_entries.occurred_at: timestamp with time zone [PASS]

数据完整性验证：

SELECT
    COUNT(*) AS total_count,
    COUNT(occurred_at) AS occurred_at_count,
    MIN(occurred_at) AS earliest_time,
    MAX(occurred_at) AS latest_time
FROM ledger_entries;

预期结果：
- occurred_at_count = total_count（所有记录的时间字段有值）
- earliest_time 和 latest_time 在合理范围内（不早于 2020-01-01，不晚于当前时间）
"""
