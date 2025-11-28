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
# Enum 枚举类型
# =====================================================================

class UserRole(str, PyEnum):
    """
    用户角色枚举

    必须与 STATE_MACHINE.md v2.6 第2章、AUTH_SPEC.md v2.0 第2.2节保持严格一致。
    合法角色：admin, finance, data_operator, account_manager, media_buyer
    """
    ADMIN = "admin"                       # L5 系统管理员
    FINANCE = "finance"                   # L4 财务
    DATA_OPERATOR = "data_operator"       # L3 数据操作员/户管
    ACCOUNT_MANAGER = "account_manager"   # L2 客户经理
    MEDIA_BUYER = "media_buyer"           # L1 投手/媒体采购


class ChannelStatus(str, PyEnum):
    """渠道状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class ProjectStatus(str, PyEnum):
    """项目状态枚举"""
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class ReviewStatus(str, PyEnum):
    """评审状态枚举（用于 ChannelReview 和 ChannelAccountRequest）"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AdAccountStatus(str, PyEnum):
    """广告账户状态枚举"""
    NEW = "new"
    TESTING = "testing"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEAD = "dead"
    ARCHIVED = "archived"


class DailyReportStatus(str, PyEnum):
    """
    日报状态枚举（粉数确认状态机）

    必须与 STATE_MACHINE.md v2.6 第8章保持严格一致。
    8 状态流程：raw_submitted → trend_pending → trend_ok/trend_flagged
    → trend_resolved → final_pending → final_confirmed → final_locked
    """
    RAW_SUBMITTED = "raw_submitted"       # 投手提交原始粉数
    TREND_PENDING = "trend_pending"       # 等待趋势风控检查
    TREND_OK = "trend_ok"                 # 趋势正常
    TREND_FLAGGED = "trend_flagged"       # 趋势异常,需人工复核
    TREND_RESOLVED = "trend_resolved"     # 运营确认异常已解决
    FINAL_PENDING = "final_pending"       # 等待最终粉数确认
    FINAL_CONFIRMED = "final_confirmed"   # 最终粉数已确认
    FINAL_LOCKED = "final_locked"         # 已进入计费,锁定(终态)


class TopupStatus(str, PyEnum):
    """充值申请状态枚举"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    FINANCE_APPROVE = "finance_approve"
    PAID = "paid"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class LedgerEntryType(str, PyEnum):
    """
    总账分录类型枚举

    必须与 LEDGER_SOT.md v1.1 第2.2节保持严格一致。
    PROJECT账本: REVENUE, TOPUP, REVERSAL
    SUPPLIER账本: COST, TOPUP, TRANSFER_OUT, TRANSFER_IN, REVERSAL
    """
    REVENUE = "REVENUE"              # 项目收入（PROJECT账本）
    COST = "COST"                    # 供应商成本（SUPPLIER账本）
    TOPUP = "TOPUP"                  # 充值（两账本通用）
    TRANSFER_OUT = "TRANSFER_OUT"    # 转出（SUPPLIER账本）
    TRANSFER_IN = "TRANSFER_IN"      # 转入（SUPPLIER账本）
    REVERSAL = "REVERSAL"            # 红冲（两账本通用）


class ReconciliationBatchStatus(str, PyEnum):
    """
    对账批次状态枚举

    必须与 STATE_MACHINE.md v2.6 第4章（全局状态一览表）保持严格一致。
    流程: draft → pending_review → approved/needs_adjustment → completed
    """
    DRAFT = "draft"                         # 草稿
    PENDING_REVIEW = "pending_review"       # 待审核
    APPROVED = "approved"                   # 已批准
    NEEDS_ADJUSTMENT = "needs_adjustment"   # 需调整
    COMPLETED = "completed"                 # 已完成（终态）


class ReconciliationDetailStatus(str, PyEnum):
    """对账明细状态枚举"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ADJUSTED = "adjusted"


class AccountAlertStatus(str, PyEnum):
    """账户预警状态枚举"""
    OPEN = "open"
    ACK = "ack"  # acknowledged
    RESOLVED = "resolved"


class AccountAlertSeverity(str, PyEnum):
    """账户预警严重性枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
