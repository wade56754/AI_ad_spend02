"""
Add team_id column to users table

Revision ID: 20251225_add_user_team_id
Revises: 20251225_daily_reports_unique_region
Create Date: 2025-12-25

变更内容:
1. users 表新增字段:
   - team_id: UUID 所属团队ID (外键关联 teams.id)
2. 创建索引: idx_users_team

业务背景:
- 投手日报 CSV 包含 "所属团队" 字段，需要直接关联用户和团队
- 原模型中用户仅通过 ad_accounts 间接关联团队
- 新增直接关联便于按团队筛选投手和统计

SoT Reference:
- DATA_SCHEMA.md v5.4 §3.1.1 users 表
- user.py v2.1 模型更新
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '20251225_add_user_team_id'
down_revision = '20251225_daily_reports_unique_region'
branch_labels = None
depends_on = None


def upgrade():
    """添加 team_id 字段到 users 表"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 检查 users 表是否存在
    if 'users' not in [t for t in inspector.get_table_names()]:
        print("users 表不存在，跳过迁移")
        return

    columns = [c['name'] for c in inspector.get_columns('users')]

    # 1. 添加 team_id 字段
    if 'team_id' not in columns:
        op.add_column(
            'users',
            sa.Column(
                'team_id',
                UUID(as_uuid=True),
                nullable=True,
                comment='所属团队ID'
            )
        )
        print("已添加 team_id 字段")

        # 2. 检查 teams 表是否存在后添加外键
        if 'teams' in [t for t in inspector.get_table_names()]:
            op.create_foreign_key(
                'fk_users_team_id',
                'users',
                'teams',
                ['team_id'],
                ['id'],
                ondelete='SET NULL'
            )
            print("已创建外键约束: fk_users_team_id")
        else:
            print("teams 表不存在，跳过外键创建")

    # 3. 创建索引
    indexes = [idx['name'] for idx in inspector.get_indexes('users')]
    if 'idx_users_team' not in indexes:
        op.create_index('idx_users_team', 'users', ['team_id'])
        print("已创建索引: idx_users_team")


def downgrade():
    """移除 team_id 字段"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'users' not in [t for t in inspector.get_table_names()]:
        return

    # 1. 删除索引
    indexes = [idx['name'] for idx in inspector.get_indexes('users')]
    if 'idx_users_team' in indexes:
        op.drop_index('idx_users_team', 'users')

    # 2. 删除外键
    fks = inspector.get_foreign_keys('users')
    fk_names = [fk['name'] for fk in fks]
    if 'fk_users_team_id' in fk_names:
        op.drop_constraint('fk_users_team_id', 'users', type_='foreignkey')

    # 3. 删除字段
    columns = [c['name'] for c in inspector.get_columns('users')]
    if 'team_id' in columns:
        op.drop_column('users', 'team_id')
