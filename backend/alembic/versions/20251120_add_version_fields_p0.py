"""P0-004: 添加 version 字段实现乐观锁（Optimistic Locking）

Revision ID: 20251120_add_version_fields_p0
Revises:
Create Date: 2025-11-20

根据 STATE_MACHINE.md v2.5 第17章要求，为核心工作流表添加 version 字段
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251120_add_version_fields_p0'
down_revision = None  # 需要根据实际最新迁移文件修改
branch_labels = None
depends_on = None


def upgrade():
    """
    添加 version 字段到以下表：
    1. topup_requests - 充值申请（防止双审批冲突）
    2. daily_reports - 日报（防止双审批冲突）
    3. reconciliation_batches - 对账批次（防止状态竞争）
    4. projects - 项目（防止状态并发修改）
    5. ad_accounts - 广告账户（防止状态并发修改）
    6. reconciliation_details - 对账明细（防止金额并发修改）
    """

    # 1. topup_requests
    op.add_column(
        'topup_requests',
        sa.Column('version', sa.Integer(), nullable=False, server_default='1', comment='乐观锁版本号')
    )
    op.create_index('idx_topup_requests_version', 'topup_requests', ['version'])

    # 2. daily_reports
    op.add_column(
        'daily_reports',
        sa.Column('version', sa.Integer(), nullable=False, server_default='1', comment='乐观锁版本号')
    )
    op.create_index('idx_daily_reports_version', 'daily_reports', ['version'])

    # 3. reconciliation_batches
    op.add_column(
        'reconciliation_batches',
        sa.Column('version', sa.Integer(), nullable=False, server_default='1', comment='乐观锁版本号')
    )
    op.create_index('idx_reconciliation_batches_version', 'reconciliation_batches', ['version'])

    # 4. projects
    op.add_column(
        'projects',
        sa.Column('version', sa.Integer(), nullable=False, server_default='1', comment='乐观锁版本号')
    )
    op.create_index('idx_projects_version', 'projects', ['version'])

    # 5. ad_accounts
    op.add_column(
        'ad_accounts',
        sa.Column('version', sa.Integer(), nullable=False, server_default='1', comment='乐观锁版本号')
    )
    op.create_index('idx_ad_accounts_version', 'ad_accounts', ['version'])

    # 6. reconciliation_details
    op.add_column(
        'reconciliation_details',
        sa.Column('version', sa.Integer(), nullable=False, server_default='1', comment='乐观锁版本号')
    )
    op.create_index('idx_reconciliation_details_version', 'reconciliation_details', ['version'])


def downgrade():
    """回滚：删除所有 version 字段和索引"""

    # 按相反顺序删除
    op.drop_index('idx_reconciliation_details_version', table_name='reconciliation_details')
    op.drop_column('reconciliation_details', 'version')

    op.drop_index('idx_ad_accounts_version', table_name='ad_accounts')
    op.drop_column('ad_accounts', 'version')

    op.drop_index('idx_projects_version', table_name='projects')
    op.drop_column('projects', 'version')

    op.drop_index('idx_reconciliation_batches_version', table_name='reconciliation_batches')
    op.drop_column('reconciliation_batches', 'version')

    op.drop_index('idx_daily_reports_version', table_name='daily_reports')
    op.drop_column('daily_reports', 'version')

    op.drop_index('idx_topup_requests_version', table_name='topup_requests')
    op.drop_column('topup_requests', 'version')
