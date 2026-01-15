"""
充值管理API路由 (重构版)

SoT Reference: STATE_MACHINE.md v2.6 §9 (充值状态机)
SoT Reference: LEDGER_SOT.md v1.1 (账本规则)

状态机 (7状态):
draft → pending_review → finance_approve → paid → completed
        ↓                ↓
     cancelled        rejected

依赖代码块:
- response-envelope: success_response, error_response
- pagination: get_pagination, create_paginated_response
- error-codes: ErrorCodes
- state-machine: TOPUP_STATE_MACHINE

Version: 2.0
"""

from typing import Optional, List
from datetime import date
from decimal import Decimal

import structlog
from fastapi import APIRouter, Depends, Query, Path, status, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.dependencies import get_current_user, require_role, get_client_info
from backend.core.utils.safe_access import safe_get  # BE-P0-1 修复: 安全属性访问
from backend.core.response import success_response, error_response
from backend.core.pagination import (
    get_pagination,
    PaginationParams,
    create_paginated_response,
)
from backend.core.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError,
    BusinessError,
    PermissionError,
)
from backend.models import User
from backend.schemas.topup import (
    TopupRequestCreate,
    TopupRequestResponse,
    TopupDataReviewRequest,
    TopupFinanceApprovalRequest,
    TopupMarkPaidRequest,
    TopupApprovalLogResponse,
    TopupStatisticsResponse,
    AdAccountBalance,
)
from backend.services.topup_service import TopupService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/topups", tags=["topups"])


def get_topup_service(db: Session = Depends(get_db)) -> TopupService:
    """获取充值服务实例"""
    return TopupService(db)


# ========================================
# Response Builder (ORM → Pydantic)
# ========================================


def build_topup_response(topup) -> TopupRequestResponse:
    """
    构建充值申请响应

    BE-P0-1 修复: 使用 safe_get 安全访问嵌套属性，避免 NoneType 崩溃
    SoT: MASTER.md v4.9 AH-01 - 禁止假设数据一致
    """
    # 安全获取关联属性，避免链式访问崩溃
    ad_account_name = safe_get(topup, 'ad_account', 'account_name', default='') or \
                      safe_get(topup, 'ad_account', 'account_code', default='')
    project_id = safe_get(topup, 'ad_account', 'project_id', default=0) or 0
    project_name = safe_get(topup, 'ad_account', 'project', 'name', default='')

    return TopupRequestResponse(
        id=topup.id,
        request_no=str(topup.id),
        ad_account_id=topup.ad_account_id,
        ad_account_name=ad_account_name,
        project_id=project_id,
        project_name=project_name,
        requested_amount=topup.amount or Decimal("0"),
        actual_amount=getattr(topup, "actual_amount", None),
        currency="CNY",
        urgency_level="normal",
        reason=topup.request_notes or "",
        notes=topup.request_notes or "",
        status=topup.status,
        requested_by=0,  # UUID → int placeholder
        requested_by_name=safe_get(topup, 'requester', 'username', default=''),
        data_reviewed_by=0 if topup.reviewed_by else None,
        data_reviewed_by_name=safe_get(topup, 'reviewer', 'username', default=None),
        data_reviewed_at=topup.reviewed_at,
        data_review_notes=None,
        finance_approved_by=0 if topup.approved_by else None,
        finance_approved_by_name=safe_get(topup, 'approver', 'username', default=None),
        finance_approved_at=topup.approved_at,
        finance_approve_notes=None,
        paid_at=topup.paid_at,
        completed_at=topup.completed_at,
        expected_date=None,
        payment_method=getattr(topup, "payment_method", None),
        transaction_id=getattr(topup, "transaction_id", None),
        receipt_url=getattr(topup, "receipt_url", None),
        created_at=topup.created_at,
        updated_at=topup.updated_at,
    )


# ========================================
# CRUD 端点
# ========================================


