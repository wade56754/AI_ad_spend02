"""
渠道账户申请模型 - 开户申请流程
"""
from uuid import UUID
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, DateTime, CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base, TimestampMixin
from backend.models.enums import ChannelAccountRequestStatus, UserRole
from backend.models.mixins.serializable import SerializableMixin
from backend.models.mixins.rls_aware import RLSAwareMixin


class ChannelAccountRequest(Base, TimestampMixin, RLSAwareMixin, SerializableMixin):
    """
    渠道开户申请记录表

    字段：
    - id: 主键
    - project_id: 项目ID（外键）
    - channel_id: 渠道ID（外键）
    - requested_by: 申请人ID（外键）
    - approved_by: 批准人ID（外键）
    - status: 状态（draft/pending/approved/rejected）
    - request_notes: 申请备注
    - approved_at: 批准时间
    - created_at/updated_at: 时间戳（自动管理）
    """
    __tablename__ = 'channel_account_requests'

    # RLS 配置
    __rls_user_field__ = 'requested_by'
    __rls_admin_roles__ = [UserRole.ADMIN, UserRole.DATA_OPERATOR]

    # 序列化配置
    __json_include_relationships__ = ['project', 'channel', 'requester', 'approver']

    # 主键：UUID（对齐 DATA_SCHEMA.md 3.2.7）
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), comment="申请记录ID")

    # 外键
    project_id = Column(
        BigInteger,
        ForeignKey('projects.id', ondelete='CASCADE'),
        nullable=False,
        comment="项目ID"
    )
    # 外键：UUID（对齐 DATA_SCHEMA.md 3.2.7）
    channel_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('channels.id', ondelete='CASCADE'),
        nullable=False,
        comment="渠道ID"
    )
    requested_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="申请人ID"
    )
    approved_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="批准人ID"
    )

    # 业务字段
    status = Column(String(20), nullable=False, comment="状态")
    request_notes = Column(Text, nullable=True, comment="申请备注")
    approved_at = Column(DateTime(timezone=True), nullable=True, comment="批准时间")

    # ========== 关系定义 ==========

    # 多对一：申请 -> 项目
    project = relationship(
        "Project",
        foreign_keys=[project_id],
        lazy="joined",
        doc="所属项目"
    )

    # 多对一：申请 -> 渠道
    channel = relationship(
        "Channel",
        foreign_keys=[channel_id],
        lazy="joined",
        doc="目标渠道"
    )

    # 多对一：申请 -> 申请人
    requester = relationship(
        "User",
        foreign_keys=[requested_by],
        lazy="selectin",
        doc="申请人"
    )

    # 多对一：申请 -> 批准人
    approver = relationship(
        "User",
        foreign_keys=[approved_by],
        lazy="selectin",
        doc="批准人"
    )

    # 约束
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'pending', 'approved', 'rejected')",
            name='chk_channel_account_requests_status'
        ),
    )

    def __repr__(self):
        return f"<ChannelAccountRequest(id={self.id}, project_id={self.project_id}, status='{self.status}')>"

    # ========== 业务属性 ==========

    @property
    def status_enum(self) -> ChannelAccountRequestStatus:
        """返回状态枚举对象"""
        return ChannelAccountRequestStatus(self.status)

    @property
    def is_pending(self) -> bool:
        """是否待审核"""
        return self.status == ChannelAccountRequestStatus.PENDING.value

    @property
    def is_approved(self) -> bool:
        """是否已批准"""
        return self.status == ChannelAccountRequestStatus.APPROVED.value

    @property
    def is_rejected(self) -> bool:
        """是否已拒绝"""
        return self.status == ChannelAccountRequestStatus.REJECTED.value

    # ========== 状态流转方法 ==========

    def can_transition_to(self, new_status: ChannelAccountRequestStatus) -> bool:
        """
        检查是否可以转换到新状态

        状态流转规则：
        - draft -> pending
        - pending -> approved, rejected
        - approved -> (终态)
        - rejected -> (终态)
        """
        current = ChannelAccountRequestStatus(self.status)
        transitions = {
            ChannelAccountRequestStatus.DRAFT: [ChannelAccountRequestStatus.PENDING],
            ChannelAccountRequestStatus.PENDING: [
                ChannelAccountRequestStatus.APPROVED,
                ChannelAccountRequestStatus.REJECTED
            ],
            ChannelAccountRequestStatus.APPROVED: [],
            ChannelAccountRequestStatus.REJECTED: [],
        }
        return new_status in transitions.get(current, [])

    def submit(self, requester_id: UUID):
        """提交开户申请"""
        if not self.can_transition_to(ChannelAccountRequestStatus.PENDING):
            raise ValueError(f"不允许从 {self.status} 状态提交申请")

        self.status = ChannelAccountRequestStatus.PENDING.value
        self.requested_by = requester_id

    def approve(self, approver_id: UUID):
        """批准开户申请"""
        if not self.can_transition_to(ChannelAccountRequestStatus.APPROVED):
            raise ValueError(f"不允许从 {self.status} 状态批准申请")

        self.status = ChannelAccountRequestStatus.APPROVED.value
        self.approved_by = approver_id
        self.approved_at = func.now()

    def reject(self, approver_id: UUID, reason: str):
        """拒绝开户申请"""
        if not self.can_transition_to(ChannelAccountRequestStatus.REJECTED):
            raise ValueError(f"不允许从 {self.status} 状态拒绝申请")

        self.status = ChannelAccountRequestStatus.REJECTED.value
        self.approved_by = approver_id
        self.approved_at = func.now()
        self.request_notes = f"[拒绝] {reason}"

    # ========== 权限判断方法 ==========

    def can_be_edited_by(self, user_id: UUID, user_role: UserRole) -> bool:
        """检查用户是否可以编辑此申请"""
        # 管理员和数据员可以编辑所有申请
        if user_role in [UserRole.ADMIN, UserRole.DATA_OPERATOR]:
            return True

        # 申请人只能编辑草稿状态的申请
        if self.requested_by == user_id:
            return self.status == ChannelAccountRequestStatus.DRAFT.value

        return False

    def can_be_approved_by(self, user_id: UUID, user_role: UserRole) -> bool:
        """检查用户是否可以审批此申请"""
        # 只有管理员和数据员可以审批
        if user_role not in [UserRole.ADMIN, UserRole.DATA_OPERATOR]:
            return False

        # 只有待审核的申请才能审批
        return self.status == ChannelAccountRequestStatus.PENDING.value

    # ========== 查询作用域方法 ==========

    @classmethod
    def get_user_accessible_query(cls, session, user_id: UUID, user_role: UserRole):
        """获取用户可访问的开户申请查询（RLS 逻辑）"""
        query = session.query(cls)

        # 管理员和数据员可以访问所有申请
        if user_role in [UserRole.ADMIN, UserRole.DATA_OPERATOR]:
            return query

        # 其他用户只能访问自己提交的申请
        return query.filter(cls.requested_by == user_id)

    @classmethod
    def get_pending_requests(cls, session):
        """获取待审核的开户申请"""
        return session.query(cls).filter(
            cls.status == ChannelAccountRequestStatus.PENDING.value
        ).order_by(
            cls.created_at.asc()
        ).all()

    @classmethod
    def get_by_project(cls, session, project_id: int, user_id: UUID, user_role: UserRole):
        """获取指定项目的所有开户申请"""
        query = cls.get_user_accessible_query(session, user_id, user_role)
        return query.filter(
            cls.project_id == project_id
        ).order_by(
            cls.created_at.desc()
        ).all()
