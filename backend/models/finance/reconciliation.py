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
from backend.models.enums import ReconciliationBatchStatus, ReconciliationDetailStatus, ReconciliationAdjustmentType, UserRole
from backend.models.mixins.serializable import SerializableMixin


class ReconciliationBatch(Base, TimestampMixin, SerializableMixin):
    """
    对账批次表

    必须与 STATE_MACHINE.md v2.6 第4章（全局状态一览表）保持严格一致。

    5状态流程：
    draft → pending_review → approved/needs_adjustment → completed

    字段：
    - id: 主键
    - batch_code: 批次代码（唯一）
    - period_start: 对账期间开始日期
    - period_end: 对账期间结束日期
    - status: 状态（5状态机）
    - total_system_spend: 系统总消耗
    - total_actual_spend: 实际总消耗
    - discrepancy: 差异金额
    - created_by: 创建人ID（外键）
    - reviewed_by: 审核人ID（外键）
    - closed_at: 完成时间
    - created_at/updated_at: 时间戳（自动管理）
    """
    __tablename__ = 'reconciliation_batches'

    # 序列化配置
    __json_include_relationships__ = ['creator', 'reviewer', 'details']

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="批次ID")

    # 业务字段
    batch_no = Column(String(50), unique=True, nullable=False, comment="批次号")
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

    # 注意：adjustments 关系暂时注释，因为 ReconciliationAdjustment 可能尚未完全实现
    # 一对多：批次 -> 调整记录（如果 ReconciliationAdjustment 存在）
    # adjustments = relationship(
    #     "ReconciliationAdjustment",
    #     back_populates="batch",
    #     cascade="all, delete-orphan",
    #     lazy="dynamic",
    #     doc="调整记录"
    # )

    # 约束和索引 - 必须与 STATE_MACHINE.md v2.6 第4章保持一致
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'pending_review', 'approved', 'needs_adjustment', 'completed')",
            name='chk_reconciliation_batches_status'
        ),
        Index('idx_reconciliation_batches_status', 'status'),
        Index('idx_reconciliation_batches_period', 'period_start', 'period_end'),
        Index('idx_reconciliation_batches_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<ReconciliationBatch(id={self.id}, batch_no='{self.batch_no}', status='{self.status}')>"

    # ========== 业务属性（5状态机）==========

    # ========== SoT 字段别名（向后兼容）==========

    @property
    def batch_code(self):
        """向后兼容：返回 batch_no 的值"""
        return self.batch_no

    @batch_code.setter
    def batch_code(self, value):
        """向后兼容：设置 batch_no 的值"""
        self.batch_no = value

    @property
    def approved_by(self):
        """
        SoT 别名：返回 reviewed_by 的值

        DATA_SCHEMA.md 使用 approved_by，模型使用 reviewed_by
        """
        return self.reviewed_by

    @approved_by.setter
    def approved_by(self, value):
        """SoT 别名：设置 reviewed_by 的值"""
        self.reviewed_by = value

    @property
    def reconciliation_date(self):
        """
        计算属性：返回对账日期（使用 period_end）

        服务层使用单日期，模型使用日期范围
        """
        return self.period_end

    @reconciliation_date.setter
    def reconciliation_date(self, value):
        """设置对账日期（同时设置 period_start 和 period_end）"""
        self.period_start = value
        self.period_end = value

    # ========== 向后兼容别名 ==========

    @property
    def total_platform_spend(self):
        """
        向后兼容别名：返回 total_system_spend 的值

        注意：此属性为向后兼容保留，新代码应使用 total_system_spend
        """
        return self.total_system_spend

    @total_platform_spend.setter
    def total_platform_spend(self, value):
        """
        向后兼容别名：设置 total_system_spend 的值

        注意：此属性为向后兼容保留，新代码应使用 total_system_spend
        """
        self.total_system_spend = value

    @property
    def total_internal_spend(self):
        """
        向后兼容别名：返回 total_actual_spend 的值

        注意：此属性为向后兼容保留，新代码应使用 total_actual_spend
        """
        return self.total_actual_spend

    @total_internal_spend.setter
    def total_internal_spend(self, value):
        """
        向后兼容别名：设置 total_actual_spend 的值

        注意：此属性为向后兼容保留，新代码应使用 total_actual_spend
        """
        self.total_actual_spend = value

    @property
    def total_difference(self):
        """
        向后兼容别名：返回 discrepancy 的值

        注意：此属性为向后兼容保留，新代码应使用 discrepancy
        """
        return self.discrepancy

    @total_difference.setter
    def total_difference(self, value):
        """
        向后兼容别名：设置 discrepancy 的值

        注意：此属性为向后兼容保留，新代码应使用 discrepancy
        """
        self.discrepancy = value

    @property
    def status_enum(self) -> ReconciliationBatchStatus:
        """返回状态枚举对象"""
        return ReconciliationBatchStatus(self.status)

    @property
    def is_draft(self) -> bool:
        """是否是草稿"""
        return self.status == ReconciliationBatchStatus.DRAFT.value

    @property
    def is_pending_review(self) -> bool:
        """是否待审核"""
        return self.status == ReconciliationBatchStatus.PENDING_REVIEW.value

    @property
    def is_approved(self) -> bool:
        """是否已批准"""
        return self.status == ReconciliationBatchStatus.APPROVED.value

    @property
    def is_needs_adjustment(self) -> bool:
        """是否需要调整"""
        return self.status == ReconciliationBatchStatus.NEEDS_ADJUSTMENT.value

    @property
    def is_completed(self) -> bool:
        """是否已完成（终态）"""
        return self.status == ReconciliationBatchStatus.COMPLETED.value

    @property
    def discrepancy_rate(self) -> Decimal:
        """差异率"""
        if not self.total_system_spend or self.total_system_spend == 0:
            return Decimal('0.0000')
        return abs(Decimal(self.discrepancy or Decimal('0.00'))) / Decimal(self.total_system_spend) * Decimal('100')

    # ========== 状态流转方法（5状态机）==========

    # 合法流转白名单 - 必须与 STATE_MACHINE.md v2.6 保持一致
    STATE_TRANSITIONS = {
        ReconciliationBatchStatus.DRAFT: [ReconciliationBatchStatus.PENDING_REVIEW],
        ReconciliationBatchStatus.PENDING_REVIEW: [ReconciliationBatchStatus.APPROVED, ReconciliationBatchStatus.NEEDS_ADJUSTMENT],
        ReconciliationBatchStatus.APPROVED: [ReconciliationBatchStatus.COMPLETED],
        ReconciliationBatchStatus.NEEDS_ADJUSTMENT: [ReconciliationBatchStatus.PENDING_REVIEW],
        ReconciliationBatchStatus.COMPLETED: [],  # 终态
    }

    def can_transition_to(self, new_status: ReconciliationBatchStatus) -> bool:
        """检查是否可以转换到新状态"""
        current = ReconciliationBatchStatus(self.status)
        return new_status in self.STATE_TRANSITIONS.get(current, [])

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

    def submit_for_review(self):
        """提交审核"""
        if not self.can_transition_to(ReconciliationBatchStatus.PENDING_REVIEW):
            raise ValueError(f"不允许从 {self.status} 状态提交审核")
        self.status = ReconciliationBatchStatus.PENDING_REVIEW.value

    def approve(self, reviewer_id: UUID):
        """批准"""
        if not self.can_transition_to(ReconciliationBatchStatus.APPROVED):
            raise ValueError(f"不允许从 {self.status} 状态批准")
        self.status = ReconciliationBatchStatus.APPROVED.value
        self.reviewed_by = reviewer_id

    def mark_needs_adjustment(self, reviewer_id: UUID, reason: str):
        """标记需要调整"""
        if not self.can_transition_to(ReconciliationBatchStatus.NEEDS_ADJUSTMENT):
            raise ValueError(f"不允许从 {self.status} 状态标记需要调整")
        self.status = ReconciliationBatchStatus.NEEDS_ADJUSTMENT.value
        self.reviewed_by = reviewer_id

    def complete(self, reviewer_id: UUID):
        """完成对账批次（终态）"""
        if not self.can_transition_to(ReconciliationBatchStatus.COMPLETED):
            raise ValueError(f"不允许从 {self.status} 状态完成")
        self.status = ReconciliationBatchStatus.COMPLETED.value
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

    # 注意：adjustments 关系暂时注释，因为 ReconciliationAdjustment 可能尚未完全实现
    # 一对多：明细 -> 调整记录（如果 ReconciliationAdjustment 存在）
    # adjustments = relationship(
    #     "ReconciliationAdjustment",
    #     back_populates="detail",
    #     cascade="all, delete-orphan",
    #     lazy="dynamic",
    #     doc="调整记录"
    # )

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


class ReconciliationAdjustment(Base, TimestampMixin, SerializableMixin):
    """
    对账调整记录表

    必须与 DATA_SCHEMA.md v5.2 第3.5.3节保持严格一致。

    字段：
    - id: 主键
    - detail_id: 明细ID（外键）
    - adjustment_type: 调整类型（increase/decrease/writeoff）
    - amount: 调整金额
    - reason: 调整原因
    - created_by: 创建人ID（外键）
    - created_at/updated_at: 时间戳（自动管理）
    """
    __tablename__ = 'reconciliation_adjustments'

    # 序列化配置
    __json_include_relationships__ = ['detail', 'creator']

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="调整ID")

    # 外键
    detail_id = Column(
        BigInteger,
        ForeignKey('reconciliation_details.id', ondelete='CASCADE'),
        nullable=False,
        comment="明细ID"
    )
    created_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="创建人ID"
    )

    # 业务字段（SoT DATA_SCHEMA.md v5.2）
    adjustment_type = Column(String(20), nullable=False, comment="调整类型")
    amount = Column(Numeric(15, 2), nullable=False, comment="调整金额")
    reason = Column(Text, nullable=True, comment="调整原因")

    # 并发控制
    version = Column(Integer, nullable=False, server_default='1', comment="乐观锁版本号")

    # ========== 关系定义 ==========

    # 多对一：调整 -> 明细
    detail = relationship(
        "ReconciliationDetail",
        foreign_keys=[detail_id],
        lazy="joined",
        doc="所属对账明细"
    )

    # 多对一：调整 -> 创建人
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        lazy="selectin",
        doc="创建人"
    )

    # 约束和索引
    __table_args__ = (
        CheckConstraint(
            "adjustment_type IN ('increase', 'decrease', 'writeoff')",
            name='chk_reconciliation_adjustments_type'
        ),
        Index('idx_reconciliation_adjustments_detail_id', 'detail_id'),
        Index('idx_reconciliation_adjustments_created_by', 'created_by'),
    )

    def __repr__(self):
        return f"<ReconciliationAdjustment(id={self.id}, detail_id={self.detail_id}, type='{self.adjustment_type}')>"

    # ========== 业务属性 ==========

    @property
    def type_enum(self) -> ReconciliationAdjustmentType:
        """返回调整类型枚举对象"""
        return ReconciliationAdjustmentType(self.adjustment_type)


