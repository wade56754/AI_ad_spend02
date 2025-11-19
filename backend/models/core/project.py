"""
项目模型 - 核心业务实体

RLS 策略：用户只能访问自己创建或被分配的项目
"""
from sqlalchemy import Column, BigInteger, String, Index, CheckConstraint
from sqlalchemy.orm import relationship

from backend.models.base import Base, TimestampMixin, UserScopeMixin
from backend.models.enums import ProjectStatus, UserRole
from backend.models.mixins.serializable import SerializableMixin
from backend.models.mixins.rls_aware import RLSAwareMixin


class Project(Base, TimestampMixin, UserScopeMixin, RLSAwareMixin, SerializableMixin):
    """
    项目主表

    字段：
    - id: 主键
    - project_name: 项目名称
    - project_code: 项目代码（唯一）
    - client_name: 客户名称
    - status: 项目状态（draft/active/suspended/archived）
    - created_by: 创建者（来自 UserScopeMixin）
    - created_at/updated_at: 时间戳（自动管理）
    """
    __tablename__ = 'projects'

    # RLS 配置
    __rls_user_field__ = 'created_by'
    __rls_admin_roles__ = [UserRole.ADMIN, UserRole.DATA_MANAGER]

    # 序列化配置
    __json_include_relationships__ = ['creator', 'ad_accounts']

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="项目ID")

    # 基本信息
    project_name = Column(String(100), nullable=False, comment="项目名称")
    project_code = Column(String(50), unique=True, nullable=False, comment="项目代码")
    client_name = Column(String(100), nullable=True, comment="客户名称")
    status = Column(String(20), nullable=False, comment="项目状态")

    # ========== 关系定义 ==========

    # 多对一：项目 -> 创建者
    creator = relationship(
        "User",
        foreign_keys="Project.created_by",
        lazy="selectin",
        doc="项目创建者"
    )

    # 一对多：项目 -> 广告账户
    ad_accounts = relationship(
        "AdAccount",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="项目下的所有广告账户"
    )

    # 一对多：项目 -> 项目成员
    members = relationship(
        "ProjectMember",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="dynamic",  # 使用dynamic避免测试时自动加载不存在的表
        doc="项目成员列表"
    )

    # 一对多：项目 -> 项目费用
    expenses = relationship(
        "ProjectExpense",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="dynamic",  # 使用dynamic避免测试时自动加载不存在的表
        doc="项目费用记录"
    )

    # 约束与索引
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'active', 'suspended', 'archived')",
            name='projects_status_check'
        ),
        Index('idx_projects_status', 'status'),
        Index('idx_projects_created_by', 'created_by'),
    )

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.project_name}', code='{self.project_code}')>"

    # ========== 业务属性 ==========

    @property
    def status_enum(self) -> ProjectStatus:
        """返回状态枚举对象"""
        return ProjectStatus(self.status)

    @property
    def is_active(self) -> bool:
        """是否是活跃项目"""
        return self.status == ProjectStatus.ACTIVE.value

    @property
    def is_archived(self) -> bool:
        """是否已归档"""
        return self.status == ProjectStatus.ARCHIVED.value

    # ========== 状态流转方法 ==========

    def can_transition_to(self, new_status: ProjectStatus) -> bool:
        """
        检查是否可以转换到新状态

        状态流转规则：
        - draft -> active, suspended, archived
        - active -> suspended, archived
        - suspended -> active, archived
        - archived -> (终态)
        """
        current = ProjectStatus(self.status)
        transitions = {
            ProjectStatus.DRAFT: [ProjectStatus.ACTIVE, ProjectStatus.SUSPENDED, ProjectStatus.ARCHIVED],
            ProjectStatus.ACTIVE: [ProjectStatus.SUSPENDED, ProjectStatus.ARCHIVED],
            ProjectStatus.SUSPENDED: [ProjectStatus.ACTIVE, ProjectStatus.ARCHIVED],
            ProjectStatus.ARCHIVED: [],
        }
        return new_status in transitions.get(current, [])

    def transition_to(self, new_status: ProjectStatus, operator_id, reason: str = None):
        """
        安全地转换项目状态

        Args:
            new_status: 目标状态
            operator_id: 操作者用户ID
            reason: 状态变更原因

        Returns:
            bool: 是否成功

        Raises:
            ValueError: 不允许的状态转换
        """
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"不允许从 {self.status} 转换到 {new_status.value}"
            )

        old_status = self.status
        self.status = new_status.value

        # TODO: 可以在这里记录状态变更历史

        return True

    # ========== 权限判断方法 ==========

    def can_be_edited_by(self, user_id, user_role: UserRole) -> bool:
        """检查用户是否可以编辑此项目"""
        if user_role in [UserRole.ADMIN, UserRole.DATA_MANAGER]:
            return True

        if user_role == UserRole.MEDIA_BUYER:
            return self.created_by == user_id

        return False

    def can_be_deleted_by(self, user_id, user_role: UserRole) -> bool:
        """检查用户是否可以删除此项目"""
        # 只有管理员可以删除项目
        return user_role == UserRole.ADMIN

    # ========== 查询作用域方法 ==========

    @classmethod
    def get_user_accessible_query(cls, session, user_id, user_role: UserRole):
        """获取用户可访问的项目查询（RLS 逻辑）"""
        query = session.query(cls)

        # 管理员和数据员可以访问所有项目
        if user_role in [UserRole.ADMIN, UserRole.DATA_MANAGER]:
            return query

        # 投手只能访问自己创建的项目
        if user_role == UserRole.MEDIA_BUYER:
            return query.filter(cls.created_by == user_id)

        # 其他角色默认可以访问自己创建的项目
        return query.filter(cls.created_by == user_id)

    @classmethod
    def get_active_projects(cls, session, user_id, user_role: UserRole):
        """获取用户可访问的活跃项目"""
        return cls.get_user_accessible_query(session, user_id, user_role).filter(
            cls.status == ProjectStatus.ACTIVE.value
        )

    @classmethod
    def get_by_code(cls, session, project_code: str):
        """根据项目代码获取项目"""
        return session.query(cls).filter(cls.project_code == project_code).first()
