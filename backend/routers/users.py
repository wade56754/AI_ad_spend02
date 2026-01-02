"""
用户管理路由 (重构版)

SoT References:
- API_SOT.md v9.3 §5 Users API
- DATA_SCHEMA.md v5.3 §3.1.1 users 表
- MASTER.md v4.8 §2.4 (6角色模型)
- ERROR_CODES_SOT.md v2.1 (错误码)

端点列表:
- GET    /users                    - 获取用户列表
- POST   /users                    - 创建用户
- GET    /users/statistics/summary - 获取用户统计
- GET    /users/{user_id}          - 获取用户详情
- PUT    /users/{user_id}          - 更新用户
- DELETE /users/{user_id}          - 删除用户

权限矩阵 (MASTER.md v4.8 §2.4 - 6角色模型):
- admin: 用户 CRUD
- ceo, finance, project_owner: 查看用户列表和统计
- 其他角色: 仅查看自己

依赖代码块:
- response-envelope: success_response, error_response
- pagination: 分页查询
- permission-filter: require_role
- error-codes: PERM-001, RES-001, BIZ-001, BIZ-002, SYS-500

Version: 2.0
Author: Claude Code
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.dependencies import get_current_user, require_role
from backend.core.response import success_response, error_response
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError,
    ValidationError,
)
from backend.models import User
from backend.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    VALID_ROLES,
)
from backend.services.user_service import UserService, get_user_service

logger = logging.getLogger(__name__)


# ========================================
# 错误响应辅助函数
# ========================================


def _handle_service_exception(e: Exception, context: str = "操作"):
    """处理服务层异常，转换为标准响应"""
    if isinstance(e, PermissionDeniedError):
        return error_response(code="PERM-001", message=str(e), status_code=403)
    elif isinstance(e, ResourceNotFoundError):
        return error_response(code="RES-001", message=str(e), status_code=404)
    elif isinstance(e, ResourceConflictError):
        return error_response(code="BIZ-002", message=str(e), status_code=409)
    elif isinstance(e, ValidationError):
        return error_response(code="VAL-001", message=str(e), status_code=400)
    elif isinstance(e, BusinessLogicError):
        return error_response(code="BIZ-001", message=str(e), status_code=400)
    else:
        logger.exception(f"服务异常 - {context}: {e}")
        return error_response(
            code="SYS-500", message=f"系统内部错误: {str(e)}", status_code=500
        )


router = APIRouter(prefix="/users", tags=["用户管理"])


def get_service(db: Session = Depends(get_db)) -> UserService:
    """获取用户服务实例"""
    return UserService(db)


@router.get("", response_model=dict)
async def get_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    role: Optional[str] = Query(None, description="角色过滤"),
    is_active: Optional[bool] = Query(None, description="账号状态过滤"),
    search: Optional[str] = Query(None, max_length=100, description="搜索用户名或邮箱"),
    current_user: User = Depends(require_role(["admin"])),
    service: UserService = Depends(get_service),
):
    """
    获取用户列表

    权限 (MASTER.md v4.8 §2.4): admin

    Query Parameters:
    - page: 页码 (默认 1)
    - page_size: 每页数量 (默认 20, 最大 100)
    - role: 角色过滤 (可选)
    - is_active: 状态过滤 (可选)
    - search: 搜索关键词 (可选)

    Response:
    - 200: 成功返回用户列表
    - 403 (PERM-001): 权限不足
    - 400 (VAL-001): 参数无效
    """
    try:
        users, total, meta = service.get_users(
            current_user=current_user,
            page=page,
            page_size=page_size,
            role=role,
            is_active=is_active,
            search=search,
        )

        # 转换为响应格式
        items = [
            UserListResponse(
                id=user.id,
                username=user.username,
                full_name=getattr(user, "full_name", None),
                email=user.email,
                role=user.role,
                department=getattr(user, "department", None),
                is_active=user.is_active,
                created_at=user.created_at,
            ).model_dump()
            for user in users
        ]

        return success_response(data={"items": items, "meta": meta}, message="查询成功")
    except Exception as e:
        return _handle_service_exception(e, "获取用户列表")


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_role(["admin"])),
    service: UserService = Depends(get_service),
):
    """
    创建用户

    权限 (MASTER.md v4.8 §2.4): admin

    Request Body:
    - username: 用户名 (必填, 2-50 字符)
    - email: 邮箱 (必填)
    - password: 密码 (必填, 最少 8 位)
    - role: 角色 (必填, 6 角色之一)
    - full_name: 真实姓名 (可选)
    - department: 部门 (可选)
    - is_active: 是否激活 (默认 true)

    Response:
    - 201: 创建成功
    - 403 (PERM-001): 权限不足
    - 409 (BIZ-002): 用户名或邮箱已存在
    """
    try:
        user = service.create_user(user_data=user_data, current_user=current_user)

        return success_response(
            data=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=getattr(user, "full_name", None),
                role=user.role,
                department=getattr(user, "department", None),
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=getattr(user, "updated_at", None),
            ).model_dump(),
            message="用户创建成功",
        )
    except Exception as e:
        return _handle_service_exception(e, "创建用户")


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_service),
):
    """
    获取用户详情

    权限 (MASTER.md v4.8 §2.4): admin 可查看任意用户，其他用户只能查看自己

    Path Parameters:
    - user_id: 用户 UUID

    Response:
    - 200: 成功返回用户详情
    - 403 (PERM-001): 权限不足
    - 404 (RES-001): 用户不存在
    """
    try:
        user = service.get_user_by_id(user_id=user_id, current_user=current_user)

        return success_response(
            data=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=getattr(user, "full_name", None),
                role=user.role,
                department=getattr(user, "department", None),
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=getattr(user, "updated_at", None),
            ).model_dump(),
            message="查询成功",
        )
    except Exception as e:
        return _handle_service_exception(e, "获取用户详情")


@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: User = Depends(require_role(["admin"])),
    service: UserService = Depends(get_service),
):
    """
    更新用户信息

    权限 (MASTER.md v4.8 §2.4): admin

    Path Parameters:
    - user_id: 用户 UUID

    Request Body (所有字段可选):
    - username: 用户名
    - email: 邮箱
    - password: 新密码
    - role: 角色
    - full_name: 真实姓名
    - department: 部门
    - is_active: 是否激活

    Response:
    - 200: 更新成功
    - 403 (PERM-001): 权限不足
    - 404 (RES-001): 用户不存在
    - 409 (BIZ-002): 用户名或邮箱已存在
    """
    try:
        user = service.update_user(
            user_id=user_id, user_data=user_data, current_user=current_user
        )

        return success_response(
            data=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=getattr(user, "full_name", None),
                role=user.role,
                department=getattr(user, "department", None),
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=getattr(user, "updated_at", None),
            ).model_dump(),
            message="用户更新成功",
        )
    except Exception as e:
        return _handle_service_exception(e, "更新用户")


@router.delete("/{user_id}", response_model=dict)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_role(["admin"])),
    service: UserService = Depends(get_service),
):
    """
    删除用户（软删除）

    权限 (MASTER.md v4.8 §2.4): admin
    约束: 不能删除自己

    Path Parameters:
    - user_id: 用户 UUID

    Response:
    - 200: 删除成功
    - 403 (PERM-001): 权限不足或尝试删除自己
    - 404 (RES-001): 用户不存在
    """
    try:
        service.delete_user(user_id=user_id, current_user=current_user)

        return success_response(data={"user_id": str(user_id)}, message="用户删除成功")
    except Exception as e:
        return _handle_service_exception(e, "删除用户")


@router.get("/statistics/summary", response_model=dict)
async def get_user_statistics(
    current_user: User = Depends(
        require_role(["admin", "ceo", "finance", "project_owner"])
    ),
    service: UserService = Depends(get_service),
):
    """
    获取用户统计信息

    权限 (MASTER.md v4.8 §2.4): admin, ceo, finance, project_owner

    Response:
    - 200: 返回统计数据
    - 403 (PERM-001): 权限不足
    """
    try:
        stats = service.get_user_statistics(current_user=current_user)

        return success_response(data=stats, message="查询成功")
    except Exception as e:
        return _handle_service_exception(e, "获取用户统计")
