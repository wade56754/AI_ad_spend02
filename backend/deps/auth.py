"""
认证和权限控制依赖模块
提供JWT认证和基于角色的权限控制
"""
from typing import List, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.core.security import get_current_user
from backend.models.users import User

# HTTP Bearer认证方案
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """获取当前用户（可选）"""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials.credentials)
    except HTTPException:
        return None


async def get_current_active_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """获取当前活跃用户（必须认证）"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await get_current_user(credentials.credentials)


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
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要角色: {', '.join(allowed_roles)}",
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
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要权限: {permission}",
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