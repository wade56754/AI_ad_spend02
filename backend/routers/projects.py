"""
项目管理API路由（完整版）
Version: 1.0
Author: Claude协作开发
"""

from typing import List, Optional
import structlog

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.dependencies import get_current_user, require_role
from backend.core.logging import log_requests
from backend.core.response import (
    success_response,
    error_response,
    StandardResponse
)
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError
)
from backend.models import User
from backend.models import Project, ProjectMember, ProjectExpense
from backend.schemas.project import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    ProjectListResponse,
    ProjectMemberResponse,
    ProjectExpenseRequest,
    ProjectExpenseResponse,
    ProjectStatisticsResponse,
    ProjectMemberAssignRequest
)
from backend.services.project_service import ProjectService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/projects", tags=["projects"])


def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    """获取项目服务实例"""
    return ProjectService(db)


def build_project_expense_response(expense) -> ProjectExpenseResponse:
    """
    构建 ProjectExpenseResponse，处理 ORM 模型到 Pydantic schema 的转换
    
    处理：
    - created_by_name: 通过 creator 关系获取（如果存在），否则使用默认值
    """
    # 获取 created_by_name
    created_by_name = None
    if hasattr(expense, 'creator') and expense.creator:
        # 如果存在 creator 关系
        created_by_name = getattr(expense.creator, 'email', None) or getattr(expense.creator, 'username', None)
    # 注意：ProjectExpense 模型可能没有定义 creator 关系，所以这里使用默认值
    # 如果 service 层需要提供 created_by_name，应该在 service 层处理
    
    # 构建响应数据
    response_data = {
        "id": expense.id,
        "expense_type": expense.expense_type,
        "amount": expense.amount,
        "description": expense.description,
        "expense_date": expense.expense_date,
        "created_by_name": created_by_name or "系统",  # 如果无法获取，使用默认值
        "created_at": expense.created_at,
    }
    
    return ProjectExpenseResponse(**response_data)


def build_project_member_response(member: ProjectMember) -> ProjectMemberResponse:
    """
    构建 ProjectMemberResponse，处理 ORM 模型到 Pydantic schema 的转换

    处理：
    - user_id: UUID → int (使用 hash 或转换为整数表示)
    - user_name: 从 member.user 关系获取
    - user_email: 从 member.user 关系获取
    - user_role: 从 member.user.role 获取 (用户全局角色)
    - project_role: 从 member.role 获取 (项目内角色)
    - joined_at: 从 member.created_at 获取
    """
    from uuid import UUID

    # 获取用户信息
    user = getattr(member, 'user', None)

    # 处理 user_id: ProjectMemberResponse.user_id 期望 str (UUID 字符串)
    # 由于 member.user_id 是 UUID，我们需要转换为字符串
    user_id_value = ""
    if member.user_id:
        if isinstance(member.user_id, UUID):
            user_id_value = str(member.user_id)
        elif isinstance(member.user_id, str):
            user_id_value = member.user_id
        else:
            # 如果是其他类型，尝试转换为字符串
            user_id_value = str(member.user_id)

    # 获取用户名称
    user_name = ""
    if user:
        user_name = getattr(user, 'username', None) or getattr(user, 'email', "") or ""

    # 获取用户邮箱
    user_email = ""
    if user:
        user_email = getattr(user, 'email', "") or ""

    # 获取用户全局角色
    user_role = ""
    if user:
        role_val = getattr(user, 'role', None)
        if role_val:
            # role 可能是 Enum 或 str
            user_role = role_val.value if hasattr(role_val, 'value') else str(role_val)

    # 获取项目角色
    project_role = getattr(member, 'role', '') or ''

    # 获取加入时间
    joined_at = getattr(member, 'created_at', None)
    if joined_at is None:
        from datetime import datetime
        joined_at = datetime.now()

    response_data = {
        "id": member.id,
        "user_id": user_id_value,
        "user_name": user_name,
        "user_email": user_email,
        "user_role": user_role,
        "project_role": project_role,
        "joined_at": joined_at,
    }

    return ProjectMemberResponse(**response_data)


