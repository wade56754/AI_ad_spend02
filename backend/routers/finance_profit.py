"""
财务利润报表 API 路由 (重构版)

SoT Reference: PROFIT_SOT.md v1.1 §3
SoT Reference: MASTER.md v4.4 §2.4 (7角色模型)

端点列表：
- POST /generate - 生成/刷新利润聚合
- GET /monthly - 获取月度利润表
- GET /daily - 获取日度利润数据
- GET /projects/{project_id} - 获取项目利润明细
- GET /accounts/{account_id} - 获取账户消耗明细
- GET /summary - 获取整体利润汇总
- GET /overview - 获取利润概览
- GET /by-project - 按项目统计利润
- GET /by-account - 按账户统计利润
- GET /by-channel - 按渠道统计利润
- GET /trend - 获取利润趋势
- POST /compare - 利润对比分析

权限矩阵 (MASTER.md v4.4 §2.4 - 7角色模型):
- admin, finance: 全部权限
- ceo: 只读全局利润概览
- project_owner: 自己负责的项目利润
- account_manager: 自己管理的项目/账户
- pitcher: 自己创建日报对应的账户
- supervisor: 团队相关利润概览

依赖代码块:
- response-envelope: success_response, error_response
- pagination: create_paginated_response
- error-codes: BusinessErrorCodes, SystemErrorCodes

Version: 2.0
"""

