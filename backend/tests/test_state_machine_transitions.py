"""
状态机流转测试
Version: 1.0 (Test Quality Enhancement Flow - Phase 2)
Author: Claude协作开发

测试范围:
- DailyReport 8状态机: happy path + exception paths
- Topup 7状态机: happy path + exception paths
- Reconciliation 5状态机: happy path + exception paths
- 终态不可变测试
- 非法流转拒绝测试

SoT对齐:
- STATE_MACHINE.md v2.6
- ERROR_CODES_SOT.md v2.1
"""

import pytest
from backend.models.base import (
    DailyReportStatus,
    TopupStatus,
    ReconciliationBatchStatus,
)


class TestDailyReportStateMachine:
    """
    日报8状态机流转测试

    状态机定义（STATE_MACHINE.md v2.6 第8章）：
    raw_submitted → trend_pending → trend_ok/trend_flagged
    → trend_resolved → final_pending → final_confirmed → final_locked

    终态: final_locked（仅可通过红冲修正）
    """

    def test_happy_path_transitions_are_valid(self, daily_report_state_helper):
        """测试正常流程中的每个流转都是合法的"""
        happy_path = daily_report_state_helper.get_happy_path()

        # 验证 happy path 中的每个流转
        for i in range(len(happy_path) - 1):
            from_status = happy_path[i]
            to_status = happy_path[i + 1]
            assert daily_report_state_helper.is_valid_transition(from_status, to_status), \
                f"Happy path 流转失败: {from_status.value} → {to_status.value}"

    def test_exception_path_trend_flagged_resolved(self, daily_report_state_helper):
        """测试趋势异常→运营确认正常路径"""
        exception_paths = daily_report_state_helper.get_exception_paths()
        path = exception_paths["trend_flagged_then_resolved"]

        for i in range(len(path) - 1):
            from_status = path[i]
            to_status = path[i + 1]
            assert daily_report_state_helper.is_valid_transition(from_status, to_status), \
                f"Exception path 流转失败: {from_status.value} → {to_status.value}"

    def test_exception_path_trend_flagged_resubmit(self, daily_report_state_helper):
        """测试趋势异常→要求重新提交路径"""
        exception_paths = daily_report_state_helper.get_exception_paths()
        path = exception_paths["trend_flagged_then_resubmit"]

        for i in range(len(path) - 1):
            from_status = path[i]
            to_status = path[i + 1]
            assert daily_report_state_helper.is_valid_transition(from_status, to_status), \
                f"Exception path 流转失败: {from_status.value} → {to_status.value}"

    def test_final_locked_is_terminal(self, daily_report_state_helper):
        """测试 final_locked 是终态"""
        assert daily_report_state_helper.is_terminal_state(DailyReportStatus.FINAL_LOCKED)

    def test_final_locked_has_no_valid_transitions(self, daily_report_state_helper):
        """测试 final_locked 不能流转到任何状态"""
        valid_targets = daily_report_state_helper.VALID_TRANSITIONS.get(
            DailyReportStatus.FINAL_LOCKED, []
        )
        assert len(valid_targets) == 0, "终态 final_locked 不应有合法流转目标"

    def test_non_terminal_states_are_not_terminal(self, daily_report_state_helper):
        """测试非终态的状态正确标识"""
        non_terminal = [
            DailyReportStatus.RAW_SUBMITTED,
            DailyReportStatus.TREND_PENDING,
            DailyReportStatus.TREND_OK,
            DailyReportStatus.TREND_FLAGGED,
            DailyReportStatus.TREND_RESOLVED,
            DailyReportStatus.FINAL_PENDING,
            DailyReportStatus.FINAL_CONFIRMED,
        ]
        for status in non_terminal:
            assert not daily_report_state_helper.is_terminal_state(status), \
                f"{status.value} 不应被标记为终态"

    @pytest.mark.parametrize("from_status,to_status", [
        # 跳过 trend_pending 直接到 trend_ok
        (DailyReportStatus.RAW_SUBMITTED, DailyReportStatus.TREND_OK),
        # 跳过 final_pending 直接到 final_confirmed
        (DailyReportStatus.TREND_OK, DailyReportStatus.FINAL_CONFIRMED),
        # 从终态回退
        (DailyReportStatus.FINAL_LOCKED, DailyReportStatus.FINAL_CONFIRMED),
        # 从终态回退到初始状态
        (DailyReportStatus.FINAL_LOCKED, DailyReportStatus.RAW_SUBMITTED),
        # 反向流转
        (DailyReportStatus.FINAL_CONFIRMED, DailyReportStatus.FINAL_PENDING),
        # trend_ok 不能直接到 final_confirmed（需经过 final_pending）
        (DailyReportStatus.TREND_OK, DailyReportStatus.FINAL_CONFIRMED),
    ])
    def test_invalid_transitions_are_rejected(
        self, daily_report_state_helper, from_status, to_status
    ):
        """测试非法流转被拒绝"""
        assert not daily_report_state_helper.is_valid_transition(from_status, to_status), \
            f"非法流转应被拒绝: {from_status.value} → {to_status.value}"


