"""
报表管理API
Version: 2.0
Author: Claude协作开发

提供多维度报表查询：
- 仪表盘摘要：今日/本月核心指标
- 效果报表：广告消耗、线索数、CPA
- 利润报表：收入、成本、利润率
- 对账报表：对账状态汇总
- 财务摘要：账户余额、充值、消耗
- 趋势报表：时间序列数据

SoT Reference: API_SOT.md v9.0 第14章 (报表模块)
"""

from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.dependencies import (
    get_current_user,
    require_role,
    require_permission
)
from backend.core.response import success_response, error_response
from backend.core.error_codes import ErrorCode, BusinessErrorCodes
from backend.models import User
from backend.schemas.reports import (
    ReportQueryRequest, ReportExportRequest,
    PerformanceReportResponse, ProfitReportResponse,
    ReconciliationReportResponse, FinancialSummaryResponse,
    DashboardSummary, TrendReportResponse,
    ReportPeriod, ReportGroupBy, ReportExportFormat
)
from backend.services.reports_service import ReportsService, get_reports_service


router = APIRouter(prefix="/reports", tags=["reports"])


# ========== 仪表盘 ==========

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取仪表盘摘要

    返回今日/本月核心指标、账户/项目统计、待办事项、趋势图数据

    权限要求: 所有已登录用户
    """
    service = get_reports_service(db)
    result = await service.get_dashboard_summary()
    return success_response(
        data=result.model_dump(),
        message="获取仪表盘成功"
    )


# ========== 效果报表 ==========

@router.get("/performance", response_model=Dict[str, Any])
async def get_performance_report(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    project_ids: Optional[str] = Query(None, description="项目ID列表,逗号分隔"),
    channel_ids: Optional[str] = Query(None, description="渠道ID列表,逗号分隔"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取效果报表

    按项目/渠道汇总广告消耗、线索数、CPA

    权限要求: 所有已登录用户
    """
    # 解析ID列表
    project_id_list = None
    channel_id_list = None
    if project_ids:
        try:
            project_id_list = [int(x.strip()) for x in project_ids.split(",")]
        except ValueError:
            return error_response(
                code="VALIDATION_002",
                message="项目ID格式错误",
                status_code=400
            )
    if channel_ids:
        try:
            channel_id_list = [int(x.strip()) for x in channel_ids.split(",")]
        except ValueError:
            return error_response(
                code="VALIDATION_002",
                message="渠道ID格式错误",
                status_code=400
            )

    service = get_reports_service(db)
    result = await service.get_performance_report(
        start_date=start_date,
        end_date=end_date,
        project_ids=project_id_list,
        channel_ids=channel_id_list
    )

    return success_response(
        data={
            "items": [item.model_dump() for item in result.items],
            "summary": result.summary,
            "meta": result.meta
        },
        message="获取效果报表成功"
    )


# ========== 利润报表 ==========

