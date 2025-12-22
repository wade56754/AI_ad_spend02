"""
权限管理模块
提供角色和权限检查功能

SoT Reference: MASTER.md v4.4 §2.4 (角色定义)
"""

from functools import wraps
from typing import Callable, Iterable, List, Union, Dict, Any, Optional
from enum import Enum
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.error_codes import ErrorCode
from backend.core.security import (
    AuthenticatedUser,
    get_current_active_user,
    require_roles as _require_roles,
    require_permissions as _require_permissions
)
from backend.core.database import get_db
from backend.models.enums import UserRole


class Permission(str, Enum):
    """权限枚举 - 按系统概述权限矩阵设计"""
    # 用户管理权限
    USER_MANAGE = "user_manage"

    # 项目管理权限
    PROJECT_CREATE = "project_create"
    PROJECT_READ = "project_read"
    PROJECT_UPDATE = "project_update"
    PROJECT_DELETE = "project_delete"

    # 渠道管理权限
    CHANNEL_CREATE = "channel_create"
    CHANNEL_READ = "channel_read"
    CHANNEL_UPDATE = "channel_update"
    CHANNEL_DELETE = "channel_delete"

    # 账户管理权限
    ACCOUNT_CREATE = "account_create"
    ACCOUNT_READ = "account_read"
    ACCOUNT_UPDATE = "account_update"
    ACCOUNT_DELETE = "account_delete"

    # 日报管理权限
    DAILY_REPORT_CREATE = "daily_report_create"
    DAILY_REPORT_READ = "daily_report_read"
    DAILY_REPORT_UPDATE = "daily_report_update"
    DAILY_REPORT_DELETE = "daily_report_delete"
    DAILY_REPORT_AUDIT = "daily_report_audit"

    # 充值管理权限
    TOPUP_CREATE = "topup_create"
    TOPUP_READ = "topup_read"
    TOPUP_UPDATE = "topup_update"
    TOPUP_DELETE = "topup_delete"
    TOPUP_APPROVE = "topup_approve"

    # 财务对账权限
    RECONCILIATION_CREATE = "reconciliation_create"
    RECONCILIATION_READ = "reconciliation_read"
    RECONCILIATION_UPDATE = "reconciliation_update"
    RECONCILIATION_DELETE = "reconciliation_delete"

    # 报表查看权限
    REPORT_READ = "report_read"
    REPORT_EXPORT = "report_export"

    # AI监控权限
    AI_MONITORING = "ai_monitoring"
    AI_ANALYSIS = "ai_analysis"

    # 通知系统权限
    NOTIFICATION_MANAGE = "notification_manage"

    # 系统管理权限
    SYSTEM_CONFIG = "system_config"
    AUDIT_LOG = "audit_log"


