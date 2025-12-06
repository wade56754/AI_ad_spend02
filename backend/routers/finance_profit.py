"""
财务利润 API 路由
处理利润汇总、利润分析等财务利润相关接口

SoT 对齐:
- DATA_SCHEMA.md v5.2: daily_reports, projects, ad_accounts 表结构
- BUSINESS_RULES.md v3.1: 利润计算公式
  - revenue = conversions_final × unit_price
  - cost = real_spend + fee
  - profit = revenue - cost
- ERROR_CODES_SOT.md v2.1: 错误码规范
- AUTH_SPEC.md v2.0: 权限矩阵 (admin, finance, data_operator)

Version: 1.0
Author: Claude Code
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.dependencies import require_role
from backend.core.response import success_response, error_response, StandardResponse
from backend.core.error_codes import BusinessErrorCodes
from backend.models import User
from backend.services.finance_service import FinanceService
from backend.schemas.finance import ProfitSummaryResponse
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
