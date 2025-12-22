"""add expense_date column to project_expenses

Revision ID: add_expense_date
Revises: 20251221_add_daily_report_fields
Create Date: 2025-12-21

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_expense_date'
down_revision = '20251221_daily_report_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add expense_date column to project_expenses table
    # First check if column exists to make migration idempotent
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'project_expenses' in [t for t in inspector.get_table_names()]:
        columns = [c['name'] for c in inspector.get_columns('project_expenses')]

        if 'expense_date' not in columns:
            op.add_column(
                'project_expenses',
                sa.Column('expense_date', sa.Date(), nullable=True, comment='费用日期')
            )

            # Set default value for existing rows (use created_at date)
            op.execute("""
                UPDATE project_expenses
                SET expense_date = DATE(created_at)
                WHERE expense_date IS NULL
            """)

            # Make column NOT NULL after populating data
            op.alter_column(
                'project_expenses',
                'expense_date',
                nullable=False
            )


def downgrade() -> None:
    # Remove expense_date column
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'project_expenses' in [t for t in inspector.get_table_names()]:
        columns = [c['name'] for c in inspector.get_columns('project_expenses')]

        if 'expense_date' in columns:
            op.drop_column('project_expenses', 'expense_date')
