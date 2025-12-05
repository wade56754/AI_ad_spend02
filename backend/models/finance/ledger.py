"""
总账模型 - 资金流水记录 (对齐 LEDGER_SOT.md v1.1)

Version: 2.0 (2025-12-05)
- 新增 ledger_type 字段支持双账本隔离
- 新增 project_id/supplier_id 字段支持双账本关联
- 新增 performed_by/reason/currency 字段支持审计追溯
- 保留 ad_account_id 字段支持账户级别流水查询
"""
from decimal import Decimal
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, BigInteger, String, Text, Numeric, DateTime, Index, CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base
from backend.models.enums import LedgerEntryType
from backend.models.mixins.serializable import SerializableMixin


class LedgerBookType(str, PyEnum):
    """
    账本类型枚举（双账本隔离）

    必须与 LEDGER_SOT.md v1.1 第2.1节保持严格一致。
    - PROJECT: 项目账本（甲方视角，收入+充值）
    - SUPPLIER: 供应商账本（平台视角，成本+转账）
    """
    PROJECT = "PROJECT"      # 项目账本
    SUPPLIER = "SUPPLIER"    # 供应商账本


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

    字段：
    - id: 主键
    - ledger_type: 账本类型（PROJECT/SUPPLIER）
    - project_id: 项目ID（PROJECT账本必填）
    - supplier_id: 供应商ID（SUPPLIER账本必填）
    - ad_account_id: 广告账户ID（可选，用于账户级别流水）
    - entry_type: 分录类型（6种）
    - amount: 金额
    - currency: 货币类型（默认CNY）
    - balance_after: 交易后余额
    - reference_id: 关联记录ID
    - reference_type: 关联记录类型
    - performed_by: 操作人ID
    - reason: 操作原因
    - notes: 备注
    - entry_date: 分录日期
    - created_at: 创建时间
    """
    __tablename__ = 'ledger_entries'

    # 序列化配置
    __json_include_relationships__ = ['ad_account', 'project', 'supplier']

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="分录ID")

    # ========== 双账本核心字段 (LEDGER_SOT.md v1.1 第2节) ==========

    # 账本类型（必填）
    ledger_type = Column(
        String(20),
        nullable=False,
        comment="账本类型: PROJECT/SUPPLIER"
    )

    # PROJECT账本关联（PROJECT账本必填，SUPPLIER账本必须为NULL）
    project_id = Column(
        BigInteger,
        ForeignKey('projects.id', ondelete='CASCADE'),
        nullable=True,
        comment="项目ID（PROJECT账本必填）"
    )

    # SUPPLIER账本关联（SUPPLIER账本必填，PROJECT账本必须为NULL）
    supplier_id = Column(
        BigInteger,
        ForeignKey('suppliers.id', ondelete='CASCADE'),
        nullable=True,
        comment="供应商ID（SUPPLIER账本必填）"
    )

    # 广告账户关联（可选，用于账户级别流水查询）
    ad_account_id = Column(
        BigInteger,
        ForeignKey('ad_accounts.id', ondelete='CASCADE'),
        nullable=True,
        comment="广告账户ID（可选）"
    )

    # ========== 业务字段 ==========

    entry_type = Column(String(20), nullable=False, comment="分录类型")
    amount = Column(Numeric(15, 2), nullable=False, comment="金额")
    currency = Column(
        String(10),
        nullable=False,
        default="CNY",
        comment="货币类型（默认CNY）"
    )
    balance_after = Column(Numeric(15, 2), nullable=False, comment="交易后余额")
    reference_id = Column(BigInteger, nullable=True, comment="关联记录ID")
    reference_type = Column(String(50), nullable=True, comment="关联记录类型")

    # ========== 审计字段 (LEDGER_SOT.md v1.1 第12节) ==========

    performed_by = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id'),
        nullable=True,
        comment="操作人ID"
    )
    reason = Column(String(200), nullable=True, comment="操作原因")
    notes = Column(Text, nullable=True, comment="备注")

    # ========== 时间字段 ==========

    entry_date = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="分录日期"
    )

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

    # 多对一：分录 -> 项目（PROJECT账本）
    project = relationship(
        "Project",
        foreign_keys=[project_id],
        lazy="joined",
        doc="所属项目（PROJECT账本）"
    )

    # 多对一：分录 -> 供应商（SUPPLIER账本）
    supplier = relationship(
        "Supplier",
        foreign_keys=[supplier_id],
        lazy="joined",
        doc="所属供应商（SUPPLIER账本）"
    )

    # 多对一：分录 -> 操作人
    performer = relationship(
        "User",
        foreign_keys=[performed_by],
        lazy="select",
        doc="操作人"
    )

    # ========== 约束和索引 (LEDGER_SOT.md v1.1 第2.3节) ==========
    __table_args__ = (
        # 分录类型CHECK约束
        CheckConstraint(
            "entry_type IN ('REVENUE', 'COST', 'TOPUP', 'TRANSFER_OUT', 'TRANSFER_IN', 'REVERSAL')",
            name='chk_ledger_entries_entry_type'
        ),
        # 账本类型CHECK约束
        CheckConstraint(
            "ledger_type IN ('PROJECT', 'SUPPLIER')",
            name='chk_ledger_entries_ledger_type'
        ),
        # 双账本互斥约束：PROJECT账本必须有project_id且无supplier_id，反之亦然
        CheckConstraint(
            "(ledger_type = 'PROJECT' AND project_id IS NOT NULL AND supplier_id IS NULL) OR "
            "(ledger_type = 'SUPPLIER' AND supplier_id IS NOT NULL AND project_id IS NULL)",
            name='chk_ledger_type_entity'
        ),
        # PROJECT账本entry_type限制
        CheckConstraint(
            "(ledger_type = 'PROJECT' AND entry_type IN ('REVENUE', 'TOPUP', 'REVERSAL')) OR "
            "(ledger_type = 'SUPPLIER' AND entry_type IN ('COST', 'TOPUP', 'TRANSFER_OUT', 'TRANSFER_IN', 'REVERSAL'))",
            name='chk_ledger_entry_type_by_book'
        ),
        # 索引
        Index('idx_ledger_entries_ledger_type', 'ledger_type'),
        Index('idx_ledger_entries_project_id', 'project_id'),
        Index('idx_ledger_entries_supplier_id', 'supplier_id'),
        Index('idx_ledger_entries_ad_account_id', 'ad_account_id'),
        Index('idx_ledger_entries_entry_date', 'entry_date'),
        Index('idx_ledger_entries_entry_type', 'entry_type'),
        Index('idx_ledger_entries_reference', 'reference_type', 'reference_id'),
    )

    def __repr__(self):
        return f"<LedgerEntry(id={self.id}, ledger_type='{self.ledger_type}', type='{self.entry_type}', amount={self.amount})>"

    # ========== 业务属性（6分录类型）==========

    @property
    def entry_type_enum(self) -> LedgerEntryType:
        """返回分录类型枚举对象"""
        return LedgerEntryType(self.entry_type)

    @property
    def ledger_book_type(self) -> LedgerBookType:
        """返回账本类型枚举对象"""
        return LedgerBookType(self.ledger_type)

    @property
    def is_project_book(self) -> bool:
        """是否是PROJECT账本"""
        return self.ledger_type == LedgerBookType.PROJECT.value

    @property
    def is_supplier_book(self) -> bool:
        """是否是SUPPLIER账本"""
        return self.ledger_type == LedgerBookType.SUPPLIER.value

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

    def validate_ledger_type_entry_type(self) -> bool:
        """
        验证账本类型和分录类型是否匹配（LEDGER_SOT.md v1.1 第2.3节）

        PROJECT账本只能有: REVENUE, TOPUP, REVERSAL
        SUPPLIER账本只能有: COST, TOPUP, TRANSFER_OUT, TRANSFER_IN, REVERSAL
        """
        project_allowed = [LedgerEntryType.REVENUE.value, LedgerEntryType.TOPUP.value, LedgerEntryType.REVERSAL.value]
        supplier_allowed = [LedgerEntryType.COST.value, LedgerEntryType.TOPUP.value,
                          LedgerEntryType.TRANSFER_OUT.value, LedgerEntryType.TRANSFER_IN.value,
                          LedgerEntryType.REVERSAL.value]

        if self.ledger_type == LedgerBookType.PROJECT.value:
            return self.entry_type in project_allowed
        elif self.ledger_type == LedgerBookType.SUPPLIER.value:
            return self.entry_type in supplier_allowed
        return False

    # ========== 查询作用域方法 (双账本支持) ==========

    @classmethod
    def get_account_ledger(cls, session, ad_account_id: int, limit: int = 100):
        """获取账户的流水记录"""
        return session.query(cls).filter(
            cls.ad_account_id == ad_account_id
        ).order_by(
            cls.entry_date.desc()
        ).limit(limit).all()

    @classmethod
    def get_project_ledger(cls, session, project_id: int, limit: int = 100):
        """获取项目账本的流水记录（PROJECT账本）"""
        return session.query(cls).filter(
            cls.ledger_type == LedgerBookType.PROJECT.value,
            cls.project_id == project_id
        ).order_by(
            cls.entry_date.desc()
        ).limit(limit).all()

    @classmethod
    def get_supplier_ledger(cls, session, supplier_id: int, limit: int = 100):
        """获取供应商账本的流水记录（SUPPLIER账本）"""
        return session.query(cls).filter(
            cls.ledger_type == LedgerBookType.SUPPLIER.value,
            cls.supplier_id == supplier_id
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
    def get_project_balance(cls, session, project_id: int) -> Decimal:
        """获取项目账本余额（PROJECT账本最后一条记录）"""
        last_entry = session.query(cls).filter(
            cls.ledger_type == LedgerBookType.PROJECT.value,
            cls.project_id == project_id
        ).order_by(
            cls.entry_date.desc()
        ).first()

        return last_entry.balance_after if last_entry else Decimal('0.00')

    @classmethod
    def get_supplier_balance(cls, session, supplier_id: int) -> Decimal:
        """获取供应商账本余额（SUPPLIER账本最后一条记录）"""
        last_entry = session.query(cls).filter(
            cls.ledger_type == LedgerBookType.SUPPLIER.value,
            cls.supplier_id == supplier_id
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

    @classmethod
    def get_project_entries_by_date(cls, session, project_id: int, start_date: datetime, end_date: datetime):
        """获取项目账本指定日期范围的流水"""
        return session.query(cls).filter(
            cls.ledger_type == LedgerBookType.PROJECT.value,
            cls.project_id == project_id,
            cls.entry_date >= start_date,
            cls.entry_date <= end_date
        ).order_by(
            cls.entry_date.asc()
        ).all()

    @classmethod
    def get_supplier_entries_by_date(cls, session, supplier_id: int, start_date: datetime, end_date: datetime):
        """获取供应商账本指定日期范围的流水"""
        return session.query(cls).filter(
            cls.ledger_type == LedgerBookType.SUPPLIER.value,
            cls.supplier_id == supplier_id,
            cls.entry_date >= start_date,
            cls.entry_date <= end_date
        ).order_by(
            cls.entry_date.asc()
        ).all()
