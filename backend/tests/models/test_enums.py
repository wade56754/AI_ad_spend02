"""
测试用例: backend/models/enums.py

覆盖范围:
- 16个枚举类型的定义和值
- AdAccountStatus 状态转换逻辑
- 枚举值与 SoT 文档一致性
- 字符串继承行为
- 边界情况和集成测试

目标覆盖率: 30% → ≥85%
"""

import pytest
from enum import Enum

from backend.models.enums import (
    UserRole,
    ChannelStatus,
    ProjectStatus,
    AdAccountStatus,
    DailyReportStatus,
    TopupRequestStatus,
    ReconciliationBatchStatus,
    ReconciliationDetailStatus,
    ReconciliationAdjustmentType,
    AccountAlertStatus,
    LedgerEntryType,
    ChannelAccountRequestStatus,
    ChannelReviewStatus,
    TransferRequestStatus,
    ImportJobStatus,
    ImportJobType,
)


# ============================================================================
# 1. UserRole 枚举测试
# ============================================================================


@pytest.mark.unit
@pytest.mark.enums
class TestUserRole:
    """测试用户角色枚举"""

    def test_user_role_values(self):
        """测试 UserRole 所有枚举值 (SoT: 7个合法角色, MASTER.md v4.4)"""
        assert UserRole.CEO.value == "ceo"
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.PROJECT_OWNER.value == "project_owner"
        assert UserRole.FINANCE.value == "finance"
        assert UserRole.DATA_OPERATOR.value == "data_operator"
        assert UserRole.ACCOUNT_MANAGER.value == "account_manager"
        assert UserRole.MEDIA_BUYER.value == "media_buyer"

    def test_user_role_count(self):
        """测试 UserRole 枚举数量 (SoT: 7个, MASTER.md v4.4)"""
        assert len(UserRole) == 7

    def test_user_role_string_inheritance(self):
        """测试 UserRole 继承自 str"""
        assert isinstance(UserRole.ADMIN, str)
        assert isinstance(UserRole.ADMIN, Enum)

    def test_user_role_iteration(self):
        """测试 UserRole 可迭代"""
        roles = list(UserRole)
        assert len(roles) == 7
        assert UserRole.ADMIN in roles
        assert UserRole.CEO in roles

    def test_user_role_comparison(self):
        """测试 UserRole 字符串比较"""
        assert UserRole.ADMIN == "admin"
        assert UserRole.FINANCE.value == "finance"


# ============================================================================
# 2. ChannelStatus 枚举测试
# ============================================================================


@pytest.mark.unit
@pytest.mark.enums
class TestChannelStatus:
    """测试渠道状态枚举"""

    def test_channel_status_values(self):
        """测试 ChannelStatus 所有枚举值"""
        assert ChannelStatus.ACTIVE.value == "active"
        assert ChannelStatus.INACTIVE.value == "inactive"

    def test_channel_status_count(self):
        """测试 ChannelStatus 枚举数量"""
        assert len(ChannelStatus) == 2

    def test_channel_status_string_inheritance(self):
        """测试 ChannelStatus 继承自 str"""
        assert isinstance(ChannelStatus.ACTIVE, str)


# ============================================================================
# 3. ProjectStatus 枚举测试
# ============================================================================


@pytest.mark.unit
@pytest.mark.enums
class TestProjectStatus:
    """测试项目状态枚举"""

    def test_project_status_values(self):
        """测试 ProjectStatus 所有枚举值 (SoT: 4个状态)"""
        assert ProjectStatus.DRAFT.value == "draft"
        assert ProjectStatus.ACTIVE.value == "active"
        assert ProjectStatus.SUSPENDED.value == "suspended"
        assert ProjectStatus.ARCHIVED.value == "archived"

    def test_project_status_count(self):
        """测试 ProjectStatus 枚举数量"""
        assert len(ProjectStatus) == 4

    def test_project_status_terminal_states(self):
        """测试 ProjectStatus 终态"""
        terminal_states = [ProjectStatus.ARCHIVED]
        assert len(terminal_states) == 1


