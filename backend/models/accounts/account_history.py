"""
账户历史和预警模型

包含：
- AccountStatusHistory: 账户状态变更历史
- AccountAlert: 账户预警
"""
from uuid import UUID
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, DateTime, Index, CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base
from backend.models.enums import AccountAlertStatus, UserRole
from backend.models.mixins.serializable import SerializableMixin


class AccountStatusHistory(Base, SerializableMixin):
    """
    账户状态变更历史表

    字段：
    - id: 主键
    - ad_account_id: 广告账户ID（外键）
    - changed_by: 变更人ID（外键）
    - old_status: 旧状态
    - new_status: 新状态
    - reason: 变更原因
    - changed_at: 变更时间
    """
    __tablename__ = 'account_status_history'

    # 序列化配置
    __json_include_relationships__ = ['ad_account', 'changer']

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="历史记录ID")

    # 外键
    ad_account_id = Column(
        BigInteger,
        ForeignKey('ad_accounts.id', ondelete='RESTRICT'),
        nullable=False,
        comment="广告账户ID"
    )
    changed_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="变更人ID"
    )

    # 业务字段
    old_status = Column(String(20), nullable=True, comment="旧状态")
    new_status = Column(String(20), nullable=False, comment="新状态")
    reason = Column(Text, nullable=True, comment="变更原因")

    # 时间字段
    changed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="变更时间"
    )

    # ========== 关系定义 ==========

    # 多对一：历史记录 -> 广告账户
    ad_account = relationship(
        "AdAccount",
        foreign_keys=[ad_account_id],
        lazy="joined",
        doc="所属广告账户"
    )

    # 多对一：历史记录 -> 变更人
    changer = relationship(
        "User",
        foreign_keys=[changed_by],
        lazy="selectin",
        doc="变更操作人"
    )

    # 索引
    __table_args__ = (
        Index('idx_account_status_history_account_id', 'ad_account_id'),
        Index('idx_account_status_history_changed_at', 'changed_at'),
    )

    def __repr__(self):
        return f"<AccountStatusHistory(id={self.id}, account_id={self.ad_account_id}, old='{self.old_status}', new='{self.new_status}')>"

    # ========== 查询作用域方法 ==========

    @classmethod
    def get_account_history(cls, session, ad_account_id: int, limit: int = 50):
        """获取账户的状态变更历史"""
        return session.query(cls).filter(
            cls.ad_account_id == ad_account_id
        ).order_by(
            cls.changed_at.desc()
        ).limit(limit).all()

    @classmethod
    def get_latest_change(cls, session, ad_account_id: int):
        """获取账户的最近一次状态变更"""
        return session.query(cls).filter(
            cls.ad_account_id == ad_account_id
        ).order_by(
            cls.changed_at.desc()
        ).first()


class AccountAlert(Base, SerializableMixin):
    """
    账户预警表

    字段：
    - id: 主键
    - ad_account_id: 广告账户ID（外键）
    - acknowledged_by: 确认人ID（外键）
    - alert_type: 预警类型
    - severity: 严重级别
    - status: 状态（open/ack/resolved）
    - message: 预警消息
    - alert_metadata: 预警元数据（JSON）
    - acknowledged_at: 确认时间
    - resolved_at: 解决时间
    - created_at: 创建时间
    """
    __tablename__ = 'account_alerts'

    # 序列化配置
    __json_include_relationships__ = ['ad_account', 'acknowledger']

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="预警ID")

    # 外键
    ad_account_id = Column(
        BigInteger,
        ForeignKey('ad_accounts.id', ondelete='CASCADE'),
        nullable=False,
        comment="广告账户ID"
    )
    acknowledged_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="确认人ID"
    )

    # 业务字段
    alert_type = Column(String(50), nullable=False, comment="预警类型")
    severity = Column(String(20), nullable=False, comment="严重级别")
    status = Column(String(20), nullable=False, comment="状态")
    message = Column(Text, nullable=False, comment="预警消息")
    alert_metadata = Column('metadata', JSONB, nullable=True, comment="预警元数据")

    # 时间字段
    acknowledged_at = Column(DateTime(timezone=True), nullable=True, comment="确认时间")
    resolved_at = Column(DateTime(timezone=True), nullable=True, comment="解决时间")

    # 时间戳
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="创建时间"
    )

    # ========== 关系定义 ==========

    # 多对一：预警 -> 广告账户
    ad_account = relationship(
        "AdAccount",
        foreign_keys=[ad_account_id],
        lazy="joined",
        doc="所属广告账户"
    )

    # 多对一：预警 -> 确认人
    acknowledger = relationship(
        "User",
        foreign_keys=[acknowledged_by],
        lazy="selectin",
        doc="确认人"
    )

    # 约束和索引
    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'ack', 'resolved')",
            name='chk_account_alerts_status'
        ),
        Index('idx_account_alerts_ad_account_id', 'ad_account_id'),
        Index('idx_account_alerts_status', 'status'),
        Index('idx_account_alerts_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<AccountAlert(id={self.id}, account_id={self.ad_account_id}, type='{self.alert_type}', status='{self.status}')>"

    # ========== 业务属性 ==========

    @property
    def status_enum(self) -> AccountAlertStatus:
        """返回状态枚举对象"""
        return AccountAlertStatus(self.status)

    @property
    def is_open(self) -> bool:
        """是否是未处理状态"""
        return self.status == AccountAlertStatus.OPEN.value

    @property
    def is_acknowledged(self) -> bool:
        """是否已确认"""
        return self.status == AccountAlertStatus.ACK.value

    @property
    def is_resolved(self) -> bool:
        """是否已解决"""
        return self.status == AccountAlertStatus.RESOLVED.value

    # ========== 业务方法 ==========

    def acknowledge(self, acknowledger_id: UUID):
        """确认预警"""
        if self.status != AccountAlertStatus.OPEN.value:
            raise ValueError(f"只有open状态的预警才能确认，当前状态: {self.status}")

        self.status = AccountAlertStatus.ACK.value
        self.acknowledged_by = acknowledger_id
        self.acknowledged_at = func.now()

    def resolve(self):
        """解决预警"""
        if self.status == AccountAlertStatus.RESOLVED.value:
            raise ValueError("预警已经是resolved状态")

        self.status = AccountAlertStatus.RESOLVED.value
        self.resolved_at = func.now()

    # ========== 查询作用域方法 ==========

    @classmethod
    def get_account_alerts(cls, session, ad_account_id: int, status: str = None):
        """获取账户的预警"""
        query = session.query(cls).filter(cls.ad_account_id == ad_account_id)

        if status:
            query = query.filter(cls.status == status)

        return query.order_by(cls.created_at.desc()).all()

    @classmethod
    def get_open_alerts(cls, session, severity: str = None):
        """获取所有未处理的预警"""
        query = session.query(cls).filter(cls.status == AccountAlertStatus.OPEN.value)

        if severity:
            query = query.filter(cls.severity == severity)

        return query.order_by(cls.created_at.desc()).all()

    @classmethod
    def get_unresolved_alerts(cls, session):
        """获取所有未解决的预警（open + ack）"""
        return session.query(cls).filter(
            cls.status.in_([AccountAlertStatus.OPEN.value, AccountAlertStatus.ACK.value])
        ).order_by(cls.created_at.desc()).all()
