"""
SQLAlchemy 基类和通用 Mixin

本模块提供：
- Base: 声明式基类
- TimestampMixin: 时间戳字段（created_at, updated_at）
- CreatedAtMixin: 仅创建时间字段（created_at）
- SoftDeleteMixin: 软删除支持（未来使用）
- UserScopeMixin: 用户作用域（created_by 字段 + RLS 支持）
- AssignableMixin: 可分配作用域（assigned_to 字段 + RLS 支持）
- Enum 枚举类型: 所有业务状态枚举
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from enum import Enum as PyEnum
from sqlalchemy import Column, DateTime, Boolean, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base, declared_attr

# 声明式基类
Base = declarative_base()


class TimestampMixin:
    """
    时间戳 Mixin - 自动管理 created_at 和 updated_at

    使用方式:
        class MyModel(Base, TimestampMixin):
            __tablename__ = 'my_table'
            ...
    """

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )


class SoftDeleteMixin:
    """
    软删除 Mixin - 未来扩展使用

    提供软删除功能，删除记录时不真正删除，只标记为已删除
    """

    is_deleted = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default='false',
        comment="是否已删除"
    )
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="删除时间"
    )


class UserScopeMixin:
    """
    用户作用域 Mixin - 支持 RLS 权限控制

    提供 created_by 字段和相关查询方法
    用于实现"用户只能访问自己创建的记录"的权限控制
    """

    @declared_attr
    def created_by(cls):
        """创建者 ID - 用于 RLS 权限过滤"""
        from sqlalchemy import ForeignKey
        return Column(
            PGUUID(as_uuid=True),
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
            comment="创建者用户ID"
        )

    @classmethod
    def query_for_user(cls, session, user_id: UUID):
        """
        获取当前用户可访问的记录查询

        Args:
            session: SQLAlchemy Session
            user_id: 当前用户 UUID

        Returns:
            Query: 已过滤的查询对象
        """
        return session.query(cls).filter(cls.created_by == user_id)


class AssignableMixin:
    """
    可分配 Mixin - 用于账户/任务分配场景

    提供 assigned_to 字段和相关查询方法
    用于实现"用户只能访问分配给自己的记录"的权限控制
    """

    @declared_attr
    def assigned_to(cls):
        """负责人 ID - 用于 RLS 权限过滤"""
        from sqlalchemy import ForeignKey
        return Column(
            PGUUID(as_uuid=True),
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
            comment="负责人用户ID"
        )

    @classmethod
    def query_assigned_to_user(cls, session, user_id: UUID):
        """
        获取分配给当前用户的记录

        Args:
            session: SQLAlchemy Session
            user_id: 当前用户 UUID

        Returns:
            Query: 已过滤的查询对象
        """
        return session.query(cls).filter(cls.assigned_to == user_id)


class CreatedAtMixin:
    """创建时间 Mixin - 仅包含 created_at（适用于不可变记录）"""
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="创建时间"
    )


# =====================================================================
# Enum 枚举类型 - 从 enums.py 统一导入，保持单一权威定义
# =====================================================================

from backend.models.enums import (
    UserRole,
    ChannelStatus,
    ProjectStatus,
    AdAccountStatus,
    DailyReportStatus,
    TopupRequestStatus as TopupStatus,
    LedgerEntryType,
    ReconciliationBatchStatus,
    ReconciliationDetailStatus,
    AccountAlertStatus,
)


# 为了向后兼容，保留这些枚举的别名
class ReviewStatus(str, PyEnum):
    """评审状态枚举（用于 ChannelReview 和 ChannelAccountRequest）"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AccountAlertSeverity(str, PyEnum):
    """账户预警严重性枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