class TestTopupStateMachine:
    """
    充值申请7状态机流转测试

    状态机定义（STATE_MACHINE.md v2.6 第9章）：
    draft → pending_review → finance_approve → paid → completed
                           ↘ rejected
                           ↘ cancelled

    终态: completed, rejected, cancelled
    """

    def test_happy_path_transitions_are_valid(self, topup_state_helper):
        """测试正常流程（审批通过并完成）中的每个流转都是合法的"""
        happy_path = topup_state_helper.get_happy_path()

        for i in range(len(happy_path) - 1):
            from_status = happy_path[i]
            to_status = happy_path[i + 1]
            assert topup_state_helper.is_valid_transition(from_status, to_status), \
                f"Happy path 流转失败: {from_status.value} → {to_status.value}"

    def test_exception_path_data_review_reject(self, topup_state_helper):
        """测试数据复核拒绝路径"""
        exception_paths = topup_state_helper.get_exception_paths()
        path = exception_paths["data_review_reject"]

        for i in range(len(path) - 1):
            from_status = path[i]
            to_status = path[i + 1]
            assert topup_state_helper.is_valid_transition(from_status, to_status), \
                f"数据复核拒绝路径流转失败: {from_status.value} → {to_status.value}"

    def test_exception_path_finance_reject(self, topup_state_helper):
        """测试财务审批拒绝路径"""
        exception_paths = topup_state_helper.get_exception_paths()
        path = exception_paths["finance_reject"]

        for i in range(len(path) - 1):
            from_status = path[i]
            to_status = path[i + 1]
            assert topup_state_helper.is_valid_transition(from_status, to_status), \
                f"财务审批拒绝路径流转失败: {from_status.value} → {to_status.value}"

    def test_exception_path_user_cancel(self, topup_state_helper):
        """测试用户取消路径"""
        exception_paths = topup_state_helper.get_exception_paths()
        path = exception_paths["user_cancel"]

        for i in range(len(path) - 1):
            from_status = path[i]
            to_status = path[i + 1]
            assert topup_state_helper.is_valid_transition(from_status, to_status), \
                f"用户取消路径流转失败: {from_status.value} → {to_status.value}"

    @pytest.mark.parametrize("terminal_status", [
        TopupStatus.COMPLETED,
        TopupStatus.REJECTED,
        TopupStatus.CANCELLED,
    ])
    def test_terminal_states_are_terminal(self, topup_state_helper, terminal_status):
        """测试所有终态都被正确标识"""
        assert topup_state_helper.is_terminal_state(terminal_status), \
            f"{terminal_status.value} 应被标记为终态"

    @pytest.mark.parametrize("terminal_status", [
        TopupStatus.COMPLETED,
        TopupStatus.REJECTED,
        TopupStatus.CANCELLED,
    ])
    def test_terminal_states_have_no_valid_transitions(
        self, topup_state_helper, terminal_status
    ):
        """测试终态不能流转到任何状态"""
        valid_targets = topup_state_helper.VALID_TRANSITIONS.get(terminal_status, [])
        assert len(valid_targets) == 0, \
            f"终态 {terminal_status.value} 不应有合法流转目标"

    def test_non_terminal_states_are_not_terminal(self, topup_state_helper):
        """测试非终态的状态正确标识"""
        non_terminal = [
            TopupStatus.DRAFT,
            TopupStatus.PENDING_REVIEW,
            TopupStatus.FINANCE_APPROVE,
            TopupStatus.PAID,
        ]
        for status in non_terminal:
            assert not topup_state_helper.is_terminal_state(status), \
                f"{status.value} 不应被标记为终态"

    @pytest.mark.parametrize("from_status,to_status", [
        # 跳过 pending_review 直接到 finance_approve
        (TopupStatus.DRAFT, TopupStatus.FINANCE_APPROVE),
        # 跳过 paid 直接到 completed
        (TopupStatus.FINANCE_APPROVE, TopupStatus.COMPLETED),
        # 从终态回退
        (TopupStatus.COMPLETED, TopupStatus.PAID),
        (TopupStatus.REJECTED, TopupStatus.PENDING_REVIEW),
        (TopupStatus.CANCELLED, TopupStatus.DRAFT),
        # 反向流转
        (TopupStatus.PAID, TopupStatus.FINANCE_APPROVE),
        (TopupStatus.FINANCE_APPROVE, TopupStatus.PENDING_REVIEW),
        # paid 之后不能 reject（STATE_MACHINE.md v2.6）
        (TopupStatus.PAID, TopupStatus.REJECTED),
    ])
    def test_invalid_transitions_are_rejected(
        self, topup_state_helper, from_status, to_status
    ):
        """测试非法流转被拒绝"""
        assert not topup_state_helper.is_valid_transition(from_status, to_status), \
            f"非法流转应被拒绝: {from_status.value} → {to_status.value}"


