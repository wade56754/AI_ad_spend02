"""启用项目管理表的RLS策略

Revision ID: 004
Revises: 003
Create Date: 2025-11-12 15:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 启用RLS
    op.execute("ALTER TABLE projects ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE project_members ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE project_expenses ENABLE ROW LEVEL SECURITY")

    # 策略1：管理员全权限
    op.execute("""
        CREATE POLICY admin_full_access_projects ON projects
        FOR ALL TO admin_role
        USING (true)
        WITH CHECK (true)
    """)

    op.execute("""
        CREATE POLICY admin_full_access_project_members ON project_members
        FOR ALL TO admin_role
        USING (true)
        WITH CHECK (true)
    """)

    op.execute("""
        CREATE POLICY admin_full_access_project_expenses ON project_expenses
        FOR ALL TO admin_role
        USING (true)
        WITH CHECK (true)
    """)

    # 策略2：财务和数据员只读
    op.execute("""
        CREATE POLICY finance_read_only_projects ON projects
        FOR SELECT TO finance_role
        USING (true)
    """)

    op.execute("""
        CREATE POLICY data_operator_read_only_projects ON projects
        FOR SELECT TO data_operator_role
        USING (true)
    """)

    op.execute("""
        CREATE POLICY finance_read_only_project_members ON project_members
        FOR SELECT TO finance_role
        USING (true)
    """)

    op.execute("""
        CREATE POLICY data_operator_read_only_project_members ON project_members
        FOR SELECT TO data_operator_role
        USING (true)
    """)

    op.execute("""
        CREATE POLICY finance_read_only_project_expenses ON project_expenses
        FOR SELECT TO finance_role
        USING (true)
    """)

    op.execute("""
        CREATE POLICY data_operator_read_only_project_expenses ON project_expenses
        FOR SELECT TO data_operator_role
        USING (true)
    """)

    # 策略3：账户管理员管理自己的项目
    op.execute("""
        CREATE POLICY manager_manage_projects ON projects
        FOR ALL TO account_manager_role
        USING (account_manager_id = current_setting('app.current_user_id')::integer)
        WITH CHECK (account_manager_id = current_setting('app.current_user_id')::integer)
    """)

    op.execute("""
        CREATE POLICY manager_view_project_members ON project_members
        FOR ALL TO account_manager_role
        USING (
            project_id IN (
                SELECT id FROM projects
                WHERE account_manager_id = current_setting('app.current_user_id')::integer
            )
        )
        WITH CHECK (
            project_id IN (
                SELECT id FROM projects
                WHERE account_manager_id = current_setting('app.current_user_id')::integer
            )
        )
    """)

    op.execute("""
        CREATE POLICY manager_manage_project_expenses ON project_expenses
        FOR ALL TO account_manager_role
        USING (
            project_id IN (
                SELECT id FROM projects
                WHERE account_manager_id = current_setting('app.current_user_id')::integer
            )
        )
        WITH CHECK (
            project_id IN (
                SELECT id FROM projects
                WHERE account_manager_id = current_setting('app.current_user_id')::integer
            )
        )
    """)

    # 策略4：投手查看参与的项目
    op.execute("""
        CREATE POLICY media_buyer_view_projects ON projects
        FOR SELECT TO media_buyer_role
        USING (
            id IN (
                SELECT project_id FROM project_members
                WHERE user_id = current_setting('app.current_user_id')::integer
            )
        )
    """)

    op.execute("""
        CREATE POLICY media_buyer_view_project_members ON project_members
        FOR SELECT TO media_buyer_role
        USING (
            user_id = current_setting('app.current_user_id')::integer
        )
    """)


def downgrade() -> None:
    # 删除RLS策略
    op.execute("DROP POLICY IF EXISTS media_buyer_view_project_members ON project_members")
    op.execute("DROP POLICY IF EXISTS media_buyer_view_projects ON projects")
    op.execute("DROP POLICY IF EXISTS manager_manage_project_expenses ON project_expenses")
    op.execute("DROP POLICY IF EXISTS manager_view_project_members ON project_members")
    op.execute("DROP POLICY IF EXISTS manager_manage_projects ON projects")
    op.execute("DROP POLICY IF EXISTS data_operator_read_only_project_expenses ON project_expenses")
    op.execute("DROP POLICY IF EXISTS finance_read_only_project_expenses ON project_expenses")
    op.execute("DROP POLICY IF EXISTS data_operator_read_only_project_members ON project_members")
    op.execute("DROP POLICY IF EXISTS finance_read_only_project_members ON project_members")
    op.execute("DROP POLICY IF EXISTS data_operator_read_only_projects ON projects")
    op.execute("DROP POLICY IF EXISTS finance_read_only_projects ON projects")
    op.execute("DROP POLICY IF EXISTS admin_full_access_project_expenses ON project_expenses")
    op.execute("DROP POLICY IF EXISTS admin_full_access_project_members ON project_members")
    op.execute("DROP POLICY IF EXISTS admin_full_access_projects ON projects")

    # 禁用RLS
    op.execute("ALTER TABLE project_expenses DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE project_members DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE projects DISABLE ROW LEVEL SECURITY")