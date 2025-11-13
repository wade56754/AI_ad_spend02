"""添加对账管理表

Revision ID: 20251112_add_reconciliation_management_tables
Revises: 20251112_add_topup_management_tables
Create Date: 2025-11-12 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251112_add_reconciliation_management_tables'
down_revision = '20251112_add_topup_management_tables'
branch_labels = None
depends_on = None


def upgrade():
    """创建对账管理相关表"""

    # 创建对账批次表
    op.create_table(
        'reconciliation_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_no', sa.String(length=50), nullable=False, comment='对账批次号'),
        sa.Column('reconciliation_date', sa.Date(), nullable=False, comment='对账日期'),
        sa.Column('status', sa.String(length=20), nullable=False, default='pending', comment='对账状态'),
        sa.Column('total_accounts', sa.Integer(), nullable=False, default=0, comment='总账户数'),
        sa.Column('matched_accounts', sa.Integer(), nullable=False, default=0, comment='匹配账户数'),
        sa.Column('mismatched_accounts', sa.Integer(), nullable=False, default=0, comment='差异账户数'),
        sa.Column('total_platform_spend', postgresql.NUMERIC(precision=15, scale=2), nullable=False, default=0.00, comment='平台总消耗'),
        sa.Column('total_internal_spend', postgresql.NUMERIC(precision=15, scale=2), nullable=False, default=0.00, comment='内部总消耗'),
        sa.Column('total_difference', postgresql.NUMERIC(precision=15, scale=2), nullable=False, default=0.00, comment='总差异金额'),
        sa.Column('auto_matched', sa.Integer(), nullable=True, comment='自动匹配数'),
        sa.Column('manual_reviewed', sa.Integer(), nullable=True, comment='人工审核数'),
        sa.Column('started_at', sa.DateTime(), nullable=True, comment='开始时间'),
        sa.Column('completed_at', sa.DateTime(), nullable=True, comment='完成时间'),
        sa.Column('created_by', sa.Integer(), nullable=False, comment='创建人ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注说明'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('batch_no'),
        sa.CheckConstraint("status IN ('pending', 'processing', 'completed', 'exception', 'resolved')", name='check_batch_status'),
        sa.CheckConstraint('total_accounts >= 0', name='check_total_accounts_non_negative'),
        sa.CheckConstraint('matched_accounts >= 0', name='check_matched_accounts_non_negative'),
        sa.CheckConstraint('mismatched_accounts >= 0', name='check_mismatched_accounts_non_negative'),
        sa.CheckConstraint('auto_matched >= 0', name='check_auto_matched_non_negative'),
        sa.CheckConstraint('manual_reviewed >= 0', name='check_manual_reviewed_non_negative'),
        comment='对账批次表'
    )
    op.create_index('idx_reconciliation_batches_date', 'reconciliation_batches', ['reconciliation_date'])
    op.create_index('idx_reconciliation_batches_status', 'reconciliation_batches', ['status'])
    op.create_index('idx_reconciliation_batches_created_at', 'reconciliation_batches', ['created_at'])

    # 创建对账详情表
    op.create_table(
        'reconciliation_details',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=False, comment='对账批次ID'),
        sa.Column('ad_account_id', sa.Integer(), nullable=False, comment='广告账户ID'),
        sa.Column('project_id', sa.Integer(), nullable=False, comment='项目ID'),
        sa.Column('channel_id', sa.Integer(), nullable=False, comment='渠道ID'),
        sa.Column('platform_spend', postgresql.NUMERIC(precision=15, scale=2), nullable=False, default=0.00, comment='平台消耗'),
        sa.Column('platform_currency', sa.String(length=10), nullable=False, default='USD', comment='平台货币'),
        sa.Column('platform_data_date', sa.Date(), nullable=True, comment='平台数据日期'),
        sa.Column('internal_spend', postgresql.NUMERIC(precision=15, scale=2), nullable=False, default=0.00, comment='内部消耗'),
        sa.Column('internal_currency', sa.String(length=10), nullable=False, default='USD', comment='内部货币'),
        sa.Column('internal_data_date', sa.Date(), nullable=True, comment='内部数据日期'),
        sa.Column('spend_difference', postgresql.NUMERIC(precision=15, scale=2), nullable=False, default=0.00, comment='消耗差异'),
        sa.Column('exchange_rate', postgresql.NUMERIC(precision=10, scale=4), nullable=False, default=1.0000, comment='汇率'),
        sa.Column('is_matched', sa.Boolean(), nullable=False, default=False, comment='是否匹配'),
        sa.Column('match_status', sa.String(length=20), nullable=False, default='pending', comment='匹配状态'),
        sa.Column('difference_type', sa.String(length=50), nullable=True, comment='差异类型'),
        sa.Column('difference_reason', sa.Text(), nullable=True, comment='差异原因描述'),
        sa.Column('auto_confidence', postgresql.NUMERIC(precision=3, scale=2), nullable=False, default=0.00, comment='自动匹配置信度'),
        sa.Column('reviewed_by', sa.Integer(), nullable=True, comment='审核人ID'),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True, comment='审核时间'),
        sa.Column('review_notes', sa.Text(), nullable=True, comment='审核说明'),
        sa.Column('resolved_by', sa.Integer(), nullable=True, comment='处理人ID'),
        sa.Column('resolved_at', sa.DateTime(), nullable=True, comment='处理时间'),
        sa.Column('resolution_method', sa.String(length=50), nullable=True, comment='处理方法'),
        sa.Column('resolution_notes', sa.Text(), nullable=True, comment='处理说明'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['ad_account_id'], ['ad_accounts.id'], ),
        sa.ForeignKeyConstraint(['batch_id'], ['reconciliation_batches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("match_status IN ('pending', 'matched', 'auto_matched', 'manual_review', 'exception', 'resolved')", name='check_match_status'),
        sa.CheckConstraint('auto_confidence >= 0 AND auto_confidence <= 1', name='check_auto_confidence_range'),
        comment='对账详情表'
    )
    op.create_index('idx_reconciliation_details_account', 'reconciliation_details', ['ad_account_id'])
    op.create_index('idx_reconciliation_details_batch', 'reconciliation_details', ['batch_id'])
    op.create_index('idx_reconciliation_details_date', 'reconciliation_details', ['platform_data_date'])
    op.create_index('idx_reconciliation_details_status', 'reconciliation_details', ['match_status'])

    # 创建对账调整记录表
    op.create_table(
        'reconciliation_adjustments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('detail_id', sa.Integer(), nullable=False, comment='对账详情ID'),
        sa.Column('batch_id', sa.Integer(), nullable=False, comment='对账批次ID'),
        sa.Column('adjustment_type', sa.String(length=50), nullable=False, comment='调整类型'),
        sa.Column('original_amount', postgresql.NUMERIC(precision=15, scale=2), nullable=False, comment='原始金额'),
        sa.Column('adjustment_amount', postgresql.NUMERIC(precision=15, scale=2), nullable=False, comment='调整金额'),
        sa.Column('adjusted_amount', postgresql.NUMERIC(precision=15, scale=2), nullable=False, comment='调整后金额'),
        sa.Column('adjustment_reason', sa.String(length=100), nullable=False, comment='调整原因'),
        sa.Column('detailed_reason', sa.Text(), nullable=False, comment='详细原因说明'),
        sa.Column('evidence_url', sa.String(length=500), nullable=True, comment='证据文件URL'),
        sa.Column('approved_by', sa.Integer(), nullable=False, comment='审批人ID'),
        sa.Column('approved_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='审批时间'),
        sa.Column('finance_approve', sa.Boolean(), nullable=False, default=False, comment='财务确认'),
        sa.Column('finance_approved_by', sa.Integer(), nullable=True, comment='财务审批人ID'),
        sa.Column('finance_approved_at', sa.DateTime(), nullable=True, comment='财务审批时间'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['batch_id'], ['reconciliation_batches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['detail_id'], ['reconciliation_details.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['finance_approved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("adjustment_type IN ('spend_adjustment', 'date_adjustment')", name='check_adjustment_type'),
        comment='对账调整记录表'
    )
    op.create_index('idx_reconciliation_adjustments_batch', 'reconciliation_adjustments', ['batch_id'])
    op.create_index('idx_reconciliation_adjustments_detail', 'reconciliation_adjustments', ['detail_id'])
    op.create_index('idx_reconciliation_adjustments_type', 'reconciliation_adjustments', ['adjustment_type'])

    # 创建对账报告表
    op.create_table(
        'reconciliation_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=True, comment='对账批次ID'),
        sa.Column('report_type', sa.String(length=50), nullable=False, comment='报告类型'),
        sa.Column('report_period_start', sa.Date(), nullable=False, comment='报告开始日期'),
        sa.Column('report_period_end', sa.Date(), nullable=False, comment='报告结束日期'),
        sa.Column('report_data', postgresql.JSON(astext_type=sa.Text()), nullable=False, comment='报告数据'),
        sa.Column('chart_data', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='图表数据'),
        sa.Column('summary_data', postgresql.JSON(astext_type=sa.Text()), nullable=False, comment='摘要数据'),
        sa.Column('generated_by', sa.Integer(), nullable=False, comment='生成人ID'),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='生成时间'),
        sa.Column('file_path', sa.String(length=500), nullable=True, comment='报告文件路径'),
        sa.Column('file_size', sa.Integer(), nullable=True, comment='文件大小（字节）'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.ForeignKeyConstraint(['batch_id'], ['reconciliation_batches.id'], ),
        sa.ForeignKeyConstraint(['generated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("report_type IN ('daily', 'weekly', 'monthly')", name='check_report_type'),
        sa.CheckConstraint('report_period_end >= report_period_start', name='check_report_period_valid'),
        comment='对账报告表'
    )
    op.create_index('idx_reconciliation_reports_batch', 'reconciliation_reports', ['batch_id'])
    op.create_index('idx_reconciliation_reports_period', 'reconciliation_reports', ['report_period_start'])
    op.create_index('idx_reconciliation_reports_type', 'reconciliation_reports', ['report_type'])

    # 创建RLS策略
    # 启用RLS
    op.execute('ALTER TABLE reconciliation_batches ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE reconciliation_details ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE reconciliation_adjustments ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE reconciliation_reports ENABLE ROW LEVEL SECURITY')

    # 管理员和财务全权限策略
    op.execute("""
        CREATE POLICY finance_full_access_reconciliation ON reconciliation_batches
        FOR ALL TO admin_role, finance_role
        USING (true)
        WITH CHECK (true)
    """)

    op.execute("""
        CREATE POLICY finance_full_access_reconciliation_details ON reconciliation_details
        FOR ALL TO admin_role, finance_role
        USING (true)
        WITH CHECK (true)
    """)

    # 数据员只读权限策略
    op.execute("""
        CREATE POLICY data_operator_read_reconciliation ON reconciliation_batches
        FOR SELECT TO data_operator_role
        USING (true)
    """)

    op.execute("""
        CREATE POLICY data_operator_read_reconciliation_details ON reconciliation_details
        FOR SELECT TO data_operator_role
        USING (true)
    """)

    # 账户管理员查看项目内数据策略
    op.execute("""
        CREATE POLICY account_manager_view_reconciliation ON reconciliation_batches
        FOR SELECT TO account_manager_role
        USING (
            EXISTS (
                SELECT 1 FROM reconciliation_details rd
                JOIN ad_accounts aa ON rd.ad_account_id = aa.id
                WHERE rd.batch_id = reconciliation_batches.id
                AND aa.project_id IN (
                    SELECT id FROM projects
                    WHERE account_manager_id = current_setting('app.current_user_id')::integer
                )
            )
        )
    """)

    # 投手查看自己相关账户数据策略
    op.execute("""
        CREATE POLICY media_buyer_view_reconciliation ON reconciliation_batches
        FOR SELECT TO media_buyer_role
        USING (
            EXISTS (
                SELECT 1 FROM reconciliation_details rd
                JOIN ad_accounts aa ON rd.ad_account_id = aa.id
                WHERE rd.batch_id = reconciliation_batches.id
                AND aa.assigned_user_id = current_setting('app.current_user_id')::integer
            )
        )
    """)


def downgrade():
    """删除对账管理相关表"""

    # 删除RLS策略
    op.execute('DROP POLICY IF EXISTS finance_full_access_reconciliation ON reconciliation_batches')
    op.execute('DROP POLICY IF EXISTS finance_full_access_reconciliation_details ON reconciliation_details')
    op.execute('DROP POLICY IF EXISTS data_operator_read_reconciliation ON reconciliation_batches')
    op.execute('DROP POLICY IF EXISTS data_operator_read_reconciliation_details ON reconciliation_details')
    op.execute('DROP POLICY IF EXISTS account_manager_view_reconciliation ON reconciliation_batches')
    op.execute('DROP POLICY IF EXISTS media_buyer_view_reconciliation ON reconciliation_batches')

    # 删除表
    op.drop_table('reconciliation_reports')
    op.drop_table('reconciliation_adjustments')
    op.drop_table('reconciliation_details')
    op.drop_table('reconciliation_batches')