@router.get("", summary="获取充值申请列表", description="支持分页、状态筛选。权限过滤自动应用。")
async def list_topups(
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    ad_account_id: Optional[int] = Query(None, description="账户ID筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    pagination: PaginationParams = Depends(get_pagination),
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(get_current_user),
):
    """获取充值申请列表 (带分页和权限过滤)"""
    try:
        requests, total = service.get_requests(
            current_user=current_user,
            page=pagination.page,
            page_size=pagination.page_size,
            status=status_filter,
            ad_account_id=ad_account_id,
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
        )

        responses = [build_topup_response(req) for req in requests]

        return create_paginated_response(
            items=responses, total=total, pagination=pagination, message="获取充值申请列表成功"
        )

    except Exception as e:
        logger.error("list_topups_error", error=str(e))
        return error_response(code="SYS-500", message="获取列表失败", status_code=500)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="创建充值申请",
    description="创建新充值申请。初始状态: draft。",
)
async def create_topup(
    request_data: TopupRequestCreate,
    req: Request,
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(require_role(["account_manager", "pitcher"])),
):
    """创建充值申请"""
    try:
        client_ip, user_agent = get_client_info(req)

        topup = service.create_request(
            request_data, current_user, ip_address=client_ip, user_agent=user_agent
        )

        return success_response(
            data=build_topup_response(topup), message="充值申请创建成功", status_code=201
        )

    except BusinessError as e:
        return error_response(code="BIZ-201", message=str(e), status_code=400)
    except ConflictError as e:
        return error_response(code="RES-002", message=str(e), status_code=409)
    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)


@router.get("/stats", summary="获取充值状态统计")
async def get_topup_stats(
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(get_current_user),
):
    """获取各状态的统计数量"""
    try:
        stats = service.get_status_stats(current_user)
        return success_response(data=stats, message="获取统计成功")
    except Exception as e:
        logger.error("get_stats_error", error=str(e))
        return error_response(code="SYS-500", message="获取统计失败", status_code=500)


@router.get("/statistics", summary="获取充值统计详情")
async def get_statistics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(require_role(["admin", "finance", "ceo"])),
):
    """获取充值统计详情"""
    try:
        stats = service.get_statistics(current_user, start_date, end_date)
        return success_response(data=stats, message="获取统计详情成功")
    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)


@router.get("/{topup_id}", summary="获取充值申请详情")
async def get_topup(
    topup_id: int = Path(..., gt=0),
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(get_current_user),
):
    """获取充值申请详情"""
    try:
        topup = service.get_request_by_id(topup_id, current_user)
        return success_response(data=build_topup_response(topup))

    except NotFoundError as e:
        return error_response(code="RES-001", message=str(e), status_code=404)
    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)


# ========================================
# 审批流程端点 (用户请求的简化接口)
# ========================================


@router.post(
    "/{topup_id}/approve",
    summary="审批充值申请",
    description="财务审批。状态流转: finance_approve → paid",
)
async def approve_topup(
    topup_id: int = Path(..., gt=0),
    approval_data: TopupFinanceApprovalRequest = None,
    req: Request = None,
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(require_role(["finance", "admin", "ceo"])),
):
    """
    审批充值申请

    状态机流转 (STATE_MACHINE.md v2.6 §9):
    - finance_approve → paid (审批通过)
    - finance_approve → rejected (审批拒绝)
    """
    try:
        client_ip, user_agent = get_client_info(req) if req else (None, None)

        topup = service.finance_approve(
            topup_id,
            approval_data,
            current_user,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        return success_response(data=build_topup_response(topup), message="审批完成")

    except NotFoundError as e:
        return error_response(code="RES-001", message=str(e), status_code=404)
    except BusinessError as e:
        return error_response(code="STATE-400", message=str(e), status_code=400)
    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)


