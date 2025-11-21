"""
项目模板管理API路由
Version: 1.0
Author: Claude协作开发
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.dependencies import get_current_user, require_role
from backend.core.response import success_response, error_response, StandardResponse
from backend.exceptions.custom_exceptions import (
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError
)
from backend.models import User
from backend.schemas.project_template import (
    ProjectTemplateCreateRequest,
    ProjectTemplateUpdateRequest,
    ProjectTemplateResponse,
    ProjectTemplateListResponse
)
from backend.services.project_template_service import ProjectTemplateService

router = APIRouter(prefix="/projects/templates", tags=["project-templates"])


def get_template_service(db: Session = Depends(get_db)) -> ProjectTemplateService:
    """获取项目模板服务实例"""
    return ProjectTemplateService(db)


@router.get(
    "",
    response_model=StandardResponse[ProjectTemplateListResponse],
    summary="获取项目模板列表"
)
async def list_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    service: ProjectTemplateService = Depends(get_template_service),
    current_user: User = Depends(get_current_user)
):
    """获取项目模板列表API"""
    try:
        templates, total = service.get_templates(
            page=page,
            page_size=page_size,
            category=category,
            is_active=is_active
        )

        # 转换为响应格式
        template_responses = [
            ProjectTemplateResponse.model_validate(template)
            for template in templates
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
            data={"items": template_responses, "meta": meta},
            message="获取项目模板列表成功"
        )

    except Exception as e:
        return error_response(
            code="SYS_500",
            message="获取项目模板列表失败",
            status_code=500
        )


@router.post(
    "",
    response_model=StandardResponse[ProjectTemplateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建项目模板"
)
@require_role(["admin", "account_manager"])
async def create_template(
    request: ProjectTemplateCreateRequest,
    service: ProjectTemplateService = Depends(get_template_service),
    current_user: User = Depends(get_current_user)
):
    """创建项目模板API"""
    try:
        template = service.create_template(request, current_user)
        template_response = ProjectTemplateResponse.model_validate(template)

        return success_response(
            data=template_response,
            message="项目模板创建成功",
            status_code=201
        )

    except (ResourceConflictError, ValueError) as e:
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
    "/{template_id}",
    response_model=StandardResponse[ProjectTemplateResponse],
    summary="获取项目模板详情"
)
async def get_template(
    template_id: int,
    service: ProjectTemplateService = Depends(get_template_service),
    current_user: User = Depends(get_current_user)
):
    """获取项目模板详情API"""
    try:
        template = service.get_template(template_id, current_user)
        template_response = ProjectTemplateResponse.model_validate(template)

        return success_response(data=template_response)

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS_004",
            message=str(e),
            status_code=404
        )


@router.put(
    "/{template_id}",
    response_model=StandardResponse[ProjectTemplateResponse],
    summary="更新项目模板"
)
@require_role(["admin", "account_manager"])
async def update_template(
    template_id: int,
    request: ProjectTemplateUpdateRequest,
    service: ProjectTemplateService = Depends(get_template_service),
    current_user: User = Depends(get_current_user)
):
    """更新项目模板API"""
    try:
        template = service.update_template(template_id, request, current_user)
        template_response = ProjectTemplateResponse.model_validate(template)

        return success_response(
            data=template_response,
            message="项目模板更新成功"
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
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除项目模板"
)
@require_role(["admin"])
async def delete_template(
    template_id: int,
    service: ProjectTemplateService = Depends(get_template_service),
    current_user: User = Depends(get_current_user)
):
    """删除项目模板API"""
    try:
        service.delete_template(template_id, current_user)
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
    "/{template_id}/apply",
    response_model=StandardResponse[dict],
    summary="应用项目模板"
)
async def apply_template(
    template_id: int,
    project_name: str,
    client_name: str,
    service: ProjectTemplateService = Depends(get_template_service),
    current_user: User = Depends(get_current_user)
):
    """应用项目模板创建项目API"""
    try:
        project = service.apply_template(
            template_id=template_id,
            project_name=project_name,
            client_name=client_name,
            current_user=current_user
        )

        return success_response(
            data={"project_id": project.id, "message": "基于模板创建项目成功"},
            message="项目模板应用成功"
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
    "/categories/list",
    response_model=StandardResponse[List[dict]],
    summary="获取模板分类列表"
)
async def get_template_categories(
    service: ProjectTemplateService = Depends(get_template_service),
    current_user: User = Depends(get_current_user)
):
    """获取模板分类列表API"""
    try:
        categories = service.get_template_categories()

        return success_response(
            data=categories,
            message="获取模板分类列表成功"
        )

    except Exception as e:
        return error_response(
            code="SYS_500",
            message="获取模板分类列表失败",
            status_code=500
        )