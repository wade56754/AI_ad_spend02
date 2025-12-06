"""
Reports 模块 FastAPI Router

对齐 SoT：
- LEDGER_SOT.md v1.1：双账本模型（PROJECT vs SUPPLIER）
- STATE_MACHINE.md v2.6：日报状态约束（仅处理 final_confirmed/final_locked）
- ERROR_CODES_SOT.md v2.1：错误码规范
- AUTH_SPEC.md v2.0：角色权限（admin/finance/data_operator 全权限，account_manager 仅自己项目，media_buyer 仅自己账户）

Version: 1.0
Created: 2025-12-07
"""

from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.services.report_service import ReportService
from backend.schemas.reports import (
    GroupByPeriod,
    ReportSortBy,
    SortOrder,
    ProjectReportQueryParams,
    ChannelReportQueryParams,
    BuyerReportQueryParams,
    ProjectReportListResponse,
    ProjectAccountReportResponse,
    ChannelReportListResponse,
    BuyerReportListResponse,
    DashboardSummary,
)
from backend.dependencies import get_current_user, require_role
from backend.exceptions import PermissionDeniedError, BusinessLogicError, ResourceNotFoundError
from backend.utils.response import StandardResponse, success_response, error_response


router = APIRouter(prefix="/reports", tags=["Reports"])


# ===== 辅助函数 =====

def _get_report_service(db: Session = Depends(get_db)) -> ReportService:
    """获取 ReportService 实例"""
    return ReportService(db)


def _handle_service_exception(e: Exception) -> StandardResponse:
    """统一处理 Service 层异常"""
    if isinstance(e, PermissionDeniedError):
        return error_response(
            code="AUTH_500",
            message="权限不足",
            http_code=403
        )
    elif isinstance(e, ResourceNotFoundError):
        return error_response(
            code="BIZ_002",
            message=str(e),
            http_code=404
        )
    elif isinstance(e, BusinessLogicError):
        return error_response(
            code="BIZ_001",
            message=str(e),
            http_code=400
        )
    else:
        # 未知错误，返回 500
        return error_response(
            code="SYS_001",
            message="服务器内部错误",
            http_code=500
        )


# ===== 项目报表 =====

