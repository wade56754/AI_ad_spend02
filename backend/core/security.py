from __future__ import annotations

import base64
import hmac
import json
import secrets
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from hashlib import sha256
from time import time
from typing import Any, Dict, Optional, List
from uuid import UUID

import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.core.db import get_db
from backend.models.users import User


def _base64url_decode(data: str) -> bytes:
    padding = (-len(data)) % 4
    return base64.urlsafe_b64decode(data + ("=" * padding))


def _decode_segment(segment: str) -> Dict[str, Any]:
    try:
        decoded = _base64url_decode(segment)
        return json.loads(decoded.decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INVALID_TOKEN", "message": "Token 解析失败"},
        ) from exc


def _verify_signature(token: str, secret: str) -> Dict[str, Any]:
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INVALID_TOKEN", "message": "Token 结构不合法"},
        ) from exc

    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    expected_signature = hmac.new(secret.encode("utf-8"), signing_input, sha256).digest()

    actual_signature = _base64url_decode(signature_segment)
    if not hmac.compare_digest(actual_signature, expected_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INVALID_TOKEN", "message": "Token 校验失败"},
        )

    header = _decode_segment(header_segment)
    if header.get("alg") != "HS256":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INVALID_TOKEN", "message": "不支持的签名算法"},
        )

    payload = _decode_segment(payload_segment)

    exp = payload.get("exp")
    if exp is not None and exp < int(time()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_EXPIRED", "message": "Token 已过期"},
        )

    return payload


@dataclass
class TokenInfo:
    """Token信息"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 0
    expires_at: Optional[datetime] = None


@dataclass
class AuthenticatedUser:
    id: str
    role: Optional[str]
    email: Optional[str]
    raw_claims: Dict[str, Any]
    permissions: List[str] = None
    is_active: bool = True
    last_login: Optional[datetime] = None

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []


class JWTManager:
    """JWT令牌管理器"""

    def __init__(self):
        self.settings = get_settings()
        self.algorithm = "HS256"
        self.access_token_expire_minutes = self.settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = self.settings.jwt_refresh_token_expire_days

    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建访问令牌"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({
            "exp": expire,
            "type": "access",
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16)  # JWT ID，用于防止重放攻击
        })

        return jwt.encode(to_encode, self.settings.jwt_secret, algorithm=self.algorithm)

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        to_encode.update({
            "exp": expire,
            "type": "refresh",
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16)
        })

        return jwt.encode(to_encode, self.settings.jwt_secret, algorithm=self.algorithm)

    def create_token_pair(self, user_data: Dict[str, Any]) -> TokenInfo:
        """创建令牌对"""
        access_token = self.create_access_token(user_data)
        refresh_token = self.create_refresh_token(user_data)

        expires_at = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        return TokenInfo(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.access_token_expire_minutes * 60,
            expires_at=expires_at
        )

    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """验证令牌"""
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret,
                algorithms=[self.algorithm]
            )

            # 检查令牌类型
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={"code": "AUTH_INVALID_TOKEN_TYPE", "message": "令牌类型错误"}
                )

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "AUTH_EXPIRED", "message": "令牌已过期"}
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "AUTH_INVALID_TOKEN", "message": "令牌无效"}
            )

    def refresh_access_token(self, refresh_token: str) -> str:
        """使用刷新令牌获取新的访问令牌"""
        payload = self.verify_token(refresh_token, "refresh")

        # 移除时间相关的声明，重新生成访问令牌
        user_data = {
            "sub": payload.get("sub"),
            "role": payload.get("role"),
            "email": payload.get("email"),
            "permissions": payload.get("permissions", [])
        }

        return self.create_access_token(user_data)

    def revoke_token(self, token: str) -> bool:
        """撤销令牌（示例实现，实际应该使用黑名单）"""
        # 这里可以实现令牌黑名单功能
        # 实际项目中应该使用Redis或数据库存储黑名单
        return True


class TokenBlacklist:
    """令牌黑名单管理"""

    def __init__(self):
        # 实际项目中应该使用Redis或数据库
        self._blacklisted_jtis: set = set()

    def add_to_blacklist(self, jti: str) -> None:
        """将令牌添加到黑名单"""
        self._blacklisted_jtis.add(jti)

    def is_blacklisted(self, jti: str) -> bool:
        """检查令牌是否在黑名单中"""
        return jti in self._blacklisted_jtis

    def cleanup_expired(self) -> None:
        """清理过期的黑名单令牌（简化实现）"""
        # 实际实现应该根据过期时间清理
        pass


# 全局实例
jwt_manager = JWTManager()
token_blacklist = TokenBlacklist()


def _extract_user(payload: Dict[str, Any]) -> AuthenticatedUser:
    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INVALID_TOKEN", "message": "Token 缺少用户标识"},
        )

    role = payload.get("role") or payload.get("app_metadata", {}).get("role")
    email = payload.get("email") or payload.get("user_metadata", {}).get("email")

    return AuthenticatedUser(id=str(user_id), role=role, email=email, raw_claims=payload)


def _resolve_role(db: Session, user_id: str, fallback: Optional[str]) -> Optional[str]:
    try:
        user_uuid = UUID(str(user_id))
    except (TypeError, ValueError):
        return fallback
    db_user = db.query(User).filter(User.id == user_uuid).first()
    if db_user:
        return db_user.role
    return fallback


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> AuthenticatedUser:
    """获取当前认证用户"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_MISSING_TOKEN", "message": "缺少 Authorization 头"},
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INVALID_TOKEN", "message": "Authorization 头格式错误"},
        )

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INVALID_TOKEN", "message": "Token 为空"},
        )

    try:
        # 使用新的JWT管理器验证令牌
        payload = jwt_manager.verify_token(token, "access")

        # 检查令牌是否在黑名单中
        jti = payload.get("jti")
        if jti and token_blacklist.is_blacklisted(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "AUTH_TOKEN_REVOKED", "message": "令牌已被撤销"}
            )

        user = _extract_user(payload)
        user.role = _resolve_role(db, user.id, user.role)

        # 更新最后登录时间
        user.last_login = datetime.utcnow()

        return user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INVALID_TOKEN", "message": "令牌验证失败"}
        )


def get_current_active_user(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INACTIVE_USER", "message": "用户已被禁用"}
        )
    return current_user


def authenticated_user_dependency(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    """认证用户依赖（兼容性）"""
    return user


def require_roles(*roles: str):
    """角色权限装饰器"""
    def role_dependency(current_user: AuthenticatedUser = Depends(get_current_active_user)) -> AuthenticatedUser:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "AUTH_PERMISSION_DENIED", "message": "权限不足"}
            )
        return current_user
    return role_dependency


def require_permissions(*permissions: str):
    """权限检查装饰器"""
    def permission_dependency(current_user: AuthenticatedUser = Depends(get_current_active_user)) -> AuthenticatedUser:
        user_permissions = set(current_user.permissions)
        required_permissions = set(permissions)

        if not required_permissions.issubset(user_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "AUTH_PERMISSION_DENIED", "message": "权限不足"}
            )
        return current_user
    return permission_dependency


