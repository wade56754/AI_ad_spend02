"""启用充值管理表的RLS策略

Revision ID: 006
Revises: 005
Create Date: 2025-11-12 17:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 启用RLS
    op.execute("ALTER TABLE topup_requests ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE topup_transactions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE topup_approval_logs ENABLE ROW LEVEL SECURITY")

    # ===== topup_requests表的RLS策略 =====

    # 策略1：管理员全权限
    op.execute("""
        CREATE POLICY admin_full_access_topup_requests ON topup_requests
        FOR ALL TO admin_role
        USING (true)
        WITH CHECK (true)
    """)

    # 策略2：财务全权限
    op.execute("""
        CREATE POLICY finance_full_access_topup_requests ON topup_requests
        FOR ALL TO finance_role
        USING (true)
        WITH CHECK (true)
    """)

    # 策略3：数据员审核权限
    op.execute("""
        CREATE POLICY data_operator_access_topup_requests ON topup_requests
        FOR ALL TO data_operator_role
        USING (true)
        WITH CHECK (true)
    """)

    # 策略4：账户管理员查看和创建自己项目的充值
    op.execute("""
        CREATE POLICY account_manager_view_topup_requests ON topup_requests
        FOR SELECT TO account_manager_role
        USING (
            project_id IN (
                SELECT id FROM projects
                WHERE account_manager_id = current_setting('app.current_user_id')::integer
            )
        )
    """)

    op.execute("""
        CREATE POLICY account_manager_create_topup_requests ON topup_requests
        FOR INSERT TO account_manager_role
        WITH CHECK (
            project_id IN (
                SELECT id FROM projects
                WHERE account_manager_id = current_setting('app.current_user_id')::integer
            )
        )
    """)

    op.execute("""
        CREATE POLICY account_manager_update_topup_requests ON topup_requests
        FOR UPDATE TO account_manager_role
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

    # 策略5：媒体买家查看和创建自己的申请
    op.execute("""
        CREATE POLICY media_buyer_own_topup_requests ON topup_requests
        FOR ALL TO media_buyer_role
        USING (requested_by = current_setting('app.current_user_id')::integer)
        WITH CHECK (requested_by = current_setting('app.current_user_id')::integer)
    """)

    # ===== topup_transactions表的RLS策略 =====

    # 策略1：财务和管理员全权限
    op.execute("""
        CREATE POLICY finance_access_topup_transactions ON topup_transactions
        FOR ALL TO finance_role, admin_role
        USING (true)
        WITH CHECK (true)
    """)

    # 策略2：数据员只读权限
    op.execute("""
        CREATE POLICY data_operator_read_topup_transactions ON topup_transactions
        FOR SELECT TO data_operator_role
        USING (true)
    """)

    # 策略3：账户管理员查看项目内的交易
    op.execute("""
        CREATE POLICY account_manager_view_topup_transactions ON topup_transactions
        FOR SELECT TO account_manager_role
        USING (
            request_id IN (
                SELECT id FROM topup_requests
                WHERE project_id IN (
                    SELECT id FROM projects
                    WHERE account_manager_id = current_setting('app.current_user_id')::integer
                )
            )
        )
    """)

    # 策略4：媒体买家查看自己的申请相关交易
    op.execute("""
        CREATE POLICY media_buyer_view_topup_transactions ON topup_transactions
        FOR SELECT TO media_buyer_role
        USING (
            request_id IN (
                SELECT id FROM topup_requests
                WHERE requested_by = current_setting('app.current_user_id')::integer
            )
        )
    """)

    # ===== topup_approval_logs表的RLS策略 =====

    # 策略1：财务和管理员全权限
    op.execute("""
        CREATE POLICY finance_admin_access_topup_approval_logs ON topup_approval_logs
        FOR ALL TO finance_role, admin_role
        USING (true)
        WITH CHECK (true)
    """)

    # 策略2：数据员查看所有日志
    op.execute("""
        CREATE POLICY data_operator_read_topup_approval_logs ON topup_approval_logs
        FOR SELECT TO data_operator_role
        USING (true)
    """)

    # 策略3：账户管理员查看项目内的日志
    op.execute("""
        CREATE POLICY account_manager_view_topup_approval_logs ON topup_approval_logs
        FOR SELECT TO account_manager_role
        USING (
            request_id IN (
                SELECT id FROM topup_requests
                WHERE project_id IN (
                    SELECT id FROM projects
                    WHERE account_manager_id = current_setting('app.current_user_id')::integer
                )
            )
        )
    """)

    # 策略4：媒体买家查看自己申请的日志
    op.execute("""
        CREATE POLICY media_buyer_own_topup_approval_logs ON topup_approval_logs
        FOR SELECT TO media_buyer_role
        USING (
            request_id IN (
                SELECT id FROM topup_requests
                WHERE requested_by = current_setting('app.current_user_id')::integer
            )
        )
    """)


def downgrade() -> None:
    # 删除topup_approval_logs的RLS策略
    op.execute("DROP POLICY IF EXISTS media_buyer_own_topup_approval_logs ON topup_approval_logs")
    op.execute("DROP POLICY IF EXISTS account_manager_view_topup_approval_logs ON topup_approval_logs")
    op.execute("DROP POLICY IF EXISTS data_operator_read_topup_approval_logs ON topup_approval_logs")
    op.execute("DROP POLICY IF EXISTS finance_admin_access_topup_approval_logs ON topup_approval_logs")

    # 删除topup_transactions的RLS策略
    op.execute("DROP POLICY IF EXISTS media_buyer_view_topup_transactions ON topup_transactions")
    op.execute("DROP POLICY IF EXISTS account_manager_view_topup_transactions ON topup_transactions")
    op.execute("DROP POLICY IF EXISTS data_operator_read_topup_transactions ON topup_transactions")
    op.execute("DROP POLICY IF EXISTS finance_access_topup_transactions ON topup_transactions")

    # 删除topup_requests的RLS策略
    op.execute("DROP POLICY IF EXISTS media_buyer_own_topup_requests ON topup_requests")
    op.execute("DROP POLICY IF EXISTS account_manager_update_topup_requests ON topup_requests")
    op.execute("DROP POLICY IF EXISTS account_manager_create_topup_requests ON topup_requests")
    op.execute("DROP POLICY IF EXISTS account_manager_view_topup_requests ON topup_requests")
    op.execute("DROP POLICY IF EXISTS data_operator_access_topup_requests ON topup_requests")
    op.execute("DROP POLICY IF EXISTS finance_full_access_topup_requests ON topup_requests")
    op.execute("DROP POLICY IF EXISTS admin_full_access_topup_requests ON topup_requests")

    # 禁用RLS
    op.execute("ALTER TABLE topup_approval_logs DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE topup_transactions DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE topup_requests DISABLE ROW LEVEL SECURITY")