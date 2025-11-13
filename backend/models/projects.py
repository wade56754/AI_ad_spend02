"""
项目管理模块
包含项目、成员、费用等相关模型
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Numeric, Boolean, Integer, Date, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base
from models.user import User


class Project(Base):
    """项目表 - 管理甲方项目信息"""
    __tablename__ = "projects"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 基本信息
    name = Column(String(200), nullable=False, index=True, comment="项目名称")
    client_name = Column(String(200), nullable=False, comment="客户联系人姓名")
    client_company = Column(String(200), nullable=False, comment="客户公司名称")
    description = Column(Text, nullable=True, comment="项目描述")

    # 项目状态
    status = Column(String(20), default="planning", nullable=False, comment="项目状态", index=True)

    # 预算信息
    budget = Column(Numeric(15, 2), default=0.00, comment="项目预算")
    currency = Column(String(10), default="USD", comment="货币类型")

    # 时间信息
    start_date = Column(Date, nullable=True, comment="项目开始日期")
    end_date = Column(Date, nullable=True, comment="项目结束日期")

    # 管理信息
    account_manager_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="项目经理ID")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="更新人ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 索引
    __table_args__ = (
        Index('idx_projects_status', 'status'),
        Index('idx_projects_client', 'client_name'),
        Index('idx_projects_manager', 'account_manager_id'),
        Index('idx_projects_created_by', 'created_by'),
        Index('idx_projects_dates', 'start_date', 'end_date'),
        {'comment': '项目信息表'}
    )

    # 关系
    account_manager = relationship("User", foreign_keys=[account_manager_id])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    ad_accounts = relationship("AdAccount", back_populates="project")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    expenses = relationship("ProjectExpense", back_populates="project", cascade="all, delete-orphan")


class ProjectMember(Base):
    """项目成员关联表"""
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False, comment="角色：account_manager, media_buyer, analyst")
    joined_at = Column(DateTime, default=datetime.utcnow, comment="加入时间")

    # 唯一约束
    __table_args__ = (
        Index('uq_project_members', 'project_id', 'user_id', unique=True),
        Index('idx_project_members_project', 'project_id'),
        Index('idx_project_members_user', 'user_id'),
        {'comment': '项目成员关联表'}
    )

    # 关系
    project = relationship("Project", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])


class ProjectExpense(Base):
    """项目费用记录表"""
    __tablename__ = "project_expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    expense_type = Column(String(50), nullable=False, comment="费用类型：media_spend, service_fee, other")
    amount = Column(Numeric(15, 2), nullable=False, comment="金额")
    description = Column(Text, nullable=True, comment="费用说明")
    expense_date = Column(Date, nullable=False, comment="费用日期")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 索引
    __table_args__ = (
        Index('idx_expenses_project', 'project_id'),
        Index('idx_expenses_date', 'expense_date'),
        Index('idx_expenses_type', 'expense_type'),
        {'comment': '项目费用记录表'}
    )

    # 关系
    project = relationship("Project", back_populates="expenses")
    creator = relationship("User", foreign_keys=[created_by])


