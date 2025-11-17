"""Add missing core models v3.0

Revision ID: 20250115_add_missing_core_models_v3
Revises:
Create Date: 2025-01-15 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250115_add_missing_core_models_v3'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建 ledger_transactions 表
    op.create_table('ledger_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('transaction_number', sa.String(length=50), nullable=False, comment='交易流水号'),
        sa.Column('transaction_type', sa.Enum('topup', 'spend', 'refund', 'fee', 'adjustment', 'transfer', name='transactiontype'), nullable=False, comment='交易类型'),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False, comment='交易金额'),
        sa.Column('currency', sa.String(length=3), nullable=False, default='USD', comment='货币类型'),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', 'cancelled', 'reversed', name='transactionstatus'), nullable=False, comment='交易状态'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True, comment='项目ID'),
        sa.Column('ad_account_id', postgresql.UUID(as_uuid=True), nullable=True, comment='广告账户ID'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, comment='用户ID'),
        sa.Column('channel_id', postgresql.UUID(as_uuid=True), nullable=True, comment='渠道ID'),
        sa.Column('counterparty', sa.String(length=255), nullable=True, comment='交易对手'),
        sa.Column('counterparty_account', sa.String(length=255), nullable=True, comment='对手账户'),
        sa.Column('description', sa.Text(), nullable=True, comment='交易描述'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注信息'),
        sa.Column('reference_id', sa.String(length=255), nullable=True, comment='关联业务ID'),
        sa.Column('reference_type', sa.String(length=50), nullable=True, comment='关联业务类型'),
        sa.Column('transaction_date', sa.DateTime(), nullable=False, comment='交易时间'),
        sa.Column('processed_at', sa.DateTime(), nullable=True, comment='处理时间'),
        sa.Column('completed_at', sa.DateTime(), nullable=True, comment='完成时间'),
        sa.Column('fee_amount', sa.Numeric(precision=10, scale=2), nullable=True, default=sa.text('0')),
        sa.Column('fee_rate', sa.Numeric(precision=5, scale=4), nullable=True, default=sa.text('0')),
        sa.Column('external_transaction_id', sa.String(length=255), nullable=True, comment='外部交易ID'),
        sa.Column('external_provider', sa.String(length=50), nullable=True, comment='外部提供商'),
        sa.Column('external_reference', sa.Text(), nullable=True, comment='外部参考信息'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False, comment='创建人'),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True, comment='审批人'),
        sa.Column('approved_at', sa.DateTime(), nullable=True, comment='审批时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True, comment='软删除时间'),
        sa.CheckConstraint('transaction_type IN (\'topup\', \'spend\', \'refund\', \'fee\', \'adjustment\', \'transfer\')', name='ck_ledger_transactions_type'),
        sa.CheckConstraint('status IN (\'pending\', \'processing\', \'completed\', \'failed\', \'cancelled\', \'reversed\')', name='ck_ledger_transactions_status'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_number', name='uq_ledger_transactions_number'),
        comment='财务流水表 - 记录所有资金变动'
    )
    op.create_index('idx_ledger_transaction_number', 'ledger_transactions', ['transaction_number'])
    op.create_index('idx_ledger_type_status', 'ledger_transactions', ['transaction_type', 'status'])
    op.create_index('idx_ledger_project', 'ledger_transactions', ['project_id'])
    op.create_index('idx_ledger_account', 'ledger_transactions', ['ad_account_id'])
    op.create_index('idx_ledger_user', 'ledger_transactions', ['user_id'])
    op.create_index('idx_ledger_date', 'ledger_transactions', ['transaction_date'])
    op.create_index('idx_ledger_created_at', 'ledger_transactions', ['created_at'])
    op.create_index('idx_ledger_reference', 'ledger_transactions', ['reference_type', 'reference_id'])
    op.create_index('idx_ledger_deleted_at', 'ledger_transactions', ['deleted_at'])

    # 外键约束
    op.create_foreign_key('fk_ledger_transactions_project_id', 'ledger_transactions', 'projects', ['project_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_ledger_transactions_ad_account_id', 'ledger_transactions', 'ad_accounts', ['ad_account_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_ledger_transactions_user_id', 'ledger_transactions', 'users', ['user_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_ledger_transactions_channel_id', 'ledger_transactions', 'channels', ['channel_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_ledger_transactions_created_by', 'ledger_transactions', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_ledger_transactions_approved_by', 'ledger_transactions', 'users', ['approved_by'], ['id'])

    # 创建 account_balances 表
    op.create_table('account_balances',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False, comment='项目ID'),
        sa.Column('ad_account_id', postgresql.UUID(as_uuid=True), nullable=True, comment='广告账户ID'),
        sa.Column('channel_id', postgresql.UUID(as_uuid=True), nullable=True, comment='渠道ID'),
        sa.Column('currency', sa.String(length=3), nullable=False, default='USD', comment='货币类型'),
        sa.Column('total_balance', sa.Numeric(precision=15, scale=2), nullable=True, default=sa.text('0'), comment='总余额'),
        sa.Column('available_balance', sa.Numeric(precision=15, scale=2), nullable=True, default=sa.text('0'), comment='可用余额'),
        sa.Column('frozen_balance', sa.Numeric(precision=15, scale=2), nullable=True, default=sa.text('0'), comment='冻结余额'),
        sa.Column('total_topup', sa.Numeric(precision=15, scale=2), nullable=True, default=sa.text('0'), comment='总充值'),
        sa.Column('total_spend', sa.Numeric(precision=15, scale=2), nullable=True, default=sa.text('0'), comment='总消耗'),
        sa.Column('total_fee', sa.Numeric(precision=15, scale=2), nullable=True, default=sa.text('0'), comment='总手续费'),
        sa.Column('last_transaction_id', postgresql.UUID(as_uuid=True), nullable=True, comment='最后交易ID'),
        sa.Column('last_transaction_at', sa.DateTime(), nullable=True, comment='最后交易时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'ad_account_id', 'currency', name='uq_account_balances'),
        comment='账户余额表 - 记录各账户实时余额'
    )
    op.create_index('idx_account_balances_project', 'account_balances', ['project_id'])
    op.create_index('idx_account_balances_account', 'account_balances', ['ad_account_id'])
    op.create_index('idx_account_balances_channel', 'account_balances', ['channel_id'])
    op.create_index('idx_account_balances_currency', 'account_balances', ['currency'])
    op.create_index('idx_account_balances_updated', 'account_balances', ['updated_at'])

    # 外键约束
    op.create_foreign_key('fk_account_balances_project_id', 'account_balances', 'projects', ['project_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_account_balances_ad_account_id', 'account_balances', 'ad_accounts', ['ad_account_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_account_balances_channel_id', 'account_balances', 'channels', ['channel_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_account_balances_last_transaction_id', 'account_balances', 'ledger_transactions', ['last_transaction_id'], ['id'])

    # 创建 reconciliation_batches 表
    op.create_table('reconciliation_batches',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('batch_number', sa.String(length=50), nullable=False, comment='对账批次号'),
        sa.Column('title', sa.String(length=255), nullable=False, comment='对账标题'),
        sa.Column('description', sa.Text(), nullable=True, comment='对账描述'),
        sa.Column('reconciliation_type', sa.Enum('daily', 'weekly', 'monthly', 'custom', name='reconciliationtype'), nullable=False, comment='对账类型'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True, comment='项目ID（可选，全局对账时为空）'),
        sa.Column('channel_id', postgresql.UUID(as_uuid=True), nullable=True, comment='渠道ID（可选）'),
        sa.Column('start_date', sa.Date(), nullable=False, comment='对账开始日期'),
        sa.Column('end_date', sa.Date(), nullable=False, comment='对账结束日期'),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', 'cancelled', name='reconciliationstatus'), default='pending', nullable=False, comment='对账状态'),
        sa.Column('total_transactions', sa.Integer(), nullable=True, default=sa.text('0'), comment='总交易数'),
        sa.Column('matched_transactions', sa.Integer(), nullable=True, default=sa.text('0'), comment='匹配交易数'),
        sa.Column('unmatched_transactions', sa.Integer(), nullable=True, default=sa.text('0'), comment='未匹配交易数'),
        sa.Column('total_differences', sa.Integer(), nullable=True, default=sa.text('0'), comment='差异总数'),
        sa.Column('resolved_differences', sa.Integer(), nullable=True, default=sa.text('0'), comment='已解决差异数'),
        sa.Column('total_spend', sa.Numeric(precision=15, scale=2), nullable=True, default=sa.text('0'), comment='总消耗'),
        sa.Column('total_topup', sa.Numeric(precision=15, scale=2), nullable=True, default=sa.text('0'), comment='总充值'),
        sa.Column('total_difference', sa.Numeric(precision=15, scale=2), nullable=True, default=sa.text('0'), comment='总差异金额'),
        sa.Column('resolved_amount', sa.Numeric(precision=15, scale=2), nullable=True, default=sa.text('0'), comment='已解决差异金额'),
        sa.Column('started_at', sa.DateTime(), nullable=True, comment='开始时间'),
        sa.Column('completed_at', sa.DateTime(), nullable=True, comment='完成时间'),
        sa.Column('execution_time', sa.Integer(), nullable=True, comment='执行时间（秒）'),
        sa.Column('auto_resolve_threshold', sa.Numeric(precision=10, scale=2), nullable=True, default=sa.text('0.01'), comment='自动解决阈值'),
        sa.Column('include_pending', sa.Boolean(), nullable=True, default=sa.text('false'), comment='是否包含待处理交易'),
        sa.Column('report_path', sa.String(length=500), nullable=True, comment='报表文件路径'),
        sa.Column('report_generated_at', sa.DateTime(), nullable=True, comment='报表生成时间'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False, comment='创建人'),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True, comment='审批人'),
        sa.Column('approved_at', sa.DateTime(), nullable=True, comment='审批时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True, comment='软删除时间'),
        sa.CheckConstraint('reconciliation_type IN (\'daily\', \'weekly\', \'monthly\', \'custom\')', name='ck_recon_batches_type'),
        sa.CheckConstraint('status IN (\'pending\', \'processing\', \'completed\', \'failed\', \'cancelled\')', name='ck_recon_batches_status'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('batch_number', name='uq_recon_batches_number'),
        comment='对账批次表 - 对账任务的主要容器'
    )
    op.create_index('idx_recon_batch_number', 'reconciliation_batches', ['batch_number'])
    op.create_index('idx_recon_type_status', 'reconciliation_batches', ['reconciliation_type', 'status'])
    op.create_index('idx_recon_project', 'reconciliation_batches', ['project_id'])
    op.create_index('idx_recon_channel', 'reconciliation_batches', ['channel_id'])
    op.create_index('idx_recon_dates', 'reconciliation_batches', ['start_date', 'end_date'])
    op.create_index('idx_recon_created_at', 'reconciliation_batches', ['created_at'])
    op.create_index('idx_recon_deleted_at', 'reconciliation_batches', ['deleted_at'])

    # 创建 ai_anomaly_detections 表
    op.create_table('ai_anomaly_detections',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('anomaly_number', sa.String(length=50), nullable=False, comment='异常编号'),
        sa.Column('title', sa.String(length=255), nullable=False, comment='异常标题'),
        sa.Column('description', sa.Text(), nullable=True, comment='异常描述'),
        sa.Column('anomaly_type', sa.Enum('spending_spike', 'performance_decline', 'lead_quality_drop', 'account_risk', 'conversion_anomaly', 'traffic_anomaly', 'budget_depletion', 'frequency_anomaly', name='anomalytype'), nullable=False, comment='异常类型'),
        sa.Column('severity', sa.Enum('low', 'medium', 'high', 'critical', name='anomalyseverity'), nullable=False, comment='严重程度'),
        sa.Column('status', sa.Enum('detected', 'investigating', 'confirmed', 'resolved', 'ignored', 'false_positive', name='anomalystatus'), default='detected', nullable=False, comment='异常状态'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True, comment='项目ID'),
        sa.Column('ad_account_id', postgresql.UUID(as_uuid=True), nullable=True, comment='广告账户ID'),
        sa.Column('channel_id', postgresql.UUID(as_uuid=True), nullable=True, comment='渠道ID'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, comment='用户ID'),
        sa.Column('anomaly_date', sa.Date(), nullable=False, comment='异常日期'),
        sa.Column('detection_time', sa.DateTime(), nullable=False, comment='检测时间'),
        sa.Column('baseline_value', sa.Numeric(precision=15, scale=2), nullable=True, default=sa.text('0'), comment='基线值'),
        sa.Column('actual_value', sa.Numeric(precision=15, scale=2), nullable=True, default=sa.text('0'), comment='实际值'),
        sa.Column('deviation_percentage', sa.Numeric(precision=5, scale=2), nullable=True, default=sa.text('0'), comment='偏差百分比'),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=4), nullable=True, default=sa.text('0'), comment='置信度分数'),
        sa.Column('metric_name', sa.String(length=100), nullable=True, comment='指标名称'),
        sa.Column('metric_value', sa.Numeric(precision=15, scale=2), nullable=True, default=sa.text('0'), comment='指标值'),
        sa.Column('threshold_value', sa.Numeric(precision=15, scale=2), nullable=True, default=sa.text('0'), comment='阈值'),
        sa.Column('model_version', sa.String(length=50), nullable=True, comment='模型版本'),
        sa.Column('financial_impact', sa.Numeric(precision=15, scale=2), nullable=True, default=sa.text('0'), comment='财务影响'),
        sa.Column('performance_impact', sa.Numeric(precision=5, scale=2), nullable=True, default=sa.text('0'), comment='性能影响'),
        sa.Column('risk_impact', sa.Numeric(precision=5, scale=2), nullable=True, default=sa.text('0'), comment='风险影响'),
        sa.Column('auto_resolution', sa.Boolean(), nullable=True, default=sa.text('false'), comment='是否自动解决'),
        sa.Column('resolution_action', sa.Text(), nullable=True, comment='解决方案'),
        sa.Column('resolution_time', sa.DateTime(), nullable=True, comment='解决时间'),
        sa.Column('notification_sent', sa.Boolean(), nullable=True, default=sa.text('false'), comment='是否已发送通知'),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True, comment='分配给'),
        sa.Column('assigned_at', sa.DateTime(), nullable=True, comment='分配时间'),
        sa.Column('context_data', sa.JSON(), nullable=True, comment='上下文数据'),
        sa.Column('raw_data', sa.JSON(), nullable=True, comment='原始数据'),
        sa.Column('investigation_notes', sa.Text(), nullable=True, comment='调查笔记'),
        sa.Column('resolution_notes', sa.Text(), nullable=True, comment='解决笔记'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False, comment='创建人'),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True, comment='解决人'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True, comment='软删除时间'),
        sa.CheckConstraint('anomaly_type IN (\'spending_spike\', \'performance_decline\', \'lead_quality_drop\', \'account_risk\', \'conversion_anomaly\', \'traffic_anomaly\', \'budget_depletion\', \'frequency_anomaly\')', name='ck_ai_anomaly_type'),
        sa.CheckConstraint('severity IN (\'low\', \'medium\', \'high\', \'critical\')', name='ck_ai_anomaly_severity'),
        sa.CheckConstraint('status IN (\'detected\', \'investigating\', \'confirmed\', \'resolved\', \'ignored\', \'false_positive\')', name='ck_ai_anomaly_status'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('anomaly_number', name='uq_ai_anomaly_number'),
        comment='AI异常检测表 - 记录系统检测到的各种异常'
    )
    op.create_index('idx_ai_anomaly_number', 'ai_anomaly_detections', ['anomaly_number'])
    op.create_index('idx_ai_anomaly_type_status', 'ai_anomaly_detections', ['anomaly_type', 'status'])
    op.create_index('idx_ai_anomaly_severity', 'ai_anomaly_detections', ['severity'])
    op.create_index('idx_ai_anomaly_project', 'ai_anomaly_detections', ['project_id'])
    op.create_index('idx_ai_anomaly_account', 'ai_anomaly_detections', ['ad_account_id'])
    op.create_index('idx_ai_anomaly_date', 'ai_anomaly_detections', ['anomaly_date'])
    op.create_index('idx_ai_anomaly_created', 'ai_anomaly_detections', ['created_at'])
    op.create_index('idx_ai_anomaly_assigned', 'ai_anomaly_detections', ['assigned_to'])
    op.create_index('idx_ai_anomaly_deleted_at', 'ai_anomaly_detections', ['deleted_at'])

    # 创建 notifications 表
    op.create_table('notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('notification_number', sa.String(length=50), nullable=False, comment='通知编号'),
        sa.Column('title', sa.String(length=255), nullable=False, comment='通知标题'),
        sa.Column('content', sa.Text(), nullable=False, comment='通知内容'),
        sa.Column('summary', sa.String(length=500), nullable=True, comment='通知摘要'),
        sa.Column('notification_type', sa.Enum('system', 'anomaly', 'approval', 'reminder', 'report', 'maintenance', 'security', 'performance', name='notificationtype'), nullable=False, comment='通知类型'),
        sa.Column('priority', sa.Enum('low', 'normal', 'high', 'urgent', name='notificationpriority'), default='normal', nullable=False, comment='优先级'),
        sa.Column('category', sa.String(length=50), nullable=True, comment='业务分类'),
        sa.Column('recipient_id', postgresql.UUID(as_uuid=True), nullable=False, comment='接收人ID'),
        sa.Column('recipient_role', sa.String(length=50), nullable=True, comment='接收人角色'),
        sa.Column('recipient_email', sa.String(length=255), nullable=True, comment='接收人邮箱'),
        sa.Column('recipient_phone', sa.String(length=20), nullable=True, comment='接收人电话'),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=True, comment='发送人ID'),
        sa.Column('sender_name', sa.String(length=255), nullable=True, comment='发送人姓名'),
        sa.Column('is_system_notification', sa.Boolean(), nullable=True, default=sa.text('false'), comment='是否系统通知'),
        sa.Column('channels', sa.JSON(), nullable=False, comment='发送渠道配置'),
        sa.Column('primary_channel', sa.Enum('in_app', 'email', 'sms', 'webhook', 'browser', 'slack', 'wechat', name='notificationchannel'), nullable=False, comment='主要渠道'),
        sa.Column('related_entity_type', sa.String(length=50), nullable=True, comment='关联实体类型'),
        sa.Column('related_entity_id', postgresql.UUID(as_uuid=True), nullable=True, comment='关联实体ID'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True, comment='项目ID'),
        sa.Column('ad_account_id', postgresql.UUID(as_uuid=True), nullable=True, comment='广告账户ID'),
        sa.Column('status', sa.Enum('pending', 'sending', 'sent', 'delivered', 'read', 'failed', 'cancelled', name='notificationstatus'), default='pending', nullable=False, comment='通知状态'),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True, comment='计划发送时间'),
        sa.Column('sent_at', sa.DateTime(), nullable=True, comment='发送时间'),
        sa.Column('read_at', sa.DateTime(), nullable=True, comment='阅读时间'),
        sa.Column('expires_at', sa.DateTime(), nullable=True, comment='过期时间'),
        sa.Column('delivery_attempts', sa.Integer(), nullable=True, default=sa.text('0'), comment='发送尝试次数'),
        sa.Column('last_error', sa.Text(), nullable=True, comment='最后错误信息'),
        sa.Column('delivery_details', sa.JSON(), nullable=True, comment='发送详情'),
        sa.Column('action_buttons', sa.JSON(), nullable=True, comment='动作按钮配置'),
        sa.Column('action_url', sa.String(length=500), nullable=True, comment='动作链接'),
        sa.Column('action_required', sa.Boolean(), nullable=True, default=sa.text('false'), comment='是否需要动作'),
        sa.Column('template_name', sa.String(length=100), nullable=True, comment='模板名称'),
        sa.Column('template_parameters', sa.JSON(), nullable=True, comment='模板参数'),
        sa.Column('batch_id', sa.String(length=100), nullable=True, comment='批次ID'),
        sa.Column('is_batch_notification', sa.Boolean(), nullable=True, default=sa.text('false'), comment='是否批量通知'),
        sa.Column('metadata', sa.JSON(), nullable=True, comment='元数据'),
        sa.Column('context_data', sa.JSON(), nullable=True, comment='上下文数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True, comment='软删除时间'),
        sa.CheckConstraint('notification_type IN (\'system\', \'anomaly\', \'approval\', \'reminder\', \'report\', \'maintenance\', \'security\', \'performance\')', name='ck_notifications_type'),
        sa.CheckConstraint('priority IN (\'low\', \'normal\', \'high\', \'urgent\')', name='ck_notifications_priority'),
        sa.CheckConstraint('status IN (\'pending\', \'sending\', \'sent\', \'delivered\', \'read\', \'failed\', \'cancelled\')', name='ck_notifications_status'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('notification_number', name='uq_notifications_number'),
        comment='通知表 - 统一管理所有系统通知'
    )
    op.create_index('idx_notification_number', 'notifications', ['notification_number'])
    op.create_index('idx_notification_recipient', 'notifications', ['recipient_id'])
    op.create_index('idx_notification_type_status', 'notifications', ['notification_type', 'status'])
    op.create_index('idx_notification_priority', 'notifications', ['priority'])
    op.create_index('idx_notification_channel', 'notifications', ['primary_channel'])
    op.create_index('idx_notification_project', 'notifications', ['project_id'])
    op.create_index('idx_notification_account', 'notifications', ['ad_account_id'])
    op.create_index('idx_notification_created', 'notifications', ['created_at'])
    op.create_index('idx_notification_scheduled', 'notifications', ['scheduled_at'])
    op.create_index('idx_notification_read', 'notifications', ['read_at'])
    op.create_index('idx_notification_deleted_at', 'notifications', ['deleted_at'])

    # 创建 system_configs 表
    op.create_table('system_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('config_key', sa.String(length=100), nullable=False, comment='配置键'),
        sa.Column('config_name', sa.String(length=255), nullable=False, comment='配置名称'),
        sa.Column('config_description', sa.Text(), nullable=True, comment='配置描述'),
        sa.Column('category', sa.String(length=50), nullable=False, comment='配置分类'),
        sa.Column('subcategory', sa.String(length=50), nullable=True, comment='子分类'),
        sa.Column('config_value', sa.JSON(), nullable=True, comment='配置值'),
        sa.Column('default_value', sa.JSON(), nullable=True, comment='默认值'),
        sa.Column('data_type', sa.String(length=20), nullable=True, default='string', comment='数据类型'),
        sa.Column('is_required', sa.Boolean(), nullable=True, default=sa.text('false'), comment='是否必需'),
        sa.Column('is_encrypted', sa.Boolean(), nullable=True, default=sa.text('false'), comment='是否加密'),
        sa.Column('is_readonly', sa.Boolean(), nullable=True, default=sa.text('false'), comment='是否只读'),
        sa.Column('validation_rules', sa.JSON(), nullable=True, comment='验证规则'),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=sa.text('true'), comment='是否启用'),
        sa.Column('environment', sa.String(length=20), nullable=True, default='production', comment='环境: development, staging, production'),
        sa.Column('access_roles', sa.JSON(), nullable=True, comment='访问角色'),
        sa.Column('edit_roles', sa.JSON(), nullable=True, comment='编辑角色'),
        sa.Column('version', sa.Integer(), nullable=True, default=sa.text('1'), comment='配置版本'),
        sa.Column('previous_value', sa.JSON(), nullable=True, comment='之前的值'),
        sa.Column('cache_ttl', sa.Integer(), nullable=True, comment='缓存时间（秒）'),
        sa.Column('cache_key', sa.String(length=255), nullable=True, comment='缓存键'),
        sa.Column('last_accessed_at', sa.DateTime(), nullable=True, comment='最后访问时间'),
        sa.Column('access_count', sa.Integer(), nullable=True, default=sa.text('0'), comment='访问次数'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False, comment='创建人'),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True, comment='更新人'),
        sa.Column('change_reason', sa.Text(), nullable=True, comment='变更原因'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True, comment='软删除时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('config_key', name='uq_config_key'),
        comment='系统配置表 - 管理系统全局配置'
    )
    op.create_index('idx_config_key', 'system_configs', ['config_key'])
    op.create_index('idx_config_category', 'system_configs', ['category'])
    op.create_index('idx_config_subcategory', 'system_configs', ['subcategory'])
    op.create_index('idx_config_active', 'system_configs', ['is_active'])
    op.create_index('idx_config_environment', 'system_configs', ['environment'])
    op.create_index('idx_config_created', 'system_configs', ['created_at'])
    op.create_index('idx_config_updated', 'system_configs', ['updated_at'])
    op.create_index('idx_config_deleted_at', 'system_configs', ['deleted_at'])

    # 创建 audit_logs 表
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('log_number', sa.String(length=50), nullable=False, comment='日志编号'),
        sa.Column('action', sa.String(length=100), nullable=False, comment='操作动作'),
        sa.Column('action_type', sa.String(length=50), nullable=False, comment='操作类型'),
        sa.Column('action_category', sa.String(length=50), nullable=False, comment='操作分类'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='操作人ID'),
        sa.Column('user_email', sa.String(length=255), nullable=False, comment='操作人邮箱'),
        sa.Column('user_role', sa.String(length=50), nullable=False, comment='操作人角色'),
        sa.Column('user_ip', sa.String(length=45), nullable=True, comment='操作人IP'),
        sa.Column('user_agent', sa.String(length=500), nullable=True, comment='用户代理'),
        sa.Column('target_entity_type', sa.String(length=50), nullable=False, comment='目标实体类型'),
        sa.Column('target_entity_id', postgresql.UUID(as_uuid=True), nullable=True, comment='目标实体ID'),
        sa.Column('target_entity_name', sa.String(length=255), nullable=True, comment='目标实体名称'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True, comment='项目ID'),
        sa.Column('ad_account_id', postgresql.UUID(as_uuid=True), nullable=True, comment='广告账户ID'),
        sa.Column('channel_id', postgresql.UUID(as_uuid=True), nullable=True, comment='渠道ID'),
        sa.Column('operation_status', sa.String(length=20), nullable=True, default='success', comment='操作状态: success, failure, partial'),
        sa.Column('result_message', sa.Text(), nullable=True, comment='操作结果消息'),
        sa.Column('error_code', sa.String(length=50), nullable=True, comment='错误代码'),
        sa.Column('error_details', sa.Text(), nullable=True, comment='错误详情'),
        sa.Column('old_values', sa.JSON(), nullable=True, comment='变更前值'),
        sa.Column('new_values', sa.JSON(), nullable=True, comment='变更后值'),
        sa.Column('changed_fields', sa.JSON(), nullable=True, comment='变更字段列表'),
        sa.Column('business_context', sa.JSON(), nullable=True, comment='业务上下文'),
        sa.Column('request_id', sa.String(length=100), nullable=True, comment='请求ID'),
        sa.Column('session_id', sa.String(length=100), nullable=True, comment='会话ID'),
        sa.Column('risk_level', sa.String(length=20), nullable=True, default='low', comment='风险级别: low, medium, high, critical'),
        sa.Column('security_flags', sa.JSON(), nullable=True, comment='安全标志'),
        sa.Column('compliance_checks', sa.JSON(), nullable=True, comment='合规检查结果'),
        sa.Column('application', sa.String(length=50), nullable=True, default='ai_ad_spend', comment='应用名称'),
        sa.Column('module', sa.String(length=50), nullable=True, comment='模块名称'),
        sa.Column('function', sa.String(length=100), nullable=True, comment='函数名称'),
        sa.Column('api_endpoint', sa.String(length=255), nullable=True, comment='API端点'),
        sa.Column('operation_time', sa.DateTime(), nullable=False, comment='操作时间'),
        sa.Column('duration_ms', sa.Integer(), nullable=True, comment='操作耗时（毫秒）'),
        sa.Column('metadata', sa.JSON(), nullable=True, comment='元数据'),
        sa.Column('tags', sa.JSON(), nullable=True, comment='标签'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('log_number', name='uq_audit_log_number'),
        comment='审计日志表 - 记录所有重要操作的审计信息'
    )
    op.create_index('idx_audit_log_number', 'audit_logs', ['log_number'])
    op.create_index('idx_audit_user', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_action', 'audit_logs', ['action', 'action_type'])
    op.create_index('idx_audit_target', 'audit_logs', ['target_entity_type', 'target_entity_id'])
    op.create_index('idx_audit_project', 'audit_logs', ['project_id'])
    op.create_index('idx_audit_status', 'audit_logs', ['operation_status'])
    op.create_index('idx_audit_risk', 'audit_logs', ['risk_level'])
    op.create_index('idx_audit_time', 'audit_logs', ['operation_time'])
    op.create_index('idx_audit_application', 'audit_logs', ['application'])
    op.create_index('idx_audit_request', 'audit_logs', ['request_id'])
    op.create_index('idx_audit_created', 'audit_logs', ['created_at'])


def downgrade() -> None:
    # 删除表（按依赖关系反向删除）
    op.drop_table('audit_logs')
    op.drop_table('system_configs')
    op.drop_table('notifications')
    op.drop_table('ai_anomaly_detections')
    op.drop_table('reconciliation_batches')
    op.drop_table('account_balances')
    op.drop_table('ledger_transactions')