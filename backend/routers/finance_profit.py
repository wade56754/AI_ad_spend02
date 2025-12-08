"""
财务利润 API 路由
处理利润汇总、利润分析等财务利润相关接口

SoT 对齐:
- DATA_SCHEMA.md v5.2: daily_reports, projects, ad_accounts, channels 表结构
- BUSINESS_RULES.md v3.1: 利润计算公式
  - revenue = conversions_final × unit_price
  - cost = real_spend + fee
  - profit = revenue - cost
  - profit_margin = profit / revenue × 100
- ERROR_CODES_SOT.md v2.1: 错误码规范
- AUTH_SPEC.md v2.0: 权限矩阵 (admin, finance, data_operator)

Version: 2.0
Author: Claude Code
"""

from datetime import date
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.dependencies import require_role
from backend.core.response import success_response, error_response, StandardResponse
from backend.core.error_codes import BusinessErrorCodes
from backend.models import User
from backend.services.finance_service import FinanceService
from backend.schemas.finance import (
    ProfitSummaryResponse,
    ProfitByProjectResponse,
    ProfitByAccountResponse,
    ProfitByChannelResponse,
    ProfitTrendResponse,
    ProfitCompareResponse,
    ProfitOverviewResponse,
    TrendGranularityEnum,
)
from backend.exceptions import ResourceNotFoundException, BusinessRuleException


router = APIRouter(prefix="/finance/profit", tags=["finance-profit"])


@router.get("/summary", response_model=StandardResponse[ProfitSummaryResponse])
async def get_profit_summary(
    project_id: Optional[int] = Query(None, description="项目ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"]))
):
    """
    获取利润汇总

    需要权限: ADMIN 或 FINANCE 或 DATA_OPERATOR

    参数:
    - project_id: 项目ID (可选，不传则返回全部项目汇总)
    - start_date: 开始日期 (可选)
    - end_date: 结束日期 (可选)

    返回:
    - 利润汇总数据，包含明细和总计

    错误码:
    - BIZ_002: 项目不存在 (ResourceNotFoundException)
    - BIZ_001: 日期范围无效 (BusinessRuleException)
    - BIZ_607: 利润统计查询失败 (STATISTICS_QUERY_ERROR)
    """
    try:
        finance_service = FinanceService(db)
        result = finance_service.get_profit_summary(
            project_id=project_id,
            start_date=start_date,
            end_date=end_date
        )

        return success_response(
            data=result,
            message="获取利润汇总成功"
        )

    except ResourceNotFoundException as e:
        return error_response(
            code=e.code,
            message=e.message,
            status_code=404
        )

    except BusinessRuleException as e:
        return error_response(
            code=e.code,
            message=e.message,
            status_code=400
        )

    except Exception as e:
        return error_response(
            code=BusinessErrorCodes.STATISTICS_QUERY_ERROR.code,
            message=f"获取利润汇总失败: {str(e)}",
            status_code=BusinessErrorCodes.STATISTICS_QUERY_ERROR.status_code
        )


@router.get("/overview", response_model=StandardResponse[ProfitOverviewResponse])
async def get_profit_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"]))
):
    """
    获取利润概览

    需要权限: ADMIN 或 FINANCE 或 DATA_OPERATOR

    返回:
    - 今日/本周/本月利润数据
    - 环比变化率
    - TOP利润项目

    错误码:
    - BIZ_607: 利润统计查询失败 (STATISTICS_QUERY_ERROR)
    """
    try:
        finance_service = FinanceService(db)
        result = finance_service.get_profit_overview()

        return success_response(
            data=result,
            message="获取利润概览成功"
        )

    except Exception as e:
        return error_response(
            code=BusinessErrorCodes.STATISTICS_QUERY_ERROR.code,
            message=f"获取利润概览失败: {str(e)}",
            status_code=BusinessErrorCodes.STATISTICS_QUERY_ERROR.status_code
        )


