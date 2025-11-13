"""
日报管理API路由
Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
import pandas as pd
import uuid

from core.database import get_db
from core.dependencies import get_current_user, require_role
from core.response import (
    success_response,
    error_response,
    paginated_response,
    StandardResponse
)
from exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError
)
from models.user import User
from schemas.daily_report import (
    DailyReportCreateRequest,
    DailyReportUpdateRequest,
    DailyReportAuditRequest,
    DailyReportBatchImportRequest,
    DailyReportQueryParams,
    DailyReportResponse,
    DailyReportListResponse,
    DailyReportStatisticsResponse,
    DailyReportExportResponse,
    DailyReportBatchImportResponse,
    DailyReportImportError,
    DailyReportAuditLogResponse
)
from services.daily_report_service import DailyReportService

router = APIRouter(prefix="/daily-reports", tags=["daily-reports"])


def get_daily_report_service(db: Session = Depends(get_db)) -> DailyReportService:
    """获取日报服务实例"""
    return DailyReportService(db)


@router.get(
    "",
    response_model=StandardResponse[DailyReportListResponse],
    summary="获取日报列表",
    description="获取日报列表，支持分页和筛选"
)
async def list_daily_reports(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    report_date_start: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    report_date_end: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    ad_account_id: Optional[int] = Query(None, description="广告账户ID"),
    status: Optional[str] = Query(None, pattern="^(pending|approved|rejected)$", description="审核状态"),
    media_buyer_id: Optional[int] = Query(None, description="投手ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(get_current_user)
):
    """
    获取日报列表API
    """
    try:
        # 构建查询参数
        params = DailyReportQueryParams(
            report_date_start=report_date_start,
            report_date_end=report_date_end,
            ad_account_id=ad_account_id,
            status=status,
            media_buyer_id=media_buyer_id,
            project_id=project_id
        )

        # 获取日报列表
        reports, total = service.get_daily_reports(params, current_user, page, page_size)

        # 转换为响应格式
        report_responses = [
            DailyReportResponse.model_validate(report)
            for report in reports
        ]

        # 返回分页响应
        return paginated_response(
            items=report_responses,
            page=page,
            page_size=page_size,
            total=total
        )

    except (BusinessLogicError, ResourceNotFoundError, PermissionDeniedError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "BIZ_ERROR",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            code="SYS_500",
            message="系统内部错误",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post(
    "",
    response_model=StandardResponse[DailyReportResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建日报",
    description="创建新的日报记录"
)
@require_role(["media_buyer", "admin", "data_operator"])
async def create_daily_report(
    request: DailyReportCreateRequest,
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(get_current_user)
):
    """
    创建日报API
    """
    try:
        # 创建日报
        report = service.create_daily_report(request, current_user)

        # 转换为响应格式
        report_response = DailyReportResponse.model_validate(report)

        return success_response(
            data=report_response,
            message="日报创建成功",
            status_code=status.HTTP_201_CREATED
        )

    except (ResourceConflictError, BusinessLogicError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "BIZ_ERROR",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except PermissionDeniedError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "PERMISSION_DENIED",
            message=str(e),
            status_code=status.HTTP_403_FORBIDDEN
        )
    except Exception as e:
        return error_response(
            code="SYS_500",
            message="系统内部错误",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/{report_id}",
    response_model=StandardResponse[DailyReportResponse],
    summary="获取日报详情",
    description="根据ID获取日报详情"
)
async def get_daily_report(
    report_id: int,
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(get_current_user)
):
    """
    获取日报详情API
    """
    try:
        # 获取日报详情
        report = service.get_daily_report(report_id, current_user)

        # 转换为响应格式
        report_response = DailyReportResponse.model_validate(report)

        return success_response(data=report_response)

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS_004",
            message=str(e),
            status_code=status.HTTP_404_NOT_FOUND
        )
    except PermissionDeniedError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "PERMISSION_DENIED",
            message=str(e),
            status_code=status.HTTP_403_FORBIDDEN
        )
    except Exception as e:
        return error_response(
            code="SYS_500",
            message="系统内部错误",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.put(
    "/{report_id}",
    response_model=StandardResponse[DailyReportResponse],
    summary="更新日报",
    description="更新日报信息（仅未审核的日报可更新）"
)
@require_role(["media_buyer", "admin"])
async def update_daily_report(
    report_id: int,
    request: DailyReportUpdateRequest,
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(get_current_user)
):
    """
    更新日报API
    """
    try:
        # 更新日报
        report = service.update_daily_report(report_id, request, current_user)

        # 转换为响应格式
        report_response = DailyReportResponse.model_validate(report)

        return success_response(
            data=report_response,
            message="日报更新成功"
        )

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS_004",
            message=str(e),
            status_code=status.HTTP_404_NOT_FOUND
        )
    except (BusinessLogicError, PermissionDeniedError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "BIZ_ERROR",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            code="SYS_500",
            message="系统内部错误",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除日报",
    description="删除日报记录（仅管理员可操作）"
)
@require_role(["admin"])
async def delete_daily_report(
    report_id: int,
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(get_current_user)
):
    """
    删除日报API
    """
    try:
        # 删除日报
        service.delete_daily_report(report_id, current_user)

        return None

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS_004",
            message=str(e),
            status_code=status.HTTP_404_NOT_FOUND
        )
    except PermissionDeniedError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "PERMISSION_DENIED",
            message=str(e),
            status_code=status.HTTP_403_FORBIDDEN
        )
    except Exception as e:
        return error_response(
            code="SYS_500",
            message="系统内部错误",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post(
    "/{report_id}/approve",
    response_model=StandardResponse[DailyReportResponse],
    summary="审核通过日报",
    description="审核通过日报记录"
)
@require_role(["data_operator", "admin"])
async def approve_daily_report(
    report_id: int,
    request: DailyReportAuditRequest,
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(get_current_user)
):
    """
    审核通过日报API
    """
    try:
        # 审核通过
        report = service.approve_daily_report(report_id, request, current_user)

        # 转换为响应格式
        report_response = DailyReportResponse.model_validate(report)

        return success_response(
            data=report_response,
            message="日报审核通过"
        )

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS_004",
            message=str(e),
            status_code=status.HTTP_404_NOT_FOUND
        )
    except (BusinessLogicError, PermissionDeniedError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "BIZ_ERROR",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            code="SYS_500",
            message="系统内部错误",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post(
    "/{report_id}/reject",
    response_model=StandardResponse[DailyReportResponse],
    summary="驳回报日",
    description="驳回报日记录"
)
@require_role(["data_operator", "admin"])
async def reject_daily_report(
    report_id: int,
    request: DailyReportAuditRequest,
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(get_current_user)
):
    """
    驳回报日API
    """
    try:
        # 驳回报日
        report = service.reject_daily_report(report_id, request, current_user)

        # 转换为响应格式
        report_response = DailyReportResponse.model_validate(report)

        return success_response(
            data=report_response,
            message="日报已驳回"
        )

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS_004",
            message=str(e),
            status_code=status.HTTP_404_NOT_FOUND
        )
    except (BusinessLogicError, PermissionDeniedError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "BIZ_ERROR",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            code="SYS_500",
            message="系统内部错误",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post(
    "/batch-import",
    response_model=StandardResponse[DailyReportBatchImportResponse],
    summary="批量导入日报",
    description="批量导入日报记录"
)
@require_role(["data_operator", "admin"])
async def batch_import_daily_reports(
    request: DailyReportBatchImportRequest,
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(get_current_user)
):
    """
    批量导入日报API
    """
    try:
        # 记录开始时间
        start_time = datetime.utcnow()

        # 批量导入
        success_count, error_count, errors, imported_ids = service.batch_import_daily_reports(
            request, current_user
        )

        # 计算处理时间
        processing_time = (datetime.utcnow() - start_time).total_seconds()

        # 转换错误格式
        error_responses = [
            DailyReportImportError.model_validate(error)
            for error in errors
        ]

        # 构建响应
        response = DailyReportBatchImportResponse(
            total_count=len(request.reports),
            success_count=success_count,
            error_count=error_count,
            errors=error_responses,
            imported_ids=imported_ids,
            processing_time_seconds=processing_time
        )

        return success_response(
            data=response,
            message=f"批量导入完成，成功{success_count}条，失败{error_count}条"
        )

    except BusinessLogicError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "BIZ_ERROR",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            code="SYS_500",
            message="系统内部错误",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post(
    "/import-file",
    response_model=StandardResponse[DailyReportBatchImportResponse],
    summary="文件导入日报",
    description="通过Excel文件导入日报"
)
@require_role(["data_operator", "admin"])
async def import_daily_reports_from_file(
    file: UploadFile = File(..., description="Excel文件"),
    skip_errors: bool = Query(False, description="是否跳过错误继续导入"),
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(get_current_user)
):
    """
    文件导入日报API
    """
    try:
        # 验证文件类型
        if not file.filename.endswith(('.xlsx', '.xls')):
            return error_response(
                code="BIZ_006",
                message="只支持Excel文件格式（.xlsx, .xls）",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # 读取Excel文件
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))

        # 转换为请求列表
        reports = []
        errors = []

        for index, row in df.iterrows():
            try:
                # 转换行数据为请求对象
                report_data = DailyReportCreateRequest(
                    report_date=pd.to_datetime(row['报表日期']).date() if '报表日期' in row else None,
                    ad_account_id=int(row['广告账户ID']) if '广告账户ID' in row else None,
                    campaign_name=str(row['广告系列名称']) if '广告系列名称' in row else None,
                    ad_group_name=str(row['广告组名称']) if '广告组名称' in row else None,
                    ad_creative_name=str(row['广告创意名称']) if '广告创意名称' in row else None,
                    impressions=int(row.get('展示次数', 0)),
                    clicks=int(row.get('点击次数', 0)),
                    spend=Decimal(str(row.get('消耗金额', 0))),
                    conversions=int(row.get('转化次数', 0)),
                    new_follows=int(row.get('新增粉丝数', 0)),
                    cpa=Decimal(str(row['CPA'])) if 'CPA' in row and pd.notna(row['CPA']) else None,
                    roas=Decimal(str(row['ROAS'])) if 'ROAS' in row and pd.notna(row['ROAS']) else None,
                    notes=str(row['备注']) if '备注' in row and pd.notna(row['备注']) else None
                )
                reports.append(report_data)
            except Exception as e:
                errors.append(
                    DailyReportImportError(
                        row_number=index + 1,
                        error_code="DATA_FORMAT_ERROR",
                        error_message=str(e),
                        invalid_data=row.to_dict()
                    )
                )

        # 如果有格式错误且不跳过错误，返回错误
        if errors and not skip_errors:
            return error_response(
                code="BIZ_006",
                message="文件格式错误，请检查数据格式",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # 批量导入
        batch_request = DailyReportBatchImportRequest(
            reports=reports,
            skip_errors=skip_errors
        )

        return await batch_import_daily_reports(
            batch_request,
            service,
            current_user
        )

    except Exception as e:
        return error_response(
            code="SYS_500",
            message="文件处理失败：" + str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/export",
    summary="导出日报",
    description="导出日报数据为Excel文件"
)
@require_role(["finance", "admin", "data_operator", "account_manager"])
async def export_daily_reports(
    report_date_start: Optional[str] = Query(None, description="开始日期"),
    report_date_end: Optional[str] = Query(None, description="结束日期"),
    ad_account_id: Optional[int] = Query(None, description="广告账户ID"),
    status: Optional[str] = Query(None, description="审核状态"),
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(get_current_user)
):
    """
    导出日报API
    """
    try:
        # 构建查询参数
        params = DailyReportQueryParams(
            report_date_start=report_date_start,
            report_date_end=report_date_end,
            ad_account_id=ad_account_id,
            status=status
        )

        # 获取所有符合条件的日报（不分页）
        reports, _ = service.get_daily_reports(params, current_user, page=1, page_size=10000)

        # 转换为DataFrame
        data = []
        for report in reports:
            data.append({
                'ID': report.id,
                '报表日期': report.report_date,
                '广告账户ID': report.ad_account_id,
                '广告账户': report.ad_account.name if report.ad_account else '',
                '广告系列': report.campaign_name or '',
                '广告组': report.ad_group_name or '',
                '广告创意': report.ad_creative_name or '',
                '展示次数': report.impressions,
                '点击次数': report.clicks,
                '消耗金额': float(report.spend),
                '转化次数': report.conversions,
                '新增粉丝': report.new_follows,
                '状态': report.status,
                '创建人': report.creator.nickname if report.creator else '',
                '创建时间': report.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                '审核人': report.auditor.nickname if report.auditor else '',
                '审核时间': report.audit_time.strftime('%Y-%m-%d %H:%M:%S') if report.audit_time else '',
                '备注': report.notes or '',
                '审核说明': report.audit_notes or ''
            })

        df = pd.DataFrame(data)

        # 创建Excel文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='日报数据')

            # 调整列宽
            worksheet = writer.sheets['日报数据']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        output.seek(0)

        # 生成文件名
        file_name = f"daily_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        # 返回文件流
        return StreamingResponse(
            BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={file_name}"}
        )

    except Exception as e:
        return error_response(
            code="SYS_500",
            message="导出失败：" + str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/statistics",
    response_model=StandardResponse[DailyReportStatisticsResponse],
    summary="获取日报统计",
    description="获取日报统计数据"
)
@require_role(["data_operator", "admin", "finance", "account_manager"])
async def get_daily_report_statistics(
    report_date_start: Optional[str] = Query(None, description="开始日期"),
    report_date_end: Optional[str] = Query(None, description="结束日期"),
    ad_account_id: Optional[int] = Query(None, description="广告账户ID"),
    status: Optional[str] = Query(None, description="审核状态"),
    media_buyer_id: Optional[int] = Query(None, description="投手ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(get_current_user)
):
    """
    获取日报统计API
    """
    try:
        # 构建查询参数
        params = DailyReportQueryParams(
            report_date_start=report_date_start,
            report_date_end=report_date_end,
            ad_account_id=ad_account_id,
            status=status,
            media_buyer_id=media_buyer_id,
            project_id=project_id
        )

        # 获取统计数据
        stats = service.get_daily_report_statistics(params, current_user)

        # 转换为响应格式
        stats_response = DailyReportStatisticsResponse.model_validate(stats)

        return success_response(data=stats_response)

    except Exception as e:
        return error_response(
            code="SYS_500",
            message="系统内部错误",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/{report_id}/audit-logs",
    response_model=StandardResponse[List[DailyReportAuditLogResponse]],
    summary="获取日报审核日志",
    description="获取日报的操作日志记录"
)
async def get_daily_report_audit_logs(
    report_id: int,
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(get_current_user)
):
    """
    获取日报审核日志API
    """
    try:
        # 获取审核日志
        logs = service.get_daily_report_audit_logs(report_id, current_user)

        # 转换为响应格式
        log_responses = [
            DailyReportAuditLogResponse.model_validate(log)
            for log in logs
        ]

        return success_response(data=log_responses)

    except ResourceNotFoundError as e:
        return error_response(
            code="SYS_004",
            message=str(e),
            status_code=status.HTTP_404_NOT_FOUND
        )
    except PermissionDeniedError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, 'error_code') else "PERMISSION_DENIED",
            message=str(e),
            status_code=status.HTTP_403_FORBIDDEN
        )
    except Exception as e:
        return error_response(
            code="SYS_500",
            message="系统内部错误",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )