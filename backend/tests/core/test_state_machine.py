"""
状态机系统测试模块
测试 backend/core/state_machine.py 的状态机定义和转换功能
"""

import pytest
from dataclasses import dataclass
from backend.core.state_machine import (
    DailyReportStatus,
    TopupStatus,
    TransferStatus,
    ReconciliationBatchStatus,
    ReconciliationDetailStatus,
    AdAccountStatus,
    ProjectStatus,
    Transition,
    StateTransitionError,
    StateMachine,
    DAILY_REPORT_STATE_MACHINE,
    TOPUP_STATE_MACHINE,
    TRANSFER_STATE_MACHINE,
    RECONCILIATION_BATCH_STATE_MACHINE,
)


# ==================== 测试辅助类 ====================

@dataclass
class MockEntity:
    """模拟实体类用于测试"""
    status: str
    amount: float = 0.0


# ==================== 状态枚举测试 ====================

@pytest.mark.unit
@pytest.mark.state_machine
class TestDailyReportStatus:
    """测试日报状态枚举"""

    def test_status_count(self):
        """测试状态数量为8"""
        assert len(DailyReportStatus) == 8

    def test_status_values(self):
        """测试状态值"""
        assert DailyReportStatus.RAW_SUBMITTED.value == "raw_submitted"
        assert DailyReportStatus.TREND_PENDING.value == "trend_pending"
        assert DailyReportStatus.TREND_OK.value == "trend_ok"
        assert DailyReportStatus.TREND_FLAGGED.value == "trend_flagged"
        assert DailyReportStatus.TREND_RESOLVED.value == "trend_resolved"
        assert DailyReportStatus.FINAL_PENDING.value == "final_pending"
        assert DailyReportStatus.FINAL_CONFIRMED.value == "final_confirmed"
        assert DailyReportStatus.FINAL_LOCKED.value == "final_locked"

    def test_status_is_string_enum(self):
        """测试状态是字符串枚举"""
        assert isinstance(DailyReportStatus.RAW_SUBMITTED, str)
        assert DailyReportStatus.RAW_SUBMITTED == "raw_submitted"


@pytest.mark.unit
@pytest.mark.state_machine
class TestTopupStatus:
    """测试充值状态枚举"""

    def test_status_count(self):
        """测试状态数量为7"""
        assert len(TopupStatus) == 7

    def test_status_values(self):
        """测试状态值"""
        assert TopupStatus.DRAFT.value == "draft"
        assert TopupStatus.PENDING_REVIEW.value == "pending_review"
        assert TopupStatus.FINANCE_APPROVE.value == "finance_approve"
        assert TopupStatus.PAID.value == "paid"
        assert TopupStatus.COMPLETED.value == "completed"
        assert TopupStatus.REJECTED.value == "rejected"
        assert TopupStatus.CANCELLED.value == "cancelled"


@pytest.mark.unit
@pytest.mark.state_machine
class TestTransferStatus:
    """测试转账状态枚举"""

    def test_status_count(self):
        """测试状态数量为5"""
        assert len(TransferStatus) == 5

    def test_status_values(self):
        """测试状态值"""
        assert TransferStatus.DRAFT.value == "draft"
        assert TransferStatus.PENDING_APPROVAL.value == "pending_approval"
        assert TransferStatus.APPROVED.value == "approved"
        assert TransferStatus.REJECTED.value == "rejected"
        assert TransferStatus.COMPLETED.value == "completed"


# ==================== StateTransitionError 测试 ====================

@pytest.mark.unit
@pytest.mark.state_machine
class TestStateTransitionError:
    """测试状态转换错误"""

    def test_error_with_default_reason(self):
        """测试默认错误原因"""
        error = StateTransitionError("draft", "completed")
        assert error.current_state == "draft"
        assert error.target_state == "completed"
        assert error.reason == "不允许的状态转换"
        assert "draft" in str(error)
        assert "completed" in str(error)

    def test_error_with_custom_reason(self):
        """测试自定义错误原因"""
        error = StateTransitionError("draft", "paid", "权限不足")
        assert error.reason == "权限不足"
        assert "权限不足" in str(error)


# ==================== StateMachine 核心功能测试 ====================

@pytest.mark.unit
@pytest.mark.state_machine
class TestStateMachineCore:
    """测试状态机核心功能"""

    @pytest.fixture
    def simple_machine(self):
        """创建简单状态机用于测试"""
        return StateMachine([
            Transition(TopupStatus.DRAFT, TopupStatus.PENDING_REVIEW),
            Transition(TopupStatus.PENDING_REVIEW, TopupStatus.FINANCE_APPROVE),
            Transition(TopupStatus.DRAFT, TopupStatus.CANCELLED),
        ])

    def test_can_transition_valid(self, simple_machine):
        """测试有效转换检查"""
        assert simple_machine.can_transition("draft", "pending_review") is True
        assert simple_machine.can_transition("pending_review", "finance_approve") is True
        assert simple_machine.can_transition("draft", "cancelled") is True

    def test_can_transition_invalid(self, simple_machine):
        """测试无效转换检查"""
        assert simple_machine.can_transition("draft", "completed") is False
        assert simple_machine.can_transition("draft", "paid") is False
        assert simple_machine.can_transition("cancelled", "draft") is False

    def test_get_allowed_transitions(self, simple_machine):
        """测试获取允许的转换"""
        allowed = simple_machine.get_allowed_transitions("draft")
        assert set(allowed) == {"pending_review", "cancelled"}

        allowed = simple_machine.get_allowed_transitions("pending_review")
        assert allowed == ["finance_approve"]

        allowed = simple_machine.get_allowed_transitions("cancelled")
        assert allowed == []

    def test_transition_success(self, simple_machine):
        """测试成功转换"""
        entity = MockEntity(status="draft")
        simple_machine.transition(entity, "draft", "pending_review")
        assert entity.status == "pending_review"

    def test_transition_invalid_raises_error(self, simple_machine):
        """测试无效转换抛出异常"""
        entity = MockEntity(status="draft")
        with pytest.raises(StateTransitionError) as exc_info:
            simple_machine.transition(entity, "draft", "completed")
        assert exc_info.value.current_state == "draft"
        assert exc_info.value.target_state == "completed"


# ==================== 角色权限测试 ====================

@pytest.mark.unit
@pytest.mark.state_machine
class TestStateMachineRoles:
    """测试状态机角色权限"""

    @pytest.fixture
    def role_machine(self):
        """创建带角色验证的状态机"""
        return StateMachine([
            Transition(TopupStatus.DRAFT, TopupStatus.PENDING_REVIEW,
                      required_roles=["pitcher", "account_manager"]),
            Transition(TopupStatus.PENDING_REVIEW, TopupStatus.FINANCE_APPROVE,
                      required_roles=["account_manager"]),  # PRD v5.1: data_operator → account_manager
        ])

    def test_transition_with_valid_role(self, role_machine):
        """测试有效角色转换"""
        entity = MockEntity(status="draft")
        role_machine.transition(entity, "draft", "pending_review", user_role="pitcher")
        assert entity.status == "pending_review"

    def test_transition_with_alternative_role(self, role_machine):
        """测试备选角色转换"""
        entity = MockEntity(status="draft")
        role_machine.transition(entity, "draft", "pending_review", user_role="account_manager")
        assert entity.status == "pending_review"

    def test_transition_with_invalid_role(self, role_machine):
        """测试无效角色抛出异常"""
        entity = MockEntity(status="draft")
        with pytest.raises(StateTransitionError) as exc_info:
            role_machine.transition(entity, "draft", "pending_review", user_role="finance")
        assert "需要角色" in exc_info.value.reason
        assert "finance" in exc_info.value.reason

    def test_transition_without_role_when_required(self, role_machine):
        """测试需要角色但未提供"""
        entity = MockEntity(status="draft")
        with pytest.raises(StateTransitionError):
            role_machine.transition(entity, "draft", "pending_review", user_role=None)


# ==================== Guard 和 Action 测试 ====================

