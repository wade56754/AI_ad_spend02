"""
测试用例: 账户转移 API - TASK-ACC-003

SoT References:
- BR-ACCT.md v5.5 §BR-ACCT-002: 账户唯一性
- BR-ACCT.md v5.5 §BR-ACCT-005: 审计日志
- AUTH_SPEC.md v2.0 §5.3.1: 权限控制

覆盖范围:
- transfer_account() 服务方法
- 权限检查 (admin/account_manager)
- 业务规则验证 (必须有原负责人, 目标必须是投手)
- 审计日志记录
- 边界情况和异常处理

Version: 1.0
Author: Claude Code (TASK-ACC-003)
"""

import pytest
from uuid import UUID, uuid4
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from backend.services.ad_account_service import AdAccountService
from backend.schemas.ad_account import AccountTransferRequest, AccountTransferResponse
from backend.exceptions import ValidationError, NotFoundError, PermissionError


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    return Mock()


@pytest.fixture
def ad_account_service(mock_db):
    """广告账户服务实例"""
    mock_audit_service = AsyncMock()
    mock_audit_service.log_action.return_value = 123  # 返回审计日志ID
    with patch(
        "backend.services.ad_account_service.AuditLogService",
        return_value=mock_audit_service,
    ):
        service = AdAccountService(mock_db)
        service.audit_service = mock_audit_service
        return service


@pytest.fixture
def sample_account_with_owner():
    """示例广告账户 - 已分配给投手"""
    from backend.tests.utils.mock_helpers import SQLAlchemyMockBuilder

    return SQLAlchemyMockBuilder.build_ad_account(
        account_code="AD001",
        account_name="测试广告账户",
        status="active",
        project_id=1,
        channel_id=1,
        owner_id=uuid4(),  # 已有负责人
        balance=None,
    )


@pytest.fixture
def sample_account_without_owner():
    """示例广告账户 - 未分配"""
    from backend.tests.utils.mock_helpers import SQLAlchemyMockBuilder

    account = SQLAlchemyMockBuilder.build_ad_account(
        account_code="AD002",
        account_name="未分配账户",
        status="active",
        project_id=1,
        channel_id=1,
        owner_id=None,  # 无负责人
        balance=None,
    )
    return account


@pytest.fixture
def sample_pitcher():
    """示例投手用户"""
    from backend.models import User

    user = Mock(spec=User)
    user.id = uuid4()
    user.role = "pitcher"
    user.username = "pitcher01"
    user.full_name = "测试投手"
    user.is_active = True
    return user


@pytest.fixture
def sample_non_pitcher():
    """示例非投手用户"""
    from backend.models import User

    user = Mock(spec=User)
    user.id = uuid4()
    user.role = "finance"
    user.username = "finance01"
    user.full_name = "财务人员"
    user.is_active = True
    return user


@pytest.fixture
def sample_previous_owner():
    """示例原负责人"""
    from backend.models import User

    user = Mock(spec=User)
    user.id = uuid4()
    user.role = "pitcher"
    user.username = "pitcher_old"
    user.full_name = "原投手"
    user.is_active = True
    return user