import logging
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.dependencies import get_current_user, require_role
from backend.core.response import success_response, error_response
from backend.core.pagination import create_paginated_response, PaginationParams, get_pagination
from backend.core.error_codes import (
    AuthErrorCodes,
    BusinessErrorCodes,
    SystemErrorCodes,
)
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    ResourceConflictError,
    PermissionDeniedError,
)
from backend.models import User, Project, AdAccount
from backend.schemas.profit import (
    GenerateProfitRequest,
    GetMonthlyProfitParams,
    GetDailyProfitParams,
    GetProjectProfitParams,
    GetAccountProfitParams,
    GetProfitSummaryParams,
    ProfitPeriodType,
    ProfitGranularity,
    GenerateProfitResponseData,
    MonthlyProfitResponseData,
    DailyProfitResponseData,
    ProjectProfitResponseData,
    AccountProfitResponseData,
    ProfitSummaryResponseData,
    PeriodInfo,
    GenerateSummary,
    ProfitSummaryData,
    ProjectProfitItem,
    AccountProfitItem,
    DailyProfitItem,
    TrendPoint,
    ProjectInfo,
    AccountInfo,
    ProjectDetailSummary,
    AccountDetailSummary,
    OverallSummary,
    TopProjectItem,
)
from backend.services.finance.profit_service import ProfitService, get_profit_service
from backend.services.finance_service import FinanceService
from backend.schemas.finance import (
    ProfitSummaryResponse,
    ProfitOverviewResponse,
    ProfitByProjectResponse,
    ProfitByAccountResponse,
    ProfitByChannelResponse,
    ProfitTrendResponse,
    ProfitCompareResponse,
    ProfitCompareRequest,
    TrendGranularityEnum,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/finance/profit", tags=["finance-profit"])


# ============ 错误码常量 (PROFIT_SOT.md v1.1 §5) ============

PROFIT_ERROR_CODES = {
    "PROFIT_001": {"message": "周期参数无效", "status_code": 400},
    "PROFIT_002": {"message": "开始日期不能是未来", "status_code": 400},
    "PROFIT_003": {"message": "项目不存在", "status_code": 404},
    "PROFIT_004": {"message": "周期已锁定，无法刷新", "status_code": 409},
    "PROFIT_005": {"message": "指定周期无数据", "status_code": 404},
    "PROFIT_006": {"message": "禁止手工修改聚合数据", "status_code": 403},
    "PROFIT_007": {"message": "账户不存在", "status_code": 404},
    "PROFIT_008": {"message": "日期范围超出限制", "status_code": 400},
}


def _get_error_response(error_code: str, details: dict = None):
    """获取错误响应 (使用标准 error_response)"""
    error_info = PROFIT_ERROR_CODES.get(error_code, {
        "message": "未知错误",
        "status_code": 400
    })
    return error_response(
        code=error_code,
        message=error_info["message"],
        status_code=error_info["status_code"],
        details=details
    )


def _handle_service_exception(e: Exception):
    """处理服务层异常，转换为标准响应"""
    if isinstance(e, BusinessLogicError):
        return _get_error_response(e.error_code, getattr(e, 'details', None))
    elif isinstance(e, ResourceNotFoundError):
        return _get_error_response(e.error_code, getattr(e, 'details', None))
    elif isinstance(e, ResourceConflictError):
        return _get_error_response(e.error_code, getattr(e, 'details', None))
    elif isinstance(e, PermissionDeniedError):
        return error_response(
            code="PERM-001",
            message=str(e),
            status_code=403
        )
    else:
        logger.exception(f"Unexpected error: {e}")
        return error_response(
            code="SYS-500",
            message="系统内部错误",
            status_code=500
        )


# ============ POST /generate ============

@router.post(
    "/generate",
    summary="生成/刷新利润聚合",
    description="生成或刷新指定周期的利润聚合数据。仅 admin/finance 角色可访问。",
    responses={
        200: {"description": "生成成功"},
        400: {"description": "参数错误 (PROFIT_001, PROFIT_002)"},
        403: {"description": "权限不足 (AUTH_500)"},
        404: {"description": "项目不存在 (PROFIT_003)"},
        409: {"description": "周期已锁定 (PROFIT_004)"},
    }
)
async def generate_profit_aggregates(
    request: GenerateProfitRequest,
    current_user: User = Depends(require_role(["admin", "finance"])),
    db: Session = Depends(get_db),
):
    """
    生成/刷新利润聚合数据

    - **period_type**: 周期类型 (daily/monthly)
    - **period_start**: 周期开始日期
    - **period_end**: 周期结束日期
    - **project_id**: 可选，指定项目ID
    - **force_refresh**: 强制刷新已锁定数据（仅 admin 可用）

    对齐 PROFIT_SOT.md v1.1 §3.2
    """
    logger.info(
        f"POST /finance/profit/generate: user={current_user.email}, "
        f"period_type={request.period_type}, "
        f"period_start={request.period_start}, period_end={request.period_end}"
    )

    # force_refresh 仅 admin 可用 (BR-PROFIT-004)
    if request.force_refresh and current_user.role != "admin":
        return error_response(
            code="PERM-001",
            message="强制刷新仅管理员可用",
            status_code=403
        )

    try:
        service = get_profit_service(db)
        result = service.generate_period_aggregates(
            period_type=request.period_type.value,
            period_start=request.period_start,
            period_end=request.period_end,
            project_id=request.project_id,
            overwrite=True,
            force_refresh=request.force_refresh,
            user_id=current_user.id,
        )

        # 转换为响应模型
        response_data = GenerateProfitResponseData(
            generated_count=result["generated_count"],
            period=PeriodInfo(
                type=result["period"]["type"],
                start=request.period_start,
                end=request.period_end,
            ),
            summary=GenerateSummary(
                total_projects=result["summary"]["total_projects"],
                total_accounts=result["summary"].get("total_accounts", 0),
                total_revenue=result["summary"]["total_revenue"],
                total_cost=result["summary"]["total_cost"],
                gross_profit=result["summary"]["gross_profit"],
            )
        )

        return success_response(
            data=response_data.model_dump(),
            message="利润聚合生成成功"
        )

    except (BusinessLogicError, ResourceNotFoundError, ResourceConflictError) as e:
        return _handle_service_exception(e)
    except Exception as e:
        return _handle_service_exception(e)


# ============ GET /monthly ============

@router.get(
    "/monthly",
    summary="获取月度利润表",
    description="获取指定月份的月度利润表。仅 admin/finance 角色可访问。",
    responses={
        200: {"description": "查询成功"},
        400: {"description": "参数错误 (PROFIT_001)"},
        403: {"description": "权限不足 (AUTH_500)"},
        404: {"description": "无数据 (PROFIT_005)"},
    }
)
async def get_monthly_profit(
    year: int = Query(..., ge=2020, le=2099, description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    include_accounts: bool = Query(False, description="是否包含账户明细"),
    current_user: User = Depends(require_role(["admin", "finance"])),
    db: Session = Depends(get_db),
):
    """
    获取月度利润表

    - **year**: 年份 (2020-2099)
    - **month**: 月份 (1-12)
    - **project_id**: 可选，指定项目ID
    - **include_accounts**: 是否包含账户明细

    对齐 PROFIT_SOT.md v1.1 §3.3
    """
    logger.info(
        f"GET /finance/profit/monthly: user={current_user.email}, "
        f"year={year}, month={month}, project_id={project_id}"
    )

    try:
        # 计算月度日期范围
        period_start = date(year, month, 1)
        if month == 12:
            period_end = date(year + 1, 1, 1)
        else:
            period_end = date(year, month + 1, 1)
        # period_end 是下月1号，减1天得到月末
        from datetime import timedelta
        period_end = period_end - timedelta(days=1)

        service = get_profit_service(db)
        result = service.get_period_aggregates(
            period_type="monthly",
            period_start=period_start,
            period_end=period_end,
            project_id=project_id,
            include_accounts=include_accounts,
        )

        # 转换为响应模型
        by_project_items = []
        for proj_data in result.get("by_project", []):
            accounts = None
            if include_accounts and proj_data.get("accounts"):
                accounts = [
                    AccountProfitItem(**acc) for acc in proj_data["accounts"]
                ]
            by_project_items.append(ProjectProfitItem(
                project_id=proj_data["project_id"],
                project_name=proj_data.get("project_name", ""),
                revenue=proj_data.get("revenue", "0.00"),
                cost=proj_data.get("cost", "0.00"),
                gross_profit=proj_data.get("gross_profit", "0.00"),
                gross_margin_pct=proj_data.get("gross_margin_pct"),
                conversions=proj_data.get("conversions", 0),
                real_spend=proj_data.get("real_spend", "0.00"),
                report_count=proj_data.get("report_count", 0),
                accounts=accounts,
            ))

        summary_data = result.get("summary", {})
        response_data = MonthlyProfitResponseData(
            period=PeriodInfo(year=year, month=month),
            summary=ProfitSummaryData(
                total_revenue=summary_data.get("total_revenue", "0.00"),
                total_cost=summary_data.get("total_cost", "0.00"),
                gross_profit=summary_data.get("gross_profit", "0.00"),
                gross_margin_pct=summary_data.get("gross_margin_pct"),
                total_conversions=summary_data.get("total_conversions", 0),
                total_real_spend=summary_data.get("total_real_spend", "0.00"),
                total_topup=summary_data.get("total_topup", "0.00"),
                report_count=summary_data.get("report_count", 0),
                is_locked=result.get("is_locked", False),
            ),
            by_project=by_project_items,
        )

        return success_response(
            data=response_data.model_dump(),
            message="查询成功"
        )

    except (BusinessLogicError, ResourceNotFoundError) as e:
        return _handle_service_exception(e)
    except Exception as e:
        return _handle_service_exception(e)


# ============ GET /daily ============

@router.get(
    "/daily",
    summary="获取日度利润数据",
    description="获取指定日期范围的日度利润数据。仅 admin/finance 角色可访问。",
    responses={
        200: {"description": "查询成功"},
        400: {"description": "参数错误 (PROFIT_001, PROFIT_008)"},
        403: {"description": "权限不足 (AUTH_500)"},
    }
)
async def get_daily_profit(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(require_role(["admin", "finance"])),
    db: Session = Depends(get_db),
):
    """
    获取日度利润数据

    - **start_date**: 开始日期
    - **end_date**: 结束日期
    - **project_id**: 可选，指定项目ID
    - **page**: 页码
    - **page_size**: 每页数量

    对齐 PROFIT_SOT.md v1.1 §3.4
    """
    logger.info(
        f"GET /finance/profit/daily: user={current_user.email}, "
        f"start_date={start_date}, end_date={end_date}"
    )

    # 参数校验
    if end_date < start_date:
        return _get_error_response("PROFIT_001", {
            "start_date": str(start_date),
            "end_date": str(end_date)
        })

    if (end_date - start_date).days > 366:
        return _get_error_response("PROFIT_008", {
            "days": (end_date - start_date).days,
            "max_days": 366
        })

    try:
        service = get_profit_service(db)
        result = service.get_period_aggregates(
            period_type="daily",
            period_start=start_date,
            period_end=end_date,
            project_id=project_id,
        )

        # 分页处理
        by_project = result.get("by_project", [])
        total = len(by_project)
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = by_project[start_idx:end_idx]

        # 转换为 DailyProfitItem
        items = []
        for proj_data in paginated_items:
            items.append(DailyProfitItem(
                period_start=start_date,
                period_end=end_date,
                project_id=proj_data.get("project_id"),
                project_name=proj_data.get("project_name", ""),
                revenue=proj_data.get("revenue", "0.00"),
                cost=proj_data.get("cost", "0.00"),
                gross_profit=proj_data.get("gross_profit", "0.00"),
                conversions=proj_data.get("conversions", 0),
            ))

        response_data = DailyProfitResponseData(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

        return success_response(
            data=response_data.model_dump(),
            message="查询成功"
        )

    except (BusinessLogicError, ResourceNotFoundError) as e:
        return _handle_service_exception(e)
    except Exception as e:
        return _handle_service_exception(e)


# ============ GET /projects/{project_id} ============

@router.get(
    "/projects/{project_id}",
    summary="获取项目利润明细",
    description="获取单个项目的利润明细。account_manager 仅可访问自己管理的项目。",
    responses={
        200: {"description": "查询成功"},
        400: {"description": "参数错误"},
        403: {"description": "权限不足 (AUTH_500)"},
        404: {"description": "项目不存在 (PROFIT_003)"},
    }
)
async def get_project_profit(
    project_id: int,
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    granularity: ProfitGranularity = Query(ProfitGranularity.MONTHLY, description="粒度"),
    current_user: User = Depends(require_role(["admin", "finance", "ceo", "project_owner", "account_manager"])),
    db: Session = Depends(get_db),
):
    """
    获取项目利润明细

    - **project_id**: 项目ID
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    - **granularity**: 粒度 (daily/monthly)

    权限控制 (PROFIT_SOT.md v1.1 §3.5):
    - admin, finance: 所有项目
    - ceo: 所有项目（只读）
    - project_owner: 自己负责的项目
    - account_manager: 仅自己管理的项目

    对齐 PROFIT_SOT.md v1.1 §3.5
    """
    logger.info(
        f"GET /finance/profit/projects/{project_id}: user={current_user.email}, "
        f"start_date={start_date}, end_date={end_date}, granularity={granularity}"
    )

    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return _get_error_response("PROFIT_003", {"project_id": project_id})

    # 权限检查: account_manager 仅可访问自己管理的项目 (MASTER.md v4.4 §2.4)
    if current_user.role == "account_manager":
        if not hasattr(project, 'account_manager_id') or project.account_manager_id != current_user.id:
            return error_response(
                code="PERM-001",
                message="无权限访问该项目",
                status_code=403
            )

    # 参数校验
    if end_date < start_date:
        return _get_error_response("PROFIT_001", {
            "start_date": str(start_date),
            "end_date": str(end_date)
        })

    try:
        service = get_profit_service(db)
        result = service.get_period_aggregates(
            period_type=granularity.value,
            period_start=start_date,
            period_end=end_date,
            project_id=project_id,
            include_accounts=True,
        )

        # 构建趋势数据
        trend = []
        by_project = result.get("by_project", [])
        if by_project:
            # 简化：将 by_project 作为趋势点
            for proj_data in by_project:
                trend.append(TrendPoint(
                    date=start_date,
                    revenue=proj_data.get("revenue", "0.00"),
                    cost=proj_data.get("cost", "0.00"),
                    conversions=proj_data.get("conversions", 0),
                    real_spend=proj_data.get("real_spend"),
                ))

        # 构建账户明细
        by_account = []
        if by_project and by_project[0].get("accounts"):
            for acc_data in by_project[0]["accounts"]:
                by_account.append(AccountProfitItem(
                    account_id=acc_data["account_id"],
                    account_name=acc_data.get("account_name", ""),
                    revenue=acc_data.get("revenue", "0.00"),
                    cost=acc_data.get("cost", "0.00"),
                    gross_profit=acc_data.get("gross_profit", "0.00"),
                    conversions=acc_data.get("conversions", 0),
                    real_spend=acc_data.get("real_spend", "0.00"),
                ))

        summary_data = result.get("summary", {})
        response_data = ProjectProfitResponseData(
            project=ProjectInfo(
                id=project.id,
                name=project.name,
                unit_price=getattr(project, 'unit_price', None),
            ),
            period=PeriodInfo(
                start=start_date,
                end=end_date,
            ),
            summary=ProjectDetailSummary(
                revenue=summary_data.get("total_revenue", "0.00"),
                cost=summary_data.get("total_cost", "0.00"),
                gross_profit=summary_data.get("gross_profit", "0.00"),
                gross_margin_pct=summary_data.get("gross_margin_pct"),
                conversions=summary_data.get("total_conversions", 0),
                avg_unit_cost=summary_data.get("avg_unit_cost"),
            ),
            trend=trend,
            by_account=by_account,
        )

        return success_response(
            data=response_data.model_dump(),
            message="查询成功"
        )

    except (BusinessLogicError, ResourceNotFoundError) as e:
        return _handle_service_exception(e)
    except Exception as e:
        return _handle_service_exception(e)


# ============ GET /accounts/{account_id} ============

@router.get(
    "/accounts/{account_id}",
    summary="获取账户消耗明细",
    description="获取单个广告账户的消耗与利润明细。pitcher 仅可访问自己创建日报的账户。",
    responses={
        200: {"description": "查询成功"},
        400: {"description": "参数错误"},
        403: {"description": "权限不足 (AUTH_500)"},
        404: {"description": "账户不存在 (PROFIT_007)"},
    }
)
async def get_account_profit(
    account_id: int,
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    current_user: User = Depends(require_role(["admin", "finance", "ceo", "project_owner", "account_manager", "pitcher"])),
    db: Session = Depends(get_db),
):
    """
    获取账户消耗明细

    - **account_id**: 广告账户ID
    - **start_date**: 开始日期
    - **end_date**: 结束日期

    权限控制 (PROFIT_SOT.md v1.1 §3.6):
    - admin, finance: 所有账户
    - ceo: 所有账户（只读）
    - project_owner: 自己负责的项目下的账户
    - account_manager: 自己管理的项目下的账户
    - pitcher: 仅自己创建日报对应的账户

    对齐 PROFIT_SOT.md v1.1 §3.6
    """
    logger.info(
        f"GET /finance/profit/accounts/{account_id}: user={current_user.email}, "
        f"start_date={start_date}, end_date={end_date}"
    )

    # 验证账户存在
    account = db.query(AdAccount).filter(AdAccount.id == account_id).first()
    if not account:
        return _get_error_response("PROFIT_007", {"account_id": account_id})

    # 权限检查 (MASTER.md v4.4 §2.4 - 7角色模型)
    if current_user.role == "account_manager":
        # account_manager: 检查是否管理该账户所属项目
        project = db.query(Project).filter(Project.id == account.project_id).first()
        if project and hasattr(project, 'account_manager_id'):
            if project.account_manager_id != current_user.id:
                return error_response(
                    code="PERM-001",
                    message="无权限访问该账户",
                    status_code=403
                )
    elif current_user.role == "pitcher":
        # pitcher: 检查是否有该账户的日报创建记录
        from backend.models import DailyReport
        has_report = db.query(DailyReport).filter(
            DailyReport.ad_account_id == account_id,
            DailyReport.submitted_by == current_user.id
        ).first()
        if not has_report:
            return error_response(
                code="PERM-001",
                message="无权限访问该账户",
                status_code=403
            )

    # 参数校验
    if end_date < start_date:
        return _get_error_response("PROFIT_001", {
            "start_date": str(start_date),
            "end_date": str(end_date)
        })

    try:
        service = get_profit_service(db)
        result = service.get_period_aggregates(
            period_type="daily",
            period_start=start_date,
            period_end=end_date,
            ad_account_id=account_id,
        )

        # 获取关联项目信息
        project = db.query(Project).filter(Project.id == account.project_id).first()
        project_name = project.name if project else ""

        summary_data = result.get("summary", {})

        # 构建日趋势数据
        daily_trend = []
        # 简化实现：使用汇总数据构建单点趋势
        if summary_data:
            daily_trend.append(TrendPoint(
                date=start_date,
                revenue=summary_data.get("total_revenue", "0.00"),
                cost=summary_data.get("total_cost", "0.00"),
                conversions=summary_data.get("total_conversions", 0),
                real_spend=summary_data.get("total_real_spend"),
            ))

        response_data = AccountProfitResponseData(
            account=AccountInfo(
                id=account.id,
                name=account.name,
                account_code=getattr(account, 'account_code', None),
                project_id=account.project_id,
                project_name=project_name,
            ),
            period=PeriodInfo(
                start=start_date,
                end=end_date,
            ),
            summary=AccountDetailSummary(
                revenue=summary_data.get("total_revenue", "0.00"),
                cost=summary_data.get("total_cost", "0.00"),
                gross_profit=summary_data.get("gross_profit", "0.00"),
                gross_margin_pct=summary_data.get("gross_margin_pct"),
                conversions=summary_data.get("total_conversions", 0),
                real_spend=summary_data.get("total_real_spend", "0.00"),
                avg_unit_cost=summary_data.get("avg_unit_cost"),
                report_count=summary_data.get("report_count", 0),
            ),
            daily_trend=daily_trend,
        )

        return success_response(
            data=response_data.model_dump(),
            message="查询成功"
        )

    except (BusinessLogicError, ResourceNotFoundError) as e:
        return _handle_service_exception(e)
    except Exception as e:
        return _handle_service_exception(e)


# ============ GET /summary ============

@router.get(
    "/summary",
    summary="获取整体利润汇总",
    description="获取整体利润汇总（跨所有项目）。仅 admin/finance 角色可访问。",
    responses={
        200: {"description": "查询成功"},
        400: {"description": "参数错误 (PROFIT_001)"},
        403: {"description": "权限不足 (AUTH_500)"},
        404: {"description": "无数据 (PROFIT_005)"},
    }
)
async def get_profit_summary(
    year: int = Query(..., ge=2020, le=2099, description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    current_user: User = Depends(require_role(["admin", "finance"])),
    db: Session = Depends(get_db),
):
    """
    获取整体利润汇总

    - **year**: 年份
    - **month**: 月份

    对齐 PROFIT_SOT.md v1.1 §3.7
    """
    logger.info(
        f"GET /finance/profit/summary: user={current_user.email}, "
        f"year={year}, month={month}"
    )

    try:
        # 计算月度日期范围
        period_start = date(year, month, 1)
        if month == 12:
            period_end = date(year + 1, 1, 1)
        else:
            period_end = date(year, month + 1, 1)
        from datetime import timedelta
        period_end = period_end - timedelta(days=1)

        service = get_profit_service(db)
        result = service.get_period_aggregates(
            period_type="monthly",
            period_start=period_start,
            period_end=period_end,
            project_id=None,  # 全局汇总
        )

        summary_data = result.get("summary", {})
        by_project = result.get("by_project", [])

        # 获取 TOP 项目
        top_projects = []
        sorted_projects = sorted(
            by_project,
            key=lambda x: float(x.get("gross_profit", 0)),
            reverse=True
        )[:5]
        for proj_data in sorted_projects:
            top_projects.append(TopProjectItem(
                project_id=proj_data["project_id"],
                project_name=proj_data.get("project_name", ""),
                gross_profit=proj_data.get("gross_profit", "0.00"),
            ))

        response_data = ProfitSummaryResponseData(
            period=PeriodInfo(year=year, month=month),
            overall=OverallSummary(
                total_revenue=summary_data.get("total_revenue", "0.00"),
                total_cost=summary_data.get("total_cost", "0.00"),
                gross_profit=summary_data.get("gross_profit", "0.00"),
                gross_margin_pct=summary_data.get("gross_margin_pct"),
                total_conversions=summary_data.get("total_conversions", 0),
                total_topup=summary_data.get("total_topup", "0.00"),
                net_transfer=summary_data.get("net_transfer", "0.00"),
                project_count=len(by_project),
                account_count=summary_data.get("account_count", 0),
                report_count=summary_data.get("report_count", 0),
            ),
            top_projects=top_projects,
            is_locked=result.get("is_locked", False),
        )

        return success_response(
            data=response_data.model_dump(),
            message="查询成功"
        )

    except (BusinessLogicError, ResourceNotFoundError) as e:
        return _handle_service_exception(e)
    except Exception as e:
        return _handle_service_exception(e)


# ============ 简化版 API (测试用) ============
# 这些端点提供简化的利润查询功能，用于前端展示和测试

@router.get(
    "/overview",
    summary="获取利润概览",
    description="获取今日/本周/本月利润概览，包含环比变化。",
    responses={
        200: {"description": "查询成功"},
        403: {"description": "权限不足"},
    }
)
async def get_profit_overview(
    current_user: User = Depends(require_role(["admin", "finance", "ceo", "supervisor"])),
    db: Session = Depends(get_db),
):
    """
    获取利润概览（今日/本周/本月）

    权限: admin, finance, ceo, supervisor
    """
    logger.info(f"GET /finance/profit/overview: user={current_user.email}")

    try:
        service = FinanceService(db)
        overview = service.get_profit_overview()

        return success_response(
            data=overview.model_dump(),
            message="查询成功"
        )
    except Exception as e:
        return _handle_service_exception(e)


@router.get(
    "/by-project",
    summary="按项目统计利润",
    description="获取按项目维度的利润统计。",
    responses={
        200: {"description": "查询成功"},
        400: {"description": "参数错误 (BIZ_001)"},
        403: {"description": "权限不足"},
    }
)
async def get_profit_by_project(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    current_user: User = Depends(require_role(["admin", "finance", "ceo", "supervisor"])),
    db: Session = Depends(get_db),
):
    """
    按项目统计利润

    权限: admin, finance, ceo, supervisor
    """
    logger.info(
        f"GET /finance/profit/by-project: user={current_user.email}, "
        f"start_date={start_date}, end_date={end_date}"
    )

    # 参数校验
    if start_date and end_date and end_date < start_date:
        return error_response(
            code="BIZ-001",
            message="开始日期不能晚于结束日期",
            status_code=400
        )

    try:
        service = FinanceService(db)
        result = service.get_profit_by_project(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        return success_response(
            data=result.model_dump(),
            message="查询成功"
        )
    except Exception as e:
        return _handle_service_exception(e)


@router.get(
    "/by-account",
    summary="按账户统计利润",
    description="获取按广告账户维度的利润统计。",
    responses={
        200: {"description": "查询成功"},
        400: {"description": "参数错误 (BIZ_001)"},
        403: {"description": "权限不足"},
        404: {"description": "项目不存在 (BIZ_002)"},
    }
)
async def get_profit_by_account(
    project_id: Optional[int] = Query(None, description="项目ID过滤"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    current_user: User = Depends(require_role(["admin", "finance", "ceo", "supervisor"])),
    db: Session = Depends(get_db),
):
    """
    按账户统计利润

    权限: admin, finance, ceo, supervisor
    """
    logger.info(
        f"GET /finance/profit/by-account: user={current_user.email}, "
        f"project_id={project_id}"
    )

    # 参数校验
    if start_date and end_date and end_date < start_date:
        return error_response(
            code="BIZ-001",
            message="开始日期不能晚于结束日期",
            status_code=400
        )

    # 验证项目存在
    if project_id:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return error_response(
                code="RES-001",
                message=f"项目不存在: project_id={project_id}",
                status_code=404
            )

    try:
        service = FinanceService(db)
        result = service.get_profit_by_account(
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        return success_response(
            data=result.model_dump(),
            message="查询成功"
        )
    except Exception as e:
        return _handle_service_exception(e)


@router.get(
    "/by-channel",
    summary="按渠道统计利润",
    description="获取按渠道维度的利润统计。",
    responses={
        200: {"description": "查询成功"},
        400: {"description": "参数错误 (BIZ_001)"},
        403: {"description": "权限不足"},
    }
)
async def get_profit_by_channel(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    current_user: User = Depends(require_role(["admin", "finance", "ceo", "supervisor"])),
    db: Session = Depends(get_db),
):
    """
    按渠道统计利润

    权限: admin, finance, ceo, supervisor
    """
    logger.info(f"GET /finance/profit/by-channel: user={current_user.email}")

    # 参数校验
    if start_date and end_date and end_date < start_date:
        return error_response(
            code="BIZ-001",
            message="开始日期不能晚于结束日期",
            status_code=400
        )

    try:
        service = FinanceService(db)
        result = service.get_profit_by_channel(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        return success_response(
            data=result.model_dump(),
            message="查询成功"
        )
    except Exception as e:
        return _handle_service_exception(e)


@router.get(
    "/trend",
    summary="获取利润趋势",
    description="获取指定时间段的利润趋势数据。",
    responses={
        200: {"description": "查询成功"},
        400: {"description": "参数错误 (BIZ_001)"},
        403: {"description": "权限不足"},
    }
)
async def get_profit_trend(
    granularity: str = Query("daily", description="趋势粒度: daily/weekly/monthly"),
    project_id: Optional[int] = Query(None, description="项目ID过滤"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(require_role(["admin", "finance", "ceo", "supervisor"])),
    db: Session = Depends(get_db),
):
    """
    获取利润趋势

    权限: admin, finance, ceo, supervisor
    """
    logger.info(
        f"GET /finance/profit/trend: user={current_user.email}, "
        f"granularity={granularity}"
    )

    # 参数校验
    if start_date and end_date and end_date < start_date:
        return error_response(
            code="BIZ-001",
            message="开始日期不能晚于结束日期",
            status_code=400
        )

    # 验证 granularity
    valid_granularities = ["daily", "weekly", "monthly"]
    if granularity not in valid_granularities:
        return error_response(
            code="VAL-001",
            message=f"无效的粒度值: {granularity}",
            status_code=400
        )

    try:
        service = FinanceService(db)
        result = service.get_profit_trend(
            granularity=granularity,
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
        )

        return success_response(
            data=result.model_dump(),
            message="查询成功"
        )
    except Exception as e:
        return _handle_service_exception(e)


@router.post(
    "/compare",
    summary="利润对比分析",
    description="对比多个项目的利润数据。",
    responses={
        200: {"description": "对比成功"},
        400: {"description": "参数错误"},
        403: {"description": "权限不足"},
        404: {"description": "项目不存在 (BIZ_002)"},
    }
)
async def compare_profit(
    request: ProfitCompareRequest,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(require_role(["admin", "finance", "ceo", "supervisor"])),
    db: Session = Depends(get_db),
):
    """
    利润对比分析

    权限: admin, finance, ceo, supervisor
    """
    logger.info(
        f"POST /finance/profit/compare: user={current_user.email}, "
        f"project_ids={request.project_ids}"
    )

    # 验证项目存在
    for pid in request.project_ids:
        project = db.query(Project).filter(Project.id == pid).first()
        if not project:
            return error_response(
                code="RES-001",
                message=f"项目不存在: project_id={pid}",
                status_code=404
            )

    try:
        service = FinanceService(db)
        result = service.compare_profit(
            project_ids=request.project_ids,
            start_date=start_date or request.start_date,
            end_date=end_date or request.end_date,
        )

        return success_response(
            data=result.model_dump(),
            message="查询成功"
        )
    except Exception as e:
        return _handle_service_exception(e)