# 角色权限映射 - 严格按照系统概述权限矩阵
ROLE_PERMISSIONS: Dict[UserRole, List[Permission]] = {
    UserRole.ADMIN: [
        # 管理员拥有全部权限 ✅
        Permission.USER_MANAGE,
        Permission.PROJECT_CREATE, Permission.PROJECT_READ, Permission.PROJECT_UPDATE, Permission.PROJECT_DELETE,
        Permission.CHANNEL_CREATE, Permission.CHANNEL_READ, Permission.CHANNEL_UPDATE, Permission.CHANNEL_DELETE,
        Permission.ACCOUNT_CREATE, Permission.ACCOUNT_READ, Permission.ACCOUNT_UPDATE, Permission.ACCOUNT_DELETE,
        Permission.DAILY_REPORT_CREATE, Permission.DAILY_REPORT_READ, Permission.DAILY_REPORT_UPDATE, Permission.DAILY_REPORT_DELETE, Permission.DAILY_REPORT_AUDIT,
        Permission.TOPUP_CREATE, Permission.TOPUP_READ, Permission.TOPUP_UPDATE, Permission.TOPUP_DELETE, Permission.TOPUP_APPROVE,
        Permission.RECONCILIATION_CREATE, Permission.RECONCILIATION_READ, Permission.RECONCILIATION_UPDATE, Permission.RECONCILIATION_DELETE,
        Permission.REPORT_READ, Permission.REPORT_EXPORT,
        Permission.AI_MONITORING, Permission.AI_ANALYSIS,
        Permission.NOTIFICATION_MANAGE,
        Permission.SYSTEM_CONFIG, Permission.AUDIT_LOG
    ],
    UserRole.ACCOUNT_MANAGER: [
        # 户管权限 - ✅ 用户管理、项目管理、渠道管理(只读)、账户管理、日报管理(只读)、充值管理(只读)、财务对账(只读)、报表查看
        Permission.USER_MANAGE,
        Permission.PROJECT_CREATE, Permission.PROJECT_READ, Permission.PROJECT_UPDATE,
        Permission.CHANNEL_READ,
        Permission.ACCOUNT_CREATE, Permission.ACCOUNT_READ, Permission.ACCOUNT_UPDATE,
        Permission.DAILY_REPORT_READ,
        Permission.TOPUP_READ,
        Permission.RECONCILIATION_READ,
        Permission.REPORT_READ, Permission.REPORT_EXPORT
    ],
    UserRole.DATA_OPERATOR: [
        # 数据员权限 - 👁 项目管理(只读)、✅ 渠道管理、✅ 账户管理、✅ 日报管理、✅ 充值管理、👁 报表查看
        Permission.PROJECT_READ,
        Permission.CHANNEL_CREATE, Permission.CHANNEL_READ, Permission.CHANNEL_UPDATE, Permission.CHANNEL_DELETE,
        Permission.ACCOUNT_CREATE, Permission.ACCOUNT_READ, Permission.ACCOUNT_UPDATE, Permission.ACCOUNT_DELETE,
        Permission.DAILY_REPORT_CREATE, Permission.DAILY_REPORT_READ, Permission.DAILY_REPORT_UPDATE, Permission.DAILY_REPORT_DELETE, Permission.DAILY_REPORT_AUDIT,
        Permission.TOPUP_CREATE, Permission.TOPUP_READ, Permission.TOPUP_UPDATE, Permission.TOPUP_DELETE,
        Permission.REPORT_READ
    ],
    UserRole.FINANCE: [
        # 财务权限 - 👁 项目管理(只读)、👁 账户管理(只读)、👁 日报管理(只读)、✅ 充值管理、✅ 财务对账、👁 报表查看
        Permission.PROJECT_READ,
        Permission.ACCOUNT_READ,
        Permission.DAILY_REPORT_READ,
        Permission.TOPUP_CREATE, Permission.TOPUP_READ, Permission.TOPUP_UPDATE, Permission.TOPUP_DELETE, Permission.TOPUP_APPROVE,
        Permission.RECONCILIATION_CREATE, Permission.RECONCILIATION_READ, Permission.RECONCILIATION_UPDATE, Permission.RECONCILIATION_DELETE,
        Permission.REPORT_READ, Permission.REPORT_EXPORT
    ],
    UserRole.MEDIA_BUYER: [
        # 投手权限 - ✅ 账户管理(只读)、✅ 日报管理、✅ 充值管理、👁 报表查看
        Permission.ACCOUNT_READ,
        Permission.DAILY_REPORT_CREATE, Permission.DAILY_REPORT_READ, Permission.DAILY_REPORT_UPDATE,
        Permission.TOPUP_CREATE, Permission.TOPUP_READ, Permission.TOPUP_UPDATE, Permission.TOPUP_DELETE,
        Permission.REPORT_READ
    ]
    # 注意: ANALYST 角色已移除 (SoT 仅定义 5 个合法角色)
}


def get_user_permissions(user: AuthenticatedUser) -> List[Permission]:
    """获取用户权限列表

    Args:
        user: 认证用户对象

    Returns:
        用户权限列表

    Raises:
        ValueError: 用户角色不在合法角色列表中
    """
    try:
        user_role = UserRole(user.role)
    except ValueError:
        raise ValueError(
            f"Invalid user role: {user.role}. "
            f"Must be one of: {[r.value for r in UserRole]}"
        )

    # 基础角色权限
    permissions = set(ROLE_PERMISSIONS.get(user_role, []))

    # 用户自定义权限（如果有）
    if user.permissions:
        permissions.update(user.permissions)

    return list(permissions)


def check_role_permission(user: AuthenticatedUser, required_roles: Iterable[str]) -> bool:
    """检查用户角色权限"""
    if not required_roles:
        return True

    return user.role in required_roles


def check_user_permission(user: AuthenticatedUser, required_permissions: Iterable[Union[str, Permission]]) -> bool:
    """检查用户具体权限"""
    if not required_permissions:
        return True

    # 获取用户权限值集合
    user_permissions = set(p.value if isinstance(p, Permission) else p for p in get_user_permissions(user))
    # 获取所需权限值集合
    required_perms = set(p.value if isinstance(p, Permission) else p for p in required_permissions)

    return required_perms.issubset(user_permissions)