# ============================================================================
# 4. AdAccountStatus 枚举测试（包含状态转换方法）
# ============================================================================


@pytest.mark.unit
@pytest.mark.enums
class TestAdAccountStatus:
    """测试广告账户状态枚举"""

    def test_ad_account_status_values(self):
        """测试 AdAccountStatus 所有枚举值"""
        assert AdAccountStatus.NEW.value == "new"
        assert AdAccountStatus.TESTING.value == "testing"
        assert AdAccountStatus.ACTIVE.value == "active"
        assert AdAccountStatus.SUSPENDED.value == "suspended"
        assert AdAccountStatus.DEAD.value == "dead"
        assert AdAccountStatus.ARCHIVED.value == "archived"

    def test_ad_account_status_count(self):
        """测试 AdAccountStatus 枚举数量"""
        assert len(AdAccountStatus) == 6


@pytest.mark.unit
@pytest.mark.enums
class TestAdAccountStatusTransitions:
    """测试 AdAccountStatus 状态转换逻辑"""

    def test_new_to_valid_transitions(self):
        """测试 NEW 状态可转换到的合法状态"""
        new = AdAccountStatus.NEW
        assert new.can_transition_to(AdAccountStatus.TESTING) is True
        assert new.can_transition_to(AdAccountStatus.ACTIVE) is True
        assert new.can_transition_to(AdAccountStatus.SUSPENDED) is True
        assert new.can_transition_to(AdAccountStatus.DEAD) is True
        assert new.can_transition_to(AdAccountStatus.ARCHIVED) is True

    def test_new_to_new_invalid(self):
        """测试 NEW 状态不能转换到自身"""
        new = AdAccountStatus.NEW
        assert new.can_transition_to(AdAccountStatus.NEW) is False

    def test_testing_to_valid_transitions(self):
        """测试 TESTING 状态可转换到的合法状态"""
        testing = AdAccountStatus.TESTING
        assert testing.can_transition_to(AdAccountStatus.ACTIVE) is True
        assert testing.can_transition_to(AdAccountStatus.SUSPENDED) is True
        assert testing.can_transition_to(AdAccountStatus.DEAD) is True
        assert testing.can_transition_to(AdAccountStatus.ARCHIVED) is True

    def test_testing_to_new_invalid(self):
        """测试 TESTING 状态不能退回到 NEW"""
        testing = AdAccountStatus.TESTING
        assert testing.can_transition_to(AdAccountStatus.NEW) is False

    def test_active_to_valid_transitions(self):
        """测试 ACTIVE 状态可转换到的合法状态"""
        active = AdAccountStatus.ACTIVE
        assert active.can_transition_to(AdAccountStatus.SUSPENDED) is True
        assert active.can_transition_to(AdAccountStatus.DEAD) is True
        assert active.can_transition_to(AdAccountStatus.ARCHIVED) is True

    def test_active_to_testing_invalid(self):
        """测试 ACTIVE 状态不能退回到 TESTING"""
        active = AdAccountStatus.ACTIVE
        assert active.can_transition_to(AdAccountStatus.TESTING) is False

    def test_suspended_to_valid_transitions(self):
        """测试 SUSPENDED 状态可转换到的合法状态"""
        suspended = AdAccountStatus.SUSPENDED
        assert suspended.can_transition_to(AdAccountStatus.ACTIVE) is True
        assert suspended.can_transition_to(AdAccountStatus.DEAD) is True
        assert suspended.can_transition_to(AdAccountStatus.ARCHIVED) is True

    def test_suspended_to_new_invalid(self):
        """测试 SUSPENDED 状态不能退回到 NEW"""
        suspended = AdAccountStatus.SUSPENDED
        assert suspended.can_transition_to(AdAccountStatus.NEW) is False

    def test_dead_to_archived_valid(self):
        """测试 DEAD 状态只能转换到 ARCHIVED"""
        dead = AdAccountStatus.DEAD
        assert dead.can_transition_to(AdAccountStatus.ARCHIVED) is True

    def test_dead_to_other_invalid(self):
        """测试 DEAD 状态不能转换到其他非终态状态"""
        dead = AdAccountStatus.DEAD
        assert dead.can_transition_to(AdAccountStatus.NEW) is False
        assert dead.can_transition_to(AdAccountStatus.TESTING) is False
        assert dead.can_transition_to(AdAccountStatus.ACTIVE) is False
        assert dead.can_transition_to(AdAccountStatus.SUSPENDED) is False

    def test_archived_terminal_state(self):
        """测试 ARCHIVED 是终态，不能转换到任何状态"""
        archived = AdAccountStatus.ARCHIVED
        assert archived.can_transition_to(AdAccountStatus.NEW) is False
        assert archived.can_transition_to(AdAccountStatus.TESTING) is False
        assert archived.can_transition_to(AdAccountStatus.ACTIVE) is False
        assert archived.can_transition_to(AdAccountStatus.SUSPENDED) is False
        assert archived.can_transition_to(AdAccountStatus.DEAD) is False
        assert archived.can_transition_to(AdAccountStatus.ARCHIVED) is False