@router.post(
    "/{topup_id}/reject",
    summary="拒绝充值申请",
    description="拒绝充值申请。状态流转: pending_review/finance_approve → rejected",
)
async def reject_topup(
    topup_id: int = Path(..., gt=0),
    reason: str = Query(..., description="拒绝原因"),
    req: Request = None,
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(require_role(["finance", "admin", "ceo"])),
):
    """
    拒绝充值申请

    状态机流转 (STATE_MACHINE.md v2.6 §9):
    - pending_review → rejected
    - finance_approve → rejected
    """
    try:
        client_ip, user_agent = get_client_info(req) if req else (None, None)

        topup = service.reject_request(
            topup_id, current_user, reason, ip_address=client_ip, user_agent=user_agent
        )

        return success_response(data=build_topup_response(topup), message="充值申请已拒绝")

    except NotFoundError as e:
        return error_response(code="RES-001", message=str(e), status_code=404)
    except BusinessError as e:
        return error_response(code="STATE-400", message=str(e), status_code=400)
    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)


@router.post(
    "/{topup_id}/complete",
    summary="确认充值完成",
    description="确认收款入账。状态流转: paid → completed。同时创建 ledger_entry。",
)
async def complete_topup(
    topup_id: int = Path(..., gt=0),
    transaction_id: Optional[str] = Query(None, description="交易流水号（Query参数）"),
    notes: Optional[str] = Query(None, description="备注（Query参数）"),
    req: Request = None,
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(require_role(["finance", "admin", "account_manager"])),
):
    """
    确认充值完成

    状态机流转 (STATE_MACHINE.md v2.6 §9):
    - paid → completed

    业务规则 (LEDGER_SOT.md v1.1):
    - BR-FIN-005: 必须同时创建 ledger_entry
    
    支持两种参数传递方式：
    - Query 参数: transaction_id, notes
    - JSON body: 如果请求包含 JSON body，优先使用 body 中的值
    """
    try:
        client_ip, user_agent = get_client_info(req) if req else (None, None)
        
        # 尝试从 JSON body 获取参数（如果存在）
        final_transaction_id = transaction_id
        final_notes = notes
        try:
            if req:
                # FastAPI Request 对象使用 json() 方法
                body = await req.json()
                if isinstance(body, dict):
                    final_transaction_id = body.get("transaction_id") or transaction_id
                    final_notes = body.get("notes") or notes
        except Exception:
            pass  # 如果没有 JSON body，使用 Query 参数

        topup = service.confirm_paid(
            topup_id,
            current_user,
            transaction_id=final_transaction_id,
            notes=final_notes,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        return success_response(data=build_topup_response(topup), message="充值已完成，账本已更新")

    except NotFoundError as e:
        return error_response(code="RES-001", message=str(e), status_code=404)
    except BusinessError as e:
        return error_response(code="STATE-400", message=str(e), status_code=400)
    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)


# ========================================
# 其他操作端点
# ========================================


@router.put(
    "/{topup_id}/review",
    summary="数据员审核",
    description="数据员审核。状态流转: pending_review → finance_approve/rejected",
)
async def review_topup(
    topup_id: int = Path(..., gt=0),
    review_data: TopupDataReviewRequest = None,
    req: Request = None,
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(require_role(["project_owner", "admin"])),
):
    """数据员审核"""
    try:
        client_ip, user_agent = get_client_info(req) if req else (None, None)

        topup = service.data_review(
            topup_id,
            review_data,
            current_user,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        return success_response(data=build_topup_response(topup), message="审核完成")

    except NotFoundError as e:
        return error_response(code="RES-001", message=str(e), status_code=404)
    except BusinessError as e:
        return error_response(code="STATE-400", message=str(e), status_code=400)
    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)