def require_roles(*roles: str):
    """
    角色权限装饰器
    要求用户具有指定角色之一
    """
    return _require_roles(*roles)


def require_permissions(*permissions: Union[str, Permission]):
    """
    权限检查装饰器
    要求用户具有所有指定权限
    """
    return _require_permissions(*(p.value if isinstance(p, Permission) else p for p in permissions))


def require_any_role(*roles: str):
    """
    角色权限装饰器（任一角色）
    要求用户具有指定角色中的任意一个
    """
    return _require_roles(*roles)


def require_any_permission(*permissions: Union[str, Permission]):
    """
    权限检查装饰器（任一权限）
    要求用户具有指定权限中的任意一个
    """
    def permission_dependency(current_user: AuthenticatedUser = Depends(get_current_active_user)) -> AuthenticatedUser:
        user_permissions = set(get_user_permissions(current_user))
        required_permissions = set(str(p) for p in permissions)

        if not user_permissions.intersection(required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": ErrorCode.PERMISSION_DENIED, "message": "权限不足"}
            )
        return current_user
    return permission_dependency


def require_project_access(project_id: str = None):
    """
    项目访问权限装饰器
    检查用户是否有权访问指定项目
    """
    def project_dependency(current_user: AuthenticatedUser = Depends(get_current_active_user)) -> AuthenticatedUser:
        # 这里应该实现实际的项目权限检查逻辑
        # 例如检查用户是否是项目的创建者、管理者或成员

        # 管理员可以访问所有项目
        if current_user.role == UserRole.ADMIN.value:
            return current_user

        # 其他角色需要具体的项目权限检查
        # 这里应该查询数据库检查用户与项目的关系

        return current_user
    return project_dependency


def require_account_access(account_id: str = None):
    """
    账户访问权限装饰器
    检查用户是否有权访问指定账户
    """
    def account_dependency(current_user: AuthenticatedUser = Depends(get_current_active_user)) -> AuthenticatedUser:
        # 这里应该实现实际的账户权限检查逻辑

        # 管理员可以访问所有账户
        if current_user.role == UserRole.ADMIN.value:
            return current_user

        # 其他角色需要检查账户所有权或权限

        return current_user
    return account_dependency


class PermissionChecker:
    """权限检查器类"""

    def __init__(self, user: AuthenticatedUser):
        self.user = user
        self._permissions = None

    @property
    def permissions(self) -> List[Permission]:
        """获取用户权限（缓存）"""
        if self._permissions is None:
            self._permissions = get_user_permissions(self.user)
        return self._permissions

    def has_role(self, role: Union[str, UserRole]) -> bool:
        """检查用户是否具有指定角色"""
        return self.user.role == str(role)

    def has_any_role(self, *roles: Union[str, UserRole]) -> bool:
        """检查用户是否具有任意指定角色"""
        return self.user.role in [str(role) for role in roles]

    def has_permission(self, permission: Union[str, Permission]) -> bool:
        """检查用户是否具有指定权限"""
        return str(permission) in self.permissions

    def has_any_permission(self, *permissions: Union[str, Permission]) -> bool:
        """检查用户是否具有任意指定权限"""
        user_perms = set(self.permissions)
        required_perms = set(str(p) for p in permissions)
        return bool(user_perms.intersection(required_perms))

    def has_all_permissions(self, *permissions: Union[str, Permission]) -> bool:
        """检查用户是否具有所有指定权限"""
        user_perms = set(self.permissions)
        required_perms = set(str(p) for p in permissions)
        return required_perms.issubset(user_perms)


def get_permission_checker(user: AuthenticatedUser = Depends(get_current_active_user)) -> PermissionChecker:
    """获取权限检查器依赖"""
    return PermissionChecker(user)


# 便捷装饰器
def admin_required(user: AuthenticatedUser = Depends(get_current_active_user)) -> AuthenticatedUser:
    """要求管理员角色"""
    if user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": ErrorCode.PERMISSION_DENIED, "message": "需要管理员权限"}
        )
    return user


def finance_required(user: AuthenticatedUser = Depends(get_current_active_user)) -> AuthenticatedUser:
    """要求财务权限"""
    if user.role not in [UserRole.ADMIN.value, UserRole.FINANCE.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": ErrorCode.PERMISSION_DENIED, "message": "需要财务权限"}
        )
    return user