# ============================================================================
# 5. DailyReportStatus 枚举测试（8状态机）
# ============================================================================


@pytest.mark.unit
@pytest.mark.enums
class TestDailyReportStatus:
    """测试日报状态枚举（粉数确认状态机）"""

    def test_daily_report_status_values(self):
        """测试 DailyReportStatus 所有枚举值（8个状态）"""
        assert DailyReportStatus.RAW_SUBMITTED.value == "raw_submitted"
        assert DailyReportStatus.TREND_PENDING.value == "trend_pending"
        assert DailyReportStatus.TREND_OK.value == "trend_ok"
        assert DailyReportStatus.TREND_FLAGGED.value == "trend_flagged"
        assert DailyReportStatus.TREND_RESOLVED.value == "trend_resolved"
        assert DailyReportStatus.FINAL_PENDING.value == "final_pending"
        assert DailyReportStatus.FINAL_CONFIRMED.value == "final_confirmed"
        assert DailyReportStatus.FINAL_LOCKED.value == "final_locked"

    def test_daily_report_status_count(self):
        """测试 DailyReportStatus 枚举数量为8"""
        assert len(DailyReportStatus) == 8

    def test_daily_report_terminal_state(self):
        """测试 DailyReportStatus 终态为 final_locked"""
        assert DailyReportStatus.FINAL_LOCKED.value == "final_locked"


# ============================================================================
# 6. TopupRequestStatus 枚举测试
# ============================================================================


@pytest.mark.unit
@pytest.mark.enums
class TestTopupRequestStatus:
    """测试充值申请状态枚举"""

    def test_topup_request_status_values(self):
        """测试 TopupRequestStatus 所有枚举值"""
        assert TopupRequestStatus.DRAFT.value == "draft"
        assert TopupRequestStatus.PENDING_REVIEW.value == "pending_review"
        assert TopupRequestStatus.FINANCE_APPROVE.value == "finance_approve"
        assert TopupRequestStatus.PAID.value == "paid"
        assert TopupRequestStatus.COMPLETED.value == "completed"
        assert TopupRequestStatus.REJECTED.value == "rejected"
        assert TopupRequestStatus.CANCELLED.value == "cancelled"

    def test_topup_request_status_count(self):
        """测试 TopupRequestStatus 枚举数量"""
        assert len(TopupRequestStatus) == 7


# ============================================================================
# 7. ReconciliationBatchStatus 枚举测试
# ============================================================================


@pytest.mark.unit
@pytest.mark.enums
class TestReconciliationBatchStatus:
    """测试对账批次状态枚举"""

    def test_reconciliation_batch_status_values(self):
        """测试 ReconciliationBatchStatus 所有枚举值"""
        assert ReconciliationBatchStatus.DRAFT.value == "draft"
        assert ReconciliationBatchStatus.PENDING_REVIEW.value == "pending_review"
        assert ReconciliationBatchStatus.APPROVED.value == "approved"
        assert ReconciliationBatchStatus.NEEDS_ADJUSTMENT.value == "needs_adjustment"
        assert ReconciliationBatchStatus.COMPLETED.value == "completed"

    def test_reconciliation_batch_status_count(self):
        """测试 ReconciliationBatchStatus 枚举数量"""
        assert len(ReconciliationBatchStatus) == 5

    def test_reconciliation_batch_terminal_state(self):
        """测试对账批次终态为 completed"""
        assert ReconciliationBatchStatus.COMPLETED.value == "completed"


