"""
日报 8 状态机单元测试
Version: 1.0
Author: Claude协作开发

SoT 依据: STATE_MACHINE.md v2.6 第 8 章

状态流转:
    raw_submitted → trend_pending → trend_ok/trend_flagged
    → trend_resolved → final_pending → final_confirmed → final_locked

测试覆盖:
- Happy Path: 正常流程测试
- Exception Path: 趋势异常 → 复核/退回流程
- Invalid Transitions: 非法状态流转测试
- Boundary Conditions: 边界条件测试
"""

import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from backend.models import DailyReport
from backend.models.base import DailyReportStatus


class TestDailyReportStateMachine:
    """日报 8 状态机测试类"""

    # ========== Happy Path Tests ==========

    def test_happy_path_transitions(
        self, db_session, test_ad_account, test_user, daily_report_state_helper
    ):
        """测试正常流程: raw_submitted → trend_pending → trend_ok → final_pending → final_confirmed → final_locked"""
        # 创建日报
        report = DailyReport(
            ad_account_id=test_ad_account.id,
            report_date=date.today(),
            status=DailyReportStatus.RAW_SUBMITTED.value,
            conversions_raw=50,
            raw_spend=Decimal("100.00"),
            submitted_by=test_user.id,
        )
        db_session.add(report)
        db_session.commit()

        # 获取 Happy Path
        happy_path = daily_report_state_helper.get_happy_path()
        assert len(happy_path) == 6

        # 验证初始状态
        assert report.status == DailyReportStatus.RAW_SUBMITTED.value

        # Step 1: raw_submitted → trend_pending
        assert report.can_transition_to(DailyReportStatus.TREND_PENDING)
        report.trigger_trend_check()
        assert report.status == DailyReportStatus.TREND_PENDING.value

        # Step 2: trend_pending → trend_ok
        assert report.can_transition_to(DailyReportStatus.TREND_OK)
        report.mark_trend_ok()
        assert report.status == DailyReportStatus.TREND_OK.value

        # Step 3: trend_ok → final_pending
        assert report.can_transition_to(DailyReportStatus.FINAL_PENDING)
        report.enter_final_pending(test_user.id)
        assert report.status == DailyReportStatus.FINAL_PENDING.value

        # Step 4: final_pending → final_confirmed
        assert report.can_transition_to(DailyReportStatus.FINAL_CONFIRMED)
        report.confirm_final(test_user.id)
        assert report.status == DailyReportStatus.FINAL_CONFIRMED.value

        # Step 5: final_confirmed → final_locked
        assert report.can_transition_to(DailyReportStatus.FINAL_LOCKED)
        report.lock_final()
        assert report.status == DailyReportStatus.FINAL_LOCKED.value

        # 验证终态
        assert daily_report_state_helper.is_terminal_state(
            DailyReportStatus(report.status)
        )

    # ========== Exception Path Tests ==========

    def test_trend_flagged_then_resolved_path(
        self, db_session, test_ad_account, test_user, daily_report_state_helper
    ):
        """测试异常路径: trend_flagged → trend_resolved → final_pending → ..."""
        report = DailyReport(
            ad_account_id=test_ad_account.id,
            report_date=date.today(),
            status=DailyReportStatus.RAW_SUBMITTED.value,
            conversions_raw=50,
            raw_spend=Decimal("100.00"),
            submitted_by=test_user.id,
        )
        db_session.add(report)
        db_session.commit()

        # raw_submitted → trend_pending
        report.trigger_trend_check()
        assert report.status == DailyReportStatus.TREND_PENDING.value

        # trend_pending → trend_flagged (异常)
        assert report.can_transition_to(DailyReportStatus.TREND_FLAGGED)
        report.mark_trend_flagged("TF-001: 粉数骤降")
        assert report.status == DailyReportStatus.TREND_FLAGGED.value

        # trend_flagged → trend_resolved (运营确认)
        assert report.can_transition_to(DailyReportStatus.TREND_RESOLVED)
        report.resolve_trend(test_user.id, "运营确认数据正常")
        assert report.status == DailyReportStatus.TREND_RESOLVED.value

        # trend_resolved → final_pending
        assert report.can_transition_to(DailyReportStatus.FINAL_PENDING)
        report.enter_final_pending(test_user.id)
        assert report.status == DailyReportStatus.FINAL_PENDING.value

        # 继续到终态
        report.confirm_final(test_user.id)
        report.lock_final()
        assert report.status == DailyReportStatus.FINAL_LOCKED.value

    def test_trend_flagged_then_resubmit_path(
        self, db_session, test_ad_account, test_user
    ):
        """测试异常路径: trend_flagged → raw_submitted (退回重提)"""
        report = DailyReport(
            ad_account_id=test_ad_account.id,
            report_date=date.today(),
            status=DailyReportStatus.RAW_SUBMITTED.value,
            conversions_raw=50,
            raw_spend=Decimal("100.00"),
            submitted_by=test_user.id,
        )
        db_session.add(report)
        db_session.commit()

        # raw_submitted → trend_pending → trend_flagged
        report.trigger_trend_check()
        report.mark_trend_flagged("TF-002: 粉数骤增")
        assert report.status == DailyReportStatus.TREND_FLAGGED.value

        # trend_flagged → raw_submitted (退回)
        assert report.can_transition_to(DailyReportStatus.RAW_SUBMITTED)
        report.status = DailyReportStatus.RAW_SUBMITTED.value
        assert report.status == DailyReportStatus.RAW_SUBMITTED.value

        # 重新提交后应该能正常流转
        report.trigger_trend_check()
        report.mark_trend_ok()
        assert report.status == DailyReportStatus.TREND_OK.value

    # ========== Invalid Transition Tests ==========

    def test_invalid_transitions(
        self, db_session, test_ad_account, test_user, daily_report_state_helper
    ):
        """测试所有非法状态流转"""
        invalid_transitions = daily_report_state_helper.get_invalid_transitions()

        for from_status, to_status in invalid_transitions:
            report = DailyReport(
                ad_account_id=test_ad_account.id,
                report_date=date.today(),
                status=from_status.value,
                conversions_raw=50,
                raw_spend=Decimal("100.00"),
                submitted_by=test_user.id,
            )

            # 验证非法流转返回 False
            assert not report.can_transition_to(
                to_status
            ), f"应该禁止从 {from_status.value} 流转到 {to_status.value}"

    def test_final_locked_is_terminal(self, db_session, test_ad_account, test_user):
        """测试 final_locked 是终态，不能流转到任何状态"""
        report = DailyReport(
            ad_account_id=test_ad_account.id,
            report_date=date.today(),
            status=DailyReportStatus.FINAL_LOCKED.value,
            conversions_raw=50,
            raw_spend=Decimal("100.00"),
            submitted_by=test_user.id,
        )

        # 验证终态不能流转
        for target_status in DailyReportStatus:
            if target_status != DailyReportStatus.FINAL_LOCKED:
                assert not report.can_transition_to(
                    target_status
                ), f"final_locked 不应该能流转到 {target_status.value}"

    def test_cannot_skip_trend_check(self, db_session, test_ad_account, test_user):
        """测试不能跳过趋势检查直接进入 final_pending"""
        report = DailyReport(
            ad_account_id=test_ad_account.id,
            report_date=date.today(),
            status=DailyReportStatus.RAW_SUBMITTED.value,
            conversions_raw=50,
            raw_spend=Decimal("100.00"),
            submitted_by=test_user.id,
        )

        # 不能直接跳到 final_pending
        assert not report.can_transition_to(DailyReportStatus.FINAL_PENDING)
        assert not report.can_transition_to(DailyReportStatus.FINAL_CONFIRMED)
        assert not report.can_transition_to(DailyReportStatus.FINAL_LOCKED)

    # ========== Boundary Condition Tests ==========

    def test_status_properties(self, db_session, test_ad_account, test_user):
        """测试状态属性方法"""
        report = DailyReport(
            ad_account_id=test_ad_account.id,
            report_date=date.today(),
            status=DailyReportStatus.RAW_SUBMITTED.value,
            conversions_raw=50,
            raw_spend=Decimal("100.00"),
            submitted_by=test_user.id,
        )

        # 测试各状态属性
        assert report.is_raw_submitted
        assert not report.is_trend_pending
        assert not report.is_final_locked

        report.trigger_trend_check()
        assert not report.is_raw_submitted
        assert report.is_trend_pending

        report.mark_trend_flagged("Test")
        assert report.is_trend_flagged

        report.resolve_trend(test_user.id, "Resolved")
        assert report.is_trend_resolved

    def test_transition_with_exception(self, db_session, test_ad_account, test_user):
        """测试非法流转抛出异常"""
        report = DailyReport(
            ad_account_id=test_ad_account.id,
            report_date=date.today(),
            status=DailyReportStatus.RAW_SUBMITTED.value,
            conversions_raw=50,
            raw_spend=Decimal("100.00"),
            submitted_by=test_user.id,
        )

        # 尝试非法流转应该抛出 ValueError
        with pytest.raises(ValueError, match="不允许从"):
            report.mark_trend_ok()  # 不能直接从 raw_submitted 到 trend_ok

        with pytest.raises(ValueError, match="不允许从"):
            report.lock_final()  # 不能直接从 raw_submitted 到 final_locked