@pytest.mark.unit
@pytest.mark.state_machine
class TestStateMachineGuardAndAction:
    """测试状态机 Guard 和 Action"""

    def test_guard_pass(self):
        """测试 Guard 通过"""
        def amount_guard(entity):
            return entity.amount > 0

        machine = StateMachine([
            Transition(TopupStatus.DRAFT, TopupStatus.PENDING_REVIEW, guard=amount_guard),
        ])

        entity = MockEntity(status="draft", amount=100.0)
        machine.transition(entity, "draft", "pending_review")
        assert entity.status == "pending_review"

    def test_guard_fail(self):
        """测试 Guard 失败"""
        def amount_guard(entity):
            return entity.amount > 0

        machine = StateMachine([
            Transition(TopupStatus.DRAFT, TopupStatus.PENDING_REVIEW, guard=amount_guard),
        ])

        entity = MockEntity(status="draft", amount=0.0)
        with pytest.raises(StateTransitionError) as exc_info:
            machine.transition(entity, "draft", "pending_review")
        assert "前置条件不满足" in exc_info.value.reason

    def test_action_executed(self):
        """测试 Action 执行"""
        action_called = []

        def log_action(entity):
            action_called.append(entity.status)

        machine = StateMachine([
            Transition(TopupStatus.DRAFT, TopupStatus.PENDING_REVIEW, action=log_action),
        ])

        entity = MockEntity(status="draft")
        machine.transition(entity, "draft", "pending_review")
        assert len(action_called) == 1
        assert action_called[0] == "pending_review"


# ==================== 预定义状态机测试 ====================

@pytest.mark.unit
@pytest.mark.state_machine
class TestDailyReportStateMachine:
    """测试日报状态机"""

    def test_raw_to_trend_pending(self):
        """测试 raw_submitted → trend_pending"""
        assert DAILY_REPORT_STATE_MACHINE.can_transition("raw_submitted", "trend_pending")

    def test_trend_pending_to_ok_or_flagged(self):
        """测试 trend_pending → trend_ok/trend_flagged"""
        assert DAILY_REPORT_STATE_MACHINE.can_transition("trend_pending", "trend_ok")
        assert DAILY_REPORT_STATE_MACHINE.can_transition("trend_pending", "trend_flagged")

    def test_trend_ok_to_final_pending(self):
        """测试 trend_ok → final_pending 需要角色"""
        entity = MockEntity(status="trend_ok")
        DAILY_REPORT_STATE_MACHINE.transition(entity, "trend_ok", "final_pending", user_role="project_owner")
        assert entity.status == "final_pending"

    def test_final_confirmed_to_locked(self):
        """测试 final_confirmed → final_locked"""
        entity = MockEntity(status="final_confirmed")
        DAILY_REPORT_STATE_MACHINE.transition(entity, "final_confirmed", "final_locked")
        assert entity.status == "final_locked"

    def test_final_locked_is_terminal(self):
        """测试 final_locked 是终态"""
        allowed = DAILY_REPORT_STATE_MACHINE.get_allowed_transitions("final_locked")
        assert allowed == []

    def test_invalid_skip_trend_check(self):
        """测试不能跳过趋势检查"""
        assert not DAILY_REPORT_STATE_MACHINE.can_transition("raw_submitted", "final_pending")


@pytest.mark.unit
@pytest.mark.state_machine
class TestTopupStateMachine:
    """测试充值状态机"""

    def test_draft_to_pending_review(self):
        """测试 draft → pending_review"""
        entity = MockEntity(status="draft")
        TOPUP_STATE_MACHINE.transition(entity, "draft", "pending_review", user_role="pitcher")
        assert entity.status == "pending_review"

    def test_pending_review_to_finance_approve(self):
        """测试 pending_review → finance_approve 需要 account_manager (PRD v5.1)"""
        entity = MockEntity(status="pending_review")
        TOPUP_STATE_MACHINE.transition(entity, "pending_review", "finance_approve", user_role="account_manager")
        assert entity.status == "finance_approve"

    def test_finance_approve_to_paid(self):
        """测试 finance_approve → paid 需要 finance"""
        entity = MockEntity(status="finance_approve")
        TOPUP_STATE_MACHINE.transition(entity, "finance_approve", "paid", user_role="finance")
        assert entity.status == "paid"

    def test_draft_can_cancel(self):
        """测试 draft 可以取消"""
        entity = MockEntity(status="draft")
        TOPUP_STATE_MACHINE.transition(entity, "draft", "cancelled")
        assert entity.status == "cancelled"

    def test_pending_review_can_reject(self):
        """测试 pending_review 可以拒绝 (account_manager, PRD v5.1)"""
        entity = MockEntity(status="pending_review")
        TOPUP_STATE_MACHINE.transition(entity, "pending_review", "rejected", user_role="account_manager")
        assert entity.status == "rejected"

    def test_invalid_skip_review(self):
        """测试不能跳过审核"""
        assert not TOPUP_STATE_MACHINE.can_transition("draft", "paid")
        assert not TOPUP_STATE_MACHINE.can_transition("draft", "completed")


