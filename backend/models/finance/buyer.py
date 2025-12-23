"""
投手模型 - 负责广告投放的人员
Version: 1.0
Author: Claude Code

Aligned with SoT:
- FINANCIAL_SOT_DESIGN.md v1.0 (buyer entity)
- DATA_SCHEMA.md v5.3 (buyers table)

投手是负责广告账户投放的人员，可关联到系统用户
"""

from sqlalchemy import Column, String, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from backend.models.base import Base, TimestampMixin
from backend.models.mixins.serializable import SerializableMixin


class BuyerStatus:
    """投手状态常量"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class Buyer(Base, TimestampMixin, SerializableMixin):
    """
    投手表 - 广告投放人员

    字段：
    - id: 主键 (UUID)
    - code: 投手代码 (唯一)
    - name: 投手姓名
    - team_id: 所属团队
    - user_id: 关联用户 (可选)
    - status: 状态 (active/inactive)
    - created_at/updated_at: 时间戳（自动管理）

    业务规则：
    - 投手代码必须唯一
    - 投手必须归属于某个团队
    - 投手可选关联到系统用户
    """
    __tablename__ = 'buyers'

    # 序列化配置
    __json_include_relationships__ = ['team', 'user']

    # 主键
    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text('gen_random_uuid()'),
        comment="投手ID"
    )

    # 基本信息
    code = Column(String(20), unique=True, nullable=False, comment="投手代码")
    name = Column(String(100), nullable=True, comment="投手姓名")

    # 外键
    team_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('teams.id', ondelete='SET NULL'),
        nullable=True,
        comment="所属团队"
    )
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="关联用户"
    )

    # 状态
    status = Column(String(20), nullable=False, default=BuyerStatus.ACTIVE, comment="状态")

    # ========== 关系定义 ==========

    # 多对一：投手 -> 团队
    team = relationship(
        "Team",
        back_populates="buyers",
        lazy="joined",
        doc="所属团队"
    )

    # 多对一：投手 -> 用户
    user = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="joined",
        doc="关联用户"
    )

    # 一对多：投手 -> 广告账户
    ad_accounts = relationship(
        "AdAccount",
        foreign_keys="AdAccount.buyer_id",
        lazy="dynamic",
        overlaps="buyer",
        doc="负责的账户"
    )

    # 一对多：投手 -> 财务事件
    financial_events = relationship(
        "FinancialEvent",
        back_populates="buyer",
        lazy="dynamic",
        doc="投手财务事件"
    )

    # 约束与索引
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive')",
            name='chk_buyers_status'
        ),
        Index('idx_buyers_code', 'code'),
        Index('idx_buyers_team_id', 'team_id'),
        Index('idx_buyers_user_id', 'user_id'),
        Index('idx_buyers_status', 'status'),
    )

    def __repr__(self):
        return f"<Buyer(id={self.id}, code='{self.code}', name='{self.name}')>"

    # ========== 业务属性 ==========

    @property
    def is_active(self) -> bool:
        """是否是活跃投手"""
        return self.status == BuyerStatus.ACTIVE

    @property
    def team_code(self) -> str:
        """获取团队代码"""
        return self.team.code if self.team else None

    # ========== 类方法 ==========

    @classmethod
    def get_by_code(cls, session, code: str):
        """根据代码获取投手"""
        return session.query(cls).filter(cls.code == code).first()

    @classmethod
    def get_active_buyers(cls, session):
        """获取所有活跃投手"""
        return session.query(cls).filter(cls.status == BuyerStatus.ACTIVE).all()

    @classmethod
    def get_by_team(cls, session, team_id):
        """获取团队的所有投手"""
        return session.query(cls).filter(
            cls.team_id == team_id,
            cls.status == BuyerStatus.ACTIVE
        ).all()