# ============================================================================
# 1. 账户转移成功测试
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.ad_account
class TestTransferAccountSuccess:
    """测试账户转移成功场景"""

    async def test_transfer_account_by_admin(
        self,
        ad_account_service,
        mock_db,
        sample_account_with_owner,
        sample_pitcher,
        sample_previous_owner,
    ):
        """测试管理员转移账户成功"""
        # 设置原负责人
        previous_owner_id = sample_previous_owner.id
        sample_account_with_owner.owner_id = previous_owner_id

        # Mock查询
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [
            sample_account_with_owner,  # 账户查询
            sample_previous_owner,  # 原负责人查询
            sample_pitcher,  # 目标投手查询
        ]
        mock_db.query.return_value = mock_query

        # 创建转移请求
        request = AccountTransferRequest(
            target_pitcher_id=sample_pitcher.id, reason="投放策略调整，需要更换投手", notes="原投手已离职"
        )

        # 执行转移
        result = await ad_account_service.transfer_account(
            account_id=1,
            request=request,
            current_user_id=str(uuid4()),
            current_user_name="管理员",
            user_role="admin",
        )

        # 验证
        assert result.account_id == 1
        assert result.previous_pitcher_id == previous_owner_id
        assert result.new_pitcher_id == sample_pitcher.id
        assert result.reason == "投放策略调整，需要更换投手"
        mock_db.commit.assert_called()

    async def test_transfer_account_by_account_manager(
        self,
        ad_account_service,
        mock_db,
        sample_account_with_owner,
        sample_pitcher,
        sample_previous_owner,
    ):
        """测试户管转移账户成功"""
        previous_owner_id = sample_previous_owner.id
        sample_account_with_owner.owner_id = previous_owner_id

        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [
            sample_account_with_owner,
            sample_previous_owner,
            sample_pitcher,
        ]
        mock_db.query.return_value = mock_query

        request = AccountTransferRequest(
            target_pitcher_id=sample_pitcher.id, reason="工作量调配，转移账户"
        )

        result = await ad_account_service.transfer_account(
            account_id=1,
            request=request,
            current_user_id=str(uuid4()),
            current_user_name="户管A",
            user_role="account_manager",
        )

        assert result.account_id == 1
        assert result.new_pitcher_id == sample_pitcher.id

    async def test_transfer_audit_log_recorded(
        self,
        ad_account_service,
        mock_db,
        sample_account_with_owner,
        sample_pitcher,
        sample_previous_owner,
    ):
        """测试转移后记录审计日志 (BR-ACCT-005)"""
        previous_owner_id = sample_previous_owner.id
        sample_account_with_owner.owner_id = previous_owner_id

        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [
            sample_account_with_owner,
            sample_previous_owner,
            sample_pitcher,
        ]
        mock_db.query.return_value = mock_query

        request = AccountTransferRequest(
            target_pitcher_id=sample_pitcher.id, reason="审计日志测试"
        )

        current_user_id = str(uuid4())
        result = await ad_account_service.transfer_account(
            account_id=1,
            request=request,
            current_user_id=current_user_id,
            current_user_name="管理员",
            user_role="admin",
        )

        # 验证审计日志被调用
        ad_account_service.audit_service.log_action.assert_called_once()
        call_args = ad_account_service.audit_service.log_action.call_args

        assert call_args.kwargs["action"] == "transfer"
        assert call_args.kwargs["resource_type"] == "ad_account"
        assert call_args.kwargs["resource_id"] == 1
        assert "old_value" in call_args.kwargs
        assert "new_value" in call_args.kwargs
        assert result.audit_log_id == 123


# ============================================================================
# 2. 权限检查测试
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.ad_account
class TestTransferAccountPermissions:
    """测试账户转移权限检查"""

    async def test_transfer_denied_for_pitcher(
        self, ad_account_service, mock_db, sample_account_with_owner, sample_pitcher
    ):
        """测试投手无权转移账户"""
        request = AccountTransferRequest(
            target_pitcher_id=sample_pitcher.id, reason="投手不应该能转移账户"
        )

        with pytest.raises(PermissionError) as exc:
            await ad_account_service.transfer_account(
                account_id=1,
                request=request,
                current_user_id=str(uuid4()),
                current_user_name="投手",
                user_role="pitcher",
            )

        assert "无权限" in str(exc.value) or "仅管理员和户管" in str(exc.value)

    async def test_transfer_denied_for_finance(
        self, ad_account_service, mock_db, sample_account_with_owner, sample_pitcher
    ):
        """测试财务无权转移账户"""
        request = AccountTransferRequest(
            target_pitcher_id=sample_pitcher.id, reason="财务不应该能转移账户"
        )

        with pytest.raises(PermissionError) as exc:
            await ad_account_service.transfer_account(
                account_id=1,
                request=request,
                current_user_id=str(uuid4()),
                current_user_name="财务",
                user_role="finance",
            )

        assert "无权限" in str(exc.value) or "仅管理员和户管" in str(exc.value)

    async def test_transfer_denied_for_project_owner(
        self, ad_account_service, mock_db, sample_account_with_owner, sample_pitcher
    ):
        """测试项目负责人无权转移账户"""
        request = AccountTransferRequest(
            target_pitcher_id=sample_pitcher.id, reason="项目负责人不应该能转移账户"
        )

        with pytest.raises(PermissionError) as exc:
            await ad_account_service.transfer_account(
                account_id=1,
                request=request,
                current_user_id=str(uuid4()),
                current_user_name="项目负责人",
                user_role="project_owner",
            )

        assert "无权限" in str(exc.value) or "仅管理员和户管" in str(exc.value)


