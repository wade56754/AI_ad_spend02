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
# 使用本地 JWT 认证服务 (已从 Supabase 迁移到本地 JWT)
from backend.services.local_auth_service import LocalAuthService
from backend.core.security import AuthenticatedUser
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
        auth_user: JWT验证后的用户对象 (来自 Supabase)
        db: 数据库会话

    Returns:
        User: 数据库User对象

    Raises:
        HTTPException: 401 - 用户ID格式无效

    Note:
        自动同步模式: 如果 Supabase 用户在本地不存在，自动创建
        这确保了 Supabase 认证用户能无缝使用系统
    """
    # 从数据库查询用户 - 优先使用 email 查询（兼容 SQLite 和 PostgreSQL）
    db_user = None
    if auth_user.email:
        db_user = db.query(User).filter(User.email == auth_user.email).first()

    # 如果 email 查询失败，尝试用 ID 查询（PostgreSQL）
    if not db_user:
        try:
            user_uuid = UUID(str(auth_user.id))
            db_user = db.query(User).filter(User.id == user_uuid).first()
        except (TypeError, ValueError) as e:
            logger.warning(f"UUID conversion failed for {auth_user.id}: {e}")
            # 继续执行，db_user 为 None 会触发自动创建逻辑

    if db_user:
        # 数据库中存在，返回完整User对象
        logger.debug(f"User {auth_user.id} found in database, role: {db_user.role}")
        return db_user

    # 用户在本地数据库不存在，自动创建
    # 这发生在用户通过 Supabase 注册但本地 users 表尚未同步的情况
    logger.info(
        f"User {auth_user.id} not found in database, auto-creating. "
        f"Email: {auth_user.email}, Role: {auth_user.role}"
    )

    try:
        # 尝试转换 UUID
        user_uuid = UUID(str(auth_user.id))
        # 从 Supabase 用户信息创建本地用户记录
        new_user = User(
            id=user_uuid,
            email=auth_user.email or f"{auth_user.id}@placeholder.local",
            username=auth_user.email.split("@")[0] if auth_user.email else str(auth_user.id)[:8],
            role=auth_user.role or "pitcher",  # 默认角色 (使用合法角色)
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"Auto-created user {auth_user.id} with role {new_user.role}")
        return new_user

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to auto-create user {auth_user.id}: {e}")
        raise HTTPException(
            status_code=AuthErrorCodes.USER_NOT_FOUND.status_code,
            detail={
                "code": AuthErrorCodes.USER_NOT_FOUND.code,
                "message": "用户同步失败，请联系管理员"
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
        # 使用本地 JWT 服务验证令牌
        local_auth = LocalAuthService(db)
        user_data = await local_auth.verify_token(credentials.credentials)

        if not user_data:
            raise HTTPException(
                status_code=AuthErrorCodes.TOKEN_INVALID.status_code,
                detail={
                    "code": AuthErrorCodes.TOKEN_INVALID.code,
                    "message": "认证令牌无效"
                }
            )

        # 从本地 JWT 返回的用户数据中提取信息
        user_info = user_data.get("user")
        profile = user_data.get("profile")

        # 创建 AuthenticatedUser 用于转换
        auth_user = AuthenticatedUser(
            id=str(user_info.get("id")),
            role=profile.get("role") if profile else None,
            email=user_info.get("email"),
            raw_claims=user_data.get("raw_claims", {})
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
        # 使用本地 JWT 服务验证令牌
        local_auth = LocalAuthService(db)
        user_data = await local_auth.verify_token(credentials.credentials)

        if not user_data:
            raise HTTPException(
                status_code=AuthErrorCodes.TOKEN_INVALID.status_code,
                detail={
                    "code": AuthErrorCodes.TOKEN_INVALID.code,
                    "message": "认证令牌无效"
                }
            )

        # 从本地 JWT 返回的用户数据中提取信息
        user_info = user_data.get("user")
        profile = user_data.get("profile")

        # 创建 AuthenticatedUser 用于转换
        auth_user = AuthenticatedUser(
            id=str(user_info.get("id")),
            role=profile.get("role") if profile else None,
            email=user_info.get("email"),
            raw_claims=user_data.get("raw_claims", {})
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


# 角色别名映射 (PRD v2.2)
# 数据库存储值 → 业务角色名
ROLE_ALIAS_MAP = {
    "media_buyer": "pitcher",  # 数据库存储 media_buyer，业务层使用 pitcher
    "data_operator": "project_owner",  # 已废弃，映射到 project_owner
}

# 反向映射：业务角色名 → 数据库存储值
ROLE_REVERSE_MAP = {v: k for k, v in ROLE_ALIAS_MAP.items()}


def normalize_role(role: str) -> str:
    """标准化角色名称为业务层角色名

    将数据库存储值转换为业务角色名。
    例如: media_buyer → pitcher

    Args:
        role: 角色字符串（可能是数据库值或业务名）

    Returns:
        标准化后的业务角色名
    """
    return ROLE_ALIAS_MAP.get(role, role)


def require_role(allowed_roles: Union[str, List[str]]):
    """角色权限装饰器 (用于 Depends)

    Args:
        allowed_roles: 允许的角色列表，单个角色可以是字符串
            支持业务角色名（如 pitcher）

    Returns:
        依赖函数

    Usage:
        @router.get("/admin")
        async def admin_endpoint(user: User = Depends(require_role(["admin"]))):
            ...

    Note:
        自动处理角色别名映射 (PRD v2.2):
        - pitcher ↔ media_buyer
        - project_owner ↔ data_operator (已废弃)
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    # 扩展允许角色列表，包含数据库存储值
    expanded_roles = set(allowed_roles)
    for role in allowed_roles:
        # 如果是业务角色名，添加对应的数据库存储值
        if role in ROLE_REVERSE_MAP:
            expanded_roles.add(ROLE_REVERSE_MAP[role])
        # 如果是数据库存储值，添加对应的业务角色名
        if role in ROLE_ALIAS_MAP:
            expanded_roles.add(ROLE_ALIAS_MAP[role])

    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        # 获取用户角色并标准化
        user_role = current_user.role
        if hasattr(user_role, 'value'):
            user_role = user_role.value

        # DEBUG: 输出角色检查详情
        logger.debug(f"Role check: user_role={user_role}, expanded_roles={expanded_roles}, allowed={user_role in expanded_roles}")

        if user_role not in expanded_roles:
            logger.warning(f"Permission denied: user_role={user_role} not in {expanded_roles}")
            raise HTTPException(
                status_code=AuthErrorCodes.PERMISSION_DENIED.status_code,
                detail={
                    "code": AuthErrorCodes.PERMISSION_DENIED.code,
                    "message": f"权限不足，需要角色: {', '.join(allowed_roles)}"
                }
            )
        return current_user

    return role_checker