class TestReconciliationStateMachine:
    """
    对账批次5状态机流转测试

    状态机定义（STATE_MACHINE.md v2.6 第11章）：
    draft → pending_review → approved → completed
                           ↘ needs_adjustment → approved → completed

    终态: completed
    """

    def test_happy_path_transitions_are_valid(self, reconciliation_state_helper):
        """测试正常流程（直接审批通过）中的每个流转都是合法的"""
        happy_path = reconciliation_state_helper.get_happy_path()

        for i in range(len(happy_path) - 1):
            from_status = happy_path[i]
            to_status = happy_path[i + 1]
            assert reconciliation_state_helper.is_valid_transition(from_status, to_status), \
                f"Happy path 流转失败: {from_status.value} → {to_status.value}"

    def test_exception_path_needs_adjustment(self, reconciliation_state_helper):
        """测试需调整后重新审批路径"""
        exception_paths = reconciliation_state_helper.get_exception_paths()
        path = exception_paths["needs_adjustment_then_approve"]

        for i in range(len(path) - 1):
            from_status = path[i]
            to_status = path[i + 1]
            assert reconciliation_state_helper.is_valid_transition(from_status, to_status), \
                f"需调整路径流转失败: {from_status.value} → {to_status.value}"

    def test_no_multiple_adjustments_path(self, reconciliation_state_helper):
        """
        P2-FIX: 测试多次调整路径已被移除

        STATE_MACHINE.md v2.6 第11章定义:
        - needs_adjustment 只能到 approved
        - 无法实现多次调整循环

        如需多次调整，业务上需要新建批次或由 admin 回退
        """
        exception_paths = reconciliation_state_helper.get_exception_paths()
        assert "multiple_adjustments" not in exception_paths, \
            "STATE_MACHINE.md v2.6 不支持多次调整循环路径"

    def test_completed_is_terminal(self, reconciliation_state_helper):
        """测试 completed 是终态"""
        assert reconciliation_state_helper.is_terminal_state(
            ReconciliationBatchStatus.COMPLETED
        )

    def test_completed_has_no_valid_transitions(self, reconciliation_state_helper):
        """测试 completed 不能流转到任何状态"""
        valid_targets = reconciliation_state_helper.VALID_TRANSITIONS.get(
            ReconciliationBatchStatus.COMPLETED, []
        )
        assert len(valid_targets) == 0, "终态 completed 不应有合法流转目标"

    def test_non_terminal_states_are_not_terminal(self, reconciliation_state_helper):
        """测试非终态的状态正确标识"""
        non_terminal = [
            ReconciliationBatchStatus.DRAFT,
            ReconciliationBatchStatus.PENDING_REVIEW,
            ReconciliationBatchStatus.APPROVED,
            ReconciliationBatchStatus.NEEDS_ADJUSTMENT,
        ]
        for status in non_terminal:
            assert not reconciliation_state_helper.is_terminal_state(status), \
                f"{status.value} 不应被标记为终态"

    @pytest.mark.parametrize("from_status,to_status", [
        # 跳过 pending_review 直接到 approved
        (ReconciliationBatchStatus.DRAFT, ReconciliationBatchStatus.APPROVED),
        # 跳过 approved 直接到 completed
        (ReconciliationBatchStatus.PENDING_REVIEW, ReconciliationBatchStatus.COMPLETED),
        # 从终态回退
        (ReconciliationBatchStatus.COMPLETED, ReconciliationBatchStatus.APPROVED),
        (ReconciliationBatchStatus.COMPLETED, ReconciliationBatchStatus.DRAFT),
        # 反向流转
        (ReconciliationBatchStatus.APPROVED, ReconciliationBatchStatus.PENDING_REVIEW),
        # needs_adjustment 不能直接到 completed (但可以到 approved)
        (ReconciliationBatchStatus.NEEDS_ADJUSTMENT, ReconciliationBatchStatus.COMPLETED),
        # P2-FIX: needs_adjustment → approved 是合法的 (STATE_MACHINE.md v2.6 第11章)
        # 移除: (ReconciliationBatchStatus.NEEDS_ADJUSTMENT, ReconciliationBatchStatus.APPROVED),
        # needs_adjustment 不能到 pending_review 或 draft
        (ReconciliationBatchStatus.NEEDS_ADJUSTMENT, ReconciliationBatchStatus.PENDING_REVIEW),
        (ReconciliationBatchStatus.NEEDS_ADJUSTMENT, ReconciliationBatchStatus.DRAFT),
    ])
    def test_invalid_transitions_are_rejected(
        self, reconciliation_state_helper, from_status, to_status
    ):
        """测试非法流转被拒绝"""
        assert not reconciliation_state_helper.is_valid_transition(from_status, to_status), \
            f"非法流转应被拒绝: {from_status.value} → {to_status.value}"


