"""P0-006: 修复 reconciliation_batches CHECK 约束名称

Revision ID: 20251120_fix_reconciliation_batch_constraint_p0
Revises: 20251120_add_version_fields_p0
Create Date: 2025-11-20

根据 STATE_MACHINE.md v2.5 第15.2.5章：
- 标准约束名：chk_reconciliation_batches_status  - 现有约束名：check_batch_status（不规范）
- 需要重命名以符合命名规范
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '20251120_fix_reconciliation_batch_constraint_p0'
down_revision = '20251120_add_version_fields_p0'
branch_labels = None
depends_on = None


def upgrade():
    """
    修复 reconciliation_batches.status CHECK 约束名称

    变更：check_batch_status → chk_reconciliation_batches_status
    ```    """
    # 尝试删除旧约束（如果存在）
    try:
        op.drop_constraint('check_batch_status', 'reconciliation_batches', type_='check')
    except Exception:
        pass  # 约束可能不存在，忽略错误

    # 创建新约束（使用规范名称）
    op.create_check_constraint(
        'chk_reconciliation_batches_status',
        'reconciliation_batches',
        "status IN ('draft', 'pending', 'reviewing', 'closed')"
    )


def downgrade():
    """回滚：恢复旧约束名"""
    op.drop_constraint('chk_reconciliation_batches_status', 'reconciliation_batches', type_='check')

    op.create_check_constraint(
        'check_batch_status',
        'reconciliation_batches',
        "status IN ('draft', 'pending', 'reviewing', 'closed')"
    )
