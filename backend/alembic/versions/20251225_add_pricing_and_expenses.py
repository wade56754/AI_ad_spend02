"""add_pricing_and_expenses

Revision ID: 20251225_pricing
Revises: 20251225_add_user_team_id
Create Date: 2025-12-25

添加阶梯定价和公司支出功能:
- projects 表新增 price_rules (JSONB), default_currency
- 创建 company_expenses 表

SoT References:
- CORE_MODULES.md §4.5 阶梯价格规则
- LEDGER_SOT.md v1.1 账本规则
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251225_pricing'
down_revision = '20251225_add_user_team_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. 给 projects 表添加 price_rules 和 default_currency 字段
    op.add_column(
        'projects',
        sa.Column('price_rules', postgresql.JSONB, nullable=True,
                  comment='阶梯价格规则 JSON')
    )
    op.add_column(
        'projects',
        sa.Column('default_currency', sa.String(10), server_default='USD', nullable=True,
                  comment='项目默认币种')
    )

    # 2. 创建 company_expenses 表
    op.create_table(
        'company_expenses',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='支出ID'),
        sa.Column('expense_type', sa.String(50), nullable=False, comment='支出类型'),
        sa.Column('category', sa.String(50), nullable=False, comment='分类'),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False, comment='金额'),
        sa.Column('currency', sa.String(10), server_default='USD', nullable=True, comment='币种'),
        sa.Column('occurred_at', sa.Date(), nullable=False, comment='发生日期'),
        sa.Column('description', sa.Text(), nullable=True, comment='描述'),
        sa.Column('receipt_url', sa.Text(), nullable=True, comment='收据URL'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True, comment='创建人'),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True, comment='审批人'),
        sa.Column('status', sa.String(20), server_default='pending', nullable=True, comment='状态'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_company_expenses_created_by'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], name='fk_company_expenses_approved_by'),
        sa.CheckConstraint(
            "category IN ('operation', 'hr', 'infrastructure', 'tools', 'other')",
            name='chk_company_expenses_category'
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'paid')",
            name='chk_company_expenses_status'
        ),
        comment='公司级运营支出（非广告业务）'
    )

    # 3. 创建索引
    op.create_index('idx_company_expenses_category', 'company_expenses', ['category'])
    op.create_index('idx_company_expenses_occurred_at', 'company_expenses', ['occurred_at'])
    op.create_index('idx_company_expenses_status', 'company_expenses', ['status'])
    op.create_index('idx_company_expenses_created_by', 'company_expenses', ['created_by'])


def downgrade() -> None:
    # 1. 删除索引
    op.drop_index('idx_company_expenses_created_by', 'company_expenses')
    op.drop_index('idx_company_expenses_status', 'company_expenses')
    op.drop_index('idx_company_expenses_occurred_at', 'company_expenses')
    op.drop_index('idx_company_expenses_category', 'company_expenses')

    # 2. 删除 company_expenses 表
    op.drop_table('company_expenses')

    # 3. 删除 projects 表的新字段
    op.drop_column('projects', 'default_currency')
    op.drop_column('projects', 'price_rules')