class TestFinalStateImmutability:
    """
    终态不可变性测试

    业务规则（STATE_MACHINE.md v2.6 第14.2章）：
    - 终态回退绝对禁止（某些场景即使 admin 也不可执行）
    - 已完成的充值申请不可回退（资金已到账，Ledger Entry 已创建）
    - 已锁定的日报不可直接修改（需通过红冲机制）
    - 已完成的对账批次不可回退
    """

    def test_daily_report_final_locked_is_immutable(self, daily_report_state_helper):
        """测试日报 final_locked 状态不可变"""
        # 获取所有可能的目标状态
        all_states = daily_report_state_helper.get_all_states()

        for target_state in all_states:
            if target_state != DailyReportStatus.FINAL_LOCKED:
                is_valid = daily_report_state_helper.is_valid_transition(
                    DailyReportStatus.FINAL_LOCKED, target_state
                )
                assert not is_valid, \
                    f"终态 final_locked 不应能流转到 {target_state.value}"

    def test_topup_completed_is_immutable(self, topup_state_helper):
        """测试充值 completed 状态不可变"""
        all_states = topup_state_helper.get_all_states()

        for target_state in all_states:
            if target_state != TopupStatus.COMPLETED:
                is_valid = topup_state_helper.is_valid_transition(
                    TopupStatus.COMPLETED, target_state
                )
                assert not is_valid, \
                    f"终态 completed 不应能流转到 {target_state.value}"

    def test_topup_rejected_is_immutable(self, topup_state_helper):
        """测试充值 rejected 状态不可变"""
        all_states = topup_state_helper.get_all_states()

        for target_state in all_states:
            if target_state != TopupStatus.REJECTED:
                is_valid = topup_state_helper.is_valid_transition(
                    TopupStatus.REJECTED, target_state
                )
                assert not is_valid, \
                    f"终态 rejected 不应能流转到 {target_state.value}"

    def test_topup_cancelled_is_immutable(self, topup_state_helper):
        """测试充值 cancelled 状态不可变"""
        all_states = topup_state_helper.get_all_states()

        for target_state in all_states:
            if target_state != TopupStatus.CANCELLED:
                is_valid = topup_state_helper.is_valid_transition(
                    TopupStatus.CANCELLED, target_state
                )
                assert not is_valid, \
                    f"终态 cancelled 不应能流转到 {target_state.value}"

    def test_reconciliation_completed_is_immutable(self, reconciliation_state_helper):
        """测试对账批次 completed 状态不可变"""
        all_states = reconciliation_state_helper.get_all_states()

        for target_state in all_states:
            if target_state != ReconciliationBatchStatus.COMPLETED:
                is_valid = reconciliation_state_helper.is_valid_transition(
                    ReconciliationBatchStatus.COMPLETED, target_state
                )
                assert not is_valid, \
                    f"终态 completed 不应能流转到 {target_state.value}"