def account_manager_required(user: AuthenticatedUser = Depends(get_current_active_user)) -> AuthenticatedUser:
    """要求户管权限"""
    if user.role not in [UserRole.ADMIN.value, UserRole.ACCOUNT_MANAGER.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": ErrorCode.PERMISSION_DENIED, "message": "需要户管权限"}
        )
    return user


def data_operator_required(user: AuthenticatedUser = Depends(get_current_active_user)) -> AuthenticatedUser:
    """要求数据员权限"""
    if user.role not in [UserRole.ADMIN.value, UserRole.DATA_OPERATOR.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": ErrorCode.PERMISSION_DENIED, "message": "需要数据员权限"}
        )
    return user


def media_buyer_required(user: AuthenticatedUser = Depends(get_current_active_user)) -> AuthenticatedUser:
    """要求投手权限"""
    if user.role not in [UserRole.ADMIN.value, UserRole.MEDIA_BUYER.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": ErrorCode.PERMISSION_DENIED, "message": "需要投手权限"}
        )
    return user


# ============================================================================
# 项目负责人权限守卫
# ============================================================================

def require_project_owner(project_id: int):
    """
    项目负责人权限守卫

    检查当前用户是否为指定项目的负责人（project_members.role = 'owner'）

    根据 MASTER.md v4.4 §2.4:
    - project_owner 角色通过 project_members 表确定
    - 用户在 project_members 表中 role = 'owner' 即为该项目的负责人
    - admin 角色可以绕过此检查

    Args:
        project_id: 项目 ID

    Returns:
        FastAPI 依赖函数

    Raises:
        HTTPException 403: 非项目负责人

    Usage:
        @router.put("/projects/{project_id}/budget")
        async def update_project_budget(
            project_id: int,
            user: AuthenticatedUser = Depends(require_project_owner(project_id))
        ):
            ...
    """
    def project_owner_dependency(
        current_user: AuthenticatedUser = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> AuthenticatedUser:
        # admin 可以绕过检查
        if current_user.role == UserRole.ADMIN.value:
            return current_user

        # 延迟导入避免循环依赖
        from backend.models.core.project_member import ProjectMember

        # 查询 project_members 表
        membership = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == UUID(str(current_user.id))
        ).first()

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": ErrorCode.PERMISSION_DENIED,
                    "message": "您不是此项目的成员"
                }
            )

        if membership.role != 'owner':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": ErrorCode.PERMISSION_DENIED,
                    "message": "此操作需要项目负责人权限"
                }
            )

        return current_user

    return project_owner_dependency


def is_project_owner(
    user_id: UUID,
    project_id: int,
    db: Session
) -> bool:
    """
    检查用户是否为项目负责人（非装饰器版本）

    用于 Service 层中的权限检查

    Args:
        user_id: 用户 UUID
        project_id: 项目 ID
        db: 数据库会话

    Returns:
        True = 是项目负责人
        False = 不是项目负责人
    """
    from backend.models.core.project_member import ProjectMember

    membership = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()

    return membership is not None and membership.role == 'owner'


def get_user_owned_projects(
    user_id: UUID,
    db: Session
) -> List[int]:
    """
    获取用户作为负责人的所有项目 ID

    Args:
        user_id: 用户 UUID
        db: 数据库会话

    Returns:
        项目 ID 列表
    """
    from backend.models.core.project_member import ProjectMember

    memberships = db.query(ProjectMember.project_id).filter(
        ProjectMember.user_id == user_id,
        ProjectMember.role == 'owner'
    ).all()

    return [m.project_id for m in memberships]


def require_project_member(project_id: int, allowed_roles: List[str] = None):
    """
    项目成员权限守卫

    检查当前用户是否为指定项目的成员，可选限制角色

    Args:
        project_id: 项目 ID
        allowed_roles: 允许的项目角色列表，默认 ['owner', 'member', 'viewer']

    Returns:
        FastAPI 依赖函数
    """
    if allowed_roles is None:
        allowed_roles = ['owner', 'member', 'viewer']

    def project_member_dependency(
        current_user: AuthenticatedUser = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> AuthenticatedUser:
        # admin 可以绕过检查
        if current_user.role == UserRole.ADMIN.value:
            return current_user

        from backend.models.core.project_member import ProjectMember

        membership = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == UUID(str(current_user.id))
        ).first()

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": ErrorCode.PERMISSION_DENIED,
                    "message": "您不是此项目的成员"
                }
            )

        if membership.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": ErrorCode.PERMISSION_DENIED,
                    "message": f"此操作需要以下项目角色之一: {', '.join(allowed_roles)}"
                }
            )

        return current_user

    return project_member_dependency

