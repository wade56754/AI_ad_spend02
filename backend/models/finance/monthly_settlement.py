"""
月度结算模型 - TASK-FIN-003 月度锁账
Version: 1.0
Author: Claude Code (TASK-FIN-003)

Aligned with SoT:
- DATA_SCHEMA.md v5.7 §3.7.1 (monthly_settlements 表结构)
- STATE_MACHINE.md v2.9 §13.1 (月度结算状态机)
- BUSINESS_RULES.md v5.0 (BR-FIN-007: 锁定后不可改)
- MASTER.md v4.8 §2.4 (CEO 角色: 月度锁账确认)

状态机流转: pending → confirmed → locked → archived
                ↑          ↓
                └──────────┘ (退回修正)

Phase 1 约束: locked 状态可由 admin 解锁（软性锁定）
Phase 2 约束: locked 后不可解锁，需走冲正流程
"""

from datetime import date
from decimal import Decimal
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    Numeric,
    Index,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from backend.models.base import Base, TimestampMixin
from backend.models.mixins.serializable import SerializableMixin
from backend.core.state_machine import SettlementStatus


class MonthlySettlement(Base, TimestampMixin, SerializableMixin):
    """
    月度结算表 - 月度锁账管理

    SoT Reference: DATA_SCHEMA.md v5.7 §3.7.1

    字段：
    - id: 主键 (BIGSERIAL)
    - project_id: 项目ID (FK → projects.id)
    - settlement_month: 结算月份 (YYYY-MM-01)
    - total_spend: 月消耗总额
    - total_conversions: 月进粉总数
    - total_revenue: 月收入 (粉数 × 单价)
    - gross_profit: 月毛利 (收入 - 消耗)
    - average_cpl: 月均 CPL
    - status: 状态 (pending/confirmed/locked/archived)
    - confirmed_at/confirmed_by: 财务确认时间/人
    - locked_at/locked_by: 锁定时间/人
    - notes: 结算备注
    - created_at/updated_at: 时间戳

    约束：
    - UNIQUE (project_id, settlement_month) - 每个项目每月仅一条
    - settlement_month 必须为月初日期 (DAY = 1)
    """

    __tablename__ = "monthly_settlements"

    # 序列化配置
    __json_include_relationships__ = ["project", "confirmed_by_user", "locked_by_user"]

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="月度结算ID")

    # 外键: 项目
    project_id = Column(
        BigInteger,
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        comment="项目ID",
    )

    # 结算月份 (YYYY-MM-01)
    settlement_month = Column(
        Date,
        nullable=False,
        comment="结算月份 (YYYY-MM-01)",
    )

    # 汇总数据 (从 daily_reports 聚合)
    total_spend = Column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="月消耗总额 (SUM of real_spend)",
    )

    total_conversions = Column(
        Integer,
        nullable=False,
        default=0,
        comment="月进粉总数 (SUM of conversions_final)",
    )

    total_revenue = Column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="月收入 (total_conversions × unit_price)",
    )

    gross_profit = Column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="月毛利 (total_revenue - total_spend)",
    )

    average_cpl = Column(
        Numeric(10, 2),
        nullable=True,
        comment="月均 CPL (total_spend / total_conversions)",
    )

    # 状态 (STATE_MACHINE.md v2.9 §13.1)
    status = Column(
        String(20),
        nullable=False,
        default=SettlementStatus.PENDING.value,
        comment="状态: pending/confirmed/locked/archived",
    )

    # 财务确认信息
    confirmed_at = Column(
        Date,
        nullable=True,
        comment="财务确认时间",
    )

    confirmed_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="确认人ID",
    )

    # 锁定信息 (CEO/admin)
    locked_at = Column(
        Date,
        nullable=True,
        comment="锁定时间",
    )

    locked_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="锁定人ID",
    )

    # 备注
    notes = Column(
        Text,
        nullable=True,
        comment="结算备注",
    )

    # ========== 关系定义 ==========

    # 多对一: 月度结算 -> 项目
    project = relationship(
        "Project",
        foreign_keys=[project_id],
        lazy="selectin",
        doc="关联项目",
    )

    # 多对一: 月度结算 -> 确认人
    confirmed_by_user = relationship(
        "User",
        foreign_keys=[confirmed_by],
        lazy="selectin",
        doc="确认人",
    )

    # 多对一: 月度结算 -> 锁定人
    locked_by_user = relationship(
        "User",
        foreign_keys=[locked_by],
        lazy="selectin",
        doc="锁定人",
    )

    # ========== 约束与索引 ==========
    __table_args__ = (
        # 唯一约束: 每个项目每月仅一条
        UniqueConstraint(
            "project_id",
            "settlement_month",
            name="uq_monthly_settlements_project_month",
        ),
        # 状态检查
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'locked', 'archived')",
            name="chk_monthly_settlements_status",
        ),
        # 金额非负
        CheckConstraint(
            "total_spend >= 0",
            name="chk_monthly_settlements_spend_positive",
        ),
        CheckConstraint(
            "total_conversions >= 0",
            name="chk_monthly_settlements_conversions_positive",
        ),
        # 索引
        Index("idx_monthly_settlements_project", "project_id"),
        Index("idx_monthly_settlements_month", "settlement_month"),
        Index("idx_monthly_settlements_status", "status"),
        Index(
            "idx_monthly_settlements_project_month", "project_id", "settlement_month"
        ),
    )

    def __repr__(self):
        return f"<MonthlySettlement(id={self.id}, project_id={self.project_id}, month='{self.settlement_month}', status='{self.status}')>"

    # ========== 业务属性 ==========

    @property
    def is_locked(self) -> bool:
        """是否已锁定 (终态)"""
        return self.status in [
            SettlementStatus.LOCKED.value,
            SettlementStatus.ARCHIVED.value,
        ]

    @property
    def is_editable(self) -> bool:
        """是否可编辑 (仅 pending 状态)"""
        return self.status == SettlementStatus.PENDING.value

    @property
    def can_confirm(self) -> bool:
        """是否可确认 (finance/admin)"""
        return self.status == SettlementStatus.PENDING.value

    @property
    def can_lock(self) -> bool:
        """是否可锁定 (ceo/admin)"""
        return self.status == SettlementStatus.CONFIRMED.value

    @property
    def can_archive(self) -> bool:
        """是否可归档 (admin)"""
        return self.status == SettlementStatus.LOCKED.value

    # ========== 计算方法 ==========

    def calculate_metrics(self, unit_price: Decimal) -> None:
        """
        计算收入、毛利、CPL

        Args:
            unit_price: 项目单价 (projects.unit_price)

        公式 (BUSINESS_RULES.md v5.0):
        - total_revenue = total_conversions × unit_price
        - gross_profit = total_revenue - total_spend
        - average_cpl = total_spend / total_conversions (if conversions > 0)
        """
        self.total_revenue = Decimal(self.total_conversions) * unit_price
        self.gross_profit = self.total_revenue - self.total_spend

        if self.total_conversions > 0:
            self.average_cpl = self.total_spend / Decimal(self.total_conversions)
        else:
            self.average_cpl = None

    @staticmethod
    def get_month_start(dt: date) -> date:
        """获取月初日期"""
        return dt.replace(day=1)
