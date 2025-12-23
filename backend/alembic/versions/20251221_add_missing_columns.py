"""add missing columns to project_members and project_expenses

Revision ID: add_missing_columns
Revises: add_expense_date
Create Date: 2025-12-21

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_missing_columns'
down_revision = 'add_expense_date'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Add missing columns to project_members table
    if 'project_members' in [t for t in inspector.get_table_names()]:
        columns = [c['name'] for c in inspector.get_columns('project_members')]

        if 'created_at' not in columns:
            op.add_column(
                'project_members',
                sa.Column('created_at', sa.DateTime(timezone=True),
                         server_default=sa.text('NOW()'), nullable=False,
                         comment='创建时间')
            )

        if 'updated_at' not in columns:
            op.add_column(
                'project_members',
                sa.Column('updated_at', sa.DateTime(timezone=True),
                         server_default=sa.text('NOW()'), nullable=False,
                         comment='更新时间')
            )

        if 'notes' not in columns:
            op.add_column(
                'project_members',
                sa.Column('notes', sa.Text(), nullable=True, comment='备注')
            )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'project_members' in [t for t in inspector.get_table_names()]:
        columns = [c['name'] for c in inspector.get_columns('project_members')]

        if 'created_at' in columns:
            op.drop_column('project_members', 'created_at')

        if 'updated_at' in columns:
            op.drop_column('project_members', 'updated_at')

        if 'notes' in columns:
            op.drop_column('project_members', 'notes')
