"""
项目成员管理 API 路由

RESTful 端点:
- POST   /project-members              创建成员
- GET    /project-members/{id}         获取单个成员
- PUT    /project-members/{id}         更新成员
- DELETE /project-members/{id}         删除成员
- GET    /projects/{id}/members        获取项目成员列表
- POST   /projects/{id}/transfer-owner 转移项目负责人
- GET    /users/{id}/projects          获取用户参与的项目
- POST   /project-members/batch        批量添加成员

SoT Reference: API_SOT.md v9.0, MASTER.md v4.4 §2.4
"""

from typing import Optional
from uuid import UUID
import structlog

from fastapi import APIRouter, Depends, Query, Path, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.dependencies import get_current_user
from backend.core.logging import log_requests
from backend.core.response import success_response, error_response
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError,
)
from backend.models import User
from backend.models.core.project_member import ProjectMember
from backend.schemas.project_member import (
    ProjectMemberCreateRequest,
    ProjectMemberUpdateRequest,
    TransferOwnershipRequest,
    BatchAddMembersRequest,
    ProjectMemberResponse,
    ProjectMemberDetailResponse,
    ProjectMemberListResponse,
    TransferOwnershipResponse,
    BatchAddMembersResponse,
)
from backend.services.project_member_service import ProjectMemberService

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["project-members"])


def get_project_member_service(db: Session = Depends(get_db)) -> ProjectMemberService:
    """获取项目成员服务实例"""
    return ProjectMemberService(db)


def build_member_response(member: ProjectMember) -> ProjectMemberResponse:
    """
    构建 ProjectMemberResponse

    处理:
    - user_id: UUID → str
    - 关联用户信息
    - 关联项目信息
    """
    # 获取用户信息
    user = getattr(member, 'user', None)
    user_name = None
    user_email = None
    user_role = None

    if user:
        user_name = getattr(user, 'username', None) or getattr(user, 'email', None)
        user_email = getattr(user, 'email', None)
        role_val = getattr(user, 'role', None)
        if role_val:
            user_role = role_val.value if hasattr(role_val, 'value') else str(role_val)

    # 获取项目信息
    project = getattr(member, 'project', None)
    project_name = None
    if project:
        project_name = getattr(project, 'name', None)

    return ProjectMemberResponse(
        id=member.id,
        project_id=member.project_id,
        user_id=str(member.user_id),
        role=member.role,
        permissions=member.permissions,
        notes=member.notes,
        created_at=member.created_at,
        updated_at=member.updated_at,
        user_name=user_name,
        user_email=user_email,
        user_role=user_role,
        project_name=project_name,
    )


def build_member_detail_response(member: ProjectMember) -> ProjectMemberDetailResponse:
    """构建详细成员响应"""
    base = build_member_response(member)

    # 额外用户信息
    user = getattr(member, 'user', None)
    user_avatar = None
    user_phone = None
    if user:
        user_avatar = getattr(user, 'avatar_url', None)
        user_phone = getattr(user, 'phone', None)

    # 额外项目信息
    project = getattr(member, 'project', None)
    project_status = None
    project_client_name = None
    if project:
        project_status = getattr(project, 'status', None)
        project_client_name = getattr(project, 'client_name', None)

    return ProjectMemberDetailResponse(
        **base.model_dump(),
        user_avatar=user_avatar,
        user_phone=user_phone,
        project_status=project_status,
        project_client_name=project_client_name,
        is_owner=member.is_owner,
        can_edit=member.can_edit,
    )


# ==================== CRUD 端点 ====================

@router.post(
    "/project-members",
    status_code=status.HTTP_201_CREATED,
    summary="创建项目成员"
)
@log_requests("project_members")
async def create_project_member(
    request: ProjectMemberCreateRequest,
    service: ProjectMemberService = Depends(get_project_member_service),
    current_user: User = Depends(get_current_user)
):
    """
    创建项目成员

    - 需要 admin 权限或项目 owner 权限
    - 每个项目最多一个 owner
    - 同一用户不能重复加入同一项目
    """
    try:
        member = service.create_member(request, current_user)
        response = build_member_response(member)

        return success_response(
            data=response,
            message="成员添加成功",
            status_code=201
        )

    except ResourceNotFoundError as e:
        return error_response(
            code=e.error_code if hasattr(e, 'error_code') else "SYS-004",
            message=str(e),
            status_code=404
        )
    except ResourceConflictError as e:
        return error_response(
            code=e.error_code if hasattr(e, 'error_code') else "BIZ-001",
            message=str(e),
            status_code=409
        )
    except PermissionDeniedError as e:
        return error_response(
            code=e.error_code if hasattr(e, 'error_code') else "AUTH-002",
            message=str(e),
            status_code=403
        )


