"""Add profit aggregates and report snapshots tables

Revision ID: 20260102_add_profit_tables
Revises: 20260102_add_receivable_table
Create Date: 2026-01-02

Affected SoT:
- DATA_SCHEMA.md v5.9 §3.6.1, §3.6.2
- PROFIT_SOT.md v1.1

Changes:
- Add profit_aggregates table (L2 汇总层)
- Add profit_report_snapshots table (报表快照层)
- Add updated_at trigger for profit_aggregates

Business Logic:
- BR-PROFIT-001: gross_profit = total_revenue - total_cost
- BR-PROFIT-002: total_topup 不参与毛利计算
- BR-PROFIT-003: 仅聚合 final_locked 状态的日报
- BR-PROFIT-005: is_locked = TRUE 时禁止重新生成
- BR-PROFIT-006: 月度报表基于 L2 聚合层生成
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260102_add_profit_tables"
down_revision = "20260102_add_receivable_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =====================================================================
    # Create profit_aggregates table (L2 汇总层)
    # DATA_SCHEMA.md v5.9 §3.6.1
    # =====================================================================
    op.create_table(
        "profit_aggregates",
        # Primary key
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
            comment="聚合记录ID",
        ),
        # Period fields
        sa.Column(
            "period_type",
            sa.String(20),
            nullable=False,
            comment="周期类型：daily/weekly/monthly",
        ),
        sa.Column(
            "period_start",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="周期开始时间",
        ),
        sa.Column(
            "period_end",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="周期结束时间",
        ),
        # Dimension fields (FK)
        sa.Column(
            "project_id",
            sa.BigInteger(),
            nullable=True,
            comment="项目ID，NULL表示全局汇总",
        ),
        sa.Column(
            "ad_account_id",
            sa.BigInteger(),
            nullable=True,
            comment="账户ID，NULL表示项目级汇总",
        ),
        # Core metrics - DECIMAL(18,2)
        sa.Column(
            "total_revenue",
            sa.Numeric(18, 2),
            server_default="0.00",
            nullable=False,
            comment="总收入，派生自 ledger_entries(entry_type='REVENUE')",
        ),
        sa.Column(
            "total_cost",
            sa.Numeric(18, 2),
            server_default="0.00",
            nullable=False,
            comment="总成本，派生自 ledger_entries(entry_type='COST')",
        ),
        sa.Column(
            "gross_profit",
            sa.Numeric(18, 2),
            server_default="0.00",
            nullable=False,
            comment="毛利，派生字段：total_revenue - total_cost (BR-PROFIT-001)",
        ),
        sa.Column(
            "gross_margin_pct",
            sa.Numeric(5, 2),
            nullable=True,
            comment="毛利率(%)，revenue=0时为NULL",
        ),
        # Auxiliary statistics
        sa.Column(
            "total_conversions",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
            comment="转化数，派生自 daily_reports.conversions_final(status='final_locked')",
        ),
        sa.Column(
            "total_real_spend",
            sa.Numeric(18, 2),
            server_default="0.00",
            nullable=False,
            comment="实际消耗，派生自 daily_reports.real_spend",
        ),
        sa.Column(
            "total_topup",
            sa.Numeric(18, 2),
            server_default="0.00",
            nullable=False,
            comment="充值金额，仅统计资金流入，不参与毛利计算(BR-PROFIT-002)",
        ),
        sa.Column(
            "transfer_in",
            sa.Numeric(18, 2),
            server_default="0.00",
            nullable=False,
            comment="转入金额",
        ),
        sa.Column(
            "transfer_out",
            sa.Numeric(18, 2),
            server_default="0.00",
            nullable=False,
            comment="转出金额",
        ),
        # Lock fields
        sa.Column(
            "is_locked",
            sa.Boolean(),
            server_default="false",
            nullable=False,
            comment="是否锁定，锁定后不可重新生成(BR-PROFIT-005)",
        ),
        sa.Column(
            "locked_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="锁定时间",
        ),
        sa.Column(
            "locked_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="锁定人",
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
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_profit_agg_project",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["ad_account_id"],
            ["ad_accounts.id"],
            name="fk_profit_agg_account",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["locked_by"],
            ["users.id"],
            name="fk_profit_agg_locked_by",
            ondelete="SET NULL",
        ),
        sa.CheckConstraint(
            "period_type IN ('daily', 'weekly', 'monthly')",
            name="chk_profit_agg_period_type",
        ),
        sa.UniqueConstraint(
            "period_type",
            "period_start",
            "project_id",
            "ad_account_id",
            name="uq_profit_agg_period_dimension",
        ),
        comment="利润聚合表（L2汇总层）- PROFIT_SOT.md v1.1",
    )

    # profit_aggregates indexes
    op.create_index("idx_profit_agg_period_type", "profit_aggregates", ["period_type"])
    op.create_index(
        "idx_profit_agg_period_start", "profit_aggregates", ["period_start"]
    )
    op.create_index("idx_profit_agg_project", "profit_aggregates", ["project_id"])
    op.create_index("idx_profit_agg_account", "profit_aggregates", ["ad_account_id"])
    op.create_index("idx_profit_agg_locked", "profit_aggregates", ["is_locked"])

    # =====================================================================
    # Create profit_report_snapshots table (报表快照层)
    # DATA_SCHEMA.md v5.9 §3.6.2
    # =====================================================================
    op.create_table(
        "profit_report_snapshots",
        # Primary key
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
            comment="报表快照ID",
        ),
        # Report type and period
        sa.Column(
            "report_type",
            sa.String(30),
            nullable=False,
            comment="报表类型：monthly_summary/project_detail/account_detail",
        ),
        sa.Column(
            "period_month",
            sa.String(7),
            nullable=False,
            comment="月份，格式 YYYY-MM",
        ),
        # Dimension field (FK)
        sa.Column(
            "project_id",
            sa.BigInteger(),
            nullable=True,
            comment="项目ID，NULL表示全局报表",
        ),
        # Report data
        sa.Column(
            "report_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            comment="报表数据，包含聚合指标和明细(BR-PROFIT-006)",
        ),
        # Status field
        sa.Column(
            "status",
            sa.String(20),
            server_default="draft",
            nullable=False,
            comment="报表状态：draft/confirmed/locked",
        ),
        # Generation info
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
            comment="生成时间",
        ),
        sa.Column(
            "generated_by",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="生成人",
        ),
        # Confirmation info
        sa.Column(
            "confirmed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="确认时间",
        ),
        sa.Column(
            "confirmed_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="确认人",
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_profit_snap_project",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["generated_by"],
            ["users.id"],
            name="fk_profit_snap_generated_by",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["confirmed_by"],
            ["users.id"],
            name="fk_profit_snap_confirmed_by",
            ondelete="SET NULL",
        ),
        sa.CheckConstraint(
            "report_type IN ('monthly_summary', 'project_detail', 'account_detail')",
            name="chk_profit_snap_report_type",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'confirmed', 'locked')",
            name="chk_profit_snap_status",
        ),
        sa.UniqueConstraint(
            "report_type",
            "period_month",
            "project_id",
            name="uq_profit_snap_type_month_project",
        ),
        comment="利润报表快照表 - PROFIT_SOT.md v1.1",
    )

    # profit_report_snapshots indexes
    op.create_index(
        "idx_profit_snap_report_type", "profit_report_snapshots", ["report_type"]
    )
    op.create_index(
        "idx_profit_snap_period_month", "profit_report_snapshots", ["period_month"]
    )
    op.create_index(
        "idx_profit_snap_project", "profit_report_snapshots", ["project_id"]
    )
    op.create_index("idx_profit_snap_status", "profit_report_snapshots", ["status"])

    # =====================================================================
    # Create updated_at trigger for profit_aggregates
    # =====================================================================
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_profit_aggregates_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """
    )

    op.execute(
        """
        DROP TRIGGER IF EXISTS update_profit_aggregates_updated_at ON profit_aggregates;
        CREATE TRIGGER update_profit_aggregates_updated_at
            BEFORE UPDATE ON profit_aggregates
            FOR EACH ROW
            EXECUTE FUNCTION update_profit_aggregates_updated_at()
    """
    )


