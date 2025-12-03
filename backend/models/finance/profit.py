"""
利润聚合与报表模块（对齐 PROFIT_SOT.md v1.1 + DATA_SCHEMA.md v5.2 §3.6）

包含：
- ProfitAggregate: 利润聚合表（L2 汇总层）
- ProfitReportSnapshot: 利润报表快照表
- ProfitPeriodType: 周期类型枚举
- ProfitReportType: 报表类型枚举
- ProfitReportStatus: 报表状态枚举

设计来源：
- PROFIT_SOT.md v1.1
- OpenSpec Change: finance-profit-v1

FK 类型对齐说明（DATA_SCHEMA.md v5.2）：
- project_id: BigInteger FK → projects.id (BIGSERIAL)
- ad_account_id: BigInteger FK → ad_accounts.id (BIGSERIAL)
- user_id (locked_by, generated_by, confirmed_by): UUID FK → users.id (UUID)
"""

from enum import Enum as PyEnum

from sqlalchemy import (
    Column, BigInteger, String, Text, Numeric, DateTime, Index,
    CheckConstraint, UniqueConstraint, ForeignKey, Boolean
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base, TimestampMixin


# =====================================================================
# Enum 枚举定义 (对齐 PROFIT_SOT.md v1.1)
# =====================================================================

class ProfitPeriodType(str, PyEnum):
    """
    利润聚合周期类型枚举

    必须与 PROFIT_SOT.md v1.1 §2.1 保持一致。
    """
    DAILY = "daily"      # 日度聚合
    WEEKLY = "weekly"    # 周度聚合
    MONTHLY = "monthly"  # 月度聚合


class ProfitReportType(str, PyEnum):
    """
    利润报表类型枚举

    必须与 PROFIT_SOT.md v1.1 §2.2 保持一致。
    """
    MONTHLY_SUMMARY = "monthly_summary"    # 月度汇总报表
    PROJECT_DETAIL = "project_detail"      # 项目明细报表
    ACCOUNT_DETAIL = "account_detail"      # 账户明细报表


class ProfitReportStatus(str, PyEnum):
    """
    利润报表状态枚举

    必须与 PROFIT_SOT.md v1.1 §2.2 保持一致。
    """
    DRAFT = "draft"          # 草稿
    CONFIRMED = "confirmed"  # 已确认
    LOCKED = "locked"        # 已锁定


# =====================================================================
# Model 定义 (对齐 DATA_SCHEMA.md v5.2 §3.6 + PROFIT_SOT.md v1.1)
# =====================================================================

class ProfitAggregate(Base, TimestampMixin):
    """
    利润聚合表（L2 汇总层）

    存储按周期/维度聚合的利润数据。
    聚合来源：daily_reports（仅 final_locked 状态）+ ledger_entries

    业务规则引用（PROFIT_SOT.md v1.1 §4）：
    - BR-PROFIT-001: gross_profit = total_revenue - total_cost
    - BR-PROFIT-002: total_topup 不参与利润计算（仅统计资金流入）
    - BR-PROFIT-003: 仅聚合 daily_reports.status = 'final_locked' 的数据
    - BR-PROFIT-005: is_locked = TRUE 时禁止重新生成

    FK 类型对齐：
    - id: BIGSERIAL (BigInteger autoincrement)
    - project_id: BIGINT FK → projects.id
    - ad_account_id: BIGINT FK → ad_accounts.id
    - locked_by: UUID FK → users.id
    """
    __tablename__ = 'profit_aggregates'

    # 主键：BIGSERIAL
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="聚合记录ID"
    )

    # 周期字段
    period_type = Column(
        String(20),
        nullable=False,
        index=True,
        comment="周期类型：daily/weekly/monthly"
    )
    period_start = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="周期开始时间"
    )
    period_end = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="周期结束时间"
    )

    # 维度字段 - FK 类型必须与 parent PK 一致
    project_id = Column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="项目ID，NULL表示全局汇总"
    )
    ad_account_id = Column(
        BigInteger,
        ForeignKey("ad_accounts.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="账户ID，NULL表示项目级汇总"
    )

    # 核心指标字段 - 金额使用 DECIMAL(18,2)
    total_revenue = Column(
        Numeric(18, 2),
        nullable=False,
        default=0,
        server_default='0.00',
        comment="总收入，派生自 ledger_entries(entry_type='REVENUE')"
    )
    total_cost = Column(
        Numeric(18, 2),
        nullable=False,
        default=0,
        server_default='0.00',
        comment="总成本，派生自 ledger_entries(entry_type='COST')"
    )
    gross_profit = Column(
        Numeric(18, 2),
        nullable=False,
        default=0,
        server_default='0.00',
        comment="毛利，派生字段：total_revenue - total_cost"
    )
    gross_margin_pct = Column(
        Numeric(5, 2),
        nullable=True,
        comment="毛利率(%)，派生字段：(gross_profit/total_revenue)×100，HALF_UP四舍五入，revenue=0时为NULL"
    )

    # 辅助统计字段
    total_conversions = Column(
        BigInteger,
        nullable=False,
        default=0,
        server_default='0',
        comment="转化数，派生自 daily_reports.conversions_final(status='final_locked')"
    )
    total_real_spend = Column(
        Numeric(18, 2),
        nullable=False,
        default=0,
        server_default='0.00',
        comment="实际消耗，派生自 daily_reports.real_spend(status='final_locked')"
    )
    total_topup = Column(
        Numeric(18, 2),
        nullable=False,
        default=0,
        server_default='0.00',
        comment="充值金额，仅统计资金流入，不参与毛利计算(BR-PROFIT-002)"
    )
    transfer_in = Column(
        Numeric(18, 2),
        nullable=False,
        default=0,
        server_default='0.00',
        comment="转入金额，派生自 ledger_entries(entry_type='TRANSFER_IN')"
    )
    transfer_out = Column(
        Numeric(18, 2),
        nullable=False,
        default=0,
        server_default='0.00',
        comment="转出金额，派生自 ledger_entries(entry_type='TRANSFER_OUT')"
    )

    # 锁定字段
    is_locked = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default='false',
        index=True,
        comment="是否锁定，锁定后不可重新生成(BR-PROFIT-005)"
    )
    locked_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="锁定时间"
    )
    locked_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="锁定人"
    )

    # 约束和索引
    __table_args__ = (
        CheckConstraint(
            "period_type IN ('daily', 'weekly', 'monthly')",
            name='chk_profit_agg_period_type'
        ),
        UniqueConstraint(
            'period_type', 'period_start', 'project_id', 'ad_account_id',
            name='uq_profit_agg_period_dimension'
        ),
        Index('idx_profit_agg_period_type', 'period_type'),
        Index('idx_profit_agg_period_start', 'period_start'),
        Index('idx_profit_agg_project', 'project_id'),
        Index('idx_profit_agg_account', 'ad_account_id'),
        Index('idx_profit_agg_locked', 'is_locked'),
        {'comment': '利润聚合表（L2汇总层）- PROFIT_SOT.md v1.1'}
    )

    # 关系
    project = relationship("Project", foreign_keys=[project_id])
    ad_account = relationship("AdAccount", foreign_keys=[ad_account_id])
    locker = relationship("User", foreign_keys=[locked_by])

    def __repr__(self):
        return (
            f"<ProfitAggregate(id={self.id}, period={self.period_type}, "
            f"start={self.period_start}, project_id={self.project_id}, "
            f"gross_profit={self.gross_profit})>"
        )


