"""
供应商（户商）API路由
Version: 1.0
Author: Claude Code (full_pipeline)

Aligned with SoT:
- API_SOT.md v9.0 (API conventions)
- AUTH_SPEC.md v2.0 (role-based access)
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.response import success_response, error_response, paginated_response
from backend.core.dependencies import get_current_user
from backend.services.supplier_service import SupplierService
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
    ResourceConflictError
)

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    request: SupplierCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    创建供应商

    权限：admin, finance
    """
    try:
        service = SupplierService(db)
        supplier = service.create_supplier(
            request=request,
            current_user_id=current_user.get("id"),
            current_user_role=current_user.get("role")
        )
        return success_response(data=supplier, message="供应商创建成功")
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ResourceConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=dict)
async def list_suppliers(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="供应商状态"),
    country: Optional[str] = Query(None, description="国家代码"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取供应商列表

    权限：admin, finance, account_manager
    """
    try:
        service = SupplierService(db)
        suppliers, total = service.get_suppliers(
            current_user_id=current_user.get("id"),
            current_user_role=current_user.get("role"),
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/statistics", response_model=dict)
async def get_supplier_statistics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取供应商统计信息

    权限：admin, finance
    """
    try:
        service = SupplierService(db)
        stats = service.get_supplier_statistics(
            current_user_id=current_user.get("id"),
            current_user_role=current_user.get("role")
        )
        return success_response(data=stats, message="获取统计信息成功")
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/{supplier_id}", response_model=dict)
async def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取供应商详情

    权限：admin, finance, account_manager
    """
    try:
        service = SupplierService(db)
        supplier = service.get_supplier(
            supplier_id=supplier_id,
            current_user_id=current_user.get("id"),
            current_user_role=current_user.get("role")
        )
        return success_response(data=supplier, message="获取供应商成功")
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.put("/{supplier_id}", response_model=dict)
async def update_supplier(
    supplier_id: int,
    request: SupplierUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    更新供应商

    权限：admin, finance
    """
    try:
        service = SupplierService(db)
        supplier = service.update_supplier(
            supplier_id=supplier_id,
            request=request,
            current_user_id=current_user.get("id"),
            current_user_role=current_user.get("role")
        )
        return success_response(data=supplier, message="供应商更新成功")
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ResourceConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/{supplier_id}", response_model=dict)
async def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    删除供应商

    权限：admin
    约束：不能删除有关联账户的供应商
    """
    try:
        service = SupplierService(db)
        service.delete_supplier(
            supplier_id=supplier_id,
            current_user_id=current_user.get("id"),
            current_user_role=current_user.get("role")
        )
        return success_response(data=None, message="供应商删除成功")
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{supplier_id}/accounts", response_model=dict)
async def get_supplier_accounts(
    supplier_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取供应商关联的广告账户

    权限：admin, finance, account_manager
    """
    try:
        service = SupplierService(db)
        accounts, total = service.get_supplier_accounts(
            supplier_id=supplier_id,
            current_user_id=current_user.get("id"),
            current_user_role=current_user.get("role"),
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/{supplier_id}/ledger-summary", response_model=dict)
async def get_supplier_ledger_summary(
    supplier_id: int,
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取供应商的账本汇总（成本侧）

    权限：admin, finance
    按 LEDGER_SOT.md v1.1 规范，汇总 COST / TRANSFER_OUT 等分录类型
    """
    try:
        service = SupplierService(db)
        summary = service.get_supplier_ledger_summary(
            supplier_id=supplier_id,
            current_user_id=current_user.get("id"),
            current_user_role=current_user.get("role"),
            start_date=start_date,
            end_date=end_date
        )
        return success_response(data=summary, message="获取账本汇总成功")
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
