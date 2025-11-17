"""Add reconciliation performance indexes

Revision ID: 20251115_add_reconciliation_indexes
Revises:
Create Date: 2025-11-15 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251115_add_reconciliation_indexes'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建对账系统性能优化索引

    # 广告消耗日报索引
    op.create_index('idx_ad_spend_daily_account_date', 'ad_spend_daily',
                   ['ad_account_id', 'date'], unique=False)
    op.create_index('idx_ad_spend_daily_date', 'ad_spend_daily',
                   ['date'], unique=False)
    op.create_index('idx_ad_spend_daily_account_id', 'ad_spend_daily',
                   ['ad_account_id'], unique=False)

    # 对账详情索引
    op.create_index('idx_reconciliation_details_batch_id', 'reconciliation_details',
                   ['batch_id'], unique=False)
    op.create_index('idx_reconciliation_details_account_id', 'reconciliation_details',
                   ['ad_account_id'], unique=False)
    op.create_index('idx_reconciliation_details_match_status', 'reconciliation_details',
                   ['match_status'], unique=False)
    op.create_index('idx_reconciliation_details_is_matched', 'reconciliation_details',
                   ['is_matched'], unique=False)

    # 广告账户索引
    op.create_index('idx_ad_accounts_status', 'ad_accounts',
                   ['status'], unique=False)
    op.create_index('idx_ad_accounts_project_id', 'ad_accounts',
                   ['project_id'], unique=False)
    op.create_index('idx_ad_accounts_channel_id', 'ad_accounts',
                   ['channel_id'], unique=False)
    op.create_index('idx_ad_accounts_status_project', 'ad_accounts',
                   ['status', 'project_id'], unique=False)

    # 对账批次索引
    op.create_index('idx_reconciliation_batches_date', 'reconciliation_batches',
                   ['reconciliation_date'], unique=False)
    op.create_index('idx_reconciliation_batches_status', 'reconciliation_batches',
                   ['status'], unique=False)
    op.create_index('idx_reconciliation_batches_created_at', 'reconciliation_batches',
                   ['created_at'], unique=False)

    # 复合索引
    op.create_index('idx_reconciliation_details_batch_account', 'reconciliation_details',
                   ['batch_id', 'ad_account_id'], unique=False)
    op.create_index('idx_reconciliation_batches_date_status', 'reconciliation_batches',
                   ['reconciliation_date', 'status'], unique=False)


def downgrade() -> None:
    # 删除对账系统性能优化索引

    # 复合索引
    op.drop_index('idx_reconciliation_batches_date_status', table_name='reconciliation_batches')
    op.drop_index('idx_reconciliation_details_batch_account', table_name='reconciliation_details')

    # 对账批次索引
    op.drop_index('idx_reconciliation_batches_created_at', table_name='reconciliation_batches')
    op.drop_index('idx_reconciliation_batches_status', table_name='reconciliation_batches')
    op.drop_index('idx_reconciliation_batches_date', table_name='reconciliation_batches')

    # 广告账户索引
    op.drop_index('idx_ad_accounts_status_project', table_name='ad_accounts')
    op.drop_index('idx_ad_accounts_channel_id', table_name='ad_accounts')
    op.drop_index('idx_ad_accounts_project_id', table_name='ad_accounts')
    op.drop_index('idx_ad_accounts_status', table_name='ad_accounts')

    # 对账详情索引
    op.drop_index('idx_reconciliation_details_is_matched', table_name='reconciliation_details')
    op.drop_index('idx_reconciliation_details_match_status', table_name='reconciliation_details')
    op.drop_index('idx_reconciliation_details_account_id', table_name='reconciliation_details')
    op.drop_index('idx_reconciliation_details_batch_id', table_name='reconciliation_details')

    # 广告消耗日报索引
    op.drop_index('idx_ad_spend_daily_account_id', table_name='ad_spend_daily')
    op.drop_index('idx_ad_spend_daily_date', table_name='ad_spend_daily')
    op.drop_index('idx_ad_spend_daily_account_date', table_name='ad_spend_daily')