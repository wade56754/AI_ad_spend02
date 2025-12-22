"""
Add project_owner role support

Revision ID: 20251222_add_project_owner_role
Revises: 20251221_add_daily_report_fields
Create Date: 2025-12-22

变更内容:
1. users 表:
   - 添加 is_project_owner 布尔字段 (可选快速标识)
   - 更新 role CHECK 约束以支持 project_owner 角色

2. project_members 表:
   - 如不存在则创建完整表结构
   - 添加 role CHECK 约束 (owner/member/viewer)
   - 添加唯一约束: 每个项目最多一个 owner

背景 (MASTER.md §2.4):
- 系统需要 7 个业务角色，其中 project_owner（项目负责人）负责:
  - 对项目盈亏负责
  - 申请充值，对使用效率负责
  - 调配投手，提交周报

SoT Reference: MASTER.md v4.4 §2.4
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB


# revision identifiers, used by Alembic.
revision = '20251222_add_project_owner_role'
down_revision = '20251221_daily_report_fields'
branch_labels = None
depends_on = None


def upgrade():
    """添加 project_owner 角色支持"""

    # ========== 1. users 表变更 ==========

    # 1.1 检查并添加 role 字段（如果不存在）
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'role'
            ) THEN
                ALTER TABLE users ADD COLUMN role VARCHAR(20);
            END IF;
        END $$;
    """)

    # 1.2 添加 is_project_owner 布尔字段（快速查询标识）
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'is_project_owner'
            ) THEN
                ALTER TABLE users
                ADD COLUMN is_project_owner BOOLEAN NOT NULL DEFAULT false;

                COMMENT ON COLUMN users.is_project_owner IS
                    '是否为项目负责人 (MASTER.md v4.4 §2.4)';
            END IF;
        END $$;
    """)

    # 1.3 更新 users.role CHECK 约束（支持 6 个技术角色）
    op.execute("""
        ALTER TABLE users
        DROP CONSTRAINT IF EXISTS users_role_check
    """)
    op.execute("""
        ALTER TABLE users
        ADD CONSTRAINT users_role_check
        CHECK (role IN (
            'admin',           -- 系统管理员
            'finance',         -- 财务
            'data_operator',   -- 数据运营
            'account_manager', -- 账户管理员
            'media_buyer',     -- 广告投手
            'project_owner'    -- 项目负责人 (新增)
        ))
    """)

    # 1.4 创建 is_project_owner 部分索引（优化查询）
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_is_project_owner
        ON users(is_project_owner)
        WHERE is_project_owner = true
    """)

    # ========== 2. project_members 表变更 ==========

    # 2.1 创建 project_members 表（如不存在）
    op.execute("""
        CREATE TABLE IF NOT EXISTS project_members (
            -- 主键
            id BIGSERIAL PRIMARY KEY,

            -- 外键
            project_id BIGINT NOT NULL,
            user_id UUID NOT NULL,

            -- 业务字段
            role VARCHAR(20) NOT NULL DEFAULT 'member',
            permissions JSONB,
            notes TEXT,

            -- 时间戳
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

            -- 约束：同一用户在同一项目中只能有一个成员关系
            CONSTRAINT project_members_project_user_key UNIQUE (project_id, user_id)
        )
    """)

    # 2.2 添加外键约束（如不存在）
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'project_members_project_id_fkey'
            ) THEN
                ALTER TABLE project_members
                ADD CONSTRAINT project_members_project_id_fkey
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'project_members_user_id_fkey'
            ) THEN
                ALTER TABLE project_members
                ADD CONSTRAINT project_members_user_id_fkey
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
            END IF;
        END $$;
    """)

    # 2.3 添加 role CHECK 约束（owner/member/viewer）
    op.execute("""
        DO $$
        BEGIN
            -- 删除旧约束
            ALTER TABLE project_members
            DROP CONSTRAINT IF EXISTS ck_project_members_role;

            -- 添加新约束（支持 owner/member/viewer）
            ALTER TABLE project_members
            ADD CONSTRAINT ck_project_members_role
            CHECK (role IN ('owner', 'member', 'viewer'));
        END $$;
    """)

    # 2.4 添加唯一约束：每个项目最多一个 owner
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_one_owner_per_project
        ON project_members(project_id)
        WHERE role = 'owner'
    """)

    # 2.5 创建常用索引（如不存在）
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_project_members_project_id
        ON project_members(project_id);

        CREATE INDEX IF NOT EXISTS idx_project_members_user_id
        ON project_members(user_id);

        CREATE INDEX IF NOT EXISTS idx_project_members_role
        ON project_members(role);
    """)

    # 2.6 添加表和字段注释
    op.execute("""
        COMMENT ON TABLE project_members IS
            '项目成员表 - 记录用户在项目中的角色和权限 (MASTER.md v4.4 §2.4)';

        COMMENT ON COLUMN project_members.role IS
            '项目内角色：owner(负责人)/member(成员)/viewer(只读)';
    """)

    # 2.7 创建更新时间触发器（如不存在）
    op.execute("""
        CREATE OR REPLACE FUNCTION update_project_members_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS trigger_update_project_members_updated_at ON project_members;

        CREATE TRIGGER trigger_update_project_members_updated_at
            BEFORE UPDATE ON project_members
            FOR EACH ROW
            EXECUTE FUNCTION update_project_members_updated_at();
    """)


def downgrade():
    """移除 project_owner 角色支持"""

    # ========== 1. project_members 表回滚 ==========

    # 1.1 移除 one owner per project 唯一索引
    op.execute("""
        DROP INDEX IF EXISTS idx_one_owner_per_project
    """)

    # 1.2 移除 role CHECK 约束
    op.execute("""
        ALTER TABLE project_members
        DROP CONSTRAINT IF EXISTS ck_project_members_role
    """)

    # 1.3 移除更新触发器
    op.execute("""
        DROP TRIGGER IF EXISTS trigger_update_project_members_updated_at ON project_members
    """)

    # 注意：不删除 project_members 表，因为可能有其他数据

    # ========== 2. users 表回滚 ==========

    # 2.1 移除 is_project_owner 索引
    op.execute("""
        DROP INDEX IF EXISTS idx_users_is_project_owner
    """)

    # 2.2 恢复旧的 role CHECK 约束（不含 project_owner）
    op.execute("""
        ALTER TABLE users
        DROP CONSTRAINT IF EXISTS users_role_check
    """)
    op.execute("""
        ALTER TABLE users
        ADD CONSTRAINT users_role_check
        CHECK (role IN (
            'admin',
            'finance',
            'data_operator',
            'account_manager',
            'media_buyer'
        ))
    """)

    # 2.3 移除 is_project_owner 字段
    op.execute("""
        ALTER TABLE users
        DROP COLUMN IF EXISTS is_project_owner
    """)
