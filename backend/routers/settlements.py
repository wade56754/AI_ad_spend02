"""
结算 API 路由 (重构版)

SoT References:
- API_SOT.md v9.3 §6 Settlements API
- DATA_SCHEMA.md v5.3 (settlements 表)
- STATE_MACHINE.md v2.6 §4 结算状态机
- LEDGER_SOT.md v1.1 (结算账本分录)
- MASTER.md v4.4 §2.4 (7角色模型)
- ERROR_CODES_SOT.md v2.1 (错误码)

端点列表 (10 个):
- POST   /settlements                  - 创建结算单
- GET    /settlements                  - 获取结算列表
- GET    /settlements/statistics       - 获取结算统计
- GET    /settlements/overdue          - 获取逾期结算
- GET    /settlements/{id}             - 获取结算详情
- PUT    /settlements/{id}             - 更新结算
- POST   /settlements/{id}/submit      - 提交审批
- POST   /settlements/{id}/approve     - 审批通过/拒绝
- POST   /settlements/{id}/pay         - 标记付款
- POST   /settlements/{id}/cancel      - 取消结算

状态机 (5状态):
- draft → pending → approved → paid
- draft/pending/approved → cancelled

权限矩阵 (MASTER.md v4.4 §2.4 - 7角色模型):
- admin: 全部操作 (包括审批、取消)
- finance: 创建、查看、提交、记录付款
- ceo, project_owner: 查看自己项目的结算
- 其他角色: 无权访问

依赖代码块:
- response-envelope: success_response, error_response
- pagination: 分页查询
- state-machine: 状态流转
- ledger-entry: 账本分录
- audit-log: 审计日志
- error-codes: PERM-001, RES-001, BIZ-001, BIZ-002, SYS-500

Version: 2.0
Author: Claude Code
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.response import success_response, error_response, paginated_response
from backend.core.dependencies import get_current_user, require_role
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

logger = logging.getLogger(__name__)


# ========================================
# 错误响应辅助函数
# ========================================

def _handle_service_exception(e: Exception, context: str = "操作"):
    """处理服务层异常，转换为标准响应"""
    if isinstance(e, PermissionDeniedError):
        return error_response(
            code="PERM-001",
            message=str(e),
            status_code=403
        )
    elif isinstance(e, ResourceNotFoundError):
        return error_response(
            code="RES-001",
            message=str(e),
            status_code=404
        )
    elif isinstance(e, ResourceConflictError):
        return error_response(
            code="BIZ-002",
            message=str(e),
            status_code=409
        )
    elif isinstance(e, BusinessLogicError):
        return error_response(
            code="BIZ-001",
            message=str(e),
            status_code=400
        )
    else:
        logger.exception(f"服务异常 - {context}: {e}")
        return error_response(
            code="SYS-500",
            message=f"系统内部错误: {str(e)}",
            status_code=500
        )

router = APIRouter(prefix="/settlements", tags=["Settlements"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_settlement(
    request: SettlementCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "finance"]))
):
    """
    创建结算

    权限 (MASTER.md v4.4 §2.4): admin, finance

    业务规则:
    - 自动汇总该月已锁定日报
    - 计算: total_revenue = conversions × unit_price
    - 计算: settlement_amount = total_revenue - total_spend
    """
    try:
        service = SettlementService(db)
        settlement = service.create_settlement(
            request=request,
            current_user_id=current_user.id,
            current_user_role=current_user.role
        )
        return success_response(data=settlement, message="结算创建成功")
    except Exception as e:
        return _handle_service_exception(e, "创建结算")


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
    current_user: dict = Depends(require_role(["admin", "finance"]))
):
    """
    获取结算列表

    权限 (MASTER.md v4.4 §2.4): admin, finance
    """
    try:
        service = SettlementService(db)
        settlements, total = service.get_settlements(
            current_user_id=current_user.id,
            current_user_role=current_user.role,
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
    except Exception as e:
        return _handle_service_exception(e, "获取结算列表")


@router.get("/statistics", response_model=dict)
async def get_settlement_statistics(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "finance"]))
):
    """
    获取结算统计信息

    权限 (MASTER.md v4.4 §2.4): admin, finance
    """
    try:
        service = SettlementService(db)
        stats = service.get_settlement_statistics(
            current_user_id=current_user.id,
            current_user_role=current_user.role,
            start_date=start_date,
            end_date=end_date
        )
        return success_response(data=stats, message="获取统计信息成功")
    except Exception as e:
        return _handle_service_exception(e, "获取结算统计")


@router.get("/overdue", response_model=dict)
async def get_overdue_settlements(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "finance"]))
):
    """
    获取逾期结算列表

    权限 (MASTER.md v4.4 §2.4): admin, finance
    """
    try:
        service = SettlementService(db)
        settlements = service.get_overdue_settlements(
            current_user_id=current_user.id,
            current_user_role=current_user.role
        )
        return success_response(data=settlements, message="获取逾期结算成功")
    except Exception as e:
        return _handle_service_exception(e, "获取逾期结算")


@router.get("/{settlement_id}", response_model=dict)
async def get_settlement(
    settlement_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "finance"]))
):
    """
    获取结算详情

    权限 (MASTER.md v4.4 §2.4): admin, finance
    """
    try:
        service = SettlementService(db)
        settlement = service.get_settlement(
            settlement_id=settlement_id,
            current_user_id=current_user.id,
            current_user_role=current_user.role
        )
        return success_response(data=settlement, message="获取结算成功")
    except Exception as e:
        return _handle_service_exception(e, "获取结算详情")


@router.put("/{settlement_id}", response_model=dict)
async def update_settlement(
    settlement_id: int,
    request: SettlementUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "finance"]))
):
    """
    更新结算

    权限 (MASTER.md v4.4 §2.4): admin, finance
    约束：只能更新 DRAFT 或 REJECTED 状态的结算
    """
    try:
        service = SettlementService(db)
        settlement = service.update_settlement(
            settlement_id=settlement_id,
            request=request,
            current_user_id=current_user.id,
            current_user_role=current_user.role
        )
        return success_response(data=settlement, message="结算更新成功")
    except Exception as e:
        return _handle_service_exception(e, "更新结算")


@router.post("/{settlement_id}/submit", response_model=dict)
async def submit_settlement(
    settlement_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "finance"]))
):
    """
    提交结算审批

    权限 (MASTER.md v4.4 §2.4): admin, finance
    状态流转 (STATE_MACHINE.md v2.6): DRAFT -> PENDING
    """
    try:
        service = SettlementService(db)
        settlement = service.submit_settlement(
            settlement_id=settlement_id,
            current_user_id=current_user.id,
            current_user_role=current_user.role
        )
        return success_response(data=settlement, message="结算已提交审批")
    except Exception as e:
        return _handle_service_exception(e, "提交结算审批")


@router.post("/{settlement_id}/approve", response_model=dict)
async def approve_settlement(
    settlement_id: int,
    request: SettlementApproveRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["admin"]))
):
    """
    审批结算

    权限 (MASTER.md v4.4 §2.4): admin only
    状态流转 (STATE_MACHINE.md v2.6): PENDING -> APPROVED / REJECTED
    """
    try:
        service = SettlementService(db)
        settlement = service.approve_settlement(
            settlement_id=settlement_id,
            request=request,
            current_user_id=current_user.id,
            current_user_role=current_user.role
        )
        action_msg = "审批通过" if request.action == "approve" else "已拒绝"
        return success_response(data=settlement, message=f"结算{action_msg}")
    except Exception as e:
        return _handle_service_exception(e, "审批结算")


@router.post("/{settlement_id}/pay", response_model=dict)
async def record_payment(
    settlement_id: int,
    request: SettlementPaymentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["admin", "finance"]))
):
    """
    记录结算支付

    权限 (MASTER.md v4.4 §2.4): admin, finance
    约束：只能对 APPROVED 或 PROCESSING 状态的结算记录支付
    账本 (LEDGER_SOT.md v1.1): 生成 COST / TRANSFER_OUT 分录
    """
    try:
        service = SettlementService(db)
        settlement = service.record_payment(
            settlement_id=settlement_id,
            request=request,
            current_user_id=current_user.id,
            current_user_role=current_user.role
        )
        return success_response(data=settlement, message="支付记录成功")
    except Exception as e:
        return _handle_service_exception(e, "记录支付")


@router.post("/{settlement_id}/cancel", response_model=dict)
async def cancel_settlement(
    settlement_id: int,
    reason: Optional[str] = Query(None, description="取消原因"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(["admin"]))
):
    """
    取消结算

    权限 (MASTER.md v4.4 §2.4): admin only
    状态流转 (STATE_MACHINE.md v2.6): DRAFT/PENDING/APPROVED -> CANCELLED
    """
    try:
        service = SettlementService(db)
        settlement = service.cancel_settlement(
            settlement_id=settlement_id,
            current_user_id=current_user.id,
            current_user_role=current_user.role,
            reason=reason
        )
        return success_response(data=settlement, message="结算已取消")
    except Exception as e:
        return _handle_service_exception(e, "取消结算")
