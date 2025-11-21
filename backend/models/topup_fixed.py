"""
充值管理数据库模型（已对齐 DATA_SCHEMA.md v5.0）
Version: 2.0 - Schema Aligned
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, BigInteger, String, Text, Numeric, Date, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base


class TopupRequest(Base):
    """充值申请主表（对齐 DATA_SCHEMA.md 3.4.1）"""
    __tablename__ = "topup_requests"

    # 主键：BIGSERIAL
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="充值申请ID")
    
    # 申请单号
    request_no = Column(String(50), unique=True, nullable=False, index=True, comment="申请单号")
    
    # 关联信息
    project_id = Column(
        BigInteger,
        ForeignKey("projects.id"),
        nullable=False,
        comment="项目ID"
    )
    ad_account_id = Column(
        BigInteger,
        ForeignKey("ad_accounts.id"),
        nullable=True,  # 可空（对齐 DATA_SCHEMA）
        comment="广告账户ID"
    )
    
    # 申请人（字段名对齐 DATA_SCHEMA：applicant_id）
    applicant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="申请人ID"
    )
    
    # 金额信息（字段名对齐 DATA_SCHEMA：amount）
    amount = Column(Numeric(15, 2), nullable=False, comment="申请金额")
    currency = Column(String(10), nullable=False, default='CNY', comment="货币类型")
    
    # 紧急程度（固定枚举，非状态机）
    urgency_level = Column(
        String(20),
        nullable=False,
        default='normal',
        comment="紧急程度：low/normal/high/urgent"
    )
    
    # 状态信息（枚举值以 STATE_MACHINE.md 为准）
    status = Column(String(20), nullable=False, index=True, comment="申请状态")
    status_reason = Column(Text, nullable=True, comment="状态变更原因")
    
    # 期望到账日期（字段名对齐 DATA_SCHEMA：expected_pay_date）
    expected_pay_date = Column(Date, nullable=True, comment="期望到账日期")
    
    # 凭证URL（新增字段，对齐 DATA_SCHEMA）
    voucher_url = Column(Text, nullable=True, comment="凭证URL")
    
    # 备注
    notes = Column(Text, nullable=True, comment="补充说明")
    
    # 审计字段
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
        func.now(),
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )
    updated_at = Column(
        func.now(),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )

    # 索引（对齐 DATA_SCHEMA 3.4.1）
    __table_args__ = (
        Index('idx_topup_requests_project', 'project_id'),
        Index('idx_topup_requests_status', 'status'),
        Index('idx_topup_requests_applicant', 'applicant_id'),
        {'comment': '充值申请表'}
    )

    # 关系
    project = relationship("Project", backref="topup_requests")
    ad_account = relationship("AdAccount", backref="topup_requests")
    applicant = relationship("User", foreign_keys=[applicant_id])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    transactions = relationship("TopupTransaction", back_populates="request")
    approval_logs = relationship("TopupApprovalLog", back_populates="request")


class TopupTransaction(Base):
    """充值交易记录表（对齐 DATA_SCHEMA.md 3.4.2）"""
    __tablename__ = "topup_transactions"

    # 主键：BIGSERIAL
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="交易ID")
    
    # 关联申请
    topup_request_id = Column(
        BigInteger,
        ForeignKey("topup_requests.id"),
        nullable=False,
        comment="关联的申请ID"
    )
    
    # 交易信息（字段名对齐 DATA_SCHEMA）
    paid_amount = Column(Numeric(15, 2), nullable=False, comment="实际打款金额")
    paid_currency = Column(String(10), nullable=False, comment="货币类型")
    payment_method = Column(
        String(50),
        nullable=False,
        comment="支付方式：bank_transfer/alipay/wechat/paypal/credit_card/other"
    )
    payment_reference = Column(String(100), nullable=True, comment="支付参考号")
    
    # 时间信息
    paid_at = Column(
        func.now(),
        server_default=func.now(),
        nullable=False,
        comment="打款时间"
    )
    
    # 凭证信息
    receipt_url = Column(Text, nullable=True, comment="凭证URL")
    notes = Column(Text, nullable=True, comment="备注")
    
    # 创建信息
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="创建人ID"
    )
    created_at = Column(
        func.now(),
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )

    # 关系
    request = relationship("TopupRequest", back_populates="transactions")
    creator = relationship("User", foreign_keys=[created_by])

    # 索引
    __table_args__ = (
        Index('idx_topup_transactions_request', 'topup_request_id'),
        Index('idx_topup_transactions_paid_at', 'paid_at'),
        {'comment': '充值交易记录表'}
    )


class TopupApprovalLog(Base):
    """充值审批日志表（对齐 DATA_SCHEMA.md 3.4.3）"""
    __tablename__ = "topup_approval_logs"

    # 主键：BIGSERIAL
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="日志ID")
    
    # 关联申请
    topup_request_id = Column(
        BigInteger,
        ForeignKey("topup_requests.id"),
        nullable=False,
        comment="关联的申请ID"
    )
    
    # 操作信息（字段名对齐 DATA_SCHEMA）
    action = Column(String(50), nullable=False, comment="操作类型")
    from_status = Column(String(20), nullable=True, comment="原状态")
    to_status = Column(String(20), nullable=True, comment="新状态")
    operator_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="操作人ID"
    )
    comments = Column(Text, nullable=True, comment="操作说明")
    
    # 时间
    created_at = Column(
        func.now(),
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )

    # 关系
    request = relationship("TopupRequest", back_populates="approval_logs")
    operator = relationship("User", foreign_keys=[operator_id])

    # 索引
    __table_args__ = (
        Index('idx_topup_approval_logs_request', 'topup_request_id'),
        Index('idx_topup_approval_logs_action', 'action'),
        Index('idx_topup_approval_logs_operator', 'operator_id'),
        {'comment': '充值审批日志表'}
    )


# 保持向后兼容的别名
Topup = TopupRequest



