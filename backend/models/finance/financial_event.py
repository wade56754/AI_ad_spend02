"""
财务事件模型 - 统一的财务事件记录
Version: 1.0
Author: Claude Code

Aligned with SoT:
- FINANCIAL_SOT_DESIGN.md v1.0 (financial events)
- DATA_SCHEMA.md v5.3 (financial_events table)

财务事件是所有财务变动的原始记录，经过状态流转后生成账本分录
"""

from decimal import Decimal
from datetime import date, datetime
from typing import Optional, Dict, Any
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Text, Date, Numeric, BigInteger, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text, func

from backend.models.base import Base, TimestampMixin
from backend.models.mixins.serializable import SerializableMixin


class EventType(str, PyEnum):
    """财务事件类型枚举"""
    TOPUP = "TOPUP"           # 充值
    SPEND = "SPEND"           # 消耗
    PAYMENT = "PAYMENT"       # 回款
    TRANSFER = "TRANSFER"     # 转移
    ADJUSTMENT = "ADJUSTMENT" # 调整
    FEE = "FEE"               # 手续费
    REFUND = "REFUND"         # 退款


class EventStatus(str, PyEnum):
    """财务事件状态枚举"""
    RAW = "raw"               # 原始数据导入
    PENDING = "pending"       # 等待确认
    CONFIRMED = "confirmed"   # 已确认，可入账
    POSTED = "posted"         # 已入账
    REVERSED = "reversed"     # 已冲正


class SourceType(str, PyEnum):
    """事件来源类型"""
    EXCEL_IMPORT = "excel_import"  # Excel 导入
    API = "api"                     # API 创建
    MANUAL = "manual"               # 手工录入
    SYSTEM = "system"               # 系统自动


