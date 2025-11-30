"""
账户辅助模型 - 性能、文档、备注
Version: 1.0
Author: Claude Code (full_pipeline)

包含：
- AccountPerformance: 账户效果数据（用于聚合统计）
- AccountDocument: 账户文档
- AccountNote: 账户备注
"""
from datetime import date
from decimal import Decimal
from sqlalchemy import Column, BigInteger, String, Text, Date, DateTime, Numeric, Boolean, Index, CheckConstraint, ForeignKey, UniqueConstraint, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base
from backend.models.mixins.serializable import SerializableMixin


class AccountPerformance(Base, SerializableMixin):
    """
    账户效果数据表（按天聚合）

    字段：
    - id: 主键
    - ad_account_id: 广告账户ID（外键）
    - date: 统计日期
    - impressions: 展示数
    - clicks: 点击数
    - spend: 消耗金额
    - conversions: 转化数
    - revenue: 收入
    - ctr: 点击率
    - cpc: 单次点击成本
    - cpa: 单次转化成本
    - roas: 广告投资回报率
    - created_at: 创建时间
    - updated_at: 更新时间

    唯一约束：(ad_account_id, date)
    """
    __tablename__ = 'account_performance'

    # 序列化配置
    __json_include_relationships__ = ['ad_account']

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="性能记录ID")

    # 外键
    ad_account_id = Column(
        BigInteger,
        ForeignKey('ad_accounts.id', ondelete='CASCADE'),
        nullable=False,
        comment="广告账户ID"
    )

    # 统计日期
    date = Column(Date, nullable=False, comment="统计日期")

    # 效果指标
    impressions = Column(BigInteger, nullable=False, default=0, comment="展示数")
    clicks = Column(BigInteger, nullable=False, default=0, comment="点击数")
    spend = Column(Numeric(15, 2), nullable=False, default=Decimal('0.00'), comment="消耗金额")
    conversions = Column(BigInteger, nullable=False, default=0, comment="转化数")
    revenue = Column(Numeric(15, 2), nullable=False, default=Decimal('0.00'), comment="收入")

    # 计算指标（可由触发器/定时任务更新）
    ctr = Column(Numeric(8, 4), nullable=True, comment="点击率 (clicks/impressions)")
    cpc = Column(Numeric(15, 4), nullable=True, comment="单次点击成本 (spend/clicks)")
    cpa = Column(Numeric(15, 4), nullable=True, comment="单次转化成本 (spend/conversions)")
    roas = Column(Numeric(8, 4), nullable=True, comment="广告投资回报率 (revenue/spend)")

    # 时间戳
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )

    # ========== 关系定义 ==========

    # 多对一：性能记录 -> 广告账户
    ad_account = relationship(
        "AdAccount",
        foreign_keys=[ad_account_id],
        lazy="joined",
        doc="所属广告账户"
    )

    # 约束与索引
    __table_args__ = (
        UniqueConstraint('ad_account_id', 'date', name='uq_account_performance_account_date'),
        Index('idx_account_performance_account_id', 'ad_account_id'),
        Index('idx_account_performance_date', 'date'),
        Index('idx_account_performance_account_date', 'ad_account_id', 'date'),
    )

    def __repr__(self):
        return f"<AccountPerformance(id={self.id}, account_id={self.ad_account_id}, date='{self.date}')>"

    # ========== 业务方法 ==========

    def calculate_derived_metrics(self):
        """计算衍生指标"""
        # CTR
        if self.impressions and self.impressions > 0:
            self.ctr = Decimal(self.clicks) / Decimal(self.impressions)
        else:
            self.ctr = None

        # CPC
        if self.clicks and self.clicks > 0:
            self.cpc = self.spend / Decimal(self.clicks)
        else:
            self.cpc = None

        # CPA
        if self.conversions and self.conversions > 0:
            self.cpa = self.spend / Decimal(self.conversions)
        else:
            self.cpa = None

        # ROAS
        if self.spend and self.spend > 0:
            self.roas = self.revenue / self.spend
        else:
            self.roas = None


