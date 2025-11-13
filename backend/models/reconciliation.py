"""
对账管理数据模型
Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Boolean,
    Text, DECIMAL, ForeignKey, JSON, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class ReconciliationBatch(Base):
    """对账批次表"""
    __tablename__ = "reconciliation_batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_no = Column(String(50), unique=True, nullable=False, comment="对账批次号")
    reconciliation_date = Column(Date, nullable=False, comment="对账日期")
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        comment="对账状态"
    )

    # 统计信息
    total_accounts = Column(Integer, nullable=False, default=0, comment="总账户数")
    matched_accounts = Column(Integer, nullable=False, default=0, comment="匹配账户数")
    mismatched_accounts = Column(Integer, nullable=False, default=0, comment="差异账户数")

    # 金额统计
    total_platform_spend = Column(
        DECIMAL(15, 2),
        nullable=False,
        default=Decimal('0.00'),
        comment="平台总消耗"
    )
    total_internal_spend = Column(
        DECIMAL(15, 2),
        nullable=False,
        default=Decimal('0.00'),
        comment="内部总消耗"
    )
    total_difference = Column(
        DECIMAL(15, 2),
        nullable=False,
        default=Decimal('0.00'),
        comment="总差异金额"
    )

    # 效率统计
    auto_matched = Column(Integer, nullable=True, comment="自动匹配数")
    manual_reviewed = Column(Integer, nullable=True, comment="人工审核数")

    # 时间信息
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    created_by = Column(Integer, nullable=False, comment="创建人ID")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )
    notes = Column(Text, nullable=True, comment="备注说明")

    # 关联关系
    details = relationship(
        "ReconciliationDetail",
        back_populates="batch",
        cascade="all, delete-orphan"
    )
    adjustments = relationship(
        "ReconciliationAdjustment",
        back_populates="batch",
        cascade="all, delete-orphan"
    )
    reports = relationship(
        "ReconciliationReport",
        back_populates="batch",
        cascade="all, delete-orphan"
    )

    # 约束
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'exception', 'resolved')",
            name="check_batch_status"
        ),
        CheckConstraint(
            "total_accounts >= 0",
            name="check_total_accounts_non_negative"
        ),
        CheckConstraint(
            "matched_accounts >= 0",
            name="check_matched_accounts_non_negative"
        ),
        CheckConstraint(
            "mismatched_accounts >= 0",
            name="check_mismatched_accounts_non_negative"
        ),
        CheckConstraint(
            "auto_matched >= 0",
            name="check_auto_matched_non_negative"
        ),
        CheckConstraint(
            "manual_reviewed >= 0",
            name="check_manual_reviewed_non_negative"
        ),
        Index("idx_reconciliation_batches_date", "reconciliation_date"),
        Index("idx_reconciliation_batches_status", "status"),
        Index("idx_reconciliation_batches_created_at", "created_at"),
        {"comment": "对账批次表"}
    )


class ReconciliationDetail(Base):
    """对账详情表"""
    __tablename__ = "reconciliation_details"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(
        Integer,
        ForeignKey("reconciliation_batches.id", ondelete="CASCADE"),
        nullable=False,
        comment="对账批次ID"
    )
    ad_account_id = Column(
        Integer,
        ForeignKey("ad_accounts.id"),
        nullable=False,
        comment="广告账户ID"
    )
    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        comment="项目ID"
    )
    channel_id = Column(
        Integer,
        ForeignKey("channels.id"),
        nullable=False,
        comment="渠道ID"
    )

    # 平台数据
    platform_spend = Column(
        DECIMAL(15, 2),
        nullable=False,
        default=Decimal('0.00'),
        comment="平台消耗"
    )
    platform_currency = Column(
        String(10),
        nullable=False,
        default="USD",
        comment="平台货币"
    )
    platform_data_date = Column(Date, nullable=True, comment="平台数据日期")

    # 内部数据
    internal_spend = Column(
        DECIMAL(15, 2),
        nullable=False,
        default=Decimal('0.00'),
        comment="内部消耗"
    )
    internal_currency = Column(
        String(10),
        nullable=False,
        default="USD",
        comment="内部货币"
    )
    internal_data_date = Column(Date, nullable=True, comment="内部数据日期")

    # 差异信息
    spend_difference = Column(
        DECIMAL(15, 2),
        nullable=False,
        default=Decimal('0.00'),
        comment="消耗差异"
    )
    exchange_rate = Column(
        DECIMAL(10, 4),
        nullable=False,
        default=Decimal('1.0000'),
        comment="汇率"
    )
    is_matched = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否匹配"
    )
    match_status = Column(
        String(20),
        nullable=False,
        default="pending",
        comment="匹配状态"
    )

    # 差异原因
    difference_type = Column(String(50), nullable=True, comment="差异类型")
    difference_reason = Column(Text, nullable=True, comment="差异原因描述")
    auto_confidence = Column(
        DECIMAL(3, 2),
        nullable=False,
        default=Decimal('0.00'),
        comment="自动匹配置信度"
    )

    # 处理信息
    reviewed_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="审核人ID"
    )
    reviewed_at = Column(DateTime, nullable=True, comment="审核时间")
    review_notes = Column(Text, nullable=True, comment="审核说明")
    resolved_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="处理人ID"
    )
    resolved_at = Column(DateTime, nullable=True, comment="处理时间")
    resolution_method = Column(String(50), nullable=True, comment="处理方法")
    resolution_notes = Column(Text, nullable=True, comment="处理说明")

    # 时间戳
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )

    # 关联关系
    batch = relationship("ReconciliationBatch", back_populates="details")
    ad_account = relationship("AdAccount")
    project = relationship("Project")
    channel = relationship("Channel")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    resolver = relationship("User", foreign_keys=[resolved_by])
    adjustments = relationship(
        "ReconciliationAdjustment",
        back_populates="detail",
        cascade="all, delete-orphan"
    )

    # 约束
    __table_args__ = (
        CheckConstraint(
            "match_status IN ('pending', 'matched', 'auto_matched', 'manual_review', 'exception', 'resolved')",
            name="check_match_status"
        ),
        CheckConstraint(
            "auto_confidence >= 0 AND auto_confidence <= 1",
            name="check_auto_confidence_range"
        ),
        Index("idx_reconciliation_details_batch", "batch_id"),
        Index("idx_reconciliation_details_account", "ad_account_id"),
        Index("idx_reconciliation_details_status", "match_status"),
        Index("idx_reconciliation_details_date", "platform_data_date"),
        {"comment": "对账详情表"}
    )


class ReconciliationAdjustment(Base):
    """对账调整记录表"""
    __tablename__ = "reconciliation_adjustments"

    id = Column(Integer, primary_key=True, index=True)
    detail_id = Column(
        Integer,
        ForeignKey("reconciliation_details.id", ondelete="CASCADE"),
        nullable=False,
        comment="对账详情ID"
    )
    batch_id = Column(
        Integer,
        ForeignKey("reconciliation_batches.id", ondelete="CASCADE"),
        nullable=False,
        comment="对账批次ID"
    )

    # 调整信息
    adjustment_type = Column(
        String(50),
        nullable=False,
        comment="调整类型"
    )
    original_amount = Column(
        DECIMAL(15, 2),
        nullable=False,
        comment="原始金额"
    )
    adjustment_amount = Column(
        DECIMAL(15, 2),
        nullable=False,
        comment="调整金额"
    )
    adjusted_amount = Column(
        DECIMAL(15, 2),
        nullable=False,
        comment="调整后金额"
    )

    # 调整原因
    adjustment_reason = Column(
        String(100),
        nullable=False,
        comment="调整原因"
    )
    detailed_reason = Column(
        Text,
        nullable=False,
        comment="详细原因说明"
    )
    evidence_url = Column(String(500), nullable=True, comment="证据文件URL")

    # 审批信息
    approved_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="审批人ID"
    )
    approved_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="审批时间"
    )
    finance_approve = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="财务确认"
    )
    finance_approved_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="财务审批人ID"
    )
    finance_approved_at = Column(DateTime, nullable=True, comment="财务审批时间")

    # 时间戳
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )
    notes = Column(Text, nullable=True, comment="备注")

    # 关联关系
    detail = relationship("ReconciliationDetail", back_populates="adjustments")
    batch = relationship("ReconciliationBatch", back_populates="adjustments")
    approver = relationship("User", foreign_keys=[approved_by])
    finance_approver = relationship("User", foreign_keys=[finance_approved_by])

    # 约束
    __table_args__ = (
        CheckConstraint(
            "adjustment_type IN ('spend_adjustment', 'date_adjustment')",
            name="check_adjustment_type"
        ),
        Index("idx_reconciliation_adjustments_detail", "detail_id"),
        Index("idx_reconciliation_adjustments_batch", "batch_id"),
        Index("idx_reconciliation_adjustments_type", "adjustment_type"),
        {"comment": "对账调整记录表"}
    )


class ReconciliationReport(Base):
    """对账报告表"""
    __tablename__ = "reconciliation_reports"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(
        Integer,
        ForeignKey("reconciliation_batches.id"),
        nullable=True,
        comment="对账批次ID"
    )
    report_type = Column(
        String(50),
        nullable=False,
        comment="报告类型"
    )
    report_period_start = Column(Date, nullable=False, comment="报告开始日期")
    report_period_end = Column(Date, nullable=False, comment="报告结束日期")

    # 报告内容
    report_data = Column(JSON, nullable=False, comment="报告数据")
    chart_data = Column(JSON, nullable=True, comment="图表数据")
    summary_data = Column(JSON, nullable=False, comment="摘要数据")

    # 生成信息
    generated_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="生成人ID"
    )
    generated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="生成时间"
    )
    file_path = Column(String(500), nullable=True, comment="报告文件路径")
    file_size = Column(Integer, nullable=True, comment="文件大小（字节）")

    # 时间戳
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="创建时间"
    )

    # 关联关系
    batch = relationship("ReconciliationBatch", back_populates="reports")
    generator = relationship("User")

    # 约束
    __table_args__ = (
        CheckConstraint(
            "report_type IN ('daily', 'weekly', 'monthly')",
            name="check_report_type"
        ),
        CheckConstraint(
            "report_period_end >= report_period_start",
            name="check_report_period_valid"
        ),
        Index("idx_reconciliation_reports_batch", "batch_id"),
        Index("idx_reconciliation_reports_type", "report_type"),
        Index("idx_reconciliation_reports_period", "report_period_start"),
        {"comment": "对账报告表"}
    )

