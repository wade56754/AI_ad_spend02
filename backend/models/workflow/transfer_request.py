"""
死号余额迁移申请数据模型
Version: 1.0
Author: Claude协作开发

SoT References:
- docs/sot/STATE_MACHINE.md v2.6 第12章 (transfer_requests 状态机)
- docs/sot/DATA_SCHEMA.md v5.2 第3.4.6节 (transfer_requests 表结构)
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, BigInteger, String, Text, Numeric, Integer,
    ForeignKey, DateTime, Index, text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base
from backend.models.enums import TransferRequestStatus


class TransferRequest(Base):
    """
    死号余额迁移申请表 (对齐 DATA_SCHEMA.md v5.2 第3.4.6节)

    状态机 (STATE_MACHINE.md v2.6 第12章):
    - draft: 草稿
    - pending_approval: 待审批
    - approved: 已审批
    - rejected: 已拒绝（终态）
    - completed: 已完成（终态）

    状态流转白名单:
    - draft → pending_approval, rejected
    - pending_approval → approved, rejected
    - approved → completed
    - rejected → [] (终态)
    - completed → [] (终态)
    """
    __tablename__ = "transfer_requests"

    # 主键：BIGSERIAL
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="迁移申请唯一标识")

    # 申请单号
    request_no = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="迁移申请编号"
    )

    # 源账户（死号）
    source_ad_account_id = Column(
        BigInteger,
        ForeignKey("ad_accounts.id"),
        nullable=False,
        index=True,
        comment="源账户(死号)"
    )

    # 目标账户（接收方）
    target_ad_account_id = Column(
        BigInteger,
        ForeignKey("ad_accounts.id"),
        nullable=False,
        index=True,
        comment="目标账户(接收方)"
    )

    # 迁移金额
    transfer_amount = Column(
        Numeric(15, 2),
        nullable=False,
        comment="迁移金额"
    )

    # 状态 (枚举值以 STATE_MACHINE.md v2.6 第12章为准)
    status = Column(
        String(20),
        nullable=False,
        default=TransferRequestStatus.DRAFT.value,
        index=True,
        comment="迁移状态: draft/pending_approval/approved/rejected/completed"
    )

    # 乐观锁版本号
    version = Column(
        Integer,
        nullable=False,
        default=1,
        comment="乐观锁版本号"
    )

    # 原因/备注
    reason = Column(Text, nullable=True, comment="迁移原因")
    approval_notes = Column(Text, nullable=True, comment="审批意见")
    rejection_reason = Column(Text, nullable=True, comment="拒绝原因")

    # 申请人
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="申请人"
    )

    # 审批人
    approved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="审批人"
    )

    # 时间戳
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
    approved_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="审批时间"
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="完成时间"
    )

    # 关系
    source_ad_account = relationship(
        "AdAccount",
        foreign_keys=[source_ad_account_id],
        backref="transfer_out_requests"
    )
    target_ad_account = relationship(
        "AdAccount",
        foreign_keys=[target_ad_account_id],
        backref="transfer_in_requests"
    )
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        backref="created_transfers"
    )
    approver = relationship(
        "User",
        foreign_keys=[approved_by],
        backref="approved_transfers"
    )

    # 索引 (对齐 DATA_SCHEMA.md)
    __table_args__ = (
        Index('idx_transfer_requests_request_no', 'request_no'),
        Index('idx_transfer_requests_source_account', 'source_ad_account_id'),
        Index('idx_transfer_requests_target_account', 'target_ad_account_id'),
        Index('idx_transfer_requests_status', 'status'),
        {'comment': '死号余额迁移申请表'}
    )

    def __repr__(self):
        return f"<TransferRequest(id={self.id}, request_no={self.request_no}, status={self.status})>"
