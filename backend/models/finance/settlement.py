"""
结算模型 - 财务结算实体
Version: 1.0
Author: Claude Code (full_pipeline)

Aligned with SoT:
- DATA_SCHEMA.md v5.2 (settlement entity)
- BUSINESS_RULES.md v3.1 (settlement constraints)
- LEDGER_SOT.md v1.1 (settlement ledger entries)
- STATE_MACHINE.md v2.6 (settlement status transitions)

RLS 策略：admin/finance 可访问所有结算记录
"""

from decimal import Decimal
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, Numeric, Index, CheckConstraint, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base, TimestampMixin, UserScopeMixin
from backend.models.mixins.serializable import SerializableMixin


class SettlementStatus:
    """结算状态常量"""
    DRAFT = "draft"              # 草稿
    PENDING = "pending"          # 待审核
    APPROVED = "approved"        # 已审核
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 已完成（终态）
    CANCELLED = "cancelled"      # 已取消（终态）
    REJECTED = "rejected"        # 已拒绝


class SettlementType:
    """结算类型常量"""
    SUPPLIER_PAYMENT = "supplier_payment"    # 供应商结算
    CLIENT_BILLING = "client_billing"        # 客户账单
    INTERNAL_TRANSFER = "internal_transfer"  # 内部转账
    REFUND = "refund"                        # 退款


class PaymentStatus:
    """支付状态常量"""
    UNPAID = "unpaid"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"


