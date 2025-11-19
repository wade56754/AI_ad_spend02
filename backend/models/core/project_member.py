"""
项目成员模型 - 用户在项目中的成员关系和权限

RLS 策略：用户可以查看自己所属项目的成员列表
"""
from sqlalchemy import Column, BigInteger, String, Text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base, TimestampMixin
from backend.models.mixins.serializable import SerializableMixin


class ProjectMember(Base, TimestampMixin, SerializableMixin):
    """
    项目成员表 - 记录用户在项目中的角色和权限

    字段：
    - id: 主键
    - project_id: 项目ID（外键）
    - user_id: 用户ID（外键）
    - role: 项目内角色（project_admin/member/viewer）
    - permissions: 扩展权限配置（JSONB）
    - created_at/updated_at: 时间戳（自动管理）
    """
    __tablename__ = 'project_members'

    # 序列化配置
    __json_include_relationships__ = ['project', 'user']

    # 主键：使用BigInteger与其他核心表保持一致
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="成员关系ID")

    # 外键
    project_id = Column(
        BigInteger,
        ForeignKey('projects.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="项目ID"
    )
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="用户ID"
    )

    # 业务字段
    role = Column(
        String(50),
        nullable=False,
        default='member',
        comment="项目内角色：project_admin/member/viewer"
    )
    permissions = Column(
        JSONB,
        nullable=True,
        comment="扩展权限配置（JSON格式）"
    )
    notes = Column(Text, nullable=True, comment="备注")

    # ========== 关系定义 ==========

    # 多对一：成员关系 -> 项目
    project = relationship(
        "Project",
        back_populates="members",
        lazy="selectin",
        doc="所属项目"
    )

    # 多对一：成员关系 -> 用户
    user = relationship(
        "User",
        back_populates="project_memberships",
        lazy="selectin",
        doc="成员用户"
    )

    # 约束与索引
    __table_args__ = (
        Index('idx_project_members_project_id', 'project_id'),
        Index('idx_project_members_user_id', 'user_id'),
        Index('idx_project_members_project_user', 'project_id', 'user_id', unique=True),
    )

    def __repr__(self):
        return f"<ProjectMember(id={self.id}, project_id={self.project_id}, user_id={self.user_id}, role='{self.role}')>"

    # ========== 业务属性 ==========

    @property
    def is_admin(self) -> bool:
        """是否是项目管理员"""
        return self.role == 'project_admin'

    @property
    def can_edit(self) -> bool:
        """是否可以编辑项目"""
        return self.role in ['project_admin', 'member']

    @property
    def is_viewer_only(self) -> bool:
        """是否仅有查看权限"""
        return self.role == 'viewer'

    # ========== 业务方法 ==========

    def grant_admin(self):
        """授予管理员权限"""
        self.role = 'project_admin'

    def revoke_admin(self):
        """撤销管理员权限，降级为普通成员"""
        if self.role == 'project_admin':
            self.role = 'member'

    def set_viewer_only(self):
        """设置为仅查看"""
        self.role = 'viewer'

    # ========== 查询作用域方法 ==========

    @classmethod
    def get_project_members(cls, session, project_id: int):
        """获取项目的所有成员"""
        return session.query(cls).filter(
            cls.project_id == project_id
        ).all()

    @classmethod
    def get_user_projects(cls, session, user_id):
        """获取用户参与的所有项目"""
        return session.query(cls).filter(
            cls.user_id == user_id
        ).all()

    @classmethod
    def is_member_of(cls, session, user_id, project_id: int) -> bool:
        """检查用户是否是项目成员"""
        return session.query(cls).filter(
            cls.user_id == user_id,
            cls.project_id == project_id
        ).first() is not None
