"""
用户核心模型

RLS 策略：用户只能访问自己的记录（id = auth.uid()）
"""
from sqlalchemy import Column, String, Boolean, Index
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
    - hashed_password: 密码哈希
    - role: 角色（admin/finance/data_manager/media_buyer/client）
    - is_active: 是否激活
    - created_at/updated_at: 时间戳（自动管理）
    """
    __tablename__ = 'users'
    
    # 序列化配置
    __json_hidden__ = ['hashed_password']  # 隐藏密码字段
    
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
    hashed_password = Column(String(255), nullable=False, comment="密码哈希")
    
    # 角色与状态
    role = Column(String(20), nullable=False, comment="角色")
    is_active = Column(Boolean, nullable=False, default=True, comment="是否激活")
    
    # 索引
    __table_args__ = (
        Index('idx_users_role', 'role'),
        Index('idx_users_is_active', 'is_active'),
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
            user.has_role(UserRole.ADMIN, UserRole.DATA_OPERATOR)
        """
        return self.role_enum in roles
    
    def is_admin(self) -> bool:
        """是否是管理员"""
        return self.role_enum == UserRole.ADMIN
    
    def is_finance(self) -> bool:
        """是否是财务"""
        return self.role_enum == UserRole.FINANCE
    
    def is_data_operator(self) -> bool:
        """是否是数据员"""
        return self.role_enum == UserRole.DATA_OPERATOR
    
    def is_media_buyer(self) -> bool:
        """是否是投手"""
        return self.role_enum == UserRole.MEDIA_BUYER
    
    def can_access_all_projects(self) -> bool:
        """是否可以访问所有项目（管理员和数据员）"""
        return self.has_role(UserRole.ADMIN, UserRole.DATA_OPERATOR)
    
    def can_approve_topup(self) -> bool:
        """是否可以批准充值申请"""
        return self.has_role(UserRole.ADMIN, UserRole.FINANCE)
    
    def can_review_daily_report(self) -> bool:
        """是否可以审核日报"""
        return self.has_role(UserRole.ADMIN, UserRole.DATA_OPERATOR)

    # ========== 关系定义 ==========

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
