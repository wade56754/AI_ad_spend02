"""
对账管理路由
Version: 2.0 (对齐 SoT STATE_MACHINE.md v2.6)
Author: Claude协作开发

对账批次状态机（5状态）：
draft → pending_review → approved/needs_adjustment → completed
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
import io
import json

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.dependencies import get_current_user, require_role
from backend.models import User
from backend.models import (
    ReconciliationBatch,
    ReconciliationDetail,
    ReconciliationAdjustment,
)

# ReconciliationReport 可能在 finance 模块或 reconciliation 模块
try:
    from backend.models.finance.reconciliation import ReconciliationReport
except ImportError:
    from backend.models.reconciliation import ReconciliationReport
from backend.schemas.reconciliation import (
    ReconciliationBatchCreateRequest,
    ReconciliationBatchResponse,
    ReconciliationBatchListResponse,
    ReconciliationDetailResponse,
    ReconciliationDetailListResponse,
    ReconciliationDetailReviewRequest,
    ReconciliationAdjustmentCreateRequest,
    ReconciliationAdjustmentResponse,
    ReconciliationStatisticsResponse,
    ReconciliationReportGenerateRequest,
    ReconciliationReportResponse,
    ReconciliationReportListResponse,
    ReconciliationExportData,
)
from backend.services.reconciliation_service import ReconciliationService
from backend.services.audit_log_service import AuditLogService
from backend.core.response import success_response, paginated_response, error_response
from backend.utils.export import export_to_excel, export_to_pdf, export_to_json
from backend.exceptions.custom_exceptions import (
    ValidationError,
    ResourceNotFoundError as NotFoundError,
    PermissionDeniedError as PermissionError,
)


# ========== 辅助函数 ==========


def _safe_get_attr(obj, attr: str, default=None):
    """安全获取对象属性"""
    try:
        return getattr(obj, attr, default)
    except Exception:
        return default


router = APIRouter(prefix="/reconciliations", tags=["对账管理"])


def get_reconciliation_service(db: Session = Depends(get_db)) -> ReconciliationService:
    """获取对账服务实例"""
    return ReconciliationService(db)


def get_audit_service(db: Session = Depends(get_db)) -> AuditLogService:
    """获取审计日志服务实例"""
    return AuditLogService(db)


@router.get("")
async def get_reconciliation_batches(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="对账状态"),
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            ["admin", "finance", "project_owner", "account_manager", "pitcher"]
        )
    ),
    service: ReconciliationService = Depends(get_reconciliation_service),
):
    """获取对账批次列表"""
    try:
        batches, total = await service.get_batches(
            page=page,
            page_size=page_size,
            status=status,
            date_from=date_from,
            date_to=date_to,
            current_user_id=current_user.id,
            user_role=current_user.role,
        )

        # 转换为响应格式
        batch_responses = []
        for batch in batches:
            batch_data = ReconciliationBatchResponse.model_validate(batch)
            # 计算匹配率和差异率
            if batch.total_accounts > 0:
                batch_data.match_rate = round(
                    (batch.matched_accounts / batch.total_accounts) * 100, 2
                )
                batch_data.difference_rate = round(
                    float(batch.total_difference / batch.total_platform_spend * 100)
                    if batch.total_platform_spend > 0
                    else 0,
                    2,
                )
            # 计算处理时长
            if batch.started_at and batch.completed_at:
                duration = batch.completed_at - batch.started_at
                batch_data.processing_duration = round(
                    duration.total_seconds() / 3600, 2
                )

            batch_responses.append(batch_data)

        return paginated_response(
            items=batch_responses, total=total, page=page, page_size=page_size
        )

    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.post("/batches")
async def create_reconciliation_batch(
    request: ReconciliationBatchCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service),
):
    """创建对账批次"""
    try:
        batch = await service.create_batch(request, current_user.id)

        # 记录审计日志
        await audit_service.log_action(
            user_id=current_user.id,
            action="create",
            resource_type="reconciliation_batch",
            resource_id=batch.id,
            details=f"创建对账批次: {batch.batch_no}",
        )

        return success_response(
            data=ReconciliationBatchResponse.model_validate(batch), message="对账批次创建成功"
        )

    except ValidationError as e:
        return error_response(code=e.error_code, message=str(e), status_code=400)
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.get("/batches/{batch_id}")
async def get_reconciliation_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            ["admin", "finance", "project_owner", "account_manager", "pitcher"]
        )
    ),
    service: ReconciliationService = Depends(get_reconciliation_service),
):
    """获取对账批次详情"""
    try:
        batch = await service.get_batch_by_id(
            batch_id, current_user.id, current_user.role
        )

        batch_data = ReconciliationBatchResponse.model_validate(batch)

        # 计算辅助字段
        if batch.total_accounts > 0:
            batch_data.match_rate = round(
                (batch.matched_accounts / batch.total_accounts) * 100, 2
            )
            batch_data.difference_rate = round(
                float(batch.total_difference / batch.total_platform_spend * 100)
                if batch.total_platform_spend > 0
                else 0,
                2,
            )

        if batch.started_at and batch.completed_at:
            duration = batch.completed_at - batch.started_at
            batch_data.processing_duration = round(duration.total_seconds() / 3600, 2)

        return success_response(data=batch_data)

    except NotFoundError as e:
        return error_response(
            code=e.error_code or "SYS_004", message=str(e), status_code=404
        )
    except PermissionError as e:
        return error_response(
            code=e.error_code or "AUTH_003", message=str(e), status_code=403
        )
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.post("/batches/{batch_id}/run")
async def run_reconciliation(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service),
):
    """执行对账"""
    try:
        batch = await service.run_reconciliation(batch_id, current_user.id)

        # 记录审计日志
        await audit_service.log_action(
            user_id=current_user.id,
            action="run",
            resource_type="reconciliation_batch",
            resource_id=batch_id,
            details=f"执行对账: {batch.batch_no}",
        )

        return success_response(
            data=ReconciliationBatchResponse.model_validate(batch), message="对账执行成功"
        )

    except ValidationError as e:
        return error_response(code=e.error_code, message=str(e), status_code=400)
    except NotFoundError as e:
        return error_response(
            code=e.error_code or "SYS_004", message=str(e), status_code=404
        )
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.get("/batches/{batch_id}/details")
async def get_reconciliation_details(
    batch_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    match_status: Optional[str] = Query(None, description="匹配状态"),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            ["admin", "finance", "project_owner", "account_manager", "pitcher"]
        )
    ),
    service: ReconciliationService = Depends(get_reconciliation_service),
):
    """获取对账详情列表"""
    try:
        details, total = await service.get_batch_details(
            batch_id=batch_id,
            page=page,
            page_size=page_size,
            match_status=match_status,
            current_user_id=current_user.id,
            user_role=current_user.role,
        )

        # 转换为响应格式
        detail_responses = []
        for detail in details:
            detail_data = ReconciliationDetailResponse.model_validate(detail)
            # 计算差异百分比
            if detail.platform_spend > 0:
                detail_data.percentage_difference = round(
                    float(detail.spend_difference / detail.platform_spend * 100), 2
                )

            # 获取用户名称
            if detail.reviewed_by:
                reviewer = db.query(User).filter(User.id == detail.reviewed_by).first()
                if reviewer:
                    detail_data.reviewed_by_name = reviewer.name

            if detail.resolved_by:
                resolver = db.query(User).filter(User.id == detail.resolved_by).first()
                if resolver:
                    detail_data.resolved_by_name = resolver.name

            detail_responses.append(detail_data)

        return paginated_response(
            items=detail_responses, total=total, page=page, page_size=page_size
        )

    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.put("/details/{detail_id}/review")
async def review_reconciliation_detail(
    detail_id: int,
    request: ReconciliationDetailReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service),
):
    """审核对账差异"""
    try:
        detail = await service.review_detail(detail_id, request, current_user.id)

        # 记录审计日志
        await audit_service.log_action(
            user_id=current_user.id,
            action="review",
            resource_type="reconciliation_detail",
            resource_id=detail_id,
            details=f"审核对账差异: {request.action}",
        )

        return success_response(
            data=ReconciliationDetailResponse.model_validate(detail), message="审核完成"
        )

    except NotFoundError as e:
        return error_response(
            code=e.error_code or "SYS_004", message=str(e), status_code=404
        )
    except ValidationError as e:
        return error_response(code=e.error_code, message=str(e), status_code=400)
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.post("/details/{detail_id}/adjust")
async def create_adjustment(
    detail_id: int,
    request: ReconciliationAdjustmentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service),
):
    """创建调整记录"""
    try:
        adjustment = await service.create_adjustment(
            detail_id, request, current_user.id
        )

        # 记录审计日志
        await audit_service.log_action(
            user_id=current_user.id,
            action="create",
            resource_type="reconciliation_adjustment",
            resource_id=adjustment.id,
            details=f"创建调整记录: {request.adjustment_amount}",
        )

        # 获取审批人名称
        approver = db.query(User).filter(User.id == adjustment.approved_by).first()
        if approver:
            adjustment_data = ReconciliationAdjustmentResponse.model_validate(
                adjustment
            )
            adjustment_data.approved_by_name = approver.name
        else:
            adjustment_data = ReconciliationAdjustmentResponse.model_validate(
                adjustment
            )

        return success_response(data=adjustment_data, message="调整记录创建成功")

    except NotFoundError as e:
        return error_response(
            code=e.error_code or "SYS_004", message=str(e), status_code=404
        )
    except ValidationError as e:
        return error_response(code=e.error_code, message=str(e), status_code=400)
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.get("/statistics")
async def get_reconciliation_statistics(
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "project_owner"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
):
    """获取对账统计信息"""
    try:
        statistics = await service.get_statistics(
            date_from=date_from,
            date_to=date_to,
            current_user_id=current_user.id,
            user_role=current_user.role,
        )

        return success_response(data=statistics)

    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.get("/export")
async def export_reconciliation_data(
    batch_id: Optional[int] = Query(None, description="批次ID"),
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    format_type: str = Query("excel", pattern="^(excel|pdf|json)$", description="导出格式"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service),
):
    """导出对账数据"""
    try:
        # 获取导出数据
        export_data = await service.export_reconciliation_data(
            batch_id=batch_id,
            date_from=date_from,
            date_to=date_to,
            format_type=format_type,
            current_user_id=current_user.id,
            user_role=current_user.role,
        )

        # 记录审计日志
        await audit_service.log_action(
            user_id=current_user.id,
            action="export",
            resource_type="reconciliation_data",
            details=f"导出对账数据: 格式={format_type}, 批次={batch_id}",
        )

        # 根据格式类型导出
        if format_type == "excel":
            file_content = export_to_excel(export_data, sheet_name="对账数据")
            filename = f"reconciliation_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
            media_type = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        elif format_type == "pdf":
            file_content = export_to_pdf(export_data, title="对账数据报表")
            filename = f"reconciliation_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            media_type = "application/pdf"
        else:  # json
            file_content = export_to_json(export_data)
            filename = f"reconciliation_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
            media_type = "application/json"

        return StreamingResponse(
            iter([file_content]),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.get("/reports")
async def get_reconciliation_reports(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    report_type: Optional[str] = Query(None, description="报告类型"),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            ["admin", "finance", "project_owner", "account_manager", "pitcher"]
        )
    ),
):
    """获取对账报告列表"""
    try:
        query = db.query(ReconciliationReport)

        # 根据角色过滤
        if current_user.role in ["account_manager", "pitcher"]:
            # TODO: 实现基于角色的数据过滤
            pass

        # 应用过滤条件
        if report_type:
            query = query.filter(ReconciliationReport.report_type == report_type)

        # 计算总数
        total = query.count()

        # 分页查询
        reports = (
            query.order_by(ReconciliationReport.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        # 转换为响应格式
        report_responses = []
        for report in reports:
            report_data = ReconciliationReportResponse.model_validate(report)
            # 获取生成人名称
            generator = db.query(User).filter(User.id == report.generated_by).first()
            if generator:
                report_data.generated_by_name = generator.name
            report_responses.append(report_data)

        return paginated_response(
            items=report_responses, total=total, page=page, page_size=page_size
        )

    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.post("/reports")
async def generate_reconciliation_report(
    request: ReconciliationReportGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service),
):
    """生成对账报告"""
    try:
        report = await service.generate_report(request, current_user.id)

        # 记录审计日志
        await audit_service.log_action(
            user_id=current_user.id,
            action="create",
            resource_type="reconciliation_report",
            resource_id=report.id,
            details=f"生成对账报告: {request.report_type}",
        )

        return success_response(
            data=ReconciliationReportResponse.model_validate(report), message="报告生成成功"
        )

    except NotFoundError as e:
        return error_response(
            code=e.error_code or "SYS_004", message=str(e), status_code=404
        )
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


# ========== 批次状态转换端点 (STATE_MACHINE.md v2.6 第16.6节) ==========


@router.put("/batches/{batch_id}/submit")
async def submit_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "project_owner"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service),
):
    """
    提交批次审核
    状态转换: draft → pending_review
    """
    try:
        batch = await service.submit_batch(batch_id, current_user.id)

        await audit_service.log_action(
            user_id=current_user.id,
            action="submit",
            resource_type="reconciliation_batch",
            resource_id=batch_id,
            details=f"提交批次审核: {batch.batch_code}",
        )

        return success_response(
            data=ReconciliationBatchResponse.model_validate(batch), message="批次已提交审核"
        )

    except ValidationError as e:
        return error_response(code=e.error_code, message=str(e), status_code=400)
    except NotFoundError as e:
        return error_response(
            code=e.error_code or "SYS_004", message=str(e), status_code=404
        )
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.put("/batches/{batch_id}/approve")
async def approve_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service),
):
    """
    批准对账批次
    状态转换: pending_review → approved
    """
    try:
        batch = await service.approve_batch(batch_id, current_user.id)

        await audit_service.log_action(
            user_id=current_user.id,
            action="approve",
            resource_type="reconciliation_batch",
            resource_id=batch_id,
            details=f"批准批次: {batch.batch_code}",
        )

        return success_response(
            data=ReconciliationBatchResponse.model_validate(batch), message="批次已批准"
        )

    except ValidationError as e:
        return error_response(code=e.error_code, message=str(e), status_code=400)
    except NotFoundError as e:
        return error_response(
            code=e.error_code or "SYS_004", message=str(e), status_code=404
        )
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.put("/batches/{batch_id}/request-adjustment")
async def request_adjustment(
    batch_id: int,
    reason: str = Query(..., min_length=1, max_length=500, description="调整原因"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service),
):
    """
    请求调整（审核不通过）
    状态转换: pending_review → needs_adjustment
    """
    try:
        batch = await service.request_adjustment(batch_id, current_user.id, reason)

        await audit_service.log_action(
            user_id=current_user.id,
            action="request_adjustment",
            resource_type="reconciliation_batch",
            resource_id=batch_id,
            details=f"请求调整批次: {batch.batch_code}, 原因: {reason}",
        )

        return success_response(
            data=ReconciliationBatchResponse.model_validate(batch), message="已请求调整"
        )

    except ValidationError as e:
        return error_response(code=e.error_code, message=str(e), status_code=400)
    except NotFoundError as e:
        return error_response(
            code=e.error_code or "SYS_004", message=str(e), status_code=404
        )
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.put("/batches/{batch_id}/resubmit")
async def resubmit_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "project_owner"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service),
):
    """
    重新提交批次（调整后）
    状态转换: needs_adjustment → pending_review
    """
    try:
        batch = await service.resubmit_batch(batch_id, current_user.id)

        await audit_service.log_action(
            user_id=current_user.id,
            action="resubmit",
            resource_type="reconciliation_batch",
            resource_id=batch_id,
            details=f"重新提交批次: {batch.batch_code}",
        )

        return success_response(
            data=ReconciliationBatchResponse.model_validate(batch), message="批次已重新提交"
        )

    except ValidationError as e:
        return error_response(code=e.error_code, message=str(e), status_code=400)
    except NotFoundError as e:
        return error_response(
            code=e.error_code or "SYS_004", message=str(e), status_code=404
        )
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.put("/batches/{batch_id}/complete")
async def complete_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service),
):
    """
    完成对账批次（终态）
    状态转换: approved → completed
    需满足完成条件
    """
    try:
        batch = await service.complete_batch(batch_id, current_user.id)

        await audit_service.log_action(
            user_id=current_user.id,
            action="complete",
            resource_type="reconciliation_batch",
            resource_id=batch_id,
            details=f"完成批次: {batch.batch_code}",
        )

        return success_response(
            data=ReconciliationBatchResponse.model_validate(batch), message="批次已完成"
        )

    except ValidationError as e:
        return error_response(code=e.error_code, message=str(e), status_code=400)
    except NotFoundError as e:
        return error_response(
            code=e.error_code or "SYS_004", message=str(e), status_code=404
        )
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.put("/batches/{batch_id}/force-complete")
async def force_complete_batch(
    batch_id: int,
    reason: str = Query(..., min_length=1, max_length=500, description="强制完成原因"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service),
):
    """
    强制完成对账批次（管理员专用）
    状态转换: any (非completed) → completed
    """
    try:
        batch = await service.force_complete_batch(batch_id, current_user.id, reason)

        await audit_service.log_action(
            user_id=current_user.id,
            action="force_complete",
            resource_type="reconciliation_batch",
            resource_id=batch_id,
            details=f"强制完成批次: {batch.batch_code}, 原因: {reason}",
        )

        return success_response(
            data=ReconciliationBatchResponse.model_validate(batch), message="批次已强制完成"
        )

    except ValidationError as e:
        return error_response(code=e.error_code, message=str(e), status_code=400)
    except NotFoundError as e:
        return error_response(
            code=e.error_code or "SYS_004", message=str(e), status_code=404
        )
    except PermissionError as e:
        return error_response(
            code=e.error_code or "AUTH_003", message=str(e), status_code=403
        )
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


# ========== 明细状态转换端点 (STATE_MACHINE.md v2.6 第16.7节) ==========


@router.put("/details/{detail_id}/confirm")
async def confirm_detail(
    detail_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "project_owner"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service),
):
    """
    确认对账明细
    状态转换: pending → confirmed
    """
    try:
        detail = await service.confirm_detail(detail_id, current_user.id)

        await audit_service.log_action(
            user_id=current_user.id,
            action="confirm",
            resource_type="reconciliation_detail",
            resource_id=detail_id,
            details="确认对账明细",
        )

        return success_response(
            data=ReconciliationDetailResponse.model_validate(detail), message="明细已确认"
        )

    except ValidationError as e:
        return error_response(code=e.error_code, message=str(e), status_code=400)
    except NotFoundError as e:
        return error_response(
            code=e.error_code or "SYS_004", message=str(e), status_code=404
        )
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.put("/details/{detail_id}/adjust")
async def adjust_detail(
    detail_id: int,
    request: ReconciliationAdjustmentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "project_owner"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service),
):
    """
    调整对账明细
    状态转换: pending → adjusted
    同时创建调整记录
    """
    try:
        detail, adjustment = await service.adjust_detail(
            detail_id,
            current_user.id,
            request.adjustment_type,
            request.adjustment_amount,
            request.adjustment_reason,
        )

        await audit_service.log_action(
            user_id=current_user.id,
            action="adjust",
            resource_type="reconciliation_detail",
            resource_id=detail_id,
            details=f"调整对账明细: 金额={request.adjustment_amount}, 原因={request.adjustment_reason}",
        )

        return success_response(
            data={
                "detail": ReconciliationDetailResponse.model_validate(detail),
                "adjustment": ReconciliationAdjustmentResponse.model_validate(
                    adjustment
                ),
            },
            message="明细已调整",
        )

    except ValidationError as e:
        return error_response(code=e.error_code, message=str(e), status_code=400)
    except NotFoundError as e:
        return error_response(
            code=e.error_code or "SYS_004", message=str(e), status_code=404
        )
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


# ========== 批次更新/删除端点 (RECONCILIATION_SOT.md §12) ==========


@router.put("/batches/{batch_id}")
async def update_batch(
    batch_id: int,
    request: ReconciliationBatchCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "project_owner"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service),
):
    """
    更新对账批次（仅 draft 状态可更新）

    权限：
    - admin/finance: 可更新所有草稿批次
    - project_owner: 仅可更新自己创建的草稿批次
    """
    try:
        batch = await service.update_batch(
            batch_id, request, current_user.id, current_user.role
        )

        await audit_service.log_action(
            user_id=current_user.id,
            action="update",
            resource_type="reconciliation_batch",
            resource_id=batch_id,
            details=f"更新对账批次: {batch.batch_code}",
        )

        return success_response(
            data=ReconciliationBatchResponse.model_validate(batch), message="批次更新成功"
        )

    except ValidationError as e:
        return error_response(code=e.error_code, message=str(e), status_code=400)
    except NotFoundError as e:
        return error_response(
            code=e.error_code or "SYS_004", message=str(e), status_code=404
        )
    except PermissionError as e:
        return error_response(
            code=e.error_code or "AUTH_003", message=str(e), status_code=403
        )
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.delete("/batches/{batch_id}")
async def delete_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service),
):
    """
    删除对账批次（仅 admin 可删除 draft 状态批次）

    业务规则 (BR-RECON-005):
    - 仅 draft 状态的批次可删除
    - completed 状态禁止删除
    """
    try:
        await service.delete_batch(batch_id, current_user.id)

        await audit_service.log_action(
            user_id=current_user.id,
            action="delete",
            resource_type="reconciliation_batch",
            resource_id=batch_id,
            details="删除对账批次",
        )

        return success_response(message="批次删除成功")

    except ValidationError as e:
        return error_response(code=e.error_code, message=str(e), status_code=400)
    except NotFoundError as e:
        return error_response(
            code=e.error_code or "SYS_004", message=str(e), status_code=404
        )
    except PermissionError as e:
        return error_response(
            code=e.error_code or "AUTH_003", message=str(e), status_code=403
        )
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


# ========== 明细单独查询端点 ==========


@router.get("/details/{detail_id}")
async def get_detail_by_id(
    detail_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "project_owner"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
):
    """获取单个对账明细详情"""
    try:
        detail = await service.get_detail_by_id(
            detail_id, current_user.id, current_user.role
        )

        return success_response(
            data=ReconciliationDetailResponse.model_validate(detail)
        )

    except NotFoundError as e:
        return error_response(
            code=e.error_code or "SYS_004", message=str(e), status_code=404
        )
    except PermissionError as e:
        return error_response(
            code=e.error_code or "AUTH_003", message=str(e), status_code=403
        )
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


# ========== 调整记录端点 ==========


@router.get("/adjustments")
async def get_adjustments(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    batch_id: Optional[int] = Query(None, description="批次ID"),
    detail_id: Optional[int] = Query(None, description="明细ID"),
    adjustment_type: Optional[str] = Query(
        None, description="调整类型: increase/decrease/writeoff"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
):
    """获取调整记录列表"""
    try:
        adjustments, total = await service.get_adjustments(
            page=page,
            page_size=page_size,
            batch_id=batch_id,
            detail_id=detail_id,
            adjustment_type=adjustment_type,
        )

        adjustment_responses = [
            ReconciliationAdjustmentResponse.model_validate(adj) for adj in adjustments
        ]

        return paginated_response(
            items=adjustment_responses, total=total, page=page, page_size=page_size
        )

    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.get("/adjustments/{adjustment_id}")
async def get_adjustment_by_id(
    adjustment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
):
    """获取单个调整记录详情"""
    try:
        adjustment = await service.get_adjustment_by_id(adjustment_id)

        return success_response(
            data=ReconciliationAdjustmentResponse.model_validate(adjustment)
        )

    except NotFoundError as e:
        return error_response(
            code=e.error_code or "SYS_004", message=str(e), status_code=404
        )
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.post("/adjustments/{adjustment_id}/execute")
async def execute_adjustment(
    adjustment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service),
):
    """
    执行调整（触发账本记录）

    根据 RECONCILIATION_SOT.md §9.3:
    - writeoff: 不影响账本，仅更新明细状态
    - increase: 创建 ledger_entries (entry_type=COST, 补录消耗)
    - decrease: 创建 ledger_entries (entry_type=REVERSAL, 红冲多计)
    """
    try:
        adjustment = await service.execute_adjustment(adjustment_id, current_user.id)

        await audit_service.log_action(
            user_id=current_user.id,
            action="execute",
            resource_type="reconciliation_adjustment",
            resource_id=adjustment_id,
            details=f"执行调整: {adjustment.adjustment_type}, 金额={adjustment.amount}",
        )

        return success_response(
            data=ReconciliationAdjustmentResponse.model_validate(adjustment),
            message="调整执行成功",
        )

    except ValidationError as e:
        return error_response(code=e.error_code, message=str(e), status_code=400)
    except NotFoundError as e:
        return error_response(
            code=e.error_code or "SYS_004", message=str(e), status_code=404
        )
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


# ========== 报告详情/删除端点 ==========


@router.get("/reports/{report_id}")
async def get_report_by_id(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "project_owner"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
):
    """获取单个对账报告详情"""
    try:
        report = await service.get_report_by_id(report_id)

        return success_response(
            data=ReconciliationReportResponse.model_validate(report)
        )

    except NotFoundError as e:
        return error_response(
            code=e.error_code or "SYS_004", message=str(e), status_code=404
        )
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)


@router.delete("/reports/{report_id}")
async def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service),
):
    """删除对账报告（仅 admin 可删除）"""
    try:
        await service.delete_report(report_id)

        await audit_service.log_action(
            user_id=current_user.id,
            action="delete",
            resource_type="reconciliation_report",
            resource_id=report_id,
            details="删除对账报告",
        )

        return success_response(message="报告删除成功")

    except NotFoundError as e:
        return error_response(
            code=e.error_code or "SYS_004", message=str(e), status_code=404
        )
    except Exception as e:
        return error_response(code="SYS_001", message=str(e), status_code=500)
