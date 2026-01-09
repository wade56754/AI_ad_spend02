"""
统一状态机模块 (Core Layer)

SoT Reference: STATE_MACHINE.md v2.6

本模块是 state-machine 代码块，提供:
1. StateMachine - 通用状态机基类
2. can_transition() - 检查状态转换是否允许
3. transition() - 执行状态转换
4. 预定义状态机: 日报(8状态), 充值(7状态), 结算(4状态), 转账(5状态)等

角色说明 (PRD v2.2 / MASTER.md v4.9 §2.4):
- 6 角色白名单: ceo, admin, project_owner, finance, pitcher, account_manager
- 废弃角色: data_operator → project_owner/finance, media_buyer → pitcher, supervisor → project_owner

使用示例:
    from backend.core.state_machine import (
        DAILY_REPORT_STATE_MACHINE,
        DailyReportStatus
    )

    # 检查是否可以转换
    if DAILY_REPORT_STATE_MACHINE.can_transition("raw_submitted", "trend_pending"):
        DAILY_REPORT_STATE_MACHINE.transition(report, "raw_submitted", "trend_pending")
"""

from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass

from backend.core.role_mapping import role_in_list, expand_role_list


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
            to_state for (f, to_state) in self._transitions.keys() if f == current_state
        ]

    def transition(
        self,
        entity: Any,
        from_state: str,
        to_state: str,
        user_role: Optional[str] = None,
    ) -> None:
        """
        执行状态转换

        Args:
            entity: 状态实体（需要有 status 属性）
            from_state: 当前状态
            to_state: 目标状态
            user_role: 用户角色（支持业务角色和技术角色）

        Raises:
            StateTransitionError: 转换不允许或权限不足

        Note:
            使用 role_in_list() 进行角色检查
            PRD v2.2: 6 角色白名单 (ceo, admin, project_owner, finance, pitcher, account_manager)
        """
        key = (from_state, to_state)
        if key not in self._transitions:
            raise StateTransitionError(from_state, to_state)

        t = self._transitions[key]

        # 使用 role_in_list 检查角色权限 (PRD v2.2)
        if t.required_roles and not role_in_list(user_role, t.required_roles):
            # 展开等价角色以便在错误消息中显示
            expanded_roles = expand_role_list(t.required_roles)
            raise StateTransitionError(
                from_state, to_state, f"需要角色 {expanded_roles}, 当前角色 {user_role}"
            )

        if t.guard and not t.guard(entity):
            raise StateTransitionError(from_state, to_state, "前置条件不满足")

        entity.status = to_state

        if t.action:
            t.action(entity)


# 预定义状态机: 日报
# SoT: STATE_MACHINE.md v2.8 §4
# Phase 1 简化流转: raw_submitted → trend_ok → final_confirmed (TASK-RPT-007)
# Phase 2 完整流转: raw_submitted → trend_pending → trend_ok → final_pending → final_confirmed
DAILY_REPORT_STATE_MACHINE = StateMachine(
    [
        Transition(DailyReportStatus.RAW_SUBMITTED, DailyReportStatus.TREND_PENDING),
        Transition(DailyReportStatus.TREND_PENDING, DailyReportStatus.TREND_OK),
        Transition(DailyReportStatus.TREND_PENDING, DailyReportStatus.TREND_FLAGGED),
        Transition(
            DailyReportStatus.TREND_OK,
            DailyReportStatus.FINAL_PENDING,
            required_roles=["project_owner", "admin"],  # PRD v2.2: data_operator → project_owner
        ),
        # Phase 1 直接确认: trend_ok → final_confirmed (BR-RPT-008: project_owner/admin)
        Transition(
            DailyReportStatus.TREND_OK,
            DailyReportStatus.FINAL_CONFIRMED,
            required_roles=["project_owner", "admin"],  # PRD v2.2: data_operator → project_owner
        ),
        Transition(
            DailyReportStatus.TREND_FLAGGED,
            DailyReportStatus.TREND_RESOLVED,
            required_roles=["project_owner", "admin"],  # PRD v2.2: data_operator → project_owner
        ),
        Transition(
            DailyReportStatus.TREND_FLAGGED,
            DailyReportStatus.RAW_SUBMITTED,
            required_roles=["project_owner", "admin"],  # PRD v2.2: data_operator → project_owner
        ),
        Transition(
            DailyReportStatus.TREND_RESOLVED,
            DailyReportStatus.FINAL_PENDING,
            required_roles=["project_owner", "admin"],  # PRD v2.2: data_operator → project_owner
        ),
        Transition(
            DailyReportStatus.FINAL_PENDING,
            DailyReportStatus.FINAL_CONFIRMED,
            required_roles=["project_owner", "admin"],  # PRD v2.2: data_operator → project_owner
        ),
        Transition(DailyReportStatus.FINAL_CONFIRMED, DailyReportStatus.FINAL_LOCKED),
    ]
)


