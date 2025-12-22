"""
本地 JWT 认证服务
替代 Supabase Auth，使用本地数据库存储用户和密码

Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
import structlog

from fastapi import HTTPException, status, Request
from jose import jwt, JWTError
import bcrypt
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.core.config import get_settings

settings = get_settings()
from backend.models import User
from backend.models.enums import UserRole

logger = structlog.get_logger(__name__)

# JWT 配置
JWT_SECRET_KEY = settings.jwt_secret
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 小时
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 天


class LocalAuthService:
    """本地 JWT 认证服务"""

    def __init__(self, db: Session):
        self.db = db

    # ========== 密码处理 ==========

    @staticmethod
    def hash_password(password: str) -> str:
        """哈希密码 - 使用 bcrypt 直接加密"""
        # 确保密码是 bytes 类型，截断到 72 字节（bcrypt 限制）
        password_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码 - 使用 bcrypt 直接验证"""
        try:
            password_bytes = plain_password.encode('utf-8')[:72]
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception as e:
            logger.warning(f"Password verification error: {e}")
            return False

    # ========== JWT Token 处理 ==========

    @staticmethod
    def create_access_token(
        user_id: str,
        email: str,
        role: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建访问令牌"""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "type": "access",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }

        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(
        user_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建刷新令牌"""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": str(uuid4()),  # JWT ID 用于令牌撤销
        }

        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """解码并验证 JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except JWTError as e:
            logger.warning(f"JWT decode error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # ========== 用户认证 ==========

    async def register_user(
        self,
        email: str,
        password: str,
        username: str,
        full_name: Optional[str] = None,
        role: str = "media_buyer"
    ) -> Dict[str, Any]:
        """
        用户注册

        Args:
            email: 邮箱
            password: 密码
            username: 用户名
            full_name: 全名（可选）
            role: 角色，默认为 media_buyer

        Returns:
            包含用户信息和令牌的字典
        """
        logger.info(f"[REGISTER] Starting registration for: {email}")

        # 检查邮箱是否已存在
        logger.info(f"[REGISTER] Checking for existing user...")
        existing_user = self.db.query(User).filter(
            or_(User.email == email, User.username == username)
        ).first()
        logger.info(f"[REGISTER] Existing user check complete: {existing_user is not None}")

        if existing_user:
            if existing_user.email == email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该邮箱已被注册"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该用户名已被使用"
                )

        # 验证角色
        valid_roles = [r.value for r in UserRole]
        if role not in valid_roles:
            role = UserRole.MEDIA_BUYER.value

        # 创建用户
        user_id = uuid4()
        password_hash = self.hash_password(password)

        new_user = User(
            id=user_id,
            email=email,
            username=username,
            role=role,
            is_active=True,
            password_hash=password_hash,  # 新增字段
        )

        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)

        logger.info(f"[REGISTER] User created: {user_id}")

        # 生成令牌
        access_token = self.create_access_token(
            user_id=str(user_id),
            email=email,
            role=role
        )
        refresh_token = self.create_refresh_token(user_id=str(user_id))

        return {
            "user": {
                "id": str(user_id),
                "email": email,
                "username": username,
                "role": role,
                "is_active": True,
            },
            "session": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "token_type": "bearer",
            }
        }

    async def login_user(
        self,
        email: str,
        password: str,
        remember_me: bool = False,
        request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """
        用户登录

        Args:
            email: 邮箱或用户名
            password: 密码
            remember_me: 是否记住我
            request: 请求对象

        Returns:
            包含用户信息和令牌的字典
        """
        logger.info(f"[LOGIN] Starting login for: {email}")

        # 查找用户（支持邮箱或用户名登录）
        user = self.db.query(User).filter(
            or_(User.email == email, User.username == email)
        ).first()

        if not user:
            logger.warning(f"[LOGIN] User not found: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误"
            )

        # 检查用户是否激活
        if not user.is_active:
            logger.warning(f"[LOGIN] User disabled: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户已被禁用"
            )

        # 验证密码
        if not user.password_hash or not self.verify_password(password, user.password_hash):
            logger.warning(f"[LOGIN] Invalid password for: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误"
            )

        logger.info(f"[LOGIN] Login successful for: {email}")

        # 生成令牌
        expires_delta = timedelta(days=30) if remember_me else None
        access_token = self.create_access_token(
            user_id=str(user.id),
            email=user.email,
            role=user.role,
            expires_delta=expires_delta
        )
        refresh_token = self.create_refresh_token(user_id=str(user.id))

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "is_active": user.is_active,
            },
            "session": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "token_type": "bearer",
            }
        }

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        验证访问令牌并返回用户信息

        Args:
            token: JWT 访问令牌

        Returns:
            用户信息字典
        """
        payload = self.decode_token(token)

        # 检查令牌类型
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌类型"
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌"
            )

        # 查找用户
        try:
            user = self.db.query(User).filter(User.id == UUID(user_id)).first()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的用户ID"
            )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户已被禁用"
            )

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "is_active": user.is_active,
            },
            "profile": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "is_active": user.is_active,
            },
            "raw_claims": payload,
        }

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        使用刷新令牌获取新的访问令牌

        Args:
            refresh_token: 刷新令牌

        Returns:
            新的令牌信息
        """
        payload = self.decode_token(refresh_token)

        # 检查令牌类型
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌"
            )

        # 查找用户
        user = self.db.query(User).filter(User.id == UUID(user_id)).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户已被禁用"
            )

        # 生成新令牌
        new_access_token = self.create_access_token(
            user_id=str(user.id),
            email=user.email,
            role=user.role
        )
        new_refresh_token = self.create_refresh_token(user_id=str(user.id))

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "token_type": "bearer",
        }

    async def logout_user(self, token: str, user_id: Optional[str] = None) -> bool:
        """
        用户登出

        注意：JWT 是无状态的，真正的登出需要实现令牌黑名单
        这里简单返回成功，客户端需要删除本地存储的令牌

        Args:
            token: 访问令牌
            user_id: 用户ID

        Returns:
            是否成功
        """
        logger.info(f"[LOGOUT] User logged out: {user_id}")
        # TODO: 实现令牌黑名单机制
        return True

    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        修改密码

        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码

        Returns:
            是否成功
        """
        user = self.db.query(User).filter(User.id == UUID(user_id)).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 验证旧密码
        if not self.verify_password(old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="原密码错误"
            )

        # 更新密码
        user.password_hash = self.hash_password(new_password)
        self.db.commit()

        logger.info(f"[CHANGE_PASSWORD] Password changed for user: {user_id}")
        return True

    async def reset_password(self, email: str) -> bool:
        """
        发送密码重置邮件（简化实现，实际需要邮件服务）

        Args:
            email: 用户邮箱

        Returns:
            是否成功（为安全起见总是返回 True）
        """
        user = self.db.query(User).filter(User.email == email).first()

        if user:
            # TODO: 实现邮件发送
            # 生成重置令牌并发送邮件
            logger.info(f"[RESET_PASSWORD] Reset requested for: {email}")

        # 为安全起见，不暴露邮箱是否存在
        return True

    async def reset_password_confirm(
        self,
        reset_token: str,
        new_password: str,
        refresh_token: Optional[str] = None
    ) -> bool:
        """
        确认密码重置

        Args:
            reset_token: 重置令牌
            new_password: 新密码
            refresh_token: 刷新令牌（可选）

        Returns:
            是否成功
        """
        # TODO: 实现令牌验证和密码重置
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="密码重置功能暂未实现，请联系管理员"
        )

    async def verify_email(self, token: str) -> bool:
        """
        验证邮箱（简化实现）

        Args:
            token: 验证令牌

        Returns:
            是否成功
        """
        # TODO: 实现邮箱验证
        return True

    async def resend_verification_email(self, email: str) -> bool:
        """
        重新发送验证邮件

        Args:
            email: 用户邮箱

        Returns:
            是否成功
        """
        # TODO: 实现邮件发送
        return True

    async def update_password(
        self,
        new_password: str,
        access_token: str = ""
    ) -> bool:
        """
        更新密码（需要认证）

        Args:
            new_password: 新密码
            access_token: 访问令牌

        Returns:
            是否成功
        """
        # TODO: 从 token 获取用户并更新密码
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="请使用修改密码接口"
        )


def get_local_auth_service(db: Session) -> LocalAuthService:
    """获取本地认证服务实例"""
    return LocalAuthService(db)
