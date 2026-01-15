"""
死号余额迁移服务测试 (Transfer Service Tests)

测试范围:
- 创建迁移申请
- 状态流转 (draft → pending_approval → approved → completed)
- 权限控制
- 账本分录生成 (TRANSFER_OUT/TRANSFER_IN)

SoT References:
- STATE_MACHINE.md v2.6 第12章 (transfer_requests 状态机)
- DATA_SCHEMA.md v5.2 第3.4.6节 (transfer_requests 表结构)
- LEDGER_SOT.md v1.1 (TRANSFER_OUT/TRANSFER_IN)

Version: 1.0
Author: Claude Code
"""

import pytest
from decimal import Decimal
from datetime import datetime
from uuid import uuid4

from backend.services.transfer_service import TransferService
from backend.schemas.transfer import (
    TransferRequestCreate,
    TransferRequestApprove,
    TransferRequestReject,
)
from backend.models import TransferRequest, User, AdAccount
from backend.models.enums import TransferRequestStatus, UserRole, LedgerEntryType
from backend.models.finance.ledger import LedgerEntry
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
)


class TestTransferServiceCreate:
    """迁移申请创建测试"""

    def test_create_transfer_success(
        self, db_session, funded_ad_account, test_ad_account_2, account_manager_user
    ):
        """测试成功创建迁移申请"""
        service = TransferService(db_session)

        request = TransferRequestCreate(
            source_ad_account_id=funded_ad_account.id,
            target_ad_account_id=test_ad_account_2.id,
            transfer_amount=Decimal("1000.00"),
            reason="测试迁移",
        )

        transfer = service.create_transfer(request, account_manager_user)

        assert transfer is not None
        assert transfer.id is not None
        assert transfer.request_no.startswith("TRF")
        assert transfer.source_ad_account_id == funded_ad_account.id
        assert transfer.target_ad_account_id == test_ad_account_2.id
        assert transfer.transfer_amount == Decimal("1000.00")
        assert transfer.status == TransferRequestStatus.DRAFT.value
        assert transfer.reason == "测试迁移"

    def test_create_transfer_same_account_fails(
        self, db_session, funded_ad_account, account_manager_user
    ):
        """测试源账户和目标账户相同时失败"""
        service = TransferService(db_session)

        with pytest.raises(ValueError):
            # Schema 层会验证源和目标不能相同
            TransferRequestCreate(
                source_ad_account_id=funded_ad_account.id,
                target_ad_account_id=funded_ad_account.id,
                transfer_amount=Decimal("1000.00"),
                reason="测试",
            )

    def test_create_transfer_insufficient_balance(
        self, db_session, test_ad_account, test_ad_account_2, account_manager_user
    ):
        """测试余额不足时失败"""
        # test_ad_account 没有初始余额
        service = TransferService(db_session)

        request = TransferRequestCreate(
            source_ad_account_id=test_ad_account.id,
            target_ad_account_id=test_ad_account_2.id,
            transfer_amount=Decimal("1000.00"),
            reason="测试",
        )

        with pytest.raises(BusinessLogicError) as exc_info:
            service.create_transfer(request, account_manager_user)

        assert "超过源账户余额" in str(exc_info.value)

    def test_create_transfer_permission_denied(
        self, db_session, funded_ad_account, test_ad_account_2, media_buyer_user
    ):
        """测试无权限用户创建失败"""
        service = TransferService(db_session)

        request = TransferRequestCreate(
            source_ad_account_id=funded_ad_account.id,
            target_ad_account_id=test_ad_account_2.id,
            transfer_amount=Decimal("1000.00"),
            reason="测试",
        )

        with pytest.raises(PermissionDeniedError):
            service.create_transfer(request, media_buyer_user)

    def test_create_transfer_source_not_found(
        self, db_session, test_ad_account_2, account_manager_user
    ):
        """测试源账户不存在时失败"""
        service = TransferService(db_session)

        request = TransferRequestCreate(
            source_ad_account_id=99999,  # 不存在的账户
            target_ad_account_id=test_ad_account_2.id,
            transfer_amount=Decimal("1000.00"),
            reason="测试",
        )

        with pytest.raises(ResourceNotFoundError):
            service.create_transfer(request, account_manager_user)


