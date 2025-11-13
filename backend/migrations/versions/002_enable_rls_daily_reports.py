"""启用日报管理表的RLS策略

Revision ID: 002
Revises: 001
Create Date: 2025-11-12 10:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 启用RLS
    op.execute("ALTER TABLE daily_reports ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE daily_report_audit_logs ENABLE ROW LEVEL SECURITY")

    # 创建角色策略
    # 注意：这里假设角色名已经存在，实际使用时可能需要先创建角色

    # 策略1：管理员全权限
    op.execute("""
        CREATE POLICY admin_full_access_daily_reports ON daily_reports
        FOR ALL TO admin_role
        USING (true)
        WITH CHECK (true)
    """)

    # 策略2：数据员全权限
    op.execute("""
        CREATE POLICY data_operator_full_access_daily_reports ON daily_reports
        FOR ALL TO data_operator_role
        USING (true)
        WITH CHECK (true)
    """)

    # 策略3：财务只读
    op.execute("""
        CREATE POLICY finance_read_only_daily_reports ON daily_reports
        FOR SELECT TO finance_role
        USING (true)
    """)

    # 策略4：账户管理员查看项目内数据
    op.execute("""
        CREATE POLICY account_manager_project_reports ON daily_reports
        FOR SELECT TO account_manager_role
        USING (
            ad_account_id IN (
                SELECT id FROM ad_accounts
                WHERE project_id IN (
                    SELECT project_id FROM user_project_assignments
                    WHERE user_id = current_setting('app.current_user_id')::integer
                )
            )
        )
    """)

    # 策略5：投手只能操作自己的数据
    op.execute("""
        CREATE POLICY media_buyer_own_reports ON daily_reports
        FOR ALL TO media_buyer_role
        USING (created_by = current_setting('app.current_user_id')::integer)
        WITH CHECK (created_by = current_setting('app.current_user_id')::integer)
    """)

    # 审核日志策略
    op.execute("""
        CREATE POLICY audit_log_access ON daily_report_audit_logs
        FOR ALL TO admin_role, data_operator_role
        USING (true)
        WITH CHECK (true)
    """)

    # 创建默认状态为pending的触发器
    op.execute("""
        CREATE OR REPLACE FUNCTION set_default_daily_report_status()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.status IS NULL THEN
                NEW.status := 'pending';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trigger_set_default_status
            BEFORE INSERT ON daily_reports
            FOR EACH ROW
            EXECUTE FUNCTION set_default_daily_report_status();
    """)


def downgrade() -> None:
    # 删除触发器和函数
    op.execute("DROP TRIGGER IF EXISTS trigger_set_default_status ON daily_reports")
    op.execute("DROP FUNCTION IF EXISTS set_default_daily_report_status()")

    # 删除RLS策略
    op.execute("DROP POLICY IF EXISTS media_buyer_own_reports ON daily_reports")
    op.execute("DROP POLICY IF EXISTS account_manager_project_reports ON daily_reports")
    op.execute("DROP POLICY IF EXISTS finance_read_only_daily_reports ON daily_reports")
    op.execute("DROP POLICY IF EXISTS data_operator_full_access_daily_reports ON daily_reports")
    op.execute("DROP POLICY IF EXISTS admin_full_access_daily_reports ON daily_reports")
    op.execute("DROP POLICY IF EXISTS audit_log_access ON daily_report_audit_logs")

    # 禁用RLS
    op.execute("ALTER TABLE daily_report_audit_logs DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE daily_reports DISABLE ROW LEVEL SECURITY")