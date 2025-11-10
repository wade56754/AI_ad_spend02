"""
渠道管理模块
包含广告代理商、渠道质量评估、开户费等模型
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Numeric, Boolean, Integer, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.core.db import Base
from backend.models.ad_spend_daily import GUID


class Channel(Base):
    """渠道表 - 管理广告代理商信息"""
    __tablename__ = "channels"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)  # 渠道编码
    company_name = Column(String(255), nullable=False)

    # 联系信息
    contact_person = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    contact_wechat = Column(String(100), nullable=True)

    # 费用结构
    service_fee_rate = Column(Numeric(5, 4), nullable=False)  # 服务费率，如0.05表示5%
    account_setup_fee = Column(Numeric(10, 2), default=0)  # 开户费
    minimum_topup = Column(Numeric(10, 2), default=0)  # 最低充值金额

    # 费用说明
    fee_structure = Column(JSON, nullable=True)  # 费用结构详细说明
    payment_terms = Column(Text, nullable=True)  # 付款条件

    # 渠道状态
    status = Column(String(20), nullable=False, default="active")  # active, inactive, suspended
    priority = Column(Integer, default=1)  # 优先级，数字越小优先级越高

    # 质量评估
    quality_score = Column(Numeric(3, 2), nullable=True)  # 质量评分 0-10
    reliability_score = Column(Numeric(3, 2), nullable=True)  # 可靠性评分 0-10
    price_competitiveness = Column(Numeric(3, 2), nullable=True)  # 价格竞争力评分 0-10

    # 统计数据
    total_accounts = Column(Integer, default=0)  # 总账户数
    active_accounts = Column(Integer, default=0)  # 活跃账户数
    dead_accounts = Column(Integer, default=0)  # 死亡账户数
    total_spend = Column(Numeric(15, 2), default=0)  # 总消耗金额

    # 管理信息
    notes = Column(Text, nullable=True)  # 备注
    created_by = Column(GUID(), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    creator = relationship("User")
    ad_accounts = relationship("AdAccount", back_populates="channel")
    channel_reviews = relationship("ChannelReview", back_populates="channel")


class ChannelReview(Base):
    """渠道评价表 - 记录渠道质量评价"""
    __tablename__ = "channel_reviews"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    channel_id = Column(GUID(), ForeignKey("channels.id"), nullable=False)

    # 评价信息
    reviewer_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    review_date = Column(DateTime, nullable=False)

    # 评分项目
    account_quality = Column(Integer, nullable=True)  # 账户质量评分 1-5
    delivery_speed = Column(Integer, nullable=True)  # 交付速度评分 1-5
    service_attitude = Column(Integer, nullable=True)  # 服务态度评分 1-5
    price_reasonable = Column(Integer, nullable=True)  # 价格合理性评分 1-5
    technical_support = Column(Integer, nullable=True)  # 技术支持评分 1-5

    # 总体评分
    overall_score = Column(Integer, nullable=True)  # 总体评分 1-5

    # 评价内容
    review_content = Column(Text, nullable=True)  # 评价内容
    pros = Column(Text, nullable=True)  # 优点
    cons = Column(Text, nullable=True)  # 缺点
    suggestions = Column(Text, nullable=True)  # 改进建议

    # 标签
    tags = Column(JSON, nullable=True)  # 标签列表

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    channel = relationship("Channel", back_populates="channel_reviews")
    reviewer = relationship("User")


class ChannelAccountRequest(Base):
    """渠道账户申请表 - 记录向渠道申请账户的记录"""
    __tablename__ = "channel_account_requests"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    channel_id = Column(GUID(), ForeignKey("channels.id"), nullable=False)
    project_id = Column(GUID(), ForeignKey("projects.id"), nullable=False)

    # 申请信息
    request_type = Column(String(20), nullable=False)  # new_account, additional_account, replacement
    account_type = Column(String(50), nullable=True)  # Facebook, Instagram, Google等
    quantity = Column(Integer, default=1)  # 申请数量
    required_by_date = Column(DateTime, nullable=True)  # 要求交付日期

    # 申请内容
    purpose = Column(Text, nullable=True)  # 用途说明
    special_requirements = Column(Text, nullable=True)  # 特殊要求

    # 申请状态
    status = Column(String(20), default="pending")  # pending, approved, rejected, delivered, cancelled
    approved_quantity = Column(Integer, nullable=True)  # 批准数量
    delivered_quantity = Column(Integer, nullable=True)  # 实际交付数量

    # 费用信息
    setup_fee_quoted = Column(Numeric(10, 2), nullable=True)  # 报价开户费
    actual_setup_fee = Column(Numeric(10, 2), nullable=True)  # 实际开户费

    # 处理记录
    approver_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    delivery_notes = Column(Text, nullable=True)

    # 申请信息
    requested_by = Column(GUID(), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    channel = relationship("Channel")
    project = relationship("Project")
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approver_id])


class ChannelPerformance(Base):
    """渠道表现表 - 统计渠道的表现数据"""
    __tablename__ = "channel_performance"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    channel_id = Column(GUID(), ForeignKey("channels.id"), nullable=False)

    # 统计周期
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly, quarterly
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # 账户统计
    new_accounts = Column(Integer, default=0)  # 新增账户
    active_accounts = Column(Integer, default=0)  # 活跃账户
    dead_accounts = Column(Integer, default=0)  # 死亡账户
    total_accounts = Column(Integer, default=0)  # 总账户数

    # 生存期统计
    avg_lifetime_days = Column(Integer, nullable=True)  # 平均生存天数
    survival_rate_7d = Column(Numeric(5, 4), nullable=True)  # 7天存活率
    survival_rate_30d = Column(Numeric(5, 4), nullable=True)  # 30天存活率

    # 财务统计
    total_spend = Column(Numeric(15, 2), default=0)  # 总消耗
    total_fee = Column(Numeric(15, 2), default=0)  # 总费用
    avg_fee_rate = Column(Numeric(5, 4), nullable=True)  # 平均费率

    # 质量指标
    account_quality_score = Column(Numeric(3, 2), nullable=True)  # 账户质量评分
    delivery_speed_hours = Column(Integer, nullable=True)  # 平均交付时间（小时）
    success_rate = Column(Numeric(5, 4), nullable=True)  # 成功率

    # 详细数据
    breakdown_data = Column(JSON, nullable=True)  # 详细分解数据

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    channel = relationship("Channel")


class ChannelContact(Base):
    """渠道联系人表 - 管理渠道的多个联系人"""
    __tablename__ = "channel_contacts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    channel_id = Column(GUID(), ForeignKey("channels.id"), nullable=False)

    # 联系人信息
    name = Column(String(255), nullable=False)
    position = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    wechat = Column(String(100), nullable=True)
    qq = Column(String(50), nullable=True)

    # 职责范围
    responsibilities = Column(Text, nullable=True)  # 职责说明
    primary_contact = Column(Boolean, default=False)  # 是否主要联系人

    # 沟通偏好
    preferred_contact_method = Column(String(20), default="email")  # email, phone, wechat
    contact_time_zone = Column(String(50), nullable=True)
    available_hours = Column(Text, nullable=True)  # 可联系时间

    # 状态
    status = Column(String(20), default="active")  # active, inactive, left

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    channel = relationship("Channel")