def build_project_response(project: Project) -> ProjectResponse:
    """
    构建 ProjectResponse，处理 ORM 模型到 Pydantic schema 的转换
    
    处理：
    - created_by: UUID → 处理（ProjectResponse.created_by 期望 int，但 Project.created_by 是 UUID）
    - account_manager_name: 通过 account_manager 关系获取
    - created_by_name: 通过 creator 关系获取
    - client_company / budget: 处理 None 值
    """
    from decimal import Decimal
    from uuid import UUID
    
    # 获取 account_manager_name
    account_manager_name = None
    if hasattr(project, 'account_manager') and project.account_manager:
        # User 模型可能没有 name 字段，使用 email 或其他可用字段
        account_manager_name = getattr(project.account_manager, 'email', None) or getattr(project.account_manager, 'username', None)
    
    # 获取 created_by_name
    created_by_name = None
    if hasattr(project, 'creator') and project.creator:
        # User 模型可能没有 name 字段，使用 email 或其他可用字段
        created_by_name = getattr(project.creator, 'email', None) or getattr(project.creator, 'username', None)
    
    # 处理 created_by: Project.created_by 是 UUID，ProjectResponse.created_by 已修改为 Optional[str]
    created_by_value = None
    if hasattr(project, 'created_by') and project.created_by:
        if isinstance(project.created_by, UUID):
            created_by_value = str(project.created_by)  # UUID 转换为字符串
        elif isinstance(project.created_by, str):
            created_by_value = project.created_by
        elif isinstance(project.created_by, int):
            created_by_value = str(project.created_by)  # int 也转换为字符串以保持一致性
        else:
            created_by_value = None
    
    # 构建响应数据
    response_data = {
        "id": project.id,
        "name": project.name,
        "client_name": project.client_name or "",
        "client_company": project.client_company or "",  # 处理 None
        "description": project.description,
        "status": project.status,
        "budget": project.budget if project.budget is not None else Decimal('0.00'),  # 处理 None
        "currency": project.currency or "USD",
        "start_date": project.start_date,
        "end_date": project.end_date,
        "account_manager_id": project.account_manager_id,
        "account_manager_name": account_manager_name or "",
        "total_spent": getattr(project, 'total_spent', Decimal('0.00')),
        "total_accounts": getattr(project, 'total_accounts', 0),
        "active_accounts": getattr(project, 'active_accounts', 0),
        "created_by": created_by_value,
        "created_by_name": created_by_name or "",
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }
    
    return ProjectResponse(**response_data)


@router.get(
    "",
    summary="获取项目列表"
)
@log_requests("projects")
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    manager_id: Optional[int] = Query(None),
    client_name: Optional[str] = Query(None),
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """获取项目列表API"""
    try:
        projects, total = service.get_projects(
            current_user=current_user,
            page=page,
            page_size=page_size,
            status=status,
            manager_id=manager_id,
            client_name=client_name
        )

        # 转换为响应格式
        project_responses = [
            build_project_response(project)
            for project in projects
        ]

        # 构建分页元数据
        meta = {
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }

        return success_response(
            data={"items": project_responses, "meta": meta},
            message="获取项目列表成功"
        )

    except Exception as e:
        return error_response(
            code="SYS-500",
            message="获取项目列表失败",
            status_code=500
        )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="创建项目"
)
@log_requests("projects")
# # @require_role(["admin"])
async def create_project(
    request: ProjectCreateRequest,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """创建项目API"""
    try:
        project = service.create_project(request, current_user)
        project_response = build_project_response(project)

        return success_response(
            data=project_response,
            message="项目创建成功",
            status_code=201
        )

    except (ResourceConflictError, BusinessLogicError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "BIZ_001",
            message=str(e),
            status_code=400
        )
    except PermissionDeniedError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "PERMISSION_DENIED",
            message=str(e),
            status_code=403
        )


@router.get(
    "/statistics",
    summary="获取项目统计"
)
@log_requests("projects")
async def get_project_statistics(
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """获取项目统计API"""
    try:
        stats = service.get_project_statistics(current_user)
        stats_response = ProjectStatisticsResponse.model_validate(stats)

        return success_response(data=stats_response)

    except PermissionDeniedError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "AUTH_500",
            message=str(e),
            status_code=403
        )
    except Exception as e:
        return error_response(
            code="SYS-500",
            message="获取统计信息失败",
            status_code=500
        )


@router.get(
    "/{project_id}",
    summary="获取项目详情"
)
@log_requests("projects")
async def get_project(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """获取项目详情API"""
    try:
        project = service.get_project(project_id, current_user)
        project_response = build_project_response(project)

        return success_response(data=project_response)

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS-004",
            message=str(e),
            status_code=404
        )
    except PermissionDeniedError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "PERMISSION_DENIED",
            message=str(e),
            status_code=403
        )