class TestTransferServiceStateTransition:
    """迁移申请状态流转测试"""

    @pytest.fixture
    def draft_transfer(
        self, db_session, funded_ad_account, test_ad_account_2, account_manager_user
    ):
        """创建草稿状态的迁移申请"""
        service = TransferService(db_session)
        request = TransferRequestCreate(
            source_ad_account_id=funded_ad_account.id,
            target_ad_account_id=test_ad_account_2.id,
            transfer_amount=Decimal("1000.00"),
            reason="测试迁移",
        )
        return service.create_transfer(request, account_manager_user)

    def test_submit_transfer(self, db_session, draft_transfer, account_manager_user):
        """测试提交迁移申请 (draft → pending_approval)"""
        service = TransferService(db_session)

        transfer = service.submit_transfer(draft_transfer.id, account_manager_user)

        assert transfer.status == TransferRequestStatus.PENDING_APPROVAL.value

    def test_approve_transfer(
        self, db_session, draft_transfer, account_manager_user, finance_user
    ):
        """测试审批迁移申请 (pending_approval → approved)"""
        service = TransferService(db_session)

        # 先提交
        service.submit_transfer(draft_transfer.id, account_manager_user)

        # 财务审批
        approval = TransferRequestApprove(approval_notes="审批通过")
        transfer = service.approve_transfer(draft_transfer.id, approval, finance_user)

        assert transfer.status == TransferRequestStatus.APPROVED.value
        assert transfer.approved_by == finance_user.id
        assert transfer.approved_at is not None

    def test_reject_transfer(
        self, db_session, draft_transfer, account_manager_user, finance_user
    ):
        """测试拒绝迁移申请 (pending_approval → rejected)"""
        service = TransferService(db_session)

        # 先提交
        service.submit_transfer(draft_transfer.id, account_manager_user)

        # 财务拒绝
        rejection = TransferRequestReject(rejection_reason="金额过大")
        transfer = service.reject_transfer(draft_transfer.id, rejection, finance_user)

        assert transfer.status == TransferRequestStatus.REJECTED.value
        assert transfer.rejection_reason == "金额过大"

    def test_complete_transfer(
        self,
        db_session,
        draft_transfer,
        account_manager_user,
        finance_user,
        admin_user,
        funded_ad_account,
        test_ad_account_2,
    ):
        """测试完成迁移 (approved → completed)"""
        service = TransferService(db_session)

        # 状态流转: draft → pending_approval → approved
        service.submit_transfer(draft_transfer.id, account_manager_user)
        approval = TransferRequestApprove(approval_notes="审批通过")
        service.approve_transfer(draft_transfer.id, approval, finance_user)

        # 记录初始余额 (使用 getattr 安全访问，与服务层一致)
        source_balance_before = getattr(
            funded_ad_account, "balance", Decimal("0.00")
        ) or Decimal("0.00")
        target_balance_before = getattr(
            test_ad_account_2, "balance", Decimal("0.00")
        ) or Decimal("0.00")

        # admin 完成迁移
        transfer = service.complete_transfer(draft_transfer.id, admin_user)

        assert transfer.status == TransferRequestStatus.COMPLETED.value
        assert transfer.completed_at is not None

        # 刷新账户数据
        db_session.refresh(funded_ad_account)
        db_session.refresh(test_ad_account_2)

        # 验证余额变化 (使用 getattr 安全访问)
        source_balance_after = getattr(
            funded_ad_account, "balance", Decimal("0.00")
        ) or Decimal("0.00")
        target_balance_after = getattr(
            test_ad_account_2, "balance", Decimal("0.00")
        ) or Decimal("0.00")
        assert source_balance_after == source_balance_before - Decimal("1000.00")
        assert target_balance_after == target_balance_before + Decimal("1000.00")

    def test_invalid_transition(self, db_session, draft_transfer, finance_user):
        """测试非法状态转换"""
        service = TransferService(db_session)

        # 尝试直接从 draft 审批（应该失败）
        approval = TransferRequestApprove(approval_notes="测试")

        with pytest.raises(BusinessLogicError) as exc_info:
            service.approve_transfer(draft_transfer.id, approval, finance_user)

        assert "不能执行" in str(exc_info.value) or "当前状态" in str(exc_info.value)