@pytest.mark.unit
@pytest.mark.state_machine
class TestTransferStateMachine:
    """测试转账状态机"""

    def test_full_approve_flow(self):
        """测试完整审批流程"""
        entity = MockEntity(status="draft")

        TRANSFER_STATE_MACHINE.transition(entity, "draft", "pending_approval", user_role="pitcher")
        assert entity.status == "pending_approval"

        TRANSFER_STATE_MACHINE.transition(entity, "pending_approval", "approved", user_role="finance")
        assert entity.status == "approved"

        TRANSFER_STATE_MACHINE.transition(entity, "approved", "completed", user_role="finance")
        assert entity.status == "completed"

    def test_reject_flow(self):
        """测试拒绝流程"""
        entity = MockEntity(status="pending_approval")
        TRANSFER_STATE_MACHINE.transition(entity, "pending_approval", "rejected", user_role="admin")
        assert entity.status == "rejected"

    def test_completed_is_terminal(self):
        """测试 completed 是终态"""
        allowed = TRANSFER_STATE_MACHINE.get_allowed_transitions("completed")
        assert allowed == []


@pytest.mark.unit
@pytest.mark.state_machine
class TestReconciliationBatchStateMachine:
    """测试对账批次状态机"""

    def test_draft_to_pending_review(self):
        """测试 draft → pending_review"""
        entity = MockEntity(status="draft")
        RECONCILIATION_BATCH_STATE_MACHINE.transition(
            entity, "draft", "pending_review", user_role="finance"
        )
        assert entity.status == "pending_review"

    def test_needs_adjustment_flow(self):
        """测试需要调整流程"""
        entity = MockEntity(status="pending_review")
        RECONCILIATION_BATCH_STATE_MACHINE.transition(
            entity, "pending_review", "needs_adjustment", user_role="admin"
        )
        assert entity.status == "needs_adjustment"

        RECONCILIATION_BATCH_STATE_MACHINE.transition(
            entity, "needs_adjustment", "approved", user_role="finance"
        )
        assert entity.status == "approved"

    def test_completed_is_terminal(self):
        """测试 completed 是终态"""
        allowed = RECONCILIATION_BATCH_STATE_MACHINE.get_allowed_transitions("completed")
        assert allowed == []


# ==================== 集成测试 ====================

@pytest.mark.integration
@pytest.mark.state_machine
class TestStateMachineIntegration:
    """状态机集成测试"""

    def test_daily_report_full_flow(self):
        """测试日报完整流程"""
        entity = MockEntity(status="raw_submitted")

        DAILY_REPORT_STATE_MACHINE.transition(entity, "raw_submitted", "trend_pending")
        DAILY_REPORT_STATE_MACHINE.transition(entity, "trend_pending", "trend_ok")
        DAILY_REPORT_STATE_MACHINE.transition(entity, "trend_ok", "final_pending", user_role="project_owner")
        DAILY_REPORT_STATE_MACHINE.transition(entity, "final_pending", "final_confirmed", user_role="project_owner")
        DAILY_REPORT_STATE_MACHINE.transition(entity, "final_confirmed", "final_locked")

        assert entity.status == "final_locked"

    def test_daily_report_flagged_flow(self):
        """测试日报异常流程"""
        entity = MockEntity(status="raw_submitted")

        DAILY_REPORT_STATE_MACHINE.transition(entity, "raw_submitted", "trend_pending")
        DAILY_REPORT_STATE_MACHINE.transition(entity, "trend_pending", "trend_flagged")
        DAILY_REPORT_STATE_MACHINE.transition(entity, "trend_flagged", "trend_resolved", user_role="project_owner")
        DAILY_REPORT_STATE_MACHINE.transition(entity, "trend_resolved", "final_pending", user_role="project_owner")

        assert entity.status == "final_pending"

    def test_topup_full_flow(self):
        """测试充值完整流程"""
        entity = MockEntity(status="draft")

        TOPUP_STATE_MACHINE.transition(entity, "draft", "pending_review", user_role="pitcher")
        TOPUP_STATE_MACHINE.transition(entity, "pending_review", "finance_approve", user_role="account_manager")
        TOPUP_STATE_MACHINE.transition(entity, "finance_approve", "paid", user_role="finance")
        TOPUP_STATE_MACHINE.transition(entity, "paid", "completed", user_role="finance")

        assert entity.status == "completed"
