"""
Service 测试: 密码重置服务 - TASK-AUTH-002

SoT References:
- AUTH_SPEC.md v2.2 §6.5: 密码重置流程
- BR-AUTH-003: 密码强度规则（min 8 chars, uppercase, lowercase, digits）

Version: 1.0
Author: Claude Code (TASK-AUTH-002)
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from jose import jwt


class TestCreateResetToken:
    """create_reset_token 令牌生成测试"""

    def test_create_reset_token_returns_jwt(self, mock_auth_service):
        """创建重置令牌返回有效 JWT"""
        user_id = str(uuid4())
        token = mock_auth_service.create_reset_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT 通常较长

    def test_create_reset_token_contains_correct_claims(self, mock_auth_service):
        """重置令牌包含正确的声明"""
        from backend.services.local_auth_service import JWT_SECRET_KEY, JWT_ALGORITHM

        user_id = str(uuid4())
        token = mock_auth_service.create_reset_token(user_id)

        # 解码验证
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        assert payload["sub"] == user_id
        assert payload["type"] == "reset"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload  # JWT ID

    def test_create_reset_token_expires_in_one_hour(self, mock_auth_service):
        """重置令牌 1 小时后过期"""
        from backend.services.local_auth_service import JWT_SECRET_KEY, JWT_ALGORITHM

        user_id = str(uuid4())
        token = mock_auth_service.create_reset_token(user_id)

        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)

        # 过期时间应该在 55-65 分钟之间（允许一些时间误差）
        time_diff = (exp_time - now).total_seconds()
        assert 55 * 60 <= time_diff <= 65 * 60


class TestResetPassword:
    """reset_password 发送重置邮件测试"""

    @pytest.mark.asyncio
    async def test_reset_password_returns_true_for_existing_user(
        self, mock_auth_service, sample_user
    ):
        """已存在用户请求重置密码返回 True"""
        mock_auth_service.db.query.return_value.filter.return_value.first.return_value = (
            sample_user
        )

        result = await mock_auth_service.reset_password(sample_user.email)

        assert result is True

    @pytest.mark.asyncio
    async def test_reset_password_returns_true_for_nonexistent_user(
        self, mock_auth_service
    ):
        """不存在用户请求重置密码也返回 True（安全考虑）"""
        mock_auth_service.db.query.return_value.filter.return_value.first.return_value = (
            None
        )

        result = await mock_auth_service.reset_password("nonexistent@example.com")

        # 为安全起见，不暴露邮箱是否存在
        assert result is True

    @pytest.mark.asyncio
    async def test_reset_password_generates_token_for_existing_user(
        self, mock_auth_service, sample_user
    ):
        """为存在的用户生成重置令牌"""
        mock_auth_service.db.query.return_value.filter.return_value.first.return_value = (
            sample_user
        )

        with patch.object(
            mock_auth_service, "create_reset_token", return_value="test_token"
        ) as mock_create:
            await mock_auth_service.reset_password(sample_user.email)

            mock_create.assert_called_once_with(str(sample_user.id))


class TestResetPasswordConfirm:
    """reset_password_confirm 密码重置确认测试"""

    @pytest.mark.asyncio
    async def test_reset_password_confirm_success(
        self, mock_auth_service, sample_user, valid_reset_token
    ):
        """有效令牌成功重置密码"""
        mock_auth_service.db.query.return_value.filter.return_value.first.return_value = (
            sample_user
        )

        result = await mock_auth_service.reset_password_confirm(
            reset_token=valid_reset_token, new_password="NewPassword123!"
        )

        assert result is True
        mock_auth_service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_password_confirm_invalid_token_type(
        self, mock_auth_service, access_token
    ):
        """非重置令牌类型被拒绝"""
        # access_token 的 type 是 "access" 而不是 "reset"
        with pytest.raises(HTTPException) as exc_info:
            await mock_auth_service.reset_password_confirm(
                reset_token=access_token, new_password="NewPassword123!"
            )

        assert exc_info.value.status_code == 400
        assert "无效的重置令牌类型" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_reset_password_confirm_expired_token(
        self, mock_auth_service, expired_reset_token
    ):
        """过期令牌被拒绝"""
        with pytest.raises(HTTPException) as exc_info:
            await mock_auth_service.reset_password_confirm(
                reset_token=expired_reset_token, new_password="NewPassword123!"
            )

        assert exc_info.value.status_code == 400
        assert "过期" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_reset_password_confirm_user_not_found(
        self, mock_auth_service, valid_reset_token
    ):
        """用户不存在返回 404"""
        mock_auth_service.db.query.return_value.filter.return_value.first.return_value = (
            None
        )

        with pytest.raises(HTTPException) as exc_info:
            await mock_auth_service.reset_password_confirm(
                reset_token=valid_reset_token, new_password="NewPassword123!"
            )

        assert exc_info.value.status_code == 404
        assert "用户不存在" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_reset_password_confirm_inactive_user(
        self, mock_auth_service, inactive_user, valid_reset_token_for_inactive
    ):
        """禁用账户无法重置密码"""
        mock_auth_service.db.query.return_value.filter.return_value.first.return_value = (
            inactive_user
        )

        with pytest.raises(HTTPException) as exc_info:
            await mock_auth_service.reset_password_confirm(
                reset_token=valid_reset_token_for_inactive,
                new_password="NewPassword123!",
            )

        assert exc_info.value.status_code == 403
        assert "禁用" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_reset_password_confirm_password_too_short(
        self, mock_auth_service, sample_user, valid_reset_token
    ):
        """密码太短被拒绝（BR-AUTH-003）"""
        mock_auth_service.db.query.return_value.filter.return_value.first.return_value = (
            sample_user
        )

        with pytest.raises(HTTPException) as exc_info:
            await mock_auth_service.reset_password_confirm(
                reset_token=valid_reset_token, new_password="short"  # < 8 chars
            )

        assert exc_info.value.status_code == 400
        assert "8" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_reset_password_confirm_updates_password_hash(
        self, mock_auth_service, sample_user, valid_reset_token
    ):
        """确认后密码哈希被更新"""
        original_hash = sample_user.password_hash
        mock_auth_service.db.query.return_value.filter.return_value.first.return_value = (
            sample_user
        )

        await mock_auth_service.reset_password_confirm(
            reset_token=valid_reset_token, new_password="NewPassword123!"
        )

        # 密码哈希应该被更新
        assert sample_user.password_hash != original_hash


class TestResetPasswordIntegration:
    """密码重置端到端集成测试"""

    @pytest.mark.asyncio
    async def test_full_reset_flow(self, mock_auth_service, sample_user):
        """完整的密码重置流程"""
        # 1. 请求重置
        mock_auth_service.db.query.return_value.filter.return_value.first.return_value = (
            sample_user
        )

        result1 = await mock_auth_service.reset_password(sample_user.email)
        assert result1 is True

        # 2. 生成令牌
        token = mock_auth_service.create_reset_token(str(sample_user.id))
        assert token is not None

        # 3. 确认重置
        result2 = await mock_auth_service.reset_password_confirm(
            reset_token=token, new_password="BrandNewPassword456!"
        )
        assert result2 is True


# ========== Fixtures ==========


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = MagicMock()
    db.commit = MagicMock()
    return db


@pytest.fixture
def mock_auth_service(mock_db):
    """模拟 LocalAuthService"""
    from backend.services.local_auth_service import LocalAuthService

    service = LocalAuthService(mock_db)
    return service


@pytest.fixture
def sample_user():
    """活跃用户样本"""
    user = MagicMock()
    user.id = uuid4()
    user.email = "test@example.com"
    user.username = "testuser"
    user.full_name = "Test User"
    user.is_active = True
    user.password_hash = "$2b$12$test_hash"
    return user


@pytest.fixture
def inactive_user():
    """禁用用户样本"""
    user = MagicMock()
    user.id = uuid4()
    user.email = "inactive@example.com"
    user.username = "inactiveuser"
    user.is_active = False
    user.password_hash = "$2b$12$test_hash"
    return user


@pytest.fixture
def valid_reset_token(sample_user):
    """有效的重置令牌"""
    from backend.services.local_auth_service import JWT_SECRET_KEY, JWT_ALGORITHM

    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    payload = {
        "sub": str(sample_user.id),
        "type": "reset",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


@pytest.fixture
def valid_reset_token_for_inactive(inactive_user):
    """禁用用户的重置令牌"""
    from backend.services.local_auth_service import JWT_SECRET_KEY, JWT_ALGORITHM

    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    payload = {
        "sub": str(inactive_user.id),
        "type": "reset",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


@pytest.fixture
def expired_reset_token(sample_user):
    """过期的重置令牌"""
    from backend.services.local_auth_service import JWT_SECRET_KEY, JWT_ALGORITHM

    expire = datetime.now(timezone.utc) - timedelta(hours=1)  # 已过期
    payload = {
        "sub": str(sample_user.id),
        "type": "reset",
        "exp": expire,
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


@pytest.fixture
def access_token(sample_user):
    """访问令牌（非重置类型）"""
    from backend.services.local_auth_service import JWT_SECRET_KEY, JWT_ALGORITHM

    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    payload = {
        "sub": str(sample_user.id),
        "type": "access",  # 不是 "reset"
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
