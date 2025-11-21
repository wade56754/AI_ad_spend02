"""
渠道相关模型 - 广告渠道、评审、表现统计

包含：
- Channel: 广告渠道主表（Facebook, Google Ads等）
- ChannelReview: 渠道评审记录
- ChannelPerformance: 渠道表现统计
"""
from decimal import Decimal
from uuid import UUID
from datetime import date
from sqlalchemy import Column, BigInteger, String, Text, Integer, Numeric, Date, DateTime, Index, CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base, TimestampMixin
from backend.models.enums import ChannelStatus, ChannelReviewStatus, UserRole
from backend.models.mixins.serializable import SerializableMixin


class Channel(Base, TimestampMixin, SerializableMixin):
    """
    广告渠道表（如 Facebook, Google Ads 等）

    字段：
    - id: 主键
    - name: 渠道名称
    - channel_code: 渠道代码（唯一）
    - status: 渠道状态（active/inactive）
    - country: 国家/地区
    - notes: 备注
    - created_at/updated_at: 时间戳（自动管理）
    """
    __tablename__ = 'channels'

    # 序列化配置
    __json_include_relationships__ = ['ad_accounts', 'reviews']

    # 主键：UUID（对齐 DATA_SCHEMA.md 3.2.4）
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), comment="渠道ID")

    # 基本信息
    name = Column(String(50), nullable=False, comment="渠道名称")
    channel_code = Column(String(20), unique=True, nullable=False, comment="渠道代码")
    status = Column(String(20), nullable=False, comment="渠道状态")
    country = Column(String(10), nullable=True, comment="国家/地区")
    notes = Column(Text, nullable=True, comment="备注")

    # ========== 关系定义 ==========

    # 一对多：渠道 -> 广告账户
    ad_accounts = relationship(
        "AdAccount",
        back_populates="channel",
        cascade="all, delete-orphan",
        lazy="dynamic",
        doc="渠道下的所有广告账户"
    )

    # 一对多：渠道 -> 评审记录
    reviews = relationship(
        "ChannelReview",
        back_populates="channel",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="ChannelReview.created_at.desc()",
        doc="渠道的评审记录"
    )

    # 一对多：渠道 -> 表现统计
    performance_stats = relationship(
        "ChannelPerformance",
        back_populates="channel",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="ChannelPerformance.stat_date.desc()",
        doc="渠道的表现统计"
    )

    # 约束
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive')",
            name='chk_channels_status'
        ),
    )

    def __repr__(self):
        return f"<Channel(id={self.id}, name='{self.name}', code='{self.channel_code}')>"

    # ========== 业务属性 ==========

    @property
    def status_enum(self) -> ChannelStatus:
        """返回状态枚举对象"""
        return ChannelStatus(self.status)

    @property
    def is_active(self) -> bool:
        """是否是活跃渠道"""
        return self.status == ChannelStatus.ACTIVE.value

    # ========== 业务方法 ==========

    def activate(self):
        """激活渠道"""
        self.status = ChannelStatus.ACTIVE.value

    def deactivate(self):
        """停用渠道"""
        self.status = ChannelStatus.INACTIVE.value

    # ========== 查询作用域方法 ==========

    @classmethod
    def get_active_channels(cls, session):
        """获取所有活跃渠道"""
        return session.query(cls).filter(
            cls.status == ChannelStatus.ACTIVE.value
        ).all()

    @classmethod
    def get_by_code(cls, session, channel_code: str):
        """根据渠道代码获取渠道"""
        return session.query(cls).filter(
            cls.channel_code == channel_code
        ).first()