@router.get("/by-project", response_model=StandardResponse[ProfitByProjectResponse])
async def get_profit_by_project(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"]))
):
    """
    按项目维度统计利润

    需要权限: ADMIN 或 FINANCE 或 DATA_OPERATOR

    参数:
    - start_date: 开始日期 (可选)
    - end_date: 结束日期 (可选)
    - limit: 返回数量限制 (默认20，最大100)

    返回:
    - 各项目利润汇总数据

    错误码:
    - BIZ_001: 日期范围无效 (BusinessRuleException)
    - BIZ_607: 利润统计查询失败 (STATISTICS_QUERY_ERROR)
    """
    try:
        finance_service = FinanceService(db)
        result = finance_service.get_profit_by_project(
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

        return success_response(
            data=result,
            message="获取项目利润统计成功"
        )

    except BusinessRuleException as e:
        return error_response(
            code=e.code,
            message=e.message,
            status_code=400
        )

    except Exception as e:
        return error_response(
            code=BusinessErrorCodes.STATISTICS_QUERY_ERROR.code,
            message=f"获取项目利润统计失败: {str(e)}",
            status_code=BusinessErrorCodes.STATISTICS_QUERY_ERROR.status_code
        )


@router.get("/by-account", response_model=StandardResponse[ProfitByAccountResponse])
async def get_profit_by_account(
    project_id: Optional[int] = Query(None, description="项目ID过滤"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"]))
):
    """
    按账户维度统计利润

    需要权限: ADMIN 或 FINANCE 或 DATA_OPERATOR

    参数:
    - project_id: 项目ID过滤 (可选)
    - start_date: 开始日期 (可选)
    - end_date: 结束日期 (可选)
    - limit: 返回数量限制 (默认20，最大100)

    返回:
    - 各账户利润汇总数据

    错误码:
    - BIZ_002: 项目不存在 (ResourceNotFoundException)
    - BIZ_001: 日期范围无效 (BusinessRuleException)
    - BIZ_607: 利润统计查询失败 (STATISTICS_QUERY_ERROR)
    """
    try:
        finance_service = FinanceService(db)
        result = finance_service.get_profit_by_account(
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

        return success_response(
            data=result,
            message="获取账户利润统计成功"
        )

    except ResourceNotFoundException as e:
        return error_response(
            code=e.code,
            message=e.message,
            status_code=404
        )

    except BusinessRuleException as e:
        return error_response(
            code=e.code,
            message=e.message,
            status_code=400
        )

    except Exception as e:
        return error_response(
            code=BusinessErrorCodes.STATISTICS_QUERY_ERROR.code,
            message=f"获取账户利润统计失败: {str(e)}",
            status_code=BusinessErrorCodes.STATISTICS_QUERY_ERROR.status_code
        )


@router.get("/by-channel", response_model=StandardResponse[ProfitByChannelResponse])
async def get_profit_by_channel(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"]))
):
    """
    按渠道维度统计利润

    需要权限: ADMIN 或 FINANCE 或 DATA_OPERATOR

    参数:
    - start_date: 开始日期 (可选)
    - end_date: 结束日期 (可选)
    - limit: 返回数量限制 (默认20，最大100)

    返回:
    - 各渠道利润汇总数据

    错误码:
    - BIZ_001: 日期范围无效 (BusinessRuleException)
    - BIZ_607: 利润统计查询失败 (STATISTICS_QUERY_ERROR)
    """
    try:
        finance_service = FinanceService(db)
        result = finance_service.get_profit_by_channel(
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

        return success_response(
            data=result,
            message="获取渠道利润统计成功"
        )

    except BusinessRuleException as e:
        return error_response(
            code=e.code,
            message=e.message,
            status_code=400
        )

    except Exception as e:
        return error_response(
            code=BusinessErrorCodes.STATISTICS_QUERY_ERROR.code,
            message=f"获取渠道利润统计失败: {str(e)}",
            status_code=BusinessErrorCodes.STATISTICS_QUERY_ERROR.status_code
        )


@router.get("/trend", response_model=StandardResponse[ProfitTrendResponse])
async def get_profit_trend(
    project_id: Optional[int] = Query(None, description="项目ID过滤"),
    channel_id: Optional[int] = Query(None, description="渠道ID过滤"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    granularity: TrendGranularityEnum = Query(
        TrendGranularityEnum.DAILY,
        description="趋势粒度（daily/weekly/monthly）"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"]))
):
    """
    获取利润趋势分析

    需要权限: ADMIN 或 FINANCE 或 DATA_OPERATOR

    参数:
    - project_id: 项目ID过滤 (可选)
    - channel_id: 渠道ID过滤 (可选)
    - start_date: 开始日期 (可选，默认最近30天)
    - end_date: 结束日期 (可选，默认今天)
    - granularity: 趋势粒度 (daily/weekly/monthly)

    返回:
    - 利润趋势数据
    - 环比变化
    - 统计指标（平均/最高/最低利润、波动率）

    错误码:
    - BIZ_001: 日期范围无效 (BusinessRuleException)
    - BIZ_607: 利润统计查询失败 (STATISTICS_QUERY_ERROR)
    """
    try:
        finance_service = FinanceService(db)
        result = finance_service.get_profit_trend(
            project_id=project_id,
            channel_id=channel_id,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity
        )

        return success_response(
            data=result,
            message="获取利润趋势成功"
        )

    except BusinessRuleException as e:
        return error_response(
            code=e.code,
            message=e.message,
            status_code=400
        )

    except Exception as e:
        return error_response(
            code=BusinessErrorCodes.STATISTICS_QUERY_ERROR.code,
            message=f"获取利润趋势失败: {str(e)}",
            status_code=BusinessErrorCodes.STATISTICS_QUERY_ERROR.status_code
        )


@router.post("/compare", response_model=StandardResponse[ProfitCompareResponse])
async def compare_profit(
    project_ids: List[int] = Body(..., embed=True, min_length=1, max_length=10, description="对比项目ID列表"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "finance", "data_operator"]))
):
    """
    项目利润对比分析

    需要权限: ADMIN 或 FINANCE 或 DATA_OPERATOR

    参数:
    - project_ids: 对比项目ID列表 (1-10个)
    - start_date: 开始日期 (可选)
    - end_date: 结束日期 (可选)

    返回:
    - 各项目利润对比数据
    - 排名信息
    - 最佳项目

    错误码:
    - BIZ_002: 项目不存在 (ResourceNotFoundException)
    - BIZ_001: 日期范围无效或项目列表为空 (BusinessRuleException)
    - BIZ_607: 利润统计查询失败 (STATISTICS_QUERY_ERROR)
    """
    try:
        finance_service = FinanceService(db)
        result = finance_service.compare_profit(
            project_ids=project_ids,
            start_date=start_date,
            end_date=end_date
        )

        return success_response(
            data=result,
            message="获取利润对比成功"
        )

    except ResourceNotFoundException as e:
        return error_response(
            code=e.code,
            message=e.message,
            status_code=404
        )

    except BusinessRuleException as e:
        return error_response(
            code=e.code,
            message=e.message,
            status_code=400
        )

    except Exception as e:
        return error_response(
            code=BusinessErrorCodes.STATISTICS_QUERY_ERROR.code,
            message=f"获取利润对比失败: {str(e)}",
            status_code=BusinessErrorCodes.STATISTICS_QUERY_ERROR.status_code
        )
