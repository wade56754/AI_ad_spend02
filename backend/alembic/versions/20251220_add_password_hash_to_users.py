"""添加 password_hash 字段到 users 表 - 支持本地 JWT 认证

Revision ID: 20251220_add_password_hash_to_users
Revises: 20251219_phase1_financial_sot_tables
Create Date: 2025-12-20

替代 Supabase Auth，使用本地 JWT 认证：
1. 添加 password_hash 字段存储 bcrypt 加密的密码
2. 密码验证由 LocalAuthService 处理
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251220_add_password_hash_to_users'
down_revision = '20251219_phase1_financial_sot_tables'
branch_labels = None
depends_on = None


def upgrade():
    """添加 password_hash 字段"""
    # 添加密码哈希字段
    op.add_column(
        'users',
        sa.Column(
            'password_hash',
            sa.String(length=255),
            nullable=True,
            comment='密码哈希(bcrypt) - 本地 JWT 认证使用'
        )
    )

    # 添加索引以加速登录查询
    op.create_index(
        'idx_users_email_active',
        'users',
        ['email', 'is_active'],
        unique=False
    )


def downgrade():
    """移除 password_hash 字段"""
    # 删除索引
    op.drop_index('idx_users_email_active', table_name='users')

    # 删除密码哈希字段
    op.drop_column('users', 'password_hash')
