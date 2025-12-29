"""
周报模型 - 项目周度简报

对齐 B3-weekly-brief.md §2.2
SoT Reference: MASTER.md v4.4 §6.2 页面 6

状态机: draft → submitted (终态)
Phase 1 约束: 周报可选提交，不强制
"""
from decimal import Decimal
from uuid import UUID
from datetime import date, datetime
from sqlalchemy import (
    Column, BigInteger, String, Text, Integer, Numeric, Date, DateTime,
    Index, CheckConstraint, ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base, TimestampMixin
from backend.models.enums import WeeklyBriefStatus, UserRole


class WeeklyBrief(Base, TimestampMixin):
    """
    周度简报表

    对齐 B3-weekly-brief.md §2.2
    每项目每周只能有一份周报 (UNIQUE project_id + week_start)

    字段说明:
    - id: BIGSERIAL 主键
    - project_id: 关联项目
    - week_start: 周开始日期 (必须是周一)
    - week_end: 周结束日期 (周日)
    - submitter_id: 提交人 UUID
    - status: draft/submitted
    - weekly_spend: 周消耗 (自动汇总)
    - weekly_conversions: 周进粉 (自动汇总)
    - weekly_cpl: 周 CPL (计算)
    - achievements: 本周成果
    - issues: 遇到问题
    - solutions: 解决方案
    - next_week_plan: 下周计划
    - submitted_at: 提交时间
    """
    __tablename__ = 'weekly_briefs'

    # 主键 - BIGSERIAL
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="周报ID")

    # 外键 - 项目
    project_id = Column(
        BigInteger,
        ForeignKey('projects.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="项目ID"
    )

    # 周期字段
    week_start = Column(Date, nullable=False, comment="周开始日期（周一）")
    week_end = Column(Date, nullable=False, comment="周结束日期（周日）")

    # 提交人
    submitter_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="提交人ID"
    )

    # 状态
    status = Column(
        String(20),
        nullable=False,
        default='draft',
        server_default='draft',
        comment="状态（draft/submitted）"
    )

    # 汇总数据 (自动计算)
    weekly_spend = Column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal('0.00'),
        server_default='0.00',
        comment="周消耗"
    )
    weekly_conversions = Column(
        Integer,
        nullable=False,
        default=0,
        server_default='0',
        comment="周进粉"
    )
    weekly_cpl = Column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal('0.00'),
        server_default='0.00',
        comment="周CPL"
    )

    # 周报内容
    achievements = Column(Text, nullable=True, comment="本周成果")
    issues = Column(Text, nullable=True, comment="遇到问题")
    solutions = Column(Text, nullable=True, comment="解决方案")
    next_week_plan = Column(Text, nullable=True, comment="下周计划")

    # 提交时间
    submitted_at = Column(DateTime(timezone=True), nullable=True, comment="提交时间")

    # ========== 关系定义 ==========

    # 多对一：周报 -> 项目
    project = relationship(
        "Project",
        foreign_keys=[project_id],
        lazy="joined",
        doc="所属项目"
    )

    # 多对一：周报 -> 提交人
    submitter = relationship(
        "User",
        foreign_keys=[submitter_id],
        lazy="selectin",
        doc="提交人"
    )

    # 约束和索引
    __table_args__ = (
        # 每项目每周只能有一份周报
        UniqueConstraint(
            'project_id', 'week_start',
            name='uq_weekly_briefs_project_week'
        ),
        # 状态约束
        CheckConstraint(
            "status IN ('draft', 'submitted')",
            name='chk_weekly_briefs_status'
        ),
        # 周期合法性
        CheckConstraint(
            "week_end >= week_start",
            name='chk_weekly_briefs_week_range'
        ),
        # 索引
        Index('idx_weekly_briefs_project', 'project_id'),
        Index('idx_weekly_briefs_week', 'week_start'),
        Index('idx_weekly_briefs_submitter', 'submitter_id'),
        Index('idx_weekly_briefs_status', 'status'),
        Index('idx_weekly_briefs_project_week', 'project_id', 'week_start'),
    )

    def __repr__(self):
        return f"<WeeklyBrief(id={self.id}, project_id={self.project_id}, week={self.week_start})>"

    # ========== 状态属性 ==========

    @property
    def status_enum(self) -> WeeklyBriefStatus:
        """返回状态枚举对象"""
        return WeeklyBriefStatus(self.status)

    @property
    def is_draft(self) -> bool:
        """是否是草稿状态"""
        return self.status == WeeklyBriefStatus.DRAFT.value

    @property
    def is_submitted(self) -> bool:
        """是否已提交"""
        return self.status == WeeklyBriefStatus.SUBMITTED.value

    @property
    def can_edit(self) -> bool:
        """是否可编辑（仅草稿可编辑）"""
        return self.is_draft

    # ========== 状态流转方法 ==========

    def can_transition_to(self, new_status: WeeklyBriefStatus) -> bool:
        """检查是否可以转换到新状态"""
        transitions = {
            WeeklyBriefStatus.DRAFT: [WeeklyBriefStatus.SUBMITTED],
            WeeklyBriefStatus.SUBMITTED: [],  # 终态
        }
        current = WeeklyBriefStatus(self.status)
        return new_status in transitions.get(current, [])

    def submit(self, submitter_id: UUID):
        """
        提交周报

        业务规则 (B3-weekly-brief.md §7.2):
        - Phase 1: 无强制必填项
        - Phase 2: issues + next_week_plan 必填
        """
        if not self.can_transition_to(WeeklyBriefStatus.SUBMITTED):
            raise ValueError(f"不允许从 {self.status} 状态提交周报")

        self.status = WeeklyBriefStatus.SUBMITTED.value
        self.submitter_id = submitter_id
        self.submitted_at = func.now()

    # ========== 计算方法 ==========

    def calculate_cpl(self) -> Decimal:
        """计算周 CPL"""
        if self.weekly_conversions and self.weekly_conversions > 0:
            return Decimal(str(self.weekly_spend)) / Decimal(self.weekly_conversions)
        return Decimal('0.00')

    def update_summary(self, spend: Decimal, conversions: int):
        """更新汇总数据"""
        self.weekly_spend = spend
        self.weekly_conversions = conversions
        self.weekly_cpl = self.calculate_cpl()

    # ========== 权限判断方法 ==========

    def can_be_edited_by(self, user_id: UUID, user_role: UserRole) -> bool:
        """检查用户是否可以编辑此周报"""
        # 管理员可以编辑所有未提交的周报
        if user_role == UserRole.ADMIN:
            return self.is_draft

        # 项目负责人只能编辑自己项目的草稿
        if user_role == UserRole.PROJECT_OWNER:
            # 需要检查用户是否是该项目的负责人 (在 service 层判断)
            return self.is_draft

        return False

    def can_be_submitted_by(self, user_id: UUID, user_role: UserRole) -> bool:
        """检查用户是否可以提交此周报"""
        if not self.is_draft:
            return False

        # 管理员可以提交所有周报
        if user_role == UserRole.ADMIN:
            return True

        # 项目负责人可以提交自己项目的周报
        if user_role == UserRole.PROJECT_OWNER:
            return True

        return False
