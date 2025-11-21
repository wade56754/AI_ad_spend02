"""
日报模型 - 投手每日报告

RLS 策略：用户只能访问分配给自己的账户的日报
"""
from decimal import Decimal
from uuid import UUID
from datetime import date, datetime
from sqlalchemy import Column, BigInteger, String, Text, Integer, Numeric, Date, DateTime, Index, CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base, TimestampMixin
from backend.models.enums import DailyReportStatus, UserRole
from backend.models.mixins.serializable import SerializableMixin
from backend.models.mixins.rls_aware import RLSAwareMixin


class DailyReport(Base, TimestampMixin, RLSAwareMixin, SerializableMixin):
    """
    投手每日报告表

    字段：
    - id: 主键
    - ad_account_id: 广告账户ID（外键）
    - submitted_by: 提交人ID（外键）
    - reviewed_by: 审核人ID（外键）
    - report_date: 报告日期
    - status: 状态（draft/pending/approved/rejected）
    - fans_gained: 新增粉丝数
    - spend_amount: 消耗金额
    - notes: 备注
    - submitted_at: 提交时间
    - reviewed_at: 审核时间
    - created_at/updated_at: 时间戳（自动管理）
    """
    __tablename__ = 'daily_reports'

    # RLS 配置
    __rls_user_field__ = 'submitted_by'
    __rls_admin_roles__ = [UserRole.ADMIN, UserRole.DATA_OPERATOR]
    __rls_readonly_roles__ = [UserRole.FINANCE]

    # 序列化配置
    __json_include_relationships__ = ['ad_account', 'submitter', 'reviewer']

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="日报ID")

    # 外键
    ad_account_id = Column(
        BigInteger,
        ForeignKey('ad_accounts.id', ondelete='CASCADE'),
        nullable=False,
        comment="广告账户ID"
    )
    submitted_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="提交人ID"
    )
    reviewed_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="审核人ID"
    )

    # 业务字段
    report_date = Column(Date, nullable=False, comment="报告日期")
    status = Column(String(20), nullable=False, comment="状态")
    fans_gained = Column(Integer, nullable=True, comment="新增粉丝数")
    spend_amount = Column(Numeric(15, 2), nullable=True, comment="消耗金额")
    notes = Column(Text, nullable=True, comment="备注")

    # 时间字段
    submitted_at = Column(DateTime(timezone=True), nullable=True, comment="提交时间")
    reviewed_at = Column(DateTime(timezone=True), nullable=True, comment="审核时间")

    # 并发控制
    version = Column(Integer, nullable=False, server_default='1', comment="乐观锁版本号")

    # ========== 关系定义 ==========

    # 多对一：日报 -> 广告账户
    ad_account = relationship(
        "AdAccount",
        foreign_keys=[ad_account_id],
        lazy="joined",
        doc="所属广告账户"
    )

    # 多对一：日报 -> 提交人
    submitter = relationship(
        "User",
        foreign_keys=[submitted_by],
        lazy="selectin",
        doc="提交人（投手）"
    )

    # 多对一：日报 -> 审核人
    reviewer = relationship(
        "User",
        foreign_keys=[reviewed_by],
        lazy="selectin",
        doc="审核人（数据员）"
    )

    # 约束和索引
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'pending', 'approved', 'rejected')",
            name='chk_daily_reports_status'
        ),
        UniqueConstraint(
            'ad_account_id', 'report_date',
            name='daily_reports_ad_account_id_report_date_key'
        ),
        Index('idx_daily_reports_ad_account_id', 'ad_account_id'),
        Index('idx_daily_reports_report_date', 'report_date'),
        Index('idx_daily_reports_status', 'status'),
    )

    def __repr__(self):
        return f"<DailyReport(id={self.id}, account_id={self.ad_account_id}, date={self.report_date})>"

    # ========== 业务属性 ==========

    @property
    def status_enum(self) -> DailyReportStatus:
        """返回状态枚举对象"""
        return DailyReportStatus(self.status)

    @property
    def is_draft(self) -> bool:
        """是否是草稿"""
        return self.status == DailyReportStatus.DRAFT.value

    @property
    def is_pending(self) -> bool:
        """是否待审核"""
        return self.status == DailyReportStatus.PENDING.value

    @property
    def is_approved(self) -> bool:
        """是否已批准"""
        return self.status == DailyReportStatus.APPROVED.value

    @property
    def is_rejected(self) -> bool:
        """是否已拒绝"""
        return self.status == DailyReportStatus.REJECTED.value

    # ========== 状态流转方法 ==========

    def can_transition_to(self, new_status: DailyReportStatus) -> bool:
        """
        检查是否可以转换到新状态

        状态流转规则：
        - draft -> pending
        - pending -> approved, rejected
        - approved -> (终态)
        - rejected -> pending（重新提交）
        """
        current = DailyReportStatus(self.status)
        transitions = {
            DailyReportStatus.DRAFT: [DailyReportStatus.PENDING],
            DailyReportStatus.PENDING: [DailyReportStatus.APPROVED, DailyReportStatus.REJECTED],
            DailyReportStatus.APPROVED: [],
            DailyReportStatus.REJECTED: [DailyReportStatus.PENDING],
        }
        return new_status in transitions.get(current, [])

    def submit(self, submitter_id: UUID):
        """提交日报"""
        if not self.can_transition_to(DailyReportStatus.PENDING):
            raise ValueError(f"不允许从 {self.status} 状态提交日报")

        self.status = DailyReportStatus.PENDING.value
        self.submitted_by = submitter_id
        self.submitted_at = func.now()

    def approve(self, reviewer_id: UUID, notes: str = None):
        """批准日报"""
        if not self.can_transition_to(DailyReportStatus.APPROVED):
            raise ValueError(f"不允许从 {self.status} 状态批准日报")

        self.status = DailyReportStatus.APPROVED.value
        self.reviewed_by = reviewer_id
        self.reviewed_at = func.now()
        if notes:
            self.notes = notes

    def reject(self, reviewer_id: UUID, reason: str):
        """拒绝日报"""
        if not self.can_transition_to(DailyReportStatus.REJECTED):
            raise ValueError(f"不允许从 {self.status} 状态拒绝日报")

        self.status = DailyReportStatus.REJECTED.value
        self.reviewed_by = reviewer_id
        self.reviewed_at = func.now()
        self.notes = reason

    # ========== 权限判断方法 ==========

    def can_be_edited_by(self, user_id: UUID, user_role: UserRole) -> bool:
        """检查用户是否可以编辑此日报"""
        # 管理员和数据员可以编辑所有日报
        if user_role in [UserRole.ADMIN, UserRole.DATA_OPERATOR]:
            return True

        # 投手只能编辑自己提交的草稿或被拒绝的日报
        if user_role == UserRole.MEDIA_BUYER:
            if self.submitted_by != user_id:
                return False
            return self.status in [DailyReportStatus.DRAFT.value, DailyReportStatus.REJECTED.value]

        return False

    def can_be_reviewed_by(self, user_id: UUID, user_role: UserRole) -> bool:
        """检查用户是否可以审核此日报"""
        # 只有管理员和数据员可以审核
        if user_role not in [UserRole.ADMIN, UserRole.DATA_OPERATOR]:
            return False

        # 只有待审核的日报才能审核
        return self.status == DailyReportStatus.PENDING.value

    # ========== 查询作用域方法 ==========

    @classmethod
    def get_user_accessible_query(cls, session, user_id: UUID, user_role: UserRole):
        """获取用户可访问的日报查询（RLS 逻辑）"""
        query = session.query(cls)

        # 管理员和数据员可以访问所有日报
        if user_role in [UserRole.ADMIN, UserRole.DATA_OPERATOR]:
            return query

        # 投手只能访问自己提交的日报
        if user_role == UserRole.MEDIA_BUYER:
            return query.filter(cls.submitted_by == user_id)

        # 财务可以查看所有已批准的日报
        if user_role == UserRole.FINANCE:
            return query.filter(cls.status == DailyReportStatus.APPROVED.value)

        return query.filter(cls.submitted_by == user_id)

    @classmethod
    def get_pending_reports(cls, session, user_role: UserRole):
        """获取待审核的日报（数据员使用）"""
        if user_role not in [UserRole.ADMIN, UserRole.DATA_OPERATOR]:
            return []

        return session.query(cls).filter(
            cls.status == DailyReportStatus.PENDING.value
        ).order_by(
            cls.submitted_at.asc()
        ).all()

    @classmethod
    def get_by_account_and_date(cls, session, ad_account_id: int, report_date: date):
        """根据账户和日期获取日报"""
        return session.query(cls).filter(
            cls.ad_account_id == ad_account_id,
            cls.report_date == report_date
        ).first()

    @classmethod
    def get_date_range_reports(cls, session, user_id: UUID, user_role: UserRole,
                               start_date: date, end_date: date):
        """获取指定日期范围内的日报"""
        query = cls.get_user_accessible_query(session, user_id, user_role)
        return query.filter(
            cls.report_date >= start_date,
            cls.report_date <= end_date
        ).order_by(
            cls.report_date.desc()
        ).all()