# ============================================================================
# 3. 业务规则验证测试
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.ad_account
class TestTransferAccountBusinessRules:
    """测试账户转移业务规则验证"""

    async def test_transfer_requires_existing_owner(
        self, ad_account_service, mock_db, sample_account_without_owner, sample_pitcher
    ):
        """测试转移要求账户必须有原负责人 (区别于首次分配)"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_account_without_owner
        mock_db.query.return_value = mock_query

        request = AccountTransferRequest(
            target_pitcher_id=sample_pitcher.id, reason="尝试转移未分配的账户"
        )

        with pytest.raises(ValidationError) as exc:
            await ad_account_service.transfer_account(
                account_id=1,
                request=request,
                current_user_id=str(uuid4()),
                current_user_name="管理员",
                user_role="admin",
            )

        assert "未分配" in str(exc.value) or "无负责人" in str(exc.value)

    async def test_transfer_target_must_be_pitcher(
        self,
        ad_account_service,
        mock_db,
        sample_account_with_owner,
        sample_non_pitcher,
        sample_previous_owner,
    ):
        """测试转移目标必须是投手角色"""
        sample_account_with_owner.owner_id = sample_previous_owner.id

        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [
            sample_account_with_owner,  # 账户
            sample_previous_owner,  # 原负责人
            sample_non_pitcher,  # 目标不是投手
        ]
        mock_db.query.return_value = mock_query

        request = AccountTransferRequest(
            target_pitcher_id=sample_non_pitcher.id, reason="目标不是投手"
        )

        with pytest.raises(ValidationError) as exc:
            await ad_account_service.transfer_account(
                account_id=1,
                request=request,
                current_user_id=str(uuid4()),
                current_user_name="管理员",
                user_role="admin",
            )

        assert "投手" in str(exc.value) or "pitcher" in str(exc.value).lower()

    async def test_transfer_cannot_transfer_to_same_owner(
        self,
        ad_account_service,
        mock_db,
        sample_account_with_owner,
        sample_previous_owner,
    ):
        """测试不能转移给当前负责人"""
        sample_account_with_owner.owner_id = sample_previous_owner.id

        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [
            sample_account_with_owner,
            sample_previous_owner,
        ]
        mock_db.query.return_value = mock_query

        # 尝试转移给同一个人
        request = AccountTransferRequest(
            target_pitcher_id=sample_previous_owner.id, reason="转移给同一个人"
        )

        with pytest.raises(ValidationError) as exc:
            await ad_account_service.transfer_account(
                account_id=1,
                request=request,
                current_user_id=str(uuid4()),
                current_user_name="管理员",
                user_role="admin",
            )

        assert "相同" in str(exc.value) or "同一" in str(exc.value)


# ============================================================================
# 4. 异常处理测试
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.ad_account
class TestTransferAccountExceptions:
    """测试账户转移异常处理"""

    async def test_transfer_account_not_found(
        self, ad_account_service, mock_db, sample_pitcher
    ):
        """测试账户不存在时抛出异常"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        request = AccountTransferRequest(
            target_pitcher_id=sample_pitcher.id, reason="账户不存在"
        )

        with pytest.raises(NotFoundError) as exc:
            await ad_account_service.transfer_account(
                account_id=999,
                request=request,
                current_user_id=str(uuid4()),
                current_user_name="管理员",
                user_role="admin",
            )

        assert "账户" in str(exc.value) and "不存在" in str(exc.value)

    async def test_transfer_target_user_not_found(
        self,
        ad_account_service,
        mock_db,
        sample_account_with_owner,
        sample_previous_owner,
    ):
        """测试目标用户不存在时抛出异常"""
        sample_account_with_owner.owner_id = sample_previous_owner.id

        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [
            sample_account_with_owner,
            sample_previous_owner,
            None,  # 目标用户不存在
        ]
        mock_db.query.return_value = mock_query

        request = AccountTransferRequest(target_pitcher_id=uuid4(), reason="目标用户不存在")

        with pytest.raises(NotFoundError) as exc:
            await ad_account_service.transfer_account(
                account_id=1,
                request=request,
                current_user_id=str(uuid4()),
                current_user_name="管理员",
                user_role="admin",
            )

        # 服务层错误消息可能是 "目标投手 ... 不存在" 或 "用户 ... 不存在"
        assert "不存在" in str(exc.value) and (
            "用户" in str(exc.value) or "投手" in str(exc.value)
        )

    async def test_transfer_reason_required(self, ad_account_service, mock_db):
        """测试转移原因为必填字段"""
        # Pydantic 验证会在创建 Request 时触发
        with pytest.raises(Exception):  # ValidationError from Pydantic
            AccountTransferRequest(
                target_pitcher_id=uuid4(), reason=""  # 空原因应该失败 (min_length=5)
            )

    async def test_transfer_reason_too_short(self, ad_account_service, mock_db):
        """测试转移原因太短"""
        with pytest.raises(Exception):  # ValidationError from Pydantic
            AccountTransferRequest(target_pitcher_id=uuid4(), reason="1234")  # 少于5个字符


