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
    投手每日报告表（粉数确认状态机）

    必须与 STATE_MACHINE.md v2.6 第8章保持严格一致。

    8 状态流程：
    raw_submitted → trend_pending → trend_ok/trend_flagged
    → trend_resolved → final_pending → final_confirmed → final_locked

    字段：
    - id: 主键
    - ad_account_id: 广告账户ID（外键）
    - submitted_by: 提交人ID（外键）
    - reviewed_by: 审核人ID（外键）
    - report_date: 报告日期
    - status: 状态（8状态机）
    - conversions_raw: 投手提交的原始粉数
    - conversions_final: 运营确认的最终粉数
    - raw_spend: 原始消耗
    - real_spend: 真实消耗
    - trend_flag: 趋势异常标记
    - trend_flag_reason: 异常原因
    - trend_resolution_note: 运营复核说明
    - final_locked_at: 锁定时间
    - unit_price: 单粉价格
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

    # 业务字段 - 基础信息
    report_date = Column(Date, nullable=False, comment="报告日期")
    status = Column(String(20), nullable=False, comment="状态（8状态机）")

    # 广告信息字段 (API_SOT.md v9.0 第 9.2 节)
    campaign_name = Column(String(200), nullable=True, comment="广告系列名称")
    ad_group_name = Column(String(200), nullable=True, comment="广告组名称")
    ad_creative_name = Column(String(200), nullable=True, comment="广告创意名称")

    # 指标字段
    impressions = Column(Integer, nullable=True, default=0, comment="展示次数/曝光量")
    clicks = Column(Integer, nullable=True, default=0, comment="点击次数")

    # 三数据流字段 (STATE_MACHINE.md v2.6 第 8 章)
    # raw 数据流 - 投手提交 (T+0)
    conversions_raw = Column(Integer, nullable=True, default=0, comment="原始粉数（raw数据流）")
    raw_spend = Column(Numeric(15, 2), nullable=True, default=0, comment="原始消耗（raw数据流）")
    # real 数据流 - 运营录入 (T+1)
    real_spend = Column(Numeric(15, 2), nullable=True, default=0, comment="真实消耗（real数据流）")
    fee = Column(Numeric(15, 2), nullable=True, default=0, comment="手续费")
    # final 数据流 - 运营确认
    conversions_final = Column(Integer, nullable=True, default=0, comment="最终粉数（final数据流）")

    # 计费字段
    unit_price = Column(Numeric(15, 2), nullable=True, comment="单粉价格（从项目继承）")

    # 趋势风控字段 (STATE_MACHINE.md v2.6 第 8.3 节)
    trend_flag = Column(String(20), nullable=True, default='normal', comment="趋势标记（normal/flagged/resolved）")
    trend_flag_reason = Column(Text, nullable=True, comment="趋势异常原因（如 TF-001）")
    trend_resolution_note = Column(Text, nullable=True, comment="运营复核说明")

    # 锁定时间
    final_locked_at = Column(DateTime(timezone=True), nullable=True, comment="计费锁定时间")

    # 兼容旧字段 (deprecated, 将在下个版本移除)
    # NOTE: 需要 Alembic migration 来添加新字段和迁移数据
    fans_gained = Column(Integer, nullable=True, comment="[DEPRECATED] 新增粉丝数，请使用 conversions_raw")
    spend_amount = Column(Numeric(15, 2), nullable=True, comment="[DEPRECATED] 消耗金额，请使用 raw_spend")

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

    # 约束和索引 - 必须与 STATE_MACHINE.md v2.6 第8章保持一致
    __table_args__ = (
        CheckConstraint(
            "status IN ('raw_submitted', 'trend_pending', 'trend_ok', 'trend_flagged', "
            "'trend_resolved', 'final_pending', 'final_confirmed', 'final_locked')",
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

    # ========== 业务属性（8状态机）==========

    @property
    def status_enum(self) -> DailyReportStatus:
        """返回状态枚举对象"""
        return DailyReportStatus(self.status)

    @property
    def is_raw_submitted(self) -> bool:
        """是否是原始提交状态"""
        return self.status == DailyReportStatus.RAW_SUBMITTED.value

    @property
    def is_trend_pending(self) -> bool:
        """是否等待趋势风控检查"""
        return self.status == DailyReportStatus.TREND_PENDING.value

    @property
    def is_trend_ok(self) -> bool:
        """趋势是否正常"""
        return self.status == DailyReportStatus.TREND_OK.value

    @property
    def is_trend_flagged(self) -> bool:
        """趋势是否异常"""
        return self.status == DailyReportStatus.TREND_FLAGGED.value

    @property
    def is_trend_resolved(self) -> bool:
        """趋势异常是否已解决"""
        return self.status == DailyReportStatus.TREND_RESOLVED.value

    @property
    def is_final_pending(self) -> bool:
        """是否等待最终粉数确认"""
        return self.status == DailyReportStatus.FINAL_PENDING.value

    @property
    def is_final_confirmed(self) -> bool:
        """最终粉数是否已确认"""
        return self.status == DailyReportStatus.FINAL_CONFIRMED.value

    @property
    def is_final_locked(self) -> bool:
        """是否已锁定（终态）"""
        return self.status == DailyReportStatus.FINAL_LOCKED.value

    # ========== 状态流转方法（8状态机）==========

    # 合法流转白名单 - 必须与 STATE_MACHINE.md v2.6 第14.5章保持一致
    STATE_TRANSITIONS = {
        DailyReportStatus.RAW_SUBMITTED: [DailyReportStatus.TREND_PENDING],
        DailyReportStatus.TREND_PENDING: [DailyReportStatus.TREND_OK, DailyReportStatus.TREND_FLAGGED],
        DailyReportStatus.TREND_OK: [DailyReportStatus.FINAL_PENDING],
        DailyReportStatus.TREND_FLAGGED: [DailyReportStatus.TREND_RESOLVED, DailyReportStatus.RAW_SUBMITTED],
        DailyReportStatus.TREND_RESOLVED: [DailyReportStatus.FINAL_PENDING],
        DailyReportStatus.FINAL_PENDING: [DailyReportStatus.FINAL_CONFIRMED],
        DailyReportStatus.FINAL_CONFIRMED: [DailyReportStatus.FINAL_LOCKED],
        DailyReportStatus.FINAL_LOCKED: [],  # 终态，仅可通过红冲修正
    }

    def can_transition_to(self, new_status: DailyReportStatus) -> bool:
        """
        检查是否可以转换到新状态

        8状态流转规则（STATE_MACHINE.md v2.6 第8章）：
        - raw_submitted -> trend_pending
        - trend_pending -> trend_ok, trend_flagged
        - trend_ok -> final_pending
        - trend_flagged -> trend_resolved, raw_submitted
        - trend_resolved -> final_pending
        - final_pending -> final_confirmed
        - final_confirmed -> final_locked
        - final_locked -> (终态，仅可红冲)
        """
        current = DailyReportStatus(self.status)
        return new_status in self.STATE_TRANSITIONS.get(current, [])

    def submit_raw(self, submitter_id: UUID, conversions_raw: int, raw_spend: Decimal):
        """投手提交原始粉数（T+0）"""
        self.status = DailyReportStatus.RAW_SUBMITTED.value
        self.submitted_by = submitter_id
        self.submitted_at = func.now()
        # conversions_raw 和 raw_spend 字段需要在模型中添加

    def trigger_trend_check(self):
        """触发趋势风控检查（系统自动）"""
        if not self.can_transition_to(DailyReportStatus.TREND_PENDING):
            raise ValueError(f"不允许从 {self.status} 状态触发趋势检查")
        self.status = DailyReportStatus.TREND_PENDING.value

    def mark_trend_ok(self):
        """标记趋势正常（系统自动）"""
        if not self.can_transition_to(DailyReportStatus.TREND_OK):
            raise ValueError(f"不允许从 {self.status} 状态标记趋势正常")
        self.status = DailyReportStatus.TREND_OK.value

    def mark_trend_flagged(self, reason: str):
        """标记趋势异常（系统自动）"""
        if not self.can_transition_to(DailyReportStatus.TREND_FLAGGED):
            raise ValueError(f"不允许从 {self.status} 状态标记趋势异常")
        self.status = DailyReportStatus.TREND_FLAGGED.value
        self.notes = reason  # trend_flag_reason 字段需要添加

    def resolve_trend(self, reviewer_id: UUID, resolution_note: str):
        """运营确认趋势异常已解决"""
        if not self.can_transition_to(DailyReportStatus.TREND_RESOLVED):
            raise ValueError(f"不允许从 {self.status} 状态解决趋势异常")
        self.status = DailyReportStatus.TREND_RESOLVED.value
        self.reviewed_by = reviewer_id
        self.notes = resolution_note  # trend_resolution_note 字段需要添加

    def enter_final_pending(self, reviewer_id: UUID):
        """运营录入real_spend后进入等待最终确认"""
        if not self.can_transition_to(DailyReportStatus.FINAL_PENDING):
            raise ValueError(f"不允许从 {self.status} 状态进入最终确认等待")
        self.status = DailyReportStatus.FINAL_PENDING.value
        self.reviewed_by = reviewer_id

    def confirm_final(self, reviewer_id: UUID):
        """运营确认最终粉数"""
        if not self.can_transition_to(DailyReportStatus.FINAL_CONFIRMED):
            raise ValueError(f"不允许从 {self.status} 状态确认最终粉数")
        self.status = DailyReportStatus.FINAL_CONFIRMED.value
        self.reviewed_by = reviewer_id
        self.reviewed_at = func.now()

    def lock_final(self):
        """系统计费锁定（终态）"""
        if not self.can_transition_to(DailyReportStatus.FINAL_LOCKED):
            raise ValueError(f"不允许从 {self.status} 状态锁定")
        self.status = DailyReportStatus.FINAL_LOCKED.value
        # final_locked_at 字段需要添加

    # ========== 权限判断方法（8状态机）==========

    def can_be_edited_by(self, user_id: UUID, user_role: UserRole) -> bool:
        """检查用户是否可以编辑此日报"""
        # 管理员和数据员可以编辑所有未锁定的日报
        if user_role in [UserRole.ADMIN, UserRole.DATA_OPERATOR]:
            return not self.is_final_locked

        # 投手只能编辑自己的原始提交状态或被退回的日报
        if user_role == UserRole.MEDIA_BUYER:
            if self.submitted_by != user_id:
                return False
            return self.status == DailyReportStatus.RAW_SUBMITTED.value

        return False

    def can_be_reviewed_by(self, user_id: UUID, user_role: UserRole) -> bool:
        """检查用户是否可以审核此日报（趋势复核或最终确认）"""
        # 只有管理员和数据员可以审核
        if user_role not in [UserRole.ADMIN, UserRole.DATA_OPERATOR]:
            return False

        # 可审核状态：trend_flagged（趋势复核）、final_pending（最终确认）
        reviewable_statuses = [
            DailyReportStatus.TREND_FLAGGED.value,
            DailyReportStatus.FINAL_PENDING.value,
        ]
        return self.status in reviewable_statuses

    # ========== 查询作用域方法（8状态机）==========

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

        # 财务可以查看所有已锁定的日报（用于计费）
        if user_role == UserRole.FINANCE:
            return query.filter(cls.status == DailyReportStatus.FINAL_LOCKED.value)

        return query.filter(cls.submitted_by == user_id)

    @classmethod
    def get_pending_trend_review(cls, session, user_role: UserRole):
        """获取待趋势复核的日报（运营使用）"""
        if user_role not in [UserRole.ADMIN, UserRole.DATA_OPERATOR]:
            return []

        return session.query(cls).filter(
            cls.status == DailyReportStatus.TREND_FLAGGED.value
        ).order_by(
            cls.submitted_at.asc()
        ).all()

    @classmethod
    def get_pending_final_confirm(cls, session, user_role: UserRole):
        """获取待最终确认的日报（运营使用）"""
        if user_role not in [UserRole.ADMIN, UserRole.DATA_OPERATOR]:
            return []

        return session.query(cls).filter(
            cls.status == DailyReportStatus.FINAL_PENDING.value
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
