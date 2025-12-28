"""
死号余额迁移API路由
Version: 1.0
Author: Claude协作开发

SoT References:
- docs/sot/STATE_MACHINE.md v2.6 第12章 (transfer_requests 状态机)
- docs/sot/API_SOT.md v9.0 (API 规范)
- docs/sot/ERROR_CODES_SOT.md v2.1 (错误码)
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.dependencies import get_current_user, require_role
from backend.core.response import success_response, error_response, StandardResponse
from backend.core.error_codes import BusinessErrorCodes, SystemErrorCodes
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError
)
from backend.models import User
from backend.schemas.transfer import (
    TransferRequestCreate,
    TransferRequestApprove,
    TransferRequestReject,
    TransferRequestResponse,
    TransferRequestListResponse,
)
from backend.services.transfer_service import TransferService

router = APIRouter(prefix="/transfers", tags=["transfers"])


def get_transfer_service(db: Session = Depends(get_db)) -> TransferService:
    """获取迁移服务实例"""
    return TransferService(db)


@router.get(
    "",
    response_model=StandardResponse[TransferRequestListResponse],
    summary="获取迁移申请列表"
)
async def list_transfers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    service: TransferService = Depends(get_transfer_service),
    current_user: User = Depends(get_current_user)
):
    """获取迁移申请列表API"""
    try:
        transfers, total = service.get_transfers(
            current_user=current_user,
            page=page,
            page_size=page_size,
            status=status,
        )

        items = [service._build_response(t) for t in transfers]

        meta = {
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }

        return success_response(
            data={"items": items, "meta": meta},
            message="获取迁移申请列表成功"
        )

    except Exception as e:
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message=f"获取迁移申请列表失败: {str(e)}",
            status_code=500
        )


@router.post(
    "",
    response_model=StandardResponse[TransferRequestResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建迁移申请"
)
async def create_transfer(
    request_data: TransferRequestCreate,
    service: TransferService = Depends(get_transfer_service),
    current_user: User = Depends(require_role(["admin", "account_manager", "finance"]))
):
    """
    创建迁移申请API

    权限: admin, account_manager, finance
    初始状态: draft
    """
    try:
        transfer = service.create_transfer(request_data, current_user)
        response = service._build_response(transfer)

        return success_response(
            data=response,
            message="迁移申请创建成功",
            status_code=201
        )

    except PermissionDeniedError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "AUTH-500",
            message=str(e),
            status_code=403
        )
    except ResourceNotFoundError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message=str(e),
            status_code=404
        )
    except BusinessLogicError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else BusinessErrorCodes.OPERATION_FAILED.code,
            message=str(e),
            status_code=400
        )
    except ValueError as e:
        return error_response(
            code="VALIDATION-001",
            message=str(e),
            status_code=400
        )


@router.get(
    "/{transfer_id}",
    response_model=StandardResponse[TransferRequestResponse],
    summary="获取迁移申请详情"
)
async def get_transfer(
    transfer_id: int,
    service: TransferService = Depends(get_transfer_service),
    current_user: User = Depends(get_current_user)
):
    """获取迁移申请详情API"""
    try:
        transfer = service.get_transfer_by_id(transfer_id, current_user)
        response = service._build_response(transfer)

        return success_response(data=response)

    except ResourceNotFoundError as e:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message=str(e),
            status_code=404
        )


@router.post(
    "/{transfer_id}/submit",
    response_model=StandardResponse[TransferRequestResponse],
    summary="提交迁移申请"
)
async def submit_transfer(
    transfer_id: int,
    service: TransferService = Depends(get_transfer_service),
    current_user: User = Depends(get_current_user)
):
    """
    提交迁移申请API

    状态流转: draft → pending_approval
    权限: 创建人或 admin
    """
    try:
        transfer = service.submit_transfer(transfer_id, current_user)
        response = service._build_response(transfer)

        return success_response(
            data=response,
            message="迁移申请已提交审批"
        )

    except ResourceNotFoundError as e:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message=str(e),
            status_code=404
        )
    except PermissionDeniedError as e:
        return error_response(
            code="AUTH-500",
            message=str(e),
            status_code=403
        )
    except BusinessLogicError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "STATE_400",
            message=str(e),
            status_code=409
        )


@router.post(
    "/{transfer_id}/approve",
    response_model=StandardResponse[TransferRequestResponse],
    summary="审批迁移申请"
)
async def approve_transfer(
    transfer_id: int,
    approval_data: TransferRequestApprove,
    service: TransferService = Depends(get_transfer_service),
    current_user: User = Depends(require_role(["admin", "finance"]))
):
    """
    审批迁移申请API

    状态流转: pending_approval → approved
    权限: finance, admin
    """
    try:
        transfer = service.approve_transfer(transfer_id, approval_data, current_user)
        response = service._build_response(transfer)

        return success_response(
            data=response,
            message="迁移申请已审批通过"
        )

    except ResourceNotFoundError as e:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message=str(e),
            status_code=404
        )
    except PermissionDeniedError as e:
        return error_response(
            code="AUTH-500",
            message=str(e),
            status_code=403
        )
    except BusinessLogicError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "STATE_400",
            message=str(e),
            status_code=409
        )


@router.post(
    "/{transfer_id}/reject",
    response_model=StandardResponse[TransferRequestResponse],
    summary="拒绝迁移申请"
)
async def reject_transfer(
    transfer_id: int,
    rejection_data: TransferRequestReject,
    service: TransferService = Depends(get_transfer_service),
    current_user: User = Depends(require_role(["admin", "finance"]))
):
    """
    拒绝迁移申请API

    状态流转: draft/pending_approval → rejected
    权限: finance, admin
    """
    try:
        transfer = service.reject_transfer(transfer_id, rejection_data, current_user)
        response = service._build_response(transfer)

        return success_response(
            data=response,
            message="迁移申请已拒绝"
        )

    except ResourceNotFoundError as e:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message=str(e),
            status_code=404
        )
    except PermissionDeniedError as e:
        return error_response(
            code="AUTH-500",
            message=str(e),
            status_code=403
        )
    except BusinessLogicError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "STATE_400",
            message=str(e),
            status_code=409
        )


@router.post(
    "/{transfer_id}/complete",
    response_model=StandardResponse[TransferRequestResponse],
    summary="完成迁移"
)
async def complete_transfer(
    transfer_id: int,
    service: TransferService = Depends(get_transfer_service),
    current_user: User = Depends(require_role(["admin"]))
):
    """
    完成迁移API

    状态流转: approved → completed
    权限: admin (或 system 自动执行)
    业务: 生成 TRANSFER_OUT/TRANSFER_IN Ledger 记录
    """
    try:
        transfer = service.complete_transfer(transfer_id, current_user)
        response = service._build_response(transfer)

        return success_response(
            data=response,
            message="迁移已完成"
        )

    except ResourceNotFoundError as e:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message=str(e),
            status_code=404
        )
    except PermissionDeniedError as e:
        return error_response(
            code="AUTH-500",
            message=str(e),
            status_code=403
        )
    except BusinessLogicError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "STATE_400",
            message=str(e),
            status_code=409
        )
