"""
认证服务
Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
import bcrypt
import secrets

from models.user import User
from core.security import jwt_manager, token_blacklist
from exceptions import ValidationError, NotFoundError, AuthenticationError
from utils.response import success_response
from utils.email import send_email


class AuthService:
    """认证服务类"""

    def __init__(self, db: Session):
        self.db = db

    async def authenticate(
        self,
        identifier: str,
        password: str,
        remember_me: bool = False
    ) -> tuple[User, dict]:
        """
        用户认证

        Args:
            identifier: 用户名或邮箱
            password: 密码
            remember_me: 记住我（延长token有效期）

        Returns:
            用户对象和token信息

        Raises:
            AuthenticationError: 认证失败
        """
        # 查找用户
        user = self.db.query(User).filter(
            or_(
                User.email == identifier,
                User.username == identifier
            )
        ).first()

        if not user:
            # 使用恒定时间比较防止时序攻击
            bcrypt.checkpw(password.encode(), bcrypt.gensalt().encode())
            raise AuthenticationError("AUTH_001", "用户名或密码错误")

        # 检查密码
        if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            raise AuthenticationError("AUTH_001", "用户名或密码错误")

        # 检查用户状态
        if not user.is_active:
            raise AuthenticationError("AUTH_002", "账户已被禁用")

        # 更新最后登录时间和登录次数
        user.last_login_at = datetime.utcnow()
        user.login_count = (user.login_count or 0) + 1
        user.last_login_ip = None  # TODO: 从请求中获取IP
        self.db.commit()

        # 创建token
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "username": user.username,
            "full_name": user.full_name,
            "permissions": self._get_user_permissions(user)
        }

        # 根据记住我调整token有效期
        if remember_me:
            # 30天的访问token
            expires_delta = timedelta(days=30)
            access_token = jwt_manager.create_access_token(token_data, expires_delta)
        else:
            access_token = jwt_manager.create_access_token(token_data)

        refresh_token = jwt_manager.create_refresh_token(token_data)

        token_info = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 30 * 60 * 60 if remember_me else 15 * 60,  # 秒
            "expires_at": datetime.utcnow() + (
                timedelta(days=30) if remember_me else timedelta(minutes=15)
            )
        }

        return user, token_info

    async def refresh_token(self, refresh_token: str) -> dict:
        """
        刷新访问令牌

        Args:
            refresh_token: 刷新令牌

        Returns:
            新的token信息

        Raises:
            AuthenticationError: 刷新失败
        """
        try:
            # 验证刷新令牌
            payload = jwt_manager.verify_token(refresh_token, "refresh")

            # 检查令牌是否在黑名单中
            jti = payload.get("jti")
            if jti and token_blacklist.is_blacklisted(jti):
                raise AuthenticationError("AUTH_003", "刷新令牌已被撤销")

            # 获取用户信息
            user_id = payload.get("sub")
            user = self.db.query(User).filter(User.id == user_id).first()

            if not user or not user.is_active:
                raise AuthenticationError("AUTH_004", "用户不存在或已被禁用")

            # 创建新的访问令牌
            token_data = {
                "sub": str(user.id),
                "email": user.email,
                "role": user.role,
                "username": user.username,
                "full_name": user.full_name,
                "permissions": self._get_user_permissions(user)
            }

            new_access_token = jwt_manager.create_access_token(token_data)

            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": 15 * 60  # 15分钟
            }

        except Exception as e:
            raise AuthenticationError("AUTH_005", "令牌刷新失败")

    async def logout(self, token: str, logout_all: bool = False) -> bool:
        """
        用户登出

        Args:
            token: 访问令牌
            logout_all: 是否登出所有设备

        Returns:
            是否成功
        """
        try:
            # 验证token
            payload = jwt_manager.verify_token(token, "access")

            # 将token加入黑名单
            jti = payload.get("jti")
            if jti:
                token_blacklist.add_to_blacklist(jti)

            if logout_all:
                # TODO: 实现撤销用户所有token的逻辑
                # 可以在用户表中维护一个token版本号
                pass

            return True

        except Exception:
            # 即使token无效也返回成功
            return True

    async def register_user(
        self,
        email: str,
        password: str,
        username: str,
        full_name: Optional[str] = None,
        role: str = "media_buyer",
        created_by: Optional[int] = None
    ) -> User:
        """
        注册新用户

        Args:
            email: 邮箱
            password: 密码
            username: 用户名
            full_name: 全名
            role: 角色
            created_by: 创建人ID

        Returns:
            创建的用户

        Raises:
            ValidationError: 验证失败
        """
        # 验证邮箱是否已存在
        if self.db.query(User).filter(User.email == email).first():
            raise ValidationError("AUTH_006", "邮箱已被注册")

        # 验证用户名是否已存在
        if self.db.query(User).filter(User.username == username).first():
            raise ValidationError("AUTH_007", "用户名已被使用")

        # 验证密码强度
        self._validate_password_strength(password)

        # 生成密码哈希
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # 创建用户
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            password_hash=password_hash,
            role=role,
            is_active=True,
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # 发送欢迎邮件
        await self._send_welcome_email(user)

        return user

    async def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
        logout_all: bool = True
    ) -> bool:
        """
        修改密码

        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码
            logout_all: 是否登出所有设备

        Returns:
            是否成功

        Raises:
            ValidationError: 验证失败
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValidationError("AUTH_008", "用户不存在")

        # 验证旧密码
        if not bcrypt.checkpw(old_password.encode(), user.password_hash.encode()):
            raise ValidationError("AUTH_009", "旧密码错误")

        # 验证新密码强度
        self._validate_password_strength(new_password)

        # 更新密码
        user.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        user.password_changed_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()

        self.db.commit()

        if logout_all:
            # 更新token版本号，使所有旧token失效
            user.token_version = (user.token_version or 0) + 1
            self.db.commit()

        # 发送密码修改通知邮件
        await self._send_password_change_notification(user)

        return True

    async def reset_password_request(self, email: str) -> bool:
        """
        请求重置密码

        Args:
            email: 用户邮箱

        Returns:
            是否成功
        """
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            # 为安全考虑，即使用户不存在也返回成功
            return True

        # 生成重置令牌
        reset_token = secrets.token_urlsafe(32)
        reset_token_hash = bcrypt.hashpw(reset_token.encode(), bcrypt.gensalt()).decode()

        # 设置过期时间（1小时）
        expires_at = datetime.utcnow() + timedelta(hours=1)

        user.reset_password_token = reset_token_hash
        user.reset_password_expires_at = expires_at
        self.db.commit()

        # 发送重置密码邮件
        await self._send_password_reset_email(user, reset_token)

        return True

    async def reset_password_confirm(
        self,
        reset_token: str,
        new_password: str
    ) -> bool:
        """
        确认重置密码

        Args:
            reset_token: 重置令牌
            new_password: 新密码

        Returns:
            是否成功

        Raises:
            ValidationError: 验证失败
        """
        # 查找使用此令牌的用户
        users = self.db.query(User).filter(
            User.reset_password_token.isnot(None),
            User.reset_password_expires_at > datetime.utcnow()
        ).all()

        user = None
        for u in users:
            if bcrypt.checkpw(reset_token.encode(), u.reset_password_token.encode()):
                user = u
                break

        if not user:
            raise ValidationError("AUTH_010", "重置令牌无效或已过期")

        # 验证新密码强度
        self._validate_password_strength(new_password)

        # 更新密码
        user.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        user.reset_password_token = None
        user.reset_password_expires_at = None
        user.password_changed_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        self.db.commit()

        # 发送密码重置成功通知
        await self._send_password_reset_success_notification(user)

        return True

    async def verify_email(self, token: str) -> bool:
        """
        验证邮箱

        Args:
            token: 验证令牌

        Returns:
            是否成功
        """
        user = self.db.query(User).filter(User.email_verification_token == token).first()
        if not user:
            return False

        if user.email_verification_expires_at and user.email_verification_expires_at < datetime.utcnow():
            return False

        # 验证邮箱
        user.email_verified = True
        user.email_verification_token = None
        user.email_verification_expires_at = None
        user.email_verified_at = datetime.utcnow()
        self.db.commit()

        return True

    async def send_email_verification(self, user_id: int) -> bool:
        """
        发送邮箱验证

        Args:
            user_id: 用户ID

        Returns:
            是否成功
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or user.email_verified:
            return True

        # 生成验证令牌
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)

        user.email_verification_token = token
        user.email_verification_expires_at = expires_at
        self.db.commit()

        # 发送验证邮件
        await self._send_email_verification(user, token)

        return True

    def _get_user_permissions(self, user: User) -> List[str]:
        """获取用户权限列表"""
        # 根据角色返回权限
        role_permissions = {
            "admin": ["*"],  # 管理员拥有所有权限
            "finance": [
                "finance:read", "finance:create", "finance:update",
                "topup:approve", "topup:confirm", "reconciliation:manage",
                "account:read", "project:read", "report:read"
            ],
            "data_operator": [
                "project:read", "project:update",
                "account:read", "account:assign",
                "report:submit", "report:review",
                "daily_report:read", "daily_report:review"
            ],
            "account_manager": [
                "project:create", "project:read", "project:update",
                "account:create", "account:read", "account:update", "account:delete",
                "channel:read", "topup:request", "report:read"
            ],
            "media_buyer": [
                "account:read", "account:monitor",
                "daily_report:create", "daily_report:read", "daily_report:update",
                "topup:request", "report:submit"
            ]
        }

        return role_permissions.get(user.role, [])

    def _validate_password_strength(self, password: str):
        """验证密码强度"""
        if len(password) < 8:
            raise ValidationError("AUTH_011", "密码长度至少8位")

        # 检查是否包含至少一个数字
        if not any(c.isdigit() for c in password):
            raise ValidationError("AUTH_012", "密码必须包含至少一个数字")

        # 检查是否包含至少一个字母
        if not any(c.isalpha() for c in password):
            raise ValidationError("AUTH_013", "密码必须包含至少一个字母")

        # 检查是否包含至少一个特殊字符
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            raise ValidationError("AUTH_014", "密码必须包含至少一个特殊字符")

    async def _send_welcome_email(self, user: User):
        """发送欢迎邮件"""
        try:
            subject = "欢迎加入AI广告代投系统"
            body = f"""
            亲爱的 {user.full_name or user.username}，

            欢迎您加入AI广告代投系统！

            您的账户信息：
            - 邮箱：{user.email}
            - 用户名：{user.username}
            - 角色：{user.role}

            请点击以下链接验证您的邮箱：
            https://example.com/verify-email?token={user.email_verification_token}

            如有任何问题，请联系管理员。

            祝好！
            AI广告代投系统团队
            """
            await send_email(user.email, subject, body)
        except Exception as e:
            # 记录错误但不阻止流程
            print(f"Failed to send welcome email: {e}")

    async def _send_password_change_notification(self, user: User):
        """发送密码修改通知"""
        try:
            subject = "密码修改通知"
            body = f"""
            亲爱的 {user.full_name or user.username}，

            您的账户密码已于 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} 修改。

            如果这不是您本人的操作，请立即联系管理员。

            AI广告代投系统团队
            """
            await send_email(user.email, subject, body)
        except Exception as e:
            print(f"Failed to send password change notification: {e}")

    async def _send_password_reset_email(self, user: User, reset_token: str):
        """发送密码重置邮件"""
        try:
            subject = "重置密码请求"
            body = f"""
            亲爱的 {user.full_name or user.username}，

            您请求重置密码。请点击以下链接进行密码重置：

            https://example.com/reset-password?token={reset_token}

            该链接将在1小时后失效。

            如果这不是您本人的操作，请忽略此邮件。

            AI广告代投系统团队
            """
            await send_email(user.email, subject, body)
        except Exception as e:
            print(f"Failed to send password reset email: {e}")

    async def _send_password_reset_success_notification(self, user: User):
        """发送密码重置成功通知"""
        try:
            subject = "密码重置成功"
            body = f"""
            亲爱的 {user.full_name or user.username}，

            您的密码已成功重置。

            如果这不是您本人的操作，请立即联系管理员。

            AI广告代投系统团队
            """
            await send_email(user.email, subject, body)
        except Exception as e:
            print(f"Failed to send password reset success notification: {e}")

    async def _send_email_verification(self, user: User, token: str):
        """发送邮箱验证邮件"""
        try:
            subject = "验证您的邮箱"
            body = f"""
            亲爱的 {user.full_name or user.username}，

            请点击以下链接验证您的邮箱地址：

            https://example.com/verify-email?token={token}

            该链接将在24小时后失效。

            AI广告代投系统团队
            """
            await send_email(user.email, subject, body)
        except Exception as e:
            print(f"Failed to send email verification: {e}")

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()

    async def update_user_last_activity(self, user_id: int, activity_type: str, details: Dict[str, Any]):
        """更新用户最后活动记录"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.last_activity_at = datetime.utcnow()
            user.last_activity_type = activity_type
            # TODO: 可以创建单独的活动记录表
            self.db.commit()