"""
项目管理API路由（完整版）
Version: 1.0
Author: Claude协作开发
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user, require_role
from core.response import (
    success_response,
    error_response,
    StandardResponse
)
from exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError
)
from models.user import User
from models.project import Project, ProjectMember, ProjectExpense
from schemas.project import (
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
from services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    """获取项目服务实例"""
    return ProjectService(db)


@router.get(
    "",
    response_model=StandardResponse[ProjectListResponse],
    summary="获取项目列表"
)
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
            ProjectResponse.model_validate(project)
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
            code="SYS_500",
            message="获取项目列表失败",
            status_code=500
        )


@router.post(
    "",
    response_model=StandardResponse[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建项目"
)
@require_role(["admin"])
async def create_project(
    request: ProjectCreateRequest,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """创建项目API"""
    try:
        project = service.create_project(request, current_user)
        project_response = ProjectResponse.model_validate(project)

        return success_response(
            data=project_response,
            message="项目创建成功",
            status_code=201
        )

    except (ResourceConflictError, BusinessLogicError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "BIZ_ERROR",
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
    "/{project_id}",
    response_model=StandardResponse[ProjectResponse],
    summary="获取项目详情"
)
async def get_project(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """获取项目详情API"""
    try:
        project = service.get_project(project_id, current_user)
        project_response = ProjectResponse.model_validate(project)

        return success_response(data=project_response)

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS_004",
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
    response_model=StandardResponse[ProjectResponse],
    summary="更新项目"
)
@require_role(["admin", "account_manager"])
async def update_project(
    project_id: int,
    request: ProjectUpdateRequest,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """更新项目API"""
    try:
        project = service.update_project(project_id, request, current_user)
        project_response = ProjectResponse.model_validate(project)

        return success_response(
            data=project_response,
            message="项目更新成功"
        )

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS_004",
            message=str(e),
            status_code=404
        )
    except (ResourceConflictError, BusinessLogicError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "BIZ_ERROR",
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
@require_role(["admin"])
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
            code="SYS_004",
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
            code=str(e.error_code) if hasattr(e, 'error_code') else "BIZ_ERROR",
            message=str(e),
            status_code=400
        )


@router.post(
    "/{project_id}/members",
    response_model=StandardResponse[ProjectMemberResponse],
    summary="分配项目成员"
)
@require_role(["admin", "account_manager"])
async def assign_member(
    project_id: int,
    request: ProjectMemberAssignRequest,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """分配项目成员API"""
    try:
        member = service.assign_member(project_id, request, current_user)
        member_response = ProjectMemberResponse.model_validate(member)

        return success_response(
            data=member_response,
            message="成员分配成功"
        )

    except (ResourceNotFoundError, ResourceConflictError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "BIZ_ERROR",
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
    response_model=StandardResponse[List[ProjectMemberResponse]],
    summary="获取项目成员列表"
)
async def get_project_members(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """获取项目成员列表API"""
    try:
        members = service.get_project_members(project_id, current_user)
        member_responses = [
            ProjectMemberResponse.model_validate(member)
            for member in members
        ]

        return success_response(
            data=member_responses,
            message="获取项目成员列表成功"
        )

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS_004",
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
@require_role(["admin", "account_manager"])
async def remove_member(
    project_id: int,
    user_id: int,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """移除项目成员API"""
    try:
        service.remove_member(project_id, user_id, current_user)
        return None

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS_004",
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
    response_model=StandardResponse[ProjectExpenseResponse],
    summary="添加项目费用"
)
@require_role(["admin", "account_manager"])
async def add_expense(
    project_id: int,
    request: ProjectExpenseRequest,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """添加项目费用API"""
    try:
        expense = service.add_expense(project_id, request, current_user)
        expense_response = ProjectExpenseResponse.model_validate(expense)

        return success_response(
            data=expense_response,
            message="费用添加成功"
        )

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS_004",
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
    response_model=StandardResponse[dict],
    summary="获取项目费用列表"
)
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
            ProjectExpenseResponse.model_validate(expense)
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
            code="SYS_004",
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
    "/statistics",
    response_model=StandardResponse[ProjectStatisticsResponse],
    summary="获取项目统计"
)
@require_role(["admin", "finance", "data_operator"])
async def get_project_statistics(
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """获取项目统计API"""
    try:
        stats = service.get_project_statistics(current_user)
        stats_response = ProjectStatisticsResponse.model_validate(stats)

        return success_response(data=stats_response)

    except Exception as e:
        return error_response(
            code="SYS_500",
            message="获取统计信息失败",
            status_code=500
        )