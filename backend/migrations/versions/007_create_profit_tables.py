"""创建利润聚合与报表快照表

Revision ID: 007
Revises: 006
Create Date: 2025-12-02

对齐文档：
- PROFIT_SOT.md v1.1
- DATA_SCHEMA.md v5.2 §3.6
- OpenSpec Change: finance-profit-v1
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =====================================================================
    # 创建 profit_aggregates 表（L2 汇总层）
    # 对齐 DATA_SCHEMA.md v5.2 §3.6.1
    # =====================================================================
    op.execute("""
        CREATE TABLE IF NOT EXISTS profit_aggregates (
            -- 主键
            id BIGSERIAL PRIMARY KEY,

            -- 周期字段
            period_type VARCHAR(20) NOT NULL CHECK (period_type IN ('daily', 'weekly', 'monthly')),
            period_start TIMESTAMPTZ NOT NULL,
            period_end TIMESTAMPTZ NOT NULL,

            -- 维度字段（FK）
            project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
            ad_account_id BIGINT REFERENCES ad_accounts(id) ON DELETE CASCADE,

            -- 核心指标字段
            total_revenue DECIMAL(18,2) NOT NULL DEFAULT 0.00,
            total_cost DECIMAL(18,2) NOT NULL DEFAULT 0.00,
            gross_profit DECIMAL(18,2) NOT NULL DEFAULT 0.00,
            gross_margin_pct DECIMAL(5,2),

            -- 辅助统计字段
            total_conversions BIGINT NOT NULL DEFAULT 0,
            total_real_spend DECIMAL(18,2) NOT NULL DEFAULT 0.00,
            total_topup DECIMAL(18,2) NOT NULL DEFAULT 0.00,
            transfer_in DECIMAL(18,2) NOT NULL DEFAULT 0.00,
            transfer_out DECIMAL(18,2) NOT NULL DEFAULT 0.00,

            -- 锁定字段
            is_locked BOOLEAN NOT NULL DEFAULT FALSE,
            locked_at TIMESTAMPTZ,
            locked_by UUID REFERENCES users(id) ON DELETE SET NULL,

            -- 时间戳
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

            -- 唯一约束：同周期同维度仅一条记录
            CONSTRAINT uq_profit_agg_period_dimension
                UNIQUE (period_type, period_start, project_id, ad_account_id)
        )
    """)

    # profit_aggregates 索引
    op.execute("CREATE INDEX IF NOT EXISTS idx_profit_agg_period_type ON profit_aggregates(period_type)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_profit_agg_period_start ON profit_aggregates(period_start)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_profit_agg_project ON profit_aggregates(project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_profit_agg_account ON profit_aggregates(ad_account_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_profit_agg_locked ON profit_aggregates(is_locked)")

    # profit_aggregates 表注释
    op.execute("COMMENT ON TABLE profit_aggregates IS '利润聚合表（L2汇总层）- PROFIT_SOT.md v1.1'")
    op.execute("COMMENT ON COLUMN profit_aggregates.total_topup IS '充值金额，仅统计资金流入，不参与毛利计算(BR-PROFIT-002)'")
    op.execute("COMMENT ON COLUMN profit_aggregates.gross_profit IS '毛利，派生字段：total_revenue - total_cost (BR-PROFIT-001)'")
    op.execute("COMMENT ON COLUMN profit_aggregates.is_locked IS '是否锁定，锁定后不可重新生成(BR-PROFIT-005)'")

    # =====================================================================
    # 创建 profit_report_snapshots 表（报表快照层）
    # 对齐 DATA_SCHEMA.md v5.2 §3.6.2
    # =====================================================================
    op.execute("""
        CREATE TABLE IF NOT EXISTS profit_report_snapshots (
            -- 主键
            id BIGSERIAL PRIMARY KEY,

            -- 报表类型和周期
            report_type VARCHAR(30) NOT NULL CHECK (
                report_type IN ('monthly_summary', 'project_detail', 'account_detail')
            ),
            period_month VARCHAR(7) NOT NULL,

            -- 维度字段（FK）
            project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,

            -- 报表数据
            report_data JSONB NOT NULL,

            -- 状态字段
            status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (
                status IN ('draft', 'confirmed', 'locked')
            ),

            -- 生成信息
            generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            generated_by UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,

            -- 确认信息
            confirmed_at TIMESTAMPTZ,
            confirmed_by UUID REFERENCES users(id) ON DELETE SET NULL,

            -- 时间戳
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

            -- 唯一约束：同类型同月份同项目仅一份报表
            CONSTRAINT uq_profit_snap_type_month_project
                UNIQUE (report_type, period_month, project_id)
        )
    """)

    # profit_report_snapshots 索引
    op.execute("CREATE INDEX IF NOT EXISTS idx_profit_snap_report_type ON profit_report_snapshots(report_type)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_profit_snap_period_month ON profit_report_snapshots(period_month)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_profit_snap_project ON profit_report_snapshots(project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_profit_snap_status ON profit_report_snapshots(status)")

    # profit_report_snapshots 表注释
    op.execute("COMMENT ON TABLE profit_report_snapshots IS '利润报表快照表 - PROFIT_SOT.md v1.1'")
    op.execute("COMMENT ON COLUMN profit_report_snapshots.report_data IS '报表数据，包含聚合指标和明细(BR-PROFIT-006)'")

    # =====================================================================
    # 创建 updated_at 触发器函数（如不存在）
    # =====================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION update_profit_aggregates_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    # 为 profit_aggregates 创建 updated_at 触发器
    op.execute("""
        DROP TRIGGER IF EXISTS update_profit_aggregates_updated_at ON profit_aggregates;
        CREATE TRIGGER update_profit_aggregates_updated_at
            BEFORE UPDATE ON profit_aggregates
            FOR EACH ROW
            EXECUTE FUNCTION update_profit_aggregates_updated_at()
    """)


def downgrade() -> None:
    # 删除触发器和函数
    op.execute("DROP TRIGGER IF EXISTS update_profit_aggregates_updated_at ON profit_aggregates")
    op.execute("DROP FUNCTION IF EXISTS update_profit_aggregates_updated_at()")

    # 删除表（按依赖关系倒序）
    op.execute("DROP TABLE IF EXISTS profit_report_snapshots")
    op.execute("DROP TABLE IF EXISTS profit_aggregates")
