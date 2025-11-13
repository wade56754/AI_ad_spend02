"""
对账管理路由
Version: 1.0
Author: Claude协作开发
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import get_current_user
from models.user import User
from models.reconciliation import ReconciliationDetail, ReconciliationAdjustment, ReconciliationReport
from schemas.reconciliation import (
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
    ReconciliationExportData
)
from services.reconciliation_service import ReconciliationService
from services.audit_log_service import AuditLogService
from utils.decorators import require_role
from utils.response import success_response, paginated_response
from utils.export import export_to_excel, export_to_pdf, export_to_json
from exceptions import ValidationError, NotFoundError, PermissionError


router = APIRouter(prefix="/reconciliations", tags=["对账管理"])


def get_reconciliation_service(db: Session = Depends(get_db)) -> ReconciliationService:
    """获取对账服务实例"""
    return ReconciliationService(db)


def get_audit_service(db: Session = Depends(get_db)) -> AuditLogService:
    """获取审计日志服务实例"""
    return AuditLogService(db)


@router.get("", response_model=dict)
@require_role(["admin", "finance", "data_operator", "account_manager", "media_buyer"])
async def get_reconciliation_batches(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="对账状态"),
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: ReconciliationService = Depends(get_reconciliation_service)
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
            user_role=current_user.role
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
                    if batch.total_platform_spend > 0 else 0, 2
                )
            # 计算处理时长
            if batch.started_at and batch.completed_at:
                duration = batch.completed_at - batch.started_at
                batch_data.processing_duration = round(duration.total_seconds() / 3600, 2)

            batch_responses.append(batch_data)

        return paginated_response(
            items=batch_responses,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/batches", response_model=dict)
@require_role(["admin", "finance"])
async def create_reconciliation_batch(
    request: ReconciliationBatchCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service)
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
            details=f"创建对账批次: {batch.batch_no}"
        )

        return success_response(
            data=ReconciliationBatchResponse.model_validate(batch),
            message="对账批次创建成功"
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.error_code, "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/batches/{batch_id}", response_model=dict)
@require_role(["admin", "finance", "data_operator", "account_manager", "media_buyer"])
async def get_reconciliation_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: ReconciliationService = Depends(get_reconciliation_service)
):
    """获取对账批次详情"""
    try:
        batch = await service.get_batch_by_id(
            batch_id,
            current_user.id,
            current_user.role
        )

        batch_data = ReconciliationBatchResponse.model_validate(batch)

        # 计算辅助字段
        if batch.total_accounts > 0:
            batch_data.match_rate = round(
                (batch.matched_accounts / batch.total_accounts) * 100, 2
            )
            batch_data.difference_rate = round(
                float(batch.total_difference / batch.total_platform_spend * 100)
                if batch.total_platform_spend > 0 else 0, 2
            )

        if batch.started_at and batch.completed_at:
            duration = batch.completed_at - batch.started_at
            batch_data.processing_duration = round(duration.total_seconds() / 3600, 2)

        return success_response(data=batch_data)

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.error_code, "message": str(e)}
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": e.error_code, "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/batches/{batch_id}/run", response_model=dict)
@require_role(["admin", "finance"])
async def run_reconciliation(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service)
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
            details=f"执行对账: {batch.batch_no}"
        )

        return success_response(
            data=ReconciliationBatchResponse.model_validate(batch),
            message="对账执行成功"
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.error_code, "message": str(e)}
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.error_code, "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/batches/{batch_id}/details", response_model=dict)
@require_role(["admin", "finance", "data_operator", "account_manager", "media_buyer"])
async def get_reconciliation_details(
    batch_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    match_status: Optional[str] = Query(None, description="匹配状态"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: ReconciliationService = Depends(get_reconciliation_service)
):
    """获取对账详情列表"""
    try:
        details, total = await service.get_batch_details(
            batch_id=batch_id,
            page=page,
            page_size=page_size,
            match_status=match_status,
            current_user_id=current_user.id,
            user_role=current_user.role
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
            items=detail_responses,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/details/{detail_id}/review", response_model=dict)
@require_role(["admin", "finance"])
async def review_reconciliation_detail(
    detail_id: int,
    request: ReconciliationDetailReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service)
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
            details=f"审核对账差异: {request.action}"
        )

        return success_response(
            data=ReconciliationDetailResponse.model_validate(detail),
            message="审核完成"
        )

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.error_code, "message": str(e)}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.error_code, "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/details/{detail_id}/adjust", response_model=dict)
@require_role(["admin", "finance"])
async def create_adjustment(
    detail_id: int,
    request: ReconciliationAdjustmentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service)
):
    """创建调整记录"""
    try:
        adjustment = await service.create_adjustment(detail_id, request, current_user.id)

        # 记录审计日志
        await audit_service.log_action(
            user_id=current_user.id,
            action="create",
            resource_type="reconciliation_adjustment",
            resource_id=adjustment.id,
            details=f"创建调整记录: {request.adjustment_amount}"
        )

        # 获取审批人名称
        approver = db.query(User).filter(User.id == adjustment.approved_by).first()
        if approver:
            adjustment_data = ReconciliationAdjustmentResponse.model_validate(adjustment)
            adjustment_data.approved_by_name = approver.name
        else:
            adjustment_data = ReconciliationAdjustmentResponse.model_validate(adjustment)

        return success_response(
            data=adjustment_data,
            message="调整记录创建成功"
        )

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.error_code, "message": str(e)}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.error_code, "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/statistics", response_model=dict)
@require_role(["admin", "finance", "data_operator"])
async def get_reconciliation_statistics(
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: ReconciliationService = Depends(get_reconciliation_service)
):
    """获取对账统计信息"""
    try:
        statistics = await service.get_statistics(
            date_from=date_from,
            date_to=date_to,
            current_user_id=current_user.id,
            user_role=current_user.role
        )

        return success_response(data=statistics)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/export")
@require_role(["admin", "finance"])
async def export_reconciliation_data(
    batch_id: Optional[int] = Query(None, description="批次ID"),
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    format_type: str = Query("excel", regex="^(excel|pdf|json)$", description="导出格式"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service)
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
            user_role=current_user.role
        )

        # 记录审计日志
        await audit_service.log_action(
            user_id=current_user.id,
            action="export",
            resource_type="reconciliation_data",
            details=f"导出对账数据: 格式={format_type}, 批次={batch_id}"
        )

        # 根据格式类型导出
        if format_type == "excel":
            file_content = export_to_excel(export_data, sheet_name="对账数据")
            filename = f"reconciliation_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
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
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/reports", response_model=dict)
@require_role(["admin", "finance", "data_operator", "account_manager", "media_buyer"])
async def get_reconciliation_reports(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    report_type: Optional[str] = Query(None, description="报告类型"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取对账报告列表"""
    try:
        query = db.query(ReconciliationReport)

        # 根据角色过滤
        if current_user.role in ["account_manager", "media_buyer"]:
            # TODO: 实现基于角色的数据过滤
            pass

        # 应用过滤条件
        if report_type:
            query = query.filter(ReconciliationReport.report_type == report_type)

        # 计算总数
        total = query.count()

        # 分页查询
        reports = query.order_by(
            ReconciliationReport.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

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
            items=report_responses,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/reports", response_model=dict)
@require_role(["admin", "finance"])
async def generate_reconciliation_report(
    request: ReconciliationReportGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: ReconciliationService = Depends(get_reconciliation_service),
    audit_service: AuditLogService = Depends(get_audit_service)
):
    """生成对账报告"""
    try:
        # TODO: 实现报告生成逻辑
        # 1. 收集数据
        # 2. 生成报告内容
        # 3. 生成图表数据（如果需要）
        # 4. 保存报告记录

        # 记录审计日志
        await audit_service.log_action(
            user_id=current_user.id,
            action="create",
            resource_type="reconciliation_report",
            details=f"生成对账报告: {request.report_type}"
        )

        # 临时返回成功
        return success_response(
            message="报告生成任务已提交，请稍后查看"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )