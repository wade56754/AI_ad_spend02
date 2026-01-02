"""
项目预付款模型 - 记录客户预付款入账

TASK-PRJ-005: 预付款管理
SoT: DATA_SCHEMA.md v5.7 §3.4 (三本账体系 - 预付款账本)

预付款账本（PROJECT）用途：
- 记录客户付给我们的钱
- 余额表示还"欠"客户多少（待消耗）
- 只有履约完成后才能确认为收入
"""
from decimal import Decimal
from datetime import datetime
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    Numeric,
    Date,
    DateTime,
    Index,
    CheckConstraint,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base, TimestampMixin
from backend.models.mixins.serializable import SerializableMixin


class PrepaymentEntryType:
    """预付款分录类型"""

    TOPUP = "TOPUP"  # 入账（客户付款）
    REVERSAL = "REVERSAL"  # 红冲（冲销）


class ProjectPrepayment(Base, TimestampMixin, SerializableMixin):
    """
    项目预付款记录表

    TASK-PRJ-005: 预付款管理
    SoT: DATA_SCHEMA.md v5.7 §3.4.4 (三本账体系)

    业务规则 (BR-FIN-004):
    - 预收款≠收入：履约完成前是负债
    - 充值到账后计入 entry_type=TOPUP
    - 收入仅在 daily_reports.status=final_locked 后确认

    字段：
    - id: 主键
    - project_id: 项目ID（FK）
    - entry_type: 分录类型（TOPUP/REVERSAL）
    - amount: 金额（正数为入账，负数为红冲）
    - balance_after: 交易后余额
    - entry_date: 入账日期
    - reference_id: 关联记录ID（红冲时必填）
    - reference_type: 关联记录类型
    - notes: 备注
    - created_by: 操作人ID
    - created_at: 创建时间
    """

    __tablename__ = "project_prepayments"

    # 序列化配置
    __json_include_relationships__ = ["project", "operator"]

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="记录ID")

    # 外键
    project_id = Column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="项目ID",
    )

    # 业务字段
    entry_type = Column(
        String(20),
        nullable=False,
        default=PrepaymentEntryType.TOPUP,
        comment="分录类型: TOPUP(入账)/REVERSAL(红冲)",
    )
    amount = Column(Numeric(15, 2), nullable=False, comment="金额（TOPUP为正数，REVERSAL为负数）")
    balance_after = Column(Numeric(15, 2), nullable=False, comment="交易后余额")
    entry_date = Column(Date, nullable=False, comment="入账日期")

    # 关联记录（红冲时使用）
    reference_id = Column(BigInteger, nullable=True, comment="关联记录ID（红冲时必填）")
    reference_type = Column(String(50), nullable=True, comment="关联记录类型")

    # 备注
    notes = Column(Text, nullable=True, comment="备注")

    # 操作人
    created_by = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="操作人ID",
    )

    # ========== 关系定义 ==========

    # 多对一：预付款 -> 项目
    project = relationship(
        "Project", foreign_keys=[project_id], lazy="joined", doc="所属项目"
    )

    # 多对一：预付款 -> 操作人
    operator = relationship("User", foreign_keys=[created_by], lazy="joined", doc="操作人")

    # 约束和索引
    __table_args__ = (
        CheckConstraint(
            "entry_type IN ('TOPUP', 'REVERSAL')",
            name="chk_project_prepayments_entry_type",
        ),
        CheckConstraint(
            "(entry_type = 'TOPUP' AND amount > 0) OR (entry_type = 'REVERSAL' AND amount < 0)",
            name="chk_project_prepayments_amount_direction",
        ),
        CheckConstraint(
            "(entry_type = 'REVERSAL' AND reference_id IS NOT NULL) OR entry_type = 'TOPUP'",
            name="chk_project_prepayments_reversal_ref",
        ),
        Index("idx_project_prepayments_project_id", "project_id"),
        Index("idx_project_prepayments_entry_date", "entry_date"),
        Index("idx_project_prepayments_entry_type", "entry_type"),
    )

    def __repr__(self):
        return f"<ProjectPrepayment(id={self.id}, project_id={self.project_id}, type='{self.entry_type}', amount={self.amount})>"

    # ========== 业务属性 ==========

    @property
    def is_topup(self) -> bool:
        """是否是入账记录"""
        return self.entry_type == PrepaymentEntryType.TOPUP

    @property
    def is_reversal(self) -> bool:
        """是否是红冲记录"""
        return self.entry_type == PrepaymentEntryType.REVERSAL

    # ========== 查询方法 ==========

    @classmethod
    def get_project_balance(cls, session, project_id: int) -> Decimal:
        """
        获取项目当前预付款余额

        Args:
            session: 数据库会话
            project_id: 项目ID

        Returns:
            Decimal: 当前余额（从最后一条记录获取）
        """
        last_entry = (
            session.query(cls)
            .filter(cls.project_id == project_id)
            .order_by(cls.id.desc())
            .first()
        )

        return last_entry.balance_after if last_entry else Decimal("0.00")

    @classmethod
    def get_project_entries(cls, session, project_id: int, limit: int = 100):
        """
        获取项目的预付款流水记录

        Args:
            session: 数据库会话
            project_id: 项目ID
            limit: 返回记录数限制

        Returns:
            List[ProjectPrepayment]: 预付款记录列表
        """
        return (
            session.query(cls)
            .filter(cls.project_id == project_id)
            .order_by(cls.id.desc())
            .limit(limit)
            .all()
        )
