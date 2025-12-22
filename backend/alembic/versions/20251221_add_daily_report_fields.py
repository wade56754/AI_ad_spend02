"""
Add daily report fields for region, platform, result_count, follows_count, currency

Revision ID: 20251221_daily_report_fields
Revises: 20251220_add_password_hash_to_users
Create Date: 2025-12-21

新增字段:
- region: 投放地区 (Turkey/India/Brazil等)
- platform: 广告平台 (FB/Google/TikTok)
- result_count: 成效数
- follows_count: 进粉数
- currency: 货币类型 (USD/CNY)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251221_daily_report_fields'
down_revision = '20251220_add_password_hash_to_users'
branch_labels = None
depends_on = None


def upgrade():
    """添加日报新字段"""
    # 添加 region 字段
    op.add_column(
        'daily_reports',
        sa.Column('region', sa.String(50), nullable=True, comment='投放地区（Turkey/India/Brazil等）')
    )

    # 添加 platform 字段
    op.add_column(
        'daily_reports',
        sa.Column('platform', sa.String(20), nullable=True, comment='广告平台（FB/Google/TikTok）')
    )

    # 添加 result_count 字段 (成效数)
    op.add_column(
        'daily_reports',
        sa.Column('result_count', sa.Integer(), nullable=False, server_default='0', comment='成效数（result）')
    )

    # 添加 follows_count 字段 (进粉数)
    op.add_column(
        'daily_reports',
        sa.Column('follows_count', sa.Integer(), nullable=False, server_default='0', comment='进粉数（people）')
    )

    # 添加 currency 字段
    op.add_column(
        'daily_reports',
        sa.Column('currency', sa.String(10), nullable=False, server_default='USD', comment='货币类型（USD/CNY）')
    )

    # 创建索引以优化查询
    op.create_index('idx_daily_reports_region', 'daily_reports', ['region'])
    op.create_index('idx_daily_reports_platform', 'daily_reports', ['platform'])


def downgrade():
    """移除日报新字段"""
    # 移除索引
    op.drop_index('idx_daily_reports_platform', table_name='daily_reports')
    op.drop_index('idx_daily_reports_region', table_name='daily_reports')

    # 移除字段
    op.drop_column('daily_reports', 'currency')
    op.drop_column('daily_reports', 'follows_count')
    op.drop_column('daily_reports', 'result_count')
    op.drop_column('daily_reports', 'platform')
    op.drop_column('daily_reports', 'region')