class ReconciliationReport(Base, TimestampMixin, SerializableMixin):
    """
    对账报告表

    必须与 DATA_SCHEMA.md v5.2 第3.5.4节保持严格一致。

    字段：
    - id: 主键
    - batch_id: 批次ID（外键）
    - report_type: 报告类型（daily/weekly/monthly）
    - period_start: 报告期间开始
    - period_end: 报告期间结束
    - metrics: 报告指标（JSONB）
    - report_url: 报告文件URL
    - generated_by: 生成人ID（外键）
    - generated_at: 生成时间
    - created_at/updated_at: 时间戳（自动管理）
    """
    __tablename__ = 'reconciliation_reports'

    # 序列化配置
    __json_include_relationships__ = ['batch', 'generator']

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="报告ID")

    # 外键
    batch_id = Column(
        BigInteger,
        ForeignKey('reconciliation_batches.id', ondelete='CASCADE'),
        nullable=False,
        comment="批次ID"
    )
    generated_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="生成人ID"
    )

    # 业务字段
    report_type = Column(String(20), nullable=False, comment="报告类型")
    period_start = Column(Date, nullable=False, comment="报告期间开始")
    period_end = Column(Date, nullable=False, comment="报告期间结束")
    metrics = Column(Text, nullable=True, comment="报告指标(JSON)")
    report_url = Column(String(500), nullable=True, comment="报告文件URL")
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), comment="生成时间")

    # ========== 关系定义 ==========

    # 多对一：报告 -> 批次
    batch = relationship(
        "ReconciliationBatch",
        foreign_keys=[batch_id],
        lazy="joined",
        doc="所属批次"
    )

    # 多对一：报告 -> 生成人
    generator = relationship(
        "User",
        foreign_keys=[generated_by],
        lazy="selectin",
        doc="生成人"
    )

    # 约束和索引
    __table_args__ = (
        CheckConstraint(
            "report_type IN ('daily', 'weekly', 'monthly')",
            name='chk_reconciliation_reports_type'
        ),
        Index('idx_reconciliation_reports_batch_id', 'batch_id'),
        Index('idx_reconciliation_reports_generated_by', 'generated_by'),
        Index('idx_reconciliation_reports_period', 'period_start', 'period_end'),
    )

    def __repr__(self):
        return f"<ReconciliationReport(id={self.id}, batch_id={self.batch_id}, type='{self.report_type}')>"

    # ========== 业务属性 ==========

    @property
    def metrics_dict(self) -> dict:
        """返回指标字典"""
        import json
        if self.metrics:
            try:
                return json.loads(self.metrics)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    @metrics_dict.setter
    def metrics_dict(self, value: dict):
        """设置指标字典"""
        import json
        self.metrics = json.dumps(value, ensure_ascii=False) if value else None
