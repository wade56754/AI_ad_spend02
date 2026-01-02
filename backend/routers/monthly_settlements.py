"""
月度结算 API 路由 - TASK-FIN-003 月度锁账

SoT References:
- API_SOT.md v9.0 §6.5 Monthly Settlements API
- DATA_SCHEMA.md v5.7 §3.7.1 (monthly_settlements 表)
- STATE_MACHINE.md v2.9 §13.1 (月度结算状态机)
- MASTER.md v4.8 §2.4 (CEO: 月度锁账确认)

端点列表 (10 个):
- POST   /monthly-settlements/generate       - 生成单个月度结算
- POST   /monthly-settlements/batch-generate - 批量生成月度结算
- GET    /monthly-settlements                - 获取月度结算列表
- GET    /monthly-settlements/statistics     - 获取统计信息
- GET    /monthly-settlements/{id}           - 获取结算详情
- PUT    /monthly-settlements/{id}           - 更新结算 (仅 pending)
- POST   /monthly-settlements/{id}/confirm   - 财务确认 (pending → confirmed)
- POST   /monthly-settlements/{id}/lock      - CEO 锁定 (confirmed → locked)
- POST   /monthly-settlements/{id}/reject    - 退回修正 (confirmed → pending)
- POST   /monthly-settlements/{id}/archive   - 归档 (locked → archived)
- POST   /monthly-settlements/{id}/recalculate - 重新计算 (仅 pending)

状态机 (4状态):
- pending → confirmed → locked → archived
- confirmed → pending (退回修正)

权限矩阵:
- admin: 全部操作
- ceo: 锁定、查看
- finance: 确认、退回、查看
- project_owner: 查看自己项目

Version: 1.0
Author: Claude Code (TASK-FIN-003)
"""

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.response import success_response, error_response, paginated_response
from backend.core.dependencies import get_current_user, require_role
from backend.services.monthly_settlement_service import MonthlySettlementService
from backend.schemas.monthly_settlement import (
    MonthlySettlementGenerateRequest,
    MonthlySettlementBatchGenerateRequest,
    MonthlySettlementConfirmRequest,
    MonthlySettlementLockRequest,
    MonthlySettlementRejectRequest,
    MonthlySettlementUpdateRequest,
    MonthlySettlementResponse,
    MonthlySettlementStatistics,
)
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monthly-settlements", tags=["Monthly Settlements"])


# ========================================
# 辅助函数
# ========================================


