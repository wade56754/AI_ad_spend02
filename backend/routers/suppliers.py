"""
供应商（户商）API路由
Version: 1.1 (Phase 4: 新增费率配置API)
Author: Claude Code (full_pipeline)

Aligned with SoT:
- API_SOT.md v9.0 (API conventions)
- AUTH_SPEC.md v2.0 (role-based access)
- FINANCIAL_REFACTOR_PLAN.md Phase 4 (费率配置)
"""

from decimal import Decimal
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.response import success_response, error_response, paginated_response
from backend.core.dependencies import get_current_user, require_role
from backend.services.supplier_service import SupplierService
from backend.services.fee_service import FeeService
from backend.schemas.supplier import (
    SupplierCreateRequest,
    SupplierUpdateRequest,
    SupplierResponse,
    SupplierListResponse,
    SupplierStatisticsResponse,
)
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError,
    ValidationError
)


# ========== Fee Rate Request/Response Models ==========

class FeeRateUpdateRequest(BaseModel):
    """费率更新请求"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "fee_rate": "0.10",
                "fee_type": "PERCENTAGE"
            }
        }
    )

    fee_rate: Decimal = Field(..., ge=0, le=1, description="费率 (0-1)")
    fee_type: Optional[str] = Field(None, pattern="^(PERCENTAGE|FIXED)$", description="费率类型")

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


# ========== 依赖注入函数 ==========

def get_supplier_service(db: Session = Depends(get_db)) -> SupplierService:
    """Supplier Service 依赖注入"""
    return SupplierService(db)


def get_fee_service(db: Session = Depends(get_db)) -> FeeService:
    """Fee Service 依赖注入"""
    return FeeService(db)


# ========== 供应商 CRUD 端点 ==========

@router.post("",  status_code=status.HTTP_201_CREATED)
async def create_supplier(
    request: SupplierCreateRequest,
    service: SupplierService = Depends(get_supplier_service),
    current_user: dict = Depends(require_role(["admin", "finance"]))
):
    """
    创建供应商

    权限：admin, finance
    """
    try:
        supplier = service.create_supplier(
            request=request,
            current_user_id=current_user.id,
            current_user_role=current_user.role
        )
        return success_response(data=supplier, message="供应商创建成功")
    except PermissionDeniedError as e:
        return error_response(code="AUTH_003", message=str(e), status_code=403)
    except ResourceConflictError as e:
        return error_response(code="BIZ_003", message=str(e), status_code=409)
    except BusinessLogicError as e:
        return error_response(code="BIZ_001", message=str(e), status_code=400)


@router.get("")
async def list_suppliers(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="供应商状态"),
    country: Optional[str] = Query(None, description="国家代码"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    service: SupplierService = Depends(get_supplier_service),
    current_user: dict = Depends(require_role(["admin", "finance", "account_manager"]))
):
    """
    获取供应商列表

    权限：admin, finance, account_manager
    """
    try:
        suppliers, total = service.get_suppliers(
            current_user_id=current_user.id,
            current_user_role=current_user.role,
            page=page,
            page_size=page_size,
            status=status,
            country=country,
            search=search
        )
        return paginated_response(
            items=suppliers,
            total=total,
            page=page,
            page_size=page_size
        )
    except PermissionDeniedError as e:
        return error_response(code="AUTH_003", message=str(e), status_code=403)


@router.get("/statistics")
async def get_supplier_statistics(
    service: SupplierService = Depends(get_supplier_service),
    current_user: dict = Depends(require_role(["admin", "finance"]))
):
    """
    获取供应商统计信息

    权限：admin, finance
    """
    try:
        stats = service.get_supplier_statistics(
            current_user_id=current_user.id,
            current_user_role=current_user.role
        )
        return success_response(data=stats, message="获取统计信息成功")
    except PermissionDeniedError as e:
        return error_response(code="AUTH_003", message=str(e), status_code=403)


@router.get("/{supplier_id}")
async def get_supplier(
    supplier_id: int,
    service: SupplierService = Depends(get_supplier_service),
    current_user: dict = Depends(get_current_user)
):
    """
    获取供应商详情

    权限：admin, finance, account_manager
    """
    try:
        supplier = service.get_supplier(
            supplier_id=supplier_id,
            current_user_id=current_user.id,
            current_user_role=current_user.role
        )
        return success_response(data=supplier, message="获取供应商成功")
    except ResourceNotFoundError as e:
        return error_response(code="SYS_004", message=str(e), status_code=404)
    except PermissionDeniedError as e:
        return error_response(code="AUTH_003", message=str(e), status_code=403)


@router.put("/{supplier_id}")
async def update_supplier(
    supplier_id: int,
    request: SupplierUpdateRequest,
    service: SupplierService = Depends(get_supplier_service),
    current_user: dict = Depends(get_current_user)
):
    """
    更新供应商

    权限：admin, finance
    """
    try:
        supplier = service.update_supplier(
            supplier_id=supplier_id,
            request=request,
            current_user_id=current_user.id,
            current_user_role=current_user.role
        )
        return success_response(data=supplier, message="供应商更新成功")
    except ResourceNotFoundError as e:
        return error_response(code="SYS_004", message=str(e), status_code=404)
    except PermissionDeniedError as e:
        return error_response(code="AUTH_003", message=str(e), status_code=403)
    except ResourceConflictError as e:
        return error_response(code="BIZ_003", message=str(e), status_code=409)


@router.delete("/{supplier_id}")
async def delete_supplier(
    supplier_id: int,
    service: SupplierService = Depends(get_supplier_service),
    current_user: dict = Depends(get_current_user)
):
    """
    删除供应商

    权限：admin
    约束：不能删除有关联账户的供应商
    """
    try:
        service.delete_supplier(
            supplier_id=supplier_id,
            current_user_id=current_user.id,
            current_user_role=current_user.role
        )
        return success_response(data=None, message="供应商删除成功")
    except ResourceNotFoundError as e:
        return error_response(code="SYS_004", message=str(e), status_code=404)
    except PermissionDeniedError as e:
        return error_response(code="AUTH_003", message=str(e), status_code=403)
    except BusinessLogicError as e:
        return error_response(code="BIZ_001", message=str(e), status_code=400)


@router.get("/{supplier_id}/accounts")
async def get_supplier_accounts(
    supplier_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    service: SupplierService = Depends(get_supplier_service),
    current_user: dict = Depends(get_current_user)
):
    """
    获取供应商关联的广告账户

    权限：admin, finance, account_manager
    """
    try:
        accounts, total = service.get_supplier_accounts(
            supplier_id=supplier_id,
            current_user_id=current_user.id,
            current_user_role=current_user.role,
            page=page,
            page_size=page_size
        )
        return paginated_response(
            items=accounts,
            total=total,
            page=page,
            page_size=page_size
        )
    except ResourceNotFoundError as e:
        return error_response(code="SYS_004", message=str(e), status_code=404)
    except PermissionDeniedError as e:
        return error_response(code="AUTH_003", message=str(e), status_code=403)


@router.get("/{supplier_id}/ledger-summary")
async def get_supplier_ledger_summary(
    supplier_id: int,
    start_date: Optional[date] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    service: SupplierService = Depends(get_supplier_service),
    current_user: dict = Depends(get_current_user)
):
    """
    获取供应商的账本汇总（成本侧）

    权限：admin, finance
    按 LEDGER_SOT.md v1.1 规范，汇总 COST / TRANSFER_OUT 等分录类型
    """
    try:
        summary = service.get_supplier_ledger_summary(
            supplier_id=supplier_id,
            current_user_id=current_user.id,
            current_user_role=current_user.role,
            start_date=start_date,
            end_date=end_date
        )
        return success_response(data=summary, message="获取账本汇总成功")
    except ResourceNotFoundError as e:
        return error_response(code="SYS_004", message=str(e), status_code=404)
    except PermissionDeniedError as e:
        return error_response(code="AUTH_003", message=str(e), status_code=403)


# ========== Fee Rate APIs (Phase 4) ==========

@router.get("/{supplier_id}/fee-rate")
async def get_supplier_fee_rate(
    supplier_id: int,
    service: FeeService = Depends(get_fee_service),
    current_user: dict = Depends(require_role(["admin", "finance"]))
):
    """
    获取供应商费率配置

    权限：admin, finance
    返回当前生效的费率和费率类型

    SoT Ref: FINANCIAL_REFACTOR_PLAN.md Phase 4
    """
    try:
        result = service.get_effective_fee_rate(supplier_id)
        return success_response(data=result, message="获取费率成功")
    except ResourceNotFoundError as e:
        return error_response(code="FEE_001", message=str(e), status_code=404)
    except BusinessLogicError as e:
        return error_response(code="FEE_010", message=str(e), status_code=400)


@router.put("/{supplier_id}/fee-rate")
async def update_supplier_fee_rate(
    supplier_id: int,
    request: FeeRateUpdateRequest,
    service: FeeService = Depends(get_fee_service),
    current_user: dict = Depends(require_role(["admin", "finance"]))
):
    """
    更新供应商费率

    权限：admin, finance
    费率范围：0-1 (0% - 100%)
    费率类型：PERCENTAGE (百分比) 或 FIXED (固定金额)

    SoT Ref: FINANCIAL_REFACTOR_PLAN.md Phase 4
    """
    try:
        result = service.update_fee_rate(
            supplier_id=supplier_id,
            new_rate=request.fee_rate,
            fee_type=request.fee_type,
            user_id=current_user.id
        )
        return success_response(data=result, message="费率更新成功")
    except ResourceNotFoundError as e:
        return error_response(code="FEE_001", message=str(e), status_code=404)
    except ValidationError as e:
        return error_response(code=e.error_code, message=str(e), status_code=400)
    except BusinessLogicError as e:
        return error_response(code="FEE_020", message=str(e), status_code=400)
