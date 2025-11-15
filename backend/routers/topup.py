"""
充值管理API路由
Version: 1.0
Author: Claude协作开发
"""

from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session

from core.db import get_db
from core.dependencies import get_current_user, require_role, get_client_info
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
from models.users import User
from schemas.topup import (
    TopupRequestCreate,
    TopupRequestResponse,
    TopupRequestListResponse,
    TopupDataReviewRequest,
    TopupFinanceApprovalRequest,
    TopupMarkPaidRequest,
    TopupReceiptUploadRequest,
    TopupApprovalLogResponse,
    TopupStatisticsResponse,
    TopupDashboardResponse,
    AdAccountBalance
)
from services.topup_service import TopupService

router = APIRouter(prefix="/topups", tags=["topups"])


def get_topup_service(db: Session = Depends(get_db)) -> TopupService:
    """获取充值服务实例"""
    return TopupService(db)


@router.get(
    "",
    response_model=StandardResponse[TopupRequestListResponse],
    summary="获取充值申请列表"
)
async def list_topup_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    ad_account_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    request_no: Optional[str] = Query(None),
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(get_current_user)
):
    """获取充值申请列表API"""
    try:
        requests, total = service.get_requests(
            current_user=current_user,
            page=page,
            page_size=page_size,
            status=status,
            urgency=urgency,
            ad_account_id=ad_account_id,
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
            request_no=request_no
        )

        # 转换为响应格式
        request_responses = [
            TopupRequestResponse.model_validate(req)
            for req in requests
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
            data={"items": request_responses, "meta": meta},
            message="获取充值申请列表成功"
        )

    except Exception as e:
        return error_response(
            code="SYS_500",
            message="获取充值申请列表失败",
            status_code=500
        )


@router.post(
    "",
    response_model=StandardResponse[TopupRequestResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建充值申请"
)
async def create_topup_request(
    request_data: TopupRequestCreate,
    req: Request,
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(require_role(["media_buyer", "account_manager"]))
):
    """创建充值申请API"""
    try:
        # 获取客户端信息
        client_ip, user_agent = get_client_info(req)

        topup_request = service.create_request(
            request_data,
            current_user,
            ip_address=client_ip,
            user_agent=user_agent
        )

        response = TopupRequestResponse.model_validate(topup_request)

        return success_response(
            data=response,
            message="充值申请创建成功",
            status_code=201
        )

    except (BusinessLogicError, ResourceConflictError) as e:
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
    "/{request_id}",
    response_model=StandardResponse[TopupRequestResponse],
    summary="获取充值申请详情"
)
async def get_topup_request(
    request_id: int,
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(get_current_user)
):
    """获取充值申请详情API"""
    try:
        request = service.get_request_by_id(request_id, current_user)
        response = TopupRequestResponse.model_validate(request)

        return success_response(data=response)

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
    "/{request_id}/review",
    response_model=StandardResponse[TopupRequestResponse],
    summary="数据员审核"
)
async def data_review_request(
    request_id: int,
    review_data: TopupDataReviewRequest,
    req: Request,
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(require_role(["data_operator"]))
):
    """数据员审核API"""
    try:
        # 获取客户端信息
        client_ip, user_agent = get_client_info(req)

        request = service.data_review(
            request_id,
            review_data,
            current_user,
            ip_address=client_ip,
            user_agent=user_agent
        )

        response = TopupRequestResponse.model_validate(request)

        return success_response(
            data=response,
            message="审核完成"
        )

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS_004",
            message=str(e),
            status_code=404
        )
    except (BusinessLogicError, PermissionDeniedError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "BIZ_ERROR",
            message=str(e),
            status_code=400
        )


@router.put(
    "/{request_id}/approve",
    response_model=StandardResponse[TopupRequestResponse],
    summary="财务审批"
)
async def finance_approve_request(
    request_id: int,
    approval_data: TopupFinanceApprovalRequest,
    req: Request,
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(require_role(["finance"]))
):
    """财务审批API"""
    try:
        # 获取客户端信息
        client_ip, user_agent = get_client_info(req)

        request = service.finance_approve(
            request_id,
            approval_data,
            current_user,
            ip_address=client_ip,
            user_agent=user_agent
        )

        response = TopupRequestResponse.model_validate(request)

        return success_response(
            data=response,
            message="财务审批完成"
        )

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS_004",
            message=str(e),
            status_code=404
        )
    except (BusinessLogicError, PermissionDeniedError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "BIZ_ERROR",
            message=str(e),
            status_code=400
        )