class TestDailyReportTrendRules:
    """趋势风控规则测试类 (STATE_MACHINE.md v2.6 第 8.3 节)"""

    def test_trend_flag_reason_stored(self, db_session, test_ad_account, test_user):
        """测试趋势异常原因正确存储"""
        report = DailyReport(
            ad_account_id=test_ad_account.id,
            report_date=date.today(),
            status=DailyReportStatus.RAW_SUBMITTED.value,
            conversions_raw=50,
            raw_spend=Decimal("100.00"),
            submitted_by=test_user.id,
        )
        db_session.add(report)
        db_session.commit()

        report.trigger_trend_check()
        report.mark_trend_flagged("TF-001: 粉数骤降")

        # 验证异常原因存储 (存储在 trend_flag_reason 字段)
        assert report.trend_flag_reason == "TF-001: 粉数骤降"
        assert "TF-001" in report.trend_flag_reason

    def test_trend_resolution_note_stored(self, db_session, test_ad_account, test_user):
        """测试趋势复核说明正确存储"""
        report = DailyReport(
            ad_account_id=test_ad_account.id,
            report_date=date.today(),
            status=DailyReportStatus.RAW_SUBMITTED.value,
            conversions_raw=50,
            raw_spend=Decimal("100.00"),
            submitted_by=test_user.id,
        )
        db_session.add(report)
        db_session.commit()

        report.trigger_trend_check()
        report.mark_trend_flagged("TF-002: 粉数骤增")
        report.resolve_trend(test_user.id, "已确认为正常波动")

        # 验证复核说明存储 (存储在 trend_resolution_note 字段)
        assert report.trend_resolution_note == "已确认为正常波动"
        assert "已确认为正常波动" in report.trend_resolution_note