@router.post(
    "/{topup_id}/submit",
    summary="提交充值申请",
    description="提交充值申请。状态流转: draft → pending_review。仅创建者可操作。",
)
async def submit_topup(
    topup_id: int = Path(..., gt=0),
    req: Request = None,
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(get_current_user),
):
    """提交充值申请"""
    try:
        client_ip, user_agent = get_client_info(req) if req else (None, None)

        topup = service.submit_request(
            topup_id,
            current_user,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        return success_response(data=build_topup_response(topup), message="充值申请已提交")

    except NotFoundError as e:
        return error_response(code="RES-001", message=str(e), status_code=404)
    except BusinessError as e:
        return error_response(code="STATE-400", message=str(e), status_code=400)
    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)


@router.post("/{topup_id}/cancel", summary="取消充值申请", description="取消充值申请。仅申请人或管理员可操作。")
async def cancel_topup(
    topup_id: int = Path(..., gt=0),
    reason: str = Query(..., description="取消原因"),
    req: Request = None,
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(get_current_user),
):
    """取消充值申请"""
    try:
        client_ip, user_agent = get_client_info(req) if req else (None, None)

        topup = service.cancel_request(
            topup_id, current_user, reason, ip_address=client_ip, user_agent=user_agent
        )

        return success_response(data=build_topup_response(topup), message="充值申请已取消")

    except NotFoundError as e:
        return error_response(code="RES-001", message=str(e), status_code=404)
    except BusinessError as e:
        return error_response(code="STATE-400", message=str(e), status_code=400)
    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)


@router.put(
    "/{topup_id}/pay",
    summary="标记已打款",
    description="财务标记已打款。状态流转: finance_approve → paid",
)
async def mark_paid(
    topup_id: int = Path(..., gt=0),
    paid_data: Optional[TopupMarkPaidRequest] = None,
    req: Request = None,
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(require_role(["finance"])),
):
    """标记已打款"""
    try:
        client_ip, user_agent = get_client_info(req) if req else (None, None)

        # 如果 paid_data 为 None，创建默认值
        if paid_data is None:
            paid_data = TopupMarkPaidRequest(transaction_id=None, notes=None)

        topup = service.mark_as_paid(
            topup_id,
            paid_data,
            current_user,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        return success_response(data=build_topup_response(topup), message="已标记为打款")

    except NotFoundError as e:
        return error_response(code="RES-001", message=str(e), status_code=404)
    except ConflictError as e:
        return error_response(code="RES-002", message=str(e), status_code=409)
    except BusinessError as e:
        return error_response(code="STATE-400", message=str(e), status_code=400)
    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)


@router.get("/{topup_id}/logs", summary="获取审批日志")
async def get_logs(
    topup_id: int = Path(..., gt=0),
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(get_current_user),
):
    """获取审批日志"""
    try:
        logs = service.get_approval_logs(topup_id, current_user)

        log_responses = []
        for log in logs:
            log_responses.append(
                TopupApprovalLogResponse(
                    id=log.id,
                    request_id=log.topup_request_id,
                    action=log.action,
                    actor_id=0,  # UUID placeholder
                    actor_name=log.operator.username if log.operator else "",
                    actor_role=log.operator.role if log.operator else "",
                    notes=log.comments,
                    previous_status=log.from_status,
                    new_status=log.to_status,
                    ip_address=None,
                    user_agent=None,
                    created_at=log.created_at,
                )
            )

        return success_response(data=log_responses, message="获取审批日志成功")

    except NotFoundError as e:
        return error_response(code="RES-001", message=str(e), status_code=404)
    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)


@router.get("/accounts/{account_id}/balance", summary="获取账户余额")
async def get_account_balance(
    account_id: int = Path(..., gt=0),
    service: TopupService = Depends(get_topup_service),
    current_user: User = Depends(get_current_user),
):
    """获取账户余额信息"""
    try:
        balance = service.get_account_balance(account_id, current_user)
        return success_response(data=balance, message="获取余额成功")

    except NotFoundError as e:
        return error_response(code="RES-001", message=str(e), status_code=404)
    except PermissionError as e:
        return error_response(code="PERM-001", message=str(e), status_code=403)
