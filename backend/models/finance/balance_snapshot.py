"""
余额快照模型 - 实体余额的每日快照
Version: 1.0
Author: Claude Code

Aligned with SoT:
- FINANCIAL_SOT_DESIGN.md v1.0 (balance snapshots)
- DATA_SCHEMA.md v5.3 (balance_snapshots table)

余额快照记录每个实体在特定日期的余额状态，用于历史追溯和对账
"""

from decimal import Decimal
from datetime import date, datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Date, Numeric, UniqueConstraint, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import text, func

from backend.models.base import Base
from backend.models.mixins.serializable import SerializableMixin


class EntityType(str, PyEnum):
    """实体类型枚举"""
    SUPPLIER = "SUPPLIER"   # 供应商
    PROJECT = "PROJECT"     # 项目
    ACCOUNT = "ACCOUNT"     # 广告账户
    TEAM = "TEAM"           # 团队


class BalanceSnapshot(Base, SerializableMixin):
    """
    余额快照表 - 实体余额的每日快照

    字段：
    - id: 主键 (UUID)
    - entity_type: 实体类型 (SUPPLIER/PROJECT/ACCOUNT/TEAM)
    - entity_id: 实体ID
    - snapshot_date: 快照日期
    - balance: 当前余额
    - total_debit: 累计借方
    - total_credit: 累计贷方
    - currency: 币种
    - calculated_at: 计算时间

    业务规则：
    - 每个实体每天只有一条快照记录 (unique constraint)
    - 余额 = 累计贷方 - 累计借方
    - 快照用于历史余额查询和对账
    """
    __tablename__ = 'balance_snapshots'

    # 主键
    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text('gen_random_uuid()'),
        comment="快照ID"
    )

    # 实体标识
    entity_type = Column(String(20), nullable=False, comment="实体类型")
    entity_id = Column(String(100), nullable=False, comment="实体ID")
    snapshot_date = Column(Date, nullable=False, comment="快照日期")

    # 余额数据
    balance = Column(Numeric(18, 4), nullable=False, comment="当前余额")
    total_debit = Column(Numeric(18, 4), nullable=False, default=Decimal('0'), comment="累计借方")
    total_credit = Column(Numeric(18, 4), nullable=False, default=Decimal('0'), comment="累计贷方")
    currency = Column(String(3), nullable=False, default='USD', comment="币种")

    # 计算时间
    calculated_at = Column(
        'calculated_at',
        type_=func.now().type,
        nullable=False,
        server_default=func.now(),
        comment="计算时间"
    )

    # 约束与索引
    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('SUPPLIER', 'PROJECT', 'ACCOUNT', 'TEAM')",
            name='chk_balance_snapshots_entity_type'
        ),
        UniqueConstraint('entity_type', 'entity_id', 'snapshot_date', name='uq_balance_snapshots_entity_date'),
        Index('idx_balance_snapshots_entity', 'entity_type', 'entity_id'),
        Index('idx_balance_snapshots_date', 'snapshot_date'),
    )

    def __repr__(self):
        return f"<BalanceSnapshot(entity={self.entity_type}:{self.entity_id}, date={self.snapshot_date}, balance={self.balance})>"

    # ========== 业务属性 ==========

    @property
    def entity_type_enum(self) -> EntityType:
        """返回实体类型枚举"""
        return EntityType(self.entity_type)

    @property
    def net_change(self) -> Decimal:
        """净变动 = 贷方 - 借方"""
        return (self.total_credit or Decimal('0')) - (self.total_debit or Decimal('0'))

    # ========== 类方法 ==========

    @classmethod
    def get_snapshot(cls, session, entity_type: str, entity_id: str, snapshot_date: date):
        """获取指定日期的快照"""
        return session.query(cls).filter(
            cls.entity_type == entity_type,
            cls.entity_id == entity_id,
            cls.snapshot_date == snapshot_date
        ).first()

    @classmethod
    def get_latest_snapshot(cls, session, entity_type: str, entity_id: str, as_of_date: date = None):
        """获取最新的快照（截至指定日期）"""
        query = session.query(cls).filter(
            cls.entity_type == entity_type,
            cls.entity_id == entity_id
        )
        if as_of_date:
            query = query.filter(cls.snapshot_date <= as_of_date)
        return query.order_by(cls.snapshot_date.desc()).first()

    @classmethod
    def get_snapshots_by_date(cls, session, snapshot_date: date, entity_type: str = None):
        """获取指定日期的所有快照"""
        query = session.query(cls).filter(cls.snapshot_date == snapshot_date)
        if entity_type:
            query = query.filter(cls.entity_type == entity_type)
        return query.all()

    @classmethod
    def get_entity_history(cls, session, entity_type: str, entity_id: str, start_date: date, end_date: date):
        """获取实体的历史快照"""
        return session.query(cls).filter(
            cls.entity_type == entity_type,
            cls.entity_id == entity_id,
            cls.snapshot_date >= start_date,
            cls.snapshot_date <= end_date
        ).order_by(cls.snapshot_date).all()

    @classmethod
    def upsert_snapshot(
        cls,
        session,
        entity_type: str,
        entity_id: str,
        snapshot_date: date,
        balance: Decimal,
        total_debit: Decimal,
        total_credit: Decimal,
        currency: str = 'USD'
    ):
        """
        插入或更新快照

        Args:
            session: 数据库会话
            entity_type: 实体类型
            entity_id: 实体ID
            snapshot_date: 快照日期
            balance: 余额
            total_debit: 累计借方
            total_credit: 累计贷方
            currency: 币种

        Returns:
            BalanceSnapshot: 快照对象
        """
        snapshot = cls.get_snapshot(session, entity_type, entity_id, snapshot_date)

        if snapshot:
            # 更新
            snapshot.balance = balance
            snapshot.total_debit = total_debit
            snapshot.total_credit = total_credit
            snapshot.currency = currency
            snapshot.calculated_at = datetime.utcnow()
        else:
            # 插入
            snapshot = cls(
                entity_type=entity_type,
                entity_id=entity_id,
                snapshot_date=snapshot_date,
                balance=balance,
                total_debit=total_debit,
                total_credit=total_credit,
                currency=currency
            )
            session.add(snapshot)

        return snapshot
