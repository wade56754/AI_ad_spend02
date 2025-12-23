"""
用户管理路由

SoT References:
- API_SOT.md v9.0 §5 Users API
- DATA_SCHEMA.md v5.2 §3.1.1 users 表
- ERROR_CODES_SOT.md v2.1

端点:
- GET  /api/v1/users           - 获取用户列表 (admin)
- POST /api/v1/users           - 创建用户 (admin)
- GET  /api/v1/users/{user_id} - 获取用户详情 (admin/self)
- PUT  /api/v1/users/{user_id} - 更新用户 (admin)
- DELETE /api/v1/users/{user_id} - 删除用户 (admin)

Author: AI 代码工厂 v2.4
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.dependencies import get_current_user, require_role
from backend.core.response import success_response, paginated_response
from backend.models import User
from backend.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    VALID_ROLES
)
from backend.services.user_service import UserService, get_user_service


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
    service: UserService = Depends(get_service)
):
    """
    获取用户列表

    权限: admin

    Query Parameters:
    - page: 页码 (默认 1)
    - page_size: 每页数量 (默认 20, 最大 100)
    - role: 角色过滤 (可选)
    - is_active: 状态过滤 (可选)
    - search: 搜索关键词 (可选)

    Response:
    - 200: 成功返回用户列表
    - 403 (AUTH_500): 非 admin 角色访问
    - 400 (VALIDATION_002): role 参数无效
    """
    users, total, meta = service.get_users(
        current_user=current_user,
        page=page,
        page_size=page_size,
        role=role,
        is_active=is_active,
        search=search
    )

    # 转换为响应格式
    items = [
        UserListResponse(
            id=user.id,
            username=user.username,
            full_name=getattr(user, 'full_name', None),
            email=user.email,
            role=user.role,
            department=getattr(user, 'department', None),
            is_active=user.is_active,
            created_at=user.created_at
        ).model_dump()
        for user in users
    ]

    return success_response(
        data={
            "items": items,
            "meta": meta
        },
        message="查询成功"
    )


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_role(["admin"])),
    service: UserService = Depends(get_service)
):
    """
    创建用户

    权限: admin

    Request Body:
    - username: 用户名 (必填, 2-50 字符)
    - email: 邮箱 (必填)
    - password: 密码 (必填, 最少 8 位)
    - role: 角色 (必填, 5 个合法值之一)
    - full_name: 真实姓名 (可选)
    - department: 部门 (可选)
    - is_active: 是否激活 (默认 true)

    Response:
    - 201: 创建成功
    - 403 (AUTH_500): 非 admin 角色
    - 409 (DB_004): 用户名或邮箱已存在
    """
    user = service.create_user(
        user_data=user_data,
        current_user=current_user
    )

    return success_response(
        data=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=getattr(user, 'full_name', None),
            role=user.role,
            department=getattr(user, 'department', None),
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=getattr(user, 'updated_at', None)
        ).model_dump(),
        message="用户创建成功"
    )


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_service)
):
    """
    获取用户详情

    权限: admin 可查看任意用户，其他用户只能查看自己

    Path Parameters:
    - user_id: 用户 UUID

    Response:
    - 200: 成功返回用户详情
    - 403 (AUTH_500): 无权限访问
    - 404 (BIZ_002): 用户不存在
    """
    user = service.get_user_by_id(
        user_id=user_id,
        current_user=current_user
    )

    return success_response(
        data=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=getattr(user, 'full_name', None),
            role=user.role,
            department=getattr(user, 'department', None),
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=getattr(user, 'updated_at', None)
        ).model_dump(),
        message="查询成功"
    )


@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: User = Depends(require_role(["admin"])),
    service: UserService = Depends(get_service)
):
    """
    更新用户信息

    权限: admin

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
    - 403 (AUTH_500): 非 admin 角色
    - 404 (BIZ_002): 用户不存在
    - 409 (DB_004): 用户名或邮箱已存在
    """
    user = service.update_user(
        user_id=user_id,
        user_data=user_data,
        current_user=current_user
    )

    return success_response(
        data=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=getattr(user, 'full_name', None),
            role=user.role,
            department=getattr(user, 'department', None),
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=getattr(user, 'updated_at', None)
        ).model_dump(),
        message="用户更新成功"
    )


@router.delete("/{user_id}", response_model=dict)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_role(["admin"])),
    service: UserService = Depends(get_service)
):
    """
    删除用户（软删除）

    权限: admin
    约束: 不能删除自己

    Path Parameters:
    - user_id: 用户 UUID

    Response:
    - 200: 删除成功
    - 403 (AUTH_500): 非 admin 角色或尝试删除自己
    - 404 (BIZ_002): 用户不存在
    """
    service.delete_user(
        user_id=user_id,
        current_user=current_user
    )

    return success_response(
        data={"user_id": str(user_id)},
        message="用户删除成功"
    )


@router.get("/statistics/summary", response_model=dict)
async def get_user_statistics(
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"])),
    service: UserService = Depends(get_service)
):
    """
    获取用户统计信息

    权限: admin, finance, data_operator

    Response:
    - 200: 返回统计数据
    - 403 (AUTH_500): 权限不足
    """
    stats = service.get_user_statistics(current_user=current_user)

    return success_response(
        data=stats,
        message="查询成功"
    )
