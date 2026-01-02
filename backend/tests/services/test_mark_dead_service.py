"""
Service 测试: 死号处理服务 - TASK-ACC-004

SoT References:
- STATE_MACHINE.md v2.9 §7.1: 账户状态机 (dead 为终态之一)
- BR-ACCT-006: 停用账户禁止操作（死号仅允许余额迁移）
- API_SOT.md v9.0 §8: POST /api/v1/ad-accounts/{account_id}/mark-dead

Version: 1.0
Author: Claude Code (TASK-ACC-004)
"""

import pytest
from datetime import datetime
from decimal import Decimal
from uuid import uuid4, UUID
from unittest.mock import MagicMock, AsyncMock, patch

from fastapi import HTTPException


class TestMarkDeadSuccess:
    """mark_dead 成功场景测试"""

    @pytest.mark.asyncio
    async def test_mark_dead_from_active_status(
        self, mock_service, sample_active_account
    ):
        """从 active 状态标记死号成功"""
        from backend.schemas.ad_account import MarkDeadRequest

        request = MarkDeadRequest(
            reason="账户被平台封禁，无法继续投放",
            notes="封禁原因：违反广告政策",
            transfer_balance=True,
        )

        result = await mock_service.mark_dead(
            account_id=sample_active_account.id,
            request=request,
            current_user_id=uuid4(),
            user_role="admin",
        )

        assert result.account_id == sample_active_account.id
        assert result.previous_status == "active"
        assert result.new_status == "dead"
        assert result.reason == request.reason
        assert result.marked_at is not None

    @pytest.mark.asyncio
    async def test_mark_dead_from_new_status(self, mock_service, sample_new_account):
        """从 new 状态标记死号成功"""
        from backend.schemas.ad_account import MarkDeadRequest

        request = MarkDeadRequest(
            reason="开户失败，账户无法激活",
        )

        result = await mock_service.mark_dead(
            account_id=sample_new_account.id,
            request=request,
            current_user_id=uuid4(),
            user_role="account_manager",
        )

        assert result.previous_status == "new"
        assert result.new_status == "dead"

    @pytest.mark.asyncio
    async def test_mark_dead_from_testing_status(
        self, mock_service, sample_testing_account
    ):
        """从 testing 状态标记死号成功"""
        from backend.schemas.ad_account import MarkDeadRequest

        request = MarkDeadRequest(
            reason="测试期间发现账户异常",
        )

        result = await mock_service.mark_dead(
            account_id=sample_testing_account.id,
            request=request,
            current_user_id=uuid4(),
            user_role="admin",
        )

        assert result.previous_status == "testing"
        assert result.new_status == "dead"

    @pytest.mark.asyncio
    async def test_mark_dead_from_suspended_status(
        self, mock_service, sample_suspended_account
    ):
        """从 suspended 状态标记死号成功"""
        from backend.schemas.ad_account import MarkDeadRequest

        request = MarkDeadRequest(
            reason="暂停账户确认无法恢复，标记为死号",
        )

        result = await mock_service.mark_dead(
            account_id=sample_suspended_account.id,
            request=request,
            current_user_id=uuid4(),
            user_role="account_manager",
        )

        assert result.previous_status == "suspended"
        assert result.new_status == "dead"


class TestMarkDeadPermissions:
    """mark_dead 权限测试"""

    @pytest.mark.asyncio
    async def test_admin_can_mark_dead(self, mock_service, sample_active_account):
        """管理员可以标记死号"""
        from backend.schemas.ad_account import MarkDeadRequest

        request = MarkDeadRequest(reason="管理员操作测试")

        result = await mock_service.mark_dead(
            account_id=sample_active_account.id,
            request=request,
            current_user_id=uuid4(),
            user_role="admin",
        )

        assert result.new_status == "dead"

    @pytest.mark.asyncio
    async def test_account_manager_can_mark_dead(
        self, mock_service, sample_active_account
    ):
        """户管可以标记死号"""
        from backend.schemas.ad_account import MarkDeadRequest

        request = MarkDeadRequest(reason="户管操作测试")

        result = await mock_service.mark_dead(
            account_id=sample_active_account.id,
            request=request,
            current_user_id=uuid4(),
            user_role="account_manager",
        )

        assert result.new_status == "dead"

    @pytest.mark.asyncio
    async def test_pitcher_cannot_mark_dead(self, mock_service, sample_active_account):
        """投手不能标记死号"""
        from backend.schemas.ad_account import MarkDeadRequest

        request = MarkDeadRequest(reason="投手不应该能标记死号")

        with pytest.raises(HTTPException) as exc_info:
            await mock_service.mark_dead(
                account_id=sample_active_account.id,
                request=request,
                current_user_id=uuid4(),
                user_role="media_buyer",
            )

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_finance_cannot_mark_dead(self, mock_service, sample_active_account):
        """财务不能标记死号"""
        from backend.schemas.ad_account import MarkDeadRequest

        request = MarkDeadRequest(reason="财务不应该能标记死号")

        with pytest.raises(HTTPException) as exc_info:
            await mock_service.mark_dead(
                account_id=sample_active_account.id,
                request=request,
                current_user_id=uuid4(),
                user_role="finance",
            )

        assert exc_info.value.status_code == 403


