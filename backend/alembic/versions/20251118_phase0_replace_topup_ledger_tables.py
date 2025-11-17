"""Phase 0: 清理废弃表并创建符合 DATA_SCHEMA v5.0 的新表

Revision ID: 20251118_phase0
Revises:
Create Date: 2025-11-18 16:00:00.000000

说明：
- DROP 废弃单表设计：topups, ledgers
- CREATE 新的多表设计：
  * topup_requests (充值申请)
  * topup_transactions (充值到账流水)
  * topup_approval_logs (充值审批日志)
  * ledger_entries (资金总账)
- 所有时间字段使用 TIMESTAMPTZ
- 主键使用 BIGSERIAL
- 外键类型对齐 DATA_SCHEMA（项目/账户 BIGINT，用户 UUID）

风险：低（废弃表为空表，无数据丢失风险）
回滚：可完全回滚（重建废弃表结构）
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '20251118_phase0'
down_revision = None  # 这是第一个 Alembic 迁移
branch_labels = None
depends_on = None


def upgrade():
    """升级函数：清理废弃表，创建新表"""

    # ========== 第1步：DROP 废弃表 ==========
    print("  [Phase 0 - Step 1/5] Dropping deprecated tables...")

    # 删除废弃的单表设计（已确认为空表）
    op.execute("DROP TABLE IF EXISTS topups CASCADE;")
    op.execute("DROP TABLE IF EXISTS ledgers CASCADE;")

    print("    [OK] Dropped: topups, ledgers")
    print()

    # ========== 第2步：CREATE topup_requests ==========
    print("  [Phase 0 - Step 2/5] Creating topup_requests table...")

    op.create_table(
        'topup_requests',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='充值申请ID'),
        sa.Column('request_no', sa.String(50), nullable=False, comment='申请单号'),
        sa.Column('project_id', sa.BigInteger(), nullable=False, comment='项目ID'),
        sa.Column('ad_account_id', sa.BigInteger(), nullable=True, comment='广告账户ID'),
        sa.Column('applicant_id', UUID(as_uuid=True), nullable=False, comment='申请人ID'),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False, comment='申请金额'),
        sa.Column('currency', sa.String(10), nullable=False, server_default='CNY', comment='货币类型'),
        sa.Column('urgency_level', sa.String(20), nullable=False, server_default='normal', comment='紧急程度: low/normal/high/urgent'),
        sa.Column('status', sa.String(20), nullable=False, comment='申请状态（以 STATE_MACHINE.md 为准）'),
        sa.Column('status_reason', sa.Text(), nullable=True, comment='状态变更原因'),
        sa.Column('expected_pay_date', sa.Date(), nullable=True, comment='期望到账日期'),
        sa.Column('voucher_url', sa.Text(), nullable=True, comment='凭证URL'),
        sa.Column('notes', sa.Text(), nullable=True, comment='补充说明'),
        sa.Column('created_by', UUID(as_uuid=True), nullable=True, comment='创建人ID'),
        sa.Column('updated_by', UUID(as_uuid=True), nullable=True, comment='更新人ID'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='创建时间'),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['ad_account_id'], ['ad_accounts.id'], ),
        sa.ForeignKeyConstraint(['applicant_id'], ['user_profiles.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['user_profiles.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['user_profiles.id'], ),
        sa.UniqueConstraint('request_no'),
        comment='充值申请表'
    )

    # 创建索引（对齐 DATA_SCHEMA 3.4.1）
    op.create_index('idx_topup_requests_project', 'topup_requests', ['project_id'])
    op.create_index('idx_topup_requests_status', 'topup_requests', ['status'])
    op.create_index('idx_topup_requests_applicant', 'topup_requests', ['applicant_id'])

    print("    [OK] Created: topup_requests + 3 indexes")
    print()

    # ========== 第3步：CREATE topup_transactions ==========
    print("  [Phase 0 - Step 3/5] Creating topup_transactions table...")

    op.create_table(
        'topup_transactions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='交易ID'),
        sa.Column('topup_request_id', sa.BigInteger(), nullable=False, comment='关联的申请ID'),
        sa.Column('paid_amount', sa.Numeric(15, 2), nullable=False, comment='实际打款金额'),
        sa.Column('paid_currency', sa.String(10), nullable=False, comment='货币类型'),
        sa.Column('payment_method', sa.String(50), nullable=False, comment='支付方式: bank_transfer/alipay/wechat/paypal/credit_card/other'),
        sa.Column('payment_reference', sa.String(100), nullable=True, comment='支付参考号'),
        sa.Column('paid_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='打款时间'),
        sa.Column('receipt_url', sa.Text(), nullable=True, comment='凭证URL'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注'),
        sa.Column('created_by', UUID(as_uuid=True), nullable=True, comment='创建人ID'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='创建时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['topup_request_id'], ['topup_requests.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['user_profiles.id'], ),
        comment='充值交易记录表'
    )

    # 创建索引
    op.create_index('idx_topup_transactions_request', 'topup_transactions', ['topup_request_id'])
    op.create_index('idx_topup_transactions_paid_at', 'topup_transactions', ['paid_at'])

    print("    [OK] Created: topup_transactions + 2 indexes")
    print()

    # ========== 第4步：CREATE topup_approval_logs ==========
    print("  [Phase 0 - Step 4/5] Creating topup_approval_logs table...")

    op.create_table(
        'topup_approval_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='日志ID'),
        sa.Column('topup_request_id', sa.BigInteger(), nullable=False, comment='关联的申请ID'),
        sa.Column('action', sa.String(50), nullable=False, comment='操作类型'),
        sa.Column('from_status', sa.String(20), nullable=True, comment='原状态'),
        sa.Column('to_status', sa.String(20), nullable=True, comment='新状态'),
        sa.Column('operator_id', UUID(as_uuid=True), nullable=False, comment='操作人ID'),
        sa.Column('comments', sa.Text(), nullable=True, comment='操作说明'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='创建时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['topup_request_id'], ['topup_requests.id'], ),
        sa.ForeignKeyConstraint(['operator_id'], ['user_profiles.id'], ),
        comment='充值审批日志表'
    )

    # 创建索引
    op.create_index('idx_topup_approval_logs_request', 'topup_approval_logs', ['topup_request_id'])
    op.create_index('idx_topup_approval_logs_action', 'topup_approval_logs', ['action'])
    op.create_index('idx_topup_approval_logs_operator', 'topup_approval_logs', ['operator_id'])

    print("    [OK] Created: topup_approval_logs + 3 indexes")
    print()

    # ========== 第5步：CREATE ledger_entries ==========
    print("  [Phase 0 - Step 5/5] Creating ledger_entries table...")

    op.create_table(
        'ledger_entries',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='账本条目ID'),
        sa.Column('project_id', sa.BigInteger(), nullable=False, comment='项目ID'),
        sa.Column('ad_account_id', sa.BigInteger(), nullable=True, comment='广告账户ID'),
        sa.Column('entry_type', sa.String(20), nullable=False, comment='条目类型: topup_received/spend/adjustment/...'),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False, comment='金额（借方为正，贷方为负）'),
        sa.Column('currency', sa.String(10), nullable=False, comment='货币类型'),
        sa.Column('reference_id', sa.BigInteger(), nullable=True, comment='关联ID（topup_transactions 或 daily_reports）'),
        sa.Column('occurred_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='发生时间'),
        sa.Column('created_by', UUID(as_uuid=True), nullable=True, comment='创建人ID'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注说明'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['ad_account_id'], ['ad_accounts.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['user_profiles.id'], ),
        comment='资金总账表'
    )

    # 创建索引（对齐 DATA_SCHEMA 3.4.4）
    op.create_index('idx_ledger_project', 'ledger_entries', ['project_id'])
    op.create_index('idx_ledger_account', 'ledger_entries', ['ad_account_id'])
    op.create_index('idx_ledger_entry_type', 'ledger_entries', ['entry_type'])

    print("    [OK] Created: ledger_entries + 3 indexes")
    print()

    print("  [Phase 0] Upgrade completed!")
    print("    - Dropped: 2 tables (topups, ledgers)")
    print("    - Created: 4 tables (topup_requests, topup_transactions, topup_approval_logs, ledger_entries)")
    print("    - Created: 11 indexes")


def downgrade():
    """回滚函数：删除新表，重建废弃表（仅结构）"""

    print("  [Phase 0 Rollback - Step 1/2] Dropping new tables...")

    # 删除新表（级联删除外键约束）
    op.drop_table('ledger_entries')
    op.drop_table('topup_approval_logs')
    op.drop_table('topup_transactions')
    op.drop_table('topup_requests')

    print("    [OK] Dropped all new tables")
    print()

    print("  [Phase 0 Rollback - Step 2/2] Recreating deprecated tables (structure only)...")

    # 重建废弃表结构（仅用于回滚，不包含数据）
    op.execute("""
        CREATE TABLE topups (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            ad_account_id UUID,
            project_id UUID,
            channel_id UUID,
            requested_by UUID,
            amount NUMERIC(15,2) NOT NULL,
            service_fee_amount NUMERIC(15,2),
            status TEXT NOT NULL DEFAULT 'pending',
            remark TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            urgency_level VARCHAR DEFAULT 'normal'
        );
    """)

    op.execute("""
        CREATE TABLE ledgers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            type TEXT NOT NULL,
            project_id UUID,
            channel_id UUID,
            ad_account_id UUID,
            amount NUMERIC(15,2) NOT NULL,
            currency TEXT NOT NULL DEFAULT 'USD',
            occurred_at TIMESTAMPTZ NOT NULL,
            remark TEXT,
            created_by UUID,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            status VARCHAR DEFAULT 'pending',
            verified_by UUID,
            verified_at TIMESTAMPTZ,
            verification_notes TEXT
        );
    """)

    print("    [OK] Recreated: topups, ledgers (empty tables)")
    print()
    print("  [Phase 0] Rollback completed!")
