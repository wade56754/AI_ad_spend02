"""
用户资料模型（适配Supabase）
Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column, String, Boolean, DateTime, JSON, Text, Integer, BigInteger,
    ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base


# ⚠️ DEPRECATED: 此 UserProfile 类已被 backend/models/core/user.py 替代
# 请使用 from backend.models.core.user import User
# 保留此类仅用于向后兼容，但已禁用表定义以避免重复注册
class _UserProfileLegacy(Base):
    """用户资料表（与Supabase Auth关联）（已废弃）"""
    # __tablename__ = "user_profiles"  # 已注释掉，避免重复定义表
    __abstract__ = True  # 标记为抽象类，不会创建表

    # 关联Supabase Auth的用户ID
    id = Column(
        UUID(as_uuid=True),
        ForeignKey("auth.users(id)", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        comment="Supabase用户ID"
    )

    # 基本信息（对齐 DATA_SCHEMA.md 3.1.1）
    username = Column(String(50), unique=True, nullable=True, index=True, comment="用户名")
    full_name = Column(String(100), nullable=True, comment="真实姓名")
    email = Column(String(255), nullable=True, comment="邮箱（冗余字段，方便联查）")
    phone = Column(String(20), nullable=True, comment="手机号")
    avatar_url = Column(String(500), nullable=True, comment="头像URL")

    # 角色和权限（对齐 DATA_SCHEMA.md 3.1.1：仅允许 admin/finance/data_operator/account_manager/media_buyer）
    role = Column(
        String(20),
        nullable=False,
        default="media_buyer",
        index=True,
        comment="用户角色：admin/finance/data_operator/account_manager/media_buyer"
    )
    department = Column(String(100), nullable=True, comment="部门")
    position = Column(String(100), nullable=True, comment="职位")

    # 组织结构
    account_manager_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
        comment="上级经理ID"
    )

    # 状态
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="是否激活"
    )
    is_verified = Column(Boolean, default=False, comment="是否已验证")
    email_verified = Column(Boolean, default=False, comment="邮箱是否已验证")
    phone_verified = Column(Boolean, default=False, comment="电话是否已验证")
    last_login_at = Column(DateTime(timezone=True), nullable=True, comment="最后登录时间")
    last_login_ip = Column(String(45), nullable=True, comment="最后登录IP")
    login_count = Column(Integer, default=0, comment="登录次数")

    # 偏好设置（对齐 DATA_SCHEMA.md 3.1.1：JSONB，默认 {}）
    preferences = Column(
        JSON,
        default=dict,
        server_default='{}',
        nullable=False,
        comment="用户偏好设置（JSONB）"
    )
    timezone = Column(String(50), default="UTC", server_default="UTC", comment="时区")
    language = Column(String(10), default="zh-CN", server_default="zh-CN", comment="语言")

    # 通知设置（对齐 DATA_SCHEMA.md 3.1.1：JSONB，默认 {}）
    notification_settings = Column(
        JSON,
        default=dict,
        server_default='{}',
        nullable=False,
        comment="通知设置（JSONB）"
    )

    # 元数据（对齐 DATA_SCHEMA.md 3.1.1：JSONB，默认 {}）
    profile_metadata = Column(
        JSON,
        default=dict,
        server_default='{}',
        nullable=False,
        comment="用户档案元数据（JSONB）"
    )

    # 审计字段
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="创建人ID"
    )
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="更新人ID"
    )

    # 关系
    account_manager = relationship(
        "User",
        remote_side=[id],
        foreign_keys=[account_manager_id],
        backref="managed_users"
    )

    # 约束和索引（对齐 DATA_SCHEMA.md 3.1.1）
    __table_args__ = (
        Index("idx_users_username", "username"),
        Index("idx_users_role", "role"),
        Index("idx_users_account_manager", "account_manager_id"),
        Index("idx_users_created_at", "created_at"),
        Index("idx_users_last_login", "last_login_at"),
        {
            "comment": "用户资料表（与Supabase Auth关联）"
        }
    )

    def __repr__(self):
        return f"<UserProfile(id={self.id}, email={self.id}, role={self.role})>"

    @property
    def is_admin(self) -> bool:
        """是否为管理员"""
        return self.role == "admin"

    @property
    def is_manager(self) -> bool:
        """是否为管理人员"""
        return self.role in ["admin", "account_manager", "finance"]

    @property
    def display_name(self) -> str:
        """显示名称"""
        return self.full_name or self.username or str(self.id)[:8]

    def has_permission(self, permission: str) -> bool:
        """检查权限"""
        role_permissions = {
            "admin": [
                "read", "write", "delete", "manage_users", "manage_projects",
                "manage_finances", "view_all_reports"
            ],
            "finance": [
                "read", "write", "manage_finances", "view_financial_reports"
            ],
            "data_operator": [
                "read", "write_reports", "view_reports"
            ],
            "account_manager": [
                "read", "write", "manage_projects", "view_team_reports"
            ],
            "media_buyer": [
                "read_own", "write_own", "view_own_reports"
            ]
        }

        return permission in role_permissions.get(self.role, [])


class UserLoginHistory(Base):
    """用户登录历史表"""
    __tablename__ = "user_login_history"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=func.gen_random_uuid(),
        comment="记录ID"
    )

    # 关联用户
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("auth.users(id)", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    email = Column(String(255), nullable=True, comment="邮箱（用于记录未注册用户）")

    # 登录信息
    login_time = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="登录时间"
    )
    logout_time = Column(DateTime(timezone=True), nullable=True, comment="登出时间")

    # 设备信息
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(Text, nullable=True, comment="用户代理")
    device_info = Column(JSON, nullable=True, comment="设备信息")

    # 登录类型和状态
    login_type = Column(
        String(20),
        default="password",
        nullable=False,
        comment="登录类型"
    )
    status = Column(
        String(20),
        default="success",
        nullable=False,
        comment="登录状态"
    )
    failure_reason = Column(String(255), nullable=True, comment="失败原因")

    # 位置信息
    country = Column(String(50), nullable=True, comment="国家")
    city = Column(String(100), nullable=True, comment="城市")

    # 索引
    __table_args__ = (
        Index("idx_login_history_user", "user_id"),
        Index("idx_login_history_time", "login_time"),
        Index("idx_login_history_status", "status"),
        Index("idx_login_history_ip", "ip_address"),
        {
            "comment": "用户登录历史表"
        }
    )


class UserSession(Base):
    """用户会话表（对齐 DATA_SCHEMA.md 3.1.3）"""
    __tablename__ = "user_sessions"

    # 主键：BIGSERIAL（对齐 DATA_SCHEMA）
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="会话ID"
    )

    # 关联用户（外键指向 users.id）
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )

    # 会话信息（对齐 DATA_SCHEMA：session_id UUID UNIQUE）
    session_id = Column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        index=True,
        comment="Supabase Session ID"
    )
    
    # 审计信息
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(Text, nullable=True, comment="用户代理")

    # 时间信息（对齐 DATA_SCHEMA）
    expires_at = Column(DateTime(timezone=True), nullable=True, comment="过期时间")
    invalidated_at = Column(DateTime(timezone=True), nullable=True, comment="手动失效时间")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )

    # 索引（对齐 DATA_SCHEMA 3.1.3）
    __table_args__ = (
        Index("idx_user_sessions_user_id", "user_id"),
        Index("idx_user_sessions_session_id", "session_id"),
        {
            "comment": "用户会话表"
        }
    )