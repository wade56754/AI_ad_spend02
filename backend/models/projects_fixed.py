"""
项目管理模块（已对齐 DATA_SCHEMA.md v5.0）
包含项目、成员、费用等相关模型
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, BigInteger, String, Text, Numeric, Date, DateTime, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# ⚠️ 此文件中的导入路径已过时，请勿使用此文件中的 Project 类
# from backend.models.base import Base  # 已注释，避免错误的导入路径
from backend.models.base import Base  # 临时修复导入路径（但此类已废弃）


# ⚠️ DEPRECATED: 此 Project 类已被 backend/models/core/project.py 替代
# 请使用 from backend.models.core.project import Project
# 保留此类仅用于向后兼容，但已禁用表定义以避免重复注册
class _ProjectFixed(Base):
    """项目表 - 管理甲方项目信息（对齐 DATA_SCHEMA.md 3.2.1）（已废弃）"""
    # __tablename__ = "projects"  # 已注释掉，避免重复定义表
    __abstract__ = True  # 标记为抽象类，不会创建表

    # 主键：BIGSERIAL
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="项目ID")

    # 基本信息
    name = Column(String(200), nullable=False, index=True, comment="项目名称")
    client_name = Column(String(200), nullable=False, comment="客户联系人姓名")
    client_company = Column(String(200), nullable=False, comment="客户公司名称")
    description = Column(Text, nullable=True, comment="项目描述")

    # 项目状态（枚举值以 STATE_MACHINE.md 为准）
    status = Column(String(20), nullable=False, index=True, comment="项目状态")

    # 预算信息（字段名对齐 DATA_SCHEMA）
    budget_total = Column(Numeric(15, 2), default=Decimal('0.00'), comment="项目预算")
    budget_currency = Column(String(10), default='CNY', comment="货币类型")

    # 时间信息
    start_date = Column(Date, nullable=True, comment="项目开始日期")
    end_date = Column(Date, nullable=True, comment="项目结束日期")

    # 管理信息（外键指向 users.id，UUID）
    account_manager_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
        comment="项目经理ID"
    )
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="创建人ID"
    )
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="更新人ID"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )

    # 索引（对齐 DATA_SCHEMA 3.2.1）
    __table_args__ = (
        Index('idx_projects_name', 'name'),
        Index('idx_projects_status', 'status'),
        Index('idx_projects_account_manager', 'account_manager_id'),
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
    """
    项目成员关联表（已废弃 - DEPRECATED）

    ⚠️ 此类已被 backend.models.core.project_member.ProjectMember 替代
    请使用 from backend.models import ProjectMember

    保留此类仅用于向后兼容，但已标记为抽象类以避免重复注册表
    """
    __abstract__ = True  # 标记为抽象类，不会创建表
    # __tablename__ = "project_members"  # 已注释掉

    # 主键：BIGSERIAL
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="成员ID")
    
    # 外键：project_id 为 BIGINT，user_id 为 UUID
    project_id = Column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="项目ID"
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="用户ID"
    )
    role = Column(String(20), nullable=False, comment="项目内角色，与全局角色一致")
    permissions = Column(Text, nullable=True, comment="扩展权限（JSONB）")
    joined_at = Column(DateTime(timezone=True), server_default=func.now(),
        nullable=False,
        comment="加入时间"
    )
    notes = Column(Text, nullable=True, comment="备注")

    # 唯一约束和索引（对齐 DATA_SCHEMA 3.2.2）
    __table_args__ = (
        Index('uq_project_members_project_user', 'project_id', 'user_id', unique=True),
        {'comment': '项目成员关联表'}
    )

    # 关系
    project = relationship("Project", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])


class ProjectExpense(Base):
    """项目费用记录表（对齐 DATA_SCHEMA.md 3.2.3）"""
    __tablename__ = "project_expenses"

    # 主键：BIGSERIAL
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="费用ID")

    project_id = Column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="项目ID"
    )
    expense_type = Column(String(50), nullable=False, comment="费用类型")
    amount = Column(Numeric(15, 2), nullable=False, comment="金额")
    currency = Column(String(10), nullable=True, comment="货币类型")
    expense_date = Column(Date, nullable=False, comment="费用日期")
    description = Column(Text, nullable=True, comment="费用说明")
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="创建人ID"
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )

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