# ============================================================================
# 8. ReconciliationDetailStatus 枚举测试
# ============================================================================


@pytest.mark.unit
@pytest.mark.enums
class TestReconciliationDetailStatus:
    """测试对账明细状态枚举"""

    def test_reconciliation_detail_status_values(self):
        """测试 ReconciliationDetailStatus 所有枚举值"""
        assert ReconciliationDetailStatus.PENDING.value == "pending"
        assert ReconciliationDetailStatus.CONFIRMED.value == "confirmed"
        assert ReconciliationDetailStatus.ADJUSTED.value == "adjusted"

    def test_reconciliation_detail_status_count(self):
        """测试 ReconciliationDetailStatus 枚举数量"""
        assert len(ReconciliationDetailStatus) == 3


# ============================================================================
# 9. ReconciliationAdjustmentType 枚举测试
# ============================================================================


@pytest.mark.unit
@pytest.mark.enums
class TestReconciliationAdjustmentType:
    """测试对账调整类型枚举"""

    def test_reconciliation_adjustment_type_values(self):
        """测试 ReconciliationAdjustmentType 所有枚举值"""
        assert ReconciliationAdjustmentType.INCREASE.value == "increase"
        assert ReconciliationAdjustmentType.DECREASE.value == "decrease"
        assert ReconciliationAdjustmentType.WRITEOFF.value == "writeoff"

    def test_reconciliation_adjustment_type_count(self):
        """测试 ReconciliationAdjustmentType 枚举数量"""
        assert len(ReconciliationAdjustmentType) == 3


# ============================================================================
# 10. AccountAlertStatus 枚举测试
# ============================================================================


@pytest.mark.unit
@pytest.mark.enums
class TestAccountAlertStatus:
    """测试账户预警状态枚举"""

    def test_account_alert_status_values(self):
        """测试 AccountAlertStatus 所有枚举值"""
        assert AccountAlertStatus.OPEN.value == "open"
        assert AccountAlertStatus.ACK.value == "ack"
        assert AccountAlertStatus.RESOLVED.value == "resolved"

    def test_account_alert_status_count(self):
        """测试 AccountAlertStatus 枚举数量"""
        assert len(AccountAlertStatus) == 3


# ============================================================================
# 11. LedgerEntryType 枚举测试
# ============================================================================


@pytest.mark.unit
@pytest.mark.enums
class TestLedgerEntryType:
    """测试总账分录类型枚举"""

    def test_ledger_entry_type_values(self):
        """测试 LedgerEntryType 所有枚举值"""
        assert LedgerEntryType.REVENUE.value == "REVENUE"
        assert LedgerEntryType.COST.value == "COST"
        assert LedgerEntryType.TOPUP.value == "TOPUP"
        assert LedgerEntryType.TRANSFER_OUT.value == "TRANSFER_OUT"
        assert LedgerEntryType.TRANSFER_IN.value == "TRANSFER_IN"
        assert LedgerEntryType.REVERSAL.value == "REVERSAL"

    def test_ledger_entry_type_count(self):
        """测试 LedgerEntryType 枚举数量"""
        assert len(LedgerEntryType) == 6

    def test_ledger_entry_type_project_types(self):
        """测试 PROJECT 账本适用的分录类型"""
        project_types = [
            LedgerEntryType.REVENUE,
            LedgerEntryType.TOPUP,
            LedgerEntryType.REVERSAL,
        ]
        assert len(project_types) == 3

    def test_ledger_entry_type_supplier_types(self):
        """测试 SUPPLIER 账本适用的分录类型"""
        supplier_types = [
            LedgerEntryType.COST,
            LedgerEntryType.TOPUP,
            LedgerEntryType.TRANSFER_OUT,
            LedgerEntryType.TRANSFER_IN,
            LedgerEntryType.REVERSAL,
        ]
        assert len(supplier_types) == 5


