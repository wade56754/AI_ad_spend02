"""
统一状态机模块

参考: STATE_MACHINE.md v2.6
参考: Saleor OrderStatus 设计
"""

from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass


class DailyReportStatus(str, Enum):
    """日报 8 状态机 (STATE_MACHINE.md v2.6 §8)"""
    RAW_SUBMITTED = "raw_submitted"
    TREND_PENDING = "trend_pending"
    TREND_OK = "trend_ok"
    TREND_FLAGGED = "trend_flagged"
    TREND_RESOLVED = "trend_resolved"
    FINAL_PENDING = "final_pending"
    FINAL_CONFIRMED = "final_confirmed"
    FINAL_LOCKED = "final_locked"


class TopupStatus(str, Enum):
    """充值状态机 (STATE_MACHINE.md v2.6 §9)"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    FINANCE_APPROVE = "finance_approve"
    PAID = "paid"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class TransferStatus(str, Enum):
    """转账状态机 (STATE_MACHINE.md v2.6 §12)"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class ReconciliationBatchStatus(str, Enum):
    """对账批次状态机 (STATE_MACHINE.md v2.6 §11.1)"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    NEEDS_ADJUSTMENT = "needs_adjustment"
    COMPLETED = "completed"


class ReconciliationDetailStatus(str, Enum):
    """对账明细状态机 (STATE_MACHINE.md v2.6 §11.2)"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ADJUSTED = "adjusted"


class AdAccountStatus(str, Enum):
    """广告账户状态机 (STATE_MACHINE.md v2.6 §7.1)"""
    NEW = "new"
    TESTING = "testing"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEAD = "dead"
    ARCHIVED = "archived"


class ProjectStatus(str, Enum):
    """项目状态机 (STATE_MACHINE.md v2.6 §5)"""
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


@dataclass
class Transition:
    """状态转换定义"""
    from_state: Enum
    to_state: Enum
    required_roles: Optional[List[str]] = None
    guard: Optional[Callable[[Any], bool]] = None
    action: Optional[Callable[[Any], None]] = None


class StateTransitionError(Exception):
    """状态转换错误"""
    def __init__(self, current_state: str, target_state: str, reason: str = None):
        self.current_state = current_state
        self.target_state = target_state
        self.reason = reason or "不允许的状态转换"
        super().__init__(f"无法从 {current_state} 转换到 {target_state}: {self.reason}")


class StateMachine:
    """通用状态机"""

    def __init__(self, transitions: List[Transition]):
        self._transitions: Dict[tuple, Transition] = {}
        for t in transitions:
            key = (t.from_state.value, t.to_state.value)
            self._transitions[key] = t

    def can_transition(self, from_state: str, to_state: str) -> bool:
        """检查是否可以转换"""
        return (from_state, to_state) in self._transitions

    def get_allowed_transitions(self, current_state: str) -> List[str]:
        """获取允许的目标状态"""
        return [
            to_state for (f, to_state) in self._transitions.keys()
            if f == current_state
        ]

    def transition(
        self,
        entity: Any,
        from_state: str,
        to_state: str,
        user_role: Optional[str] = None,
    ) -> None:
        """执行状态转换"""
        key = (from_state, to_state)
        if key not in self._transitions:
            raise StateTransitionError(from_state, to_state)

        t = self._transitions[key]

        if t.required_roles and user_role not in t.required_roles:
            raise StateTransitionError(
                from_state, to_state,
                f"需要角色 {t.required_roles}, 当前角色 {user_role}"
            )

        if t.guard and not t.guard(entity):
            raise StateTransitionError(from_state, to_state, "前置条件不满足")

        entity.status = to_state

        if t.action:
            t.action(entity)


# 预定义状态机: 日报
DAILY_REPORT_STATE_MACHINE = StateMachine([
    Transition(DailyReportStatus.RAW_SUBMITTED, DailyReportStatus.TREND_PENDING),
    Transition(DailyReportStatus.TREND_PENDING, DailyReportStatus.TREND_OK),
    Transition(DailyReportStatus.TREND_PENDING, DailyReportStatus.TREND_FLAGGED),
    Transition(DailyReportStatus.TREND_OK, DailyReportStatus.FINAL_PENDING, required_roles=["data_operator", "admin"]),
    Transition(DailyReportStatus.TREND_FLAGGED, DailyReportStatus.TREND_RESOLVED, required_roles=["data_operator", "admin"]),
    Transition(DailyReportStatus.TREND_FLAGGED, DailyReportStatus.RAW_SUBMITTED, required_roles=["data_operator", "admin"]),
    Transition(DailyReportStatus.TREND_RESOLVED, DailyReportStatus.FINAL_PENDING, required_roles=["data_operator", "admin"]),
    Transition(DailyReportStatus.FINAL_PENDING, DailyReportStatus.FINAL_CONFIRMED, required_roles=["data_operator", "admin"]),
    Transition(DailyReportStatus.FINAL_CONFIRMED, DailyReportStatus.FINAL_LOCKED),
])


