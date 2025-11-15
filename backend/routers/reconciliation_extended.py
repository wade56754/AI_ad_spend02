"""
对账流程管理API路由
处理对账批次、对账详情、差异处理等完整对账流程接口
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional
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
from models.reconciliation_extended import ReconciliationStatus, DifferenceStatus, DifferenceType
from services.reconciliation_service_extended import get_reconciliation_service_extended, ReconciliationServiceExtended


# 定义分页响应类型
class PaginatedResponse(BaseModel):
    """分页响应"""
    items: List[Any]
    total: int
    page: int
    size: int


router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])


# Pydantic模型定义
class ReconciliationBatchCreateRequest(BaseModel):
    """创建对账批次请求"""
    name: str = Field(..., description="对账批次名称")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    project_ids: Optional[List[UUID]] = Field(None, description="项目ID列表")
    description: Optional[str] = Field(None, description="描述")


class DifferenceResolveRequest(BaseModel):
    """解决差异请求"""
    resolution_note: str = Field(..., description="解决方案说明")
    adjustment_amount: Optional[Decimal] = Field(None, description="调整金额")


class ReconciliationBatchResponse(BaseModel):
    """对账批次响应"""
    id: str
    name: str
    start_date: str
    end_date: str
    status: str
    project_ids: List[str]
    description: Optional[str]
    total_records: Optional[int]
    difference_count: Optional[int]
    matched_count: Optional[int]
    error_message: Optional[str]
    created_by: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]


class ReconciliationDetailResponse(BaseModel):
    """对账详情响应"""
    id: str
    batch_id: str
    transaction_id: Optional[str]
    transaction_type: Optional[str]
    transaction_amount: Optional[float]
    external_reference: Optional[str]
    external_amount: Optional[float]
    match_status: str
    difference_amount: Optional[float]
    created_at: str
    updated_at: Optional[str]


class ReconciliationDifferenceResponse(BaseModel):
    """对账差异响应"""
    id: str
    batch_id: str
    detail_id: Optional[str]
    difference_type: str
    difference_amount: Optional[float]
    description: str
    status: str
    resolution_note: Optional[str]
    adjustment_amount: Optional[float]
    resolved_by: Optional[str]
    created_at: str
    updated_at: Optional[str]
    resolved_at: Optional[str]


class ReconciliationSummaryResponse(BaseModel):
    """对账汇总响应"""
    batch_info: ReconciliationBatchResponse
    by_difference_type: List[Dict[str, Any]]
    by_status: List[Dict[str, Any]]


# API路由定义
@router.post("/batches", response_model=StandardResponse[ReconciliationBatchResponse])
async def create_reconciliation_batch(
    request: ReconciliationBatchCreateRequest,
    reconciliation_service: ReconciliationServiceExtended = Depends(get_reconciliation_service_extended),
    current_user: User = Depends(require_role(["admin", "finance"]))
):
    """
    创建对账批次
    需要权限: RECONCILIATION_CREATE 或 ADMIN
    """
    try:
        batch = reconciliation_service.create_reconciliation_batch(
            name=request.name,
            start_date=request.start_date,
            end_date=request.end_date,
            project_ids=request.project_ids,
            description=request.description,
            user_id=current_user.id
        )

        return success_response(data=ReconciliationBatchResponse(**reconciliation_service._batch_to_dict(batch)), message="对账批次创建成功")

    except Exception as e:
        return error_response(
            code="INTERNAL_ERROR",
            message=f"创建对账批次失败: {str(e)}",
            status_code=500
        )


@router.post("/batches/{batch_id}/process", response_model=StandardResponse[ReconciliationBatchResponse])
async def process_reconciliation_batch(
    batch_id: UUID,
    reconciliation_service: ReconciliationServiceExtended = Depends(get_reconciliation_service_extended),
    current_user: User = Depends(require_role(["admin", "finance"]))
):
    """
    执行对账批次
    需要权限: RECONCILIATION_UPDATE 或 ADMIN
    """
    try:
        batch = reconciliation_service.process_reconciliation_batch(
            batch_id=batch_id,
            user_id=current_user.id
        )

        return success_response(data=ReconciliationBatchResponse(**reconciliation_service._batch_to_dict(batch)), message="对账批次执行完成")

    except ValueError as e:
        return error_response(
            code="VALIDATION_ERROR",
            message=f"参数验证失败: {str(e)}",
            status_code=400
        )
    except Exception as e:
        return error_response(
            code="INTERNAL_ERROR",
            message=f"执行对账批次失败: {str(e)}",
            status_code=500
        )


@router.get("/batches", response_model=StandardResponse[PaginatedResponse])
async def get_reconciliation_batches(
    status: Optional[ReconciliationStatus] = Query(None, description="批次状态"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"])),
    reconciliation_service: ReconciliationServiceExtended = Depends(get_reconciliation_service_extended)
):
    """
    获取对账批次列表
    需要权限: RECONCILIATION_READ
    """
    try:
        result = reconciliation_service.get_reconciliation_batches(
            status=status,
            start_date=start_date,
            end_date=end_date,
            page=page,
            size=size
        )

        return success_response(data=result, message="获取对账批次列表成功")

    except Exception as e:
        return error_response(
            code="INTERNAL_ERROR",
            message=f"获取对账批次列表失败: {str(e)}",
            status_code=500
        )


@router.get("/batches/{batch_id}/details", response_model=StandardResponse[PaginatedResponse])
async def get_reconciliation_details(
    batch_id: UUID,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"])),
    reconciliation_service: ReconciliationServiceExtended = Depends(get_reconciliation_service_extended)
):
    """
    获取对账详情列表
    需要权限: RECONCILIATION_READ
    """
    try:
        result = reconciliation_service.get_reconciliation_details(
            batch_id=batch_id,
            page=page,
            size=size
        )

        return success_response(data=result, message="获取对账详情列表成功")

    except Exception as e:
        return error_response(
            code="INTERNAL_ERROR",
            message=f"获取对账详情列表失败: {str(e)}",
            status_code=500
        )


@router.get("/differences", response_model=StandardResponse[PaginatedResponse])
async def get_reconciliation_differences(
    batch_id: Optional[UUID] = Query(None, description="批次ID"),
    status: Optional[DifferenceStatus] = Query(None, description="差异状态"),
    difference_type: Optional[DifferenceType] = Query(None, description="差异类型"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"])),
    reconciliation_service: ReconciliationServiceExtended = Depends(get_reconciliation_service_extended)
):
    """
    获取对账差异列表
    需要权限: RECONCILIATION_READ
    """
    try:
        result = reconciliation_service.get_reconciliation_differences(
            batch_id=batch_id,
            status=status,
            difference_type=difference_type,
            page=page,
            size=size
        )

        return success_response(data=result, message="获取对账差异列表成功")

    except Exception as e:
        return error_response(
            code="INTERNAL_ERROR",
            message=f"获取对账差异列表失败: {str(e)}",
            status_code=500
        )


@router.put("/differences/{difference_id}/resolve", response_model=StandardResponse[ReconciliationDifferenceResponse])
async def resolve_difference(
    difference_id: UUID,
    request: DifferenceResolveRequest,
    reconciliation_service: ReconciliationServiceExtended = Depends(get_reconciliation_service_extended),
    current_user: User = Depends(require_role(["admin", "finance"]))
):
    """
    解决对账差异
    需要权限: RECONCILIATION_UPDATE 或 ADMIN
    """
    try:
        difference = reconciliation_service.resolve_difference(
            difference_id=difference_id,
            resolution_note=request.resolution_note,
            adjustment_amount=request.adjustment_amount,
            user_id=current_user.id
        )

        if not difference:
            return error_response(
                code="NOT_FOUND",
                message="对账差异不存在",
                status_code=404
            )

        return success_response(data=ReconciliationDifferenceResponse(**reconciliation_service._difference_to_dict(difference)), message="对账差异解决成功")

    except ValueError as e:
        return error_response(
            code="VALIDATION_ERROR",
            message=f"参数验证失败: {str(e)}",
            status_code=400
        )
    except Exception as e:
        return error_response(
            code="INTERNAL_ERROR",
            message=f"解决对账差异失败: {str(e)}",
            status_code=500
        )


@router.get("/batches/{batch_id}/summary", response_model=StandardResponse[ReconciliationSummaryResponse])
async def get_reconciliation_summary(
    batch_id: UUID,
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"])),
    reconciliation_service: ReconciliationServiceExtended = Depends(get_reconciliation_service_extended)
):
    """
    获取对账汇总信息
    需要权限: RECONCILIATION_READ
    """
    try:
        summary_data = reconciliation_service.get_reconciliation_summary(batch_id)

        if not summary_data:
            return error_response(
                code="NOT_FOUND",
                message="对账批次不存在",
                status_code=404
            )

        return success_response(data=ReconciliationSummaryResponse(**summary_data), message="获取对账汇总信息成功")

    except HTTPException:
        raise
    except Exception as e:
        return error_response(
            code="INTERNAL_ERROR",
            message=f"获取对账汇总信息失败: {str(e)}",
            status_code=500
        )


@router.get("/export", response_model=StandardResponse[Dict[str, Any]])
async def export_reconciliation_data(
    batch_id: Optional[UUID] = Query(None, description="批次ID"),
    status: Optional[ReconciliationStatus] = Query(None, description="批次状态"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    format: str = Query("excel", pattern="^(csv|excel)$", description="导出格式"),
    current_user: User = Depends(require_role(["admin", "finance"])),
    request: Request = None,
    reconciliation_service: ReconciliationServiceExtended = Depends(get_reconciliation_service_extended)
):
    """
    导出对账数据
    需要权限: REPORT_EXPORT
    """
    try:
        # 获取对账批次数据
        result = reconciliation_service.get_reconciliation_batches(
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
            table_name="reconciliation_batches",
            record_count=result.total,
            filters={
                "batch_id": str(batch_id) if batch_id else None,
                "status": status.value if status else None,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            },
            request=request
        )

        return success_response(
            data={
                "download_url": f"/api/v1/reconciliation/download/batches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}",
                "total_records": result.total,
                "format": format,
                "generated_at": datetime.now().isoformat()
            },
            message="对账数据导出任务已创建"
        )

    except Exception as e:
        return error_response(
            code="INTERNAL_ERROR",
            message=f"导出对账数据失败: {str(e)}",
            status_code=500
        )


@router.get("/statistics", response_model=StandardResponse[Dict[str, Any]])
async def get_reconciliation_statistics(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"])),
    reconciliation_service: ReconciliationServiceExtended = Depends(get_reconciliation_service_extended)
):
    """
    获取对账统计信息
    需要权限: RECONCILIATION_READ
    """
    try:
        # 获取对账批次统计
        result = reconciliation_service.get_reconciliation_batches(
            start_date=start_date,
            end_date=end_date,
            page=1,
            size=10000  # 统计时获取所有数据
        )

        # 计算统计信息
        batches = result.items
        total_batches = len(batches)
        completed_batches = len([b for b in batches if b["status"] == "completed"])
        processing_batches = len([b for b in batches if b["status"] == "processing"])
        failed_batches = len([b for b in batches if b["status"] == "failed"])

        total_records = sum(b.get("total_records", 0) for b in batches)
        total_differences = sum(b.get("difference_count", 0) for b in batches)
        total_matched = sum(b.get("matched_count", 0) for b in batches)

        statistics = {
            "batch_summary": {
                "total": total_batches,
                "completed": completed_batches,
                "processing": processing_batches,
                "failed": failed_batches,
                "pending": total_batches - completed_batches - processing_batches - failed_batches
            },
            "record_summary": {
                "total_records": total_records,
                "total_differences": total_differences,
                "total_matched": total_matched,
                "match_rate": (total_matched / total_records * 100) if total_records > 0 else 0
            },
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }

        return success_response(data=statistics, message="获取对账统计信息成功")

    except Exception as e:
        return error_response(
            code="INTERNAL_ERROR",
            message=f"获取对账统计信息失败: {str(e)}",
            status_code=500
        )