# 预定义状态机: 充值
TOPUP_STATE_MACHINE = StateMachine(
    [
        Transition(
            TopupStatus.DRAFT,
            TopupStatus.PENDING_REVIEW,
            required_roles=["pitcher", "account_manager"],  # PRD v2.2: media_buyer → pitcher
        ),
        Transition(
            TopupStatus.PENDING_REVIEW,
            TopupStatus.FINANCE_APPROVE,
            required_roles=["account_manager"],  # PRD v2.2: data_operator → account_manager (户管审核)
        ),
        Transition(
            TopupStatus.PENDING_REVIEW,
            TopupStatus.REJECTED,
            required_roles=["account_manager"],  # PRD v2.2: data_operator → account_manager
        ),
        Transition(
            TopupStatus.FINANCE_APPROVE, TopupStatus.PAID, required_roles=["finance"]
        ),
        Transition(
            TopupStatus.FINANCE_APPROVE,
            TopupStatus.REJECTED,
            required_roles=["finance"],
        ),
        Transition(TopupStatus.PAID, TopupStatus.COMPLETED, required_roles=["finance"]),
        Transition(TopupStatus.DRAFT, TopupStatus.CANCELLED),
        Transition(TopupStatus.PENDING_REVIEW, TopupStatus.CANCELLED),  # 申请人可在审核前取消
    ]
)


# 预定义状态机: 转账
TRANSFER_STATE_MACHINE = StateMachine(
    [
        Transition(
            TransferStatus.DRAFT,
            TransferStatus.PENDING_APPROVAL,
            required_roles=["pitcher", "account_manager"],  # PRD v2.2: media_buyer → pitcher
        ),
        Transition(
            TransferStatus.DRAFT,
            TransferStatus.REJECTED,
            required_roles=["finance", "admin"],
        ),  # 草稿阶段可直接拒绝
        Transition(
            TransferStatus.PENDING_APPROVAL,
            TransferStatus.APPROVED,
            required_roles=["finance", "admin"],
        ),
        Transition(
            TransferStatus.PENDING_APPROVAL,
            TransferStatus.REJECTED,
            required_roles=["finance", "admin"],
        ),
        Transition(
            TransferStatus.APPROVED,
            TransferStatus.COMPLETED,
            required_roles=["finance", "admin"],
        ),
    ]
)


# 预定义状态机: 对账批次
RECONCILIATION_BATCH_STATE_MACHINE = StateMachine(
    [
        Transition(
            ReconciliationBatchStatus.DRAFT,
            ReconciliationBatchStatus.PENDING_REVIEW,
            required_roles=["finance"],  # PRD v2.2: 移除废弃的 data_operator
        ),
        Transition(
            ReconciliationBatchStatus.PENDING_REVIEW,
            ReconciliationBatchStatus.APPROVED,
            required_roles=["finance", "admin"],
        ),
        Transition(
            ReconciliationBatchStatus.PENDING_REVIEW,
            ReconciliationBatchStatus.NEEDS_ADJUSTMENT,
            required_roles=["finance", "admin"],
        ),
        Transition(
            ReconciliationBatchStatus.NEEDS_ADJUSTMENT,
            ReconciliationBatchStatus.PENDING_REVIEW,
            required_roles=["finance"],  # PRD v2.2: 移除废弃的 data_operator
        ),  # 重新提交
        Transition(
            ReconciliationBatchStatus.NEEDS_ADJUSTMENT,
            ReconciliationBatchStatus.APPROVED,
            required_roles=["finance", "admin"],
        ),
        Transition(
            ReconciliationBatchStatus.APPROVED,
            ReconciliationBatchStatus.COMPLETED,
            required_roles=["finance", "admin"],
        ),
    ]
)