@router.get("/profit", response_model=Dict[str, Any])
async def get_profit_report(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    project_ids: Optional[str] = Query(None, description="项目ID列表,逗号分隔"),
    current_user: User = Depends(require_role(["admin", "finance"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取利润报表

    按项目汇总收入、成本、利润、利润率

    权限要求: admin, finance
    """
    project_id_list = None
    if project_ids:
        try:
            project_id_list = [int(x.strip()) for x in project_ids.split(",")]
        except ValueError:
            return error_response(
                code="VALIDATION_002",
                message="项目ID格式错误",
                status_code=400
            )

    service = get_reports_service(db)
    result = await service.get_profit_report(
        start_date=start_date,
        end_date=end_date,
        project_ids=project_id_list
    )

    return success_response(
        data={
            "items": [item.model_dump() for item in result.items],
            "summary": result.summary,
            "meta": result.meta
        },
        message="获取利润报表成功"
    )


# ========== 对账报表 ==========

@router.get("/reconciliation", response_model=Dict[str, Any])
async def get_reconciliation_report(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(require_role(["admin", "finance"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取对账报表

    汇总对账批次状态、系统消耗vs实际消耗、差异率

    权限要求: admin, finance
    """
    service = get_reports_service(db)
    result = await service.get_reconciliation_report(
        start_date=start_date,
        end_date=end_date
    )

    return success_response(
        data={
            "items": [item.model_dump() for item in result.items],
            "summary": result.summary,
            "meta": result.meta
        },
        message="获取对账报表成功"
    )


# ========== 财务摘要 ==========

@router.get("/financial", response_model=Dict[str, Any])
async def get_financial_summary(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    project_ids: Optional[str] = Query(None, description="项目ID列表,逗号分隔"),
    current_user: User = Depends(require_role(["admin", "finance"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取财务摘要

    按账户汇总余额、充值、消耗、转账

    权限要求: admin, finance
    """
    project_id_list = None
    if project_ids:
        try:
            project_id_list = [int(x.strip()) for x in project_ids.split(",")]
        except ValueError:
            return error_response(
                code="VALIDATION_002",
                message="项目ID格式错误",
                status_code=400
            )

    service = get_reports_service(db)
    result = await service.get_financial_summary(
        start_date=start_date,
        end_date=end_date,
        project_ids=project_id_list
    )

    return success_response(
        data={
            "items": [item.model_dump() for item in result.items],
            "summary": result.summary,
            "meta": result.meta
        },
        message="获取财务摘要成功"
    )


# ========== 趋势报表 ==========

@router.get("/trends/{metric}", response_model=Dict[str, Any])
async def get_trend_report(
    metric: str,
    period: str = Query("daily", description="统计周期: daily, weekly, monthly"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取趋势报表

    支持指标: spend(消耗), leads(线索), topup(充值)

    权限要求: 所有已登录用户
    """
    valid_metrics = ["spend", "leads", "topup"]
    if metric not in valid_metrics:
        return error_response(
            code="VALIDATION_002",
            message=f"无效的指标类型，支持: {', '.join(valid_metrics)}",
            status_code=400
        )

    valid_periods = ["daily", "weekly", "monthly"]
    if period not in valid_periods:
        return error_response(
            code="VALIDATION_002",
            message=f"无效的统计周期，支持: {', '.join(valid_periods)}",
            status_code=400
        )

    service = get_reports_service(db)
    result = await service.get_trend_report(
        metric=metric,
        period=period,
        start_date=start_date,
        end_date=end_date
    )

    return success_response(
        data={
            "period": result.period,
            "data_points": [
                {
                    "date": dp.date.isoformat(),
                    "value": str(dp.value),
                    "label": dp.label
                }
                for dp in result.data_points
            ],
            "summary": result.summary
        },
        message=f"获取{metric}趋势报表成功"
    )


# ========== 综合报表（向后兼容） ==========

@router.get("", response_model=Dict[str, Any])
async def get_report_summary(
    start_date: Optional[date] = Query(None, alias="start", description="开始日期"),
    end_date: Optional[date] = Query(None, alias="end", description="结束日期"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取综合报表摘要（向后兼容）

    返回效果报表的简化版本
    """
    service = get_reports_service(db)
    result = await service.get_performance_report(
        start_date=start_date,
        end_date=end_date
    )

    # 转换为简化格式（向后兼容旧版API）
    data = []
    for item in result.items:
        data.append({
            "project_id": str(item.project_id) if item.project_id else None,
            "project_name": item.project_name,
            "total_spend": str(item.total_spend.quantize(__import__('decimal').Decimal("0.01"))),
            "total_leads": item.total_leads,
        })

    return success_response(data=data, message="获取报表成功")


@router.get("/{project_id}", response_model=Dict[str, Any])
async def get_project_report(
    project_id: int,
    start_date: Optional[date] = Query(None, alias="start", description="开始日期"),
    end_date: Optional[date] = Query(None, alias="end", description="结束日期"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取单个项目报表（向后兼容）
    """
    service = get_reports_service(db)
    result = await service.get_performance_report(
        start_date=start_date,
        end_date=end_date,
        project_ids=[project_id]
    )

    if not result.items:
        return error_response(
            code="RESOURCE_001",
            message="指定项目暂无报表数据",
            status_code=404
        )

    item = result.items[0]
    data = {
        "project_id": str(item.project_id) if item.project_id else None,
        "project_name": item.project_name,
        "total_spend": str(item.total_spend.quantize(__import__('decimal').Decimal("0.01"))),
        "total_leads": item.total_leads,
        "cpa": str(item.cpa.quantize(__import__('decimal').Decimal("0.01"))) if item.cpa else None,
    }

    return success_response(data=data, message="获取项目报表成功")