# ============================================================================
# 5. 响应格式验证测试
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.ad_account
class TestTransferAccountResponse:
    """测试账户转移响应格式"""

    async def test_response_contains_all_required_fields(
        self,
        ad_account_service,
        mock_db,
        sample_account_with_owner,
        sample_pitcher,
        sample_previous_owner,
    ):
        """测试响应包含所有必需字段"""
        previous_owner_id = sample_previous_owner.id
        sample_account_with_owner.owner_id = previous_owner_id
        sample_account_with_owner.account_name = "测试账户"
        sample_account_with_owner.account_code = "AD001"

        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [
            sample_account_with_owner,
            sample_previous_owner,
            sample_pitcher,
        ]
        mock_db.query.return_value = mock_query

        request = AccountTransferRequest(
            target_pitcher_id=sample_pitcher.id, reason="响应格式测试"
        )

        current_user_id = str(uuid4())
        result = await ad_account_service.transfer_account(
            account_id=1,
            request=request,
            current_user_id=current_user_id,
            current_user_name="管理员",
            user_role="admin",
        )

        # 验证响应类型
        assert isinstance(result, AccountTransferResponse)

        # 验证必需字段
        assert result.account_id == 1
        assert result.account_name == "测试账户"
        assert result.account_code == "AD001"
        assert result.previous_pitcher_id == previous_owner_id
        assert result.previous_pitcher_name is not None
        assert result.new_pitcher_id == sample_pitcher.id
        assert result.new_pitcher_name is not None
        assert result.transferred_at is not None
        assert result.transferred_by is not None
        assert result.transferred_by_name == "管理员"
        assert result.reason == "响应格式测试"
