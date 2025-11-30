"""
供应商（户商）业务逻辑层
Version: 1.0
Author: Claude Code (full_pipeline)

Aligned with SoT:
- DATA_SCHEMA.md v5.2 (supplier entity)
- BUSINESS_RULES.md v3.1 (supplier constraints)
- LEDGER_SOT.md v1.1 (cost-side ledger entries)
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy import func, desc
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from backend.core.response import success_response, error_response, paginated_response
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError
)
from backend.schemas.supplier import (
    SupplierCreateRequest,
    SupplierUpdateRequest,
    SupplierStatus,
)

# TODO: Import actual Supplier model when created
# from backend.models import Supplier, User, AdAccount


class SupplierService:
    """供应商管理服务类"""

    def __init__(self, db: Session):
        self.db = db

    def create_supplier(
        self,
        request: SupplierCreateRequest,
        current_user_id: int,
        current_user_role: str
    ) -> Dict[str, Any]:
        """
        创建供应商

        权限：admin, finance
        """
        if current_user_role not in ["admin", "finance"]:
            raise PermissionDeniedError("只有管理员或财务可以创建供应商")

        # 检查供应商名称是否已存在
        # TODO: Replace with actual model query
        # if self.db.query(Supplier).filter(Supplier.name == request.name).first():
        #     raise ResourceConflictError(f"供应商名称 '{request.name}' 已存在")

        # 创建供应商
        # TODO: Replace with actual model creation
        supplier_data = {
            "id": 1,  # placeholder
            "name": request.name,
            "contact_name": request.contact_name,
            "contact_email": request.contact_email,
            "contact_phone": request.contact_phone,
            "base_currency": request.base_currency,
            "payment_method": request.payment_method.value,
            "payment_terms": request.payment_terms,
            "bank_info": request.bank_info,
            "tax_id": request.tax_id,
            "address": request.address,
            "country": request.country,
            "status": SupplierStatus.ACTIVE.value,
            "notes": request.notes,
            "extra_metadata": request.extra_metadata,  # NOTE: ORM 属性名，对应 DB 列 "metadata"
            "created_by": current_user_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "total_accounts": 0,
            "total_spend": Decimal("0"),
        }

        return supplier_data

    def get_suppliers(
        self,
        current_user_id: int,
        current_user_role: str,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        country: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取供应商列表

        权限：admin, finance, account_manager 可查看所有
        """
        # TODO: Replace with actual model query
        # query = self.db.query(Supplier)
        #
        # if status:
        #     query = query.filter(Supplier.status == status)
        # if country:
        #     query = query.filter(Supplier.country == country)
        # if search:
        #     query = query.filter(Supplier.name.ilike(f"%{search}%"))
        #
        # total = query.count()
        # suppliers = query.order_by(desc(Supplier.created_at)).offset(
        #     (page - 1) * page_size
        # ).limit(page_size).all()

        # Placeholder return
        return [], 0

    def get_supplier(
        self,
        supplier_id: int,
        current_user_id: int,
        current_user_role: str
    ) -> Dict[str, Any]:
        """
        获取供应商详情

        权限：admin, finance, account_manager
        """
        # TODO: Replace with actual model query
        # supplier = self.db.query(Supplier).filter(Supplier.id == supplier_id).first()
        # if not supplier:
        #     raise ResourceNotFoundError(f"供应商 {supplier_id} 不存在")
        #
        # # 计算统计信息
        # total_accounts = self.db.query(func.count(AdAccount.id)).filter(
        #     AdAccount.supplier_id == supplier_id
        # ).scalar() or 0
        #
        # return supplier

        raise ResourceNotFoundError(f"供应商 {supplier_id} 不存在 (model not implemented)")

    def update_supplier(
        self,
        supplier_id: int,
        request: SupplierUpdateRequest,
        current_user_id: int,
        current_user_role: str
    ) -> Dict[str, Any]:
        """
        更新供应商

        权限：admin, finance
        """
        if current_user_role not in ["admin", "finance"]:
            raise PermissionDeniedError("只有管理员或财务可以更新供应商")

        supplier = self.get_supplier(supplier_id, current_user_id, current_user_role)

        # TODO: Replace with actual model update
        # update_data = request.model_dump(exclude_unset=True)
        # for field, value in update_data.items():
        #     if hasattr(supplier, field):
        #         setattr(supplier, field, value)
        #
        # supplier.updated_at = datetime.utcnow()
        # self.db.commit()
        # return supplier

        raise ResourceNotFoundError(f"供应商 {supplier_id} 不存在 (model not implemented)")

    def delete_supplier(
        self,
        supplier_id: int,
        current_user_id: int,
        current_user_role: str
    ) -> bool:
        """
        删除供应商

        权限：admin only
        约束：不能删除有关联账户的供应商
        """
        if current_user_role != "admin":
            raise PermissionDeniedError("只有管理员可以删除供应商")

        supplier = self.get_supplier(supplier_id, current_user_id, current_user_role)

        # TODO: Check for associated accounts
        # associated_accounts = self.db.query(AdAccount).filter(
        #     AdAccount.supplier_id == supplier_id
        # ).count()
        # if associated_accounts > 0:
        #     raise BusinessLogicError(f"供应商下还有 {associated_accounts} 个关联账户，无法删除")

        # TODO: Replace with actual model deletion
        # self.db.delete(supplier)
        # self.db.commit()

        return True

    def get_supplier_statistics(
        self,
        current_user_id: int,
        current_user_role: str
    ) -> Dict[str, Any]:
        """
        获取供应商统计信息

        权限：admin, finance
        """
        # TODO: Replace with actual model query
        # stats = self.db.query(
        #     func.count(Supplier.id).label('total_suppliers'),
        #     func.count(case((Supplier.status == 'active', 1))).label('active_suppliers'),
        # ).first()

        return {
            "total_suppliers": 0,
            "active_suppliers": 0,
            "inactive_suppliers": 0,
            "total_accounts_managed": 0,
            "total_spend": Decimal("0"),
            "currency_distribution": [],
            "payment_method_distribution": [],
        }

    def get_supplier_accounts(
        self,
        supplier_id: int,
        current_user_id: int,
        current_user_role: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取供应商关联的广告账户

        权限：admin, finance, account_manager
        """
        # Verify supplier exists
        self.get_supplier(supplier_id, current_user_id, current_user_role)

        # TODO: Replace with actual model query
        # query = self.db.query(AdAccount).filter(AdAccount.supplier_id == supplier_id)
        # total = query.count()
        # accounts = query.offset((page - 1) * page_size).limit(page_size).all()

        return [], 0

    def get_supplier_ledger_summary(
        self,
        supplier_id: int,
        current_user_id: int,
        current_user_role: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取供应商的账本汇总（成本侧）

        权限：admin, finance
        按 LEDGER_SOT.md v1.1 规范，汇总 COST / TRANSFER_OUT 等分录类型
        """
        if current_user_role not in ["admin", "finance"]:
            raise PermissionDeniedError("只有管理员或财务可以查看供应商账本汇总")

        # Verify supplier exists
        self.get_supplier(supplier_id, current_user_id, current_user_role)

        # TODO: Implement ledger query based on LEDGER_SOT.md v1.1
        # Query ledger_entries where supplier_id matches and entry_type in (COST, TRANSFER_OUT)

        return {
            "supplier_id": supplier_id,
            "total_cost": Decimal("0"),
            "total_transfer_out": Decimal("0"),
            "period_start": start_date,
            "period_end": end_date,
            "entry_count": 0,
        }
