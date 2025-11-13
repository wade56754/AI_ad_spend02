"""创建充值管理相关表

Revision ID: 005
Revises: 004
Create Date: 2025-11-12 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建充值申请主表
    op.execute("""
        CREATE TABLE IF NOT EXISTS topup_requests (
            id SERIAL PRIMARY KEY,
            request_no VARCHAR(50) NOT NULL UNIQUE,
            ad_account_id INTEGER NOT NULL REFERENCES ad_accounts(id),
            project_id INTEGER NOT NULL REFERENCES projects(id),
            requested_amount DECIMAL(15,2) NOT NULL CHECK (requested_amount > 0),
            actual_amount DECIMAL(15,2) CHECK (actual_amount > 0),
            currency VARCHAR(10) NOT NULL DEFAULT 'USD',
            urgency_level VARCHAR(20) NOT NULL DEFAULT 'normal' CHECK (urgency_level IN ('low', 'normal', 'high', 'urgent')),
            reason TEXT NOT NULL,
            notes TEXT,
            expected_date DATE,
            status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (
                status IN ('pending', 'data_review', 'finance_approve', 'rejected', 'paid', 'completed', 'cancelled')
            ),
            payment_method VARCHAR(50),
            transaction_id VARCHAR(100),
            receipt_url VARCHAR(500),
            requested_by INTEGER NOT NULL REFERENCES users(id),
            data_reviewed_by INTEGER REFERENCES users(id),
            data_reviewed_at TIMESTAMP,
            data_review_notes TEXT,
            finance_approved_by INTEGER REFERENCES users(id),
            finance_approved_at TIMESTAMP,
            finance_approve_notes TEXT,
            paid_at TIMESTAMP,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 创建充值申请表索引
    op.execute("CREATE INDEX IF NOT EXISTS idx_topup_requests_no ON topup_requests(request_no)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_topup_requests_account ON topup_requests(ad_account_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_topup_requests_project ON topup_requests(project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_topup_requests_status ON topup_requests(status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_topup_requests_requested_by ON topup_requests(requested_by)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_topup_requests_created_at ON topup_requests(created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_topup_requests_urgency ON topup_requests(urgency_level)")

    # 创建充值交易记录表
    op.execute("""
        CREATE TABLE IF NOT EXISTS topup_transactions (
            id SERIAL PRIMARY KEY,
            request_id INTEGER NOT NULL REFERENCES topup_requests(id),
            transaction_no VARCHAR(100) NOT NULL UNIQUE,
            amount DECIMAL(15,2) NOT NULL CHECK (amount > 0),
            currency VARCHAR(10) NOT NULL DEFAULT 'USD',
            payment_method VARCHAR(50) NOT NULL,
            payment_account VARCHAR(100),
            transaction_date TIMESTAMP NOT NULL,
            receipt_file VARCHAR(500),
            notes TEXT,
            created_by INTEGER NOT NULL REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 创建交易记录表索引
    op.execute("CREATE INDEX IF NOT EXISTS idx_topup_transactions_no ON topup_transactions(transaction_no)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_topup_transactions_request ON topup_transactions(request_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_topup_transactions_date ON topup_transactions(transaction_date)")

    # 创建充值审批日志表
    op.execute("""
        CREATE TABLE IF NOT EXISTS topup_approval_logs (
            id SERIAL PRIMARY KEY,
            request_id INTEGER NOT NULL REFERENCES topup_requests(id),
            action VARCHAR(50) NOT NULL,
            actor_id INTEGER NOT NULL REFERENCES users(id),
            actor_role VARCHAR(50) NOT NULL,
            notes TEXT,
            previous_status VARCHAR(20),
            new_status VARCHAR(20),
            ip_address INET,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 创建审批日志表索引
    op.execute("CREATE INDEX IF NOT EXISTS idx_topup_approval_logs_request ON topup_approval_logs(request_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_topup_approval_logs_action ON topup_approval_logs(action)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_topup_approval_logs_actor ON topup_approval_logs(actor_id)")

    # 创建更新时间触发器函数
    op.execute("""
        CREATE OR REPLACE FUNCTION update_topup_requests_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # 为充值申请表创建更新时间触发器
    op.execute("""
        CREATE TRIGGER update_topup_requests_updated_at
            BEFORE UPDATE ON topup_requests
            FOR EACH ROW
            EXECUTE FUNCTION update_topup_requests_updated_at();
    """)


def downgrade() -> None:
    # 删除触发器和函数
    op.execute("DROP TRIGGER IF EXISTS update_topup_requests_updated_at ON topup_requests")
    op.execute("DROP FUNCTION IF EXISTS update_topup_requests_updated_at()")

    # 删除表（按依赖关系倒序）
    op.execute("DROP TABLE IF EXISTS topup_approval_logs")
    op.execute("DROP TABLE IF EXISTS topup_transactions")
    op.execute("DROP TABLE IF EXISTS topup_requests")