@router.get(
    "/project-members/{member_id}",
    summary="获取项目成员详情"
)
@log_requests("project_members")
async def get_project_member(
    member_id: int = Path(..., gt=0, description="成员关系ID"),
    service: ProjectMemberService = Depends(get_project_member_service),
    current_user: User = Depends(get_current_user)
):
    """获取单个项目成员详情"""
    try:
        member = service.get_member(member_id, current_user)
        response = build_member_detail_response(member)

        return success_response(data=response)

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS-004",
            message=str(e),
            status_code=404
        )
    except PermissionDeniedError as e:
        return error_response(
            code="AUTH-002",
            message=str(e),
            status_code=403
        )


@router.put(
    "/project-members/{member_id}",
    summary="更新项目成员"
)
@log_requests("project_members")
async def update_project_member(
    request: ProjectMemberUpdateRequest,
    member_id: int = Path(..., gt=0, description="成员关系ID"),
    service: ProjectMemberService = Depends(get_project_member_service),
    current_user: User = Depends(get_current_user)
):
    """
    更新项目成员角色/权限

    - 需要 admin 权限或项目 owner 权限
    - 如果要升级为 owner，需使用转移负责人接口
    """
    try:
        member = service.update_member(member_id, request, current_user)
        response = build_member_response(member)

        return success_response(
            data=response,
            message="成员更新成功"
        )

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS-004",
            message=str(e),
            status_code=404
        )
    except ResourceConflictError as e:
        return error_response(
            code=e.error_code if hasattr(e, 'error_code') else "BIZ-002",
            message=str(e),
            status_code=409
        )
    except PermissionDeniedError as e:
        return error_response(
            code="AUTH-002",
            message=str(e),
            status_code=403
        )


@router.delete(
    "/project-members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除项目成员"
)
@log_requests("project_members")
async def delete_project_member(
    member_id: int = Path(..., gt=0, description="成员关系ID"),
    service: ProjectMemberService = Depends(get_project_member_service),
    current_user: User = Depends(get_current_user)
):
    """
    删除项目成员

    - 需要 admin 权限或项目 owner 权限
    - 项目负责人不能直接删除，需先转移负责人
    """
    try:
        service.delete_member(member_id, current_user)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS-004",
            message=str(e),
            status_code=404
        )
    except BusinessLogicError as e:
        return error_response(
            code=e.error_code if hasattr(e, 'error_code') else "BIZ-003",
            message=str(e),
            status_code=400
        )
    except PermissionDeniedError as e:
        return error_response(
            code="AUTH-002",
            message=str(e),
            status_code=403
        )


# ==================== 列表端点 ====================

