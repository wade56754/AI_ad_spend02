"""创建日报管理表

Revision ID: 001
Revises:
Create Date: 2025-11-12 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建日报主表
    op.create_table(
        'daily_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_date', sa.Date(), nullable=False, comment='报表日期'),
        sa.Column('ad_account_id', sa.Integer(), nullable=False, comment='广告账户ID'),
        sa.Column('campaign_name', sa.String(length=200), nullable=True, comment='广告系列名称'),
        sa.Column('ad_group_name', sa.String(length=200), nullable=True, comment='广告组名称'),
        sa.Column('ad_creative_name', sa.String(length=200), nullable=True, comment='广告创意名称'),
        sa.Column('impressions', sa.Integer(), server_default='0', nullable=True, comment='展示次数'),
        sa.Column('clicks', sa.Integer(), server_default='0', nullable=True, comment='点击次数'),
        sa.Column('spend', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=True, comment='消耗金额'),
        sa.Column('conversions', sa.Integer(), server_default='0', nullable=True, comment='转化次数'),
        sa.Column('new_follows', sa.Integer(), server_default='0', nullable=True, comment='新增粉丝数'),
        sa.Column('cpa', sa.Numeric(precision=10, scale=2), nullable=True, comment='CPA'),
        sa.Column('roas', sa.Numeric(precision=10, scale=2), nullable=True, comment='ROAS'),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=True, comment='审核状态'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注说明'),
        sa.Column('audit_notes', sa.Text(), nullable=True, comment='审核说明'),
        sa.Column('audit_user_id', sa.Integer(), nullable=True, comment='审核人ID'),
        sa.Column('audit_time', sa.DateTime(timezone=True), nullable=True, comment='审核时间'),
        sa.Column('created_by', sa.Integer(), nullable=False, comment='创建人ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='更新时间'),
        sa.CheckConstraint('status IN (\'pending\', \'approved\', \'rejected\')', name='check_daily_reports_status'),
        sa.UniqueConstraint('report_date', 'ad_account_id', name='uq_daily_reports_date_account'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['ad_account_id'], ['ad_accounts.id'], ),
        sa.ForeignKeyConstraint(['audit_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        comment='日报数据表'
    )

    # 创建索引
    op.create_index('idx_daily_reports_date', 'daily_reports', ['report_date'])
    op.create_index('idx_daily_reports_account', 'daily_reports', ['ad_account_id'])
    op.create_index('idx_daily_reports_status', 'daily_reports', ['status'])
    op.create_index('idx_daily_reports_created_by', 'daily_reports', ['created_by'])
    op.create_index('idx_daily_reports_audit_user', 'daily_reports', ['audit_user_id'])
    op.create_index('idx_daily_reports_date_status', 'daily_reports', ['report_date', 'status'])
    op.create_index('idx_daily_reports_account_date', 'daily_reports', ['ad_account_id', 'report_date'])

    # 创建审核日志表
    op.create_table(
        'daily_report_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('daily_report_id', sa.Integer(), nullable=False, comment='日报ID'),
        sa.Column('action', sa.String(length=20), nullable=False, comment='操作类型'),
        sa.Column('old_status', sa.String(length=20), nullable=True, comment='旧状态'),
        sa.Column('new_status', sa.String(length=20), nullable=True, comment='新状态'),
        sa.Column('audit_user_id', sa.Integer(), nullable=False, comment='操作人ID'),
        sa.Column('audit_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='操作时间'),
        sa.Column('audit_notes', sa.Text(), nullable=True, comment='操作说明'),
        sa.Column('ip_address', postgresql.INET(), nullable=True, comment='IP地址'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='用户代理'),
        sa.CheckConstraint('action IN (\'created\', \'updated\', \'approved\', \'rejected\')', name='check_audit_logs_action'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['audit_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['daily_report_id'], ['daily_reports.id'], ondelete='CASCADE'),
        comment='日报操作审计日志表'
    )

    # 创建审核日志索引
    op.create_index('idx_audit_logs_report', 'daily_report_audit_logs', ['daily_report_id'])
    op.create_index('idx_audit_logs_user', 'daily_report_audit_logs', ['audit_user_id'])
    op.create_index('idx_audit_logs_time', 'daily_report_audit_logs', ['audit_time'])
    op.create_index('idx_audit_logs_action', 'daily_report_audit_logs', ['action'])


def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_audit_logs_action', table_name='daily_report_audit_logs')
    op.drop_index('idx_audit_logs_time', table_name='daily_report_audit_logs')
    op.drop_index('idx_audit_logs_user', table_name='daily_report_audit_logs')
    op.drop_index('idx_audit_logs_report', table_name='daily_report_audit_logs')

    op.drop_index('idx_daily_reports_account_date', table_name='daily_reports')
    op.drop_index('idx_daily_reports_date_status', table_name='daily_reports')
    op.drop_index('idx_daily_reports_audit_user', table_name='daily_reports')
    op.drop_index('idx_daily_reports_created_by', table_name='daily_reports')
    op.drop_index('idx_daily_reports_status', table_name='daily_reports')
    op.drop_index('idx_daily_reports_account', table_name='daily_reports')
    op.drop_index('idx_daily_reports_date', table_name='daily_reports')

    # 删除表
    op.drop_table('daily_report_audit_logs')
    op.drop_table('daily_reports')