class TestStateHelperConsistency:
    """
    状态辅助类一致性测试

    确保所有 StateHelper 类遵循相同的接口规范
    """

    def test_all_helpers_have_required_methods(
        self, daily_report_state_helper, topup_state_helper, reconciliation_state_helper
    ):
        """测试所有辅助类都有必需的方法"""
        required_methods = [
            'is_valid_transition',
            'is_terminal_state',
            'get_all_states',
            'get_happy_path',
            'get_exception_paths',
            'get_invalid_transitions',
        ]

        helpers = [
            daily_report_state_helper,
            topup_state_helper,
            reconciliation_state_helper,
        ]

        for helper in helpers:
            for method in required_methods:
                assert hasattr(helper, method), \
                    f"{helper.__name__} 缺少方法: {method}"

    def test_happy_path_starts_with_initial_state(
        self, daily_report_state_helper, topup_state_helper, reconciliation_state_helper
    ):
        """测试 happy path 从初始状态开始"""
        # DailyReport 初始状态是 raw_submitted
        dr_path = daily_report_state_helper.get_happy_path()
        assert dr_path[0] == DailyReportStatus.RAW_SUBMITTED

        # Topup 初始状态是 draft
        topup_path = topup_state_helper.get_happy_path()
        assert topup_path[0] == TopupStatus.DRAFT

        # Reconciliation 初始状态是 draft
        recon_path = reconciliation_state_helper.get_happy_path()
        assert recon_path[0] == ReconciliationBatchStatus.DRAFT

    def test_happy_path_ends_with_terminal_state(
        self, daily_report_state_helper, topup_state_helper, reconciliation_state_helper
    ):
        """测试 happy path 以终态结束"""
        # DailyReport 终态是 final_locked
        dr_path = daily_report_state_helper.get_happy_path()
        assert daily_report_state_helper.is_terminal_state(dr_path[-1])

        # Topup 终态是 completed（happy path）
        topup_path = topup_state_helper.get_happy_path()
        assert topup_state_helper.is_terminal_state(topup_path[-1])

        # Reconciliation 终态是 completed
        recon_path = reconciliation_state_helper.get_happy_path()
        assert reconciliation_state_helper.is_terminal_state(recon_path[-1])

    def test_exception_paths_end_with_terminal_state(
        self, daily_report_state_helper, topup_state_helper, reconciliation_state_helper
    ):
        """测试所有异常路径都以终态结束"""
        # DailyReport
        for path_name, path in daily_report_state_helper.get_exception_paths().items():
            assert daily_report_state_helper.is_terminal_state(path[-1]), \
                f"DailyReport 异常路径 '{path_name}' 未以终态结束"

        # Topup
        for path_name, path in topup_state_helper.get_exception_paths().items():
            assert topup_state_helper.is_terminal_state(path[-1]), \
                f"Topup 异常路径 '{path_name}' 未以终态结束"

        # Reconciliation
        for path_name, path in reconciliation_state_helper.get_exception_paths().items():
            assert reconciliation_state_helper.is_terminal_state(path[-1]), \
                f"Reconciliation 异常路径 '{path_name}' 未以终态结束"

    def test_invalid_transitions_list_is_non_empty(
        self, daily_report_state_helper, topup_state_helper, reconciliation_state_helper
    ):
        """测试非法流转列表非空（状态机应该有限制）"""
        assert len(daily_report_state_helper.get_invalid_transitions()) > 0
        assert len(topup_state_helper.get_invalid_transitions()) > 0
        assert len(reconciliation_state_helper.get_invalid_transitions()) > 0


