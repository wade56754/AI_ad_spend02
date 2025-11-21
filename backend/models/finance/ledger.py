"""
总账模型 - 资金流水记录
"""
from decimal import Decimal
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, Numeric, DateTime, Index, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base
from backend.models.enums import LedgerEntryType
from backend.models.mixins.serializable import SerializableMixin


class LedgerEntry(Base, SerializableMixin):
    """
    总账分录表 - 记录所有资金流水

    字段：
    - id: 主键
    - ad_account_id: 广告账户ID（外键）
    - entry_type: 分录类型（topup_received/spend/adjustment）
    - amount: 金额
    - balance_after: 交易后余额
    - reference_id: 关联记录ID
    - reference_type: 关联记录类型
    - notes: 备注
    - entry_date: 分录日期
    - created_at: 创建时间
    """
    __tablename__ = 'ledger_entries'

    # 序列化配置
    __json_include_relationships__ = ['ad_account']

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="分录ID")

    # 外键
    ad_account_id = Column(
        BigInteger,
        ForeignKey('ad_accounts.id', ondelete='CASCADE'),
        nullable=False,
        comment="广告账户ID"
    )

    # 业务字段
    entry_type = Column(String(20), nullable=False, comment="分录类型")
    amount = Column(Numeric(15, 2), nullable=False, comment="金额")
    balance_after = Column(Numeric(15, 2), nullable=False, comment="交易后余额")
    reference_id = Column(BigInteger, nullable=True, comment="关联记录ID")
    reference_type = Column(String(50), nullable=True, comment="关联记录类型")
    notes = Column(Text, nullable=True, comment="备注")

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

    # ========== 关系定义 ==========

    # 多对一：分录 -> 广告账户
    ad_account = relationship(
        "AdAccount",
        foreign_keys=[ad_account_id],
        lazy="joined",
        doc="所属广告账户"
    )

    # 约束和索引
    __table_args__ = (
        CheckConstraint(
            "entry_type IN ('topup_received', 'spend', 'adjustment')",
            name='chk_ledger_entries_entry_type'
        ),
        Index('idx_ledger_entries_ad_account_id', 'ad_account_id'),
        Index('idx_ledger_entries_entry_date', 'entry_date'),
        Index('idx_ledger_entries_entry_type', 'entry_type'),
    )

    def __repr__(self):
        return f"<LedgerEntry(id={self.id}, account_id={self.ad_account_id}, type='{self.entry_type}', amount={self.amount})>"

    # ========== 业务属性 ==========

    @property
    def entry_type_enum(self) -> LedgerEntryType:
        """返回分录类型枚举对象"""
        return LedgerEntryType(self.entry_type)

    @property
    def is_topup(self) -> bool:
        """是否是充值"""
        return self.entry_type == LedgerEntryType.TOPUP_RECEIVED.value

    @property
    def is_spend(self) -> bool:
        """是否是消耗"""
        return self.entry_type == LedgerEntryType.SPEND.value

    @property
    def is_adjustment(self) -> bool:
        """是否是调整"""
        return self.entry_type == LedgerEntryType.ADJUSTMENT.value

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
        """获取账户当前余额（从最后一条记录）"""
        last_entry = session.query(cls).filter(
            cls.ad_account_id == ad_account_id
        ).order_by(
            cls.entry_date.desc()
        ).first()

        return last_entry.balance_after if last_entry else Decimal('0.00')

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
