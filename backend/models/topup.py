"""
充值管理数据库模型
Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DECIMAL, TIMESTAMP, ForeignKey, DATE, Index
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class TopupRequest(Base):
    """充值申请主表"""
    __tablename__ = "topup_requests"

    id = Column(Integer, primary_key=True, index=True)
    request_no = Column(String(50), unique=True, nullable=False, index=True, comment="申请单号")
    ad_account_id = Column(Integer, ForeignKey("ad_accounts.id"), nullable=False, comment="广告账户ID")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID")

    # 金额相关
    requested_amount = Column(DECIMAL(15, 2), nullable=False, comment="申请金额")
    actual_amount = Column(DECIMAL(15, 2), comment="实际打款金额")
    currency = Column(String(10), nullable=False, default="USD", comment="货币类型")

    # 申请信息
    urgency_level = Column(String(20), nullable=False, default="normal", comment="紧急程度")
    reason = Column(Text, nullable=False, comment="充值原因")
    notes = Column(Text, comment="补充说明")
    expected_date = Column(DATE, comment="期望到账日期")

    # 状态信息
    status = Column(String(20), nullable=False, default="pending", comment="申请状态")

    # 支付信息
    payment_method = Column(String(50), comment="打款方式")
    transaction_id = Column(String(100), comment="交易流水号")
    receipt_url = Column(String(500), comment="凭证URL")

    # 申请人信息
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="申请人ID")

    # 数据审核信息
    data_reviewed_by = Column(Integer, ForeignKey("users.id"), comment="数据审核人ID")
    data_reviewed_at = Column(TIMESTAMP, comment="数据审核时间")
    data_review_notes = Column(Text, comment="数据审核说明")

    # 财务审批信息
    finance_approved_by = Column(Integer, ForeignKey("users.id"), comment="财务审批人ID")
    finance_approved_at = Column(TIMESTAMP, comment="财务审批时间")
    finance_approve_notes = Column(Text, comment="财务审批说明")

    # 支付完成时间
    paid_at = Column(TIMESTAMP, comment="打款时间")
    completed_at = Column(TIMESTAMP, comment="完成时间")

    # 时间戳
    created_at = Column(TIMESTAMP, default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")

    # 关系
    ad_account = relationship("AdAccount", backref="topup_requests")
    project = relationship("Project", backref="topup_requests")
    requester = relationship("User", foreign_keys=[requested_by])
    data_reviewer = relationship("User", foreign_keys=[data_reviewed_by])
    finance_approver = relationship("User", foreign_keys=[finance_approved_by])
    transactions = relationship("TopupTransaction", back_populates="request")
    approval_logs = relationship("TopupApprovalLog", back_populates="request")

    # 索引
    __table_args__ = (
        Index('idx_topup_requests_account', 'ad_account_id'),
        Index('idx_topup_requests_project', 'project_id'),
        Index('idx_topup_requests_status', 'status'),
        Index('idx_topup_requests_requested_by', 'requested_by'),
        Index('idx_topup_requests_created_at', 'created_at'),
        Index('idx_topup_requests_urgency', 'urgency_level'),
        {'comment': '充值申请表'}
    )


class TopupTransaction(Base):
    """充值交易记录表（实际资金流水）"""
    __tablename__ = "topup_transactions"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("topup_requests.id"), nullable=False, comment="关联的申请ID")
    transaction_no = Column(String(100), unique=True, nullable=False, index=True, comment="交易号")

    # 交易信息
    amount = Column(DECIMAL(15, 2), nullable=False, comment="交易金额")
    currency = Column(String(10), nullable=False, default="USD", comment="货币类型")
    payment_method = Column(String(50), nullable=False, comment="支付方式")
    payment_account = Column(String(100), comment="付款账户")

    # 时间信息
    transaction_date = Column(TIMESTAMP, nullable=False, comment="交易时间")

    # 凭证信息
    receipt_file = Column(String(500), comment="凭证文件路径")
    notes = Column(Text, comment="备注")

    # 创建信息
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    created_at = Column(TIMESTAMP, default=func.now(), nullable=False, comment="创建时间")

    # 关系
    request = relationship("TopupRequest", back_populates="transactions")
    creator = relationship("User")

    # 索引
    __table_args__ = (
        Index('idx_topup_transactions_request', 'request_id'),
        Index('idx_topup_transactions_date', 'transaction_date'),
        {'comment': '充值交易记录表'}
    )


class TopupApprovalLog(Base):
    """充值审批日志表"""
    __tablename__ = "topup_approval_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("topup_requests.id"), nullable=False, comment="关联的申请ID")

    # 操作信息
    action = Column(String(50), nullable=False, comment="操作类型")
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="操作人ID")
    actor_role = Column(String(50), nullable=False, comment="操作人角色")
    notes = Column(Text, comment="操作说明")

    # 状态变更
    previous_status = Column(String(20), comment="原状态")
    new_status = Column(String(20), comment="新状态")

    # 请求信息
    ip_address = Column(INET, comment="IP地址")
    user_agent = Column(Text, comment="用户代理")

    # 时间
    created_at = Column(TIMESTAMP, default=func.now(), nullable=False, comment="创建时间")

    # 关系
    request = relationship("TopupRequest", back_populates="approval_logs")
    actor = relationship("User")

    # 索引
    __table_args__ = (
        Index('idx_topup_approval_logs_request', 'request_id'),
        Index('idx_topup_approval_logs_action', 'action'),
        Index('idx_topup_approval_logs_actor', 'actor_id'),
        {'comment': '充值审批日志表'}
    )


# 保持向后兼容的别名
Topup = TopupRequest