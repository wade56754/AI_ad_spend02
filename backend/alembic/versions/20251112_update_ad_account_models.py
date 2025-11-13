"""更新广告账户模型

Revision ID: 20251112_update_ad_account_models
Revises: 20251112_add_reconciliation_management_tables
Create Date: 2025-11-12 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251112_update_ad_account_models'
down_revision = '20251112_add_reconciliation_management_tables'
branch_labels = None
depends_on = None


def upgrade():
    """更新广告账户表结构"""

    # 创建新的广告账户表（如果不存在）
    op.create_table(
        'ad_accounts_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.String(length=255), nullable=False, comment='平台账户ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='账户名称'),
        sa.Column('platform', sa.String(length=50), nullable=False, comment='广告平台'),
        sa.Column('platform_account_id', sa.String(length=255), nullable=True, comment='平台内部账户ID'),
        sa.Column('platform_business_id', sa.String(length=255), nullable=True, comment='商务管理器ID'),
        sa.Column('project_id', sa.Integer(), nullable=False, comment='项目ID'),
        sa.Column('channel_id', sa.Integer(), nullable=False, comment='渠道ID'),
        sa.Column('assigned_user_id', sa.Integer(), nullable=False, comment='负责投手ID'),
        sa.Column('status', sa.String(length=20), nullable=False, default='new', comment='账户状态'),
        sa.Column('status_reason', sa.Text(), nullable=True, comment='状态变更原因'),
        sa.Column('last_status_change', sa.DateTime(timezone=True), nullable=True, comment='最后状态变更时间'),
        sa.Column('created_date', sa.DateTime(timezone=True), nullable=True, comment='账户创建时间'),
        sa.Column('activated_date', sa.DateTime(timezone=True), nullable=True, comment='激活时间'),
        sa.Column('suspended_date', sa.DateTime(timezone=True), nullable=True, comment='暂停时间'),
        sa.Column('dead_date', sa.DateTime(timezone=True), nullable=True, comment='死亡时间'),
        sa.Column('archived_date', sa.DateTime(timezone=True), nullable=True, comment='归档时间'),
        sa.Column('daily_budget', postgresql.NUMERIC(precision=10, scale=2), nullable=True, comment='日预算'),
        sa.Column('total_budget', postgresql.NUMERIC(precision=12, scale=2), nullable=True, comment='总预算'),
        sa.Column('remaining_budget', postgresql.NUMERIC(precision=12, scale=2), nullable=True, comment='剩余预算'),
        sa.Column('currency', sa.String(length=3), nullable=True, comment='货币单位'),
        sa.Column('timezone', sa.String(length=50), nullable=True, comment='时区设置'),
        sa.Column('country', sa.String(length=2), nullable=True, comment='国家代码'),
        sa.Column('total_spend', postgresql.NUMERIC(precision=15, scale=2), nullable=True, comment='总消耗'),
        sa.Column('total_leads', sa.Integer(), nullable=True, comment='总潜在客户数'),
        sa.Column('avg_cpl', postgresql.NUMERIC(precision=10, scale=2), nullable=True, comment='平均单粉成本'),
        sa.Column('best_cpl', postgresql.NUMERIC(precision=10, scale=2), nullable=True, comment='最佳单粉成本'),
        sa.Column('setup_fee', postgresql.NUMERIC(precision=10, scale=2), nullable=True, comment='开户费'),
        sa.Column('setup_fee_paid', sa.Boolean(), nullable=True, comment='开户费是否已支付'),
        sa.Column('account_type', sa.String(length=50), nullable=True, comment='账户类型'),
        sa.Column('payment_method', sa.String(length=50), nullable=True, comment='支付方式'),
        sa.Column('billing_information', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='账单信息'),
        sa.Column('auto_monitoring', sa.Boolean(), nullable=True, comment='自动监控'),
        sa.Column('alert_thresholds', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='预警阈值设置'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注'),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='标签'),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='元数据'),
        sa.Column('created_by', sa.Integer(), nullable=False, comment='创建人ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_id'),
        sa.ForeignKeyConstraint(['assigned_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.CheckConstraint("status IN ('new', 'testing', 'active', 'suspended', 'dead', 'archived')", name='check_account_status'),
        sa.CheckConstraint('daily_budget >= 0', name='check_daily_budget_non_negative'),
        sa.CheckConstraint('total_budget >= 0', name='check_total_budget_non_negative'),
        sa.CheckConstraint('total_spend >= 0', name='check_total_spend_non_negative'),
        sa.Index('idx_ad_accounts_assigned_user', 'assigned_user_id'),
        sa.Index('idx_ad_accounts_channel', 'channel_id'),
        sa.Index('idx_ad_accounts_created_at', 'created_at'),
        sa.Index('idx_ad_accounts_platform', 'platform'),
        sa.Index('idx_ad_accounts_project', 'project_id'),
        sa.Index('idx_ad_accounts_status', 'status'),
        {'comment': '广告账户表'}
    )

    # 如果旧表存在，迁移数据
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if 'ad_accounts' in inspector.get_table_names():
        # 检查旧表是否使用GUID
        columns = inspector.get_columns('ad_accounts')
        id_column = next((c for c in columns if c['name'] == 'id'), None)

        if id_column and id_column['type'].upper().startswith('UUID'):
            # 旧表使用UUID，需要数据迁移
            op.execute("""
                INSERT INTO ad_accounts_new (
                    account_id, name, platform, platform_account_id,
                    platform_business_id, project_id, channel_id,
                    assigned_user_id, status, status_reason,
                    daily_budget, total_budget, currency,
                    total_spend, total_leads, avg_cpl,
                    created_by, created_at, updated_at,
                    notes, tags, metadata
                )
                SELECT
                    account_id, name, platform, platform_account_id,
                    platform_business_id, CAST(project_id AS INTEGER),
                    CAST(channel_id AS INTEGER), CAST(assigned_user_id AS INTEGER),
                    status, status_reason, daily_budget,
                    total_budget, currency, total_spend,
                    total_leads, avg_cpl, CAST(created_by AS INTEGER),
                    created_at, updated_at, notes, tags, metadata
                FROM ad_accounts
            """)

            # 删除旧表
            op.drop_table('ad_accounts')

        # 重命名新表
        op.execute('ALTER TABLE ad_accounts_new RENAME TO ad_accounts')
    else:
        # 直接使用新表
        op.execute('ALTER TABLE ad_accounts_new RENAME TO ad_accounts')

    # 创建账户状态历史表
    op.create_table(
        'account_status_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False, comment='账户ID'),
        sa.Column('old_status', sa.String(length=20), nullable=True, comment='原状态'),
        sa.Column('new_status', sa.String(length=20), nullable=False, comment='新状态'),
        sa.Column('change_reason', sa.Text(), nullable=True, comment='变更原因'),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='变更时间'),
        sa.Column('changed_by', sa.Integer(), nullable=False, comment='变更人ID'),
        sa.Column('change_source', sa.String(length=50), nullable=True, comment='变更来源'),
        sa.Column('performance_data', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='变更时的性能数据'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注说明'),
        sa.ForeignKeyConstraint(['account_id'], ['ad_accounts.id'], ),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_account_status_history_account', 'account_id'),
        sa.Index('idx_account_status_history_changed_at', 'changed_at'),
        {'comment': '账户状态历史表'}
    )

    # 创建账户表现表
    op.create_table(
        'account_performance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False, comment='账户ID'),
        sa.Column('period_type', sa.String(length=20), nullable=False, comment='统计周期'),
        sa.Column('period_start', sa.Date(), nullable=False, comment='周期开始日期'),
        sa.Column('period_end', sa.Date(), nullable=False, comment='周期结束日期'),
        sa.Column('spend', postgresql.NUMERIC(precision=15, scale=2), nullable=False, comment='消耗'),
        sa.Column('impressions', sa.Integer(), nullable=True, comment='展示次数'),
        sa.Column('clicks', sa.Integer(), nullable=True, comment='点击次数'),
        sa.Column('ctr', postgresql.NUMERIC(precision=5, scale=4), nullable=True, comment='点击率'),
        sa.Column('leads', sa.Integer(), nullable=True, comment='潜在客户数'),
        sa.Column('conversions', sa.Integer(), nullable=True, comment='转化数'),
        sa.Column('conversion_rate', postgresql.NUMERIC(precision=5, scale=4), nullable=True, comment='转化率'),
        sa.Column('cpl', postgresql.NUMERIC(precision=10, scale=2), nullable=True, comment='单粉成本'),
        sa.Column('cpa', postgresql.NUMERIC(precision=10, scale=2), nullable=True, comment='单次转化成本'),
        sa.Column('roas', postgresql.NUMERIC(precision=5, scale=2), nullable=True, comment='广告支出回报率'),
        sa.Column('lead_quality_score', postgresql.NUMERIC(precision=3, scale=2), nullable=True, comment='潜在客户质量评分'),
        sa.Column('account_health_score', postgresql.NUMERIC(precision=3, scale=2), nullable=True, comment='账户健康评分'),
        sa.Column('breakdown_data', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='细分数据'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.ForeignKeyConstraint(['account_id'], ['ad_accounts.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("period_type IN ('daily', 'weekly', 'monthly')", name='check_period_type'),
        sa.CheckConstraint('period_end >= period_start', name='check_period_date_valid'),
        sa.Index('idx_account_performance_account', 'account_id'),
        sa.Index('idx_account_performance_period', 'period_type', 'period_start'),
        sa.Index('idx_account_performance_spend', 'spend'),
        {'comment': '账户表现表'}
    )

    # 创建账户预警表
    op.create_table(
        'account_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False, comment='账户ID'),
        sa.Column('alert_type', sa.String(length=50), nullable=False, comment='预警类型'),
        sa.Column('severity', sa.String(length=20), nullable=False, comment='严重程度'),
        sa.Column('title', sa.String(length=255), nullable=False, comment='预警标题'),
        sa.Column('message', sa.Text(), nullable=False, comment='预警消息'),
        sa.Column('status', sa.String(length=20), nullable=True, comment='预警状态'),
        sa.Column('trigger_condition', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='触发条件'),
        sa.Column('trigger_value', postgresql.NUMERIC(precision=15, scale=2), nullable=True, comment='触发值'),
        sa.Column('threshold_value', postgresql.NUMERIC(precision=15, scale=2), nullable=True, comment='阈值'),
        sa.Column('acknowledged_by', sa.Integer(), nullable=True, comment='确认人ID'),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True, comment='确认时间'),
        sa.Column('resolution', sa.Text(), nullable=True, comment='解决方案'),
        sa.Column('resolved_by', sa.Integer(), nullable=True, comment='解决人ID'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True, comment='解决时间'),
        sa.Column('notify_users', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='通知用户列表'),
        sa.Column('notification_sent', sa.Boolean(), nullable=True, comment='是否已发送通知'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['account_id'], ['ad_accounts.id'], ),
        sa.ForeignKeyConstraint(['acknowledged_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("severity IN ('low', 'medium', 'high', 'critical')", name='check_alert_severity'),
        sa.CheckConstraint("status IN ('active', 'acknowledged', 'resolved', 'ignored')", name='check_alert_status'),
        sa.Index('idx_account_alerts_account', 'account_id'),
        sa.Index('idx_account_alerts_severity', 'severity'),
        sa.Index('idx_account_alerts_status', 'status'),
        sa.Index('idx_account_alerts_type', 'alert_type'),
        sa.Index('idx_account_alerts_created_at', 'created_at'),
        {'comment': '账户预警表'}
    )

    # 创建账户文档表
    op.create_table(
        'account_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False, comment='账户ID'),
        sa.Column('document_type', sa.String(length=50), nullable=False, comment='文档类型'),
        sa.Column('document_name', sa.String(length=255), nullable=False, comment='文档名称'),
        sa.Column('file_path', sa.String(length=500), nullable=True, comment='文件路径'),
        sa.Column('file_size', sa.Integer(), nullable=True, comment='文件大小'),
        sa.Column('file_type', sa.String(length=50), nullable=True, comment='文件类型'),
        sa.Column('description', sa.Text(), nullable=True, comment='文档描述'),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='标签'),
        sa.Column('status', sa.String(length=20), nullable=True, comment='状态'),
        sa.Column('uploaded_by', sa.Integer(), nullable=False, comment='上传人ID'),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='上传时间'),
        sa.Column('is_public', sa.Boolean(), nullable=True, comment='是否公开'),
        sa.Column('shared_users', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='共享用户列表'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['account_id'], ['ad_accounts.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('active', 'archived', 'deleted')", name='check_document_status'),
        sa.Index('idx_account_documents_account', 'account_id'),
        sa.Index('idx_account_documents_status', 'status'),
        sa.Index('idx_account_documents_type', 'document_type'),
        sa.Index('idx_account_documents_uploaded_at', 'uploaded_at'),
        {'comment': '账户文档表'}
    )

    # 创建账户备注表
    op.create_table(
        'account_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False, comment='账户ID'),
        sa.Column('title', sa.String(length=255), nullable=False, comment='备注标题'),
        sa.Column('content', sa.Text(), nullable=False, comment='备注内容'),
        sa.Column('note_type', sa.String(length=50), nullable=True, comment='备注类型'),
        sa.Column('priority', sa.Integer(), nullable=True, comment='优先级'),
        sa.Column('is_resolved', sa.Boolean(), nullable=True, comment='是否已解决'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True, comment='解决时间'),
        sa.Column('created_by', sa.Integer(), nullable=False, comment='创建人ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.ForeignKeyConstraint(['account_id'], ['ad_accounts.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('priority BETWEEN 1 AND 5', name='check_note_priority_range'),
        sa.Index('idx_account_notes_account', 'account_id'),
        sa.Index('idx_account_notes_priority', 'priority'),
        sa.Index('idx_account_notes_resolved', 'is_resolved'),
        sa.Index('idx_account_notes_type', 'note_type'),
        sa.Index('idx_account_notes_created_at', 'created_at'),
        {'comment': '账户备注表'}
    )

    # 启用RLS
    op.execute('ALTER TABLE ad_accounts ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE account_status_history ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE account_alerts ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE account_documents ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE account_notes ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE account_performance ENABLE ROW LEVEL SECURITY')

    # 创建RLS策略
    # 管理员和财务全权限
    op.execute("""
        CREATE POLICY admin_full_access_ad_accounts ON ad_accounts
        FOR ALL TO admin_role, finance_role
        USING (true)
        WITH CHECK (true)
    """)

    # 投手只能看自己负责的账户
    op.execute("""
        CREATE POLICY media_buyer_own_accounts ON ad_accounts
        FOR ALL TO media_buyer_role
        USING (assigned_user_id = current_setting('app.current_user_id')::integer)
        WITH CHECK (assigned_user_id = current_setting('app.current_user_id')::integer)
    """)

    # 账户管理员只能看自己项目的账户
    op.execute("""
        CREATE POLICY account_manager_project_accounts ON ad_accounts
        FOR SELECT TO account_manager_role
        USING (
            EXISTS (
                SELECT 1 FROM projects
                WHERE projects.id = ad_accounts.project_id
                AND projects.account_manager_id = current_setting('app.current_user_id')::integer
            )
        )
    """)

    # 数据员只读权限
    op.execute("""
        CREATE POLICY data_operator_read_ad_accounts ON ad_accounts
        FOR SELECT TO data_operator_role
        USING (true)
    """)


def downgrade():
    """回滚广告账户表结构"""
    # 删除新表
    op.drop_table('account_notes')
    op.drop_table('account_documents')
    op.drop_table('account_alerts')
    op.drop_table('account_performance')
    op.drop_table('account_status_history')
    op.drop_table('ad_accounts')

    # 恢复旧表结构（如果需要）
    # 这里可以根据实际需要添加回滚逻辑