# 预定义状态机: 对账明细
RECONCILIATION_DETAIL_STATE_MACHINE = StateMachine(
    [
        Transition(
            ReconciliationDetailStatus.PENDING,
            ReconciliationDetailStatus.CONFIRMED,
            required_roles=["finance"],  # PRD v2.2: 移除废弃的 data_operator
        ),
        Transition(
            ReconciliationDetailStatus.PENDING,
            ReconciliationDetailStatus.ADJUSTED,
            required_roles=["finance"],  # PRD v2.2: 移除废弃的 data_operator
        ),
        Transition(
            ReconciliationDetailStatus.CONFIRMED,
            ReconciliationDetailStatus.ADJUSTED,
            required_roles=["finance", "admin"],
        ),  # 已确认可调整
        Transition(
            ReconciliationDetailStatus.ADJUSTED,
            ReconciliationDetailStatus.CONFIRMED,
            required_roles=["finance", "admin"],
        ),  # 调整后可重新确认
    ]
)


# 预定义状态机: 广告账户 (STATE_MACHINE.md v2.6 §7.1)
AD_ACCOUNT_STATE_MACHINE = StateMachine(
    [
        # new 可以转换到任何状态
        Transition(
            AdAccountStatus.NEW,
            AdAccountStatus.TESTING,
            required_roles=["account_manager", "admin"],
        ),
        Transition(
            AdAccountStatus.NEW,
            AdAccountStatus.ACTIVE,
            required_roles=["account_manager", "admin"],
        ),
        Transition(
            AdAccountStatus.NEW,
            AdAccountStatus.SUSPENDED,
            required_roles=["account_manager", "admin"],
        ),
        Transition(AdAccountStatus.NEW, AdAccountStatus.DEAD, required_roles=["admin"]),
        Transition(
            AdAccountStatus.NEW, AdAccountStatus.ARCHIVED, required_roles=["admin"]
        ),
        # testing 可以转换到 active/suspended/dead/archived
        Transition(
            AdAccountStatus.TESTING,
            AdAccountStatus.ACTIVE,
            required_roles=["account_manager", "admin"],
        ),
        Transition(
            AdAccountStatus.TESTING,
            AdAccountStatus.SUSPENDED,
            required_roles=["account_manager", "admin"],
        ),
        Transition(
            AdAccountStatus.TESTING, AdAccountStatus.DEAD, required_roles=["admin"]
        ),
        Transition(
            AdAccountStatus.TESTING, AdAccountStatus.ARCHIVED, required_roles=["admin"]
        ),
        # active 可以暂停/死亡/归档
        Transition(
            AdAccountStatus.ACTIVE,
            AdAccountStatus.SUSPENDED,
            required_roles=["account_manager", "admin"],
        ),
        Transition(
            AdAccountStatus.ACTIVE, AdAccountStatus.DEAD, required_roles=["admin"]
        ),
        Transition(
            AdAccountStatus.ACTIVE, AdAccountStatus.ARCHIVED, required_roles=["admin"]
        ),
        # suspended 可以恢复/死亡/归档
        Transition(
            AdAccountStatus.SUSPENDED,
            AdAccountStatus.ACTIVE,
            required_roles=["account_manager", "admin"],
        ),
        Transition(
            AdAccountStatus.SUSPENDED, AdAccountStatus.DEAD, required_roles=["admin"]
        ),
        Transition(
            AdAccountStatus.SUSPENDED,
            AdAccountStatus.ARCHIVED,
            required_roles=["admin"],
        ),
        # dead 只能归档 (终态之一)
        Transition(
            AdAccountStatus.DEAD, AdAccountStatus.ARCHIVED, required_roles=["admin"]
        ),
        # archived 是终态，无法转换
    ]
)


class SettlementStatus(str, Enum):
    """月度结算状态机 (STATE_MACHINE.md v2.6 §13.1)

    状态流转: pending → confirmed → locked → archived
                ↑          ↓
                └──────────┘ (退回修正)
    """

    PENDING = "pending"  # 待确认 - 系统自动汇总生成
    CONFIRMED = "confirmed"  # 已确认 - 财务确认数据正确
    LOCKED = "locked"  # 已锁定 - 老板最终确认锁定 (终态)
    ARCHIVED = "archived"  # 已归档 - 年度归档 (终态)


# 预定义状态机: 月度结算 (STATE_MACHINE.md v2.6 §13.1)
SETTLEMENT_STATE_MACHINE = StateMachine(
    [
        # pending → confirmed (财务确认)
        Transition(
            SettlementStatus.PENDING,
            SettlementStatus.CONFIRMED,
            required_roles=["finance", "admin"],
        ),
        # confirmed → locked (老板锁定)
        Transition(
            SettlementStatus.CONFIRMED,
            SettlementStatus.LOCKED,
            required_roles=["ceo", "admin"],
        ),
        # confirmed → pending (退回修正)
        Transition(
            SettlementStatus.CONFIRMED,
            SettlementStatus.PENDING,
            required_roles=["finance", "admin"],
        ),
        # locked → archived (年度归档)
        Transition(
            SettlementStatus.LOCKED, SettlementStatus.ARCHIVED, required_roles=["admin"]
        ),
    ]
)


