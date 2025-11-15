"""
财务总账API路由
处理财务流水、账户余额、预算分配等接口
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from pydantic import BaseModel, Field

from core.permissions import (
    require_permissions,
    get_permission_checker,
    Permission,
    finance_required,
    admin_required
)
from core.security import AuthenticatedUser
from core.response import ApiResponse, PaginatedResponse
from core.error_codes import ErrorCode
from models.ledger import TransactionType, TransactionStatus
from services.ledger_service import get_ledger_service, LedgerService
from services.audit_service import audit_dependency, BusinessAction


router = APIRouter(prefix="/api/v1/ledger", tags=["财务总账"])


# Pydantic模型定义
class TransactionCreateRequest(BaseModel):
    """创建交易请求"""
    transaction_type: TransactionType
    amount: Decimal = Field(..., gt=0, description="交易金额必须大于0")
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$", description="货币代码")
    project_id: Optional[UUID] = Field(None, description="项目ID")
    account_id: Optional[UUID] = Field(None, description="账户ID")
    topup_id: Optional[UUID] = Field(None, description="充值ID")
    reference_id: Optional[str] = Field(None, description="关联业务ID")
    description: Optional[str] = Field(None, description="交易描述")
    metadata: Optional[Dict[str, Any]] = Field(None, description="交易元数据")


class TransactionUpdateRequest(BaseModel):
    """更新交易请求"""
    status: TransactionStatus
    note: Optional[str] = Field(None, description="备注信息")


class BudgetAllocationCreateRequest(BaseModel):
    """创建预算分配请求"""
    project_id: UUID
    category: str = Field(..., description="预算类别")
    allocated_amount: Decimal = Field(..., gt=0, description="分配金额")


class TransactionResponse(BaseModel):
    """交易响应"""
    id: str
    transaction_number: str
    transaction_type: str
    amount: float
    currency: str
    status: str
    project_id: Optional[str]
    account_id: Optional[str]
    topup_id: Optional[str]
    reference_id: Optional[str]
    description: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: str
    updated_at: Optional[str]


class AccountBalanceResponse(BaseModel):
    """账户余额响应"""
    account_id: Optional[str]
    project_id: Optional[str]
    currency: str
    current_balance: float
    available_balance: float
    frozen_balance: float
    total_credit: float
    total_debit: float
    last_updated: Optional[str]


class BudgetAllocationResponse(BaseModel):
    """预算分配响应"""
    id: str
    category: str
    allocated_amount: float
    spent_amount: float
    remaining_amount: float
    percentage_used: float
    is_active: bool
    created_at: str
    updated_at: Optional[str]


# API路由定义
@router.post("/transactions", response_model=ApiResponse[TransactionResponse])
async def create_transaction(
    request: TransactionCreateRequest,
    current_user: AuthenticatedUser,
    audit_data: tuple[AuthenticatedUser, Any] = Depends(audit_dependency),
    permission_checker: Any = Depends(get_permission_checker),
    ledger_service: LedgerService = Depends(get_ledger_service)
):
    """
    创建财务交易记录
    需要权限: FINANCE_CREATE 或 ADMIN
    """
    user, audit_service = audit_data

    # 权限检查
    if not (permission_checker.has_permission(Permission.FINANCE_CREATE) or
            permission_checker.has_role("admin")):
        audit_service.log_permission_denied(
            user_id=user.id,
            resource="ledger_transactions",
            action="create"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": ErrorCode.PERMISSION_DENIED, "message": "权限不足"}
        )

    try:
        transaction = ledger_service.create_transaction(
            transaction_type=request.transaction_type,
            amount=request.amount,
            currency=request.currency,
            project_id=request.project_id,
            account_id=request.account_id,
            topup_id=request.topup_id,
            reference_id=request.reference_id,
            description=request.description,
            metadata=request.metadata,
            user_id=user.id
        )

        return ApiResponse(
            success=True,
            data=TransactionResponse(**ledger_service._transaction_to_dict(transaction)),
            message="交易记录创建成功",
            code="SUCCESS"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": ErrorCode.INTERNAL_ERROR, "message": f"创建交易失败: {str(e)}"}
        )


@router.get("/transactions", response_model=ApiResponse[PaginatedResponse])
async def get_transactions(
    project_id: Optional[UUID] = Query(None, description="项目ID"),
    account_id: Optional[UUID] = Query(None, description="账户ID"),
    transaction_type: Optional[TransactionType] = Query(None, description="交易类型"),
    status: Optional[TransactionStatus] = Query(None, description="交易状态"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: AuthenticatedUser = Depends(require_permissions(Permission.FINANCE_READ)),
    ledger_service: LedgerService = Depends(get_ledger_service)
):
    """
    获取交易记录列表
    需要权限: FINANCE_READ
    """
    try:
        result = ledger_service.get_transactions(
            project_id=project_id,
            account_id=account_id,
            transaction_type=transaction_type,
            status=status,
            start_date=start_date,
            end_date=end_date,
            page=page,
            size=size
        )

        return ApiResponse(
            success=True,
            data=result,
            message="获取交易记录成功",
            code="SUCCESS"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": ErrorCode.INTERNAL_ERROR, "message": f"获取交易记录失败: {str(e)}"}
        )


@router.put("/transactions/{transaction_id}/status", response_model=ApiResponse[TransactionResponse])
async def update_transaction_status(
    transaction_id: UUID,
    request: TransactionUpdateRequest,
    current_user: AuthenticatedUser,
    audit_data: tuple[AuthenticatedUser, Any] = Depends(audit_dependency),
    permission_checker: Any = Depends(get_permission_checker),
    ledger_service: LedgerService = Depends(get_ledger_service)
):
    """
    更新交易状态
    需要权限: FINANCE_UPDATE 或 ADMIN
    """
    user, audit_service = audit_data

    # 权限检查
    if not (permission_checker.has_permission(Permission.FINANCE_UPDATE) or
            permission_checker.has_role("admin")):
        audit_service.log_permission_denied(
            user_id=user.id,
            resource="ledger_transactions",
            action="update_status"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": ErrorCode.PERMISSION_DENIED, "message": "权限不足"}
        )

    try:
        transaction = ledger_service.update_transaction_status(
            transaction_id=transaction_id,
            status=request.status,
            user_id=user.id,
            note=request.note
        )

        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": ErrorCode.NOT_FOUND, "message": "交易记录不存在"}
            )

        return ApiResponse(
            success=True,
            data=TransactionResponse(**ledger_service._transaction_to_dict(transaction)),
            message="交易状态更新成功",
            code="SUCCESS"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": ErrorCode.INTERNAL_ERROR, "message": f"更新交易状态失败: {str(e)}"}
        )


@router.get("/balance", response_model=ApiResponse[Optional[AccountBalanceResponse]])
async def get_account_balance(
    account_id: Optional[UUID] = Query(None, description="账户ID"),
    project_id: Optional[UUID] = Query(None, description="项目ID"),
    current_user: AuthenticatedUser = Depends(require_permissions(Permission.FINANCE_READ)),
    ledger_service: LedgerService = Depends(get_ledger_service)
):
    """
    获取账户余额
    需要权限: FINANCE_READ
    """
    try:
        balance_data = ledger_service.get_account_balance(
            account_id=account_id,
            project_id=project_id
        )

        return ApiResponse(
            success=True,
            data=AccountBalanceResponse(**balance_data) if balance_data else None,
            message="获取账户余额成功",
            code="SUCCESS"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": ErrorCode.INTERNAL_ERROR, "message": f"获取账户余额失败: {str(e)}"}
        )


@router.get("/projects/{project_id}/budget", response_model=ApiResponse[List[BudgetAllocationResponse]])
async def get_project_budget_allocation(
    project_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permissions(Permission.FINANCE_READ)),
    ledger_service: LedgerService = Depends(get_ledger_service)
):
    """
    获取项目预算分配
    需要权限: FINANCE_READ
    """
    try:
        allocations = ledger_service.get_project_budget_allocation(project_id)

        return ApiResponse(
            success=True,
            data=[BudgetAllocationResponse(**allocation) for allocation in allocations],
            message="获取项目预算分配成功",
            code="SUCCESS"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": ErrorCode.INTERNAL_ERROR, "message": f"获取项目预算分配失败: {str(e)}"}
        )


@router.post("/budget", response_model=ApiResponse[BudgetAllocationResponse])
async def create_budget_allocation(
    request: BudgetAllocationCreateRequest,
    current_user: AuthenticatedUser,
    audit_data: tuple[AuthenticatedUser, Any] = Depends(audit_dependency),
    permission_checker: Any = Depends(get_permission_checker),
    ledger_service: LedgerService = Depends(get_ledger_service)
):
    """
    创建预算分配
    需要权限: FINANCE_CREATE 或 ADMIN
    """
    user, audit_service = audit_data

    # 权限检查
    if not (permission_checker.has_permission(Permission.FINANCE_CREATE) or
            permission_checker.has_role("admin")):
        audit_service.log_permission_denied(
            user_id=user.id,
            resource="budget_allocations",
            action="create"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": ErrorCode.PERMISSION_DENIED, "message": "权限不足"}
        )

    try:
        allocation = ledger_service.create_budget_allocation(
            project_id=request.project_id,
            category=request.category,
            allocated_amount=request.allocated_amount,
            user_id=user.id
        )

        response_data = {
            "id": str(allocation.id),
            "category": allocation.category,
            "allocated_amount": float(allocation.allocated_amount),
            "spent_amount": float(allocation.spent_amount),
            "remaining_amount": float(allocation.remaining_amount),
            "percentage_used": float(allocation.percentage_used),
            "is_active": allocation.is_active,
            "created_at": allocation.created_at.isoformat(),
            "updated_at": allocation.updated_at.isoformat() if allocation.updated_at else None
        }

        return ApiResponse(
            success=True,
            data=BudgetAllocationResponse(**response_data),
            message="预算分配创建成功",
            code="SUCCESS"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": ErrorCode.INTERNAL_ERROR, "message": f"创建预算分配失败: {str(e)}"}
        )


@router.get("/statistics", response_model=ApiResponse[Dict[str, Any]])
async def get_transaction_statistics(
    project_id: Optional[UUID] = Query(None, description="项目ID"),
    account_id: Optional[UUID] = Query(None, description="账户ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: AuthenticatedUser = Depends(require_permissions(Permission.FINANCE_READ)),
    ledger_service: LedgerService = Depends(get_ledger_service)
):
    """
    获取交易统计信息
    需要权限: FINANCE_READ
    """
    try:
        statistics = ledger_service.get_transaction_statistics(
            project_id=project_id,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date
        )

        return ApiResponse(
            success=True,
            data=statistics,
            message="获取交易统计成功",
            code="SUCCESS"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": ErrorCode.INTERNAL_ERROR, "message": f"获取交易统计失败: {str(e)}"}
        )


@router.get("/export", response_model=ApiResponse[Dict[str, Any]])
async def export_transactions(
    project_id: Optional[UUID] = Query(None, description="项目ID"),
    account_id: Optional[UUID] = Query(None, description="账户ID"),
    transaction_type: Optional[TransactionType] = Query(None, description="交易类型"),
    status: Optional[TransactionStatus] = Query(None, description="交易状态"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    format: str = Query("csv", pattern="^(csv|excel)$", description="导出格式"),
    current_user: AuthenticatedUser = Depends(require_permissions(Permission.REPORT_EXPORT)),
    request: Request = None,
    ledger_service: LedgerService = Depends(get_ledger_service)
):
    """
    导出交易记录
    需要权限: REPORT_EXPORT
    """
    try:
        # 获取所有符合条件的交易记录
        result = ledger_service.get_transactions(
            project_id=project_id,
            account_id=account_id,
            transaction_type=transaction_type,
            status=status,
            start_date=start_date,
            end_date=end_date,
            page=1,
            size=10000  # 导出时使用较大的页面大小
        )

        # 记录导出操作到审计日志
        from services.audit_service import get_audit_service
        audit_service = get_audit_service()
        audit_service.log_data_export(
            user_id=current_user.id,
            table_name="ledger_transactions",
            record_count=result.total,
            filters={
                "project_id": str(project_id) if project_id else None,
                "account_id": str(account_id) if account_id else None,
                "transaction_type": transaction_type.value if transaction_type else None,
                "status": status.value if status else None,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            },
            request=request
        )

        return ApiResponse(
            success=True,
            data={
                "download_url": f"/api/v1/ledger/download/transactions/{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}",
                "total_records": result.total,
                "format": format,
                "generated_at": datetime.now().isoformat()
            },
            message="交易记录导出任务已创建",
            code="SUCCESS"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": ErrorCode.INTERNAL_ERROR, "message": f"导出交易记录失败: {str(e)}"}
        )