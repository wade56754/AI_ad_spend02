"""
项目管理API路由 (重构版)

SoT Reference: API_SOT.md v9.3 §6 (Projects API)
SoT Reference: STATE_MACHINE.md v2.6 §5 (项目状态机)

依赖代码块:
- response-envelope: success_response, error_response
- pagination: get_pagination, create_paginated_response
- error-codes: BusinessErrorCodes

Version: 2.0
"""

from typing import Optional
from decimal import Decimal
from uuid import UUID
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, Query, Path, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.dependencies import get_current_user
from backend.core.logging import log_requests
from backend.core.response import success_response, error_response
from backend.core.pagination import get_pagination, PaginationParams, create_paginated_response
from backend.core.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError,
    BusinessError,
    PermissionError,
)
from backend.models import User, Project, ProjectMember
from backend.schemas.project import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    ProjectMemberResponse,
    ProjectExpenseRequest,
    ProjectExpenseResponse,
    ProjectStatisticsResponse,
    ProjectMemberAssignRequest,
    ProjectMarkFulfilledRequest,
)
from backend.services.project_service import ProjectService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/projects", tags=["projects"])


def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    """获取项目服务实例"""
    return ProjectService(db)


# ========================================
# Response Builders (ORM → Pydantic)
# ========================================

