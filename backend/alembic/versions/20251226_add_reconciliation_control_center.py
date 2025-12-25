"""Add reconciliation control center tables

Revision ID: 20251226_add_reconciliation_control_center
Revises: 20251225_add_pricing_and_expenses
Create Date: 2025-12-26

OpenSpec Change: add-reconciliation-control-center
Affected SoT: DATA_SCHEMA.md v5.3 -> v5.4

Changes:
- Add settlement_rules table
- Add ad_account_balance_snapshots table
- Add reconciliation_issues table
- Extend projects table (settlement_type, settlement_rules_id)
- Extend ad_accounts table (deposit, deposit_updated_at)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251226_add_reconciliation_control_center"
down_revision = "20251225_pricing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Phase 1: Create settlement_rules table (must be first due to FK dependency)
    op.create_table(
        "settlement_rules",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("rule_type", sa.String(20), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name="fk_settlement_rules_created_by"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "rule_type IN ('tiered', 'markup')", name="chk_settlement_rules_rule_type"
        ),
        sa.CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from",
            name="chk_settlement_rules_effective_period",
        ),
    )
    op.create_index("idx_settlement_rules_type", "settlement_rules", ["rule_type"])
    op.create_index(
        "idx_settlement_rules_effective",
        "settlement_rules",
        ["effective_from", "effective_to"],
    )

    # Phase 2: Create ad_account_balance_snapshots table
    op.create_table(
        "ad_account_balance_snapshots",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("ad_account_id", sa.BigInteger(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("balance", sa.Numeric(15, 2), nullable=False),
        sa.Column("deposit", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("remaining_balance", sa.Numeric(15, 2), nullable=False),
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["ad_account_id"],
            ["ad_accounts.id"],
            name="fk_ad_account_balance_snapshots_ad_account",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_ad_account_balance_snapshots_created_by",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ad_account_id",
            "snapshot_date",
            name="uq_ad_account_balance_snapshots_account_date",
        ),
        sa.CheckConstraint(
            "source IN ('manual', 'api', 'import')",
            name="chk_ad_account_balance_snapshots_source",
        ),
    )
    op.create_index(
        "idx_ad_account_balance_snapshots_date",
        "ad_account_balance_snapshots",
        ["snapshot_date"],
    )
    op.create_index(
        "idx_ad_account_balance_snapshots_account",
        "ad_account_balance_snapshots",
        ["ad_account_id"],
    )
    op.create_index(
        "idx_ad_account_balance_snapshots_account_date",
        "ad_account_balance_snapshots",
        ["ad_account_id", "snapshot_date"],
    )

    # Phase 3: Create reconciliation_issues table
    op.create_table(
        "reconciliation_issues",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("reconciliation_batch_id", sa.BigInteger(), nullable=True),
        sa.Column("ad_account_id", sa.BigInteger(), nullable=True),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("issue_type", sa.String(30), nullable=False),
        sa.Column("expected_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("actual_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column(
            "difference_amount",
            sa.Numeric(15, 2),
            sa.Computed("COALESCE(actual_amount, 0) - COALESCE(expected_amount, 0)"),
            nullable=True,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_type", sa.String(30), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "attachments",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        sa.Column("sla_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sla_breached", sa.Boolean(), server_default="false", nullable=True),
        sa.ForeignKeyConstraint(
            ["reconciliation_batch_id"],
            ["reconciliation_batches.id"],
            name="fk_rec_issues_batch",
        ),
        sa.ForeignKeyConstraint(
            ["ad_account_id"], ["ad_accounts.id"], name="fk_rec_issues_ad_account"
        ),
        sa.ForeignKeyConstraint(
            ["assigned_to"], ["users.id"], name="fk_rec_issues_assigned_to"
        ),
        sa.ForeignKeyConstraint(
            ["resolved_by"], ["users.id"], name="fk_rec_issues_resolved_by"
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name="fk_rec_issues_created_by"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "issue_type IN ('topup_mismatch', 'spend_mismatch', 'deposit_change', 'balance_anomaly', 'snapshot_missing', 'conservation_failed', 'other')",
            name="chk_rec_issues_issue_type",
        ),
        sa.CheckConstraint(
            "status IN ('open', 'assigned', 'investigating', 'resolved', 'closed')",
            name="chk_rec_issues_status",
        ),
        sa.CheckConstraint(
            "resolution_type IS NULL OR resolution_type IN ('data_correction', 'ledger_adjustment', 'external_confirm', 'write_off', 'false_positive')",
            name="chk_rec_issues_resolution_type",
        ),
    )
    op.create_index("idx_rec_issues_status", "reconciliation_issues", ["status"])
    op.create_index("idx_rec_issues_date", "reconciliation_issues", ["issue_date"])
    op.create_index(
        "idx_rec_issues_assigned",
        "reconciliation_issues",
        ["assigned_to"],
        postgresql_where=sa.text("assigned_to IS NOT NULL"),
    )
    op.create_index(
        "idx_rec_issues_batch", "reconciliation_issues", ["reconciliation_batch_id"]
    )

    # Phase 4: Extend projects table
    op.add_column(
        "projects",
        sa.Column(
            "settlement_type", sa.String(20), server_default="fixed", nullable=True
        ),
    )
    op.add_column(
        "projects", sa.Column("settlement_rules_id", sa.BigInteger(), nullable=True)
    )
    op.create_foreign_key(
        "fk_projects_settlement_rules",
        "projects",
        "settlement_rules",
        ["settlement_rules_id"],
        ["id"],
    )
    op.create_check_constraint(
        "chk_projects_settlement_type",
        "projects",
        "settlement_type IN ('fixed', 'tiered', 'markup')",
    )
    op.create_index("idx_projects_settlement_type", "projects", ["settlement_type"])

    # Phase 5: Extend ad_accounts table
    op.add_column(
        "ad_accounts",
        sa.Column("deposit", sa.Numeric(15, 2), server_default="0.00", nullable=True),
    )
    op.add_column(
        "ad_accounts",
        sa.Column("deposit_updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint("chk_ad_accounts_deposit", "ad_accounts", "deposit >= 0")
    op.create_index("idx_ad_accounts_deposit", "ad_accounts", ["deposit"])


def downgrade() -> None:
    # Reverse order of upgrade

    # Phase 5: Remove ad_accounts extensions
    op.drop_index("idx_ad_accounts_deposit", table_name="ad_accounts")
    op.drop_constraint("chk_ad_accounts_deposit", "ad_accounts", type_="check")
    op.drop_column("ad_accounts", "deposit_updated_at")
    op.drop_column("ad_accounts", "deposit")

    # Phase 4: Remove projects extensions
    op.drop_index("idx_projects_settlement_type", table_name="projects")
    op.drop_constraint("chk_projects_settlement_type", "projects", type_="check")
    op.drop_constraint("fk_projects_settlement_rules", "projects", type_="foreignkey")
    op.drop_column("projects", "settlement_rules_id")
    op.drop_column("projects", "settlement_type")

    # Phase 3: Drop reconciliation_issues
    op.drop_index("idx_rec_issues_batch", table_name="reconciliation_issues")
    op.drop_index("idx_rec_issues_assigned", table_name="reconciliation_issues")
    op.drop_index("idx_rec_issues_date", table_name="reconciliation_issues")
    op.drop_index("idx_rec_issues_status", table_name="reconciliation_issues")
    op.drop_table("reconciliation_issues")

    # Phase 2: Drop ad_account_balance_snapshots
    op.drop_index(
        "idx_ad_account_balance_snapshots_account_date",
        table_name="ad_account_balance_snapshots",
    )
    op.drop_index(
        "idx_ad_account_balance_snapshots_account",
        table_name="ad_account_balance_snapshots",
    )
    op.drop_index(
        "idx_ad_account_balance_snapshots_date",
        table_name="ad_account_balance_snapshots",
    )
    op.drop_table("ad_account_balance_snapshots")

    # Phase 1: Drop settlement_rules
    op.drop_index("idx_settlement_rules_effective", table_name="settlement_rules")
    op.drop_index("idx_settlement_rules_type", table_name="settlement_rules")
    op.drop_table("settlement_rules")