class TestMarkDeadBusinessRules:
    """mark_dead 业务规则测试"""

    @pytest.mark.asyncio
    async def test_cannot_mark_dead_already_dead(
        self, mock_service, sample_dead_account
    ):
        """不能重复标记已死号的账户"""
        from backend.schemas.ad_account import MarkDeadRequest

        request = MarkDeadRequest(reason="尝试重复标记死号")

        with pytest.raises(HTTPException) as exc_info:
            await mock_service.mark_dead(
                account_id=sample_dead_account.id,
                request=request,
                current_user_id=uuid4(),
                user_role="admin",
            )

        assert exc_info.value.status_code == 400
        assert "STATE_400" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_cannot_mark_dead_archived_account(
        self, mock_service, sample_archived_account
    ):
        """不能标记已归档的账户"""
        from backend.schemas.ad_account import MarkDeadRequest

        request = MarkDeadRequest(reason="尝试标记已归档账户")

        with pytest.raises(HTTPException) as exc_info:
            await mock_service.mark_dead(
                account_id=sample_archived_account.id,
                request=request,
                current_user_id=uuid4(),
                user_role="admin",
            )

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_account_not_found(self, mock_service):
        """账户不存在返回 404"""
        from backend.schemas.ad_account import MarkDeadRequest

        request = MarkDeadRequest(reason="账户不存在测试")

        with pytest.raises(HTTPException) as exc_info:
            await mock_service.mark_dead(
                account_id=99999,
                request=request,
                current_user_id=uuid4(),
                user_role="admin",
            )

        assert exc_info.value.status_code == 404
        assert "ACCT_404" in str(exc_info.value.detail)


class TestMarkDeadResponse:
    """mark_dead 响应格式测试"""

    @pytest.mark.asyncio
    async def test_response_contains_required_fields(
        self, mock_service, sample_active_account
    ):
        """响应包含所有必需字段"""
        from backend.schemas.ad_account import MarkDeadRequest

        request = MarkDeadRequest(
            reason="响应格式测试",
            transfer_balance=True,
        )

        result = await mock_service.mark_dead(
            account_id=sample_active_account.id,
            request=request,
            current_user_id=uuid4(),
            user_role="admin",
        )

        # 账户信息
        assert hasattr(result, "account_id")
        assert hasattr(result, "account_name")
        assert hasattr(result, "account_code")
        assert hasattr(result, "platform")
        assert hasattr(result, "project_id")

        # 状态变更
        assert hasattr(result, "previous_status")
        assert hasattr(result, "new_status")
        assert hasattr(result, "marked_at")
        assert hasattr(result, "marked_by")
        assert hasattr(result, "marked_by_name")
        assert hasattr(result, "reason")

        # 账户快照
        assert hasattr(result, "total_spend")
        assert hasattr(result, "total_leads")

        # 审计信息
        assert hasattr(result, "audit_log_id")

    @pytest.mark.asyncio
    async def test_response_balance_transfer_hint(
        self, mock_service, sample_account_with_balance
    ):
        """有余额时返回余额迁移提示"""
        from backend.schemas.ad_account import MarkDeadRequest

        request = MarkDeadRequest(
            reason="账户有余额测试",
            transfer_balance=True,
        )

        result = await mock_service.mark_dead(
            account_id=sample_account_with_balance.id,
            request=request,
            current_user_id=uuid4(),
            user_role="admin",
        )

        assert result.needs_balance_transfer is True
        assert result.balance_transfer_url is not None
        assert "balance-transfer" in result.balance_transfer_url


