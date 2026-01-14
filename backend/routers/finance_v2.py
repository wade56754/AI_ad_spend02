"""
财务管理统一 API - 资金总览 + 项目盈亏
Updated: 2026-01-12 v1.1 - Fixed supplier_costs Supplier.name JOIN

这是财务模块的主路由，整合了资金总览和利润分析功能。

SoT References (最新版本):
- MASTER.md v4.9 §2.4 (6 角色模型)
- BR-FIN.md v1.1 (财务流程规则)
- BR-PROFIT.md v1.2 (利润统计规则)
- DATA_SCHEMA.md v5.7 §3.4 (ledger_entries, topup_requests)
- API_SOT.md v9.4 §5.7 (财务 API 契约)

权限矩阵 (MASTER.md v4.9 §2.4):
- ceo (admin): 全公司数据（只读）
- finance: 全公司数据（读写）
- project_owner: 自己负责的项目
- account_manager: 账户余额部分
- pitcher (media_buyer): 无访问权限

API 端点:
资金总览 (Fund Overview):
- GET /api/v1/finance/fund/overview      - 资金概览统计
- GET /api/v1/finance/fund/receivables   - 应收账款明细
- GET /api/v1/finance/fund/distribution  - 资金分布分析

项目盈亏 (Profit Analysis):
- GET /api/v1/finance/profit/overview    - 盈亏概览统计
- GET /api/v1/finance/profit/projects    - 项目利润明细
- GET /api/v1/finance/profit/suppliers   - 渠道成本分析
- GET /api/v1/finance/profit/trend       - 利润趋势分析

Version: 2.0
Author: AI Code Factory
Updated: 2026-01-12
"""

import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from backend.core.dependencies import get_db, get_current_user, require_role
from backend.core.response import success_response, error_response
from backend.models import User
from backend.services.fund_service_v2 import FundServiceV2
from backend.services.profit_service_v2 import ProfitServiceV2

logger = logging.getLogger(__name__)

# 权限定义 (MASTER.md v4.9 §2.4)
FINANCE_READ_ROLES = ["admin", "finance", "ceo"]
FINANCE_FULL_ROLES = ["admin", "finance"]
PROFIT_READ_ROLES = ["admin", "finance", "ceo", "project_owner"]
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


@fund_router.get("/overview", summary="获取资金概览", description="返回本期收款、支出、应收未收、可用余额等核心指标")
def get_fund_overview(
    period: str = Query(
        None, description="时间范围: month/quarter/year", pattern="^(month|quarter|year)$"
    ),
    date: str = Query(None, description="指定月份: 2025-12", pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(FINANCE_READ_ROLES)),
):
    """
    获取资金概览

    返回本期收款、支出、应收未收、可用余额等核心指标，以及环比变化率。

    SoT: BR-FIN.md v1.1 §BR-FIN-006 (可用资金公式)
    权限: ceo, finance, admin (MASTER.md v4.9 §2.4)
    """
    logger.info(f"GET /finance/fund/overview: user={current_user.email}, period={period}, date={date}")
    try:
        service = FundServiceV2(db)
        data = service.get_overview(period=period, date_str=date)
        return success_response(data=data.model_dump())
    except Exception as e:
        logger.exception(f"Error in fund overview: {e}")
        return error_response(code="SYS-500", message="获取资金概览失败", status_code=500)


@fund_router.get("/receivables", summary="获取应收账款明细", description="返回每个项目的打款、应收、已收、未收情况")
def get_receivables(
    status: str = Query(
        "all",
        description="状态: all/outstanding/settled",
        pattern="^(all|outstanding|settled)$",
    ),
    sort_by: str = Query(
        "outstanding",
        description="排序: outstanding/receivable/client",
        pattern="^(outstanding|receivable|client)$",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(FINANCE_READ_ROLES)),
):
    """
    获取应收账款明细

    返回每个项目的打款、应收、已收、未收情况。

    SoT: BR-FIN.md v1.1 §BR-FIN-004 (预收款非收入)
    权限: ceo, finance, admin (MASTER.md v4.9 §2.4)
    """
    logger.info(f"GET /finance/fund/receivables: user={current_user.email}, status={status}")
    try:
        service = FundServiceV2(db)
        data = service.get_receivables(status=status, sort_by=sort_by)
        return success_response(data=data.model_dump())
    except Exception as e:
        logger.exception(f"Error in receivables: {e}")
        return error_response(code="SYS-500", message="获取应收账款失败", status_code=500)


@fund_router.get("/distribution", summary="获取资金分布", description="返回资金在各项目/渠道的分布情况及占比")
def get_fund_distribution(
    group_by: str = Query(
        "project",
        description="分组: project/supplier/platform",
        pattern="^(project|supplier|platform)$",
    ),
    period: str = Query(None, description="时间范围"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(FINANCE_READ_ROLES)),
):
    """
    获取资金分布

    返回资金在各项目/渠道的分布情况及占比。

    SoT: BR-FIN.md v1.1 §BR-FIN-009 (三本账体系)
    权限: ceo, finance, admin (MASTER.md v4.9 §2.4)
    """
    logger.info(f"GET /finance/fund/distribution: user={current_user.email}, group_by={group_by}")
    try:
        service = FundServiceV2(db)
        data = service.get_distribution(group_by=group_by, period=period)
        return success_response(data=data.model_dump())
    except Exception as e:
        logger.exception(f"Error in fund distribution: {e}")
        return error_response(code="SYS-500", message="获取资金分布失败", status_code=500)


