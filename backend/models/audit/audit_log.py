"""
审计日志模型 - 记录所有敏感操作
"""
from uuid import UUID
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, DateTime, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base
from backend.models.mixins.serializable import SerializableMixin


class AuditLog(Base, SerializableMixin):
    """
    审计日志表 - 记录所有敏感操作

    字段：
    - id: 主键
    - user_id: 用户ID（外键）
    - action: 操作类型
    - resource_type: 资源类型
    - resource_id: 资源ID
    - old_values: 旧值（JSON）
    - new_values: 新值（JSON）
    - ip_address: IP地址
    - user_agent: 用户代理
    - created_at: 创建时间
    """
    __tablename__ = 'audit_logs'

    # 序列化配置
    __json_include_relationships__ = ['user']

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="日志ID")

    # 外键
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=True,
        comment="用户ID"
    )

    # 业务字段
    action = Column(String(50), nullable=False, comment="操作类型")
    resource_type = Column(String(50), nullable=False, comment="资源类型")
    resource_id = Column(String(50), nullable=True, comment="资源ID")
    old_values = Column(JSONB, nullable=True, comment="旧值")
    new_values = Column(JSONB, nullable=True, comment="新值")
    ip_address = Column(String(50), nullable=True, comment="IP地址")
    user_agent = Column(Text, nullable=True, comment="用户代理")

    # 时间戳
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="创建时间"
    )

    # ========== 关系定义 ==========

    # 多对一：日志 -> 用户
    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="audit_logs",
        lazy="selectin",
        doc="操作用户"
    )

    # 索引
    __table_args__ = (
        Index('idx_audit_logs_user_id', 'user_id'),
        Index('idx_audit_logs_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_logs_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', resource_type='{self.resource_type}')>"

    # ========== 查询作用域方法 ==========

    @classmethod
    def get_user_logs(cls, session, user_id: UUID, limit: int = 100):
        """获取用户的操作日志"""
        return session.query(cls).filter(
            cls.user_id == user_id
        ).order_by(
            cls.created_at.desc()
        ).limit(limit).all()

    @classmethod
    def get_resource_logs(cls, session, resource_type: str, resource_id: str, limit: int = 50):
        """获取指定资源的操作日志"""
        return session.query(cls).filter(
            cls.resource_type == resource_type,
            cls.resource_id == resource_id
        ).order_by(
            cls.created_at.desc()
        ).limit(limit).all()

    @classmethod
    def get_action_logs(cls, session, action: str, start_date: datetime = None, end_date: datetime = None):
        """获取指定操作类型的日志"""
        query = session.query(cls).filter(cls.action == action)

        if start_date:
            query = query.filter(cls.created_at >= start_date)
        if end_date:
            query = query.filter(cls.created_at <= end_date)

        return query.order_by(cls.created_at.desc()).all()

    @classmethod
    def create_log(cls, session, user_id: UUID, action: str, resource_type: str,
                  resource_id: str = None, old_values: dict = None, new_values: dict = None,
                  ip_address: str = None, user_agent: str = None):
        """创建审计日志"""
        log = cls(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent
        )
        session.add(log)
        return log