def _handle_service_exception(e: Exception, context: str = "操作"):
    """处理服务层异常，转换为标准响应"""
    if isinstance(e, PermissionDeniedError):
        return error_response(
            message=str(e),
            code="PERM-001",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    elif isinstance(e, ResourceNotFoundError):
        return error_response(
            message=str(e),
            code="RES-001",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    elif isinstance(e, ResourceConflictError):
        return error_response(
            message=str(e),
            code="BIZ-002",
            status_code=status.HTTP_409_CONFLICT,
        )
    elif isinstance(e, BusinessLogicError):
        return error_response(
            message=str(e),
            code="BIZ-001",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    else:
        logger.exception(f"月度结算{context}失败: {e}")
        return error_response(
            message=f"月度结算{context}失败",
            code="SYS-500",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _to_response(settlement) -> dict:
    """将 MonthlySettlement 转换为响应 dict"""
    return {
        "id": settlement.id,
        "project_id": settlement.project_id,
        "project_name": settlement.project.name if settlement.project else None,
        "settlement_month": settlement.settlement_month,
        "total_spend": settlement.total_spend,
        "total_conversions": settlement.total_conversions,
        "total_revenue": settlement.total_revenue,
        "gross_profit": settlement.gross_profit,
        "average_cpl": settlement.average_cpl,
        "status": settlement.status,
        "confirmed_at": settlement.confirmed_at,
        "confirmed_by": settlement.confirmed_by,
        "confirmed_by_name": (
            settlement.confirmed_by_user.full_name
            if settlement.confirmed_by_user
            else None
        ),
        "locked_at": settlement.locked_at,
        "locked_by": settlement.locked_by,
        "locked_by_name": (
            settlement.locked_by_user.full_name if settlement.locked_by_user else None
        ),
        "notes": settlement.notes,
        "created_at": settlement.created_at,
        "updated_at": settlement.updated_at,
    }


# ========================================
# 生成端点
# ========================================


@router.post(
    "/generate",
    response_model=None,
    summary="生成单个月度结算",
    description="从日报数据聚合生成单个项目的月度结算记录",
)
async def generate_settlement(
    request: MonthlySettlementGenerateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["finance", "admin"])),
):
    """
    生成单个项目的月度结算

    权限: finance, admin
    """
    try:
        service = MonthlySettlementService(db)
        settlement = service.generate_settlement(request, current_user)
        return success_response(
            data=_to_response(settlement),
            message="月度结算生成成功",
        )
    except Exception as e:
        return _handle_service_exception(e, "生成")


@router.post(
    "/batch-generate",
    response_model=None,
    summary="批量生成月度结算",
    description="为多个项目批量生成月度结算记录",
)
async def batch_generate_settlements(
    request: MonthlySettlementBatchGenerateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["finance", "admin"])),
):
    """
    批量生成月度结算

    权限: finance, admin
    """
    try:
        service = MonthlySettlementService(db)
        settlements = service.batch_generate_settlements(request, current_user)
        return success_response(
            data={
                "generated_count": len(settlements),
                "items": [_to_response(s) for s in settlements],
            },
            message=f"成功生成 {len(settlements)} 条月度结算",
        )
    except Exception as e:
        return _handle_service_exception(e, "批量生成")


# ========================================
# 查询端点
# ========================================


@router.get(
    "",
    response_model=None,
    summary="获取月度结算列表",
)
async def list_settlements(
    project_id: Optional[int] = Query(None, description="项目ID"),
    status: Optional[str] = Query(None, description="状态过滤"),
    start_month: Optional[date] = Query(None, description="开始月份"),
    end_month: Optional[date] = Query(None, description="结束月份"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["ceo", "finance", "admin", "project_owner"])),
):
    """
    获取月度结算列表

    权限: ceo, finance, admin, project_owner
    """
    try:
        service = MonthlySettlementService(db)
        settlements, total = service.list_settlements(
            project_id=project_id,
            status=status,
            start_month=start_month,
            end_month=end_month,
            page=page,
            page_size=page_size,
        )
        return paginated_response(
            items=[_to_response(s) for s in settlements],
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        return _handle_service_exception(e, "查询")


@router.get(
    "/statistics",
    response_model=None,
    summary="获取月度结算统计",
)
async def get_statistics(
    settlement_month: Optional[date] = Query(None, description="结算月份"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["ceo", "finance", "admin"])),
):
    """
    获取月度结算统计

    权限: ceo, finance, admin
    """
    try:
        service = MonthlySettlementService(db)
        stats = service.get_statistics(
            settlement_month=settlement_month,
            project_id=project_id,
        )
        return success_response(data=stats.model_dump())
    except Exception as e:
        return _handle_service_exception(e, "统计")


@router.get(
    "/{settlement_id}",
    response_model=None,
    summary="获取月度结算详情",
)
async def get_settlement(
    settlement_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["ceo", "finance", "admin", "project_owner"])),
):
    """
    获取月度结算详情

    权限: ceo, finance, admin, project_owner
    """
    try:
        service = MonthlySettlementService(db)
        settlement = service.get_by_id(settlement_id)
        if not settlement:
            return error_response(
                message=f"月度结算 {settlement_id} 不存在",
                code="RES-001",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return success_response(data=_to_response(settlement))
    except Exception as e:
        return _handle_service_exception(e, "查询")


# ========================================
# 更新端点
# ========================================


@router.put(
    "/{settlement_id}",
    response_model=None,
    summary="更新月度结算",
    description="更新月度结算 (仅 pending 状态可更新)",
)
async def update_settlement(
    settlement_id: int,
    request: MonthlySettlementUpdateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["finance", "admin"])),
):
    """
    更新月度结算

    权限: finance, admin
    仅 pending 状态可更新
    """
    try:
        service = MonthlySettlementService(db)
        settlement = service.update_settlement(settlement_id, request, current_user)
        return success_response(
            data=_to_response(settlement),
            message="月度结算更新成功",
        )
    except Exception as e:
        return _handle_service_exception(e, "更新")


