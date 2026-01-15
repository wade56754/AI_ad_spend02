"""
用户核心模型

RLS 策略：用户只能访问自己的记录（id = auth.uid()）

v2.1 更新 (2025-12):
- 新增 team_id 字段：投手直接归属团队
- 新增 full_name 字段：用户真实姓名
"""
from sqlalchemy import Column, String, Boolean, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base, TimestampMixin
from backend.models.enums import UserRole
from backend.models.mixins.serializable import SerializableMixin


class User(Base, TimestampMixin, SerializableMixin):
    """
    系统用户表

    字段：
    - id: UUID 主键（Supabase auth.uid）
    - username: 用户名（唯一）
    - email: 邮箱（唯一）
    - full_name: 真实姓名 (v2.1)
    - department: 部门 (v2.1)
    - team_id: 所属团队ID (v2.1) - 投手直接归属团队
    - role: 角色（6角色：ceo/project_owner/finance/pitcher/account_manager/admin）
    - is_project_owner: 是否为项目负责人（MASTER.md v4.6 §2.4）
    - is_active: 是否激活
    - created_at/updated_at: 时间戳（自动管理）

    NOTE:
    - 密码管理可使用本地 JWT 认证（password_hash）或 Supabase Auth
    - supervisor 角色已废弃 (PRD v5.1)，职责合并到 project_owner

    SoT Reference: DATA_SCHEMA.md v5.6 §3.1.1, MASTER.md v4.6 §2.4
    """
    __tablename__ = 'users'

    # 序列化配置
    __json_hidden__ = []  # 无需隐藏字段

    # 主键
    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        comment="用户UUID（Supabase auth.uid）"
    )

    # 基本信息
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, comment="邮箱")

    # 密码哈希 - 使用本地 JWT 认证
    password_hash = Column(String(255), nullable=True, comment="密码哈希(bcrypt)")

    # 扩展信息 (v2.1)
    full_name = Column(String(100), nullable=True, comment="真实姓名")
    department = Column(String(100), nullable=True, comment="部门")

    # 团队归属 (v2.1) - 投手直接归属团队
    team_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('teams.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="所属团队ID"
    )

    # 角色与状态
    role = Column(String(20), nullable=False, comment="角色")
    is_active = Column(Boolean, nullable=False, default=True, comment="是否激活")

    # 索引
    __table_args__ = (
        Index('idx_users_role', 'role'),
        Index('idx_users_is_active', 'is_active'),
        Index('idx_users_team', 'team_id'),  # v2.1: 团队索引
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
    
    # ========== 业务属性 ==========
    
    @property
    def role_enum(self) -> UserRole:
        """返回角色枚举对象"""
        return UserRole(self.role)
    
    # ========== 业务方法 ==========
    
    def has_role(self, *roles: UserRole) -> bool:
        """
        检查用户是否拥有指定角色之一
        
        Args:
            *roles: 角色枚举列表
            
        Returns:
            bool: 是否拥有任一角色

        Example:
            user.has_role(UserRole.ADMIN, UserRole.PROJECT_OWNER)
        """
        return self.role_enum in roles
    
    def is_admin(self) -> bool:
        """是否是管理员"""
        return self.role_enum == UserRole.ADMIN
    
    def is_finance(self) -> bool:
        """是否是财务"""
        return self.role_enum == UserRole.FINANCE
    
    def is_media_buyer(self) -> bool:
        """是否是投手"""
        return self.role_enum == UserRole.MEDIA_BUYER
    
    def can_access_all_projects(self) -> bool:
        """是否可以访问所有项目（管理员和项目负责人）"""
        return self.has_role(UserRole.ADMIN, UserRole.PROJECT_OWNER)
    
    def can_approve_topup(self) -> bool:
        """是否可以批准充值申请"""
        return self.has_role(UserRole.ADMIN, UserRole.FINANCE)
    
    def can_review_daily_report(self) -> bool:
        """是否可以审核日报（管理员和项目负责人）"""
        return self.has_role(UserRole.ADMIN, UserRole.PROJECT_OWNER)

    # ========== 关系定义 ==========

    # 多对一：用户 -> 团队 (v2.1)
    team = relationship(
        "Team",
        foreign_keys=[team_id],
        lazy="joined",
        doc="用户所属团队"
    )

    # 一对多：用户 -> 项目成员关系
    project_memberships = relationship(
        "ProjectMember",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
        doc="用户参与的所有项目成员关系"
    )

    # 一对多：用户 -> 审计日志
    audit_logs = relationship(
        "AuditLog",
        foreign_keys="AuditLog.user_id",
        back_populates="user",
        lazy="dynamic",
        doc="用户的操作审计日志"
    )