class TestTransferServiceLedger:
    """迁移完成后账本分录测试"""

    def test_ledger_entries_created_on_complete(
        self,
        db_session,
        funded_ad_account,
        funded_ad_account_2,
        account_manager_user,
        finance_user,
        admin_user,
    ):
        """测试完成迁移时生成正确的账本分录"""
        service = TransferService(db_session)

        # 创建并完成迁移
        request = TransferRequestCreate(
            source_ad_account_id=funded_ad_account.id,
            target_ad_account_id=funded_ad_account_2.id,
            transfer_amount=Decimal("500.00"),
            reason="账本测试",
        )
        transfer = service.create_transfer(request, account_manager_user)
        service.submit_transfer(transfer.id, account_manager_user)
        service.approve_transfer(
            transfer.id, TransferRequestApprove(approval_notes="ok"), finance_user
        )
        service.complete_transfer(transfer.id, admin_user)

        # 查询生成的账本分录
        entries = (
            db_session.query(LedgerEntry)
            .filter(
                LedgerEntry.reference_type == "transfer_request",
                LedgerEntry.reference_id == transfer.id,
            )
            .all()
        )

        assert len(entries) == 2

        # 验证 TRANSFER_OUT 分录
        transfer_out = next(
            (e for e in entries if e.entry_type == LedgerEntryType.TRANSFER_OUT.value),
            None,
        )
        assert transfer_out is not None
        assert transfer_out.ad_account_id == funded_ad_account.id
        assert transfer_out.amount == Decimal("-500.00")  # 负数表示转出

        # 验证 TRANSFER_IN 分录
        transfer_in = next(
            (e for e in entries if e.entry_type == LedgerEntryType.TRANSFER_IN.value),
            None,
        )
        assert transfer_in is not None
        assert transfer_in.ad_account_id == funded_ad_account_2.id
        assert transfer_in.amount == Decimal("500.00")  # 正数表示转入


class TestTransferServiceQuery:
    """迁移申请查询测试"""

    def test_get_transfer_by_id(
        self, db_session, funded_ad_account, test_ad_account_2, account_manager_user
    ):
        """测试根据 ID 获取迁移申请"""
        service = TransferService(db_session)

        request = TransferRequestCreate(
            source_ad_account_id=funded_ad_account.id,
            target_ad_account_id=test_ad_account_2.id,
            transfer_amount=Decimal("1000.00"),
            reason="测试",
        )
        created = service.create_transfer(request, account_manager_user)

        transfer = service.get_transfer_by_id(created.id, account_manager_user)

        assert transfer.id == created.id
        assert transfer.request_no == created.request_no

    def test_get_transfer_not_found(self, db_session, account_manager_user):
        """测试获取不存在的迁移申请"""
        service = TransferService(db_session)

        with pytest.raises(ResourceNotFoundError):
            service.get_transfer_by_id(99999, account_manager_user)

    def test_get_transfers_list(
        self, db_session, funded_ad_account, test_ad_account_2, account_manager_user
    ):
        """测试获取迁移申请列表"""
        service = TransferService(db_session)

        # 创建多个迁移申请
        for i in range(3):
            request = TransferRequestCreate(
                source_ad_account_id=funded_ad_account.id,
                target_ad_account_id=test_ad_account_2.id,
                transfer_amount=Decimal(f"{100 + i * 100}.00"),
                reason=f"测试{i+1}",
            )
            service.create_transfer(request, account_manager_user)

        transfers, total = service.get_transfers(
            account_manager_user, page=1, page_size=10
        )

        assert total >= 3
        assert len(transfers) >= 3

    def test_get_transfers_filter_by_status(
        self, db_session, funded_ad_account, test_ad_account_2, account_manager_user
    ):
        """测试按状态筛选迁移申请"""
        service = TransferService(db_session)

        # 创建一个 draft 状态的申请
        request = TransferRequestCreate(
            source_ad_account_id=funded_ad_account.id,
            target_ad_account_id=test_ad_account_2.id,
            transfer_amount=Decimal("100.00"),
            reason="筛选测试",
        )
        service.create_transfer(request, account_manager_user)

        transfers, total = service.get_transfers(
            account_manager_user, status=TransferRequestStatus.DRAFT.value
        )

        assert all(t.status == TransferRequestStatus.DRAFT.value for t in transfers)
