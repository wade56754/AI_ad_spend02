"""
Reconciliation Issue Model

OpenSpec Change: add-reconciliation-control-center
SoT Reference: DATA_SCHEMA.md v5.4 §3.5.6
State Machine: STATE_MACHINE.md §11.4 对账差异单状态机
"""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Any
from uuid import UUID

from sqlalchemy import (
    BigInteger, String, Date, DateTime, Text, Numeric, Boolean,
    ForeignKey, CheckConstraint, Computed
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


class IssueType(str, Enum):
    """差异类型"""
    TOPUP_MISMATCH = "topup_mismatch"           # 充值差异
    SPEND_MISMATCH = "spend_mismatch"           # 消耗差异
    DEPOSIT_CHANGE = "deposit_change"           # 押款变化
    BALANCE_ANOMALY = "balance_anomaly"         # 余额异常
    SNAPSHOT_MISSING = "snapshot_missing"       # 快照缺失
    CONSERVATION_FAILED = "conservation_failed" # 守恒校验失败
    OTHER = "other"                             # 其他


class IssueStatus(str, Enum):
    """
    差异单状态

    状态机流转白名单:
    - open -> assigned
    - assigned -> investigating
    - investigating -> resolved, assigned
    - resolved -> closed, investigating
    - closed (终态)
    """
    OPEN = "open"                   # 待处理（初始态）
    ASSIGNED = "assigned"           # 已分配
    INVESTIGATING = "investigating" # 调查中
    RESOLVED = "resolved"           # 已处理
    CLOSED = "closed"               # 已关闭（终态）


class ResolutionType(str, Enum):
    """处理类型"""
    DATA_CORRECTION = "data_correction"     # 数据修正
    LEDGER_ADJUSTMENT = "ledger_adjustment" # 账本调整
    EXTERNAL_CONFIRM = "external_confirm"   # 外部确认（代理商/甲方）
    WRITE_OFF = "write_off"                 # 核销
    FALSE_POSITIVE = "false_positive"       # 误报


# 状态流转白名单
ISSUE_STATUS_TRANSITIONS = {
    IssueStatus.OPEN: [IssueStatus.ASSIGNED],
    IssueStatus.ASSIGNED: [IssueStatus.INVESTIGATING],
    IssueStatus.INVESTIGATING: [IssueStatus.RESOLVED, IssueStatus.ASSIGNED],
    IssueStatus.RESOLVED: [IssueStatus.CLOSED, IssueStatus.INVESTIGATING],
    IssueStatus.CLOSED: [],  # 终态
}


class ReconciliationIssue(Base):
    """
    对账差异单表

    追踪对账发现的差异及其处理过程。

    SoT Reference: DATA_SCHEMA.md v5.4 §3.5.6
    State Machine: STATE_MACHINE.md §11.4
    Business Rules: BR-REC-001, BR-REC-002, BR-REC-003, BR-REC-004
    Error Codes: REC_001 ~ REC_006
    """
    __tablename__ = "reconciliation_issues"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    reconciliation_batch_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("reconciliation_batches.id"), nullable=True)
    ad_account_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ad_accounts.id"), nullable=True)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False, comment="差异日期")
    issue_type: Mapped[str] = mapped_column(String(30), nullable=False, comment="差异类型")
    expected_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True, comment="预期金额")
    actual_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True, comment="实际金额")
    difference_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        Computed("COALESCE(actual_amount, 0) - COALESCE(expected_amount, 0)"),
        comment="差异金额"
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", comment="状态")
    assigned_to: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, comment="处理类型")
    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="处理说明")
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    attachments: Mapped[Optional[list[Any]]] = mapped_column(JSONB, default=list, comment="附件")
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default="NOW()")
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default="NOW()", onupdate=datetime.utcnow)
    sla_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, comment="SLA 截止时间")
    sla_breached: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, comment="SLA 超时标记")

    # Relationships
    reconciliation_batch = relationship("ReconciliationBatch", back_populates="issues")
    ad_account = relationship("AdAccount", back_populates="reconciliation_issues")
    assignee = relationship("User", foreign_keys=[assigned_to])
    resolver = relationship("User", foreign_keys=[resolved_by])
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        CheckConstraint(
            "issue_type IN ('topup_mismatch', 'spend_mismatch', 'deposit_change', 'balance_anomaly', 'snapshot_missing', 'conservation_failed', 'other')",
            name="chk_rec_issues_issue_type"
        ),
        CheckConstraint(
            "status IN ('open', 'assigned', 'investigating', 'resolved', 'closed')",
            name="chk_rec_issues_status"
        ),
        CheckConstraint(
            "resolution_type IS NULL OR resolution_type IN ('data_correction', 'ledger_adjustment', 'external_confirm', 'write_off', 'false_positive')",
            name="chk_rec_issues_resolution_type"
        ),
    )

    def can_transition_to(self, target_status: IssueStatus) -> bool:
        """检查是否可以转换到目标状态"""
        current = IssueStatus(self.status)
        allowed = ISSUE_STATUS_TRANSITIONS.get(current, [])
        return target_status in allowed

    def is_terminal(self) -> bool:
        """检查是否处于终态"""
        return self.status == IssueStatus.CLOSED.value

    def __repr__(self) -> str:
        return f"<ReconciliationIssue(id={self.id}, type='{self.issue_type}', status='{self.status}')>"