class TestPhase1SimplifiedFlow:
    """
    Phase 1 简化流程测试 (TASK-RPT-007)

    SoT 依据: STATE_MACHINE.md v2.8 §4
    Phase 1 流转: raw_submitted → trend_ok → final_confirmed (直接确认)
    """

    def test_phase1_direct_confirm_from_trend_ok(
        self, db_session, test_ad_account, test_user
    ):
        """
        测试 Phase 1 简化流程: trend_ok → final_confirmed (直接确认)
        跳过 final_pending 状态
        """
        report = DailyReport(
            ad_account_id=test_ad_account.id,
            report_date=date.today(),
            status=DailyReportStatus.RAW_SUBMITTED.value,
            conversions_raw=50,
            raw_spend=Decimal("100.00"),
            submitted_by=test_user.id,
        )
        db_session.add(report)
        db_session.commit()

        # Step 1: raw_submitted → trend_pending
        report.trigger_trend_check()
        assert report.status == DailyReportStatus.TREND_PENDING.value

        # Step 2: trend_pending → trend_ok
        report.mark_trend_ok()
        assert report.status == DailyReportStatus.TREND_OK.value

        # Step 3: trend_ok → final_confirmed (Phase 1 直接确认，跳过 final_pending)
        assert report.can_transition_to(
            DailyReportStatus.FINAL_CONFIRMED
        ), "Phase 1 应该允许从 trend_ok 直接到 final_confirmed"
        report.confirm_final(test_user.id)
        assert report.status == DailyReportStatus.FINAL_CONFIRMED.value

        # Step 4: final_confirmed → final_locked (终态)
        report.lock_final()
        assert report.status == DailyReportStatus.FINAL_LOCKED.value

    def test_phase1_allows_both_paths_from_trend_ok(
        self, db_session, test_ad_account, test_user
    ):
        """
        验证从 trend_ok 可以走两条路径:
        1. Phase 1: trend_ok → final_confirmed (直接)
        2. Phase 2: trend_ok → final_pending → final_confirmed
        """
        report = DailyReport(
            ad_account_id=test_ad_account.id,
            report_date=date.today(),
            status=DailyReportStatus.TREND_OK.value,
            conversions_raw=50,
            raw_spend=Decimal("100.00"),
            submitted_by=test_user.id,
        )

        # 验证两条路径都可用
        assert report.can_transition_to(
            DailyReportStatus.FINAL_PENDING
        ), "Phase 2 路径: trend_ok → final_pending 应该可用"
        assert report.can_transition_to(
            DailyReportStatus.FINAL_CONFIRMED
        ), "Phase 1 路径: trend_ok → final_confirmed 应该可用"

    def test_phase1_complete_short_path(self, db_session, test_ad_account, test_user):
        """
        测试 Phase 1 完整短路径:
        raw_submitted → trend_pending → trend_ok → final_confirmed → final_locked

        比 Phase 2 少一个 final_pending 状态
        """
        report = DailyReport(
            ad_account_id=test_ad_account.id,
            report_date=date.today(),
            status=DailyReportStatus.RAW_SUBMITTED.value,
            conversions_raw=100,
            raw_spend=Decimal("500.00"),
            submitted_by=test_user.id,
        )
        db_session.add(report)
        db_session.commit()

        # 完整 Phase 1 路径 (5 个状态，比 Phase 2 少 1 个)
        status_sequence = []

        # 记录初始状态
        status_sequence.append(report.status)

        # raw_submitted → trend_pending
        report.trigger_trend_check()
        status_sequence.append(report.status)

        # trend_pending → trend_ok
        report.mark_trend_ok()
        status_sequence.append(report.status)

        # trend_ok → final_confirmed (Phase 1 直接确认)
        report.confirm_final(test_user.id)
        status_sequence.append(report.status)

        # final_confirmed → final_locked
        report.lock_final()
        status_sequence.append(report.status)

        # 验证 Phase 1 路径 (5 个状态)
        expected_sequence = [
            DailyReportStatus.RAW_SUBMITTED.value,
            DailyReportStatus.TREND_PENDING.value,
            DailyReportStatus.TREND_OK.value,
            DailyReportStatus.FINAL_CONFIRMED.value,
            DailyReportStatus.FINAL_LOCKED.value,
        ]
        assert (
            status_sequence == expected_sequence
        ), f"Phase 1 路径不正确: {status_sequence} != {expected_sequence}"