class Settlement(Base, TimestampMixin, UserScopeMixin, SerializableMixin):
    """
    结算表 - 财务结算管理

    字段：
    - id: 主键
    - settlement_no: 结算单号（唯一）
    - settlement_type: 结算类型
    - supplier_id: 供应商ID（供应商结算时使用）
    - client_id: 客户ID（客户账单时使用，实际为 project_id）
    - period_start/period_end: 结算周期
    - currency: 结算货币
    - amount: 结算金额
    - exchange_rate: 汇率
    - amount_in_base_currency: 基础货币金额
    - due_date: 到期日期
    - status: 结算状态
    - payment_status: 支付状态
    - paid_amount: 已支付金额
    - paid_at: 支付时间
    - description: 结算说明
    - reference_ids: 关联的日报ID列表
    - extra_metadata: 元数据，DB 列名为 "metadata"
    - created_by: 创建者
    - approved_by: 审批人
    - approved_at: 审批时间
    - created_at/updated_at: 时间戳
    """
    __tablename__ = 'settlements'

    # 序列化配置
    __json_include_relationships__ = ['creator', 'approver', 'supplier']

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="结算ID")

    # 结算单号
    settlement_no = Column(String(50), unique=True, nullable=False, comment="结算单号")

    # 结算类型
    settlement_type = Column(String(50), nullable=False, comment="结算类型")

    # 关联外键
    supplier_id = Column(BigInteger, ForeignKey('suppliers.id', ondelete='SET NULL'), nullable=True, comment="供应商ID")
    # client_id 实际映射到 project_id，用于客户账单
    client_id = Column(BigInteger, ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, comment="客户/项目ID")

    # 结算周期
    period_start = Column(Date, nullable=False, comment="结算周期开始日期")
    period_end = Column(Date, nullable=False, comment="结算周期结束日期")

    # 金额信息
    currency = Column(String(3), nullable=False, default="USD", comment="结算货币")
    amount = Column(Numeric(15, 2), nullable=False, comment="结算金额")
    exchange_rate = Column(Numeric(10, 6), nullable=False, default=Decimal('1.0'), comment="汇率")
    amount_in_base_currency = Column(Numeric(15, 2), nullable=False, default=Decimal('0.00'), comment="基础货币金额")

    # 到期与支付
    due_date = Column(Date, nullable=True, comment="到期日期")
    status = Column(String(20), nullable=False, default=SettlementStatus.DRAFT, comment="结算状态")
    payment_status = Column(String(20), nullable=False, default=PaymentStatus.UNPAID, comment="支付状态")
    paid_amount = Column(Numeric(15, 2), nullable=False, default=Decimal('0.00'), comment="已支付金额")
    paid_at = Column(DateTime(timezone=True), nullable=True, comment="支付时间")

    # 描述与备注
    description = Column(Text, nullable=True, comment="结算说明")

    # 关联日报ID列表（PostgreSQL ARRAY 类型，SQLite 用 JSON 兼容）
    reference_ids = Column(JSONB, nullable=True, comment="关联的日报ID列表")

    # 元数据
    # NOTE: 属性名从 metadata 改为 extra_metadata，避免与 SQLAlchemy Declarative Base.metadata 冲突
    # 数据库列名仍为 "metadata"，与 SoT DATA_SCHEMA.md v5.2 保持一致
    extra_metadata = Column("metadata", JSONB, nullable=True, comment="元数据")

    # 审批信息
    approved_by = Column(PGUUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment="审批人ID")
    approved_at = Column(DateTime(timezone=True), nullable=True, comment="审批时间")

    # 取消/拒绝原因
    cancel_reason = Column(Text, nullable=True, comment="取消/拒绝原因")

    # ========== 关系定义 ==========

    # 多对一：结算 -> 创建者
    creator = relationship(
        "User",
        foreign_keys="Settlement.created_by",
        lazy="selectin",
        doc="创建者"
    )

    # 多对一：结算 -> 审批人
    approver = relationship(
        "User",
        foreign_keys="Settlement.approved_by",
        lazy="selectin",
        doc="审批人"
    )

    # 多对一：结算 -> 供应商
    supplier = relationship(
        "Supplier",
        foreign_keys="Settlement.supplier_id",
        lazy="selectin",
        doc="关联供应商"
    )

    # 多对一：结算 -> 项目（客户）
    project = relationship(
        "Project",
        foreign_keys="Settlement.client_id",
        lazy="selectin",
        doc="关联项目/客户"
    )

    # TODO: 与 ledger_entries 的聚合关系
    # 结算完成后会生成对应的 ledger entries，可通过 settlement_id 或 reference 字段关联

    # TODO: 与 daily_reports 的聚合关系
    # reference_ids 字段存储关联的日报ID列表，实际查询时需要 join daily_reports 表

    # 约束与索引
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'pending', 'approved', 'processing', 'completed', 'cancelled', 'rejected')",
            name='chk_settlements_status'
        ),
        CheckConstraint(
            "settlement_type IN ('supplier_payment', 'client_billing', 'internal_transfer', 'refund')",
            name='chk_settlements_type'
        ),
        CheckConstraint(
            "payment_status IN ('unpaid', 'partial', 'paid', 'overdue')",
            name='chk_settlements_payment_status'
        ),
        CheckConstraint(
            "period_end >= period_start",
            name='chk_settlements_period_valid'
        ),
        CheckConstraint(
            "amount >= 0",
            name='chk_settlements_amount_positive'
        ),
        CheckConstraint(
            "paid_amount >= 0",
            name='chk_settlements_paid_amount_positive'
        ),
        Index('idx_settlements_settlement_no', 'settlement_no'),
        Index('idx_settlements_type', 'settlement_type'),
        Index('idx_settlements_status', 'status'),
        Index('idx_settlements_payment_status', 'payment_status'),
        Index('idx_settlements_supplier_id', 'supplier_id'),
        Index('idx_settlements_client_id', 'client_id'),
        Index('idx_settlements_due_date', 'due_date'),
        Index('idx_settlements_created_by', 'created_by'),
        Index('idx_settlements_period', 'period_start', 'period_end'),
    )

    def __repr__(self):
        return f"<Settlement(id={self.id}, no='{self.settlement_no}', status='{self.status}')>"

    # ========== 状态流转规则 ==========

    ALLOWED_TRANSITIONS = {
        SettlementStatus.DRAFT: [SettlementStatus.PENDING, SettlementStatus.CANCELLED],
        SettlementStatus.PENDING: [SettlementStatus.APPROVED, SettlementStatus.REJECTED],
        SettlementStatus.APPROVED: [SettlementStatus.PROCESSING, SettlementStatus.CANCELLED],
        SettlementStatus.PROCESSING: [SettlementStatus.COMPLETED],
        SettlementStatus.COMPLETED: [],  # 终态
        SettlementStatus.CANCELLED: [],  # 终态
        SettlementStatus.REJECTED: [SettlementStatus.DRAFT],  # 可重新编辑
    }

    # ========== 业务属性 ==========

    @property
    def is_terminal(self) -> bool:
        """是否是终态"""
        return self.status in [SettlementStatus.COMPLETED, SettlementStatus.CANCELLED]

    @property
    def is_editable(self) -> bool:
        """是否可编辑"""
        return self.status in [SettlementStatus.DRAFT, SettlementStatus.REJECTED]

    @property
    def is_overdue(self) -> bool:
        """是否逾期"""
        if not self.due_date:
            return False
        from datetime import date
        return self.payment_status != PaymentStatus.PAID and self.due_date < date.today()

    @property
    def remaining_amount(self) -> Decimal:
        """剩余应付金额"""
        return self.amount - self.paid_amount

    # ========== 业务方法 ==========

    def can_transition_to(self, new_status: str) -> bool:
        """检查是否可以转换到新状态"""
        allowed = self.ALLOWED_TRANSITIONS.get(self.status, [])
        return new_status in allowed

    def transition_to(self, new_status: str, operator_id=None, reason: str = None) -> bool:
        """
        安全地转换结算状态

        Args:
            new_status: 目标状态
            operator_id: 操作者ID
            reason: 状态变更原因（用于拒绝/取消）

        Returns:
            bool: 是否转换成功

        Raises:
            ValueError: 不允许的状态转换
        """
        if not self.can_transition_to(new_status):
            raise ValueError(f"不允许从 {self.status} 转换到 {new_status}")

        old_status = self.status
        self.status = new_status

        # 处理审批相关
        if new_status == SettlementStatus.APPROVED:
            self.approved_by = operator_id
            self.approved_at = datetime.utcnow()

        # 处理拒绝/取消原因
        if new_status in [SettlementStatus.REJECTED, SettlementStatus.CANCELLED] and reason:
            self.cancel_reason = reason

        return True

    def record_payment(self, amount: Decimal, paid_at: datetime = None) -> bool:
        """
        记录支付

        Args:
            amount: 支付金额
            paid_at: 支付时间

        Returns:
            bool: 是否记录成功

        Raises:
            ValueError: 金额超过剩余应付
        """
        if amount > self.remaining_amount:
            raise ValueError(f"支付金额 {amount} 超过剩余应付 {self.remaining_amount}")

        self.paid_amount += amount
        self.paid_at = paid_at or datetime.utcnow()

        # 更新支付状态
        if self.paid_amount >= self.amount:
            self.payment_status = PaymentStatus.PAID
        elif self.paid_amount > 0:
            self.payment_status = PaymentStatus.PARTIAL

        return True

    def update_overdue_status(self):
        """更新逾期状态（可由定时任务调用）"""
        if self.is_overdue and self.payment_status not in [PaymentStatus.PAID, PaymentStatus.OVERDUE]:
            self.payment_status = PaymentStatus.OVERDUE
