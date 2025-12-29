"""
Add ceo role to users table

Revision ID: 20251224_add_ceo_role
Revises: 20251223_add_weekly_briefs_table
Create Date: 2025-12-24

变更内容:
1. users 表:
   - 更新 role CHECK 约束以支持 ceo 角色 (7 个技术角色)

背景 (MASTER.md v4.4 §2.4, AUTH_SPEC.md v2.1 §2.2):
- 系统需要 7 个业务角色，其中 ceo（老板）负责:
  - 资金安全、公司盈亏、最终决策
  - 批准充值，锁定结算
  - 可见范围：全部

7 角色清单:
  | 业务角色 | 技术枚举 | 权限级别 |
  |---------|----------|---------|
  | ceo | ceo | L7 (最高) |
  | admin | admin | L6 |
  | project_owner | project_owner | L5 |
  | finance | finance | L4 |
  | supervisor | data_operator | L3 |
  | account_manager | account_manager | L2 |
  | pitcher | media_buyer | L1 (最低) |

SoT Reference: MASTER.md v4.4 §2.4, AUTH_SPEC.md v2.1 §2.2
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '20251224_add_ceo_role'
down_revision = '20251223_add_weekly_briefs_table'
branch_labels = None
depends_on = None


def upgrade():
    """添加 ceo 角色支持，完成 7 角色体系"""

    # 1. 删除旧的 role CHECK 约束
    op.execute("""
        ALTER TABLE users
        DROP CONSTRAINT IF EXISTS users_role_check
    """)

    # 2. 添加新的 role CHECK 约束（7 个技术角色）
    op.execute("""
        ALTER TABLE users
        ADD CONSTRAINT users_role_check
        CHECK (role IN (
            'ceo',             -- 老板 (L7 最高) - 资金安全、公司盈亏、最终决策
            'admin',           -- 系统管理员 (L6) - 系统配置、全局审计
            'project_owner',   -- 项目负责人 (L5) - 项目盈亏、资金使用效率
            'finance',         -- 财务 (L4) - 资金出入准确、数据真实
            'data_operator',   -- 主管/supervisor (L3) - 团队产出、投手管理
            'account_manager', -- 户管 (L2) - 账户分配、账户状态监控
            'media_buyer'      -- 投手/pitcher (L1 最低) - CPL达标、日报准确
        ))
    """)

    # 3. 添加注释
    op.execute("""
        COMMENT ON COLUMN users.role IS
            '用户角色 (7 技术角色) - SoT: MASTER.md v4.4 §2.4, AUTH_SPEC.md v2.1 §2.2';
    """)


def downgrade():
    """回滚到 6 角色版本（不含 ceo）"""

    # 1. 删除新的 CHECK 约束
    op.execute("""
        ALTER TABLE users
        DROP CONSTRAINT IF EXISTS users_role_check
    """)

    # 2. 恢复旧的 CHECK 约束（6 个技术角色）
    op.execute("""
        ALTER TABLE users
        ADD CONSTRAINT users_role_check
        CHECK (role IN (
            'admin',
            'finance',
            'data_operator',
            'account_manager',
            'media_buyer',
            'project_owner'
        ))
    """)
