"""
日报模型 - 投手每日报告

对齐 DATA_SCHEMA.md v5.2 和 init_schema.sql §6.1
字段来源: init_schema.sql 第 408-447 行
状态机: STATE_MACHINE.md v2.6 第 8 章 (8 状态机)

v2.0 更新 (2024-12):
- 新增 region 地区字段
- 新增 platform 平台字段 (FB/Google/TikTok)
- 新增 result_count 成效数
- 新增 follows_count 进粉数
- 新增计算属性: cost_per_follow, cost_per_result
"""
from decimal import Decimal
from uuid import UUID
from datetime import date, datetime
from sqlalchemy import Column, BigInteger, String, Text, Integer, Numeric, Date, DateTime, Index, CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base, TimestampMixin
from backend.models.enums import DailyReportStatus, UserRole
from backend.models.mixins.serializable import SerializableMixin
from backend.models.mixins.rls_aware import RLSAwareMixin


# 平台枚举
PLATFORM_CHOICES = ['FB', 'Google', 'TikTok', 'Other']

# 地区列表 (基于实际业务数据)
REGION_CHOICES = [
    'Turkey', 'India', 'Italy', 'Germany', 'Brazil', 'UK', 'Korea', 'France',
    'Malaysia', 'Japan', 'Austria', 'Spain', 'Nigeria', 'Singapore', 'Belgium',
    'Sweden', 'Canada', 'Indonesia', 'USA', 'Ireland', 'Other'
]