@router.get(
    "/projects/{project_id}/members",
    summary="获取项目成员列表"
)
@log_requests("project_members")
async def list_project_members(
    project_id: int = Path(..., gt=0, description="项目ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    role: Optional[str] = Query(None, description="筛选角色: owner/member/viewer"),
    service: ProjectMemberService = Depends(get_project_member_service),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目成员列表

    - 需要项目成员身份或 admin 权限
    - owner 排在列表最前
    """
    try:
        members, total = service.get_project_members(
            project_id=project_id,
            current_user=current_user,
            page=page,
            page_size=page_size,
            role=role
        )

        member_responses = [build_member_response(m) for m in members]

        meta = {
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }

        return success_response(
            data={"items": member_responses, "meta": meta},
            message="获取成员列表成功"
        )

    except PermissionDeniedError as e:
        return error_response(
            code="AUTH-002",
            message=str(e),
            status_code=403
        )


@router.get(
    "/users/{user_id}/projects",
    summary="获取用户参与的项目"
)
@log_requests("project_members")
async def list_user_projects(
    user_id: UUID = Path(..., description="用户ID (UUID)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    role: Optional[str] = Query(None, description="筛选角色: owner/member/viewer"),
    service: ProjectMemberService = Depends(get_project_member_service),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户参与的项目列表

    - 普通用户只能查看自己的
    - admin 可以查看任意用户
    """
    try:
        members, total = service.get_user_projects(
            user_id=user_id,
            current_user=current_user,
            page=page,
            page_size=page_size,
            role=role
        )

        member_responses = [build_member_response(m) for m in members]

        meta = {
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }

        return success_response(
            data={"items": member_responses, "meta": meta},
            message="获取用户项目列表成功"
        )

    except PermissionDeniedError as e:
        return error_response(
            code="AUTH-002",
            message=str(e),
            status_code=403
        )


# ==================== 特殊操作端点 ====================

@router.post(
    "/projects/{project_id}/transfer-owner",
    summary="转移项目负责人"
)
@log_requests("project_members")
async def transfer_project_ownership(
    request: TransferOwnershipRequest,
    project_id: int = Path(..., gt=0, description="项目ID"),
    service: ProjectMemberService = Depends(get_project_member_service),
    current_user: User = Depends(get_current_user)
):
    """
    转移项目负责人

    - 需要 admin 权限或当前项目 owner 权限
    - 原子操作：降级当前 owner + 升级新 owner
    - 如果新负责人不是成员，会自动添加
    """
    try:
        result = service.transfer_ownership(project_id, request, current_user)

        response = TransferOwnershipResponse(
            success=True,
            previous_owner=build_member_response(result["previous_owner"]) if result["previous_owner"] else None,
            new_owner=build_member_response(result["new_owner"]),
            message="项目负责人转移成功"
        )

        return success_response(
            data=response,
            message="项目负责人转移成功"
        )

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS-004",
            message=str(e),
            status_code=404
        )
    except BusinessLogicError as e:
        return error_response(
            code=e.error_code if hasattr(e, 'error_code') else "BIZ-003",
            message=str(e),
            status_code=400
        )
    except PermissionDeniedError as e:
        return error_response(
            code="AUTH-002",
            message=str(e),
            status_code=403
        )


@router.post(
    "/project-members/batch",
    summary="批量添加成员"
)
@log_requests("project_members")
async def batch_add_members(
    request: BatchAddMembersRequest,
    service: ProjectMemberService = Depends(get_project_member_service),
    current_user: User = Depends(get_current_user)
):
    """
    批量添加项目成员

    - 最多 50 个成员
    - 部分失败不影响其他成功项
    - 返回成功/失败详情
    """
    try:
        result = service.batch_add_members(request.members, current_user)

        response = BatchAddMembersResponse(
            success_count=result["success_count"],
            failed_count=result["failed_count"],
            members=[build_member_response(m) for m in result["members"]],
            errors=result["errors"]
        )

        return success_response(
            data=response,
            message=f"批量添加完成: 成功 {result['success_count']}, 失败 {result['failed_count']}"
        )

    except Exception as e:
        logger.error("batch_add_members_error", error=str(e))
        return error_response(
            code="SYS-500",
            message="批量添加失败",
            status_code=500
        )


# ==================== 项目负责人查询 ====================

@router.get(
    "/projects/{project_id}/owner",
    summary="获取项目负责人"
)
@log_requests("project_members")
async def get_project_owner(
    project_id: int = Path(..., gt=0, description="项目ID"),
    service: ProjectMemberService = Depends(get_project_member_service),
    current_user: User = Depends(get_current_user)
):
    """获取项目负责人信息"""
    try:
        owner = service.get_project_owner(project_id)

        if not owner:
            return success_response(
                data=None,
                message="项目暂无负责人"
            )

        response = build_member_detail_response(owner)
        return success_response(
            data=response,
            message="获取项目负责人成功"
        )

    except Exception as e:
        logger.error("get_project_owner_error", error=str(e))
        return error_response(
            code="SYS-500",
            message="获取项目负责人失败",
            status_code=500
        )
