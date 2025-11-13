"""创建项目管理相关表

Revision ID: 003
Revises: 002
Create Date: 2025-11-12 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建项目主表
    op.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            client_name VARCHAR(200) NOT NULL,
            client_company VARCHAR(200) NOT NULL,
            description TEXT,
            status VARCHAR(20) DEFAULT 'planning' CHECK (status IN ('planning', 'active', 'paused', 'completed', 'cancelled')),
            budget DECIMAL(15,2) DEFAULT 0.00,
            currency VARCHAR(10) DEFAULT 'USD',
            start_date DATE,
            end_date DATE,
            account_manager_id INTEGER REFERENCES users(id),
            created_by INTEGER NOT NULL REFERENCES users(id),
            updated_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 创建索引
    op.execute("CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_projects_client ON projects(client_name)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_projects_manager ON projects(account_manager_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_projects_created_by ON projects(created_by)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_name_client ON projects(name, client_name)")

    # 创建项目成员关联表
    op.execute("""
        CREATE TABLE IF NOT EXISTS project_members (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role VARCHAR(50) NOT NULL CHECK (role IN ('account_manager', 'media_buyer', 'analyst')),
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, user_id)
        )
    """)

    # 创建项目成员表索引
    op.execute("CREATE INDEX IF NOT EXISTS idx_project_members_project ON project_members(project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_project_members_user ON project_members(user_id)")

    # 创建项目费用记录表
    op.execute("""
        CREATE TABLE IF NOT EXISTS project_expenses (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            expense_type VARCHAR(50) NOT NULL CHECK (expense_type IN ('media_spend', 'service_fee', 'other')),
            amount DECIMAL(15,2) NOT NULL CHECK (amount > 0),
            description TEXT,
            expense_date DATE NOT NULL,
            created_by INTEGER NOT NULL REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 创建项目费用表索引
    op.execute("CREATE INDEX IF NOT EXISTS idx_expenses_project ON project_expenses(project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON project_expenses(expense_date)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_expenses_type ON project_expenses(expense_type)")

    # 创建更新时间触发器函数
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    # 为项目表创建更新时间触发器
    op.execute("""
        CREATE TRIGGER update_projects_updated_at
            BEFORE UPDATE ON projects
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    # 删除触发器
    op.execute("DROP TRIGGER IF EXISTS update_projects_updated_at ON projects")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # 删除表（按依赖关系倒序）
    op.execute("DROP TABLE IF EXISTS project_expenses")
    op.execute("DROP TABLE IF EXISTS project_members")
    op.execute("DROP TABLE IF EXISTS projects")