class WeeklyBriefStatus(str, Enum):
    """周报状态机 (STATE_MACHINE.md v2.6 §13.2)"""

    DRAFT = "draft"  # 草稿
    SUBMITTED = "submitted"  # 已提交
    REVIEWED = "reviewed"  # 已审阅
    ARCHIVED = "archived"  # 已归档


# 预定义状态机: 周报
WEEKLY_BRIEF_STATE_MACHINE = StateMachine(
    [
        Transition(
            WeeklyBriefStatus.DRAFT,
            WeeklyBriefStatus.SUBMITTED,
            required_roles=["project_owner", "pitcher"],  # PRD v2.2: data_operator→project_owner, media_buyer→pitcher
        ),
        Transition(
            WeeklyBriefStatus.SUBMITTED,
            WeeklyBriefStatus.REVIEWED,
            required_roles=["account_manager", "admin"],
        ),
        Transition(
            WeeklyBriefStatus.REVIEWED,
            WeeklyBriefStatus.ARCHIVED,
            required_roles=["admin"],
        ),
        # 可以退回修改
        Transition(
            WeeklyBriefStatus.SUBMITTED,
            WeeklyBriefStatus.DRAFT,
            required_roles=["project_owner", "account_manager"],  # PRD v2.2: data_operator→project_owner
        ),
    ]
)


# ============================================================================
# 便捷函数
# ============================================================================


def get_state_machine(entity_type: str) -> Optional[StateMachine]:
    """
    根据实体类型获取对应的状态机

    Args:
        entity_type: 实体类型名称 (daily_report, topup, settlement, etc.)

    Returns:
        对应的 StateMachine 实例，未找到返回 None
    """
    machines = {
        "daily_report": DAILY_REPORT_STATE_MACHINE,
        "topup": TOPUP_STATE_MACHINE,
        "transfer": TRANSFER_STATE_MACHINE,
        "reconciliation_batch": RECONCILIATION_BATCH_STATE_MACHINE,
        "reconciliation_detail": RECONCILIATION_DETAIL_STATE_MACHINE,
        "ad_account": AD_ACCOUNT_STATE_MACHINE,
        "settlement": SETTLEMENT_STATE_MACHINE,
        "weekly_brief": WEEKLY_BRIEF_STATE_MACHINE,
    }
    return machines.get(entity_type)


def validate_transition(
    entity_type: str, from_state: str, to_state: str, user_role: str = None
) -> tuple[bool, Optional[str]]:
    """
    验证状态转换是否合法

    Args:
        entity_type: 实体类型
        from_state: 当前状态
        to_state: 目标状态
        user_role: 用户角色 (可选)

    Returns:
        (is_valid, error_message) 元组
    """
    machine = get_state_machine(entity_type)
    if not machine:
        return False, f"未知的实体类型: {entity_type}"

    if not machine.can_transition(from_state, to_state):
        allowed = machine.get_allowed_transitions(from_state)
        return False, f"不允许从 {from_state} 转换到 {to_state}，允许的目标状态: {allowed}"

    return True, None


# ============================================================================
# 导出列表
# ============================================================================

__all__ = [
    # 状态机基类
    "StateMachine",
    "Transition",
    "StateTransitionError",
    # 状态枚举
    "DailyReportStatus",
    "TopupStatus",
    "TransferStatus",
    "ReconciliationBatchStatus",
    "ReconciliationDetailStatus",
    "AdAccountStatus",
    "ProjectStatus",
    "SettlementStatus",
    "WeeklyBriefStatus",
    # 预定义状态机实例
    "DAILY_REPORT_STATE_MACHINE",
    "TOPUP_STATE_MACHINE",
    "TRANSFER_STATE_MACHINE",
    "RECONCILIATION_BATCH_STATE_MACHINE",
    "RECONCILIATION_DETAIL_STATE_MACHINE",
    "AD_ACCOUNT_STATE_MACHINE",
    "SETTLEMENT_STATE_MACHINE",
    "WEEKLY_BRIEF_STATE_MACHINE",
    # 便捷函数
    "get_state_machine",
    "validate_transition",
]
