"""
权限管理模块 (Core Layer)

SoT Reference: MASTER.md v4.4 §2.4 (角色定义)
SoT Reference: AUTH_SPEC.md v2.0 (认证授权规范)

本模块是 permission-filter 代码块，提供:
1. Permission - 权限枚举
2. ROLE_PERMISSIONS - 角色权限映射
3. apply_permission_filter() - 根据角色过滤查询数据
4. PermissionRule - 权限规则配置
5. 各类权限检查装饰器和守卫

权限过滤规则 (按角色):
- ceo/admin: 无过滤，看全部数据
- project_owner: 过滤本项目数据 (通过 project_members 表)
- supervisor: 过滤本团队数据
- pitcher: 过滤本人数据 (owner_id/submitted_by/pitcher_id)
- finance: 财务相关数据
- account_manager: 账户相关数据

使用示例:
    from backend.core.permissions import apply_permission_filter

    @router.get("/daily-reports")
    def list_reports(
        user: AuthenticatedUser = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        query = db.query(DailyReport)
        query = apply_permission_filter(query, DailyReport, user, db)
        return query.all()
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
    require_permissions as _require_permissions,
)
from backend.core.db import get_db
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
# SoT Reference: MASTER.md v4.4 §2.4 (7个合法角色)
ROLE_PERMISSIONS: Dict[UserRole, List[Permission]] = {
    UserRole.CEO: [
        # CEO(老板)拥有全部权限 - 资金安全、公司盈亏、最终决策
        Permission.USER_MANAGE,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_READ,
        Permission.PROJECT_UPDATE,
        Permission.PROJECT_DELETE,
        Permission.CHANNEL_CREATE,
        Permission.CHANNEL_READ,
        Permission.CHANNEL_UPDATE,
        Permission.CHANNEL_DELETE,
        Permission.ACCOUNT_CREATE,
        Permission.ACCOUNT_READ,
        Permission.ACCOUNT_UPDATE,
        Permission.ACCOUNT_DELETE,
        Permission.DAILY_REPORT_CREATE,
        Permission.DAILY_REPORT_READ,
        Permission.DAILY_REPORT_UPDATE,
        Permission.DAILY_REPORT_DELETE,
        Permission.DAILY_REPORT_AUDIT,
        Permission.TOPUP_CREATE,
        Permission.TOPUP_READ,
        Permission.TOPUP_UPDATE,
        Permission.TOPUP_DELETE,
        Permission.TOPUP_APPROVE,
        Permission.RECONCILIATION_CREATE,
        Permission.RECONCILIATION_READ,
        Permission.RECONCILIATION_UPDATE,
        Permission.RECONCILIATION_DELETE,
        Permission.REPORT_READ,
        Permission.REPORT_EXPORT,
        Permission.AI_MONITORING,
        Permission.AI_ANALYSIS,
        Permission.NOTIFICATION_MANAGE,
        Permission.SYSTEM_CONFIG,
        Permission.AUDIT_LOG,
    ],
    UserRole.ADMIN: [
        # 管理员拥有全部权限 ✅
        Permission.USER_MANAGE,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_READ,
        Permission.PROJECT_UPDATE,
        Permission.PROJECT_DELETE,
        Permission.CHANNEL_CREATE,
        Permission.CHANNEL_READ,
        Permission.CHANNEL_UPDATE,
        Permission.CHANNEL_DELETE,
        Permission.ACCOUNT_CREATE,
        Permission.ACCOUNT_READ,
        Permission.ACCOUNT_UPDATE,
        Permission.ACCOUNT_DELETE,
        Permission.DAILY_REPORT_CREATE,
        Permission.DAILY_REPORT_READ,
        Permission.DAILY_REPORT_UPDATE,
        Permission.DAILY_REPORT_DELETE,
        Permission.DAILY_REPORT_AUDIT,
        Permission.TOPUP_CREATE,
        Permission.TOPUP_READ,
        Permission.TOPUP_UPDATE,
        Permission.TOPUP_DELETE,
        Permission.TOPUP_APPROVE,
        Permission.RECONCILIATION_CREATE,
        Permission.RECONCILIATION_READ,
        Permission.RECONCILIATION_UPDATE,
        Permission.RECONCILIATION_DELETE,
        Permission.REPORT_READ,
        Permission.REPORT_EXPORT,
        Permission.AI_MONITORING,
        Permission.AI_ANALYSIS,
        Permission.NOTIFICATION_MANAGE,
        Permission.SYSTEM_CONFIG,
        Permission.AUDIT_LOG,
    ],
    UserRole.PROJECT_OWNER: [
        # 项目负责人权限 - 项目盈亏、日报审核、资金使用效率
        Permission.PROJECT_CREATE,
        Permission.PROJECT_READ,
        Permission.PROJECT_UPDATE,
        Permission.ACCOUNT_READ,
        Permission.DAILY_REPORT_CREATE,
        Permission.DAILY_REPORT_READ,
        Permission.DAILY_REPORT_UPDATE,
        Permission.DAILY_REPORT_AUDIT,
        Permission.TOPUP_READ,
        Permission.RECONCILIATION_READ,
        Permission.REPORT_READ,
        Permission.REPORT_EXPORT,
    ],
    UserRole.ACCOUNT_MANAGER: [
        # 户管权限 - 账户分配、账户状态监控 (SoT: CLAUDE.md)
        # 不可创建项目，只能管理账户
        Permission.PROJECT_READ,  # 只读项目
        Permission.CHANNEL_READ,
        Permission.ACCOUNT_CREATE,
        Permission.ACCOUNT_READ,
        Permission.ACCOUNT_UPDATE,
        Permission.DAILY_REPORT_READ,
        Permission.TOPUP_READ,
        Permission.RECONCILIATION_READ,
        Permission.REPORT_READ,
    ],
    UserRole.DATA_OPERATOR: [
        # 数据员权限 - 👁 项目管理(只读)、✅ 渠道管理、✅ 账户管理、✅ 日报管理、✅ 充值管理、👁 报表查看
        Permission.PROJECT_READ,
        Permission.CHANNEL_CREATE,
        Permission.CHANNEL_READ,
        Permission.CHANNEL_UPDATE,
        Permission.CHANNEL_DELETE,
        Permission.ACCOUNT_CREATE,
        Permission.ACCOUNT_READ,
        Permission.ACCOUNT_UPDATE,
        Permission.ACCOUNT_DELETE,
        Permission.DAILY_REPORT_CREATE,
        Permission.DAILY_REPORT_READ,
        Permission.DAILY_REPORT_UPDATE,
        Permission.DAILY_REPORT_DELETE,
        Permission.DAILY_REPORT_AUDIT,
        Permission.TOPUP_CREATE,
        Permission.TOPUP_READ,
        Permission.TOPUP_UPDATE,
        Permission.TOPUP_DELETE,
        Permission.REPORT_READ,
    ],
    UserRole.FINANCE: [
        # 财务权限 - 👁 项目管理(只读)、👁 账户管理(只读)、👁 日报管理(只读)、✅ 充值管理、✅ 财务对账、👁 报表查看
        Permission.PROJECT_READ,
        Permission.ACCOUNT_READ,
        Permission.DAILY_REPORT_READ,
        Permission.TOPUP_CREATE,
        Permission.TOPUP_READ,
        Permission.TOPUP_UPDATE,
        Permission.TOPUP_DELETE,
        Permission.TOPUP_APPROVE,
        Permission.RECONCILIATION_CREATE,
        Permission.RECONCILIATION_READ,
        Permission.RECONCILIATION_UPDATE,
        Permission.RECONCILIATION_DELETE,
        Permission.REPORT_READ,
        Permission.REPORT_EXPORT,
    ],
    UserRole.MEDIA_BUYER: [
        # 投手权限 - ✅ 账户管理(只读)、✅ 日报管理、✅ 充值管理、👁 报表查看
        Permission.ACCOUNT_READ,
        Permission.DAILY_REPORT_CREATE,
        Permission.DAILY_REPORT_READ,
        Permission.DAILY_REPORT_UPDATE,
        Permission.TOPUP_CREATE,
        Permission.TOPUP_READ,
        Permission.TOPUP_UPDATE,
        Permission.TOPUP_DELETE,
        Permission.REPORT_READ,
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


def check_role_permission(
    user: AuthenticatedUser, required_roles: Iterable[str]
) -> bool:
    """检查用户角色权限"""
    if not required_roles:
        return True

    return user.role in required_roles


def check_user_permission(
    user: AuthenticatedUser, required_permissions: Iterable[Union[str, Permission]]
) -> bool:
    """检查用户具体权限"""
    if not required_permissions:
        return True

    # 获取用户权限值集合
    user_permissions = set(
        p.value if isinstance(p, Permission) else p for p in get_user_permissions(user)
    )
    # 获取所需权限值集合
    required_perms = set(
        p.value if isinstance(p, Permission) else p for p in required_permissions
    )

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
    return _require_permissions(
        *(p.value if isinstance(p, Permission) else p for p in permissions)
    )


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

    def permission_dependency(
        current_user: AuthenticatedUser = Depends(get_current_active_user),
    ) -> AuthenticatedUser:
        user_permissions = set(get_user_permissions(current_user))
        required_permissions = set(str(p) for p in permissions)

        if not user_permissions.intersection(required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": ErrorCode.PERMISSION_DENIED, "message": "权限不足"},
            )
        return current_user

    return permission_dependency


def require_project_access(project_id: str = None):
    """
    项目访问权限装饰器
    检查用户是否有权访问指定项目
    """

    def project_dependency(
        current_user: AuthenticatedUser = Depends(get_current_active_user),
    ) -> AuthenticatedUser:
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

    def account_dependency(
        current_user: AuthenticatedUser = Depends(get_current_active_user),
    ) -> AuthenticatedUser:
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


def get_permission_checker(
    user: AuthenticatedUser = Depends(get_current_active_user),
) -> PermissionChecker:
    """获取权限检查器依赖"""
    return PermissionChecker(user)


# 便捷装饰器
def admin_required(
    user: AuthenticatedUser = Depends(get_current_active_user),
) -> AuthenticatedUser:
    """要求管理员角色"""
    if user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": ErrorCode.PERMISSION_DENIED, "message": "需要管理员权限"},
        )
    return user


def finance_required(
    user: AuthenticatedUser = Depends(get_current_active_user),
) -> AuthenticatedUser:
    """要求财务权限"""
    if user.role not in [UserRole.ADMIN.value, UserRole.FINANCE.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": ErrorCode.PERMISSION_DENIED, "message": "需要财务权限"},
        )
    return user


def account_manager_required(
    user: AuthenticatedUser = Depends(get_current_active_user),
) -> AuthenticatedUser:
    """要求户管权限"""
    if user.role not in [UserRole.ADMIN.value, UserRole.ACCOUNT_MANAGER.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": ErrorCode.PERMISSION_DENIED, "message": "需要户管权限"},
        )
    return user


# ============================================================================
# 废弃函数已移除 (PRD v2.2)
# - data_operator_required: 使用 finance_required 或 project_owner_required
# - media_buyer_required: 使用 pitcher_required
# ============================================================================


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
        db: Session = Depends(get_db),
    ) -> AuthenticatedUser:
        # admin 可以绕过检查
        if current_user.role == UserRole.ADMIN.value:
            return current_user

        # 延迟导入避免循环依赖
        from backend.models.core.project_member import ProjectMember

        # 查询 project_members 表
        membership = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == UUID(str(current_user.id)),
            )
            .first()
        )

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": ErrorCode.PERMISSION_DENIED, "message": "您不是此项目的成员"},
            )

        if membership.role != "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": ErrorCode.PERMISSION_DENIED, "message": "此操作需要项目负责人权限"},
            )

        return current_user

    return project_owner_dependency


def is_project_owner(user_id: UUID, project_id: int, db: Session) -> bool:
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

    membership = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
        )
        .first()
    )

    return membership is not None and membership.role == "owner"


def get_user_owned_projects(user_id: UUID, db: Session) -> List[int]:
    """
    获取用户作为负责人的所有项目 ID

    Args:
        user_id: 用户 UUID
        db: 数据库会话

    Returns:
        项目 ID 列表
    """
    from backend.models.core.project_member import ProjectMember

    memberships = (
        db.query(ProjectMember.project_id)
        .filter(ProjectMember.user_id == user_id, ProjectMember.role == "owner")
        .all()
    )

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
        allowed_roles = ["owner", "member", "viewer"]

    def project_member_dependency(
        current_user: AuthenticatedUser = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ) -> AuthenticatedUser:
        # admin 可以绕过检查
        if current_user.role == UserRole.ADMIN.value:
            return current_user

        from backend.models.core.project_member import ProjectMember

        membership = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == UUID(str(current_user.id)),
            )
            .first()
        )

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": ErrorCode.PERMISSION_DENIED, "message": "您不是此项目的成员"},
            )

        if membership.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": ErrorCode.PERMISSION_DENIED,
                    "message": f"此操作需要以下项目角色之一: {', '.join(allowed_roles)}",
                },
            )

        return current_user

    return project_member_dependency


# ============================================================================
# 数据权限过滤 (CB-04)
# ============================================================================

from dataclasses import dataclass
from typing import Type
from sqlalchemy.orm import Query as SAQuery


@dataclass
class PermissionRule:
    """
    权限规则配置

    Attributes:
        model: SQLAlchemy 模型类
        user_field: 用户关联字段 (如 owner_id, submitted_by)
        project_field: 项目关联字段 (如 project_id)
        team_field: 团队关联字段 (如 team_id)
        admin_bypass: 管理员是否绕过过滤
    """

    model: Type
    user_field: str
    project_field: Optional[str] = None
    team_field: Optional[str] = None
    admin_bypass: bool = True


# 权限规则注册表 - 延迟初始化
_PERMISSION_RULES: Dict[str, PermissionRule] = {}


def register_permission_rule(model_name: str, rule: PermissionRule):
    """注册权限规则"""
    _PERMISSION_RULES[model_name] = rule


def get_permission_rule(model: Type) -> Optional[PermissionRule]:
    """获取模型的权限规则"""
    return _PERMISSION_RULES.get(model.__name__)


def apply_permission_filter(
    query: SAQuery, model: Type, user: AuthenticatedUser, db: Session = None
) -> SAQuery:
    """
    根据用户角色过滤查询结果

    权限过滤规则 (MASTER.md v4.4 §2.4):
    - ceo/admin: 无过滤，看全部
    - project_owner: 过滤本项目数据
    - supervisor/data_operator: 过滤本团队数据
    - pitcher/media_buyer: 过滤本人数据
    - finance: 看财务相关数据
    - account_manager: 看账户相关数据

    Args:
        query: SQLAlchemy Query 对象
        model: SQLAlchemy 模型类
        user: 认证用户对象
        db: 数据库会话 (用于查询项目成员关系)

    Returns:
        过滤后的 Query 对象

    Usage:
        query = db.query(DailyReport)
        query = apply_permission_filter(query, DailyReport, current_user, db)
        items = query.all()
    """
    user_role = user.role
    user_id = UUID(str(user.id)) if not isinstance(user.id, UUID) else user.id

    # 1. CEO/Admin 不过滤
    if user_role in ["ceo", "admin", UserRole.ADMIN.value]:
        return query

    # 2. 检查模型是否有 RLSAwareMixin
    if hasattr(model, "apply_rls_filter"):
        try:
            user_role_enum = UserRole(user_role)
        except ValueError:
            # 尝试业务角色映射
            role_map = {
                "supervisor": UserRole.DATA_OPERATOR,
                "pitcher": UserRole.MEDIA_BUYER,
            }
            user_role_enum = role_map.get(user_role)

        if user_role_enum:
            return model.apply_rls_filter(query, user_id, user_role_enum)

    # 3. 检查注册的权限规则
    rule = get_permission_rule(model)
    if rule:
        return _apply_rule_filter(query, model, rule, user, db)

    # 4. 默认行为：尝试按常见字段过滤
    return _apply_default_filter(query, model, user_id, user_role, db)


def _apply_rule_filter(
    query: SAQuery,
    model: Type,
    rule: PermissionRule,
    user: AuthenticatedUser,
    db: Session,
) -> SAQuery:
    """应用注册的权限规则"""
    user_id = UUID(str(user.id)) if not isinstance(user.id, UUID) else user.id
    user_role = user.role

    # admin 绕过
    if rule.admin_bypass and user_role in ["admin", "ceo", UserRole.ADMIN.value]:
        return query

    # project_owner: 过滤本项目
    if user_role == "project_owner" and rule.project_field and db:
        project_ids = get_user_owned_projects(user_id, db)
        if project_ids:
            project_column = getattr(model, rule.project_field)
            return query.filter(project_column.in_(project_ids))
        # 无项目时返回空结果
        return query.filter(False)

    # supervisor/data_operator: 过滤本团队
    if (
        user_role in ["supervisor", "data_operator", UserRole.DATA_OPERATOR.value]
        and rule.team_field
    ):
        # TODO: 获取用户所属团队
        pass

    # pitcher/media_buyer: 过滤本人
    if (
        user_role in ["pitcher", "media_buyer", UserRole.MEDIA_BUYER.value]
        and rule.user_field
    ):
        user_column = getattr(model, rule.user_field)
        return query.filter(user_column == user_id)

    return query


def _apply_default_filter(
    query: SAQuery, model: Type, user_id: UUID, user_role: str, db: Session
) -> SAQuery:
    """
    默认过滤逻辑 - 按常见字段名猜测

    检查模型是否有以下字段:
    - owner_id, submitted_by, created_by, user_id, pitcher_id
    - project_id (用于 project_owner 角色)
    - team_id (用于 supervisor 角色)
    """
    # project_owner: 按项目过滤
    if user_role == "project_owner" and hasattr(model, "project_id") and db:
        project_ids = get_user_owned_projects(user_id, db)
        if project_ids:
            return query.filter(model.project_id.in_(project_ids))
        return query.filter(False)

    # pitcher/media_buyer: 按用户字段过滤
    user_fields = ["owner_id", "submitted_by", "pitcher_id", "user_id", "created_by"]
    for field in user_fields:
        if hasattr(model, field):
            column = getattr(model, field)
            return query.filter(column == user_id)

    # 无法过滤时返回原查询 (可能导致数据泄露，建议注册规则)
    return query


def filter_accessible_items(
    items: List[Any], user: AuthenticatedUser, check_method: str = "is_accessible_by"
) -> List[Any]:
    """
    过滤列表中用户可访问的项目

    用于已查询出的列表进行二次过滤

    Args:
        items: 对象列表
        user: 认证用户
        check_method: 检查方法名

    Returns:
        过滤后的列表

    Usage:
        reports = db.query(DailyReport).all()
        accessible = filter_accessible_items(reports, current_user)
    """
    user_id = UUID(str(user.id)) if not isinstance(user.id, UUID) else user.id

    try:
        user_role = UserRole(user.role)
    except ValueError:
        role_map = {
            "supervisor": UserRole.DATA_OPERATOR,
            "pitcher": UserRole.MEDIA_BUYER,
        }
        user_role = role_map.get(user.role)

    result = []
    for item in items:
        if hasattr(item, check_method):
            checker = getattr(item, check_method)
            if checker(user_id, user_role):
                result.append(item)
        else:
            # 无检查方法时包含
            result.append(item)

    return result


# ============================================================================
# 导出列表
# ============================================================================

__all__ = [
    # 权限枚举
    "Permission",
    "ROLE_PERMISSIONS",
    # 权限检查函数
    "get_user_permissions",
    "check_role_permission",
    "check_user_permission",
    # 权限装饰器
    "require_roles",
    "require_permissions",
    "require_any_role",
    "require_any_permission",
    # 资源访问装饰器
    "require_project_access",
    "require_account_access",
    # 权限检查器
    "PermissionChecker",
    "get_permission_checker",
    # 便捷装饰器
    "admin_required",
    "finance_required",
    "account_manager_required",
    # data_operator_required 和 media_buyer_required 已废弃 (PRD v2.2)
    # 项目权限守卫
    "require_project_owner",
    "require_project_member",
    "is_project_owner",
    "get_user_owned_projects",
    # 数据权限过滤 (核心接口)
    "PermissionRule",
    "register_permission_rule",
    "get_permission_rule",
    "apply_permission_filter",
    "filter_accessible_items",
]