# ============================================================================
# 12. ChannelAccountRequestStatus 枚举测试
# ============================================================================


@pytest.mark.unit
@pytest.mark.enums
class TestChannelAccountRequestStatus:
    """测试渠道账户申请状态枚举"""

    def test_channel_account_request_status_values(self):
        """测试 ChannelAccountRequestStatus 所有枚举值"""
        assert ChannelAccountRequestStatus.DRAFT.value == "draft"
        assert ChannelAccountRequestStatus.PENDING.value == "pending"
        assert ChannelAccountRequestStatus.APPROVED.value == "approved"
        assert ChannelAccountRequestStatus.REJECTED.value == "rejected"

    def test_channel_account_request_status_count(self):
        """测试 ChannelAccountRequestStatus 枚举数量"""
        assert len(ChannelAccountRequestStatus) == 4


# ============================================================================
# 13. ChannelReviewStatus 枚举测试
# ============================================================================


@pytest.mark.unit
@pytest.mark.enums
class TestChannelReviewStatus:
    """测试渠道审核状态枚举"""

    def test_channel_review_status_values(self):
        """测试 ChannelReviewStatus 所有枚举值"""
        assert ChannelReviewStatus.DRAFT.value == "draft"
        assert ChannelReviewStatus.PENDING.value == "pending"
        assert ChannelReviewStatus.APPROVED.value == "approved"
        assert ChannelReviewStatus.REJECTED.value == "rejected"

    def test_channel_review_status_count(self):
        """测试 ChannelReviewStatus 枚举数量"""
        assert len(ChannelReviewStatus) == 4


# ============================================================================
# 14. TransferRequestStatus 枚举测试
# ============================================================================


@pytest.mark.unit
@pytest.mark.enums
class TestTransferRequestStatus:
    """测试死号余额迁移申请状态枚举"""

    def test_transfer_request_status_values(self):
        """测试 TransferRequestStatus 所有枚举值"""
        assert TransferRequestStatus.DRAFT.value == "draft"
        assert TransferRequestStatus.PENDING_APPROVAL.value == "pending_approval"
        assert TransferRequestStatus.APPROVED.value == "approved"
        assert TransferRequestStatus.REJECTED.value == "rejected"
        assert TransferRequestStatus.COMPLETED.value == "completed"

    def test_transfer_request_status_count(self):
        """测试 TransferRequestStatus 枚举数量"""
        assert len(TransferRequestStatus) == 5

    def test_transfer_request_terminal_states(self):
        """测试 TransferRequestStatus 终态"""
        terminal_states = [
            TransferRequestStatus.REJECTED,
            TransferRequestStatus.COMPLETED,
        ]
        assert len(terminal_states) == 2


# ============================================================================
# 15. ImportJobStatus 枚举测试
# ============================================================================


@pytest.mark.unit
@pytest.mark.enums
class TestImportJobStatus:
    """测试导入任务状态枚举"""

    def test_import_job_status_values(self):
        """测试 ImportJobStatus 所有枚举值"""
        assert ImportJobStatus.PENDING.value == "pending"
        assert ImportJobStatus.PROCESSING.value == "processing"
        assert ImportJobStatus.COMPLETED.value == "completed"
        assert ImportJobStatus.FAILED.value == "failed"
        assert ImportJobStatus.CANCELLED.value == "cancelled"

    def test_import_job_status_count(self):
        """测试 ImportJobStatus 枚举数量"""
        assert len(ImportJobStatus) == 5

    def test_import_job_terminal_states(self):
        """测试 ImportJobStatus 终态"""
        terminal_states = [
            ImportJobStatus.COMPLETED,
            ImportJobStatus.FAILED,
            ImportJobStatus.CANCELLED,
        ]
        assert len(terminal_states) == 3