class DailyReport(Base, TimestampMixin, RLSAwareMixin, SerializableMixin):
    """
    投手每日报告表（粉数确认状态机）

    对齐 init_schema.sql §6.1 daily_reports 表定义
    必须与 STATE_MACHINE.md v2.6 第 8 章保持严格一致

    8 状态流程：
    raw_submitted → trend_pending → trend_ok/trend_flagged
    → trend_resolved → final_pending → final_confirmed → final_locked

    字段（与数据库完全对齐）：
    - id: BIGSERIAL 主键
    - report_date: DATE 报告日期
    - ad_account_id: BIGINT 广告账户外键
    - campaign_name/ad_group_name/ad_creative_name: 广告信息
    - impressions/clicks/conversions/new_follows: 基础指标
    - conversions_raw/conversions_final: 粉数（raw/final 数据流）
    - raw_spend/real_spend/unit_price: 消耗数据
    - cpc/cpa/ctr/roi: 效果指标
    - status: 8 状态机
    - trend_flag/trend_flag_reason/trend_resolution_note: 趋势风控
    - final_locked_at: 锁定时间
    - notes/attachments: 备注和附件
    - submitted_by/audit_user_id: 提交人/审核人
    - submitted_at/approved_at: 时间戳
    - created_by/updated_by: 审计字段
    - created_at/updated_at: 时间戳
    """
    __tablename__ = 'daily_reports'

    # RLS 配置
    __rls_user_field__ = 'submitted_by'
    __rls_admin_roles__ = [UserRole.ADMIN, UserRole.DATA_OPERATOR]
    __rls_readonly_roles__ = [UserRole.FINANCE]

    # 序列化配置
    __json_include_relationships__ = ['ad_account', 'submitter', 'auditor']

    # 主键 - BIGSERIAL
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="日报ID")

    # 报告日期
    report_date = Column(Date, nullable=False, comment="报告日期")

    # 外键
    ad_account_id = Column(
        BigInteger,
        ForeignKey('ad_accounts.id', ondelete='RESTRICT'),
        nullable=False,
        comment="广告账户ID"
    )

    # 广告信息字段 - 对齐 init_schema.sql
    campaign_name = Column(String(200), nullable=True, comment="广告系列名称")
    ad_group_name = Column(String(200), nullable=True, comment="广告组名称")
    ad_creative_name = Column(String(200), nullable=True, comment="广告创意名称")

    # ========== 新增字段 v2.0 ==========
    # 地区 - 投放目标地区
    region = Column(String(50), nullable=True, comment="投放地区（Turkey/India/Brazil等）")

    # 平台 - 广告平台（直接字段，便于查询）
    platform = Column(String(20), nullable=True, comment="广告平台（FB/Google/TikTok）")

    # 成效数 - 广告成效数量
    result_count = Column(Integer, nullable=False, default=0, server_default='0', comment="成效数（result）")

    # 进粉数 - 实际进粉数量
    follows_count = Column(Integer, nullable=False, default=0, server_default='0', comment="进粉数（people）")

    # 货币类型
    currency = Column(String(10), nullable=False, default='USD', server_default='USD', comment="货币类型（USD/CNY）")

    # ========== 原有基础指标 ==========
    impressions = Column(Integer, nullable=False, default=0, server_default='0', comment="展示次数/曝光量")
    clicks = Column(Integer, nullable=False, default=0, server_default='0', comment="点击次数")
    conversions = Column(Integer, nullable=False, default=0, server_default='0', comment="转化数")
    new_follows = Column(Integer, nullable=False, default=0, server_default='0', comment="新增关注数（兼容旧字段）")

    # 三数据流字段 - 对齐 init_schema.sql 和 STATE_MACHINE.md v2.6 第 8 章
    # raw 数据流 - 投手提交 (T+0)
    conversions_raw = Column(Integer, nullable=False, default=0, server_default='0', comment="原始粉数（raw数据流）")
    # final 数据流 - 运营确认
    conversions_final = Column(Integer, nullable=False, default=0, server_default='0', comment="最终粉数（final数据流）")

    # 消耗字段 - 对齐 init_schema.sql
    raw_spend = Column(Numeric(15, 2), nullable=False, default=Decimal('0.00'), server_default='0.00', comment="原始消耗（raw数据流）")
    real_spend = Column(Numeric(15, 2), nullable=False, default=Decimal('0.00'), server_default='0.00', comment="真实消耗（real数据流）")
    unit_price = Column(Numeric(15, 2), nullable=False, default=Decimal('0.00'), server_default='0.00', comment="单粉价格")

    # 效果指标 - 对齐 init_schema.sql
    cpc = Column(Numeric(12, 4), nullable=True, comment="单次点击成本")
    cpa = Column(Numeric(12, 4), nullable=True, comment="单次转化成本")
    ctr = Column(Numeric(12, 4), nullable=True, comment="点击率")
    roi = Column(Numeric(12, 4), nullable=True, comment="投资回报率")

    # 状态 - 8 状态机
    status = Column(
        String(20),
        nullable=False,
        default='raw_submitted',
        server_default='raw_submitted',
        comment="状态（8状态机）"
    )

    # 趋势风控字段 - 对齐 init_schema.sql 和 STATE_MACHINE.md v2.6 第 8.3 节
    trend_flag = Column(
        String(20),
        nullable=False,
        default='normal',
        server_default='normal',
        comment="趋势标记（normal/flagged/resolved）"
    )
    trend_flag_reason = Column(Text, nullable=True, comment="趋势异常原因（如 TF-001）")
    trend_resolution_note = Column(Text, nullable=True, comment="运营复核说明")

    # 锁定时间
    final_locked_at = Column(DateTime(timezone=True), nullable=True, comment="计费锁定时间")

    # 备注和附件 - 对齐 init_schema.sql
    notes = Column(Text, nullable=True, comment="备注")
    attachments = Column(JSONB, nullable=True, comment="附件")

    # 用户关联 - 对齐 init_schema.sql
    submitted_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="提交人ID"
    )
    audit_user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="审核人ID"
    )

    # 审计字段 - 对齐 init_schema.sql
    created_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="创建者ID"
    )
    updated_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="更新者ID"
    )

    # 时间字段 - 对齐 init_schema.sql
    submitted_at = Column(DateTime(timezone=True), nullable=True, comment="提交时间")
    approved_at = Column(DateTime(timezone=True), nullable=True, comment="审批时间")

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
    auditor = relationship(
        "User",
        foreign_keys=[audit_user_id],
        lazy="selectin",
        doc="审核人（数据员）"
    )

    # 约束和索引 - 对齐 init_schema.sql
    __table_args__ = (
        CheckConstraint(
            "status IN ('raw_submitted', 'trend_pending', 'trend_ok', 'trend_flagged', "
            "'trend_resolved', 'final_pending', 'final_confirmed', 'final_locked')",
            name='chk_daily_reports_status'
        ),
        CheckConstraint(
            "trend_flag IN ('normal', 'flagged', 'resolved')",
            name='chk_daily_reports_trend_flag'
        ),
        UniqueConstraint(
            'report_date', 'ad_account_id',
            name='uq_daily_reports_date_account'
        ),
        Index('idx_daily_reports_date', 'report_date'),
        Index('idx_daily_reports_account', 'ad_account_id'),
        Index('idx_daily_reports_status', 'status'),
        Index('idx_daily_reports_created_by', 'created_by'),
        Index('idx_daily_reports_date_status', 'report_date', 'status'),
    )

    def __repr__(self):
        return f"<DailyReport(id={self.id}, account_id={self.ad_account_id}, date={self.report_date})>"

    # ========== 计算属性 (v2.0) ==========

    @property
    def cost_per_follow(self) -> Decimal:
        """
        单粉成本 = 广告消耗 / 进粉数

        如果进粉数为0，返回0
        """
        if self.follows_count and self.follows_count > 0:
            return Decimal(str(self.raw_spend)) / Decimal(self.follows_count)
        return Decimal('0.00')

    @property
    def cost_per_result(self) -> Decimal:
        """
        单次成效费用 = 广告消耗 / 成效数

        如果成效数为0，返回0
        """
        if self.result_count and self.result_count > 0:
            return Decimal(str(self.raw_spend)) / Decimal(self.result_count)
        return Decimal('0.00')

    # ========== 向后兼容属性 ==========

    @property
    def reviewed_by(self):
        """向后兼容：返回 audit_user_id"""
        return self.audit_user_id

    @reviewed_by.setter
    def reviewed_by(self, value):
        """向后兼容：设置 audit_user_id"""
        self.audit_user_id = value

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
        self.conversions_raw = conversions_raw
        self.raw_spend = raw_spend

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
        self.trend_flag = 'flagged'
        self.trend_flag_reason = reason

    def resolve_trend(self, reviewer_id: UUID, resolution_note: str):
        """运营确认趋势异常已解决"""
        if not self.can_transition_to(DailyReportStatus.TREND_RESOLVED):
            raise ValueError(f"不允许从 {self.status} 状态解决趋势异常")
        self.status = DailyReportStatus.TREND_RESOLVED.value
        self.audit_user_id = reviewer_id
        self.trend_flag = 'resolved'
        self.trend_resolution_note = resolution_note

    def enter_final_pending(self, reviewer_id: UUID):
        """运营录入real_spend后进入等待最终确认"""
        if not self.can_transition_to(DailyReportStatus.FINAL_PENDING):
            raise ValueError(f"不允许从 {self.status} 状态进入最终确认等待")
        self.status = DailyReportStatus.FINAL_PENDING.value
        self.audit_user_id = reviewer_id

    def confirm_final(self, reviewer_id: UUID):
        """运营确认最终粉数"""
        if not self.can_transition_to(DailyReportStatus.FINAL_CONFIRMED):
            raise ValueError(f"不允许从 {self.status} 状态确认最终粉数")
        self.status = DailyReportStatus.FINAL_CONFIRMED.value
        self.audit_user_id = reviewer_id
        self.approved_at = func.now()

    def lock_final(self):
        """系统计费锁定（终态）"""
        if not self.can_transition_to(DailyReportStatus.FINAL_LOCKED):
            raise ValueError(f"不允许从 {self.status} 状态锁定")
        self.status = DailyReportStatus.FINAL_LOCKED.value
        self.final_locked_at = func.now()

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
