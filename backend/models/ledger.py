"""
财务流水和账本模块（对齐 LEDGER_SOT.md v1.1 + DATA_SCHEMA.md v5.2）

包含：
- LedgerTransaction: 财务交易记录
- AccountBalance: 账户余额快照
- BudgetAllocation: 项目预算分配
- TransactionType/TransactionStatus: 交易类型和状态枚举
- LedgerBookType/LedgerEntryType: 账本类型枚举

NOTE: LedgerEntry 模型定义在 backend/models/finance/ledger.py 中，
      由 backend/models/__init__.py 统一导出。
      本文件仅包含其他财务相关模型和枚举。

FK 类型对齐说明（DATA_SCHEMA.md v5.2）：
- project_id: BigInteger FK → projects.id (BIGSERIAL)
- ad_account_id: BigInteger FK → ad_accounts.id (BIGSERIAL)
- user_id (created_by): UUID FK → users.id (UUID)
"""

from enum import Enum as PyEnum
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Column, BigInteger, String, Text, Numeric, ForeignKey, DateTime, Index, Boolean, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base, TimestampMixin


# =====================================================================
# Enum 枚举定义 (对齐 LEDGER_SOT.md v1.1 第2.2节)
# =====================================================================

class LedgerBookType(str, PyEnum):
    """
    账本类型枚举（双账本隔离）

    必须与 LEDGER_SOT.md v1.1 第2.1节保持严格一致。
    - PROJECT: 项目账本（甲方视角，收入+充值）
    - SUPPLIER: 供应商账本（平台视角，成本+转账）
    """
    PROJECT = "PROJECT"      # 项目账本
    SUPPLIER = "SUPPLIER"    # 供应商账本


class LedgerEntryType(str, PyEnum):
    """
    账本分录类型枚举

    必须与 LEDGER_SOT.md v1.1 第2.2节保持严格一致。
    PROJECT账本: REVENUE, RECHARGE, REVERSAL
    SUPPLIER账本: COST, RECHARGE, TRANSFER_OUT, TRANSFER_IN, REVERSAL
    """
    # PROJECT 账本分录类型
    REVENUE = "REVENUE"              # 项目收入（基于 daily_reports 锁定后生成）
    RECHARGE = "RECHARGE"            # 项目充值（topup_requests 到账后生成）

    # SUPPLIER 账本分录类型
    COST = "COST"                    # 供应商成本（基于 daily_reports 锁定后生成）
    TRANSFER_OUT = "TRANSFER_OUT"    # 转出（SUPPLIER账本）
    TRANSFER_IN = "TRANSFER_IN"      # 转入（SUPPLIER账本）

    # 通用分录类型
    REVERSAL = "REVERSAL"            # 红冲（两账本通用，用于错误修正）


class TransactionType(str, PyEnum):
    """
    交易类型枚举

    定义财务交易的类型，对齐 LEDGER_SOT.md v1.1
    """
    TOPUP = "TOPUP"              # 充值
    SPEND = "SPEND"              # 消耗
    REFUND = "REFUND"            # 退款
    FEE = "FEE"                  # 手续费
    ADJUSTMENT = "ADJUSTMENT"    # 调整
    TRANSFER = "TRANSFER"        # 转账


class TransactionStatus(str, PyEnum):
    """
    交易状态枚举

    定义财务交易的处理状态
    """
    PENDING = "pending"          # 待处理
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 已取消


# =====================================================================
# Model 定义 (对齐 DATA_SCHEMA.md v5.2 + LEDGER_SOT.md v1.1)
# NOTE: LedgerEntry 定义在 backend/models/finance/ledger.py
# =====================================================================

