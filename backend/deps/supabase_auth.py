"""
Supabase认证依赖
Version: 1.0
Author: Claude协作开发
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any, List

from services.supabase_auth_service import supabase_auth_service

# HTTP Bearer认证
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    获取当前用户（可选）
    如果没有提供token，返回None
    """
    if not credentials:
        return None

    try:
        user_data = await supabase_auth_service.verify_token(credentials.credentials)
        return user_data
    except HTTPException:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    获取当前认证用户
    必须提供有效的token
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_data = await supabase_auth_service.verify_token(credentials.credentials)

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查用户是否激活
    if not user_data.get("profile", {}).get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )

    return user_data


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取当前活跃用户
    （与get_current_user相同，但提供更清晰的语义）
    """
    return current_user


def require_role(required_roles: List[str]):
    """
    角色权限装饰器工厂

    Args:
        required_roles: 需要的角色列表

    Returns:
        依赖函数
    """
    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        user_profile = current_user.get("profile", {})
        user_role = user_profile.get("role")

        if not user_role or user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下角色之一: {', '.join(required_roles)}",
                headers={"X-Required-Roles": ", ".join(required_roles)}
            )

        return current_user

    return role_checker


def require_permission(permission: str):
    """
    权限检查装饰器工厂

    Args:
        permission: 需要的权限

    Returns:
        依赖函数
    """
    async def permission_checker(
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        user_profile = current_user.get("profile", {})
        user_role = user_profile.get("role")

        # 检查权限映射
        role_permissions = {
            "admin": [
                "read", "write", "delete", "manage_users", "manage_projects",
                "manage_finances", "view_all_reports", "approve_topups",
                "manage_channels", "system_settings"
            ],
            "finance": [
                "read", "write", "manage_finances", "view_financial_reports",
                "approve_topups", "manage_reconciliations"
            ],
            "data_operator": [
                "read", "write_reports", "view_reports", "import_data",
                "export_data", "manage_daily_reports"
            ],
            "account_manager": [
                "read", "write", "manage_projects", "view_team_reports",
                "assign_accounts", "manage_ad_accounts"
            ],
            "media_buyer": [
                "read_own", "write_own", "view_own_reports",
                "submit_daily_reports", "manage_own_accounts"
            ]
        }

        permissions = role_permissions.get(user_role, [])

        if permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要权限: {permission}",
                headers={"X-Required-Permission": permission}
            )

        return current_user

    return permission_checker


def require_ownership(resource_user_id_field: str = "user_id"):
    """
    资源所有权检查装饰器工厂

    Args:
        resource_user_id_field: 资源中用户ID字段的名称

    Returns:
        依赖函数
    """
    async def ownership_checker(
        request: Request,
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        # 获取资源的用户ID
        # 这个需要在具体的路由中实现
        # 这里只是示例
        return current_user

    return ownership_checker


# 常用角色依赖
require_admin = require_role(["admin"])
require_finance = require_role(["admin", "finance"])
require_manager = require_role(["admin", "account_manager"])
require_data_operator = require_role(["admin", "finance", "data_operator"])
require_any_authenticated = require_role([
    "admin", "finance", "data_operator", "account_manager", "media_buyer"
])

# 常用权限依赖
require_user_management = require_permission("manage_users")
require_project_management = require_permission("manage_projects")
require_financial_management = require_permission("manage_finances")
require_report_management = require_permission("manage_reports")
require_topup_approval = require_permission("approve_topups")


class SecurityHeaders:
    """安全头部工具"""

    @staticmethod
    def add_security_headers(response):
        """添加安全头部"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


def get_client_ip(request: Request) -> Optional[str]:
    """获取客户端真实IP"""
    # 尝试从各种头部获取真实IP
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    cf_connecting_ip = request.headers.get("CF-Connecting-IP")
    if cf_connecting_ip:
        return cf_connecting_ip

    return request.client.host if request.client else None


async def validate_device_fingerprint(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> bool:
    """
    验证设备指纹（简单实现）
    可以扩展为更复杂的指纹验证
    """
    # 获取当前请求的设备信息
    user_agent = request.headers.get("user-agent", "")
    ip_address = get_client_ip(request)

    # 这里可以实现更复杂的设备指纹逻辑
    # 例如：检查Canvas指纹、WebGL指纹等

    return True