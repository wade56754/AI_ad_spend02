"""
广告账户管理数据模型
Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, BigInteger, String, Date, DateTime, Boolean,
    Text, Numeric, ForeignKey, JSON, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.db import Base


class AdAccount(Base):
    """广告账户表（对齐 DATA_SCHEMA.md 3.2.9）"""
    __tablename__ = "ad_accounts"

    # 主键：BIGSERIAL（对齐 DATA_SCHEMA）
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="账户ID")
    
    # 基本信息（字段名对齐 DATA_SCHEMA）
    name = Column(String(200), nullable=False, index=True, comment="账户别名")
    account_code = Column(String(100), unique=True, nullable=False, index=True, comment="平台编号")

    # 平台信息
    platform = Column(String(50), nullable=False, comment="广告平台")
    platform_account_id = Column(String(255), nullable=True, comment="平台内部账户ID")
    platform_business_id = Column(String(255), nullable=True, comment="商务管理器ID")

    # 关联信息（外键类型对齐 DATA_SCHEMA）
    project_id = Column(
        BigInteger,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
        comment="项目ID"
    )
    channel_id = Column(
        UUID(as_uuid=True),
        ForeignKey("channels.id"),
        nullable=False,
        index=True,
        comment="渠道ID"
    )
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=False,
        comment="账户负责人ID"
    )

    # 账户状态
    status = Column(String(20), nullable=False, default="new", comment="账户状态")
    status_reason = Column(Text, nullable=True, comment="状态变更原因")
    last_status_change = Column(DateTime, nullable=True, comment="最后状态变更时间")

    # 生命周期管理
    created_date = Column(DateTime, nullable=True, comment="账户创建时间")
    activated_date = Column(DateTime, nullable=True, comment="激活时间")
    suspended_date = Column(DateTime, nullable=True, comment="暂停时间")
    dead_date = Column(DateTime, nullable=True, comment="死亡时间")
    archived_date = Column(DateTime, nullable=True, comment="归档时间")

    # 预算信息（对齐 DATA_SCHEMA：spend_limit）
    spend_limit = Column(Numeric(15, 2), default=0.00, server_default='0.00', comment="消费限额")
    
    # 账户信息（对齐 DATA_SCHEMA）
    currency = Column(String(10), default='CNY', server_default='CNY', comment="货币单位")
    timezone = Column(String(50), default='Asia/Shanghai', server_default='Asia/Shanghai', comment="时区设置")
    country = Column(String(2), nullable=True, comment="国家代码")

    # 性能数据
    total_spend = Column(DECIMAL(15, 2), default=0, comment="总消耗")
    total_leads = Column(Integer, default=0, comment="总潜在客户数")
    avg_cpl = Column(DECIMAL(10, 2), nullable=True, comment="平均单粉成本")
    best_cpl = Column(DECIMAL(10, 2), nullable=True, comment="最佳单粉成本")

    # 开户费用
    setup_fee = Column(DECIMAL(10, 2), default=0, comment="开户费")
    setup_fee_paid = Column(Boolean, default=False, comment="开户费是否已支付")

    # 账户配置
    account_type = Column(String(50), nullable=True, comment="账户类型")
    payment_method = Column(String(50), nullable=True, comment="支付方式")
    billing_information = Column(JSON, nullable=True, comment="账单信息")

    # 监控设置
    auto_monitoring = Column(Boolean, default=True, comment="自动监控")
    alert_thresholds = Column(JSON, nullable=True, comment="预警阈值设置")

    # 管理信息
    notes = Column(Text, nullable=True, comment="备注")
    tags = Column(JSON, nullable=True, comment="标签")
    account_metadata = Column(JSON, nullable=True, comment="账户元数据")

    # 审计字段（外键指向 user_profiles.id，UUID）
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=True,
        comment="创建人ID"
    )
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=True,
        comment="更新人ID"
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")

    # 关系
    project = relationship("Project", back_populates="ad_accounts")
    channel = relationship("Channel", back_populates="ad_accounts")
    owner = relationship("UserProfile", foreign_keys=[owner_id])
    creator = relationship("UserProfile", foreign_keys=[created_by])
    updater = relationship("UserProfile", foreign_keys=[updated_by])
    daily_reports = relationship("DailyReport", back_populates="ad_account", cascade="all, delete-orphan")
    status_history = relationship("AccountStatusHistory", back_populates="account", cascade="all, delete-orphan")
    performance_records = relationship("AccountPerformance", back_populates="account", cascade="all, delete-orphan")
    alerts = relationship("AccountAlert", back_populates="account", cascade="all, delete-orphan")
    documents = relationship("AccountDocument", back_populates="account", cascade="all, delete-orphan")
    notes = relationship("AccountNote", back_populates="account", cascade="all, delete-orphan")

    # 约束
    __table_args__ = (
        CheckConstraint(
            "status IN ('new', 'testing', 'active', 'suspended', 'dead', 'archived')",
            name="check_account_status"
        ),
        CheckConstraint(
            "daily_budget >= 0",
            name="check_daily_budget_non_negative"
        ),
        CheckConstraint(
            "total_budget >= 0",
            name="check_total_budget_non_negative"
        ),
        CheckConstraint(
            "total_spend >= 0",
            name="check_total_spend_non_negative"
        ),
        Index("idx_ad_accounts_project", "project_id"),
        Index("idx_ad_accounts_channel", "channel_id"),
        Index("idx_ad_accounts_status", "status"),
        {"comment": "广告账户表"}
    )


class AccountStatusHistory(Base):
    """账户状态历史表（对齐 DATA_SCHEMA.md 3.2.9）"""
    __tablename__ = "account_status_history"

    # 主键：BIGSERIAL（对齐 DATA_SCHEMA）
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="历史记录ID")
    ad_account_id = Column(
        BigInteger,
        ForeignKey("ad_accounts.id"),
        nullable=False,
        index=True,
        comment="账户ID"
    )

    # 状态变更信息（字段名对齐 DATA_SCHEMA）
    from_status = Column(String(20), nullable=True, comment="原状态")
    to_status = Column(String(20), nullable=False, comment="新状态")
    notes = Column(Text, nullable=True, comment="备注说明")

    # 变更时间
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="变更时间")

    # 变更人员（外键指向 user_profiles.id，UUID）
    changed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=False,
        comment="变更人ID"
    )

    # 关系
    account = relationship("AdAccount", back_populates="status_history")
    changed_user = relationship("UserProfile", foreign_keys=[changed_by])

    # 索引
    __table_args__ = (
        Index("idx_account_status_history_account", "ad_account_id"),
        Index("idx_account_status_history_changed_at", "changed_at"),
        {"comment": "账户状态历史表"}
    )


class AccountPerformance(Base):
    """账户表现表（不在 DATA_SCHEMA 核心定义中，保留用于业务逻辑）"""
    __tablename__ = "account_performance"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="表现记录ID")
    account_id = Column(BigInteger, ForeignKey("ad_accounts.id"), nullable=False, comment="账户ID")

    # 统计周期
    period_type = Column(String(20), nullable=False, comment="统计周期")
    period_start = Column(Date, nullable=False, comment="周期开始日期")
    period_end = Column(Date, nullable=False, comment="周期结束日期")

    # 消耗数据
    spend = Column(DECIMAL(15, 2), nullable=False, comment="消耗")
    impressions = Column(Integer, default=0, comment="展示次数")
    clicks = Column(Integer, default=0, comment="点击次数")
    ctr = Column(DECIMAL(5, 4), nullable=True, comment="点击率")

    # 转化数据
    leads = Column(Integer, default=0, comment="潜在客户数")
    conversions = Column(Integer, default=0, comment="转化数")
    conversion_rate = Column(DECIMAL(5, 4), nullable=True, comment="转化率")

    # 成本数据
    cpl = Column(DECIMAL(10, 2), nullable=True, comment="单粉成本")
    cpa = Column(DECIMAL(10, 2), nullable=True, comment="单次转化成本")
    roas = Column(DECIMAL(5, 2), nullable=True, comment="广告支出回报率")

    # 质量指标
    lead_quality_score = Column(DECIMAL(3, 2), nullable=True, comment="潜在客户质量评分")
    account_health_score = Column(DECIMAL(3, 2), nullable=True, comment="账户健康评分")

    # 详细数据
    breakdown_data = Column(JSON, nullable=True, comment="细分数据")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

    # 关系
    account = relationship("AdAccount", back_populates="performance_records")

    # 索引和约束
    __table_args__ = (
        CheckConstraint(
            "period_type IN ('daily', 'weekly', 'monthly')",
            name="check_period_type"
        ),
        CheckConstraint(
            "period_end >= period_start",
            name="check_period_date_valid"
        ),
        Index("idx_account_performance_account", "account_id"),
        Index("idx_account_performance_period", "period_type", "period_start"),
        Index("idx_account_performance_spend", "spend"),
        {"comment": "账户表现表"}
    )


class AccountAlert(Base):
    """账户预警表（对齐 DATA_SCHEMA.md 3.2.9）"""
    __tablename__ = "account_alerts"

    # 主键：BIGSERIAL（对齐 DATA_SCHEMA）
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="预警ID")
    ad_account_id = Column(
        BigInteger,
        ForeignKey("ad_accounts.id"),
        nullable=False,
        index=True,
        comment="账户ID"
    )

    # 预警信息（对齐 DATA_SCHEMA）
    alert_type = Column(String(50), nullable=False, comment="预警类型")
    severity = Column(String(20), nullable=False, comment="严重程度：info/warning/critical")
    message = Column(Text, nullable=False, comment="预警消息")

    # 预警状态（枚举值以 STATE_MACHINE.md 为准）
    status = Column(String(20), default="active", comment="预警状态")

    # 触发条件
    trigger_condition = Column(JSON, nullable=True, comment="触发条件")
    trigger_value = Column(Numeric(15, 2), nullable=True, comment="触发值")
    threshold_value = Column(Numeric(15, 2), nullable=True, comment="阈值")

    # 处理信息（对齐 DATA_SCHEMA）
    resolved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=True,
        comment="解决人ID"
    )
    resolved_at = Column(DateTime(timezone=True), nullable=True, comment="解决时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")

    # 关系
    account = relationship("AdAccount", back_populates="alerts")
    resolved_user = relationship("UserProfile", foreign_keys=[resolved_by])

    # 索引和约束
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'acknowledged', 'resolved', 'ignored')",
            name="check_alert_status"
        ),
        CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="check_alert_severity"
        ),
        Index("idx_account_alerts_account", "account_id"),
        Index("idx_account_alerts_status", "status"),
        Index("idx_account_alerts_severity", "severity"),
        Index("idx_account_alerts_type", "alert_type"),
        Index("idx_account_alerts_created_at", "created_at"),
        {"comment": "账户预警表"}
    )


class AccountDocument(Base):
    """账户文档表（对齐 DATA_SCHEMA.md 3.2.9）"""
    __tablename__ = "account_documents"

    # 主键：BIGSERIAL（对齐 DATA_SCHEMA）
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="文档ID")
    ad_account_id = Column(
        BigInteger,
        ForeignKey("ad_accounts.id"),
        nullable=False,
        index=True,
        comment="账户ID"
    )

    # 文档信息（字段名对齐 DATA_SCHEMA）
    document_type = Column(String(50), nullable=False, comment="文档类型")
    storage_path = Column(String(500), nullable=True, comment="存储路径")
    file_name = Column(String(255), nullable=False, comment="文件名称")
    notes = Column(Text, nullable=True, comment="备注说明")

    # 上传信息（外键指向 user_profiles.id，UUID）
    uploaded_by = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=False,
        comment="上传人ID"
    )
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="上传时间")

    # 关系
    account = relationship("AdAccount", back_populates="documents")
    uploader = relationship("UserProfile", foreign_keys=[uploaded_by])

    # 索引和约束
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'archived', 'deleted')",
            name="check_document_status"
        ),
        Index("idx_account_documents_account", "account_id"),
        Index("idx_account_documents_type", "document_type"),
        Index("idx_account_documents_status", "status"),
        Index("idx_account_documents_uploaded_at", "uploaded_at"),
        {"comment": "账户文档表"}
    )


class AccountNote(Base):
    """账户备注表（对齐 DATA_SCHEMA.md 3.2.9）"""
    __tablename__ = "account_notes"

    # 主键：BIGSERIAL（对齐 DATA_SCHEMA）
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="备注ID")
    ad_account_id = Column(
        BigInteger,
        ForeignKey("ad_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="账户ID"
    )

    # 备注信息（字段名对齐 DATA_SCHEMA）
    note_type = Column(String(20), nullable=False, default="general", comment="备注类型：general/risk/finance")
    content = Column(Text, nullable=False, comment="备注内容")

    # 创建信息（外键指向 user_profiles.id，UUID）
    author_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=False,
        comment="作者ID"
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")

    # 关系
    account = relationship("AdAccount", back_populates="notes")
    author = relationship("UserProfile", foreign_keys=[author_id])

    # 索引
    __table_args__ = (
        Index("idx_account_notes_account", "ad_account_id"),
        Index("idx_account_notes_type", "note_type"),
        {"comment": "账户备注表"}
    )