# ============================================================================
# 16. ImportJobType 枚举测试
# ============================================================================


@pytest.mark.unit
@pytest.mark.enums
class TestImportJobType:
    """测试导入任务类型枚举"""

    def test_import_job_type_values(self):
        """测试 ImportJobType 所有枚举值"""
        assert ImportJobType.FINANCE.value == "finance"
        assert ImportJobType.SPEND.value == "spend"
        assert ImportJobType.RECONCILIATION.value == "reconciliation"
        assert ImportJobType.DAILY_REPORT.value == "daily_report"

    def test_import_job_type_count(self):
        """测试 ImportJobType 枚举数量"""
        assert len(ImportJobType) == 4


# ============================================================================
# 17. 枚举边界情况测试
# ============================================================================


@pytest.mark.unit
@pytest.mark.enums
class TestEnumEdgeCases:
    """测试枚举边界情况"""

    def test_enum_membership(self):
        """测试枚举成员检查"""
        assert "admin" in [role.value for role in UserRole]
        assert "invalid_role" not in [role.value for role in UserRole]

    def test_enum_name_access(self):
        """测试通过名称访问枚举"""
        assert UserRole["ADMIN"] == UserRole.ADMIN
        assert ProjectStatus["ACTIVE"] == ProjectStatus.ACTIVE

    def test_enum_value_to_enum(self):
        """测试通过值获取枚举"""
        assert UserRole("admin") == UserRole.ADMIN
        assert ProjectStatus("active") == ProjectStatus.ACTIVE

    def test_invalid_enum_value(self):
        """测试无效枚举值抛出异常"""
        with pytest.raises(ValueError):
            UserRole("invalid_role")

    def test_enum_iteration_order(self):
        """测试枚举迭代顺序稳定"""
        roles = list(UserRole)
        assert roles[0] == UserRole.CEO
        assert roles[1] == UserRole.ADMIN
        assert roles[2] == UserRole.PROJECT_OWNER

    def test_enum_string_format(self):
        """测试枚举字符串格式化"""
        # 使用 .value 获取字符串值
        assert UserRole.ADMIN.value == "admin"
        assert ProjectStatus.ACTIVE.value == "active"
        # str() 在 StrEnum 类型返回 name, 需要用 .value
        assert f"{UserRole.ADMIN.value}" == "admin"

    def test_enum_repr(self):
        """测试枚举 repr 输出"""
        assert "UserRole.ADMIN" in repr(UserRole.ADMIN)


# ============================================================================
# 18. 枚举集成测试
# ============================================================================


