"""Phase 1: Financial SoT 核心表结构

Revision ID: 20251219_phase1_financial_sot_tables
Revises: 20251120_fix_reconciliation_batch_constraint_p0
Create Date: 2025-12-19

根据 FINANCIAL_SOT_DESIGN.md v1.0 和 FINANCIAL_REFACTOR_PLAN.md Phase 1 要求：
1. 新增 teams 表 (团队)
2. 新增 buyers 表 (投手)
3. 新增 financial_events 表 (财务事件)
4. 新增 balance_snapshots 表 (余额快照)
5. 扩展 suppliers 表 (添加 fee_rate, fee_type, platform)
6. 扩展 ad_accounts 表 (添加 buyer_id, team_id)
7. 扩展 ledger_entries 表 (添加 entity_type, entity_id, event_id, idempotency_key)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251219_phase1_financial_sot_tables'
down_revision = '20251120_fix_reconciliation_batch_constraint_p0'
branch_labels = None
depends_on = None


def upgrade():
    """
    Phase 1 升级脚本

    执行顺序：
    1. 创建 teams 表
    2. 创建 buyers 表 (依赖 teams)
    3. 创建 financial_events 表 (依赖 teams, buyers, suppliers, ad_accounts, projects)
    4. 创建 balance_snapshots 表
    5. 扩展 suppliers 表
    6. 扩展 ad_accounts 表 (依赖 teams, buyers)
    7. 扩展 ledger_entries 表 (依赖 financial_events)
    """

    # ========== 1. 创建 teams 表 ==========
    op.create_table(
        'teams',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()'), comment='团队ID'),
        sa.Column('code', sa.String(10), unique=True, nullable=False, comment='团队代码 (SZ/ZZ)'),
        sa.Column('name', sa.String(100), nullable=True, comment='团队名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='团队描述'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active', comment='状态'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now(), comment='更新时间'),

        sa.CheckConstraint("status IN ('active', 'inactive')", name='chk_teams_status'),
    )
    op.create_index('idx_teams_code', 'teams', ['code'])
    op.create_index('idx_teams_status', 'teams', ['status'])

    # ========== 2. 创建 buyers 表 ==========
    op.create_table(
        'buyers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()'), comment='投手ID'),
        sa.Column('code', sa.String(20), unique=True, nullable=False, comment='投手代码'),
        sa.Column('name', sa.String(100), nullable=True, comment='投手姓名'),
        sa.Column('team_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('teams.id', ondelete='SET NULL'), nullable=True, comment='所属团队'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='关联用户'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active', comment='状态'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now(), comment='更新时间'),

        sa.CheckConstraint("status IN ('active', 'inactive')", name='chk_buyers_status'),
    )
    op.create_index('idx_buyers_code', 'buyers', ['code'])
    op.create_index('idx_buyers_team_id', 'buyers', ['team_id'])
    op.create_index('idx_buyers_user_id', 'buyers', ['user_id'])
    op.create_index('idx_buyers_status', 'buyers', ['status'])

    # ========== 3. 创建 financial_events 表 ==========
    op.create_table(
        'financial_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()'), comment='事件ID'),

        # 事件类型和状态
        sa.Column('event_type', sa.String(20), nullable=False, comment='事件类型'),
        sa.Column('event_status', sa.String(20), nullable=False, server_default='raw', comment='事件状态'),

        # 来源追溯
        sa.Column('source_type', sa.String(50), nullable=True, comment='来源类型 (excel_import/api/manual)'),
        sa.Column('source_ref', sa.String(255), nullable=True, comment='来源引用 (文件名/API调用ID)'),
        sa.Column('idempotency_key', sa.String(255), unique=True, nullable=False, comment='幂等键'),

        # 金额字段
        sa.Column('amount', sa.Numeric(18, 4), nullable=False, comment='金额'),
        sa.Column('fee_amount', sa.Numeric(18, 4), nullable=False, server_default='0', comment='手续费'),
        sa.Column('gross_amount', sa.Numeric(18, 4), nullable=True, comment='含费金额'),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD', comment='币种'),
        sa.Column('event_date', sa.Date(), nullable=False, comment='事件日期'),

        # 关联实体
        sa.Column('team_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('teams.id', ondelete='SET NULL'), nullable=True, comment='团队ID'),
        sa.Column('buyer_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('buyers.id', ondelete='SET NULL'), nullable=True, comment='投手ID'),
        sa.Column('supplier_id', sa.BigInteger(),
                  sa.ForeignKey('suppliers.id', ondelete='SET NULL'), nullable=True, comment='供应商ID'),
        sa.Column('ad_account_id', sa.BigInteger(),
                  sa.ForeignKey('ad_accounts.id', ondelete='SET NULL'), nullable=True, comment='广告账户ID'),
        sa.Column('project_id', sa.BigInteger(),
                  sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, comment='项目ID'),

        # 扩展数据
        sa.Column('payload', postgresql.JSONB(), nullable=False, server_default='{}', comment='扩展数据'),

        # 审计字段
        sa.Column('created_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='创建者'),
        sa.Column('confirmed_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='确认者'),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True, comment='确认时间'),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=True, comment='入账时间'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now(), comment='更新时间'),

        # 约束
        sa.CheckConstraint(
            "event_type IN ('TOPUP', 'SPEND', 'PAYMENT', 'TRANSFER', 'ADJUSTMENT', 'FEE', 'REFUND')",
            name='chk_financial_events_event_type'
        ),
        sa.CheckConstraint(
            "event_status IN ('raw', 'pending', 'confirmed', 'posted', 'reversed')",
            name='chk_financial_events_event_status'
        ),
    )

    # 索引
    op.create_index('idx_fin_events_type_status', 'financial_events', ['event_type', 'event_status'])
    op.create_index('idx_fin_events_event_date', 'financial_events', ['event_date'])
    op.create_index('idx_fin_events_supplier_id', 'financial_events', ['supplier_id'])
    op.create_index('idx_fin_events_ad_account_id', 'financial_events', ['ad_account_id'])
    op.create_index('idx_fin_events_project_id', 'financial_events', ['project_id'])
    op.create_index('idx_fin_events_team_id', 'financial_events', ['team_id'])
    op.create_index('idx_fin_events_buyer_id', 'financial_events', ['buyer_id'])
    op.create_index('idx_fin_events_idempotency_key', 'financial_events', ['idempotency_key'])
    op.create_index('idx_fin_events_created_at', 'financial_events', ['created_at'])

    # ========== 4. 创建 balance_snapshots 表 ==========
    op.create_table(
        'balance_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()'), comment='快照ID'),
        sa.Column('entity_type', sa.String(20), nullable=False, comment='实体类型'),
        sa.Column('entity_id', sa.String(100), nullable=False, comment='实体ID'),
        sa.Column('snapshot_date', sa.Date(), nullable=False, comment='快照日期'),

        # 余额数据
        sa.Column('balance', sa.Numeric(18, 4), nullable=False, comment='当前余额'),
        sa.Column('total_debit', sa.Numeric(18, 4), nullable=False, server_default='0', comment='累计借方'),
        sa.Column('total_credit', sa.Numeric(18, 4), nullable=False, server_default='0', comment='累计贷方'),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD', comment='币种'),

        # 计算时间
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), comment='计算时间'),

        # 约束
        sa.CheckConstraint(
            "entity_type IN ('SUPPLIER', 'PROJECT', 'ACCOUNT', 'TEAM')",
            name='chk_balance_snapshots_entity_type'
        ),
        sa.UniqueConstraint('entity_type', 'entity_id', 'snapshot_date', name='uq_balance_snapshots_entity_date'),
    )

    op.create_index('idx_balance_snapshots_entity', 'balance_snapshots', ['entity_type', 'entity_id'])
    op.create_index('idx_balance_snapshots_date', 'balance_snapshots', ['snapshot_date'])

    # ========== 5. 扩展 suppliers 表 ==========
    op.add_column('suppliers', sa.Column('fee_rate', sa.Numeric(5, 4), nullable=True,
                                          server_default='0.1000', comment='手续费率 (0.01-0.15)'))
    op.add_column('suppliers', sa.Column('fee_type', sa.String(20), nullable=True,
                                          server_default='PERCENTAGE', comment='费率类型'))
    op.add_column('suppliers', sa.Column('platform', sa.String(20), nullable=True,
                                          comment='平台 (FB/TK/Google)'))

    # 添加约束
    op.create_check_constraint(
        'chk_suppliers_fee_type',
        'suppliers',
        "fee_type IN ('PERCENTAGE', 'FIXED') OR fee_type IS NULL"
    )
    op.create_check_constraint(
        'chk_suppliers_fee_rate_range',
        'suppliers',
        "(fee_rate >= 0 AND fee_rate <= 1) OR fee_rate IS NULL"
    )

    # ========== 6. 扩展 ad_accounts 表 ==========
    op.add_column('ad_accounts', sa.Column('buyer_id', postgresql.UUID(as_uuid=True), nullable=True,
                                            comment='投手ID'))
    op.add_column('ad_accounts', sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=True,
                                            comment='团队ID'))
    op.add_column('ad_accounts', sa.Column('supplier_id', sa.BigInteger(), nullable=True,
                                            comment='供应商ID'))
    op.add_column('ad_accounts', sa.Column('account_type', sa.String(50), nullable=True,
                                            comment='账户类型 (美金户/越南盾户/企业户...)'))
    op.add_column('ad_accounts', sa.Column('platform', sa.String(20), nullable=True,
                                            comment='平台 (FB/TK/Google)'))
    op.add_column('ad_accounts', sa.Column('region', sa.String(50), nullable=True,
                                            comment='地区'))

    # 添加外键
    op.create_foreign_key(
        'fk_ad_accounts_buyer_id',
        'ad_accounts', 'buyers',
        ['buyer_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_ad_accounts_team_id',
        'ad_accounts', 'teams',
        ['team_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_ad_accounts_supplier_id',
        'ad_accounts', 'suppliers',
        ['supplier_id'], ['id'],
        ondelete='SET NULL'
    )

    # 添加索引
    op.create_index('idx_ad_accounts_buyer_id', 'ad_accounts', ['buyer_id'])
    op.create_index('idx_ad_accounts_team_id', 'ad_accounts', ['team_id'])
    op.create_index('idx_ad_accounts_supplier_id', 'ad_accounts', ['supplier_id'])
    op.create_index('idx_ad_accounts_platform', 'ad_accounts', ['platform'])

    # ========== 7. 扩展 ledger_entries 表 ==========
    op.add_column('ledger_entries', sa.Column('entity_type', sa.String(20), nullable=True,
                                               comment='实体类型 (SUPPLIER/PROJECT/ACCOUNT/TEAM)'))
    op.add_column('ledger_entries', sa.Column('entity_id', sa.String(100), nullable=True,
                                               comment='实体ID'))
    op.add_column('ledger_entries', sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=True,
                                               comment='财务事件ID'))
    op.add_column('ledger_entries', sa.Column('idempotency_key', sa.String(255), nullable=True,
                                               comment='幂等键'))
    op.add_column('ledger_entries', sa.Column('direction', sa.String(10), nullable=True,
                                               comment='方向 (DEBIT/CREDIT)'))

    # 添加外键
    op.create_foreign_key(
        'fk_ledger_entries_event_id',
        'ledger_entries', 'financial_events',
        ['event_id'], ['id'],
        ondelete='SET NULL'
    )

    # 添加索引
    op.create_index('idx_ledger_entries_entity', 'ledger_entries', ['entity_type', 'entity_id'])
    op.create_index('idx_ledger_entries_event_id', 'ledger_entries', ['event_id'])
    op.create_index(
        'idx_ledger_entries_idempotency_key',
        'ledger_entries',
        ['idempotency_key'],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL")
    )

    # 添加约束
    op.create_check_constraint(
        'chk_ledger_entries_entity_type',
        'ledger_entries',
        "entity_type IN ('SUPPLIER', 'PROJECT', 'ACCOUNT', 'TEAM') OR entity_type IS NULL"
    )
    op.create_check_constraint(
        'chk_ledger_entries_direction',
        'ledger_entries',
        "direction IN ('DEBIT', 'CREDIT') OR direction IS NULL"
    )

    # ========== 8. 回填现有数据的 entity_type ==========
    # 注意：这是一个数据迁移，根据现有的业务逻辑设置 entity_type
    # 由于现有 ledger_entries 是通过 ad_account_id 关联的，默认设为 ACCOUNT
    op.execute("""
        UPDATE ledger_entries
        SET entity_type = 'ACCOUNT',
            entity_id = ad_account_id::varchar
        WHERE entity_type IS NULL AND ad_account_id IS NOT NULL
    """)

    # ========== 9. 插入初始团队数据 ==========
    op.execute("""
        INSERT INTO teams (code, name, description) VALUES
        ('SZ', '深圳团队', '深圳运营团队'),
        ('ZZ', 'ZZ团队', 'ZZ运营团队')
        ON CONFLICT (code) DO NOTHING
    """)


def downgrade():
    """
    Phase 1 回滚脚本

    按相反顺序删除所有变更
    """

    # ========== 7. 回滚 ledger_entries 扩展 ==========
    op.drop_constraint('chk_ledger_entries_direction', 'ledger_entries', type_='check')
    op.drop_constraint('chk_ledger_entries_entity_type', 'ledger_entries', type_='check')
    op.drop_index('idx_ledger_entries_idempotency_key', table_name='ledger_entries')
    op.drop_index('idx_ledger_entries_event_id', table_name='ledger_entries')
    op.drop_index('idx_ledger_entries_entity', table_name='ledger_entries')
    op.drop_constraint('fk_ledger_entries_event_id', 'ledger_entries', type_='foreignkey')
    op.drop_column('ledger_entries', 'direction')
    op.drop_column('ledger_entries', 'idempotency_key')
    op.drop_column('ledger_entries', 'event_id')
    op.drop_column('ledger_entries', 'entity_id')
    op.drop_column('ledger_entries', 'entity_type')

    # ========== 6. 回滚 ad_accounts 扩展 ==========
    op.drop_index('idx_ad_accounts_platform', table_name='ad_accounts')
    op.drop_index('idx_ad_accounts_supplier_id', table_name='ad_accounts')
    op.drop_index('idx_ad_accounts_team_id', table_name='ad_accounts')
    op.drop_index('idx_ad_accounts_buyer_id', table_name='ad_accounts')
    op.drop_constraint('fk_ad_accounts_supplier_id', 'ad_accounts', type_='foreignkey')
    op.drop_constraint('fk_ad_accounts_team_id', 'ad_accounts', type_='foreignkey')
    op.drop_constraint('fk_ad_accounts_buyer_id', 'ad_accounts', type_='foreignkey')
    op.drop_column('ad_accounts', 'region')
    op.drop_column('ad_accounts', 'platform')
    op.drop_column('ad_accounts', 'account_type')
    op.drop_column('ad_accounts', 'supplier_id')
    op.drop_column('ad_accounts', 'team_id')
    op.drop_column('ad_accounts', 'buyer_id')

    # ========== 5. 回滚 suppliers 扩展 ==========
    op.drop_constraint('chk_suppliers_fee_rate_range', 'suppliers', type_='check')
    op.drop_constraint('chk_suppliers_fee_type', 'suppliers', type_='check')
    op.drop_column('suppliers', 'platform')
    op.drop_column('suppliers', 'fee_type')
    op.drop_column('suppliers', 'fee_rate')

    # ========== 4. 删除 balance_snapshots 表 ==========
    op.drop_index('idx_balance_snapshots_date', table_name='balance_snapshots')
    op.drop_index('idx_balance_snapshots_entity', table_name='balance_snapshots')
    op.drop_table('balance_snapshots')

    # ========== 3. 删除 financial_events 表 ==========
    op.drop_index('idx_fin_events_created_at', table_name='financial_events')
    op.drop_index('idx_fin_events_idempotency_key', table_name='financial_events')
    op.drop_index('idx_fin_events_buyer_id', table_name='financial_events')
    op.drop_index('idx_fin_events_team_id', table_name='financial_events')
    op.drop_index('idx_fin_events_project_id', table_name='financial_events')
    op.drop_index('idx_fin_events_ad_account_id', table_name='financial_events')
    op.drop_index('idx_fin_events_supplier_id', table_name='financial_events')
    op.drop_index('idx_fin_events_event_date', table_name='financial_events')
    op.drop_index('idx_fin_events_type_status', table_name='financial_events')
    op.drop_table('financial_events')

    # ========== 2. 删除 buyers 表 ==========
    op.drop_index('idx_buyers_status', table_name='buyers')
    op.drop_index('idx_buyers_user_id', table_name='buyers')
    op.drop_index('idx_buyers_team_id', table_name='buyers')
    op.drop_index('idx_buyers_code', table_name='buyers')
    op.drop_table('buyers')

    # ========== 1. 删除 teams 表 ==========
    op.drop_index('idx_teams_status', table_name='teams')
    op.drop_index('idx_teams_code', table_name='teams')
    op.drop_table('teams')
