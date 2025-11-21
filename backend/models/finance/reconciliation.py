"""
对账模型 - 对账批次和明细
"""
from decimal import Decimal
from uuid import UUID
from datetime import date, datetime
from sqlalchemy import Column, BigInteger, String, Text, Integer, Numeric, Date, DateTime, Index, CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base, TimestampMixin
from backend.models.enums import ReconciliationBatchStatus, ReconciliationDetailStatus, UserRole
from backend.models.mixins.serializable import SerializableMixin


class ReconciliationBatch(Base, TimestampMixin, SerializableMixin):
    """
    对账批次表

    字段：
    - id: 主键
    - batch_code: 批次代码（唯一）
    - period_start: 对账期间开始日期
    - period_end: 对账期间结束日期
    - status: 状态（draft/pending/reviewing/closed）
    - total_system_spend: 系统总消耗
    - total_actual_spend: 实际总消耗
    - discrepancy: 差异金额
    - created_by: 创建人ID（外键）
    - reviewed_by: 审核人ID（外键）
    - closed_at: 关闭时间
    - created_at/updated_at: 时间戳（自动管理）
    """
    __tablename__ = 'reconciliation_batches'

    # 序列化配置
    __json_include_relationships__ = ['creator', 'reviewer', 'details']

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="批次ID")

    # 业务字段
    batch_code = Column(String(50), unique=True, nullable=False, comment="批次代码")
    period_start = Column(Date, nullable=False, comment="对账期间开始")
    period_end = Column(Date, nullable=False, comment="对账期间结束")
    status = Column(String(20), nullable=False, comment="状态")
    total_system_spend = Column(Numeric(15, 2), nullable=True, comment="系统总消耗")
    total_actual_spend = Column(Numeric(15, 2), nullable=True, comment="实际总消耗")
    discrepancy = Column(Numeric(15, 2), nullable=True, comment="差异金额")

    # 外键
    created_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="创建人ID"
    )
    reviewed_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="审核人ID"
    )

    # 时间字段
    closed_at = Column(DateTime(timezone=True), nullable=True, comment="关闭时间")

    # 并发控制
    version = Column(Integer, nullable=False, server_default='1', comment="乐观锁版本号")

    # ========== 关系定义 ==========

    # 多对一：批次 -> 创建人
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        lazy="selectin",
        doc="创建人"
    )

    # 多对一：批次 -> 审核人
    reviewer = relationship(
        "User",
        foreign_keys=[reviewed_by],
        lazy="selectin",
        doc="审核人"
    )

    # 一对多：批次 -> 明细
    details = relationship(
        "ReconciliationDetail",
        back_populates="batch",
        cascade="all, delete-orphan",
        lazy="dynamic",
        doc="对账明细"
    )

    # 约束和索引
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'pending', 'reviewing', 'closed')",
            name='chk_reconciliation_batches_status'
        ),
        Index('idx_reconciliation_batches_status', 'status'),
        Index('idx_reconciliation_batches_period', 'period_start', 'period_end'),
        Index('idx_reconciliation_batches_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<ReconciliationBatch(id={self.id}, code='{self.batch_code}', status='{self.status}')>"

    # ========== 业务属性 ==========

    @property
    def status_enum(self) -> ReconciliationBatchStatus:
        """返回状态枚举对象"""
        return ReconciliationBatchStatus(self.status)

    @property
    def is_closed(self) -> bool:
        """是否已关闭"""
        return self.status == ReconciliationBatchStatus.CLOSED.value

    @property
    def discrepancy_rate(self) -> Decimal:
        """差异率"""
        if not self.total_system_spend or self.total_system_spend == 0:
            return Decimal('0.0000')
        return abs(Decimal(self.discrepancy or Decimal('0.00'))) / Decimal(self.total_system_spend) * Decimal('100')

    # ========== 业务方法 ==========

    def calculate_totals(self, session):
        """计算批次总金额和差异"""
        from sqlalchemy import func as sql_func
        result = session.query(
            sql_func.sum(ReconciliationDetail.system_spend).label('total_system'),
            sql_func.sum(ReconciliationDetail.actual_spend).label('total_actual')
        ).filter(
            ReconciliationDetail.batch_id == self.id
        ).first()

        self.total_system_spend = result.total_system or Decimal('0.00')
        self.total_actual_spend = result.total_actual or Decimal('0.00')
        self.discrepancy = self.total_actual_spend - self.total_system_spend

    def close(self, reviewer_id: UUID):
        """关闭对账批次"""
        self.status = ReconciliationBatchStatus.CLOSED.value
        self.reviewed_by = reviewer_id
        self.closed_at = func.now()


class ReconciliationDetail(Base, TimestampMixin, SerializableMixin):
    """
    对账明细表

    字段：
    - id: 主键
    - batch_id: 批次ID（外键）
    - ad_account_id: 广告账户ID（外键）
    - system_spend: 系统消耗
    - actual_spend: 实际消耗
    - discrepancy: 差异金额
    - status: 状态（pending/confirmed/adjusted）
    - notes: 备注
    - created_at/updated_at: 时间戳（自动管理）
    """
    __tablename__ = 'reconciliation_details'

    # 序列化配置
    __json_include_relationships__ = ['batch', 'ad_account']

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="明细ID")

    # 外键
    batch_id = Column(
        BigInteger,
        ForeignKey('reconciliation_batches.id', ondelete='CASCADE'),
        nullable=False,
        comment="批次ID"
    )
    ad_account_id = Column(
        BigInteger,
        ForeignKey('ad_accounts.id', ondelete='CASCADE'),
        nullable=False,
        comment="广告账户ID"
    )

    # 业务字段
    system_spend = Column(Numeric(15, 2), nullable=False, comment="系统消耗")
    actual_spend = Column(Numeric(15, 2), nullable=False, comment="实际消耗")
    discrepancy = Column(Numeric(15, 2), nullable=False, comment="差异金额")
    status = Column(String(20), nullable=False, comment="状态")
    notes = Column(Text, nullable=True, comment="备注")

    # 并发控制
    version = Column(Integer, nullable=False, server_default='1', comment="乐观锁版本号")

    # ========== 关系定义 ==========

    # 多对一：明细 -> 批次
    batch = relationship(
        "ReconciliationBatch",
        back_populates="details",
        lazy="joined",
        doc="所属批次"
    )

    # 多对一：明细 -> 广告账户
    ad_account = relationship(
        "AdAccount",
        foreign_keys=[ad_account_id],
        lazy="joined",
        doc="所属广告账户"
    )

    # 约束和索引
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'adjusted')",
            name='chk_reconciliation_details_status'
        ),
        Index('idx_reconciliation_details_batch_id', 'batch_id'),
        Index('idx_reconciliation_details_ad_account_id', 'ad_account_id'),
    )

    def __repr__(self):
        return f"<ReconciliationDetail(id={self.id}, batch_id={self.batch_id}, account_id={self.ad_account_id})>"

    # ========== 业务属性 ==========

    @property
    def status_enum(self) -> ReconciliationDetailStatus:
        """返回状态枚举对象"""
        return ReconciliationDetailStatus(self.status)

    @property
    def discrepancy_rate(self) -> Decimal:
        """差异率"""
        if not self.system_spend or self.system_spend == 0:
            return Decimal('0.0000')
        return abs(Decimal(self.discrepancy)) / Decimal(self.system_spend) * Decimal('100')

    @property
    def has_discrepancy(self) -> bool:
        """是否存在差异"""
        return abs(self.discrepancy) > Decimal('0.01')  # 容忍1分钱的舍入误差

    # ========== 业务方法 ==========

    def confirm(self):
        """确认对账"""
        self.status = ReconciliationDetailStatus.CONFIRMED.value

    def adjust(self, notes: str):
        """标记为需要调整"""
        self.status = ReconciliationDetailStatus.ADJUSTED.value
        self.notes = notes