@router.put(
    "/{project_id}",
    summary="更新项目"
)
@log_requests("projects")
# @require_role(["admin", "account_manager"])
async def update_project(
    project_id: int,
    request: ProjectUpdateRequest,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """更新项目API"""
    try:
        project = service.update_project(project_id, request, current_user)
        project_response = build_project_response(project)

        return success_response(
            data=project_response,
            message="项目更新成功"
        )

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS-004",
            message=str(e),
            status_code=404
        )
    except (ResourceConflictError, BusinessLogicError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "BIZ_001",
            message=str(e),
            status_code=400
        )
    except PermissionDeniedError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "PERMISSION_DENIED",
            message=str(e),
            status_code=403
        )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除项目"
)
@log_requests("projects")
# @require_role(["admin"])
async def delete_project(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """删除项目API"""
    try:
        service.delete_project(project_id, current_user)
        return None

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS-004",
            message=str(e),
            status_code=404
        )
    except PermissionDeniedError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "PERMISSION_DENIED",
            message=str(e),
            status_code=403
        )
    except BusinessLogicError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "BIZ_001",
            message=str(e),
            status_code=400
        )


@router.post(
    "/{project_id}/members",
    summary="分配项目成员"
)
@log_requests("projects")
# @require_role(["admin", "account_manager"])
async def assign_member(
    project_id: int,
    request: ProjectMemberAssignRequest,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """分配项目成员API"""
    try:
        member = service.assign_member(project_id, request, current_user)
        member_response = build_project_member_response(member)

        return success_response(
            data=member_response,
            message="成员分配成功"
        )

    except (ResourceNotFoundError, ResourceConflictError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "BIZ_001",
            message=str(e),
            status_code=400
        )
    except PermissionDeniedError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "PERMISSION_DENIED",
            message=str(e),
            status_code=403
        )


@router.get(
    "/{project_id}/members",
    summary="获取项目成员列表"
)
@log_requests("projects")
async def get_project_members(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """获取项目成员列表API"""
    try:
        members = service.get_project_members(project_id, current_user)
        member_responses = [
            build_project_member_response(member)
            for member in members
        ]

        return success_response(
            data=member_responses,
            message="获取项目成员列表成功"
        )

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS-004",
            message=str(e),
            status_code=404
        )
    except PermissionDeniedError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "PERMISSION_DENIED",
            message=str(e),
            status_code=403
        )


@router.delete(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="移除项目成员"
)
@log_requests("projects")
# @require_role(["admin", "account_manager"])
async def remove_member(
    project_id: int,
    user_id: str = Path(..., description="用户ID（UUID 字符串）"),  # 接受 UUID 字符串
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """移除项目成员API"""
    try:
        # service.remove_member 现在接受 UUID 对象或 UUID 字符串
        service.remove_member(project_id, user_id, current_user)
        # 成功删除返回 204 No Content
        from fastapi.responses import Response
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS-004",
            message=str(e),
            status_code=404
        )
    except PermissionDeniedError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "PERMISSION_DENIED",
            message=str(e),
            status_code=403
        )


@router.post(
    "/{project_id}/expenses",
    summary="添加项目费用"
)
@log_requests("projects")
# @require_role(["admin", "account_manager"])
async def add_expense(
    project_id: int,
    request: ProjectExpenseRequest,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """添加项目费用API"""
    try:
        expense = service.add_expense(project_id, request, current_user)
        expense_response = build_project_expense_response(expense)

        return success_response(
            data=expense_response,
            message="费用添加成功"
        )

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS-004",
            message=str(e),
            status_code=404
        )
    except PermissionDeniedError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "PERMISSION_DENIED",
            message=str(e),
            status_code=403
        )


@router.get(
    "/{project_id}/expenses",
    summary="获取项目费用列表"
)
@log_requests("projects")
async def get_project_expenses(
    project_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """获取项目费用列表API"""
    try:
        expenses, total = service.get_project_expenses(
            project_id,
            current_user,
            page,
            page_size
        )

        # 转换为响应格式
        expense_responses = [
            build_project_expense_response(expense)
            for expense in expenses
        ]

        meta = {
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }

        return success_response(
            data={"items": expense_responses, "meta": meta},
            message="获取费用列表成功"
        )

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS-004",
            message=str(e),
            status_code=404
        )
    except PermissionDeniedError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "PERMISSION_DENIED",
            message=str(e),
            status_code=403
        )