class AccountDocument(Base, SerializableMixin):
    """
    账户文档表

    字段：
    - id: 主键
    - ad_account_id: 广告账户ID（外键）
    - uploaded_by: 上传人ID（外键）
    - title: 文档标题
    - file_name: 文件名
    - file_url: 文件URL
    - file_type: 文件类型
    - file_size: 文件大小（字节）
    - description: 文档描述
    - document_type: 文档类型（contract/invoice/screenshot/other）
    - created_at: 创建时间
    """
    __tablename__ = 'account_documents'

    # 序列化配置
    __json_include_relationships__ = ['ad_account', 'uploader']

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="文档ID")

    # 外键
    ad_account_id = Column(
        BigInteger,
        ForeignKey('ad_accounts.id', ondelete='CASCADE'),
        nullable=False,
        comment="广告账户ID"
    )
    uploaded_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="上传人ID"
    )

    # 文档信息
    title = Column(String(200), nullable=False, comment="文档标题")
    file_name = Column(String(255), nullable=False, comment="文件名")
    file_url = Column(String(500), nullable=False, comment="文件URL")
    file_type = Column(String(50), nullable=True, comment="文件类型")
    file_size = Column(BigInteger, nullable=True, comment="文件大小（字节）")
    description = Column(Text, nullable=True, comment="文档描述")
    document_type = Column(String(50), nullable=False, default='other', comment="文档类型")

    # 时间戳
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="创建时间"
    )

    # ========== 关系定义 ==========

    # 多对一：文档 -> 广告账户
    ad_account = relationship(
        "AdAccount",
        foreign_keys=[ad_account_id],
        lazy="joined",
        doc="所属广告账户"
    )

    # 多对一：文档 -> 上传人
    uploader = relationship(
        "User",
        foreign_keys=[uploaded_by],
        lazy="selectin",
        doc="上传人"
    )

    # 约束与索引
    __table_args__ = (
        CheckConstraint(
            "document_type IN ('contract', 'invoice', 'screenshot', 'report', 'other')",
            name='chk_account_documents_type'
        ),
        Index('idx_account_documents_account_id', 'ad_account_id'),
        Index('idx_account_documents_document_type', 'document_type'),
        Index('idx_account_documents_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<AccountDocument(id={self.id}, account_id={self.ad_account_id}, title='{self.title}')>"


class AccountNote(Base, SerializableMixin):
    """
    账户备注表

    字段：
    - id: 主键
    - ad_account_id: 广告账户ID（外键）
    - created_by: 创建人ID（外键）
    - title: 备注标题
    - content: 备注内容
    - note_type: 备注类型（general/important/action_item/issue）
    - priority: 优先级（1-5）
    - is_resolved: 是否已解决（用于 action_item/issue 类型）
    - resolved_by: 解决人ID
    - resolved_at: 解决时间
    - created_at: 创建时间
    - updated_at: 更新时间
    """
    __tablename__ = 'account_notes'

    # 序列化配置
    __json_include_relationships__ = ['ad_account', 'creator', 'resolver']

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="备注ID")

    # 外键
    ad_account_id = Column(
        BigInteger,
        ForeignKey('ad_accounts.id', ondelete='CASCADE'),
        nullable=False,
        comment="广告账户ID"
    )
    created_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="创建人ID"
    )
    resolved_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="解决人ID"
    )

    # 备注信息
    title = Column(String(200), nullable=False, comment="备注标题")
    content = Column(Text, nullable=False, comment="备注内容")
    note_type = Column(String(50), nullable=False, default='general', comment="备注类型")
    priority = Column(Integer, nullable=False, default=3, comment="优先级（1-5，5最高）")

    # 解决状态
    is_resolved = Column(Boolean, nullable=False, default=False, comment="是否已解决")
    resolved_at = Column(DateTime(timezone=True), nullable=True, comment="解决时间")

    # 时间戳
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )

    # ========== 关系定义 ==========

    # 多对一：备注 -> 广告账户
    ad_account = relationship(
        "AdAccount",
        foreign_keys=[ad_account_id],
        lazy="joined",
        doc="所属广告账户"
    )

    # 多对一：备注 -> 创建人
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        lazy="selectin",
        doc="创建人"
    )

    # 多对一：备注 -> 解决人
    resolver = relationship(
        "User",
        foreign_keys=[resolved_by],
        lazy="selectin",
        doc="解决人"
    )

    # 约束与索引
    __table_args__ = (
        CheckConstraint(
            "note_type IN ('general', 'important', 'action_item', 'issue')",
            name='chk_account_notes_type'
        ),
        CheckConstraint(
            "priority BETWEEN 1 AND 5",
            name='chk_account_notes_priority'
        ),
        Index('idx_account_notes_account_id', 'ad_account_id'),
        Index('idx_account_notes_note_type', 'note_type'),
        Index('idx_account_notes_priority', 'priority'),
        Index('idx_account_notes_is_resolved', 'is_resolved'),
        Index('idx_account_notes_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<AccountNote(id={self.id}, account_id={self.ad_account_id}, title='{self.title}')>"

    # ========== 业务方法 ==========

    def resolve(self, resolver_id):
        """标记备注为已解决"""
        if self.is_resolved:
            raise ValueError("备注已经是解决状态")

        self.is_resolved = True
        self.resolved_by = resolver_id
        self.resolved_at = func.now()
