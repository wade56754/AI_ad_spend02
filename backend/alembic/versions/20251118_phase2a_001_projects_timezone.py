"""Phase 2A-001: projects 模块时间字段 timezone 修复

Revision ID: phase2a_001
Revises:
Create Date: 2025-11-18

Description:
    修复 projects, project_members, project_expenses 表的时间字段，
    将 TIMESTAMP 类型升级为 TIMESTAMPTZ，符合 DATA_SCHEMA.md § 1.1 规范。

Tables affected:
    - projects: created_at, updated_at
    - project_members: joined_at
    - project_expenses: occurred_at, created_at

Migration Strategy:
    - ALTER COLUMN TYPE TIMESTAMPTZ USING ... AT TIME ZONE 'UTC'
    - 完全可逆
    - 数据风险：低（PostgreSQL 自动处理转换）

SoT References:
    - DATA_SCHEMA.md v5.0 § 1.1: "时间字段统一使用 TIMESTAMPTZ"
    - PHASE2_MIGRATION_PLAN_APPEND.md § Rev 2A-001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'phase2a_001'
down_revision = None  # 根据实际情况填写前一个 revision
branch_labels = None
depends_on = None


def upgrade():
    """
    升级函数：将 projects 模块时间字段升级为 TIMESTAMPTZ
    """

    # ========== 表 1: projects ==========
    print("[Phase 2A-001] 正在修复 projects 表...")

    # created_at: TIMESTAMP → TIMESTAMPTZ
    op.execute("""
        ALTER TABLE projects
        ALTER COLUMN created_at TYPE TIMESTAMPTZ
        USING created_at AT TIME ZONE 'UTC'
    """)

    # updated_at: TIMESTAMP → TIMESTAMPTZ
    op.execute("""
        ALTER TABLE projects
        ALTER COLUMN updated_at TYPE TIMESTAMPTZ
        USING updated_at AT TIME ZONE 'UTC'
    """)

    print("  [OK] projects 表完成（2 个字段）")

    # ========== 表 2: project_members ==========
    print("[Phase 2A-001] 正在修复 project_members 表...")

    # joined_at: TIMESTAMP → TIMESTAMPTZ
    op.execute("""
        ALTER TABLE project_members
        ALTER COLUMN joined_at TYPE TIMESTAMPTZ
        USING joined_at AT TIME ZONE 'UTC'
    """)

    print("  [OK] project_members 表完成（1 个字段）")

    # ========== 表 3: project_expenses ==========
    print("[Phase 2A-001] 正在修复 project_expenses 表...")

    # occurred_at: TIMESTAMP → TIMESTAMPTZ
    op.execute("""
        ALTER TABLE project_expenses
        ALTER COLUMN occurred_at TYPE TIMESTAMPTZ
        USING occurred_at AT TIME ZONE 'UTC'
    """)

    # created_at: TIMESTAMP → TIMESTAMPTZ
    op.execute("""
        ALTER TABLE project_expenses
        ALTER COLUMN created_at TYPE TIMESTAMPTZ
        USING created_at AT TIME ZONE 'UTC'
    """)

    print("  [OK] project_expenses 表完成（2 个字段）")

    print("[Phase 2A-001] 迁移完成！共修复 3 个表，5 个字段")
    print("[Phase 2A-001] 请执行 Gate #2A-001 验证")


def downgrade():
    """
    降级函数：将时间字段回滚为 TIMESTAMP（无 timezone）
    """

    print("[Phase 2A-001 ROLLBACK] 正在回滚 projects 模块时间字段...")

    # ========== 表 3: project_expenses（逆序回滚）==========
    print("  [ROLLBACK] project_expenses 表...")

    op.execute("""
        ALTER TABLE project_expenses
        ALTER COLUMN created_at TYPE TIMESTAMP
        USING created_at
    """)

    op.execute("""
        ALTER TABLE project_expenses
        ALTER COLUMN occurred_at TYPE TIMESTAMP
        USING occurred_at
    """)

    # ========== 表 2: project_members ==========
    print("  [ROLLBACK] project_members 表...")

    op.execute("""
        ALTER TABLE project_members
        ALTER COLUMN joined_at TYPE TIMESTAMP
        USING joined_at
    """)

    # ========== 表 1: projects ==========
    print("  [ROLLBACK] projects 表...")

    op.execute("""
        ALTER TABLE projects
        ALTER COLUMN updated_at TYPE TIMESTAMP
        USING updated_at
    """)

    op.execute("""
        ALTER TABLE projects
        ALTER COLUMN created_at TYPE TIMESTAMP
        USING created_at
    """)

    print("[Phase 2A-001 ROLLBACK] 回滚完成")


# ========== Gate #2A-001: 验证脚本 ==========
"""
Gate #2A-001: 验证 projects 模块时间字段类型

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
WHERE table_name IN ('projects', 'project_members', 'project_expenses')
AND column_name IN ('created_at', 'updated_at', 'occurred_at', 'joined_at')
ORDER BY table_name, column_name;

预期结果：
- projects.created_at: timestamp with time zone [PASS]
- projects.updated_at: timestamp with time zone [PASS]
- project_members.joined_at: timestamp with time zone [PASS]
- project_expenses.created_at: timestamp with time zone [PASS]
- project_expenses.occurred_at: timestamp with time zone [PASS]

数据完整性验证：

SELECT
    'projects' AS table_name,
    COUNT(*) AS total_count,
    COUNT(created_at) AS created_at_count,
    COUNT(updated_at) AS updated_at_count
FROM projects;

SELECT
    'project_members' AS table_name,
    COUNT(*) AS total_count,
    COUNT(joined_at) AS joined_at_count
FROM project_members;

SELECT
    'project_expenses' AS table_name,
    COUNT(*) AS total_count,
    COUNT(occurred_at) AS occurred_at_count,
    COUNT(created_at) AS created_at_count
FROM project_expenses;

预期结果：所有 count 字段数量与 total_count 一致（除非字段定义允许 NULL）
"""