@router.post(
    "/{settlement_id}/recalculate",
    response_model=None,
    summary="重新计算月度结算",
    description="从日报重新聚合数据 (仅 pending 状态)",
)
async def recalculate_settlement(
    settlement_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["finance", "admin"])),
):
    """
    重新计算月度结算

    权限: finance, admin
    仅 pending 状态可重新计算
    """
    try:
        service = MonthlySettlementService(db)
        settlement = service.recalculate_settlement(settlement_id, current_user)
        return success_response(
            data=_to_response(settlement),
            message="月度结算重新计算成功",
        )
    except Exception as e:
        return _handle_service_exception(e, "重新计算")


# ========================================
# 状态流转端点
# ========================================


@router.post(
    "/{settlement_id}/confirm",
    response_model=None,
    summary="财务确认月度结算",
    description="pending → confirmed",
)
async def confirm_settlement(
    settlement_id: int,
    request: MonthlySettlementConfirmRequest = MonthlySettlementConfirmRequest(),
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["finance", "admin"])),
):
    """
    财务确认月度结算

    权限: finance, admin
    状态: pending → confirmed
    """
    try:
        service = MonthlySettlementService(db)
        settlement = service.confirm_settlement(settlement_id, request, current_user)
        return success_response(
            data=_to_response(settlement),
            message="月度结算已确认",
        )
    except Exception as e:
        return _handle_service_exception(e, "确认")


@router.post(
    "/{settlement_id}/lock",
    response_model=None,
    summary="CEO 锁定月度结算",
    description="confirmed → locked (月度锁账)",
)
async def lock_settlement(
    settlement_id: int,
    request: MonthlySettlementLockRequest = MonthlySettlementLockRequest(),
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["ceo", "admin"])),
):
    """
    CEO 锁定月度结算

    权限: ceo, admin
    状态: confirmed → locked

    这是月度锁账的核心操作，锁定后数据不可修改 (BR-FIN-007)
    Phase 1: 可由 admin 解锁
    Phase 2: 需走冲正流程
    """
    try:
        service = MonthlySettlementService(db)
        settlement = service.lock_settlement(settlement_id, request, current_user)
        return success_response(
            data=_to_response(settlement),
            message="月度结算已锁定",
        )
    except Exception as e:
        return _handle_service_exception(e, "锁定")


@router.post(
    "/{settlement_id}/reject",
    response_model=None,
    summary="退回月度结算",
    description="confirmed → pending (退回修正)",
)
async def reject_settlement(
    settlement_id: int,
    request: MonthlySettlementRejectRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["finance", "admin"])),
):
    """
    退回月度结算

    权限: finance, admin
    状态: confirmed → pending
    """
    try:
        service = MonthlySettlementService(db)
        settlement = service.reject_settlement(settlement_id, request, current_user)
        return success_response(
            data=_to_response(settlement),
            message="月度结算已退回修正",
        )
    except Exception as e:
        return _handle_service_exception(e, "退回")


@router.post(
    "/{settlement_id}/archive",
    response_model=None,
    summary="归档月度结算",
    description="locked → archived (年度归档)",
)
async def archive_settlement(
    settlement_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin"])),
):
    """
    归档月度结算

    权限: admin
    状态: locked → archived
    """
    try:
        service = MonthlySettlementService(db)
        settlement = service.archive_settlement(settlement_id, current_user)
        return success_response(
            data=_to_response(settlement),
            message="月度结算已归档",
        )
    except Exception as e:
        return _handle_service_exception(e, "归档")