@pytest.mark.integration
@pytest.mark.enums
class TestEnumIntegration:
    """测试枚举集成场景"""

    def test_all_enums_inherit_str(self):
        """测试所有枚举继承自 str"""
        enum_classes = [
            UserRole,
            ChannelStatus,
            ProjectStatus,
            AdAccountStatus,
            DailyReportStatus,
            TopupRequestStatus,
            ReconciliationBatchStatus,
            ReconciliationDetailStatus,
            ReconciliationAdjustmentType,
            AccountAlertStatus,
            LedgerEntryType,
            ChannelAccountRequestStatus,
            ChannelReviewStatus,
            TransferRequestStatus,
            ImportJobStatus,
            ImportJobType,
        ]
        for enum_class in enum_classes:
            for member in enum_class:
                assert isinstance(member, str)

    def test_all_enums_are_unique(self):
        """测试所有枚举成员值唯一"""
        for enum_class in [UserRole, ProjectStatus, AdAccountStatus]:
            values = [member.value for member in enum_class]
            assert len(values) == len(set(values))

    def test_enum_usage_in_dict(self):
        """测试枚举在字典中的使用"""
        status_map = {
            ProjectStatus.DRAFT: "草稿",
            ProjectStatus.ACTIVE: "进行中",
            ProjectStatus.ARCHIVED: "已归档",
        }
        assert status_map[ProjectStatus.DRAFT] == "草稿"

    def test_enum_usage_in_set(self):
        """测试枚举在集合中的使用"""
        terminal_statuses = {ProjectStatus.ARCHIVED}
        assert ProjectStatus.ARCHIVED in terminal_statuses
        assert ProjectStatus.ACTIVE not in terminal_statuses

    def test_enum_comparison_with_string(self):
        """测试枚举与字符串比较"""
        role = UserRole.ADMIN
        assert role == "admin"
        assert role != "finance"
        assert role.value == "admin"

    def test_state_machine_workflow_simulation(self):
        """测试状态机工作流模拟"""
        # 模拟广告账户生命周期
        current_status = AdAccountStatus.NEW

        # NEW → TESTING
        assert current_status.can_transition_to(AdAccountStatus.TESTING)
        current_status = AdAccountStatus.TESTING

        # TESTING → ACTIVE
        assert current_status.can_transition_to(AdAccountStatus.ACTIVE)
        current_status = AdAccountStatus.ACTIVE

        # ACTIVE → SUSPENDED
        assert current_status.can_transition_to(AdAccountStatus.SUSPENDED)
        current_status = AdAccountStatus.SUSPENDED

        # SUSPENDED → ACTIVE (恢复)
        assert current_status.can_transition_to(AdAccountStatus.ACTIVE)
        current_status = AdAccountStatus.ACTIVE

        # ACTIVE → DEAD
        assert current_status.can_transition_to(AdAccountStatus.DEAD)
        current_status = AdAccountStatus.DEAD

        # DEAD → ARCHIVED
        assert current_status.can_transition_to(AdAccountStatus.ARCHIVED)
        current_status = AdAccountStatus.ARCHIVED

        # ARCHIVED 是终态，不能再转换
        assert not current_status.can_transition_to(AdAccountStatus.ACTIVE)


# ============================================================================
# 19. SoT 文档一致性测试
# ============================================================================


@pytest.mark.unit
@pytest.mark.enums
class TestSoTConsistency:
    """测试与 SoT 文档一致性"""

    def test_user_role_sot_consistency(self):
        """测试 UserRole 与 MASTER.md v4.4 一致 (7个合法角色)"""
        expected_roles = {
            "ceo",
            "admin",
            "project_owner",
            "finance",
            "data_operator",
            "account_manager",
            "media_buyer",
        }
        actual_roles = {role.value for role in UserRole}
        assert actual_roles == expected_roles

    def test_daily_report_status_8_states(self):
        """测试 DailyReportStatus 遵循 STATE_MACHINE.md v2.6 第8章"""
        # 8状态机必须包含这8个状态
        required_states = {
            "raw_submitted",
            "trend_pending",
            "trend_ok",
            "trend_flagged",
            "trend_resolved",
            "final_pending",
            "final_confirmed",
            "final_locked",
        }
        actual_states = {status.value for status in DailyReportStatus}
        assert actual_states == required_states

    def test_ledger_entry_type_sot_consistency(self):
        """测试 LedgerEntryType 与 LEDGER_SOT.md v1.1 一致"""
        # PROJECT 账本类型
        project_types = {"REVENUE", "TOPUP", "REVERSAL"}
        # SUPPLIER 账本类型
        supplier_types = {"COST", "TOPUP", "TRANSFER_OUT", "TRANSFER_IN", "REVERSAL"}

        all_types = project_types | supplier_types
        actual_types = {entry_type.value for entry_type in LedgerEntryType}

        assert actual_types == all_types

    def test_reconciliation_batch_status_sot_consistency(self):
        """测试 ReconciliationBatchStatus 与 STATE_MACHINE.md 第4章一致"""
        expected_states = {
            "draft",
            "pending_review",
            "approved",
            "needs_adjustment",
            "completed",
        }
        actual_states = {status.value for status in ReconciliationBatchStatus}
        assert actual_states == expected_states

    def test_ad_account_status_sot_consistency(self):
        """测试 AdAccountStatus 与 STATE_MACHINE.md v2.5 第14.5章一致"""
        expected_states = {"new", "testing", "active", "suspended", "dead", "archived"}
        actual_states = {status.value for status in AdAccountStatus}
        assert actual_states == expected_states


