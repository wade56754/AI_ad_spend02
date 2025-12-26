"""
财务管理 V2 API - 资金总览 + 项目盈亏

基于任务规格重构，提供 7 个新 API 端点。

SoT References:
- MASTER.md v4.4 §4.5.5 资金口径定义
- LEDGER_SOT.md v1.1 §2-3 双账本
- A2-fund-overview.md §5 API 接口
- A3-project-pnl.md §5 API 接口

API 端点:
- GET /api/v1/finance/fund/overview - 资金概览
- GET /api/v1/finance/fund/receivables - 应收账款明细
- GET /api/v1/finance/fund/distribution - 资金分布
- GET /api/v1/finance/profit/overview - 盈亏概览
- GET /api/v1/finance/profit/projects - 项目利润明细
- GET /api/v1/finance/profit/suppliers - 渠道成本分析
- GET /api/v1/finance/profit/trend - 利润趋势

Version: 1.0
Author: Claude Code
Created: 2025-12-25
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.core.dependencies import get_db, get_current_user
from backend.core.response import success_response
from backend.services.fund_service_v2 import FundServiceV2
from backend.services.profit_service_v2 import ProfitServiceV2
from backend.schemas.finance_v2 import (
    # Fund schemas
    FundOverviewData,
    ReceivablesData,
    FundDistributionData,
    # Profit schemas
    ProfitOverviewData,
    ProjectProfitsData,
    SupplierCostsData,
    ProfitTrendData,
)

# 创建两个子路由
fund_router = APIRouter(prefix="/finance/fund", tags=["Finance - Fund Overview"])
profit_router = APIRouter(prefix="/finance/profit", tags=["Finance - Profit Analysis"])


# ============================================================================
# 资金总览 API (Fund Overview)
# ============================================================================


@fund_router.get("/overview")
def get_fund_overview(
    period: str = Query(
        None, description="时间范围: month/quarter/year", regex="^(month|quarter|year)$"
    ),
    date: str = Query(None, description="指定月份: 2025-12", regex=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取资金概览

    返回本期收款、支出、应收未收、可用余额等核心指标，
    以及环比变化率。

    权限: ceo, finance
    """
    service = FundServiceV2(db)
    data = service.get_overview(period=period, date_str=date)
    return success_response(data=data.model_dump())


@fund_router.get("/receivables")
def get_receivables(
    status: str = Query(
        "all",
        description="状态: all/outstanding/settled",
        regex="^(all|outstanding|settled)$",
    ),
    sort_by: str = Query(
        "outstanding",
        description="排序: outstanding/receivable/client",
        regex="^(outstanding|receivable|client)$",
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取应收账款明细

    返回每个项目的打款、应收、已收、未收情况。

    权限: ceo, finance
    """
    service = FundServiceV2(db)
    data = service.get_receivables(status=status, sort_by=sort_by)
    return success_response(data=data.model_dump())


@fund_router.get("/distribution")
def get_fund_distribution(
    group_by: str = Query(
        "project",
        description="分组: project/supplier/platform",
        regex="^(project|supplier|platform)$",
    ),
    period: str = Query(None, description="时间范围"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取资金分布

    返回资金在各项目/渠道的分布情况及占比。

    权限: ceo, finance
    """
    service = FundServiceV2(db)
    data = service.get_distribution(group_by=group_by, period=period)
    return success_response(data=data.model_dump())


# ============================================================================
# 项目盈亏 API (Profit Analysis)
# ============================================================================


@profit_router.get("/overview")
def get_profit_overview(
    period: str = Query(None, description="指定月份: 2025-12", regex=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取盈亏概览

    返回总收入、总成本、总利润、平均利润率等核心指标，
    以及环比变化率和行业基准值。

    权限: ceo, finance, project_owner
    """
    service = ProfitServiceV2(db)
    data = service.get_overview(period=period)
    return success_response(data=data.model_dump())


@profit_router.get("/projects")
def get_project_profits(
    period: str = Query(None, description="时间范围"),
    sort_by: str = Query(
        "profit",
        description="排序: profit/profit_rate/revenue",
        regex="^(profit|profit_rate|revenue)$",
    ),
    status: str = Query(
        "all", description="状态: all/active/inactive", regex="^(all|active|inactive)$"
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取项目利润明细

    返回每个项目的进粉、收入、成本、利润、利润率，
    包含利润状态标记（健康/关注/警告/非活跃）。

    权限: ceo, finance, project_owner
    """
    service = ProfitServiceV2(db)
    data = service.get_project_profits(period=period, sort_by=sort_by, status=status)
    return success_response(data=data.model_dump())


@profit_router.get("/suppliers")
def get_supplier_costs(
    period: str = Query(None, description="时间范围"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取渠道成本分析

    返回每个渠道/供应商的费率、消耗、服务费等信息。

    权限: ceo, finance
    """
    service = ProfitServiceV2(db)
    data = service.get_supplier_costs(period=period)
    return success_response(data=data.model_dump())


@profit_router.get("/trend")
def get_profit_trend(
    granularity: str = Query(
        "week", description="颗粒度: day/week/month", regex="^(day|week|month)$"
    ),
    period: str = Query(None, description="时间范围"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取利润趋势

    返回按日/周/月聚合的收入、成本、利润趋势数据。

    权限: ceo, finance, project_owner
    """
    service = ProfitServiceV2(db)
    data = service.get_trend(granularity=granularity, period=period)
    return success_response(data=data.model_dump())


# ============================================================================
# 主路由 - 合并两个子路由
# ============================================================================

router = APIRouter(prefix="/api/v1", tags=["Finance V2"])
router.include_router(fund_router)
router.include_router(profit_router)
