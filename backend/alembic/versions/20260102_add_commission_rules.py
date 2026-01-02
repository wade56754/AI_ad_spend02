"""Add commission rules table and project FK

Revision ID: 20260102_add_commission_rules
Revises: 20251226_add_reconciliation_control_center
Create Date: 2026-01-02

TASK-PRJ-003: 提成配置
Affected SoT: DATA_SCHEMA.md v5.7 §3.5.8

Changes:
- Add commission_rules table (tiered pitcher commission)
- Extend projects table (commission_rules_id FK)

Business Logic:
- 阶梯提成: 按 conversions_final 计算
- 累加公式: Σ(tier.count × tier.rate)
- 按月累计，按项目计算
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260102_add_commission_rules"
down_revision = "20251226_add_reconciliation_control_center"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Phase 1: Create commission_rules table
    op.create_table(
        "commission_rules",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False, comment="规则名称"),
        sa.Column(
            "config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            comment="阶梯提成配置JSON {tiers: [{min, max, rate}]}",
        ),
        sa.Column(
            "effective_from",
            sa.Date(),
            nullable=False,
            comment="生效开始日",
        ),
        sa.Column(
            "effective_to",
            sa.Date(),
            nullable=True,
            comment="生效结束日 (null=永久)",
        ),
        sa.Column(
            "is_default",
            sa.Boolean(),
            server_default="false",
            nullable=False,
            comment="是否为默认规则",
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="创建者",
        ),
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
            ["created_by"],
            ["users.id"],
            name="fk_commission_rules_created_by",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from",
            name="chk_commission_rules_effective_period",
        ),
        comment="提成规则表 (TASK-PRJ-003)",
    )
    op.create_index(
        "idx_commission_rules_effective",
        "commission_rules",
        ["effective_from", "effective_to"],
    )
    op.create_index(
        "idx_commission_rules_default",
        "commission_rules",
        ["is_default"],
        postgresql_where=sa.text("is_default = true"),
    )

    # Phase 2: Extend projects table with commission_rules_id
    op.add_column(
        "projects",
        sa.Column(
            "commission_rules_id",
            sa.BigInteger(),
            nullable=True,
            comment="提成规则ID (基于 conversions_final 计算投手提成)",
        ),
    )
    op.create_foreign_key(
        "fk_projects_commission_rules",
        "projects",
        "commission_rules",
        ["commission_rules_id"],
        ["id"],
    )
    op.create_index(
        "idx_projects_commission_rules",
        "projects",
        ["commission_rules_id"],
    )


def downgrade() -> None:
    # Reverse order of upgrade

    # Phase 2: Remove projects extensions
    op.drop_index("idx_projects_commission_rules", table_name="projects")
    op.drop_constraint("fk_projects_commission_rules", "projects", type_="foreignkey")
    op.drop_column("projects", "commission_rules_id")

    # Phase 1: Drop commission_rules
    op.drop_index("idx_commission_rules_default", table_name="commission_rules")
    op.drop_index("idx_commission_rules_effective", table_name="commission_rules")
    op.drop_table("commission_rules")
