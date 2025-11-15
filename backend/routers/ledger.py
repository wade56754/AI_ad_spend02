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

from core.db import get_db
from core.dependencies import get_current_user, require_role
from core.response import (
    success_response,
    error_response,
    StandardResponse
)
from core.error_codes import ErrorCode
from models.users import User
from models.ledger import TransactionType, TransactionStatus
from services.ledger_service import get_ledger_service, LedgerService


# 定义分页响应类型
class PaginatedResponse(BaseModel):
    """分页响应"""
    items: List[Any]
    total: int
    page: int
    size: int


router = APIRouter(prefix="/ledger", tags=["ledger"])


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
@router.post("/transactions", response_model=StandardResponse[TransactionResponse])
async def create_transaction(
    request: TransactionCreateRequest,
    ledger_service: LedgerService = Depends(get_ledger_service),
    current_user: User = Depends(require_role(["admin", "finance"]))
):
    """
    创建财务交易记录
    需要权限: FINANCE 或 ADMIN
    """
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
            user_id=current_user.id
        )

        return success_response(
            data=TransactionResponse(**ledger_service._transaction_to_dict(transaction)),
            message="交易记录创建成功"
        )

    except Exception as e:
        return error_response(
            code="LEDGER_CREATE_ERROR",
            message=f"创建交易失败: {str(e)}",
            status_code=500
        )


@router.get("/transactions", response_model=StandardResponse[PaginatedResponse])
async def get_transactions(
    project_id: Optional[UUID] = Query(None, description="项目ID"),
    account_id: Optional[UUID] = Query(None, description="账户ID"),
    transaction_type: Optional[TransactionType] = Query(None, description="交易类型"),
    status: Optional[TransactionStatus] = Query(None, description="交易状态"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    ledger_service: LedgerService = Depends(get_ledger_service),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"]))
):
    """
    获取交易记录列表
    需要权限: FINANCE 或 ADMIN 或 DATA_OPERATOR
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

        return success_response(data=result, message="获取交易记录成功")

    except Exception as e:
        return error_response(
            code="LEDGER_QUERY_ERROR",
            message=f"获取交易记录失败: {str(e)}",
            status_code=500
        )


@router.put("/transactions/{transaction_id}/status", response_model=StandardResponse[TransactionResponse])
async def update_transaction_status(
    transaction_id: UUID,
    request: TransactionUpdateRequest,
    ledger_service: LedgerService = Depends(get_ledger_service),
    current_user: User = Depends(require_role(["admin", "finance"]))
):
    """
    更新交易状态
    需要权限: FINANCE 或 ADMIN
    """
    try:
        transaction = ledger_service.update_transaction_status(
            transaction_id=transaction_id,
            status=request.status,
            user_id=current_user.id,
            note=request.note
        )

        if not transaction:
            return error_response(
                code="TRANSACTION_NOT_FOUND",
                message="交易记录不存在",
                status_code=404
            )

        return success_response(
            data=TransactionResponse(**ledger_service._transaction_to_dict(transaction)),
            message="交易状态更新成功"
        )

    except Exception as e:
        return error_response(
            code="LEDGER_UPDATE_ERROR",
            message=f"更新交易状态失败: {str(e)}",
            status_code=500
        )


@router.get("/balance", response_model=StandardResponse[Optional[AccountBalanceResponse]])
async def get_account_balance(
    account_id: Optional[UUID] = Query(None, description="账户ID"),
    project_id: Optional[UUID] = Query(None, description="项目ID"),
    ledger_service: LedgerService = Depends(get_ledger_service),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"]))
):
    """
    获取账户余额
    需要权限: FINANCE 或 ADMIN 或 DATA_OPERATOR
    """
    try:
        balance_data = ledger_service.get_account_balance(
            account_id=account_id,
            project_id=project_id
        )

        return success_response(
            data=AccountBalanceResponse(**balance_data) if balance_data else None,
            message="获取账户余额成功"
        )

    except Exception as e:
        return error_response(
            code="BALANCE_QUERY_ERROR",
            message=f"获取账户余额失败: {str(e)}",
            status_code=500
        )


@router.get("/projects/{project_id}/budget", response_model=StandardResponse[List[BudgetAllocationResponse]])
async def get_project_budget_allocation(
    project_id: UUID,
    ledger_service: LedgerService = Depends(get_ledger_service),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"]))
):
    """
    获取项目预算分配
    需要权限: FINANCE 或 ADMIN 或 DATA_OPERATOR
    """
    try:
        allocations = ledger_service.get_project_budget_allocation(project_id)

        return success_response(
            data=[BudgetAllocationResponse(**allocation) for allocation in allocations],
            message="获取项目预算分配成功"
        )

    except Exception as e:
        return error_response(
            code="BUDGET_QUERY_ERROR",
            message=f"获取项目预算分配失败: {str(e)}",
            status_code=500
        )


@router.post("/budget", response_model=StandardResponse[BudgetAllocationResponse])
async def create_budget_allocation(
    request: BudgetAllocationCreateRequest,
    ledger_service: LedgerService = Depends(get_ledger_service),
    current_user: User = Depends(require_role(["admin", "finance"]))
):
    """
    创建预算分配
    需要权限: FINANCE 或 ADMIN
    """
    try:
        allocation = ledger_service.create_budget_allocation(
            project_id=request.project_id,
            category=request.category,
            allocated_amount=request.allocated_amount,
            user_id=current_user.id
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

        return success_response(
            data=BudgetAllocationResponse(**response_data),
            message="预算分配创建成功"
        )

    except Exception as e:
        return error_response(
            code="BUDGET_CREATE_ERROR",
            message=f"创建预算分配失败: {str(e)}",
            status_code=500
        )


@router.get("/statistics", response_model=StandardResponse[Dict[str, Any]])
async def get_transaction_statistics(
    project_id: Optional[UUID] = Query(None, description="项目ID"),
    account_id: Optional[UUID] = Query(None, description="账户ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    ledger_service: LedgerService = Depends(get_ledger_service),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"]))
):
    """
    获取交易统计信息
    需要权限: FINANCE 或 ADMIN 或 DATA_OPERATOR
    """
    try:
        statistics = ledger_service.get_transaction_statistics(
            project_id=project_id,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date
        )

        return success_response(data=statistics, message="获取交易统计成功")

    except Exception as e:
        return error_response(
            code="STATISTICS_QUERY_ERROR",
            message=f"获取交易统计失败: {str(e)}",
            status_code=500
        )


@router.get("/export", response_model=StandardResponse[Dict[str, Any]])
async def export_transactions(
    project_id: Optional[UUID] = Query(None, description="项目ID"),
    account_id: Optional[UUID] = Query(None, description="账户ID"),
    transaction_type: Optional[TransactionType] = Query(None, description="交易类型"),
    status: Optional[TransactionStatus] = Query(None, description="交易状态"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    format: str = Query("csv", pattern="^(csv|excel)$", description="导出格式"),
    request: Request = None,
    ledger_service: LedgerService = Depends(get_ledger_service),
    current_user: User = Depends(require_role(["admin", "finance"]))
):
    """
    导出交易记录
    需要权限: FINANCE 或 ADMIN
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

        return success_response(
            data={
                "download_url": f"/api/v1/ledger/download/transactions/{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}",
                "total_records": result.total,
                "format": format,
                "generated_at": datetime.now().isoformat()
            },
            message="交易记录导出任务已创建"
        )

    except Exception as e:
        return error_response(
            code="EXPORT_ERROR",
            message=f"导出交易记录失败: {str(e)}",
            status_code=500
        )