class ChannelReview(Base, TimestampMixin, SerializableMixin):
    """
    渠道评审记录表

    字段：
    - id: 主键
    - channel_id: 渠道ID（外键）
    - reviewer_id: 评审人ID（外键）
    - review_status: 评审状态（draft/pending/approved/rejected）
    - review_notes: 评审备注
    - reviewed_at: 评审完成时间
    - created_at/updated_at: 时间戳（自动管理）
    """
    __tablename__ = 'channel_reviews'

    # 序列化配置
    __json_include_relationships__ = ['channel', 'reviewer']

    # 主键：UUID（对齐 DATA_SCHEMA.md 3.2.6）
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), comment="评审记录ID")

    # 外键：UUID（对齐 DATA_SCHEMA.md 3.2.6）
    channel_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('channels.id', ondelete='CASCADE'),
        nullable=False,
        comment="渠道ID"
    )
    reviewer_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="评审人ID"
    )

    # 业务字段
    review_status = Column(String(20), nullable=False, comment="评审状态")
    review_notes = Column(Text, nullable=True, comment="评审备注")
    reviewed_at = Column(DateTime(timezone=True), nullable=True, comment="评审完成时间")

    # ========== 关系定义 ==========

    # 多对一：评审记录 -> 渠道
    channel = relationship(
        "Channel",
        back_populates="reviews",
        lazy="joined",
        doc="所属渠道"
    )

    # 多对一：评审记录 -> 评审人
    reviewer = relationship(
        "User",
        foreign_keys=[reviewer_id],
        lazy="selectin",
        doc="评审人"
    )

    # 约束
    __table_args__ = (
        CheckConstraint(
            "review_status IN ('draft', 'pending', 'approved', 'rejected')",
            name='chk_channel_reviews_review_status'
        ),
    )

    def __repr__(self):
        return f"<ChannelReview(id={self.id}, channel_id={self.channel_id}, status='{self.review_status}')>"

    # ========== 业务属性 ==========

    @property
    def status_enum(self) -> ChannelReviewStatus:
        """返回状态枚举对象"""
        return ChannelReviewStatus(self.review_status)

    @property
    def is_approved(self) -> bool:
        """是否已批准"""
        return self.review_status == ChannelReviewStatus.APPROVED.value

    @property
    def is_rejected(self) -> bool:
        """是否已拒绝"""
        return self.review_status == ChannelReviewStatus.REJECTED.value

    # ========== 业务方法 ==========

    def approve(self, reviewer_id: UUID, notes: str = None):
        """批准评审"""
        self.review_status = ChannelReviewStatus.APPROVED.value
        self.reviewer_id = reviewer_id
        self.reviewed_at = func.now()
        if notes:
            self.review_notes = notes

    def reject(self, reviewer_id: UUID, reason: str):
        """拒绝评审"""
        self.review_status = ChannelReviewStatus.REJECTED.value
        self.reviewer_id = reviewer_id
        self.reviewed_at = func.now()
        self.review_notes = reason


class ChannelPerformance(Base, SerializableMixin):
    """
    渠道表现统计表

    字段：
    - id: 主键
    - channel_id: 渠道ID（外键）
    - stat_date: 统计日期
    - total_accounts: 总账户数
    - active_accounts: 活跃账户数
    - dead_accounts: 死号数量
    - total_spend: 总消耗
    - avg_account_lifespan: 平均账户寿命（天）
    - death_rate: 死号率
    - created_at: 创建时间
    """
    __tablename__ = 'channel_performance'

    # 序列化配置
    __json_include_relationships__ = ['channel']

    # 主键：UUID（对齐 DATA_SCHEMA.md 3.2.8）
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), comment="统计记录ID")

    # 外键：UUID（对齐 DATA_SCHEMA.md 3.2.8）
    channel_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('channels.id', ondelete='CASCADE'),
        nullable=False,
        comment="渠道ID"
    )

    # 业务字段
    stat_date = Column(Date, nullable=False, comment="统计日期")
    total_accounts = Column(Integer, nullable=False, default=0, comment="总账户数")
    active_accounts = Column(Integer, nullable=False, default=0, comment="活跃账户数")
    dead_accounts = Column(Integer, nullable=False, default=0, comment="死号数量")
    total_spend = Column(Numeric(15, 2), nullable=False, default=Decimal('0.00'), comment="总消耗")
    avg_account_lifespan = Column(Numeric(12, 2), nullable=True, comment="平均账户寿命（天）")
    death_rate = Column(Numeric(12, 4), nullable=True, comment="死号率")

    # 时间戳
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="创建时间"
    )

    # ========== 关系定义 ==========

    # 多对一：统计记录 -> 渠道
    channel = relationship(
        "Channel",
        back_populates="performance_stats",
        lazy="joined",
        doc="所属渠道"
    )

    # 约束
    __table_args__ = (
        UniqueConstraint(
            'channel_id', 'stat_date',
            name='channel_performance_channel_id_stat_date_key'
        ),
    )

    def __repr__(self):
        return f"<ChannelPerformance(id={self.id}, channel_id={self.channel_id}, date={self.stat_date})>"

    # ========== 业务属性 ==========

    @property
    def survival_rate(self) -> Decimal:
        """账户存活率"""
        if self.total_accounts == 0:
            return Decimal('0.0000')
        return Decimal('1.0000') - (self.death_rate or Decimal('0.0000'))

    @property
    def account_utilization_rate(self) -> Decimal:
        """账户利用率"""
        if self.total_accounts == 0:
            return Decimal('0.0000')
        return Decimal(self.active_accounts) / Decimal(self.total_accounts)

    # ========== 查询作用域方法 ==========

    @classmethod
    def get_by_channel_and_date(cls, session, channel_id: UUID, stat_date: date):
        """根据渠道和日期获取统计记录"""
        return session.query(cls).filter(
            cls.channel_id == channel_id,
            cls.stat_date == stat_date
        ).first()

    @classmethod
    def get_latest_stats(cls, session, channel_id: UUID, limit: int = 30):
        """获取渠道的最近N天统计"""
        return session.query(cls).filter(
            cls.channel_id == channel_id
        ).order_by(
            cls.stat_date.desc()
        ).limit(limit).all()
