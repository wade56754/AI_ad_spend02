"""
认证服务测试
Version: 1.0
Author: Claude协作开发
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from models.user import User
from services.auth_service import AuthService
from exceptions import ValidationError, AuthenticationError
from utils.response import success_response


class TestAuthService:
    """认证服务测试类"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = Mock()
        db.query = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """获取服务实例"""
        return AuthService(mock_db)

    @pytest.fixture
    def sample_user(self):
        """示例用户"""
        return User(
            id=1,
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password_hash="hashed_password",
            role="media_buyer",
            is_active=True,
            created_at=datetime.utcnow()
        )

    @pytest.mark.asyncio
    async def test_authenticate_success(self, service, mock_db, sample_user):
        """测试成功认证"""
        # 准备数据
        identifier = "test@example.com"
        password = "password123"

        # 模拟查询返回用户
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_user

        # 模拟bcrypt验证
        with patch('services.auth_service.bcrypt.checkpw', return_value=True):
            user, token_info = await service.authenticate(identifier, password, remember_me=False)

        # 验证
        assert user.id == 1
        assert user.email == "test@example.com"
        assert "access_token" in token_info
        assert "refresh_token" in token_info
        assert token_info["expires_in"] == 15 * 60  # 15分钟

    @pytest.mark.asyncio
    async def test_authenticate_invalid_password(self, service, mock_db, sample_user):
        """测试密码错误"""
        identifier = "test@example.com"
        password = "wrong_password"

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_user

        # 模拟bcrypt验证失败
        with patch('services.auth_service.bcrypt.checkpw', return_value=False):
            with pytest.raises(AuthenticationError) as exc_info:
                await service.authenticate(identifier, password)

        assert exc_info.value.error_code == "AUTH_001"

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, service, mock_db):
        """测试用户不存在"""
        identifier = "notfound@example.com"
        password = "password123"

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with patch('services.auth_service.bcrypt.checkpw', return_value=False):
            with pytest.raises(AuthenticationError) as exc_info:
                await service.authenticate(identifier, password)

        assert exc_info.value.error_code == "AUTH_001"

    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self, service, mock_db, sample_user):
        """测试非活跃用户"""
        sample_user.is_active = False

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_user

        with patch('services.auth_service.bcrypt.checkpw', return_value=True):
            with pytest.raises(AuthenticationError) as exc_info:
                await service.authenticate("test@example.com", "password123")

        assert exc_info.value.error_code == "AUTH_002"

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, service, mock_db, sample_user):
        """测试刷新令牌成功"""
        refresh_token = "valid_refresh_token"

        # 模拟token黑名单
        with patch('services.auth_service.jwt_manager.verify_token') as mock_verify:
            mock_verify.return_value = {
                "sub": "1",
                "email": "test@example.com",
                "role": "media_buyer"
            }

            mock_query = Mock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = sample_user

            # 模拟token不在黑名单
            with patch('services.auth_service.token_blacklist.is_blacklisted', return_value=False):
                with patch('services.auth_service.jwt_manager.create_access_token') as mock_create:
                    mock_create.return_value = "new_access_token"

                    result = await service.refresh_token(refresh_token)

                    assert result["access_token"] == "new_access_token"
                    assert result["expires_in"] == 15 * 60

    @pytest.mark.asyncio
    async def test_refresh_token_blacklisted(self, service, mock_db):
        """测试刷新令牌在黑名单中"""
        refresh_token = "blacklisted_token"

        with patch('services.auth_service.jwt_manager.verify_token') as mock_verify:
            mock_verify.return_value = {"jti": "test_jti"}

            with patch('services.auth_service.token_blacklist.is_blacklisted', return_value=True):
                with pytest.raises(AuthenticationError) as exc_info:
                    await service.refresh_token(refresh_token)

        assert exc_info.value.error_code == "AUTH_003"

    @pytest.mark.asyncio
    async def test_register_user_success(self, service, mock_db):
        """测试成功注册用户"""
        email = "newuser@example.com"
        password = "Password123!"
        username = "newuser"
        full_name = "New User"

        # 模拟邮箱和用户名不存在
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # 模拟用户创建
        mock_user = User(
            id=2,
            email=email,
            username=username,
            full_name=full_name,
            password_hash="hashed",
            role="media_buyer"
        )
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # 模拟bcrypt哈希
        with patch('services.auth_service.bcrypt.hashpw', return_value=b"hashed"):
            with patch.object(service, '_send_welcome_email', new_callable=AsyncMock):
                user = await service.register_user(
                    email=email,
                    password=password,
                    username=username,
                    full_name=full_name
                )

        assert user.email == email
        assert user.username == username
        assert user.role == "media_buyer"

    @pytest.mark.asyncio
    async def test_register_user_email_exists(self, service, mock_db):
        """测试邮箱已存在"""
        email = "existing@example.com"
        password = "Password123!"
        username = "newuser"

        # 模拟邮箱已存在
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = User(email=email)

        with pytest.raises(ValidationError) as exc_info:
            await service.register_user(email, password, username)

        assert exc_info.value.error_code == "AUTH_006"

    @pytest.mark.asyncio
    async def test_register_user_username_exists(self, service, mock_db):
        """测试用户名已存在"""
        email = "newuser@example.com"
        password = "Password123!"
        username = "existing"

        # 模拟邮箱不存在但用户名存在
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        def side_effect(*args):
            if "email" in str(args):
                return mock_query.first.return_value = None
            elif "username" in str(args):
                return mock_query.first.return_value = User(username=username)
            return mock_query

        mock_query.first.side_effect = side_effect

        with pytest.raises(ValidationError) as exc_info:
            await service.register_user(email, password, username)

        assert exc_info.value.error_code == "AUTH_007"

    @pytest.mark.asyncio
    async def test_register_user_weak_password(self, service, mock_db):
        """测试密码强度不足"""
        email = "newuser@example.com"
        password = "123"  # 太弱
        username = "newuser"

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with pytest.raises(ValidationError) as exc_info:
            await service.register_user(email, password, username)

        assert exc_info.value.error_code == "AUTH_011"

    @pytest.mark.asyncio
    async def test_change_password_success(self, service, mock_db, sample_user):
        """测试成功修改密码"""
        old_password = "oldpassword"
        new_password = "newpassword123!"

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_user

        # 模拟密码验证
        with patch('services.auth_service.bcrypt.checkpw', side_effect=[True, True]):
            # 模拟新密码哈希
            with patch('services.auth_service.bcrypt.hashpw', return_value=b"new_hashed"):
                success = await service.change_password(
                    user_id=1,
                    old_password=old_password,
                    new_password=new_password
                )

        assert success is True

    @pytest.mark.asyncio
    async def test_change_password_wrong_old_password(self, service, mock_db, sample_user):
        """测试旧密码错误"""
        old_password = "wrongpassword"
        new_password = "newpassword123!"

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_user

        with patch('services.auth_service.bcrypt.checkpw', side_effect=[False]):
            with pytest.raises(ValidationError) as exc_info:
                await service.change_password(
                    user_id=1,
                    old_password=old_password,
                    new_password=new_password
                )

        assert exc_info.value.error_code == "AUTH_009"

    @pytest.mark.asyncio
    async def test_reset_password_request_success(self, service, mock_db, sample_user):
        """测试成功请求重置密码"""
        email = "test@example.com"

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_user

        # 模拟生成token
        with patch('services.auth_service.secrets.token_urlsafe', return_value="reset_token"):
            # 模拟token哈希
            with patch('services.auth_service.bcrypt.hashpw', return_value=b"hashed_token"):
                with patch.object(service, '_send_password_reset_email', new_callable=AsyncMock):
                    success = await service.reset_password_request(email)

        assert success is True

    @pytest.mark.asyncio
    async def test_reset_password_request_user_not_found(self, service, mock_db):
        """测试用户不存在"""
        email = "notfound@example.com"

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # 为了安全，即使用户不存在也返回成功
        success = await service.reset_password_request(email)
        assert success is True

    @pytest.mark.asyncio
    async def test_reset_password_confirm_success(self, service, mock_db, sample_user):
        """测试成功确认重置密码"""
        reset_token = "valid_token"
        new_password = "newpassword123!"

        # 模拟用户有待处理的重置请求
        sample_user.reset_password_token = "hashed_token"
        sample_user.reset_password_expires_at = datetime.utcnow() + timedelta(hours=1)

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [sample_user]

        # 模拟token验证
        with patch('services.auth_service.bcrypt.checkpw', return_value=True):
            # 模拟新密码哈希
            with patch('services.auth_service.bcrypt.hashpw', return_value=b"new_hashed"):
                with patch.object(service, '_send_password_reset_success_notification', new_callable=AsyncMock):
                    success = await service.reset_password_confirm(
                        reset_token=reset_token,
                        new_password=new_password
                    )

        assert success is True

    @pytest.mark.asyncio
    async def test_reset_password_confirm_invalid_token(self, service, mock_db):
        """测试无效的重置令牌"""
        reset_token = "invalid_token"
        new_password = "newpassword123!"

        # 模拟没有用户有待处理的重置请求
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        with pytest.raises(ValidationError) as exc_info:
            await service.reset_password_confirm(
                reset_token=reset_token,
                new_password=new_password
            )

        assert exc_info.value.error_code == "AUTH_010"

    @pytest.mark.asyncio
    async def test_verify_email_success(self, service, mock_db, sample_user):
        """测试成功验证邮箱"""
        token = "valid_token"
        sample_user.email_verification_token = "hashed_token"
        sample_user.email_verification_expires_at = datetime.utcnow() + timedelta(hours=24)

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_user

        # 模拟token验证
        with patch('services.auth_service.bcrypt.checkpw', return_value=True):
            success = await service.verify_email(token)

        assert success is True
        assert sample_user.email_verified is True

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, service, mock_db):
        """测试无效的验证令牌"""
        token = "invalid_token"

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        success = await service.verify_email(token)
        assert success is False

    @pytest.mark.asyncio
    async def test_get_user_permissions(self, service, sample_user):
        """测试获取用户权限"""
        # 测试不同角色的权限
        permissions = service._get_user_permissions(sample_user)
        assert isinstance(permissions, list)

        # 测试admin角色
        sample_user.role = "admin"
        permissions = service._get_user_permissions(sample_user)
        assert permissions == ["*"]

        # 测试media_buyer角色
        sample_user.role = "media_buyer"
        permissions = service._get_user_permissions(sample_user)
        assert "account:read" in permissions
        assert "report:submit" in permissions

    @pytest.mark.asyncio
    async def test_validate_password_strength(self, service):
        """测试密码强度验证"""
        # 测试弱密码
        weak_passwords = ["12345678", "password", "abcdefgh", "Password1"]
        for pwd in weak_passwords:
            with pytest.raises(ValidationError):
                service._validate_password_strength(pwd)

        # 测试强密码
        strong_password = "Password@123"
        service._validate_password_strength(strong_password)  # 不应该抛出异常

    @pytest.mark.asyncio
    async def test_logout_success(self, service, mock_db):
        """测试登出成功"""
        token = "valid_token"

        # 模拟token验证
        with patch('services.auth_service.jwt_manager.verify_token') as mock_verify:
            mock_verify.return_value = {"jti": "test_jti"}

            with patch('services.auth_service.token_blacklist.add_to_blacklist') as mock_add:
                success = await service.logout(token)

        assert success is True

    @pytest.mark.asyncio
    async def test_logout_invalid_token(self, service, mock_db):
        """测试登出无效token"""
        token = "invalid_token"

        # 即使token无效也应该返回成功
        success = await service.logout(token)
        assert success is True