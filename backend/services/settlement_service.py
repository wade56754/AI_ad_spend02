"""
结算业务逻辑层 (重构版)

SoT References:
- DATA_SCHEMA.md v5.3 (settlements 表)
- API_SOT.md v9.3 §6 Settlements API
- STATE_MACHINE.md v2.6 §4 结算状态机
- LEDGER_SOT.md v1.1 (结算账本分录)
- MASTER.md v4.4 §2.4 (7角色模型)
- BUSINESS_RULES.md v3.2 (结算约束)

状态机 (5状态):
- draft → pending → approved → paid
- draft/pending/approved → cancelled

依赖代码块:
- state-machine: 状态流转验证
- ledger-entry: 账本分录 (付款时)
- audit-log: 审计日志
- permission-filter: 权限过滤

权限矩阵 (MASTER.md v4.4 §2.4):
- admin: 全部操作 (包括审批、取消)
- finance: 创建、查看、提交、记录付款
- ceo, project_owner: 查看自己项目的结算
- 其他角色: 无权访问

Version: 2.0
Author: Claude Code
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
import uuid

from sqlalchemy import func, desc, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError
)
from backend.schemas.settlement import (
    SettlementCreateRequest,
    SettlementUpdateRequest,
    SettlementApproveRequest,
    SettlementPaymentRequest,
    SettlementStatus,
    SettlementType,
    PaymentStatus,
)

# TODO: Import actual Settlement model when created
# from backend.models import Settlement, Supplier, User, DailyReport


class SettlementService:
    """结算管理服务类"""

    # 允许的状态流转（按 STATE_MACHINE.md v2.6）
    ALLOWED_TRANSITIONS = {
        SettlementStatus.DRAFT: [SettlementStatus.PENDING, SettlementStatus.CANCELLED],
        SettlementStatus.PENDING: [SettlementStatus.APPROVED, SettlementStatus.REJECTED],
        SettlementStatus.APPROVED: [SettlementStatus.PROCESSING, SettlementStatus.CANCELLED],
        SettlementStatus.PROCESSING: [SettlementStatus.COMPLETED],
        SettlementStatus.COMPLETED: [],  # 终态
        SettlementStatus.CANCELLED: [],  # 终态
        SettlementStatus.REJECTED: [SettlementStatus.DRAFT],  # 可重新编辑
    }

    def __init__(self, db: Session):
        self.db = db

    def _generate_settlement_no(self, settlement_type: SettlementType) -> str:
        """生成结算单号"""
        prefix_map = {
            SettlementType.SUPPLIER_PAYMENT: "SP",
            SettlementType.CLIENT_BILLING: "CB",
            SettlementType.INTERNAL_TRANSFER: "IT",
            SettlementType.REFUND: "RF",
        }
        prefix = prefix_map.get(settlement_type, "ST")
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = uuid.uuid4().hex[:6].upper()
        return f"{prefix}-{timestamp}-{random_suffix}"

    def _validate_status_transition(
        self,
        current_status: SettlementStatus,
        new_status: SettlementStatus
    ) -> bool:
        """验证状态流转是否合法"""
        allowed = self.ALLOWED_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            raise BusinessLogicError(
                f"无效的状态流转: {current_status.value} -> {new_status.value}"
            )
        return True

    def create_settlement(
        self,
        request: SettlementCreateRequest,
        current_user_id: int,
        current_user_role: str
    ) -> Dict[str, Any]:
        """
        创建结算

        权限：admin, finance
        """
        if current_user_role not in ["admin", "finance"]:
            raise PermissionDeniedError("只有管理员或财务可以创建结算")

        # 验证供应商/客户ID
        if request.settlement_type == SettlementType.SUPPLIER_PAYMENT:
            if not request.supplier_id:
                raise BusinessLogicError("供应商结算必须指定供应商ID")
            # TODO: Verify supplier exists
        elif request.settlement_type == SettlementType.CLIENT_BILLING:
            if not request.client_id:
                raise BusinessLogicError("客户账单必须指定客户ID")
            # TODO: Verify client exists

        # 生成结算单号
        settlement_no = self._generate_settlement_no(request.settlement_type)

        # 计算基础货币金额
        amount_in_base = request.amount * request.exchange_rate

        # TODO: Replace with actual model creation
        settlement_data = {
            "id": 1,  # placeholder
            "settlement_no": settlement_no,
            "settlement_type": request.settlement_type.value,
            "supplier_id": request.supplier_id,
            "client_id": request.client_id,
            "period_start": request.period_start.isoformat(),
            "period_end": request.period_end.isoformat(),
            "currency": request.currency,
            "amount": str(request.amount),
            "exchange_rate": str(request.exchange_rate),
            "amount_in_base_currency": str(amount_in_base),
            "due_date": request.due_date.isoformat() if request.due_date else None,
            "status": SettlementStatus.DRAFT.value,
            "payment_status": PaymentStatus.UNPAID.value,
            "paid_amount": "0",
            "description": request.description,
            "reference_ids": request.reference_ids,
            "extra_metadata": request.extra_metadata,  # NOTE: ORM 属性名，对应 DB 列 "metadata"
            "created_by": current_user_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        return settlement_data

    def get_settlements(
        self,
        current_user_id: int,
        current_user_role: str,
        page: int = 1,
        page_size: int = 20,
        settlement_type: Optional[str] = None,
        status: Optional[str] = None,
        payment_status: Optional[str] = None,
        supplier_id: Optional[int] = None,
        client_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取结算列表

        权限：admin, finance 可查看所有
        """
        if current_user_role not in ["admin", "finance"]:
            raise PermissionDeniedError("只有管理员或财务可以查看结算列表")

        # TODO: Replace with actual model query
        # query = self.db.query(Settlement)
        #
        # if settlement_type:
        #     query = query.filter(Settlement.settlement_type == settlement_type)
        # if status:
        #     query = query.filter(Settlement.status == status)
        # if payment_status:
        #     query = query.filter(Settlement.payment_status == payment_status)
        # if supplier_id:
        #     query = query.filter(Settlement.supplier_id == supplier_id)
        # if client_id:
        #     query = query.filter(Settlement.client_id == client_id)
        # if start_date:
        #     query = query.filter(Settlement.period_start >= start_date)
        # if end_date:
        #     query = query.filter(Settlement.period_end <= end_date)
        #
        # total = query.count()
        # settlements = query.order_by(desc(Settlement.created_at)).offset(
        #     (page - 1) * page_size
        # ).limit(page_size).all()

        return [], 0

    def get_settlement(
        self,
        settlement_id: int,
        current_user_id: int,
        current_user_role: str
    ) -> Dict[str, Any]:
        """
        获取结算详情

        权限：admin, finance
        """
        if current_user_role not in ["admin", "finance"]:
            raise PermissionDeniedError("只有管理员或财务可以查看结算详情")

        # TODO: Replace with actual model query
        # settlement = self.db.query(Settlement).filter(Settlement.id == settlement_id).first()
        # if not settlement:
        #     raise ResourceNotFoundError(f"结算 {settlement_id} 不存在")
        # return settlement

        raise ResourceNotFoundError(f"结算 {settlement_id} 不存在 (model not implemented)")

    def update_settlement(
        self,
        settlement_id: int,
        request: SettlementUpdateRequest,
        current_user_id: int,
        current_user_role: str
    ) -> Dict[str, Any]:
        """
        更新结算

        权限：admin, finance
        约束：只能更新 DRAFT 或 REJECTED 状态的结算
        """
        if current_user_role not in ["admin", "finance"]:
            raise PermissionDeniedError("只有管理员或财务可以更新结算")

        settlement = self.get_settlement(settlement_id, current_user_id, current_user_role)

        # 检查是否可编辑
        # if settlement.status not in [SettlementStatus.DRAFT, SettlementStatus.REJECTED]:
        #     raise BusinessLogicError(f"结算状态为 {settlement.status}，无法编辑")

        # 如果更新状态，验证状态流转
        if request.status:
            self._validate_status_transition(
                SettlementStatus(settlement.get("status")),
                request.status
            )

        # TODO: Replace with actual model update
        raise ResourceNotFoundError(f"结算 {settlement_id} 不存在 (model not implemented)")

    def submit_settlement(
        self,
        settlement_id: int,
        current_user_id: int,
        current_user_role: str
    ) -> Dict[str, Any]:
        """
        提交结算审批

        权限：admin, finance
        状态流转：DRAFT -> PENDING
        """
        if current_user_role not in ["admin", "finance"]:
            raise PermissionDeniedError("只有管理员或财务可以提交结算")

        settlement = self.get_settlement(settlement_id, current_user_id, current_user_role)

        # self._validate_status_transition(
        #     SettlementStatus(settlement.status),
        #     SettlementStatus.PENDING
        # )

        # TODO: Update settlement status
        raise ResourceNotFoundError(f"结算 {settlement_id} 不存在 (model not implemented)")

    def approve_settlement(
        self,
        settlement_id: int,
        request: SettlementApproveRequest,
        current_user_id: int,
        current_user_role: str
    ) -> Dict[str, Any]:
        """
        审批结算

        权限：admin only
        状态流转：PENDING -> APPROVED / REJECTED
        """
        if current_user_role != "admin":
            raise PermissionDeniedError("只有管理员可以审批结算")

        settlement = self.get_settlement(settlement_id, current_user_id, current_user_role)

        new_status = SettlementStatus.APPROVED if request.action == "approve" else SettlementStatus.REJECTED

        # self._validate_status_transition(
        #     SettlementStatus(settlement.status),
        #     new_status
        # )

        # TODO: Update settlement with approval info
        raise ResourceNotFoundError(f"结算 {settlement_id} 不存在 (model not implemented)")

    def record_payment(
        self,
        settlement_id: int,
        request: SettlementPaymentRequest,
        current_user_id: int,
        current_user_role: str
    ) -> Dict[str, Any]:
        """
        记录结算支付

        权限：admin, finance
        约束：只能对 APPROVED 或 PROCESSING 状态的结算记录支付
        按 LEDGER_SOT.md v1.1 生成账本分录
        """
        if current_user_role not in ["admin", "finance"]:
            raise PermissionDeniedError("只有管理员或财务可以记录支付")

        settlement = self.get_settlement(settlement_id, current_user_id, current_user_role)

        # 验证状态
        # if settlement.status not in [SettlementStatus.APPROVED, SettlementStatus.PROCESSING]:
        #     raise BusinessLogicError(f"结算状态为 {settlement.status}，无法记录支付")

        # 验证支付金额
        # remaining = settlement.amount - settlement.paid_amount
        # if request.paid_amount > remaining:
        #     raise BusinessLogicError(f"支付金额超过剩余应付金额 {remaining}")

        # TODO: Record payment and create ledger entry
        # 按 LEDGER_SOT.md v1.1 生成 COST / TRANSFER_OUT 分录

        raise ResourceNotFoundError(f"结算 {settlement_id} 不存在 (model not implemented)")

    def cancel_settlement(
        self,
        settlement_id: int,
        current_user_id: int,
        current_user_role: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        取消结算

        权限：admin
        状态流转：DRAFT/APPROVED -> CANCELLED
        """
        if current_user_role != "admin":
            raise PermissionDeniedError("只有管理员可以取消结算")

        settlement = self.get_settlement(settlement_id, current_user_id, current_user_role)

        # self._validate_status_transition(
        #     SettlementStatus(settlement.status),
        #     SettlementStatus.CANCELLED
        # )

        # TODO: Update settlement status to CANCELLED
        raise ResourceNotFoundError(f"结算 {settlement_id} 不存在 (model not implemented)")

    def get_settlement_statistics(
        self,
        current_user_id: int,
        current_user_role: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取结算统计信息

        权限：admin, finance
        """
        if current_user_role not in ["admin", "finance"]:
            raise PermissionDeniedError("只有管理员或财务可以查看结算统计")

        # TODO: Replace with actual model query
        return {
            "total_settlements": 0,
            "pending_settlements": 0,
            "completed_settlements": 0,
            "total_amount": Decimal("0"),
            "total_paid": Decimal("0"),
            "total_unpaid": Decimal("0"),
            "overdue_count": 0,
            "overdue_amount": Decimal("0"),
            "by_type": [],
            "by_status": [],
        }

    def get_settlement_by_supplier(
        self,
        supplier_id: int,
        current_user_id: int,
        current_user_role: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取供应商的结算列表

        权限：admin, finance
        """
        return self.get_settlements(
            current_user_id=current_user_id,
            current_user_role=current_user_role,
            page=page,
            page_size=page_size,
            supplier_id=supplier_id
        )

    def get_overdue_settlements(
        self,
        current_user_id: int,
        current_user_role: str
    ) -> List[Dict[str, Any]]:
        """
        获取逾期结算列表

        权限：admin, finance
        """
        if current_user_role not in ["admin", "finance"]:
            raise PermissionDeniedError("只有管理员或财务可以查看逾期结算")

        # TODO: Query settlements where due_date < today and payment_status != PAID
        return []