def build_project_response(project: Project) -> ProjectResponse:
    """构建项目响应"""
    # 获取 account_manager_name
    account_manager_name = None
    if hasattr(project, 'account_manager') and project.account_manager:
        account_manager_name = getattr(project.account_manager, 'email', None) or \
                               getattr(project.account_manager, 'username', None)

    # 获取 created_by_name
    created_by_name = None
    if hasattr(project, 'creator') and project.creator:
        created_by_name = getattr(project.creator, 'email', None) or \
                          getattr(project.creator, 'username', None)

    # 处理 created_by (UUID → str)
    created_by_value = None
    if hasattr(project, 'created_by') and project.created_by:
        if isinstance(project.created_by, UUID):
            created_by_value = str(project.created_by)
        else:
            created_by_value = str(project.created_by) if project.created_by else None

    return ProjectResponse(
        id=project.id,
        name=project.name,
        client_name=project.client_name or "",
        client_company=project.client_company or "",
        description=project.description,
        status=project.status,
        budget=project.budget if project.budget is not None else Decimal('0.00'),
        currency=project.currency or "CNY",
        start_date=project.start_date,
        end_date=project.end_date,
        account_manager_id=project.account_manager_id,
        account_manager_name=account_manager_name or "",
        # 新增字段
        region=getattr(project, 'region', None),
        unit_price=getattr(project, 'unit_price', None),
        total_follows=getattr(project, 'total_follows', 0),
        # 履约状态字段 (BUSINESS_RULES.md v4.6 BR-PROJ-006)
        fulfillment_status=getattr(project, 'fulfillment_status', 'running'),
        fulfillment_reason=getattr(project, 'fulfillment_reason', None),
        fulfilled_at=getattr(project, 'fulfilled_at', None),
        # 原有字段
        total_spent=getattr(project, 'total_spent', Decimal('0.00')),
        total_accounts=getattr(project, 'total_accounts', 0),
        active_accounts=getattr(project, 'active_accounts', 0),
        created_by=created_by_value,
        created_by_name=created_by_name or "",
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def build_project_member_response(member: ProjectMember) -> ProjectMemberResponse:
    """构建项目成员响应"""
    user = getattr(member, 'user', None)

    # user_id: UUID → str
    user_id_value = ""
    if member.user_id:
        user_id_value = str(member.user_id)

    # 用户信息
    user_name = ""
    user_email = ""
    user_role = ""
    if user:
        user_name = getattr(user, 'username', None) or getattr(user, 'email', "") or ""
        user_email = getattr(user, 'email', "") or ""
        role_val = getattr(user, 'role', None)
        if role_val:
            user_role = role_val.value if hasattr(role_val, 'value') else str(role_val)

    project_role = getattr(member, 'role', '') or ''
    joined_at = getattr(member, 'created_at', None) or datetime.now()

    return ProjectMemberResponse(
        id=member.id,
        user_id=user_id_value,
        user_name=user_name,
        user_email=user_email,
        user_role=user_role,
        project_role=project_role,
        joined_at=joined_at,
    )


def build_project_expense_response(expense) -> ProjectExpenseResponse:
    """构建项目费用响应"""
    created_by_name = None
    if hasattr(expense, 'creator') and expense.creator:
        created_by_name = getattr(expense.creator, 'email', None) or \
                          getattr(expense.creator, 'username', None)

    return ProjectExpenseResponse(
        id=expense.id,
        expense_type=expense.expense_type,
        amount=expense.amount,
        description=expense.description,
        expense_date=expense.expense_date,
        created_by_name=created_by_name or "系统",
        created_at=expense.created_at,
    )


# ========================================
# 项目 CRUD
# ========================================

@router.get(
    "",
    summary="获取项目列表",
    description="支持分页、状态筛选、客户名称筛选。权限过滤自动应用。"
)
@log_requests("projects")
async def list_projects(
    status: Optional[str] = Query(None, description="状态筛选: draft/active/suspended/archived"),
    client_name: Optional[str] = Query(None, description="客户名称模糊搜索"),
    pagination: PaginationParams = Depends(get_pagination),
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """获取项目列表 (带分页和权限过滤)"""
    try:
        projects, total = service.get_projects(
            current_user=current_user,
            pagination=pagination,
            status=status,
            client_name=client_name
        )

        # 转换为响应格式
        project_responses = [build_project_response(p) for p in projects]

        # 使用标准分页响应
        return create_paginated_response(
            items=project_responses,
            total=total,
            pagination=pagination,
            message="获取项目列表成功"
        )

    except Exception as e:
        logger.error("list_projects_error", error=str(e))
        return error_response(
            code="SYS-500",
            message="获取项目列表失败",
            status_code=500
        )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="创建项目",
    description="创建新项目。初始状态: draft。权限: admin, account_manager"
)
@log_requests("projects")
async def create_project(
    request: ProjectCreateRequest,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """创建项目"""
    try:
        project = service.create_project(request, current_user)
        return success_response(
            data=build_project_response(project),
            message="项目创建成功",
            status_code=201
        )

    except ConflictError as e:
        return error_response(code="RES-002", message=str(e), status_code=409)
    except ValidationError as e:
        return error_response(code="VAL-001", message=str(e), status_code=400)
    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)
    except Exception as e:
        logger.error("create_project_error", error=str(e))
        return error_response(code="SYS-500", message="创建项目失败", status_code=500)


@router.get(
    "/statistics",
    summary="获取项目统计",
    description="获取项目统计信息。权限: admin, finance, account_manager, ceo"
)
@log_requests("projects")
async def get_project_statistics(
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """获取项目统计"""
    try:
        stats = service.get_project_statistics(current_user)
        return success_response(data=stats, message="获取统计成功")

    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)
    except Exception as e:
        logger.error("get_statistics_error", error=str(e))
        return error_response(code="SYS-500", message="获取统计信息失败", status_code=500)


@router.get(
    "/{project_id}",
    summary="获取项目详情"
)
@log_requests("projects")
async def get_project(
    project_id: int = Path(..., gt=0),
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """获取项目详情"""
    try:
        project = service.get_project(project_id, current_user)
        return success_response(data=build_project_response(project))

    except NotFoundError as e:
        return error_response(code="RES-001", message=str(e), status_code=404)
    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)


@router.put(
    "/{project_id}",
    summary="更新项目",
    description="更新项目信息。权限: admin, account_manager (仅自己负责的)"
)
@log_requests("projects")
async def update_project(
    project_id: int = Path(..., gt=0),
    request: ProjectUpdateRequest = None,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """更新项目"""
    try:
        project = service.update_project(project_id, request, current_user)
        return success_response(
            data=build_project_response(project),
            message="项目更新成功"
        )

    except NotFoundError as e:
        return error_response(code="RES-001", message=str(e), status_code=404)
    except ConflictError as e:
        return error_response(code="RES-002", message=str(e), status_code=409)
    except ValidationError as e:
        return error_response(code="VAL-001", message=str(e), status_code=400)
    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除项目",
    description="删除项目。权限: admin only。有关联数据时禁止删除。"
)
@log_requests("projects")
async def delete_project(
    project_id: int = Path(..., gt=0),
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """删除项目"""
    try:
        service.delete_project(project_id, current_user)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except NotFoundError as e:
        return error_response(code="RES-001", message=str(e), status_code=404)
    except BusinessError as e:
        return error_response(code="BIZ-001", message=str(e), status_code=400)
    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)


@router.post(
    "/{project_id}/fulfill",
    summary="标记项目履约完成",
    description="""
标记项目履约完成。

**SoT Reference**: BUSINESS_RULES.md v4.6 BR-PROJ-006, BI-06

**状态转换**: running → fulfilled (不可逆)

**权限**: admin, project_owner, ceo, account_manager (仅负责的项目)

**履约原因**:
- `spend_exhausted`: 消耗完毕
- `client_stopped`: 客户喊停
"""
)
@log_requests("projects")
async def mark_project_fulfilled(
    project_id: int = Path(..., gt=0),
    request: ProjectMarkFulfilledRequest = None,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """标记项目履约完成"""
    try:
        project = service.mark_project_fulfilled(project_id, request, current_user)
        return success_response(
            data=build_project_response(project),
            message="项目已标记为履约完成"
        )

    except NotFoundError as e:
        return error_response(code="RES-001", message=str(e), status_code=404)
    except BusinessError as e:
        return error_response(code="STATE-002", message=str(e), status_code=400)
    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)


# ========================================
# 项目成员管理
# ========================================

@router.post(
    "/{project_id}/members",
    summary="分配项目成员",
    description="分配用户到项目。权限: admin, account_manager"
)
@log_requests("projects")
async def assign_member(
    project_id: int = Path(..., gt=0),
    request: ProjectMemberAssignRequest = None,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """分配项目成员"""
    try:
        member = service.assign_member(project_id, request, current_user)
        return success_response(
            data=build_project_member_response(member),
            message="成员分配成功"
        )

    except NotFoundError as e:
        return error_response(code="RES-001", message=str(e), status_code=404)
    except ConflictError as e:
        return error_response(code="RES-002", message=str(e), status_code=409)
    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)


@router.get(
    "/{project_id}/members",
    summary="获取项目成员列表"
)
@log_requests("projects")
async def get_project_members(
    project_id: int = Path(..., gt=0),
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """获取项目成员列表"""
    try:
        members = service.get_project_members(project_id, current_user)
        return success_response(
            data=[build_project_member_response(m) for m in members],
            message="获取成员列表成功"
        )

    except NotFoundError as e:
        return error_response(code="RES-001", message=str(e), status_code=404)
    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)


@router.delete(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="移除项目成员",
    description="从项目中移除成员。权限: admin, account_manager"
)
@log_requests("projects")
async def remove_member(
    project_id: int = Path(..., gt=0),
    user_id: str = Path(..., description="用户ID (UUID字符串)"),
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """移除项目成员"""
    try:
        service.remove_member(project_id, user_id, current_user)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except NotFoundError as e:
        return error_response(code="RES-001", message=str(e), status_code=404)
    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)


# ========================================
# 项目费用管理
# ========================================

@router.post(
    "/{project_id}/expenses",
    summary="添加项目费用",
    description="记录项目费用。权限: admin, account_manager, finance"
)
@log_requests("projects")
async def add_expense(
    project_id: int = Path(..., gt=0),
    request: ProjectExpenseRequest = None,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """添加项目费用"""
    try:
        expense = service.add_expense(project_id, request, current_user)
        return success_response(
            data=build_project_expense_response(expense),
            message="费用添加成功"
        )

    except NotFoundError as e:
        return error_response(code="RES-001", message=str(e), status_code=404)
    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)


@router.get(
    "/{project_id}/expenses",
    summary="获取项目费用列表"
)
@log_requests("projects")
async def get_project_expenses(
    project_id: int = Path(..., gt=0),
    pagination: PaginationParams = Depends(get_pagination),
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    """获取项目费用列表 (分页)"""
    try:
        expenses, total = service.get_project_expenses(
            project_id,
            current_user,
            pagination
        )

        expense_responses = [build_project_expense_response(e) for e in expenses]

        return create_paginated_response(
            items=expense_responses,
            total=total,
            pagination=pagination,
            message="获取费用列表成功"
        )

    except NotFoundError as e:
        return error_response(code="RES-001", message=str(e), status_code=404)
    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)
