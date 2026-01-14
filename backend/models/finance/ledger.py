"""
总账模型 - 资金流水记录

Phase 1 Financial SoT 新增字段:
- entity_type: 实体类型 (SUPPLIER/PROJECT/ACCOUNT/TEAM)
- entity_id: 实体ID
- event_id: 财务事件ID (FK to financial_events)
- idempotency_key: 幂等键
- direction: 方向 (DEBIT/CREDIT)
"""
from decimal import Decimal
from datetime import datetime
from uuid import UUID
from sqlalchemy import Column, BigInteger, String, Text, Numeric, DateTime, Index, CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base
from backend.models.enums import LedgerEntryType
from backend.models.mixins.serializable import SerializableMixin


class LedgerEntry(Base, SerializableMixin):
    """
    总账分录表 - 双账本记录所有资金流水

    必须与 LEDGER_SOT.md v1.1 第2.2节保持严格一致。

    双账本设计：
    - PROJECT账本：记录项目收入（REVENUE, TOPUP, REVERSAL）
    - SUPPLIER账本：记录供应商成本（COST, TOPUP, TRANSFER_OUT, TRANSFER_IN, REVERSAL）

    6种分录类型：
    - REVENUE: 项目收入（PROJECT账本，正数）
    - COST: 供应商成本（SUPPLIER账本，负数）
    - TOPUP: 充值（两账本通用，正数）
    - TRANSFER_OUT: 转出（SUPPLIER账本，负数）
    - TRANSFER_IN: 转入（SUPPLIER账本，正数）
    - REVERSAL: 红冲（两账本通用，负数）

    实际数据库列（共19个）:
    - id, ledger_type, project_id, supplier_id, ad_account_id, entry_type,
    - amount, currency, reference_id, occurred_at, created_by, notes,
    - created_at, entity_type, entity_id, event_id, idempotency_key, direction, entry_date
    """
    __tablename__ = 'ledger_entries'

    # 序列化配置
    __json_include_relationships__ = ['ad_account']

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="分录ID")

    # 账本类型和实体关联
    ledger_type = Column(String(20), nullable=True, comment="账本类型 (PROJECT/SUPPLIER)")
    project_id = Column(BigInteger, nullable=True, comment="项目ID")
    supplier_id = Column(PGUUID(as_uuid=True), nullable=True, comment="供应商ID")

    # 外键
    ad_account_id = Column(
        BigInteger,
        ForeignKey('ad_accounts.id', ondelete='CASCADE'),
        nullable=True,  # 数据库允许为空
        comment="广告账户ID"
    )

    # 业务字段
    entry_type = Column(String(20), nullable=False, comment="分录类型")
    amount = Column(Numeric(15, 2), nullable=False, comment="金额")
    currency = Column(String(10), nullable=True, comment="货币代码")
    reference_id = Column(BigInteger, nullable=True, comment="关联记录ID")
    notes = Column(Text, nullable=True, comment="备注")

    # 操作相关
    occurred_at = Column(DateTime(timezone=True), nullable=True, comment="发生时间")
    created_by = Column(PGUUID(as_uuid=True), nullable=True, comment="创建人ID")

    # 时间字段
    entry_date = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="分录日期"
    )

    # 时间戳
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="创建时间"
    )

    # Phase 1 Financial SoT 新增字段
    entity_type = Column(String(20), nullable=True, comment="实体类型 (SUPPLIER/PROJECT/ACCOUNT/TEAM)")
    entity_id = Column(String(100), nullable=True, comment="实体ID")
    event_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('financial_events.id', ondelete='SET NULL'),
        nullable=True,
        comment="财务事件ID"
    )
    idempotency_key = Column(String(255), nullable=True, unique=False, comment="幂等键")
    direction = Column(String(10), nullable=True, comment="方向 (DEBIT/CREDIT)")

    # ========== 关系定义 ==========

    # 多对一：分录 -> 广告账户
    ad_account = relationship(
        "AdAccount",
        foreign_keys=[ad_account_id],
        lazy="joined",
        doc="所属广告账户"
    )

    # Phase 1 Financial SoT 新增关系
    # 多对一：分录 -> 财务事件
    financial_event = relationship(
        "FinancialEvent",
        foreign_keys=[event_id],
        lazy="joined",
        doc="关联财务事件"
    )

    # 约束和索引 - 必须与 LEDGER_SOT.md v1.1 第2.2节保持一致
    __table_args__ = (
        CheckConstraint(
            "entry_type IN ('REVENUE', 'COST', 'TOPUP', 'TRANSFER_OUT', 'TRANSFER_IN', 'REVERSAL')",
            name='chk_ledger_entries_entry_type'
        ),
        # Phase 1 Financial SoT 新增约束
        CheckConstraint(
            "entity_type IN ('SUPPLIER', 'PROJECT', 'ACCOUNT', 'TEAM') OR entity_type IS NULL",
            name='chk_ledger_entries_entity_type'
        ),
        CheckConstraint(
            "direction IN ('DEBIT', 'CREDIT') OR direction IS NULL",
            name='chk_ledger_entries_direction'
        ),
        Index('idx_ledger_entries_ad_account_id', 'ad_account_id'),
        Index('idx_ledger_entries_entry_date', 'entry_date'),
        Index('idx_ledger_entries_entry_type', 'entry_type'),
        # Phase 1 Financial SoT 新增索引
        Index('idx_ledger_entries_entity', 'entity_type', 'entity_id'),
        Index('idx_ledger_entries_event_id', 'event_id'),
    )

    def __repr__(self):
        return f"<LedgerEntry(id={self.id}, account_id={self.ad_account_id}, type='{self.entry_type}', amount={self.amount})>"

    # ========== 业务属性（6分录类型）==========

    @property
    def entry_type_enum(self) -> LedgerEntryType:
        """返回分录类型枚举对象"""
        return LedgerEntryType(self.entry_type)

    @property
    def is_revenue(self) -> bool:
        """是否是收入（PROJECT账本）"""
        return self.entry_type == LedgerEntryType.REVENUE.value

    @property
    def is_cost(self) -> bool:
        """是否是成本（SUPPLIER账本）"""
        return self.entry_type == LedgerEntryType.COST.value

    @property
    def is_topup(self) -> bool:
        """是否是充值"""
        return self.entry_type == LedgerEntryType.TOPUP.value

    @property
    def is_transfer_out(self) -> bool:
        """是否是转出（SUPPLIER账本）"""
        return self.entry_type == LedgerEntryType.TRANSFER_OUT.value

    @property
    def is_transfer_in(self) -> bool:
        """是否是转入（SUPPLIER账本）"""
        return self.entry_type == LedgerEntryType.TRANSFER_IN.value

    @property
    def is_reversal(self) -> bool:
        """是否是红冲"""
        return self.entry_type == LedgerEntryType.REVERSAL.value

    # ========== 金额方向验证（LEDGER_SOT.md v1.1 第4章）==========

    def validate_amount_direction(self) -> bool:
        """
        验证金额方向是否正确（不可变量检查）

        金额方向绝对规则：
        - REVENUE: 正数（收入增加）
        - COST: 负数（成本增加）
        - TOPUP: 正数（充值增加）
        - TRANSFER_OUT: 负数（余额减少）
        - TRANSFER_IN: 正数（余额增加）
        - REVERSAL: 负数（冲销）
        """
        positive_types = [LedgerEntryType.REVENUE.value, LedgerEntryType.TOPUP.value, LedgerEntryType.TRANSFER_IN.value]
        negative_types = [LedgerEntryType.COST.value, LedgerEntryType.TRANSFER_OUT.value, LedgerEntryType.REVERSAL.value]

        if self.entry_type in positive_types:
            return self.amount >= 0
        elif self.entry_type in negative_types:
            return self.amount <= 0
        return False

    # ========== 查询作用域方法 ==========

    @classmethod
    def get_account_ledger(cls, session, ad_account_id: int, limit: int = 100):
        """获取账户的流水记录"""
        return session.query(cls).filter(
            cls.ad_account_id == ad_account_id
        ).order_by(
            cls.entry_date.desc()
        ).limit(limit).all()

    @classmethod
    def get_account_balance(cls, session, ad_account_id: int) -> Decimal:
        """获取账户当前余额（通过汇总所有分录金额计算）

        注意: 数据库表中没有 balance_after 列，需要通过汇总计算
        """
        from sqlalchemy import func
        result = session.query(func.sum(cls.amount)).filter(
            cls.ad_account_id == ad_account_id
        ).scalar()

        return Decimal(str(result)) if result else Decimal('0.00')

    @classmethod
    def get_date_range_entries(cls, session, ad_account_id: int, start_date: datetime, end_date: datetime):
        """获取指定日期范围的流水"""
        return session.query(cls).filter(
            cls.ad_account_id == ad_account_id,
            cls.entry_date >= start_date,
            cls.entry_date <= end_date
        ).order_by(
            cls.entry_date.asc()
        ).all()
