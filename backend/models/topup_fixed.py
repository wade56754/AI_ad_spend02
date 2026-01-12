"""
充值管理辅助表模型（已对齐 DATA_SCHEMA.md v5.2）
Version: 2.1 - Fixed SQLAlchemy syntax

仅包含 TopupTransaction 和 TopupApprovalLog。
TopupRequest 定义在 backend/models/workflow/topup_request.py 中。

⚠️ 注意：此文件名为 `topup_fixed.py`，但包含的是当前正在使用的模型类。
这些类（TopupTransaction, TopupApprovalLog）正在被以下模块使用：
- backend/services/topup_service.py
- backend/models/__init__.py
- backend/tests/test_topup_service.py

未来重构建议：将此文件重命名为 `topup_transaction.py` 或移动到 `backend/models/workflow/` 目录。
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, BigInteger, String, Text, Numeric, DateTime, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base


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
        DateTime(timezone=True),
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
        DateTime(timezone=True),
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
        DateTime(timezone=True),
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
