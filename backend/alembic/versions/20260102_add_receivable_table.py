"""Add receivable table (已回款 SoT)

Revision ID: 20260102_add_receivable_table
Revises: 20260102_add_commission_rules
Create Date: 2026-01-02

Affected SoT:
- DATA_SCHEMA.md v5.8 §3.4.5
- MASTER.md v4.8 §4.5.5

Changes:
- Add receivable table (回款记录表)

Business Logic:
- 已回款 SoT: SELECT SUM(amount) FROM receivable WHERE status = 'received' AND project_id = ?
- status IN ('pending', 'received', 'cancelled')
- amount > 0 (CHECK constraint)
- status='received' 时 received_at 不能为空 (应用层验证)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260102_add_receivable_table"
down_revision = "20260102_add_commission_rules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create receivable table
    op.create_table(
        "receivable",
        # Primary key
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
            comment="回款记录唯一标识",
        ),
        # Foreign key to projects
        sa.Column(
            "project_id",
            sa.BigInteger(),
            nullable=False,
            comment="所属项目",
        ),
        # Core amount field
        sa.Column(
            "amount",
            sa.Numeric(15, 2),
            nullable=False,
            comment="回款金额（必须为正数）",
        ),
        # Status field
        sa.Column(
            "status",
            sa.String(20),
            server_default="pending",
            nullable=False,
            comment="回款状态：pending（待确认）/ received（已到账）/ cancelled（已取消）",
        ),
        # Received timestamp
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="实际到账时间（status='received'时必填）",
        ),
        # Source info
        sa.Column(
            "source",
            sa.String(50),
            nullable=True,
            comment="回款来源（客户名/渠道等）",
        ),
        sa.Column(
            "invoice_no",
            sa.String(100),
            nullable=True,
            comment="发票编号",
        ),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
            comment="备注说明",
        ),
        # User references
        sa.Column(
            "recorded_by",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="记录人",
        ),
        sa.Column(
            "confirmed_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="确认人（status='received'时填充）",
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        # Primary key constraint
        sa.PrimaryKeyConstraint("id"),
        # Foreign key constraints
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_receivable_project",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["recorded_by"],
            ["users.id"],
            name="fk_receivable_recorded_by",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["confirmed_by"],
            ["users.id"],
            name="fk_receivable_confirmed_by",
            ondelete="SET NULL",
        ),
        # Check constraints
        sa.CheckConstraint(
            "status IN ('pending', 'received', 'cancelled')",
            name="chk_receivable_status",
        ),
        sa.CheckConstraint(
            "amount > 0",
            name="chk_receivable_amount_positive",
        ),
        comment="回款记录表（已回款 SoT）- DATA_SCHEMA.md v5.8 §3.4.5",
    )

    # Create indexes
    op.create_index("idx_receivable_project", "receivable", ["project_id"])
    op.create_index("idx_receivable_status", "receivable", ["status"])
    op.create_index("idx_receivable_received_at", "receivable", ["received_at"])
    op.create_index("idx_receivable_created_at", "receivable", ["created_at"])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index("idx_receivable_created_at", table_name="receivable")
    op.drop_index("idx_receivable_received_at", table_name="receivable")
    op.drop_index("idx_receivable_status", table_name="receivable")
    op.drop_index("idx_receivable_project", table_name="receivable")

    # Drop table
    op.drop_table("receivable")