class ProfitReportSnapshot(Base):
    """
    利润报表快照表

    存储生成的利润报表 JSON 数据，支持 draft/confirmed/locked 三态管理。

    业务规则引用（PROFIT_SOT.md v1.1 §4）：
    - BR-PROFIT-006: 月度报表基于 L2 聚合层 (profit_aggregates) 生成

    FK 类型对齐：
    - id: BIGSERIAL (BigInteger autoincrement)
    - project_id: BIGINT FK → projects.id
    - generated_by, confirmed_by: UUID FK → users.id
    """
    __tablename__ = 'profit_report_snapshots'

    # 主键：BIGSERIAL
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="报表快照ID"
    )

    # 报表类型和周期
    report_type = Column(
        String(30),
        nullable=False,
        index=True,
        comment="报表类型：monthly_summary/project_detail/account_detail"
    )
    period_month = Column(
        String(7),
        nullable=False,
        index=True,
        comment="月份，格式 YYYY-MM"
    )

    # 维度字段
    project_id = Column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="项目ID，NULL表示全局报表"
    )

    # 报表数据
    report_data = Column(
        JSONB,
        nullable=False,
        comment="报表数据，包含聚合指标和明细"
    )

    # 状态字段
    status = Column(
        String(20),
        nullable=False,
        default='draft',
        server_default='draft',
        index=True,
        comment="报表状态：draft/confirmed/locked"
    )

    # 生成信息
    generated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="生成时间"
    )
    generated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        comment="生成人"
    )

    # 确认信息
    confirmed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="确认时间"
    )
    confirmed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="确认人"
    )

    # 创建时间
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="创建时间"
    )

    # 约束和索引
    __table_args__ = (
        CheckConstraint(
            "report_type IN ('monthly_summary', 'project_detail', 'account_detail')",
            name='chk_profit_snap_report_type'
        ),
        CheckConstraint(
            "status IN ('draft', 'confirmed', 'locked')",
            name='chk_profit_snap_status'
        ),
        UniqueConstraint(
            'report_type', 'period_month', 'project_id',
            name='uq_profit_snap_type_month_project'
        ),
        Index('idx_profit_snap_report_type', 'report_type'),
        Index('idx_profit_snap_period_month', 'period_month'),
        Index('idx_profit_snap_project', 'project_id'),
        Index('idx_profit_snap_status', 'status'),
        {'comment': '利润报表快照表 - PROFIT_SOT.md v1.1'}
    )

    # 关系
    project = relationship("Project", foreign_keys=[project_id])
    generator = relationship("User", foreign_keys=[generated_by])
    confirmer = relationship("User", foreign_keys=[confirmed_by])

    def __repr__(self):
        return (
            f"<ProfitReportSnapshot(id={self.id}, type={self.report_type}, "
            f"month={self.period_month}, status={self.status})>"
        )