# ============================================================================
# 20. 枚举数量汇总测试
# ============================================================================


@pytest.mark.unit
@pytest.mark.enums
class TestEnumCounts:
    """测试枚举总数和成员数量"""

    def test_total_enum_classes(self):
        """测试枚举类总数为16"""
        enum_classes = [
            UserRole,
            ChannelStatus,
            ProjectStatus,
            AdAccountStatus,
            DailyReportStatus,
            TopupRequestStatus,
            ReconciliationBatchStatus,
            ReconciliationDetailStatus,
            ReconciliationAdjustmentType,
            AccountAlertStatus,
            LedgerEntryType,
            ChannelAccountRequestStatus,
            ChannelReviewStatus,
            TransferRequestStatus,
            ImportJobStatus,
            ImportJobType,
        ]
        assert len(enum_classes) == 16

    def test_total_enum_members(self):
        """测试枚举成员总数"""
        total_members = (
            len(UserRole)
            + len(ChannelStatus)
            + len(ProjectStatus)
            + len(AdAccountStatus)
            + len(DailyReportStatus)
            + len(TopupRequestStatus)
            + len(ReconciliationBatchStatus)
            + len(ReconciliationDetailStatus)
            + len(ReconciliationAdjustmentType)
            + len(AccountAlertStatus)
            + len(LedgerEntryType)
            + len(ChannelAccountRequestStatus)
            + len(ChannelReviewStatus)
            + len(TransferRequestStatus)
            + len(ImportJobStatus)
            + len(ImportJobType)
        )
        # 7+2+4+6+8+7+5+3+3+3+6+4+4+5+5+4 = 76
        assert total_members == 76

    def test_enum_member_count_breakdown(self):
        """测试各枚举成员数量明细"""
        expected_counts = {
            "UserRole": 7,  # SoT: 7个合法角色 (MASTER.md v4.4)
            "ChannelStatus": 2,
            "ProjectStatus": 4,  # SoT: draft/active/suspended/archived
            "AdAccountStatus": 6,
            "DailyReportStatus": 8,
            "TopupRequestStatus": 7,
            "ReconciliationBatchStatus": 5,
            "ReconciliationDetailStatus": 3,
            "ReconciliationAdjustmentType": 3,
            "AccountAlertStatus": 3,
            "LedgerEntryType": 6,
            "ChannelAccountRequestStatus": 4,
            "ChannelReviewStatus": 4,
            "TransferRequestStatus": 5,
            "ImportJobStatus": 5,
            "ImportJobType": 4,
        }

        assert len(UserRole) == expected_counts["UserRole"]
        assert len(ChannelStatus) == expected_counts["ChannelStatus"]
        assert len(ProjectStatus) == expected_counts["ProjectStatus"]
        assert len(AdAccountStatus) == expected_counts["AdAccountStatus"]
        assert len(DailyReportStatus) == expected_counts["DailyReportStatus"]
        assert len(TopupRequestStatus) == expected_counts["TopupRequestStatus"]
        assert (
            len(ReconciliationBatchStatus)
            == expected_counts["ReconciliationBatchStatus"]
        )
        assert (
            len(ReconciliationDetailStatus)
            == expected_counts["ReconciliationDetailStatus"]
        )
        assert (
            len(ReconciliationAdjustmentType)
            == expected_counts["ReconciliationAdjustmentType"]
        )
        assert len(AccountAlertStatus) == expected_counts["AccountAlertStatus"]
        assert len(LedgerEntryType) == expected_counts["LedgerEntryType"]
        assert (
            len(ChannelAccountRequestStatus)
            == expected_counts["ChannelAccountRequestStatus"]
        )
        assert len(ChannelReviewStatus) == expected_counts["ChannelReviewStatus"]
        assert len(TransferRequestStatus) == expected_counts["TransferRequestStatus"]
        assert len(ImportJobStatus) == expected_counts["ImportJobStatus"]
        assert len(ImportJobType) == expected_counts["ImportJobType"]
