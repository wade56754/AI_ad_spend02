"""
FastAPI依赖注入模块
整合数据库、认证和权限控制依赖
"""
from typing import List, Optional, Union, Tuple
from uuid import UUID
import logging

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.models import User
# 导入真实的JWT验证逻辑
from backend.core.security import (
    get_current_user as security_get_current_user,
    get_current_active_user as security_get_current_active_user,
    AuthenticatedUser
)
from backend.core.error_codes import AuthErrorCodes, SystemErrorCodes

# HTTP Bearer认证方案
security = HTTPBearer(auto_error=False)

logger = logging.getLogger(__name__)


def _auth_user_to_db_user(
    auth_user: AuthenticatedUser,
    db: Session
) -> User:
    """
    将 AuthenticatedUser 转换为 models.User

    Args:
        auth_user: JWT验证后的用户对象
        db: 数据库会话

    Returns:
        User: 数据库User对象

    Raises:
        HTTPException: 401 - 用户ID格式无效
        HTTPException: 404 - 用户在数据库中不存在

    Note:
        严格模式: JWT中的用户ID必须对应数据库中的有效User记录
        如果用户不存在,将抛出404错误而不是构造临时对象
    """
    try:
        # 尝试将字符串ID转为UUID
        user_uuid = UUID(str(auth_user.id))
    except (TypeError, ValueError) as e:
        logger.error(f"Invalid user ID format: {auth_user.id}, error: {e}")
        raise HTTPException(
            status_code=AuthErrorCodes.TOKEN_INVALID.status_code,
            detail={
                "code": AuthErrorCodes.TOKEN_INVALID.code,
                "message": "用户ID格式无效"
            }
        )

    # 从数据库查询用户
    db_user = db.query(User).filter(User.id == user_uuid).first()

    if db_user:
        # 数据库中存在，返回完整User对象
        logger.debug(f"User {user_uuid} found in database, role: {db_user.role}")
        return db_user

    # 用户在数据库中不存在,拒绝请求
    # 生产环境中JWT中的用户ID必须对应有效的数据库记录
    logger.error(
        f"User {user_uuid} not found in database. "
        f"JWT contains valid user ID but no corresponding database record exists. "
        f"Email: {auth_user.email}, Role: {auth_user.role}"
    )
    raise HTTPException(
        status_code=AuthErrorCodes.USER_NOT_FOUND.status_code,
        detail={
            "code": AuthErrorCodes.USER_NOT_FOUND.code,
            "message": AuthErrorCodes.USER_NOT_FOUND.message
        }
    )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    获取当前用户（可选）

    如果没有提供认证令牌，返回None
    如果提供了令牌但无效，抛出401异常
    """
    if not credentials:
        return None

    try:
        # 使用真实的JWT验证
        auth_user = security_get_current_user(
            authorization=f"Bearer {credentials.credentials}",
            db=db
        )
        return _auth_user_to_db_user(auth_user, db)
    except HTTPException:
        # JWT验证失败，抛出异常
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user_optional: {e}", exc_info=True)
        raise HTTPException(
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
            detail={
                "code": SystemErrorCodes.INTERNAL_ERROR.code,
                "message": "认证过程发生错误"
            }
        )


async def get_current_active_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前活跃用户（必须认证）

    Returns:
        User: 数据库User对象

    Raises:
        HTTPException: 401 - 未认证或认证失败
        HTTPException: 403 - 用户已被禁用
    """
    if not credentials:
        raise HTTPException(
            status_code=AuthErrorCodes.TOKEN_MISSING.status_code,
            detail={
                "code": AuthErrorCodes.TOKEN_MISSING.code,
                "message": AuthErrorCodes.TOKEN_MISSING.message
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # 使用真实的JWT验证（调用 get_current_user 而非 get_current_active_user）
        auth_user = security_get_current_user(
            authorization=f"Bearer {credentials.credentials}",
            db=db
        )

        # 转换为DB User对象
        db_user = _auth_user_to_db_user(auth_user, db)

        # 额外检查：确保用户活跃（如果DB user存在is_active字段）
        if hasattr(db_user, 'is_active') and not db_user.is_active:
            raise HTTPException(
                status_code=AuthErrorCodes.USER_DISABLED.status_code,
                detail={
                    "code": AuthErrorCodes.USER_DISABLED.code,
                    "message": AuthErrorCodes.USER_DISABLED.message
                }
            )

        logger.info(f"User authenticated successfully: {db_user.email}, role: {db_user.role}")
        return db_user

    except HTTPException:
        # JWT验证失败，直接抛出
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_current_active_user: {e}", exc_info=True)
        raise HTTPException(
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
            detail={
                "code": SystemErrorCodes.INTERNAL_ERROR.code,
                "message": "认证过程发生错误"
            }
        )


# 简化的别名，用于向后兼容
get_current_user = get_current_active_user


def require_role(allowed_roles: Union[str, List[str]]):
    """角色权限装饰器

    Args:
        allowed_roles: 允许的角色列表，单个角色可以是字符串

    Returns:
        依赖函数
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=AuthErrorCodes.PERMISSION_DENIED.status_code,
                detail={
                    "code": AuthErrorCodes.PERMISSION_DENIED.code,
                    "message": f"权限不足，需要角色: {', '.join(allowed_roles)}"
                }
            )
        return current_user

    return role_checker


def require_admin():
    """需要管理员权限"""
    return require_role("admin")


def require_finance():
    """需要财务权限"""
    return require_role(["admin", "finance"])


def require_data_operator():
    """需要数据员权限"""
    return require_role(["admin", "data_operator"])


def require_account_manager():
    """需要户管权限"""
    return require_role(["admin", "account_manager"])


def require_media_buyer():
    """需要投手权限"""
    return require_role(["admin", "media_buyer"])


# 角色权限映射
ROLE_PERMISSIONS = {
    "admin": ["*"],  # 管理员拥有所有权限
    "finance": [
        "finance:read", "finance:create", "finance:update",
        "topup:approve", "topup:confirm", "reconciliation:manage"
    ],
    "data_operator": [
        "project:read", "project:update",
        "account:read", "account:assign",
        "report:submit", "report:review"
    ],
    "account_manager": [
        "account:create", "account:read", "account:update",
        "channel:read", "channel:apply"
    ],
    "media_buyer": [
        "account:read", "account:monitor",
        "report:submit", "topup:request"
    ]
}


def has_permission(user: User, permission: str) -> bool:
    """检查用户是否有特定权限

    Args:
        user: 用户对象
        permission: 权限标识

    Returns:
        是否有权限
    """
    # 管理员拥有所有权限
    if user.role == "admin":
        return True

    # 获取用户角色的权限列表
    permissions = ROLE_PERMISSIONS.get(user.role, [])

    # 检查是否有通配符权限
    if "*" in permissions:
        return True

    # 检查具体权限
    return permission in permissions


def require_permission(permission: str):
    """权限检查装饰器

    Args:
        permission: 需要的权限

    Returns:
        依赖函数
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=AuthErrorCodes.PERMISSION_DENIED.status_code,
                detail={
                    "code": AuthErrorCodes.PERMISSION_DENIED.code,
                    "message": f"权限不足，需要权限: {permission}"
                }
            )
        return current_user

    return permission_checker


# 项目相关权限
def require_project_access(action: str = "read"):
    """项目访问权限

    Args:
        action: 操作类型 (read, update, delete)
    """
    return require_permission(f"project:{action}")


# 账户相关权限
def require_account_access(action: str = "read"):
    """账户访问权限

    Args:
        action: 操作类型 (read, update, assign)
    """
    return require_permission(f"account:{action}")


# 财务相关权限
def require_finance_access(action: str = "read"):
    """财务访问权限

    Args:
        action: 操作类型 (read, approve, confirm)
    """
    return require_permission(f"finance:{action}")


# 报表相关权限
def require_report_access(action: str = "read"):
    """报表访问权限

    Args:
        action: 操作类型 (read, submit, review)
    """
    return require_permission(f"report:{action}")

def get_client_info(request: Request) -> Tuple[str, str]:
    """获取客户端信息
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        (client_ip, user_agent) 元组
    """
    # 获取客户端IP
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"
    
    # 获取User-Agent
    user_agent = request.headers.get("user-agent", "unknown")
    
    return client_ip, user_agent