def downgrade() -> None:
    # Drop trigger and function
    op.execute(
        "DROP TRIGGER IF EXISTS update_profit_aggregates_updated_at ON profit_aggregates"
    )
    op.execute("DROP FUNCTION IF EXISTS update_profit_aggregates_updated_at()")

    # Drop indexes for profit_report_snapshots
    op.drop_index("idx_profit_snap_status", table_name="profit_report_snapshots")
    op.drop_index("idx_profit_snap_project", table_name="profit_report_snapshots")
    op.drop_index("idx_profit_snap_period_month", table_name="profit_report_snapshots")
    op.drop_index("idx_profit_snap_report_type", table_name="profit_report_snapshots")

    # Drop profit_report_snapshots table
    op.drop_table("profit_report_snapshots")

    # Drop indexes for profit_aggregates
    op.drop_index("idx_profit_agg_locked", table_name="profit_aggregates")
    op.drop_index("idx_profit_agg_account", table_name="profit_aggregates")
    op.drop_index("idx_profit_agg_project", table_name="profit_aggregates")
    op.drop_index("idx_profit_agg_period_start", table_name="profit_aggregates")
    op.drop_index("idx_profit_agg_period_type", table_name="profit_aggregates")

    # Drop profit_aggregates table
    op.drop_table("profit_aggregates")
