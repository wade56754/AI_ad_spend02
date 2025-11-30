"""
结算API路由
Version: 1.0
Author: Claude Code (full_pipeline)

Aligned with SoT:
- API_SOT.md v9.0 (API conventions)
- AUTH_SPEC.md v2.0 (role-based access)
- LEDGER_SOT.md v1.1 (ledger integration)
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.response import success_response, error_response, paginated_response
from backend.core.dependencies import get_current_user
from backend.services.settlement_service import SettlementService
from backend.schemas.settlement import (
    SettlementCreateRequest,
    SettlementUpdateRequest,
    SettlementApproveRequest,
    SettlementPaymentRequest,
    SettlementResponse,
    SettlementListResponse,
    SettlementStatisticsResponse,
)
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError
)

router = APIRouter(prefix="/settlements", tags=["Settlements"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_settlement(
    request: SettlementCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    创建结算

    权限：admin, finance
    """
    try:
        service = SettlementService(db)
        settlement = service.create_settlement(
            request=request,
            current_user_id=current_user.get("id"),
            current_user_role=current_user.get("role")
        )
        return success_response(data=settlement, message="结算创建成功")
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=dict)
async def list_settlements(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    settlement_type: Optional[str] = Query(None, description="结算类型"),
    status: Optional[str] = Query(None, description="结算状态"),
    payment_status: Optional[str] = Query(None, description="支付状态"),
    supplier_id: Optional[int] = Query(None, description="供应商ID"),
    client_id: Optional[int] = Query(None, description="客户ID"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取结算列表

    权限：admin, finance
    """
    try:
        service = SettlementService(db)
        settlements, total = service.get_settlements(
            current_user_id=current_user.get("id"),
            current_user_role=current_user.get("role"),
            page=page,
            page_size=page_size,
            settlement_type=settlement_type,
            status=status,
            payment_status=payment_status,
            supplier_id=supplier_id,
            client_id=client_id,
            start_date=start_date,
            end_date=end_date
        )
        return paginated_response(
            items=settlements,
            total=total,
            page=page,
            page_size=page_size
        )
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/statistics", response_model=dict)
async def get_settlement_statistics(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取结算统计信息

    权限：admin, finance
    """
    try:
        service = SettlementService(db)
        stats = service.get_settlement_statistics(
            current_user_id=current_user.get("id"),
            current_user_role=current_user.get("role"),
            start_date=start_date,
            end_date=end_date
        )
        return success_response(data=stats, message="获取统计信息成功")
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/overdue", response_model=dict)
async def get_overdue_settlements(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取逾期结算列表

    权限：admin, finance
    """
    try:
        service = SettlementService(db)
        settlements = service.get_overdue_settlements(
            current_user_id=current_user.get("id"),
            current_user_role=current_user.get("role")
        )
        return success_response(data=settlements, message="获取逾期结算成功")
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/{settlement_id}", response_model=dict)
async def get_settlement(
    settlement_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取结算详情

    权限：admin, finance
    """
    try:
        service = SettlementService(db)
        settlement = service.get_settlement(
            settlement_id=settlement_id,
            current_user_id=current_user.get("id"),
            current_user_role=current_user.get("role")
        )
        return success_response(data=settlement, message="获取结算成功")
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.put("/{settlement_id}", response_model=dict)
async def update_settlement(
    settlement_id: int,
    request: SettlementUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    更新结算

    权限：admin, finance
    约束：只能更新 DRAFT 或 REJECTED 状态的结算
    """
    try:
        service = SettlementService(db)
        settlement = service.update_settlement(
            settlement_id=settlement_id,
            request=request,
            current_user_id=current_user.get("id"),
            current_user_role=current_user.get("role")
        )
        return success_response(data=settlement, message="结算更新成功")
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{settlement_id}/submit", response_model=dict)
async def submit_settlement(
    settlement_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    提交结算审批

    权限：admin, finance
    状态流转：DRAFT -> PENDING
    """
    try:
        service = SettlementService(db)
        settlement = service.submit_settlement(
            settlement_id=settlement_id,
            current_user_id=current_user.get("id"),
            current_user_role=current_user.get("role")
        )
        return success_response(data=settlement, message="结算已提交审批")
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{settlement_id}/approve", response_model=dict)
async def approve_settlement(
    settlement_id: int,
    request: SettlementApproveRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    审批结算

    权限：admin only
    状态流转：PENDING -> APPROVED / REJECTED
    """
    try:
        service = SettlementService(db)
        settlement = service.approve_settlement(
            settlement_id=settlement_id,
            request=request,
            current_user_id=current_user.get("id"),
            current_user_role=current_user.get("role")
        )
        action_msg = "审批通过" if request.action == "approve" else "已拒绝"
        return success_response(data=settlement, message=f"结算{action_msg}")
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{settlement_id}/payment", response_model=dict)
async def record_payment(
    settlement_id: int,
    request: SettlementPaymentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    记录结算支付

    权限：admin, finance
    约束：只能对 APPROVED 或 PROCESSING 状态的结算记录支付
    按 LEDGER_SOT.md v1.1 生成账本分录
    """
    try:
        service = SettlementService(db)
        settlement = service.record_payment(
            settlement_id=settlement_id,
            request=request,
            current_user_id=current_user.get("id"),
            current_user_role=current_user.get("role")
        )
        return success_response(data=settlement, message="支付记录成功")
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{settlement_id}/cancel", response_model=dict)
async def cancel_settlement(
    settlement_id: int,
    reason: Optional[str] = Query(None, description="取消原因"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    取消结算

    权限：admin
    状态流转：DRAFT/APPROVED -> CANCELLED
    """
    try:
        service = SettlementService(db)
        settlement = service.cancel_settlement(
            settlement_id=settlement_id,
            current_user_id=current_user.get("id"),
            current_user_role=current_user.get("role"),
            reason=reason
        )
        return success_response(data=settlement, message="结算已取消")
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
