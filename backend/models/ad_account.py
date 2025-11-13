"""
广告账户管理数据模型
Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Boolean,
    Text, DECIMAL, ForeignKey, JSON, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class AdAccount(Base):
    """广告账户表"""
    __tablename__ = "ad_accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(255), unique=True, nullable=False, index=True, comment="平台账户ID")
    name = Column(String(255), nullable=False, index=True, comment="账户名称")

    # 平台信息
    platform = Column(String(50), nullable=False, comment="广告平台")
    platform_account_id = Column(String(255), nullable=True, comment="平台内部账户ID")
    platform_business_id = Column(String(255), nullable=True, comment="商务管理器ID")

    # 关联信息
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID")
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, comment="渠道ID")
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="负责投手ID")

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

    # 预算信息
    daily_budget = Column(DECIMAL(10, 2), nullable=True, comment="日预算")
    total_budget = Column(DECIMAL(12, 2), nullable=True, comment="总预算")
    remaining_budget = Column(DECIMAL(12, 2), nullable=True, comment="剩余预算")

    # 账户信息
    currency = Column(String(3), default="USD", comment="货币单位")
    timezone = Column(String(50), nullable=True, comment="时区设置")
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
    metadata = Column(JSON, nullable=True, comment="元数据")

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    project = relationship("Project", back_populates="ad_accounts")
    channel = relationship("Channel", back_populates="ad_accounts")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
    creator = relationship("User", foreign_keys=[created_by])
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
        Index("idx_ad_accounts_platform", "platform"),
        Index("idx_ad_accounts_status", "status"),
        Index("idx_ad_accounts_project", "project_id"),
        Index("idx_ad_accounts_channel", "channel_id"),
        Index("idx_ad_accounts_assigned_user", "assigned_user_id"),
        Index("idx_ad_accounts_created_at", "created_at"),
        {"comment": "广告账户表"}
    )


class AccountStatusHistory(Base):
    """账户状态历史表"""
    __tablename__ = "account_status_history"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("ad_accounts.id"), nullable=False, comment="账户ID")

    # 状态变更信息
    old_status = Column(String(20), nullable=True, comment="原状态")
    new_status = Column(String(20), nullable=False, comment="新状态")
    change_reason = Column(Text, nullable=True, comment="变更原因")

    # 变更时间
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="变更时间")

    # 变更人员
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="变更人ID")
    change_source = Column(String(50), default="manual", comment="变更来源")

    # 相关数据
    performance_data = Column(JSON, nullable=True, comment="变更时的性能数据")
    notes = Column(Text, nullable=True, comment="备注说明")

    # 关系
    account = relationship("AdAccount", back_populates="status_history")
    changed_user = relationship("User")

    # 索引
    __table_args__ = (
        Index("idx_account_status_history_account", "account_id"),
        Index("idx_account_status_history_changed_at", "changed_at"),
        {"comment": "账户状态历史表"}
    )


class AccountPerformance(Base):
    """账户表现表"""
    __tablename__ = "account_performance"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("ad_accounts.id"), nullable=False, comment="账户ID")

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
    """账户预警表"""
    __tablename__ = "account_alerts"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("ad_accounts.id"), nullable=False, comment="账户ID")

    # 预警信息
    alert_type = Column(String(50), nullable=False, comment="预警类型")
    severity = Column(String(20), nullable=False, comment="严重程度")
    title = Column(String(255), nullable=False, comment="预警标题")
    message = Column(Text, nullable=False, comment="预警消息")

    # 预警状态
    status = Column(String(20), default="active", comment="预警状态")

    # 触发条件
    trigger_condition = Column(JSON, nullable=True, comment="触发条件")
    trigger_value = Column(DECIMAL(15, 2), nullable=True, comment="触发值")
    threshold_value = Column(DECIMAL(15, 2), nullable=True, comment="阈值")

    # 处理信息
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="确认人ID")
    acknowledged_at = Column(DateTime, nullable=True, comment="确认时间")
    resolution = Column(Text, nullable=True, comment="解决方案")
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="解决人ID")
    resolved_at = Column(DateTime, nullable=True, comment="解决时间")

    # 通知设置
    notify_users = Column(JSON, nullable=True, comment="通知用户列表")
    notification_sent = Column(Boolean, default=False, comment="是否已发送通知")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    account = relationship("AdAccount", back_populates="alerts")
    acknowledged_user = relationship("User", foreign_keys=[acknowledged_by])
    resolved_user = relationship("User", foreign_keys=[resolved_by])

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
    """账户文档表"""
    __tablename__ = "account_documents"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("ad_accounts.id"), nullable=False, comment="账户ID")

    # 文档信息
    document_type = Column(String(50), nullable=False, comment="文档类型")
    document_name = Column(String(255), nullable=False, comment="文档名称")
    file_path = Column(String(500), nullable=True, comment="文件路径")
    file_size = Column(Integer, nullable=True, comment="文件大小")
    file_type = Column(String(50), nullable=True, comment="文件类型")

    # 文档描述
    description = Column(Text, nullable=True, comment="文档描述")
    tags = Column(JSON, nullable=True, comment="标签")

    # 状态信息
    status = Column(String(20), default="active", comment="状态")

    # 上传信息
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="上传人ID")
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), comment="上传时间")

    # 访问权限
    is_public = Column(Boolean, default=False, comment="是否公开")
    shared_users = Column(JSON, nullable=True, comment="共享用户列表")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    account = relationship("AdAccount", back_populates="documents")
    uploader = relationship("User")

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
    """账户备注表"""
    __tablename__ = "account_notes"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("ad_accounts.id"), nullable=False, comment="账户ID")

    # 备注信息
    title = Column(String(255), nullable=False, comment="备注标题")
    content = Column(Text, nullable=False, comment="备注内容")
    note_type = Column(String(50), default="general", comment="备注类型")

    # 重要性
    priority = Column(Integer, default=1, comment="优先级")

    # 状态
    is_resolved = Column(Boolean, default=False, comment="是否已解决")
    resolved_at = Column(DateTime, nullable=True, comment="解决时间")

    # 创建信息
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

    # 关系
    account = relationship("AdAccount", back_populates="notes")
    creator = relationship("User")

    # 索引和约束
    __table_args__ = (
        CheckConstraint(
            "priority BETWEEN 1 AND 5",
            name="check_note_priority_range"
        ),
        Index("idx_account_notes_account", "account_id"),
        Index("idx_account_notes_type", "note_type"),
        Index("idx_account_notes_priority", "priority"),
        Index("idx_account_notes_resolved", "is_resolved"),
        Index("idx_account_notes_created_at", "created_at"),
        {"comment": "账户备注表"}
    )