# 预定义状态机: 充值
TOPUP_STATE_MACHINE = StateMachine([
    Transition(TopupStatus.DRAFT, TopupStatus.PENDING_REVIEW, required_roles=["media_buyer", "account_manager"]),
    Transition(TopupStatus.PENDING_REVIEW, TopupStatus.FINANCE_APPROVE, required_roles=["data_operator"]),
    Transition(TopupStatus.PENDING_REVIEW, TopupStatus.REJECTED, required_roles=["data_operator"]),
    Transition(TopupStatus.FINANCE_APPROVE, TopupStatus.PAID, required_roles=["finance"]),
    Transition(TopupStatus.FINANCE_APPROVE, TopupStatus.REJECTED, required_roles=["finance"]),
    Transition(TopupStatus.PAID, TopupStatus.COMPLETED, required_roles=["finance"]),
    Transition(TopupStatus.DRAFT, TopupStatus.CANCELLED),
    Transition(TopupStatus.PENDING_REVIEW, TopupStatus.CANCELLED),  # 申请人可在审核前取消
])


# 预定义状态机: 转账
TRANSFER_STATE_MACHINE = StateMachine([
    Transition(TransferStatus.DRAFT, TransferStatus.PENDING_APPROVAL, required_roles=["media_buyer", "account_manager"]),
    Transition(TransferStatus.DRAFT, TransferStatus.REJECTED, required_roles=["finance", "admin"]),  # 草稿阶段可直接拒绝
    Transition(TransferStatus.PENDING_APPROVAL, TransferStatus.APPROVED, required_roles=["finance", "admin"]),
    Transition(TransferStatus.PENDING_APPROVAL, TransferStatus.REJECTED, required_roles=["finance", "admin"]),
    Transition(TransferStatus.APPROVED, TransferStatus.COMPLETED, required_roles=["finance", "admin"]),
])


# 预定义状态机: 对账批次
RECONCILIATION_BATCH_STATE_MACHINE = StateMachine([
    Transition(ReconciliationBatchStatus.DRAFT, ReconciliationBatchStatus.PENDING_REVIEW, required_roles=["finance", "data_operator"]),
    Transition(ReconciliationBatchStatus.PENDING_REVIEW, ReconciliationBatchStatus.APPROVED, required_roles=["finance", "admin"]),
    Transition(ReconciliationBatchStatus.PENDING_REVIEW, ReconciliationBatchStatus.NEEDS_ADJUSTMENT, required_roles=["finance", "admin"]),
    Transition(ReconciliationBatchStatus.NEEDS_ADJUSTMENT, ReconciliationBatchStatus.PENDING_REVIEW, required_roles=["finance", "data_operator"]),  # 重新提交
    Transition(ReconciliationBatchStatus.NEEDS_ADJUSTMENT, ReconciliationBatchStatus.APPROVED, required_roles=["finance", "admin"]),
    Transition(ReconciliationBatchStatus.APPROVED, ReconciliationBatchStatus.COMPLETED, required_roles=["finance", "admin"]),
])


# 预定义状态机: 对账明细
RECONCILIATION_DETAIL_STATE_MACHINE = StateMachine([
    Transition(ReconciliationDetailStatus.PENDING, ReconciliationDetailStatus.CONFIRMED, required_roles=["finance", "data_operator"]),
    Transition(ReconciliationDetailStatus.PENDING, ReconciliationDetailStatus.ADJUSTED, required_roles=["finance", "data_operator"]),
    Transition(ReconciliationDetailStatus.CONFIRMED, ReconciliationDetailStatus.ADJUSTED, required_roles=["finance", "admin"]),  # 已确认可调整
    Transition(ReconciliationDetailStatus.ADJUSTED, ReconciliationDetailStatus.CONFIRMED, required_roles=["finance", "admin"]),  # 调整后可重新确认
])