@router.get(
    "/projects/summary",
    response_model=StandardResponse,
    summary="获取项目汇总报表",
    description="""
    按项目维度汇总收入、成本、粉数等核心指标

    权限要求（AUTH_SPEC v2.0）：
    - admin/finance/data_operator：查看所有项目
    - account_manager：仅查看自己负责的项目
    - media_buyer：仅查看自己管理的账户所属项目

    数据来源（LEDGER_SOT v1.1）：
    - 收入：PROJECT 账本 REVENUE 分录
    - 成本：SUPPLIER 账本 COST 分录（绝对值）
    - 粉数：daily_reports（仅 final_confirmed/final_locked 状态）
    """
)
def get_project_summary_report(
    project_id: Optional[int] = Query(None, description="项目 ID（可选筛选）"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    group_by: GroupByPeriod = Query(GroupByPeriod.DAY, description="时间分组粒度"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    sort_by: ReportSortBy = Query(ReportSortBy.REVENUE, description="排序字段"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="排序方向"),
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(_get_report_service),
):
    """获取项目汇总报表"""
    try:
        # 调用 Service 层
        rows, summary, total_count = service.get_project_summary_report(
            current_user=current_user,
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by.value,
            page=page,
            page_size=page_size,
            sort_by=sort_by.value,
            sort_order=sort_order.value,
        )

        # 构造响应
        response_data = ProjectReportListResponse(
            items=rows,
            summary=summary,
            meta={
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": (total_count + page_size - 1) // page_size,
            }
        )

        return success_response(data=response_data.model_dump())

    except (PermissionDeniedError, ResourceNotFoundError, BusinessLogicError) as e:
        raise HTTPException(
            status_code=403 if isinstance(e, PermissionDeniedError) else 400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@router.get(
    "/projects/{project_id}/accounts",
    response_model=StandardResponse,
    summary="获取项目详细报表（账户维度）",
    description="""
    查询指定项目下所有广告账户的明细数据

    权限要求：
    - admin/finance/data_operator：可查看任意项目
    - account_manager：仅查看自己负责的项目
    - media_buyer：仅查看自己管理的账户
    """
)
def get_project_accounts_report(
    project_id: int,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(_get_report_service),
):
    """获取项目详细报表（账户维度）"""
    try:
        # 调用 Service 层
        project_info, accounts, summary = service.get_project_accounts_report(
            current_user=current_user,
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
        )

        # 构造响应
        response_data = ProjectAccountReportResponse(
            project=project_info,
            accounts=accounts,
            summary=summary,
        )

        return success_response(data=response_data.model_dump())

    except (PermissionDeniedError, ResourceNotFoundError, BusinessLogicError) as e:
        raise HTTPException(
            status_code=403 if isinstance(e, PermissionDeniedError) else (404 if isinstance(e, ResourceNotFoundError) else 400),
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


# ===== 渠道报表 =====

@router.get(
    "/channels/summary",
    response_model=StandardResponse,
    summary="获取渠道汇总报表",
    description="""
    按渠道维度汇总成本、充值、余额等供应商账本指标

    权限要求：
    - admin/finance/data_operator：查看所有渠道
    - account_manager/media_buyer：仅查看自己项目/账户涉及的渠道

    数据来源（LEDGER_SOT v1.1）：
    - 所有指标均来自 SUPPLIER 账本
    - 成本：COST 分录（绝对值）
    - 充值：TOPUP 分录
    - 转入：TRANSFER_IN 分录
    - 转出：TRANSFER_OUT 分录（绝对值）
    - 余额：按分录类型计算（TOPUP + TRANSFER_IN - COST - TRANSFER_OUT）
    """
)
def get_channel_summary_report(
    channel_id: Optional[str] = Query(None, description="渠道 ID（UUID）"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    group_by: GroupByPeriod = Query(GroupByPeriod.DAY, description="时间分组粒度"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    sort_by: str = Query('cost', description="排序字段（cost/topup/balance）"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="排序方向"),
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(_get_report_service),
):
    """获取渠道汇总报表"""
    try:
        # 调用 Service 层
        rows, summary, total_count = service.get_channel_summary_report(
            current_user=current_user,
            channel_id=channel_id,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by.value,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order.value,
        )

        # 构造响应
        response_data = ChannelReportListResponse(
            items=rows,
            summary=summary,
            meta={
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": (total_count + page_size - 1) // page_size,
            }
        )

        return success_response(data=response_data.model_dump())

    except (PermissionDeniedError, ResourceNotFoundError, BusinessLogicError) as e:
        raise HTTPException(
            status_code=403 if isinstance(e, PermissionDeniedError) else 400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


# ===== 投手报表 =====

@router.get(
    "/buyers/summary",
    response_model=StandardResponse,
    summary="获取投手汇总报表",
    description="""
    按投手维度汇总绩效指标（粉数、收入、成本、毛利）

    权限要求：
    - admin/finance/data_operator：查看所有投手
    - account_manager：仅查看自己项目下的投手
    - media_buyer：仅查看自己的数据
    """
)
def get_buyer_summary_report(
    buyer_id: Optional[str] = Query(None, description="投手 ID（UUID）"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    group_by: GroupByPeriod = Query(GroupByPeriod.DAY, description="时间分组粒度"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    sort_by: ReportSortBy = Query(ReportSortBy.REVENUE, description="排序字段"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="排序方向"),
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(_get_report_service),
):
    """获取投手汇总报表"""
    try:
        # 调用 Service 层
        rows, summary, total_count = service.get_buyer_summary_report(
            current_user=current_user,
            buyer_id=buyer_id,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by.value,
            page=page,
            page_size=page_size,
            sort_by=sort_by.value,
            sort_order=sort_order.value,
        )

        # 构造响应
        response_data = BuyerReportListResponse(
            items=rows,
            summary=summary,
            meta={
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": (total_count + page_size - 1) // page_size,
            }
        )

        return success_response(data=response_data.model_dump())

    except (PermissionDeniedError, ResourceNotFoundError, BusinessLogicError) as e:
        raise HTTPException(
            status_code=403 if isinstance(e, PermissionDeniedError) else 400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


# ===== 仪表板汇总 =====

@router.get(
    "/dashboard/summary",
    response_model=StandardResponse,
    summary="获取仪表板汇总数据",
    description="""
    返回首页仪表板所需的核心指标汇总：
    - 总览指标（总收入、总成本、总毛利、平均毛利率）
    - 按项目统计（活跃项目数、TOP 项目列表）
    - 按渠道统计（活跃渠道数、总余额）
    - 按投手统计（活跃投手数、平均粉数）
    - 趋势数据（日趋势、月趋势）

    权限要求：
    - admin/finance/data_operator：查看全局数据
    - account_manager：仅查看自己负责项目的数据
    - media_buyer：仅查看自己管理账户的数据
    """
)
def get_dashboard_summary(
    start_date: Optional[date] = Query(None, description="开始日期（默认近 30 天）"),
    end_date: Optional[date] = Query(None, description="结束日期（默认今天）"),
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(_get_report_service),
):
    """获取仪表板汇总数据"""
    try:
        # 调用 Service 层
        dashboard_data = service.get_dashboard_summary(
            current_user=current_user,
            start_date=start_date,
            end_date=end_date,
        )

        return success_response(data=dashboard_data.model_dump())

    except (PermissionDeniedError, BusinessLogicError) as e:
        raise HTTPException(
            status_code=403 if isinstance(e, PermissionDeniedError) else 400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")
