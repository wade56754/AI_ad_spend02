"""
资金总览 API 路由 (重构版)

SoT References:
- A2-fund-overview.md §5 API 接口
- API_SOT.md v9.3 标准响应格式
- AUTH_SPEC.md v2.0 角色权限控制
- MASTER.md v4.8 §2.4 (6角色模型)
- ERROR_CODES_SOT.md v2.1 (错误码)

端点列表:
- GET /fund/overview              - 获取资金概览
- GET /fund/distribution/projects - 按项目资金分布
- GET /fund/distribution/channels - 按渠道资金分布
- GET /fund/receivables           - 应收明细
- GET /fund/payments              - 回款记录
- GET /fund/alerts                - 资金预警

权限矩阵 (MASTER.md v4.8 §2.4 - 6角色模型):
- ceo, finance: 全公司数据
- admin: 全公司数据 (只读)
- project_owner: 自己负责的项目
- account_manager: 账户余额部分
- pitcher: 无访问权限

依赖代码块:
- response-envelope: success_response, error_response
- pagination: PaginationParams, get_pagination, create_paginated_response
- permission-filter: require_role
- error-codes: PERM-001, SYS-500

Version: 2.0
Author: Claude Code
"""

from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.dependencies import get_current_user
from backend.core.pagination import (
    PaginationParams,
    get_pagination,
    create_paginated_response,
)
from backend.core.response import success_response, error_response
from backend.core.security import require_roles
from backend.exceptions.custom_exceptions import (
    PermissionDeniedError,
    ResourceNotFoundError,
    BusinessLogicError,
)
from backend.models import User
from backend.schemas.fund import (
    FundOverviewResponse,
    FundDistributionProjectsResponse,
    FundDistributionChannelsResponse,
    ReceivableListResponse,
    PaymentListResponse,
    FundAlertsResponse,
)
from backend.services.fund_service import FundService, get_fund_service


# ========================================
# 错误响应辅助函数
# ========================================


def _handle_service_exception(e: Exception):
    """处理服务层异常，转换为标准响应"""
    if isinstance(e, PermissionDeniedError):
        return error_response(code="PERM-001", message=str(e), status_code=403)
    elif isinstance(e, ResourceNotFoundError):
        return error_response(code="RES-001", message=str(e), status_code=404)
    elif isinstance(e, BusinessLogicError):
        return error_response(code="BIZ-001", message=str(e), status_code=400)
    else:
        return error_response(
            code="SYS-500", message=f"系统内部错误: {str(e)}", status_code=500
        )


router = APIRouter(prefix="/fund", tags=["资金总览"])


@router.get("/overview", response_model=dict)
async def get_fund_overview(
    date_from: Optional[date] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取资金概览

    返回 5 个核心资金指标:
    - total_topup: 累计充值
    - total_spend: 累计消耗
    - current_balance: 当前余额
    - total_receivable: 应收款
    - fund_occupied: 资金占用

    权限 (MASTER.md v4.8 §2.4):
    - ceo, finance, admin: 全公司数据
    - project_owner: 自己负责的项目
    - account_manager: 账户余额部分
    """
    try:
        service = FundService(db)
        result = service.get_fund_overview(
            current_user=current_user,
            date_from=date_from,
            date_to=date_to,
        )
        return success_response(data=result.model_dump(), message="获取资金概览成功")
    except Exception as e:
        return _handle_service_exception(e)


@router.get("/distribution/projects", response_model=dict)
async def get_fund_distribution_by_projects(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort_by: Literal["topup", "spend", "balance"] = Query("topup", description="排序字段"),
    order: Literal["asc", "desc"] = Query("desc", description="排序方向"),
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取按项目的资金分布

    返回每个项目的充值、消耗、余额等数据

    权限 (MASTER.md v4.8 §2.4):
    - ceo, finance, admin: 全公司项目
    - project_owner: 自己负责的项目
    """
    try:
        service = FundService(db)
        result = service.get_fund_distribution_by_projects(
            current_user=current_user,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            order=order,
            date_from=date_from,
            date_to=date_to,
        )
        return success_response(data=result.model_dump(), message="获取项目资金分布成功")
    except Exception as e:
        return _handle_service_exception(e)


@router.get("/distribution/channels", response_model=dict)
async def get_fund_distribution_by_channels(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort_by: Literal["topup", "spend", "balance"] = Query("topup", description="排序字段"),
    order: Literal["asc", "desc"] = Query("desc", description="排序方向"),
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取按渠道的资金分布

    返回每个渠道/供应商的充值、消耗、余额等数据

    权限 (MASTER.md v4.8 §2.4):
    - ceo, finance, admin: 全部渠道
    - project_owner: 自己项目关联的渠道
    """
    try:
        service = FundService(db)
        result = service.get_fund_distribution_by_channels(
            current_user=current_user,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            order=order,
            date_from=date_from,
            date_to=date_to,
        )
        return success_response(data=result.model_dump(), message="获取渠道资金分布成功")
    except Exception as e:
        return _handle_service_exception(e)


@router.get("/receivables", response_model=dict)
async def get_receivables(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    project_id: Optional[int] = Query(None, gt=0, description="项目ID筛选"),
    status: Optional[Literal["pending", "partial", "received"]] = Query(
        None, description="状态筛选"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取应收明细

    返回待收款项目列表，包括金额、状态、待收天数等

    权限 (MASTER.md v4.8 §2.4):
    - ceo, finance: 全部应收
    - project_owner: 自己项目的应收
    """
    try:
        service = FundService(db)
        result = service.get_receivables(
            current_user=current_user,
            page=page,
            page_size=page_size,
            project_id=project_id,
            status=status,
        )
        return success_response(data=result.model_dump(), message="获取应收明细成功")
    except Exception as e:
        return _handle_service_exception(e)


@router.get("/payments", response_model=dict)
async def get_payments(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    project_id: Optional[int] = Query(None, gt=0, description="项目ID筛选"),
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取回款记录

    返回已回款记录列表

    权限 (MASTER.md v4.8 §2.4):
    - ceo, finance: 全部回款记录
    - project_owner: 自己项目的回款记录
    """
    try:
        service = FundService(db)
        result = service.get_payments(
            current_user=current_user,
            page=page,
            page_size=page_size,
            project_id=project_id,
            date_from=date_from,
            date_to=date_to,
        )
        return success_response(data=result.model_dump(), message="获取回款记录成功")
    except Exception as e:
        return _handle_service_exception(e)


@router.get("/alerts", response_model=dict)
async def get_fund_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取资金预警

    返回资金相关预警列表:
    - high_occupy_rate: 资金占用率过高
    - negative_balance: 余额为负
    - overdue_receivable: 应收逾期

    权限 (MASTER.md v4.8 §2.4):
    - ceo, finance, admin: 全部预警
    """
    try:
        service = FundService(db)
        result = service.get_fund_alerts(current_user=current_user)
        return success_response(data=result.model_dump(), message="获取资金预警成功")
    except Exception as e:
        return _handle_service_exception(e)
