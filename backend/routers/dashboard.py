"""
Dashboard API 路由

提供运营驾驶舱数据，包括：
- KPI 指标
- 消耗趋势
- 项目排行
- 待办事项
- 告警信息

权限：
- CEO 驾驶舱端点仅 admin/ceo 可访问
- 通用端点根据角色过滤数据

SoT Reference: MASTER.md v4.4 §6.5
"""

import logging
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.dependencies import get_current_user
from backend.core.error_codes import SystemErrorCodes
from backend.core.response import StandardResponse, error_response, success_response
from backend.core.role_mapping import role_in_list
from backend.exceptions.custom_exceptions import PermissionDeniedError
from backend.models import User
from backend.schemas.dashboard import (
    DashboardDetail,
    DashboardSummary,
    KpiResponse,
    RankingResponse,
    TodoResponse,
    TrendResponse,
)
from backend.services.dashboard_service import DashboardService
from backend.services.dashboard.ceo_dashboard_service import CEODashboardService
from backend.services.dashboard.profit_service import ProfitService
from backend.services.dashboard.project_balance_service import ProjectBalanceService
from backend.services.dashboard.cash_status_service import CashStatusService
from backend.schemas.dashboard.ceo import (
    CEOOverviewResponse,
    CashStatusResponse,
    ProfitSummaryResponse,
    ProjectBalanceResponse,
    ActionItemsResponse,
    ProjectRankingResponse,
    TrendDataResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


# ============ 权限检查 ============


def require_ceo_access(current_user: User = Depends(get_current_user)) -> User:
    """
    CEO 驾驶舱权限检查

    仅允许以下角色访问：
    - admin
    - ceo (映射到 admin)

    使用 role_in_list 支持等价角色
    """
    allowed_roles = ["admin", "ceo"]
    
    # 获取用户角色（可能为 None）
    user_role = current_user.role if current_user.role else None
    
    # 规范化角色值（去除空格，转小写）
    if user_role:
        user_role = user_role.strip().lower()
    
    # 详细日志：记录实际角色值和检查过程
    logger.info(
        f"CEO dashboard access check: user_id={current_user.id}, "
        f"email={current_user.email}, "
        f"user_role={user_role} (raw={current_user.role}), "
        f"allowed_roles={allowed_roles}"
    )

    # 检查角色是否在允许列表中
    if not role_in_list(user_role, allowed_roles):
        logger.warning(
            f"User {current_user.id} (email={current_user.email}, role={user_role}) "
            f"denied access to CEO dashboard. Allowed roles: {allowed_roles}"
        )
        raise PermissionDeniedError(
            message="CEO 驾驶舱仅限老板和管理员访问"
        )
    
    logger.info(
        f"User {current_user.id} (role={user_role}) granted access to CEO dashboard"
    )

    return current_user


def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    """Dashboard Service 依赖注入"""
    return DashboardService(db)


# ============ KPI 端点 ============


@router.get(
    "/kpi",
    response_model=StandardResponse[KpiResponse],
    summary="KPI 指标",
    description="获取核心 KPI 指标数据，包括消耗、转化、CPL、ROI 及环比变化",
)
async def get_kpi(
    period: Optional[str] = Query(None, description="统计周期 (YYYY-MM)，默认当月"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user),
):
    """
    KPI 指标 API

    返回：
    - 总消耗、总转化、总进粉
    - 平均 CPL、ROI、利润率
    - 消耗/转化/CPL 环比变化

    Phase 1 行为：仅展示数据，不阻断任何操作
    """
    try:
        logger.info(f"KPI request: user={current_user.id}, period={period}")

        start_date, end_date, period_str = service.parse_period(period)
        kpi = service.get_kpi(start_date, end_date, project_id)

        response = KpiResponse(
            period=period_str,
            start_date=start_date,
            end_date=end_date,
            kpi=kpi,
        )

        return success_response(data=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in KPI endpoint: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="获取 KPI 数据失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


# ============ 趋势端点 ============


@router.get(
    "/trend",
    response_model=StandardResponse[TrendResponse],
    summary="消耗趋势",
    description="获取时间维度的消耗趋势数据",
)
async def get_trend(
    period: Optional[str] = Query(None, description="统计周期 (YYYY-MM)"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    granularity: Literal["day", "week", "month"] = Query(
        "day", description="数据粒度"
    ),
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user),
):
    """
    消耗趋势 API

    返回：
    - 按日/周/月聚合的消耗、转化、进粉、CPL 数据
    """
    try:
        logger.info(
            f"Trend request: user={current_user.id}, period={period}, granularity={granularity}"
        )

        start_date, end_date, period_str = service.parse_period(period)
        items = service.get_trend(start_date, end_date, project_id, granularity)

        response = TrendResponse(
            period=period_str,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
            items=items,
        )

        return success_response(data=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in trend endpoint: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="获取趋势数据失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


# ============ 项目排行端点 ============


@router.get(
    "/ranking",
    response_model=StandardResponse[RankingResponse],
    summary="项目排行",
    description="获取项目排行榜数据",
)
async def get_ranking(
    period: Optional[str] = Query(None, description="统计周期 (YYYY-MM)"),
    ranking_type: Literal["spend", "cpl", "roas"] = Query(
        "spend", description="排名类型: spend(消耗)/cpl(单粉成本)/roas(回报率)"
    ),
    top_n: int = Query(10, ge=1, le=50, description="返回 Top N 项目"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user),
):
    """
    项目排行 API

    返回：
    - 按消耗/CPL/ROAS 排名的项目列表
    """
    try:
        logger.info(
            f"Ranking request: user={current_user.id}, type={ranking_type}, top_n={top_n}"
        )

        start_date, end_date, period_str = service.parse_period(period)
        items = service.get_project_ranking(start_date, end_date, ranking_type, top_n)

        response = RankingResponse(
            period=period_str,
            start_date=start_date,
            end_date=end_date,
            ranking_type=ranking_type,
            items=items,
        )

        return success_response(data=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in ranking endpoint: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="获取排行数据失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


# ============ 待办事项端点 ============


@router.get(
    "/todos",
    response_model=StandardResponse[TodoResponse],
    summary="待办事项",
    description="获取当前待处理事项列表",
)
async def get_todos(
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user),
):
    """
    待办事项 API

    返回：
    - 待审核日报数
    - 趋势异常日报数
    - 待审批充值数

    优先级规则：
    - urgent: 趋势异常
    - high: 数量 > 10
    - normal: 其他
    """
    try:
        logger.info(f"Todos request: user={current_user.id}")

        response = service.get_todos(current_user)

        return success_response(data=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in todos endpoint: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="获取待办事项失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


# ============ CEO 驾驶舱端点 (保持向后兼容) ============


@router.get(
    "/ceo/summary",
    response_model=StandardResponse[DashboardSummary],
    summary="CEO 驾驶舱汇总",
    description="获取 CEO 驾驶舱汇总数据，包括项目统计、消耗统计、待处理事项、告警列表",
)
async def get_ceo_dashboard_summary(
    period: Optional[str] = Query(None, description="统计周期 (YYYY-MM)，默认当月"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(require_ceo_access),
):
    """
    CEO 驾驶舱汇总 API

    权限：仅 admin/ceo 可访问

    返回：
    - 项目总数、活跃项目数
    - KPI 数据 (消耗、收入、利润率)
    - 待审核日报数、待审批充值数
    - 异常告警列表

    Phase 1 行为：仅展示数据，不阻断任何操作
    """
    try:
        logger.info(f"CEO dashboard summary request: user={current_user.id}, period={period}")

        summary = service.get_summary(period)

        logger.info(
            f"CEO dashboard summary: total_projects={summary.total_projects}, "
            f"active={summary.active_projects}, spend={summary.kpi.total_spend}, "
            f"pending_reports={summary.pending_reports}, alerts={len(summary.alerts)}"
        )

        return success_response(data=summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in CEO dashboard summary: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="获取驾驶舱数据失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.get(
    "/ceo/detail",
    response_model=StandardResponse[DashboardDetail],
    summary="CEO 驾驶舱详细数据",
    description="获取 CEO 驾驶舱详细数据，包括汇总 + 趋势 + 项目排名 + 待办",
)
async def get_ceo_dashboard_detail(
    period: Optional[str] = Query(None, description="统计周期 (YYYY-MM)"),
    top_n: int = Query(5, ge=1, le=20, description="Top N 项目数"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(require_ceo_access),
):
    """
    CEO 驾驶舱详细数据 API

    权限：仅 admin/ceo 可访问

    返回：
    - 汇总数据
    - 消耗趋势
    - 消耗 Top N 项目
    - CPL 最差 Top N 项目
    - 待办事项
    """
    try:
        logger.info(f"CEO dashboard detail request: user={current_user.id}, top_n={top_n}")

        detail = service.get_detail(period, top_n)

        return success_response(data=detail)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in CEO dashboard detail: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="获取驾驶舱详细数据失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


# ============ CEO Dashboard V3 端点 (毛利=收款-消耗) ============


def get_ceo_dashboard_v3_service(db: Session = Depends(get_db)) -> CEODashboardService:
    """CEO Dashboard V3 Service 依赖注入"""
    return CEODashboardService(db)


def get_profit_service(db: Session = Depends(get_db)) -> ProfitService:
    """Profit Service 依赖注入"""
    return ProfitService(db)


def get_project_balance_service(db: Session = Depends(get_db)) -> ProjectBalanceService:
    """Project Balance Service 依赖注入"""
    return ProjectBalanceService(db)


def get_cash_status_service(db: Session = Depends(get_db)) -> CashStatusService:
    """Cash Status Service 依赖注入"""
    return CashStatusService(db)


@router.get(
    "/ceo/v3/overview",
    response_model=StandardResponse[CEOOverviewResponse],
    summary="CEO 仪表盘概览 (V3)",
    description="获取 CEO 仪表盘全部数据，包括现金、利润、项目余额、待办事项、Top项目",
)
async def get_ceo_overview_v3(
    period: Optional[str] = Query(None, description="统计周期 (YYYY-MM)，默认当月"),
    service: CEODashboardService = Depends(get_ceo_dashboard_v3_service),
    current_user: User = Depends(require_ceo_access),
):
    """
    CEO 仪表盘概览 (V3)

    核心公式：毛利 = 收款 - 消耗（不含手续费）

    权限：仅 admin/ceo 可访问

    返回：
    - 公司现金状况
    - 利润概览（毛利=收款-消耗）
    - 项目余额汇总
    - 待办事项
    - Top 5 项目
    """
    try:
        logger.info(f"CEO dashboard V3 overview: user={current_user.id}, period={period}")

        data = service.get_overview(period)

        # 安全地记录日志（避免 KeyError 或类型错误）
        try:
            profit_rate_pct = data.get('profit_summary', {}).get('profit_rate_pct')
            total_projects = data.get('project_balance_summary', {}).get('total_projects', 0)
            # 处理 Decimal 类型和 None 值
            if profit_rate_pct is not None:
                if hasattr(profit_rate_pct, '__float__'):
                    profit_rate_pct = float(profit_rate_pct)
                logger.info(
                    f"CEO V3 overview: profit_rate={profit_rate_pct:.1f}%, "
                    f"projects={total_projects}"
                )
            else:
                logger.info(
                    f"CEO V3 overview: profit_rate=None (no revenue), "
                    f"projects={total_projects}"
                )
        except Exception as log_error:
            logger.warning(f"Failed to log CEO V3 overview details: {log_error}")

        return success_response(data=data)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in CEO dashboard V3 overview: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="获取 CEO 仪表盘概览失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.get(
    "/ceo/v3/cash-status",
    response_model=StandardResponse[CashStatusResponse],
    summary="公司现金状况",
    description="获取公司现金状况，包括余额、收支明细、周转天数",
)
async def get_cash_status_v3(
    period: Optional[str] = Query(None, description="统计周期 (YYYY-MM)，默认当月"),
    service: CashStatusService = Depends(get_cash_status_service),
    current_user: User = Depends(require_ceo_access),
):
    """
    公司现金状况 API

    公式：期末余额 = 期初余额 + 收入 - 支出

    权限：仅 admin/ceo 可访问
    """
    try:
        logger.info(f"CEO cash status: user={current_user.id}, period={period}")

        data = service.get_cash_status(period)

        return success_response(data=data)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in cash status: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="获取公司现金状况失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.get(
    "/ceo/v3/profit-summary",
    response_model=StandardResponse[ProfitSummaryResponse],
    summary="利润概览",
    description="获取利润概览，核心公式：毛利 = 收款 - 消耗（不含手续费）",
)
async def get_profit_summary_v3(
    period: Optional[str] = Query(None, description="统计周期 (YYYY-MM)，默认当月"),
    service: ProfitService = Depends(get_profit_service),
    current_user: User = Depends(require_ceo_access),
):
    """
    利润概览 API

    核心公式：毛利 = 收款 - 消耗（⚠️ 不含手续费）

    权限：仅 admin/ceo 可访问

    返回：
    - 本月收款（=转化数×单价）
    - 本月消耗（=real_spend）
    - 本月毛利（=收款-消耗）
    - 毛利率、CPL
    """
    try:
        logger.info(f"CEO profit summary: user={current_user.id}, period={period}")

        data = service.get_profit_summary(period)

        logger.info(
            f"Profit V3: revenue={data['revenue']['total']}, "
            f"cost={data['cost']['total']}, "
            f"profit_rate={data['profit']['rate_pct']:.1f}%"
        )

        return success_response(data=data)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in profit summary: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="获取利润概览失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.get(
    "/ceo/v3/project-balance",
    response_model=StandardResponse[ProjectBalanceResponse],
    summary="项目余额列表",
    description="获取所有项目余额，公式：余额 = 累计收款 - 累计消耗",
)
async def get_project_balance_v3(
    period: Optional[str] = Query(None, description="统计周期 (YYYY-MM)"),
    service: ProjectBalanceService = Depends(get_project_balance_service),
    current_user: User = Depends(require_ceo_access),
):
    """
    项目余额列表 API

    公式：余额 = 累计收款 - 累计消耗

    权限：仅 admin/ceo 可访问

    状态说明：
    - prepaid: 客户预付
    - pending_refund: 待退款
    - refunded: 已退款
    - settled: 已结清
    - need_topup: 需补款
    """
    try:
        logger.info(f"CEO project balance: user={current_user.id}, period={period}")

        data = service.get_all_balances(period)

        return success_response(data=data)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in project balance: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="获取项目余额失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.get(
    "/ceo/v3/action-items",
    response_model=StandardResponse[ActionItemsResponse],
    summary="待办事项",
    description="获取待办事项，包括异常项目、待处理日报、待退款项目",
)
async def get_action_items_v3(
    period: Optional[str] = Query(None, description="统计周期 (YYYY-MM)"),
    service: CEODashboardService = Depends(get_ceo_dashboard_v3_service),
    current_user: User = Depends(require_ceo_access),
):
    """
    待办事项 API

    权限：仅 admin/ceo 可访问

    返回：
    - 异常项目（毛利率<10%或亏损）
    - 待处理日报
    - 待退款项目
    """
    try:
        logger.info(f"CEO action items: user={current_user.id}, period={period}")

        data = service.get_action_items(period)

        return success_response(data=data)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in action items: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="获取待办事项失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.get(
    "/ceo/v3/project-ranking",
    response_model=StandardResponse[ProjectRankingResponse],
    summary="项目毛利排行",
    description="获取项目毛利排行，按毛利从高到低排序",
)
async def get_project_ranking_v3(
    period: Optional[str] = Query(None, description="统计周期 (YYYY-MM)，默认当月"),
    limit: int = Query(10, ge=1, le=50, description="返回项目数"),
    service: ProfitService = Depends(get_profit_service),
    current_user: User = Depends(require_ceo_access),
):
    """
    项目毛利排行 API

    核心公式：毛利 = 收款 - 消耗（不含手续费）

    权限：仅 admin/ceo 可访问

    返回：
    - 项目列表（按毛利排序）
    - 每个项目：收入、成本、毛利、毛利率、CPL
    - 状态：healthy(>=20%) / warning(>=10%) / danger(>=0%) / loss(<0%)
    """
    try:
        logger.info(f"CEO project ranking: user={current_user.id}, period={period}, limit={limit}")

        data = service.get_project_ranking(period, limit)

        return success_response(data=data)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in project ranking: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="获取项目排行失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.get(
    "/ceo/v3/trend",
    response_model=StandardResponse[TrendDataResponse],
    summary="趋势数据",
    description="获取收入、消耗、毛利的时间趋势",
)
async def get_trend_v3(
    period: Optional[str] = Query(None, description="统计周期 (YYYY-MM)，默认当月"),
    granularity: Literal["daily", "weekly", "monthly"] = Query(
        "daily", description="数据粒度"
    ),
    service: CEODashboardService = Depends(get_ceo_dashboard_v3_service),
    current_user: User = Depends(require_ceo_access),
):
    """
    趋势数据 API

    权限：仅 admin/ceo 可访问

    返回：
    - 按日/周/月聚合的数据
    - 每个时间点：收入、消耗、毛利、转化数
    """
    try:
        logger.info(f"CEO trend V3: user={current_user.id}, period={period}, granularity={granularity}")

        data = service.get_trend_data(period, granularity)

        return success_response(data=data)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in trend V3: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="获取趋势数据失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )
