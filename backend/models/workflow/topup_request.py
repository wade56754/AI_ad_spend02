"""
充值申请模型 - 广告账户充值流程

RLS 策略：用户只能访问自己提交或被分配的充值申请
"""
from decimal import Decimal
from uuid import UUID
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, Numeric, DateTime, Index, CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base, TimestampMixin
from backend.models.enums import TopupRequestStatus, UserRole
from backend.models.mixins.serializable import SerializableMixin
from backend.models.mixins.rls_aware import RLSAwareMixin


class TopupRequest(Base, TimestampMixin, RLSAwareMixin, SerializableMixin):
    """
    充值申请表

    字段：
    - id: 主键
    - ad_account_id: 广告账户ID（外键）
    - requested_by: 申请人ID（外键）
    - reviewed_by: 审核人ID（外键）
    - approved_by: 批准人ID（外键）
    - amount: 充值金额
    - status: 状态（draft/pending_review/finance_approve/paid/completed/rejected/cancelled）
    - request_notes: 申请备注
    - reject_reason: 拒绝原因
    - requested_at: 申请时间
    - reviewed_at: 审核时间
    - approved_at: 批准时间
    - paid_at: 打款时间
    - completed_at: 完成时间
    - created_at/updated_at: 时间戳（自动管理）
    """
    __tablename__ = 'topup_requests'

    # RLS 配置
    __rls_user_field__ = 'requested_by'
    __rls_admin_roles__ = [UserRole.ADMIN, UserRole.DATA_MANAGER, UserRole.FINANCE]
    __rls_readonly_roles__ = []

    # 序列化配置
    __json_include_relationships__ = ['ad_account', 'requester', 'reviewer', 'approver', 'transactions', 'approval_logs']

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="充值申请ID")

    # 外键
    ad_account_id = Column(
        BigInteger,
        ForeignKey('ad_accounts.id', ondelete='CASCADE'),
        nullable=False,
        comment="广告账户ID"
    )
    requested_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="申请人ID"
    )
    reviewed_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="审核人ID（数据员）"
    )
    approved_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="批准人ID（财务）"
    )

    # 业务字段
    amount = Column(Numeric(15, 2), nullable=False, comment="充值金额")
    status = Column(String(20), nullable=False, comment="状态")
    request_notes = Column(Text, nullable=True, comment="申请备注")
    reject_reason = Column(Text, nullable=True, comment="拒绝原因")

    # 时间字段
    requested_at = Column(DateTime(timezone=True), nullable=True, comment="申请时间")
    reviewed_at = Column(DateTime(timezone=True), nullable=True, comment="审核时间")
    approved_at = Column(DateTime(timezone=True), nullable=True, comment="批准时间")
    paid_at = Column(DateTime(timezone=True), nullable=True, comment="打款时间")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="完成时间")

    # ========== 关系定义 ==========

    # 多对一：充值申请 -> 广告账户
    ad_account = relationship(
        "AdAccount",
        foreign_keys=[ad_account_id],
        lazy="joined",
        doc="所属广告账户"
    )

    # 多对一：充值申请 -> 申请人
    requester = relationship(
        "User",
        foreign_keys=[requested_by],
        lazy="selectin",
        doc="申请人（投手）"
    )

    # 多对一：充值申请 -> 审核人
    reviewer = relationship(
        "User",
        foreign_keys=[reviewed_by],
        lazy="selectin",
        doc="审核人（数据员）"
    )

    # 多对一：充值申请 -> 批准人
    approver = relationship(
        "User",
        foreign_keys=[approved_by],
        lazy="selectin",
        doc="批准人（财务）"
    )

    # 一对多：充值申请 -> 交易记录（来自 topup.py 的 TopupTransaction）
    # 注意：TopupTransaction 定义在 backend.models.topup 中
    transactions = relationship(
        "TopupTransaction",
        back_populates="request",
        cascade="all, delete-orphan",
        lazy="dynamic",  # 使用dynamic避免测试时自动加载不存在的表
        doc="相关的交易记录"
    )

    # 一对多：充值申请 -> 审批日志（来自 topup.py 的 TopupApprovalLog）
    # 注意：TopupApprovalLog 定义在 backend.models.topup 中
    approval_logs = relationship(
        "TopupApprovalLog",
        back_populates="request",
        cascade="all, delete-orphan",
        lazy="dynamic",  # 使用dynamic避免测试时自动加载不存在的表
        doc="审批日志记录"
    )

    # 约束和索引
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'pending_review', 'finance_approve', 'paid', 'completed', 'rejected', 'cancelled')",
            name='topup_requests_status_check'
        ),
        Index('idx_topup_requests_ad_account_id', 'ad_account_id'),
        Index('idx_topup_requests_status', 'status'),
        Index('idx_topup_requests_requested_by', 'requested_by'),
    )

    def __repr__(self):
        return f"<TopupRequest(id={self.id}, account_id={self.ad_account_id}, amount={self.amount}, status='{self.status}')>"

    # ========== 业务属性 ==========

    @property
    def status_enum(self) -> TopupRequestStatus:
        """返回状态枚举对象"""
        return TopupRequestStatus(self.status)

    @property
    def is_pending(self) -> bool:
        """是否待处理"""
        return self.status in [
            TopupRequestStatus.PENDING_REVIEW.value,
            TopupRequestStatus.FINANCE_APPROVE.value
        ]

    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status == TopupRequestStatus.COMPLETED.value

    @property
    def is_rejected(self) -> bool:
        """是否已拒绝"""
        return self.status == TopupRequestStatus.REJECTED.value

    @property
    def is_cancelled(self) -> bool:
        """是否已取消"""
        return self.status == TopupRequestStatus.CANCELLED.value

    # ========== 状态流转方法 ==========

    def can_transition_to(self, new_status: TopupRequestStatus) -> bool:
        """
        检查是否可以转换到新状态

        状态流转规则：
        - draft -> pending_review, cancelled
        - pending_review -> finance_approve, rejected, cancelled
        - finance_approve -> paid, rejected
        - paid -> completed
        - completed -> (终态)
        - rejected -> (终态)
        - cancelled -> (终态)
        """
        current = TopupRequestStatus(self.status)
        transitions = {
            TopupRequestStatus.DRAFT: [TopupRequestStatus.PENDING_REVIEW, TopupRequestStatus.CANCELLED],
            TopupRequestStatus.PENDING_REVIEW: [
                TopupRequestStatus.FINANCE_APPROVE,
                TopupRequestStatus.REJECTED,
                TopupRequestStatus.CANCELLED
            ],
            TopupRequestStatus.FINANCE_APPROVE: [TopupRequestStatus.PAID, TopupRequestStatus.REJECTED],
            TopupRequestStatus.PAID: [TopupRequestStatus.COMPLETED],
            TopupRequestStatus.COMPLETED: [],
            TopupRequestStatus.REJECTED: [],
            TopupRequestStatus.CANCELLED: [],
        }
        return new_status in transitions.get(current, [])

    def submit(self, requester_id: UUID):
        """提交充值申请"""
        if not self.can_transition_to(TopupRequestStatus.PENDING_REVIEW):
            raise ValueError(f"不允许从 {self.status} 状态提交申请")

        self.status = TopupRequestStatus.PENDING_REVIEW.value
        self.requested_by = requester_id
        self.requested_at = func.now()

    def review_approve(self, reviewer_id: UUID):
        """数据员审核通过"""
        if not self.can_transition_to(TopupRequestStatus.FINANCE_APPROVE):
            raise ValueError(f"不允许从 {self.status} 状态审核通过")

        self.status = TopupRequestStatus.FINANCE_APPROVE.value
        self.reviewed_by = reviewer_id
        self.reviewed_at = func.now()

    def finance_approve(self, approver_id: UUID):
        """财务批准打款"""
        if not self.can_transition_to(TopupRequestStatus.PAID):
            raise ValueError(f"不允许从 {self.status} 状态批准打款")

        self.status = TopupRequestStatus.PAID.value
        self.approved_by = approver_id
        self.approved_at = func.now()
        self.paid_at = func.now()

    def complete(self):
        """标记为已完成"""
        if not self.can_transition_to(TopupRequestStatus.COMPLETED):
            raise ValueError(f"不允许从 {self.status} 状态标记完成")

        self.status = TopupRequestStatus.COMPLETED.value
        self.completed_at = func.now()

    def reject(self, rejector_id: UUID, reason: str, is_reviewer: bool = True):
        """拒绝充值申请"""
        if not self.can_transition_to(TopupRequestStatus.REJECTED):
            raise ValueError(f"不允许从 {self.status} 状态拒绝申请")

        self.status = TopupRequestStatus.REJECTED.value
        self.reject_reason = reason

        if is_reviewer:
            self.reviewed_by = rejector_id
            self.reviewed_at = func.now()
        else:
            self.approved_by = rejector_id
            self.approved_at = func.now()

    def cancel(self, requester_id: UUID):
        """取消充值申请"""
        if not self.can_transition_to(TopupRequestStatus.CANCELLED):
            raise ValueError(f"不允许从 {self.status} 状态取消申请")

        if self.requested_by != requester_id:
            raise ValueError("只有申请人本人可以取消申请")

        self.status = TopupRequestStatus.CANCELLED.value

    # ========== 权限判断方法 ==========

    def can_be_edited_by(self, user_id: UUID, user_role: UserRole) -> bool:
        """检查用户是否可以编辑此充值申请"""
        # 管理员可以编辑所有申请
        if user_role == UserRole.ADMIN:
            return True

        # 投手只能编辑自己提交的草稿
        if user_role == UserRole.MEDIA_BUYER:
            if self.requested_by != user_id:
                return False
            return self.status == TopupRequestStatus.DRAFT.value

        return False

    def can_be_reviewed_by(self, user_id: UUID, user_role: UserRole) -> bool:
        """检查用户是否可以审核此充值申请（数据员）"""
        # 只有管理员和数据员可以审核
        if user_role not in [UserRole.ADMIN, UserRole.DATA_MANAGER]:
            return False

        # 只有待审核的申请才能审核
        return self.status == TopupRequestStatus.PENDING_REVIEW.value

    def can_be_approved_by(self, user_id: UUID, user_role: UserRole) -> bool:
        """检查用户是否可以批准此充值申请（财务）"""
        # 只有管理员和财务可以批准
        if user_role not in [UserRole.ADMIN, UserRole.FINANCE]:
            return False

        # 只有通过数据员审核的申请才能批准
        return self.status == TopupRequestStatus.FINANCE_APPROVE.value

    # ========== 查询作用域方法 ==========

    @classmethod
    def get_user_accessible_query(cls, session, user_id: UUID, user_role: UserRole):
        """获取用户可访问的充值申请查询（RLS 逻辑）"""
        query = session.query(cls)

        # 管理员可以访问所有申请
        if user_role == UserRole.ADMIN:
            return query

        # 数据员可以访问所有申请
        if user_role == UserRole.DATA_MANAGER:
            return query

        # 财务可以访问所有申请
        if user_role == UserRole.FINANCE:
            return query

        # 投手只能访问自己提交的申请
        if user_role == UserRole.MEDIA_BUYER:
            return query.filter(cls.requested_by == user_id)

        return query.filter(cls.requested_by == user_id)

    @classmethod
    def get_pending_review_requests(cls, session):
        """获取待数据员审核的充值申请"""
        return session.query(cls).filter(
            cls.status == TopupRequestStatus.PENDING_REVIEW.value
        ).order_by(
            cls.requested_at.asc()
        ).all()

    @classmethod
    def get_pending_finance_requests(cls, session):
        """获取待财务批准的充值申请"""
        return session.query(cls).filter(
            cls.status == TopupRequestStatus.FINANCE_APPROVE.value
        ).order_by(
            cls.reviewed_at.asc()
        ).all()

    @classmethod
    def get_by_account(cls, session, ad_account_id: int, user_id: UUID, user_role: UserRole):
        """获取指定账户的所有充值申请"""
        query = cls.get_user_accessible_query(session, user_id, user_role)
        return query.filter(
            cls.ad_account_id == ad_account_id
        ).order_by(
            cls.created_at.desc()
        ).all()