class LedgerTransaction(Base, TimestampMixin):
    """
    财务交易记录表

    记录所有财务交易的详细信息，用于交易追踪和对账

    FK 类型对齐：
    - id: BIGSERIAL (BigInteger autoincrement)
    - project_id: BIGINT FK → projects.id
    - account_id: BIGINT FK → ad_accounts.id
    - topup_id: BIGINT FK → topup_requests.id
    """
    __tablename__ = "ledger_transactions"

    # 主键：BIGSERIAL
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="交易ID"
    )

    # 交易流水号
    transaction_number = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="交易流水号（格式：TXN{YYYYMMDD}{类型代码}{序号}）"
    )

    # 交易类型和状态
    transaction_type = Column(
        String(20),
        nullable=False,
        index=True,
        comment="交易类型：TOPUP/SPEND/REFUND/FEE/ADJUSTMENT/TRANSFER"
    )
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
        comment="交易状态：pending/processing/completed/failed/cancelled"
    )

    # 金额信息
    amount = Column(
        Numeric(15, 2),
        nullable=False,
        comment="交易金额"
    )
    currency = Column(
        String(10),
        nullable=False,
        default="USD",
        comment="货币类型"
    )

    # 关联信息 - FK 类型必须与 parent PK 一致
    project_id = Column(
        BigInteger,
        ForeignKey("projects.id"),
        nullable=True,
        index=True,
        comment="项目ID"
    )
    account_id = Column(
        BigInteger,
        ForeignKey("ad_accounts.id"),
        nullable=True,
        index=True,
        comment="广告账户ID"
    )
    topup_id = Column(
        BigInteger,
        ForeignKey("topup_requests.id"),
        nullable=True,
        comment="关联的充值申请ID"
    )

    # 关联业务ID（通用）
    reference_id = Column(
        String(100),
        nullable=True,
        comment="关联业务ID"
    )
    description = Column(
        Text,
        nullable=True,
        comment="交易描述"
    )

    # 元数据（JSON格式存储附加信息）
    transaction_metadata = Column(
        Text,
        nullable=True,
        comment="交易元数据（JSON格式）"
    )

    # 索引
    __table_args__ = (
        Index('idx_txn_number', 'transaction_number'),
        Index('idx_txn_type', 'transaction_type'),
        Index('idx_txn_status', 'status'),
        Index('idx_txn_project', 'project_id'),
        Index('idx_txn_account', 'account_id'),
        Index('idx_txn_created_at', 'created_at'),
        {'comment': '财务交易记录表'}
    )

    # 关系
    project = relationship("Project", foreign_keys=[project_id])
    account = relationship("AdAccount", foreign_keys=[account_id])


class AccountBalance(Base, TimestampMixin):
    """
    账户余额快照表

    记录账户/项目的余额快照，支持实时余额查询

    FK 类型对齐：
    - id: BIGSERIAL (BigInteger autoincrement)
    - account_id: BIGINT FK → ad_accounts.id
    - project_id: BIGINT FK → projects.id
    """
    __tablename__ = "account_balances"

    # 主键：BIGSERIAL
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="余额记录ID"
    )

    # 关联信息（账户或项目二选一）- FK 类型必须与 parent PK 一致
    account_id = Column(
        BigInteger,
        ForeignKey("ad_accounts.id"),
        nullable=True,
        index=True,
        comment="广告账户ID"
    )
    project_id = Column(
        BigInteger,
        ForeignKey("projects.id"),
        nullable=True,
        index=True,
        comment="项目ID"
    )

    # 余额信息
    currency = Column(
        String(10),
        nullable=False,
        default="USD",
        comment="货币类型"
    )
    current_balance = Column(
        Numeric(15, 2),
        nullable=False,
        default=0,
        comment="当前余额"
    )
    available_balance = Column(
        Numeric(15, 2),
        nullable=False,
        default=0,
        comment="可用余额"
    )
    frozen_balance = Column(
        Numeric(15, 2),
        nullable=False,
        default=0,
        comment="冻结余额"
    )

    # 累计统计
    total_credit = Column(
        Numeric(15, 2),
        nullable=False,
        default=0,
        comment="累计入账"
    )
    total_debit = Column(
        Numeric(15, 2),
        nullable=False,
        default=0,
        comment="累计出账"
    )

    # 索引
    __table_args__ = (
        Index('idx_balance_account', 'account_id'),
        Index('idx_balance_project', 'project_id'),
        Index('idx_balance_currency', 'currency'),
        {'comment': '账户余额快照表'}
    )

    # 关系
    account = relationship("AdAccount", foreign_keys=[account_id])
    project = relationship("Project", foreign_keys=[project_id])


class BudgetAllocation(Base, TimestampMixin):
    """
    项目预算分配表

    记录项目的预算分配和使用情况

    FK 类型对齐：
    - id: BIGSERIAL (BigInteger autoincrement)
    - project_id: BIGINT FK → projects.id
    """
    __tablename__ = "budget_allocations"

    # 主键：BIGSERIAL
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="预算分配ID"
    )

    # 关联信息 - FK 类型必须与 parent PK 一致
    project_id = Column(
        BigInteger,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
        comment="项目ID"
    )

    # 预算类别
    category = Column(
        String(50),
        nullable=False,
        index=True,
        comment="预算类别：ad_spend/operation/other"
    )

    # 预算金额
    allocated_amount = Column(
        Numeric(15, 2),
        nullable=False,
        comment="分配金额"
    )
    spent_amount = Column(
        Numeric(15, 2),
        nullable=False,
        default=0,
        comment="已使用金额"
    )
    remaining_amount = Column(
        Numeric(15, 2),
        nullable=False,
        comment="剩余金额"
    )

    # 使用率
    percentage_used = Column(
        Numeric(5, 2),
        nullable=False,
        default=0,
        comment="使用百分比"
    )

    # 状态
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否有效"
    )

    # 索引
    __table_args__ = (
        Index('idx_budget_project', 'project_id'),
        Index('idx_budget_category', 'category'),
        Index('idx_budget_active', 'is_active'),
        {'comment': '项目预算分配表'}
    )

    # 关系
    project = relationship("Project", foreign_keys=[project_id])