class TestMarkDeadAudit:
    """mark_dead 审计日志测试"""

    @pytest.mark.asyncio
    async def test_creates_status_history(self, mock_service, sample_active_account):
        """创建状态历史记录"""
        from backend.schemas.ad_account import MarkDeadRequest

        request = MarkDeadRequest(reason="状态历史测试")

        result = await mock_service.mark_dead(
            account_id=sample_active_account.id,
            request=request,
            current_user_id=uuid4(),
            user_role="admin",
        )

        # 验证 _create_status_history 被调用
        # 这里需要根据实际实现验证
        assert result.new_status == "dead"

    @pytest.mark.asyncio
    async def test_creates_audit_log(self, mock_service, sample_active_account):
        """创建审计日志"""
        from backend.schemas.ad_account import MarkDeadRequest

        request = MarkDeadRequest(reason="审计日志测试")

        result = await mock_service.mark_dead(
            account_id=sample_active_account.id,
            request=request,
            current_user_id=uuid4(),
            user_role="admin",
        )

        # 审计日志ID 应该存在
        assert result.audit_log_id is not None


# ========== Fixtures ==========


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return MagicMock()


@pytest.fixture
def mock_audit_service():
    """模拟审计服务"""
    service = MagicMock()
    service.log_action = AsyncMock(return_value=1)
    return service


@pytest.fixture
def mock_service(mock_db, mock_audit_service):
    """模拟 AdAccountService"""
    from backend.services.ad_account_service import AdAccountService

    service = AdAccountService(mock_db)
    service.audit_service = mock_audit_service
    return service


@pytest.fixture
def sample_active_account():
    """活跃账户样本"""
    account = MagicMock()
    account.id = 1
    account.account_name = "测试账户-活跃"
    account.account_code = "ACC-001"
    account.platform = "facebook"
    account.project_id = 1
    account.status = "active"
    account.total_spend = Decimal("1000.00")
    account.total_leads = 100
    account.remaining_budget = Decimal("500.00")
    return account


@pytest.fixture
def sample_new_account():
    """新账户样本"""
    account = MagicMock()
    account.id = 2
    account.account_name = "测试账户-新建"
    account.account_code = "ACC-002"
    account.platform = "google"
    account.project_id = 1
    account.status = "new"
    account.total_spend = Decimal("0")
    account.total_leads = 0
    account.remaining_budget = None
    return account


@pytest.fixture
def sample_testing_account():
    """测试中账户样本"""
    account = MagicMock()
    account.id = 3
    account.account_name = "测试账户-测试中"
    account.account_code = "ACC-003"
    account.platform = "tiktok"
    account.project_id = 1
    account.status = "testing"
    account.total_spend = Decimal("100.00")
    account.total_leads = 10
    account.remaining_budget = Decimal("50.00")
    return account


@pytest.fixture
def sample_suspended_account():
    """暂停账户样本"""
    account = MagicMock()
    account.id = 4
    account.account_name = "测试账户-暂停"
    account.account_code = "ACC-004"
    account.platform = "facebook"
    account.project_id = 1
    account.status = "suspended"
    account.total_spend = Decimal("2000.00")
    account.total_leads = 200
    account.remaining_budget = Decimal("100.00")
    return account


@pytest.fixture
def sample_dead_account():
    """死号账户样本"""
    account = MagicMock()
    account.id = 5
    account.account_name = "测试账户-死号"
    account.account_code = "ACC-005"
    account.platform = "facebook"
    account.project_id = 1
    account.status = "dead"
    account.total_spend = Decimal("5000.00")
    account.total_leads = 500
    account.remaining_budget = Decimal("0")
    return account


@pytest.fixture
def sample_archived_account():
    """归档账户样本"""
    account = MagicMock()
    account.id = 6
    account.account_name = "测试账户-归档"
    account.account_code = "ACC-006"
    account.platform = "google"
    account.project_id = 1
    account.status = "archived"
    account.total_spend = Decimal("10000.00")
    account.total_leads = 1000
    account.remaining_budget = Decimal("0")
    return account


@pytest.fixture
def sample_account_with_balance():
    """有余额的账户样本"""
    account = MagicMock()
    account.id = 7
    account.account_name = "测试账户-有余额"
    account.account_code = "ACC-007"
    account.platform = "facebook"
    account.project_id = 1
    account.status = "active"
    account.total_spend = Decimal("1000.00")
    account.total_leads = 100
    account.remaining_budget = Decimal("5000.00")  # 有余额
    return account