class FinancialEvent(Base, TimestampMixin, SerializableMixin):
    """
    财务事件表 - 统一的财务事件记录

    字段：
    - id: 主键 (UUID)
    - event_type: 事件类型 (TOPUP/SPEND/PAYMENT/TRANSFER/ADJUSTMENT/FEE/REFUND)
    - event_status: 事件状态 (raw/pending/confirmed/posted/reversed)
    - source_type: 来源类型
    - source_ref: 来源引用
    - idempotency_key: 幂等键 (唯一)
    - amount: 金额
    - fee_amount: 手续费
    - gross_amount: 含费金额
    - currency: 币种
    - event_date: 事件日期
    - team_id/buyer_id/supplier_id/ad_account_id/project_id: 关联实体
    - payload: 扩展数据 (JSONB)
    - created_by/confirmed_by: 审计用户
    - confirmed_at/posted_at: 审计时间

    状态机：
    RAW → PENDING → CONFIRMED → POSTED → REVERSED

    业务规则：
    - 每个事件有唯一的 idempotency_key 防止重复
    - 只有 CONFIRMED 状态的事件才能入账
    - POSTED 状态的事件可以冲正，生成反向分录
    """
    __tablename__ = 'financial_events'

    # 序列化配置
    __json_include_relationships__ = ['team', 'buyer', 'supplier', 'ad_account', 'project']

    # 主键
    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text('gen_random_uuid()'),
        comment="事件ID"
    )

    # 事件类型和状态
    event_type = Column(String(20), nullable=False, comment="事件类型")
    event_status = Column(String(20), nullable=False, default=EventStatus.RAW.value, comment="事件状态")

    # 来源追溯
    source_type = Column(String(50), nullable=True, comment="来源类型")
    source_ref = Column(String(255), nullable=True, comment="来源引用")
    idempotency_key = Column(String(255), unique=True, nullable=False, comment="幂等键")

    # 金额字段
    amount = Column(Numeric(18, 4), nullable=False, comment="金额")
    fee_amount = Column(Numeric(18, 4), nullable=False, default=Decimal('0'), comment="手续费")
    gross_amount = Column(Numeric(18, 4), nullable=True, comment="含费金额")
    currency = Column(String(3), nullable=False, default='USD', comment="币种")
    event_date = Column(Date, nullable=False, comment="事件日期")

    # 关联实体
    team_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('teams.id', ondelete='SET NULL'),
        nullable=True,
        comment="团队ID"
    )
    buyer_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('buyers.id', ondelete='SET NULL'),
        nullable=True,
        comment="投手ID"
    )
    supplier_id = Column(
        BigInteger,
        ForeignKey('suppliers.id', ondelete='SET NULL'),
        nullable=True,
        comment="供应商ID"
    )
    ad_account_id = Column(
        BigInteger,
        ForeignKey('ad_accounts.id', ondelete='SET NULL'),
        nullable=True,
        comment="广告账户ID"
    )
    project_id = Column(
        BigInteger,
        ForeignKey('projects.id', ondelete='SET NULL'),
        nullable=True,
        comment="项目ID"
    )

    # 扩展数据
    payload = Column(JSONB, nullable=False, default=dict, comment="扩展数据")

    # 审计字段
    created_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="创建者"
    )
    confirmed_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="确认者"
    )
    confirmed_at = Column(
        'confirmed_at',
        type_=func.now().type,
        nullable=True,
        comment="确认时间"
    )
    posted_at = Column(
        'posted_at',
        type_=func.now().type,
        nullable=True,
        comment="入账时间"
    )

    # ========== 关系定义 ==========

    # 多对一：事件 -> 团队
    team = relationship(
        "Team",
        back_populates="financial_events",
        lazy="joined",
        doc="所属团队"
    )

    # 多对一：事件 -> 投手
    buyer = relationship(
        "Buyer",
        back_populates="financial_events",
        lazy="joined",
        doc="所属投手"
    )

    # 多对一：事件 -> 供应商
    supplier = relationship(
        "Supplier",
        foreign_keys=[supplier_id],
        lazy="joined",
        doc="关联供应商"
    )

    # 多对一：事件 -> 广告账户
    ad_account = relationship(
        "AdAccount",
        foreign_keys=[ad_account_id],
        lazy="joined",
        doc="关联账户"
    )

    # 多对一：事件 -> 项目
    project = relationship(
        "Project",
        foreign_keys=[project_id],
        lazy="joined",
        doc="关联项目"
    )

    # 多对一：事件 -> 创建者
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        lazy="selectin",
        doc="创建者"
    )

    # 多对一：事件 -> 确认者
    confirmer = relationship(
        "User",
        foreign_keys=[confirmed_by],
        lazy="selectin",
        doc="确认者"
    )

    # 一对多：事件 -> 账本分录
    ledger_entries = relationship(
        "LedgerEntry",
        foreign_keys="LedgerEntry.event_id",
        lazy="dynamic",
        doc="关联分录"
    )

    # 约束与索引
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('TOPUP', 'SPEND', 'PAYMENT', 'TRANSFER', 'ADJUSTMENT', 'FEE', 'REFUND')",
            name='chk_financial_events_event_type'
        ),
        CheckConstraint(
            "event_status IN ('raw', 'pending', 'confirmed', 'posted', 'reversed')",
            name='chk_financial_events_event_status'
        ),
        Index('idx_fin_events_type_status', 'event_type', 'event_status'),
        Index('idx_fin_events_event_date', 'event_date'),
        Index('idx_fin_events_supplier_id', 'supplier_id'),
        Index('idx_fin_events_ad_account_id', 'ad_account_id'),
        Index('idx_fin_events_project_id', 'project_id'),
        Index('idx_fin_events_team_id', 'team_id'),
        Index('idx_fin_events_buyer_id', 'buyer_id'),
        Index('idx_fin_events_idempotency_key', 'idempotency_key'),
        Index('idx_fin_events_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<FinancialEvent(id={self.id}, type='{self.event_type}', status='{self.event_status}', amount={self.amount})>"

    # ========== 业务属性 ==========

    @property
    def event_type_enum(self) -> EventType:
        """返回事件类型枚举"""
        return EventType(self.event_type)

    @property
    def event_status_enum(self) -> EventStatus:
        """返回事件状态枚举"""
        return EventStatus(self.event_status)

    @property
    def is_posted(self) -> bool:
        """是否已入账"""
        return self.event_status == EventStatus.POSTED.value

    @property
    def can_post(self) -> bool:
        """是否可以入账"""
        return self.event_status == EventStatus.CONFIRMED.value

    @property
    def can_reverse(self) -> bool:
        """是否可以冲正"""
        return self.event_status == EventStatus.POSTED.value

    # ========== 状态机方法 ==========

    # 状态转换规则
    TRANSITIONS = {
        EventStatus.RAW.value: [EventStatus.PENDING.value],
        EventStatus.PENDING.value: [EventStatus.CONFIRMED.value, EventStatus.RAW.value],
        EventStatus.CONFIRMED.value: [EventStatus.POSTED.value],
        EventStatus.POSTED.value: [EventStatus.REVERSED.value],
        EventStatus.REVERSED.value: [],  # 终态
    }

    def can_transition_to(self, target_status: str) -> bool:
        """检查是否可以转换到目标状态"""
        return target_status in self.TRANSITIONS.get(self.event_status, [])

    def transition_to(self, target_status: str, user_id=None) -> bool:
        """
        转换状态

        Args:
            target_status: 目标状态
            user_id: 操作用户ID

        Returns:
            bool: 转换是否成功

        Raises:
            ValueError: 不允许的状态转换
        """
        if not self.can_transition_to(target_status):
            raise ValueError(
                f"不允许从 {self.event_status} 转换到 {target_status}"
            )

        self.event_status = target_status

        if target_status == EventStatus.CONFIRMED.value:
            self.confirmed_by = user_id
            self.confirmed_at = datetime.utcnow()
        elif target_status == EventStatus.POSTED.value:
            self.posted_at = datetime.utcnow()

        return True

    # ========== 业务方法 ==========

    def calculate_gross_amount(self) -> Decimal:
        """计算含费金额"""
        return self.amount + (self.fee_amount or Decimal('0'))

    def set_payload_field(self, key: str, value: Any):
        """设置扩展字段"""
        if self.payload is None:
            self.payload = {}
        self.payload[key] = value

    def get_payload_field(self, key: str, default=None):
        """获取扩展字段"""
        if self.payload is None:
            return default
        return self.payload.get(key, default)

    # ========== 类方法 ==========

    @classmethod
    def get_by_idempotency_key(cls, session, key: str):
        """根据幂等键获取事件"""
        return session.query(cls).filter(cls.idempotency_key == key).first()

    @classmethod
    def get_pending_events(cls, session, event_type: str = None):
        """获取待确认的事件"""
        query = session.query(cls).filter(cls.event_status == EventStatus.PENDING.value)
        if event_type:
            query = query.filter(cls.event_type == event_type)
        return query.all()

    @classmethod
    def get_confirmed_events(cls, session, event_type: str = None):
        """获取已确认待入账的事件"""
        query = session.query(cls).filter(cls.event_status == EventStatus.CONFIRMED.value)
        if event_type:
            query = query.filter(cls.event_type == event_type)
        return query.all()

    @classmethod
    def get_events_by_date_range(cls, session, start_date: date, end_date: date, event_type: str = None):
        """获取日期范围内的事件"""
        query = session.query(cls).filter(
            cls.event_date >= start_date,
            cls.event_date <= end_date
        )
        if event_type:
            query = query.filter(cls.event_type == event_type)
        return query.order_by(cls.event_date).all()


# ========== 幂等键生成函数 ==========

def generate_spend_idempotency_key(account_id: str, event_date: date) -> str:
    """生成 SPEND 事件幂等键"""
    return f"SPEND:{account_id}:{event_date.isoformat()}"


def generate_topup_idempotency_key(
    supplier_id: int,
    amount: Decimal,
    payment_date: date,
    buyer_code: str
) -> str:
    """生成 TOPUP 事件幂等键"""
    return f"TOPUP:{supplier_id}:{amount}:{payment_date.isoformat()}:{buyer_code}"


def generate_payment_idempotency_key(
    project_id: int,
    amount: Decimal,
    payment_date: date,
    reference_no: str
) -> str:
    """生成 PAYMENT 事件幂等键"""
    return f"PAYMENT:{project_id}:{amount}:{payment_date.isoformat()}:{reference_no}"
