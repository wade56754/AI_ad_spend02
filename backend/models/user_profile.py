"""
用户资料模型（适配Supabase）
Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column, String, Boolean, DateTime, JSON, Text,
    ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class UserProfile(Base):
    """用户资料表（与Supabase Auth关联）"""
    __tablename__ = "user_profiles"

    # 关联Supabase Auth的用户ID
    id = Column(
        UUID(as_uuid=True),
        ForeignKey("auth.users(id)", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        comment="Supabase用户ID"
    )

    # 基本信息
    username = Column(String(50), unique=True, nullable=True, index=True, comment="用户名")
    full_name = Column(String(100), nullable=True, comment="全名")
    phone = Column(String(20), nullable=True, comment="手机号")
    avatar_url = Column(String(500), nullable=True, comment="头像URL")

    # 角色和权限
    role = Column(
        String(20),
        nullable=False,
        default="media_buyer",
        index=True,
        comment="用户角色"
    )
    department = Column(String(100), nullable=True, comment="部门")
    position = Column(String(100), nullable=True, comment="职位")

    # 组织结构
    account_manager_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
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
    last_login_at = Column(DateTime(timezone=True), nullable=True, comment="最后登录时间")
    last_login_ip = Column(String(45), nullable=True, comment="最后登录IP")

    # 偏好设置
    preferences = Column(
        JSON,
        default=dict,
        nullable=False,
        comment="用户偏好设置"
    )
    timezone = Column(String(50), default="UTC", comment="时区")
    language = Column(String(10), default="zh-CN", comment="语言")

    # 通知设置
    notification_settings = Column(
        JSON,
        default=dict,
        nullable=False,
        comment="通知设置"
    )

    # 元数据
    metadata = Column(
        JSON,
        default=dict,
        nullable=False,
        comment="额外的元数据"
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
        ForeignKey("user_profiles.id"),
        nullable=True,
        comment="创建人ID"
    )
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=True,
        comment="更新人ID"
    )

    # 关系
    account_manager = relationship(
        "UserProfile",
        remote_side=[id],
        foreign_keys=[account_manager_id],
        backref="managed_users"
    )

    # 约束
    __table_args__ = (
        Index("idx_user_profiles_created_at", "created_at"),
        Index("idx_user_profiles_last_login", "last_login_at"),
        Index("idx_user_profiles_department", "department"),
        Index("idx_user_profiles_position", "position"),
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
    """用户会话表"""
    __tablename__ = "user_sessions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=func.gen_random_uuid(),
        comment="会话ID"
    )

    # 关联用户
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("auth.users(id)", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )

    # 会话信息
    session_token = Column(
        String(500),
        unique=True,
        nullable=False,
        index=True,
        comment="会话令牌"
    )
    device_info = Column(JSON, nullable=True, comment="设备信息")

    # 状态和时间
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否活跃"
    )
    expires_at = Column(DateTime(timezone=True), nullable=True, comment="过期时间")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )
    last_accessed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="最后访问时间"
    )

    # 索引
    __table_args__ = (
        Index("idx_sessions_user", "user_id"),
        Index("idx_sessions_token", "session_token"),
        Index("idx_sessions_active", "is_active"),
        Index("idx_sessions_expires", "expires_at"),
        {
            "comment": "用户会话表"
        }
    )