def check_user_role(user: User, allowed_roles: Union[str, List[str]]) -> None:
    """直接检查用户角色 (用于路由函数内部)

    Args:
        user: 当前用户对象
        allowed_roles: 允许的角色列表，单个角色可以是字符串
            支持业务角色名（如 pitcher）

    Raises:
        HTTPException: 403 - 权限不足

    Usage:
        async def my_endpoint(current_user: User = Depends(get_current_user)):
            check_user_role(current_user, ["admin", "finance"])
            # 继续处理...

    Note:
        自动处理角色别名映射 (PRD v2.2):
        - pitcher ↔ media_buyer
        - project_owner ↔ data_operator (已废弃)
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    # 扩展允许角色列表，包含数据库存储值
    expanded_roles = set(allowed_roles)
    for role in allowed_roles:
        if role in ROLE_REVERSE_MAP:
            expanded_roles.add(ROLE_REVERSE_MAP[role])
        if role in ROLE_ALIAS_MAP:
            expanded_roles.add(ROLE_ALIAS_MAP[role])

    # 获取用户角色
    user_role = user.role
    if hasattr(user_role, 'value'):
        user_role = user_role.value

    if user_role not in expanded_roles:
        raise HTTPException(
            status_code=AuthErrorCodes.PERMISSION_DENIED.status_code,
            detail={
                "code": AuthErrorCodes.PERMISSION_DENIED.code,
                "message": f"权限不足，需要角色: {', '.join(allowed_roles)}"
            }
        )


def require_admin():
    """需要管理员权限"""
    return require_role("admin")


def require_finance():
    """需要财务权限"""
    return require_role(["admin", "finance"])


def require_project_owner():
    """需要项目负责人权限"""
    return require_role(["admin", "ceo", "project_owner"])


def require_account_manager():
    """需要户管权限"""
    return require_role(["admin", "account_manager"])


def require_pitcher():
    """需要投手权限"""
    return require_role(["admin", "pitcher"])


# 角色权限映射 (SoT 6 角色)
ROLE_PERMISSIONS = {
    "admin": ["*"],  # 管理员拥有所有权限
    "ceo": ["*"],  # CEO 拥有所有权限
    "finance": [
        "finance:read", "finance:create", "finance:update",
        "topup:approve", "topup:confirm", "reconciliation:manage"
    ],
    "project_owner": [
        "project:read", "project:update",
        "account:read", "account:assign",
        "report:submit", "report:review",
        "topup:request"
    ],
    "account_manager": [
        "account:create", "account:read", "account:update",
        "channel:read", "channel:apply"
    ],
    "pitcher": [
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