# ============================================================================
# 项目盈亏 API (Profit Analysis)
# ============================================================================


@profit_router.get("/overview", summary="获取盈亏概览", description="返回总收入、总成本、总利润、平均利润率等核心指标")
def get_profit_overview(
    period: str = Query(None, description="指定月份: 2025-12", pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(PROFIT_READ_ROLES)),
):
    """
    获取盈亏概览

    返回总收入、总成本、总利润、平均利润率等核心指标，
    以及环比变化率和行业基准值。

    SoT: BR-PROFIT.md v1.2 §BR-PROFIT-001/002/003/004 (利润公式)
    权限: ceo, finance, admin, project_owner (MASTER.md v4.9 §2.4)
    """
    logger.info(f"GET /finance/profit/overview: user={current_user.email}, period={period}")
    try:
        service = ProfitServiceV2(db)
        data = service.get_overview(period=period)
        return success_response(data=data.model_dump())
    except Exception as e:
        logger.exception(f"Error in profit overview: {e}")
        return error_response(code="SYS-500", message="获取盈亏概览失败", status_code=500)


@profit_router.get("/projects", summary="获取项目利润明细", description="返回每个项目的进粉、收入、成本、利润、利润率")
def get_project_profits(
    period: str = Query(None, description="时间范围"),
    sort_by: str = Query(
        "profit",
        description="排序: profit/profit_rate/revenue",
        pattern="^(profit|profit_rate|revenue)$",
    ),
    status: str = Query(
        "all", description="状态: all/active/inactive", pattern="^(all|active|inactive)$"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(PROFIT_READ_ROLES)),
):
    """
    获取项目利润明细

    返回每个项目的进粉、收入、成本、利润、利润率，
    包含利润状态标记（健康/关注/警告/非活跃）。

    SoT: BR-PROFIT.md v1.2 §BR-PROFIT-005 (CPL 公式)
    权限: ceo, finance, admin, project_owner (MASTER.md v4.9 §2.4)
    """
    logger.info(f"GET /finance/profit/projects: user={current_user.email}, sort_by={sort_by}")
    try:
        service = ProfitServiceV2(db)
        data = service.get_project_profits(period=period, sort_by=sort_by, status=status)
        return success_response(data=data.model_dump())
    except Exception as e:
        logger.exception(f"Error in project profits: {e}")
        return error_response(code="SYS-500", message="获取项目利润失败", status_code=500)


@profit_router.get("/suppliers", summary="获取渠道成本分析", description="返回每个渠道/供应商的费率、消耗、服务费等信息")
def get_supplier_costs(
    period: str = Query(None, description="时间范围"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(FINANCE_READ_ROLES)),
):
    """
    获取渠道成本分析

    返回每个渠道/供应商的费率、消耗、服务费等信息。

    SoT: BR-FIN.md v1.1 §BR-FIN-005 (消耗不含手续费)
    权限: ceo, finance, admin (MASTER.md v4.9 §2.4)
    """
    logger.info(f"GET /finance/profit/suppliers: user={current_user.email}, period={period}")
    try:
        service = ProfitServiceV2(db)
        data = service.get_supplier_costs(period=period)
        return success_response(data=data.model_dump())
    except Exception as e:
        logger.exception(f"Error in supplier costs: {e}")
        # 返回详细错误信息以便调试
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}"
        return error_response(code="SYS-500", message=f"获取渠道成本失败: {error_detail}", status_code=500)


@profit_router.get("/trend", summary="获取利润趋势", description="返回按日/周/月聚合的收入、成本、利润趋势数据")
def get_profit_trend(
    granularity: str = Query(
        "week", description="颗粒度: day/week/month", pattern="^(day|week|month)$"
    ),
    period: str = Query(None, description="时间范围"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(PROFIT_READ_ROLES)),
):
    """
    获取利润趋势

    返回按日/周/月聚合的收入、成本、利润趋势数据。

    SoT: BR-PROFIT.md v1.2 (利润趋势分析)
    权限: ceo, finance, admin, project_owner (MASTER.md v4.9 §2.4)
    """
    logger.info(f"GET /finance/profit/trend: user={current_user.email}, granularity={granularity}")
    try:
        service = ProfitServiceV2(db)
        data = service.get_trend(granularity=granularity, period=period)
        return success_response(data=data.model_dump())
    except Exception as e:
        logger.exception(f"Error in profit trend: {e}")
        return error_response(code="SYS-500", message="获取利润趋势失败", status_code=500)


# ============================================================================
# 主路由 - 合并资金总览和利润分析子路由
# ============================================================================

router = APIRouter(prefix="/api/v1", tags=["Finance - Unified API"])
router.include_router(fund_router)
router.include_router(profit_router)

# ============================================================================
# 注意事项
# ============================================================================
#
# 1. 此路由是财务模块的统一入口，推荐使用
# 2. 旧的 /api/v1/fund/* 和 /api/v1/profit/* 端点已废弃
# 3. 所有权限检查基于 MASTER.md v4.9 §2.4 的 6 角色模型
# 4. 财务数据计算规则见 BR-FIN.md v1.1 和 BR-PROFIT.md v1.2
#
