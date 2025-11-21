"""
广告消耗模型 - 每日广告花费数据（从渠道导入）
"""
from decimal import Decimal
from uuid import UUID
from datetime import date
from sqlalchemy import Column, BigInteger, String, Integer, Numeric, Date, DateTime, Index, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base, TimestampMixin
from backend.models.mixins.serializable import SerializableMixin


class AdSpendDaily(Base, TimestampMixin, SerializableMixin):
    """
    每日广告花费数据表（从渠道导入）

    字段：
    - id: 主键
    - ad_account_code: 广告账户代码
    - spend_date: 消耗日期
    - impressions: 展示次数
    - clicks: 点击次数
    - conversions: 转化次数
    - cost: 成本
    - revenue: 收入
    - roi: 投资回报率
    - imported_by: 导入人ID（外键）
    - imported_at: 导入时间
    - created_at/updated_at: 时间戳（自动管理）
    """
    __tablename__ = 'ad_spend_daily'

    # 序列化配置
    __json_include_relationships__ = ['importer']

    # 主键：UUID（对齐 DATA_SCHEMA.md 3.3.5）
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), comment="记录ID")

    # 业务字段
    ad_account_code = Column(String(50), nullable=False, comment="广告账户代码")
    spend_date = Column(Date, nullable=False, comment="消耗日期")
    impressions = Column(BigInteger, nullable=True, comment="展示次数")
    clicks = Column(BigInteger, nullable=True, comment="点击次数")
    conversions = Column(Integer, nullable=True, comment="转化次数")
    cost = Column(Numeric(15, 2), nullable=True, comment="成本")
    revenue = Column(Numeric(15, 2), nullable=True, comment="收入")
    roi = Column(Numeric(12, 4), nullable=True, comment="投资回报率")

    # 外键
    imported_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="导入人ID"
    )
    imported_at = Column(DateTime(timezone=True), nullable=True, comment="导入时间")

    # ========== 关系定义 ==========

    # 多对一：消耗记录 -> 导入人
    importer = relationship(
        "User",
        foreign_keys=[imported_by],
        lazy="selectin",
        doc="数据导入人"
    )

    # 约束和索引
    __table_args__ = (
        UniqueConstraint(
            'ad_account_code', 'spend_date',
            name='ad_spend_daily_ad_account_code_spend_date_key'
        ),
        Index('idx_ad_spend_daily_account_code', 'ad_account_code'),
        Index('idx_ad_spend_daily_spend_date', 'spend_date'),
    )

    def __repr__(self):
        return f"<AdSpendDaily(id={self.id}, account_code='{self.ad_account_code}', date={self.spend_date})>"

    # ========== 业务属性 ==========

    @property
    def ctr(self) -> Decimal:
        """点击率 (Click Through Rate)"""
        if not self.impressions or self.impressions == 0:
            return Decimal('0.0000')
        return Decimal(self.clicks or 0) / Decimal(self.impressions) * Decimal('100')

    @property
    def cvr(self) -> Decimal:
        """转化率 (Conversion Rate)"""
        if not self.clicks or self.clicks == 0:
            return Decimal('0.0000')
        return Decimal(self.conversions or 0) / Decimal(self.clicks) * Decimal('100')

    @property
    def cpc(self) -> Decimal:
        """单次点击成本 (Cost Per Click)"""
        if not self.clicks or self.clicks == 0:
            return Decimal('0.00')
        return Decimal(self.cost or Decimal('0.00')) / Decimal(self.clicks)

    @property
    def cpa(self) -> Decimal:
        """单次转化成本 (Cost Per Action)"""
        if not self.conversions or self.conversions == 0:
            return Decimal('0.00')
        return Decimal(self.cost or Decimal('0.00')) / Decimal(self.conversions)

    @property
    def profit(self) -> Decimal:
        """利润"""
        return Decimal(self.revenue or Decimal('0.00')) - Decimal(self.cost or Decimal('0.00'))

    # ========== 查询作用域方法 ==========

    @classmethod
    def get_by_account_and_date(cls, session, ad_account_code: str, spend_date: date):
        """根据账户代码和日期获取记录"""
        return session.query(cls).filter(
            cls.ad_account_code == ad_account_code,
            cls.spend_date == spend_date
        ).first()

    @classmethod
    def get_account_date_range(cls, session, ad_account_code: str, start_date: date, end_date: date):
        """获取账户在指定日期范围内的消耗记录"""
        return session.query(cls).filter(
            cls.ad_account_code == ad_account_code,
            cls.spend_date >= start_date,
            cls.spend_date <= end_date
        ).order_by(
            cls.spend_date.asc()
        ).all()

    @classmethod
    def get_date_total(cls, session, spend_date: date):
        """获取指定日期所有账户的总消耗"""
        from sqlalchemy import func as sql_func
        result = session.query(
            sql_func.sum(cls.cost).label('total_cost'),
            sql_func.sum(cls.revenue).label('total_revenue'),
            sql_func.sum(cls.impressions).label('total_impressions'),
            sql_func.sum(cls.clicks).label('total_clicks'),
            sql_func.sum(cls.conversions).label('total_conversions')
        ).filter(
            cls.spend_date == spend_date
        ).first()

        return {
            'total_cost': result.total_cost or Decimal('0.00'),
            'total_revenue': result.total_revenue or Decimal('0.00'),
            'total_impressions': result.total_impressions or 0,
            'total_clicks': result.total_clicks or 0,
            'total_conversions': result.total_conversions or 0
        }
