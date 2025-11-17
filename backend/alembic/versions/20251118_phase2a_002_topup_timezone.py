"""Phase 2A-002: topup 模块时间字段 timezone 修复

Revision ID: phase2a_002
Revises: phase2a_001
Create Date: 2025-11-18

Description:
    修复 topup_requests, topup_transactions, topup_approval_logs 表的时间字段，
    将 TIMESTAMP 类型升级为 TIMESTAMPTZ，符合 DATA_SCHEMA.md § 1.1 规范。

Tables affected:
    - topup_requests: created_at, updated_at
    - topup_transactions: paid_at, created_at
    - topup_approval_logs: created_at

Migration Strategy:
    - ALTER COLUMN TYPE TIMESTAMPTZ USING ... AT TIME ZONE 'UTC'
    - 完全可逆
    - 数据风险：低（PostgreSQL 自动处理转换）

SoT References:
    - DATA_SCHEMA.md v5.0 § 1.1: "时间字段统一使用 TIMESTAMPTZ"
    - DATA_SCHEMA.md v5.0 § 3.4.1, 3.4.2, 3.4.3
    - PHASE2_MIGRATION_PLAN_APPEND.md § Rev 2A-002
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'phase2a_002'
down_revision = 'phase2a_001'
branch_labels = None
depends_on = None


def upgrade():
    """
    升级函数：将 topup 模块时间字段升级为 TIMESTAMPTZ
    """

    # ========== 表 1: topup_requests ==========
    print("[Phase 2A-002] 正在修复 topup_requests 表...")

    # created_at: TIMESTAMP → TIMESTAMPTZ
    op.execute("""
        ALTER TABLE topup_requests
        ALTER COLUMN created_at TYPE TIMESTAMPTZ
        USING created_at AT TIME ZONE 'UTC'
    """)

    # updated_at: TIMESTAMP → TIMESTAMPTZ
    op.execute("""
        ALTER TABLE topup_requests
        ALTER COLUMN updated_at TYPE TIMESTAMPTZ
        USING updated_at AT TIME ZONE 'UTC'
    """)

    print("  [OK] topup_requests 表完成（2 个字段）")

    # ========== 表 2: topup_transactions ==========
    print("[Phase 2A-002] 正在修复 topup_transactions 表...")

    # paid_at: TIMESTAMP → TIMESTAMPTZ
    op.execute("""
        ALTER TABLE topup_transactions
        ALTER COLUMN paid_at TYPE TIMESTAMPTZ
        USING paid_at AT TIME ZONE 'UTC'
    """)

    # created_at: TIMESTAMP → TIMESTAMPTZ
    op.execute("""
        ALTER TABLE topup_transactions
        ALTER COLUMN created_at TYPE TIMESTAMPTZ
        USING created_at AT TIME ZONE 'UTC'
    """)

    print("  [OK] topup_transactions 表完成（2 个字段）")

    # ========== 表 3: topup_approval_logs ==========
    print("[Phase 2A-002] 正在修复 topup_approval_logs 表...")

    # created_at: TIMESTAMP → TIMESTAMPTZ
    op.execute("""
        ALTER TABLE topup_approval_logs
        ALTER COLUMN created_at TYPE TIMESTAMPTZ
        USING created_at AT TIME ZONE 'UTC'
    """)

    print("  [OK] topup_approval_logs 表完成（1 个字段）")

    print("[Phase 2A-002] 迁移完成！共修复 3 个表，5 个字段")
    print("[Phase 2A-002] 请执行 Gate #2A-002 验证")


def downgrade():
    """
    降级函数：将时间字段回滚为 TIMESTAMP（无 timezone）
    """

    print("[Phase 2A-002 ROLLBACK] 正在回滚 topup 模块时间字段...")

    # ========== 表 3: topup_approval_logs（逆序回滚）==========
    print("  [ROLLBACK] topup_approval_logs 表...")

    op.execute("""
        ALTER TABLE topup_approval_logs
        ALTER COLUMN created_at TYPE TIMESTAMP
        USING created_at
    """)

    # ========== 表 2: topup_transactions ==========
    print("  [ROLLBACK] topup_transactions 表...")

    op.execute("""
        ALTER TABLE topup_transactions
        ALTER COLUMN created_at TYPE TIMESTAMP
        USING created_at
    """)

    op.execute("""
        ALTER TABLE topup_transactions
        ALTER COLUMN paid_at TYPE TIMESTAMP
        USING paid_at
    """)

    # ========== 表 1: topup_requests ==========
    print("  [ROLLBACK] topup_requests 表...")

    op.execute("""
        ALTER TABLE topup_requests
        ALTER COLUMN updated_at TYPE TIMESTAMP
        USING updated_at
    """)

    op.execute("""
        ALTER TABLE topup_requests
        ALTER COLUMN created_at TYPE TIMESTAMP
        USING created_at
    """)

    print("[Phase 2A-002 ROLLBACK] 回滚完成")


# ========== Gate #2A-002: 验证脚本 ==========
"""
Gate #2A-002: 验证 topup 模块时间字段类型

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
WHERE table_name IN ('topup_requests', 'topup_transactions', 'topup_approval_logs')
AND column_name IN ('created_at', 'updated_at', 'paid_at')
ORDER BY table_name, column_name;

预期结果：
- topup_approval_logs.created_at: timestamp with time zone [PASS]
- topup_requests.created_at: timestamp with time zone [PASS]
- topup_requests.updated_at: timestamp with time zone [PASS]
- topup_transactions.created_at: timestamp with time zone [PASS]
- topup_transactions.paid_at: timestamp with time zone [PASS]

数据完整性验证：

SELECT
    'topup_requests' AS table_name,
    COUNT(*) AS total_count,
    COUNT(created_at) AS created_at_count,
    COUNT(updated_at) AS updated_at_count
FROM topup_requests;

SELECT
    'topup_transactions' AS table_name,
    COUNT(*) AS total_count,
    COUNT(paid_at) AS paid_at_count,
    COUNT(created_at) AS created_at_count
FROM topup_transactions;

SELECT
    'topup_approval_logs' AS table_name,
    COUNT(*) AS total_count,
    COUNT(created_at) AS created_at_count
FROM topup_approval_logs;

预期结果：所有 count 字段数量与 total_count 一致
"""
