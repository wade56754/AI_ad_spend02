"""
项目管理模块
包含项目、客户、收费模式等相关模型
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Numeric, Boolean, Integer, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.core.db import Base
from backend.models.ad_spend_daily import GUID


class Project(Base):
    """项目表 - 管理甲方项目信息"""
    __tablename__ = "projects"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)  # 项目编码
    description = Column(Text, nullable=True)

    # 客户信息
    client_name = Column(String(255), nullable=False)
    client_contact = Column(String(255), nullable=True)
    client_email = Column(String(255), nullable=True)
    client_phone = Column(String(50), nullable=True)

    # 收费模式
    pricing_model = Column(String(50), nullable=False, default="per_lead")  # per_lead, fixed_fee, hybrid
    lead_price = Column(Numeric(10, 2), nullable=False)  # 每个潜在客户价格
    setup_fee = Column(Numeric(10, 2), default=0)  # 项目启动费
    currency = Column(String(3), default="USD")  # 货币单位

    # 项目状态
    status = Column(String(20), nullable=False, default="planning")  # planning, active, paused, completed, cancelled
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    # 预算和限制
    monthly_budget = Column(Numeric(12, 2), nullable=True)  # 月度预算
    total_budget = Column(Numeric(15, 2), nullable=True)  # 总预算

    # 目标设置
    monthly_target_leads = Column(Integer, default=0)  # 月度目标潜在客户数
    target_cpl = Column(Numeric(10, 2), nullable=True)  # 目标单粉成本

    # 管理信息
    manager_id = Column(GUID(), ForeignKey("users.id"), nullable=True)  # 项目经理
    created_by = Column(GUID(), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    manager = relationship("User", foreign_keys=[manager_id], lazy="joined")
    creator = relationship("User", foreign_keys=[created_by])
    ad_accounts = relationship("AdAccount", back_populates="project")
    topups = relationship("Topup", back_populates="project")


class Contract(Base):
    """合同表 - 管理客户合同信息"""
    __tablename__ = "contracts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    project_id = Column(GUID(), ForeignKey("projects.id"), nullable=False)
    contract_number = Column(String(100), unique=True, nullable=False)
    contract_name = Column(String(255), nullable=False)

    # 合同条款
    lead_price = Column(Numeric(10, 2), nullable=False)  # 合同约定的单粉价格
    setup_fee = Column(Numeric(10, 2), default=0)
    billing_cycle = Column(String(20), default="monthly")  # monthly, weekly, daily

    # 合同期限
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # 合同状态
    status = Column(String(20), default="draft")  # draft, active, expired, terminated

    # 附加条款
    terms = Column(Text, nullable=True)
    special_requirements = Column(Text, nullable=True)

    # 管理信息
    created_by = Column(GUID(), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    project = relationship("Project", back_populates="contracts")
    creator = relationship("User")


class ProjectTarget(Base):
    """项目目标表 - 管理项目KPI目标"""
    __tablename__ = "project_targets"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    project_id = Column(GUID(), ForeignKey("projects.id"), nullable=False)

    # 目标类型
    target_type = Column(String(50), nullable=False)  # leads_count, cpl, spend, roi
    target_value = Column(Numeric(15, 2), nullable=False)

    # 时间范围
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly, quarterly
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # 目标状态
    status = Column(String(20), default="active")  # active, achieved, failed, cancelled

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    project = relationship("Project")


class ProjectMetrics(Base):
    """项目指标表 - 记录项目实际完成情况"""
    __tablename__ = "project_metrics"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    project_id = Column(GUID(), ForeignKey("projects.id"), nullable=False)

    # 指标类型
    metric_type = Column(String(50), nullable=False)  # leads_count, cpl, spend, revenue, profit

    # 时间范围
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # 实际值
    actual_value = Column(Numeric(15, 2), nullable=False)

    # 对比信息
    target_value = Column(Numeric(15, 2), nullable=True)  # 目标值
    achievement_rate = Column(Numeric(5, 2), nullable=True)  # 达成率

    # 详细数据
    breakdown_data = Column(JSON, nullable=True)  # 详细分解数据

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    project = relationship("Project")


# 为Project模型添加contracts关系
Project.contracts = relationship("Contract", back_populates="project", order_by="Contract.created_at.desc()")