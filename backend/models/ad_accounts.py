"""
广告账户管理模块
包含Facebook广告账户、账户状态管理、生命周期跟踪等
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Numeric, Boolean, Integer, JSON, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.core.db import Base
from backend.models.ad_spend_daily import GUID


class AdAccount(Base):
    """广告账户表 - 管理Facebook等广告账户"""
    __tablename__ = "ad_accounts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    account_id = Column(String(255), unique=True, nullable=False, index=True)  # 平台账户ID
    name = Column(String(255), nullable=False, index=True)  # 账户名称

    # 平台信息
    platform = Column(String(50), nullable=False)  # Facebook, Instagram, Google, TikTok等
    platform_account_id = Column(String(255), nullable=True)  # 平台内部账户ID
    platform_business_id = Column(String(255), nullable=True)  # 商务管理器ID

    # 关联信息
    project_id = Column(GUID(), ForeignKey("projects.id"), nullable=False)
    channel_id = Column(GUID(), ForeignKey("channels.id"), nullable=False)
    assigned_user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)  # 负责投手

    # 账户状态
    status = Column(String(20), nullable=False, default="new")  # new, testing, active, suspended, dead, archived
    status_reason = Column(Text, nullable=True)  # 状态变更原因
    last_status_change = Column(DateTime, nullable=True)  # 最后状态变更时间

    # 生命周期管理
    created_date = Column(DateTime, nullable=True)  # 账户创建时间
    activated_date = Column(DateTime, nullable=True)  # 激活时间
    suspended_date = Column(DateTime, nullable=True)  # 暂停时间
    dead_date = Column(DateTime, nullable=True)  # 死亡时间
    archived_date = Column(DateTime, nullable=True)  # 归档时间

    # 预算信息
    daily_budget = Column(Numeric(10, 2), nullable=True)  # 日预算
    total_budget = Column(Numeric(12, 2), nullable=True)  # 总预算
    remaining_budget = Column(Numeric(12, 2), nullable=True)  # 剩余预算

    # 账户信息
    currency = Column(String(3), default="USD")  # 货币单位
    timezone = Column(String(50), nullable=True)  # 时区设置
    country = Column(String(2), nullable=True)  # 国家代码

    # 性能数据
    total_spend = Column(Numeric(15, 2), default=0)  # 总消耗
    total_leads = Column(Integer, default=0)  # 总潜在客户数
    avg_cpl = Column(Numeric(10, 2), nullable=True)  # 平均单粉成本
    best_cpl = Column(Numeric(10, 2), nullable=True)  # 最佳单粉成本

    # 开户费用
    setup_fee = Column(Numeric(10, 2), default=0)  # 开户费
    setup_fee_paid = Column(Boolean, default=False)  # 开户费是否已支付

    # 账户配置
    account_type = Column(String(50), nullable=True)  # 账户类型
    payment_method = Column(String(50), nullable=True)  # 支付方式
    billing_information = Column(JSON, nullable=True)  # 账单信息

    # 监控设置
    auto_monitoring = Column(Boolean, default=True)  # 自动监控
    alert_thresholds = Column(JSON, nullable=True)  # 预警阈值设置

    # 管理信息
    notes = Column(Text, nullable=True)  # 备注
    tags = Column(JSON, nullable=True)  # 标签
    metadata = Column(JSON, nullable=True)  # 元数据

    created_by = Column(GUID(), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    project = relationship("Project", back_populates="ad_accounts")
    channel = relationship("Channel", back_populates="ad_accounts")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
    creator = relationship("User", foreign_keys=[created_by])
    daily_spends = relationship("AdSpendDaily", back_populates="ad_account")
    topups = relationship("Topup", back_populates="ad_account")
    status_history = relationship("AccountStatusHistory", back_populates="account")


class AccountStatusHistory(Base):
    """账户状态历史表 - 跟踪账户状态变更"""
    __tablename__ = "account_status_history"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    account_id = Column(GUID(), ForeignKey("ad_accounts.id"), nullable=False)

    # 状态变更信息
    old_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=False)
    change_reason = Column(Text, nullable=True)

    # 变更时间
    changed_at = Column(DateTime, nullable=False)

    # 变更人员
    changed_by = Column(GUID(), ForeignKey("users.id"), nullable=False)
    change_source = Column(String(50), default="manual")  # manual, automatic, system

    # 相关数据
    performance_data = Column(JSON, nullable=True)  # 变更时的性能数据
    notes = Column(Text, nullable=True)  # 备注说明

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    account = relationship("AdAccount", back_populates="status_history")
    changed_user = relationship("User")


class AccountPerformance(Base):
    """账户表现表 - 记录账户的详细表现数据"""
    __tablename__ = "account_performance"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    account_id = Column(GUID(), ForeignKey("ad_accounts.id"), nullable=False)

    # 统计周期
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # 消耗数据
    spend = Column(Numeric(15, 2), nullable=False)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    ctr = Column(Numeric(5, 4), nullable=True)  # 点击率

    # 转化数据
    leads = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    conversion_rate = Column(Numeric(5, 4), nullable=True)

    # 成本数据
    cpl = Column(Numeric(10, 2), nullable=True)  # 单粉成本
    cpa = Column(Numeric(10, 2), nullable=True)  # 单个转化成本
    roas = Column(Numeric(5, 2), nullable=True)  # 广告支出回报率

    # 质量指标
    lead_quality_score = Column(Numeric(3, 2), nullable=True)  # 潜在客户质量评分
    account_health_score = Column(Numeric(3, 2), nullable=True)  # 账户健康评分

    # 详细数据
    breakdown_data = Column(JSON, nullable=True)  # 按广告组、广告等细分数据

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    account = relationship("AdAccount")


class AccountAlert(Base):
    """账户预警表 - 管理账户相关的预警信息"""
    __tablename__ = "account_alerts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    account_id = Column(GUID(), ForeignKey("ad_accounts.id"), nullable=False)

    # 预警信息
    alert_type = Column(String(50), nullable=False)  # budget_exceeded, low_performance, account_risk, etc.
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # 预警状态
    status = Column(String(20), default="active")  # active, acknowledged, resolved, ignored

    # 触发条件
    trigger_condition = Column(JSON, nullable=True)  # 触发条件
    trigger_value = Column(Numeric(15, 2), nullable=True)  # 触发值
    threshold_value = Column(Numeric(15, 2), nullable=True)  # 阈值

    # 处理信息
    acknowledged_by = Column(GUID(), ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolution = Column(Text, nullable=True)
    resolved_by = Column(GUID(), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # 通知设置
    notify_users = Column(JSON, nullable=True)  # 需要通知的用户列表
    notification_sent = Column(Boolean, default=False)  # 是否已发送通知

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    account = relationship("AdAccount")
    acknowledged_user = relationship("User", foreign_keys=[acknowledged_by])
    resolved_user = relationship("User", foreign_keys=[resolved_by])


class AccountDocument(Base):
    """账户文档表 - 管理账户相关的文档"""
    __tablename__ = "account_documents"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    account_id = Column(GUID(), ForeignKey("ad_accounts.id"), nullable=False)

    # 文档信息
    document_type = Column(String(50), nullable=False)  # contract, invoice, screenshot, report, etc.
    document_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String(50), nullable=True)

    # 文档描述
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)

    # 状态信息
    status = Column(String(20), default="active")  # active, archived, deleted

    # 上传信息
    uploaded_by = Column(GUID(), ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 访问权限
    is_public = Column(Boolean, default=False)  # 是否公开
    shared_users = Column(JSON, nullable=True)  # 共享用户列表

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    account = relationship("AdAccount")
    uploader = relationship("User")


class AccountNote(Base):
    """账户备注表 - 记录账户相关的重要备注"""
    __tablename__ = "account_notes"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    account_id = Column(GUID(), ForeignKey("ad_accounts.id"), nullable=False)

    # 备注信息
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    note_type = Column(String(50), default="general")  # general, important, warning, success, etc.

    # 重要性
    priority = Column(Integer, default=1)  # 1-5，5最重要

    # 状态
    is_resolved = Column(Boolean, default=False)  # 是否已解决
    resolved_at = Column(DateTime, nullable=True)

    # 创建信息
    created_by = Column(GUID(), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    account = relationship("AdAccount")
    creator = relationship("User")