@router.put(
    "/{request_id}/pay",
    response_model=StandardResponse[TopupRequestResponse],
    summary="标记已打款"
)
async def mark_as_paid(
    request_id: int,
    paid_data: TopupMarkPaidRequest,
    req: Request,
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(require_role(["finance"]))
):
    """标记已打款API"""
    try:
        # 获取客户端信息
        client_ip, user_agent = get_client_info(req)

        request = service.mark_as_paid(
            request_id,
            paid_data,
            current_user,
            ip_address=client_ip,
            user_agent=user_agent
        )

        response = TopupRequestResponse.model_validate(request)

        return success_response(
            data=response,
            message="已标记为打款"
        )

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS_004",
            message=str(e),
            status_code=404
        )
    except (BusinessLogicError, PermissionDeniedError, ResourceConflictError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "BIZ_ERROR",
            message=str(e),
            status_code=400
        )


@router.post(
    "/{request_id}/receipt",
    response_model=StandardResponse[TopupRequestResponse],
    summary="上传打款凭证"
)
async def upload_receipt(
    request_id: int,
    receipt_data: TopupReceiptUploadRequest,
    req: Request,
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(require_role(["finance"]))
):
    """上传打款凭证API"""
    try:
        # 获取客户端信息
        client_ip, user_agent = get_client_info(req)

        request = service.upload_receipt(
            request_id,
            receipt_data,
            current_user,
            ip_address=client_ip,
            user_agent=user_agent
        )

        response = TopupRequestResponse.model_validate(request)

        return success_response(
            data=response,
            message="凭证上传成功"
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
    "/{request_id}/logs",
    response_model=StandardResponse[List[TopupApprovalLogResponse]],
    summary="获取审批日志"
)
async def get_approval_logs(
    request_id: int,
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(get_current_user)
):
    """获取审批日志API"""
    try:
        logs = service.get_approval_logs(request_id, current_user)
        log_responses = [
            TopupApprovalLogResponse.model_validate(log)
            for log in logs
        ]

        return success_response(
            data=log_responses,
            message="获取审批日志成功"
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
    response_model=StandardResponse[TopupStatisticsResponse],
    summary="获取充值统计"
)
async def get_statistics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"]))
):
    """获取充值统计API"""
    try:
        stats = service.get_statistics(
            current_user=current_user,
            start_date=start_date,
            end_date=end_date
        )
        stats_response = TopupStatisticsResponse.model_validate(stats)

        return success_response(data=stats_response)

    except Exception as e:
        return error_response(
            code="SYS_500",
            message="获取统计信息失败",
            status_code=500
        )


@router.get(
    "/dashboard",
    response_model=StandardResponse[TopupDashboardResponse],
    summary="获取仪表板数据"
)
async def get_dashboard(
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(get_current_user)
):
    """获取仪表板数据API"""
    try:
        dashboard_data = service.get_dashboard_data(current_user)
        dashboard_response = TopupDashboardResponse.model_validate(dashboard_data)

        return success_response(data=dashboard_response)

    except Exception as e:
        return error_response(
            code="SYS_500",
            message="获取仪表板数据失败",
            status_code=500
        )


@router.get(
    "/accounts/{account_id}/balance",
    response_model=StandardResponse[AdAccountBalance],
    summary="获取账户余额"
)
async def get_account_balance(
    account_id: int,
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(get_current_user)
):
    """获取账户余额API"""
    try:
        balance = service.get_account_balance(account_id, current_user)
        balance_response = AdAccountBalance.model_validate(balance)

        return success_response(data=balance_response)

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
    "/export",
    response_model=StandardResponse[List[dict]],
    summary="导出充值记录"
)
async def export_requests(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(require_role(["admin", "finance"]))
):
    """导出充值记录API"""
    try:
        export_data = service.export_requests(
            current_user=current_user,
            start_date=start_date,
            end_date=end_date,
            status=status
        )

        return success_response(
            data=export_data,
            message="导出数据生成成功"
        )

    except Exception as e:
        return error_response(
            code="SYS_500",
            message="导出数据失败",
            status_code=500
        )