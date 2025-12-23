"""
团队模型 - 独立核算单元
Version: 1.0
Author: Claude Code

Aligned with SoT:
- FINANCIAL_SOT_DESIGN.md v1.0 (team entity)
- DATA_SCHEMA.md v5.3 (teams table)

团队是业务核算的独立单元，用于区分不同运营团队（如 SZ/ZZ）
"""

from sqlalchemy import Column, String, Text, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from backend.models.base import Base, TimestampMixin
from backend.models.mixins.serializable import SerializableMixin


class TeamStatus:
    """团队状态常量"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class Team(Base, TimestampMixin, SerializableMixin):
    """
    团队表 - 独立核算单元

    字段：
    - id: 主键 (UUID)
    - code: 团队代码 (唯一，如 SZ/ZZ)
    - name: 团队名称
    - description: 团队描述
    - status: 状态 (active/inactive)
    - created_at/updated_at: 时间戳（自动管理）

    业务规则：
    - 团队代码必须唯一
    - 团队用于消耗归属和利润核算
    """
    __tablename__ = 'teams'

    # 序列化配置
    __json_include_relationships__ = ['buyers']

    # 主键
    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text('gen_random_uuid()'),
        comment="团队ID"
    )

    # 基本信息
    code = Column(String(10), unique=True, nullable=False, comment="团队代码 (SZ/ZZ)")
    name = Column(String(100), nullable=True, comment="团队名称")
    description = Column(Text, nullable=True, comment="团队描述")

    # 状态
    status = Column(String(20), nullable=False, default=TeamStatus.ACTIVE, comment="状态")

    # ========== 关系定义 ==========

    # 一对多：团队 -> 投手
    buyers = relationship(
        "Buyer",
        back_populates="team",
        lazy="dynamic",
        doc="团队投手"
    )

    # 一对多：团队 -> 广告账户
    ad_accounts = relationship(
        "AdAccount",
        foreign_keys="AdAccount.team_id",
        lazy="dynamic",
        overlaps="team",
        doc="团队账户"
    )

    # 一对多：团队 -> 财务事件
    financial_events = relationship(
        "FinancialEvent",
        back_populates="team",
        lazy="dynamic",
        doc="团队财务事件"
    )

    # 约束与索引
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive')",
            name='chk_teams_status'
        ),
        Index('idx_teams_code', 'code'),
        Index('idx_teams_status', 'status'),
    )

    def __repr__(self):
        return f"<Team(id={self.id}, code='{self.code}', name='{self.name}')>"

    # ========== 业务属性 ==========

    @property
    def is_active(self) -> bool:
        """是否是活跃团队"""
        return self.status == TeamStatus.ACTIVE

    # ========== 类方法 ==========

    @classmethod
    def get_by_code(cls, session, code: str):
        """根据代码获取团队"""
        return session.query(cls).filter(cls.code == code).first()

    @classmethod
    def get_active_teams(cls, session):
        """获取所有活跃团队"""
        return session.query(cls).filter(cls.status == TeamStatus.ACTIVE).all()
