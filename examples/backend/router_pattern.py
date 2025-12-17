"""
Router 层标准模式 - AI 广告代投系统
Version: 1.0
SoT Reference: API_SOT.md v9.0

本文件展示 Router 层的标准写法，供 AI 代码生成参考。

关键模式：
1. 依赖注入获取 Service 实例
2. 统一响应格式 (success_response, error_response)
3. 错误码遵循 ERROR_CODES_SOT.md v2.1
4. 权限控制通过 require_role 装饰器
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

# === 核心依赖导入 ===
from backend.core.db import get_db
from backend.core.dependencies import get_current_user, require_role
from backend.core.response import (
    success_response,
    error_response,
    paginated_response,
    StandardResponse
)
from backend.core.error_codes import (
    SystemErrorCodes,
    BusinessErrorCodes,
    ValidationErrorCodes,
)
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
)

# === Schema 和 Service 导入 ===
from backend.models import User
from backend.schemas.example import (  # 替换为实际 schema
    ExampleCreateRequest,
    ExampleUpdateRequest,
    ExampleResponse,
    ExampleQueryParams,
)
from backend.services.example_service import ExampleService  # 替换为实际 service

logger = logging.getLogger(__name__)

# === Router 定义 ===
router = APIRouter(prefix="/examples", tags=["examples"])


# === 依赖注入函数 ===
def get_example_service(db: Session = Depends(get_db)) -> ExampleService:
    """获取服务实例 - 标准依赖注入模式"""
    return ExampleService(db)


# === CRUD 端点 ===

@router.get("", response_model=StandardResponse)
async def list_examples(
    # 分页参数
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    # 筛选参数
    status: Optional[str] = Query(None, description="状态筛选"),
    # 依赖注入
    service: ExampleService = Depends(get_example_service),
    current_user: User = Depends(get_current_user),
):
    """
    获取列表 - GET /api/v1/examples

    权限: 登录用户
    SoT: API_SOT.md v9.0 Section X.X
    """
    try:
        items, total = service.list_examples(
            page=page,
            page_size=page_size,
            status=status,
            current_user=current_user,
        )
        return paginated_response(
            data=[ExampleResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        logger.error(f"List examples failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=SystemErrorCodes.INTERNAL_ERROR,
                message="获取列表失败",
            )
        )


@router.get("/{item_id}", response_model=StandardResponse)
async def get_example(
    item_id: int,
    service: ExampleService = Depends(get_example_service),
    current_user: User = Depends(get_current_user),
):
    """
    获取详情 - GET /api/v1/examples/{item_id}

    权限: 登录用户
    错误码: BIZ_002 (资源不存在)
    """
    try:
        item = service.get_by_id(item_id, current_user)
        return success_response(data=ExampleResponse.model_validate(item))
    except ResourceNotFoundError as e:
        # ERROR_CODES_SOT v2.1: BIZ_002 = 资源未找到 (404)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="BIZ_002", message=str(e))
        )


@router.post("", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def create_example(
    request: ExampleCreateRequest,
    service: ExampleService = Depends(get_example_service),
    current_user: User = Depends(get_current_user),
):
    """
    创建资源 - POST /api/v1/examples

    权限: 登录用户
    错误码: BIZ_003 (资源已存在), VAL_001 (参数校验失败)
    """
    try:
        item = service.create(request, current_user)
        logger.info(f"Created example {item.id} by user {current_user.id}")
        return success_response(
            data=ExampleResponse.model_validate(item),
            message="创建成功"
        )
    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code=e.error_code, message=str(e))
        )


@router.put("/{item_id}", response_model=StandardResponse)
async def update_example(
    item_id: int,
    request: ExampleUpdateRequest,
    service: ExampleService = Depends(get_example_service),
    current_user: User = Depends(get_current_user),
):
    """
    更新资源 - PUT /api/v1/examples/{item_id}

    权限: 登录用户 + 资源所有者/管理员
    """
    try:
        item = service.update(item_id, request, current_user)
        return success_response(
            data=ExampleResponse.model_validate(item),
            message="更新成功"
        )
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="BIZ_002", message=str(e))
        )
    except PermissionDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(code="AUTH_003", message=str(e))
        )


@router.delete("/{item_id}", response_model=StandardResponse)
async def delete_example(
    item_id: int,
    service: ExampleService = Depends(get_example_service),
    current_user: User = Depends(require_role(["admin"])),  # 仅管理员
):
    """
    删除资源 - DELETE /api/v1/examples/{item_id}

    权限: 管理员
    """
    try:
        service.delete(item_id, current_user)
        return success_response(message="删除成功")
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(code="BIZ_002", message=str(e))
        )


# === 业务操作端点 ===

@router.post("/{item_id}/approve", response_model=StandardResponse)
async def approve_example(
    item_id: int,
    service: ExampleService = Depends(get_example_service),
    current_user: User = Depends(require_role(["admin", "finance"])),
):
    """
    审批操作 - POST /api/v1/examples/{item_id}/approve

    权限: 管理员或财务
    状态机: STATE_MACHINE.md v2.6
    """
    try:
        item = service.approve(item_id, current_user)
        return success_response(
            data=ExampleResponse.model_validate(item),
            message="审批成功"
        )
    except BusinessLogicError as e:
        # 状态转换失败等业务错误
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(code=e.error_code, message=str(e))
        )