class TestLedgerInvariants:
    """
    账本不可变量测试

    业务规则（LEDGER_SOT.md v1.1）：
    - 金额方向必须正确（正数/负数）
    - 双账本隔离（PROJECT / SUPPLIER）
    - 分录类型限制
    """

    def test_positive_amount_types(self, ledger_invariant_helper):
        """测试正数金额类型验证"""
        from decimal import Decimal

        for entry_type in ledger_invariant_helper.POSITIVE_TYPES:
            assert ledger_invariant_helper.validate_amount_direction(entry_type, Decimal("100.00"))
            assert ledger_invariant_helper.validate_amount_direction(entry_type, Decimal("0.00"))
            assert not ledger_invariant_helper.validate_amount_direction(entry_type, Decimal("-100.00"))

    def test_negative_amount_types(self, ledger_invariant_helper):
        """测试负数金额类型验证"""
        from decimal import Decimal

        for entry_type in ledger_invariant_helper.NEGATIVE_TYPES:
            assert ledger_invariant_helper.validate_amount_direction(entry_type, Decimal("-100.00"))
            assert ledger_invariant_helper.validate_amount_direction(entry_type, Decimal("0.00"))
            assert not ledger_invariant_helper.validate_amount_direction(entry_type, Decimal("100.00"))

    def test_project_ledger_types(self, ledger_invariant_helper):
        """测试 PROJECT 账本允许的分录类型"""
        from backend.models.base import LedgerEntryType

        project_types = ledger_invariant_helper.get_project_ledger_types()

        # 应该包含 REVENUE, TOPUP, REVERSAL
        assert LedgerEntryType.REVENUE in project_types
        assert LedgerEntryType.TOPUP in project_types
        assert LedgerEntryType.REVERSAL in project_types

        # 不应该包含 COST, TRANSFER_OUT, TRANSFER_IN
        assert LedgerEntryType.COST not in project_types
        assert LedgerEntryType.TRANSFER_OUT not in project_types
        assert LedgerEntryType.TRANSFER_IN not in project_types

    def test_supplier_ledger_types(self, ledger_invariant_helper):
        """测试 SUPPLIER 账本允许的分录类型"""
        from backend.models.base import LedgerEntryType

        supplier_types = ledger_invariant_helper.get_supplier_ledger_types()

        # 应该包含 COST, TOPUP, TRANSFER_OUT, TRANSFER_IN, REVERSAL
        assert LedgerEntryType.COST in supplier_types
        assert LedgerEntryType.TOPUP in supplier_types
        assert LedgerEntryType.TRANSFER_OUT in supplier_types
        assert LedgerEntryType.TRANSFER_IN in supplier_types
        assert LedgerEntryType.REVERSAL in supplier_types

        # 不应该包含 REVENUE
        assert LedgerEntryType.REVENUE not in supplier_types
