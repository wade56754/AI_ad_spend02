"""
Add project_owner role support

Revision ID: 20251222_add_project_owner_role
Revises: 20251221_add_daily_report_fields
Create Date: 2025-12-22

变更内容:
- 更新 users.role CHECK 约束以支持 project_owner 角色
- 添加 users.is_project_owner 布尔字段 (可选标识)
- 添加 project_members.member_role 字段区分 owner/member

SoT Reference: MASTER.md v4.4 §2.4
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251222_add_project_owner_role'
down_revision = '20251221_add_daily_report_fields'
branch_labels = None
depends_on = None


def upgrade():
    """添加 project_owner 角色支持"""

    # 1. 添加 users.is_project_owner 布尔字段
    op.add_column(
        'users',
        sa.Column(
            'is_project_owner',
            sa.Boolean(),
            nullable=False,
            server_default='false',
            comment='是否为项目负责人 (MASTER.md v4.4)'
        )
    )

    # 2. 更新 users.role CHECK 约束
    # 先删除旧约束
    op.execute("""
        ALTER TABLE users
        DROP CONSTRAINT IF EXISTS users_role_check
    """)

    # 添加新约束,包含 project_owner
    op.execute("""
        ALTER TABLE users
        ADD CONSTRAINT users_role_check
        CHECK (role IN ('admin', 'finance', 'data_operator', 'account_manager', 'media_buyer', 'project_owner'))
    """)

    # 3. 检查 project_members 表是否存在,如果存在则添加 member_role 字段
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'project_members') THEN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                               WHERE table_name = 'project_members' AND column_name = 'member_role') THEN
                    ALTER TABLE project_members
                    ADD COLUMN member_role VARCHAR(20) DEFAULT 'member' NOT NULL;

                    ALTER TABLE project_members
                    ADD CONSTRAINT ck_project_members_role
                    CHECK (member_role IN ('owner', 'member'));
                END IF;
            END IF;
        END $$;
    """)

    # 4. 创建索引优化查询
    op.create_index(
        'idx_users_is_project_owner',
        'users',
        ['is_project_owner'],
        postgresql_where=sa.text('is_project_owner = true')
    )


def downgrade():
    """移除 project_owner 角色支持"""

    # 1. 移除索引
    op.drop_index('idx_users_is_project_owner', table_name='users')

    # 2. 移除 project_members.member_role 字段
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name = 'project_members' AND column_name = 'member_role') THEN
                ALTER TABLE project_members DROP CONSTRAINT IF EXISTS ck_project_members_role;
                ALTER TABLE project_members DROP COLUMN member_role;
            END IF;
        END $$;
    """)

    # 3. 恢复旧的 role CHECK 约束
    op.execute("""
        ALTER TABLE users
        DROP CONSTRAINT IF EXISTS users_role_check
    """)
    op.execute("""
        ALTER TABLE users
        ADD CONSTRAINT users_role_check
        CHECK (role IN ('admin', 'finance', 'data_operator', 'account_manager', 'media_buyer'))
    """)

    # 4. 移除 is_project_owner 字段
    op.drop_column('users', 'is_project_owner')
