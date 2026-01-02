"""
AdSpend Router - 外部消耗数据 API (重构版)

SoT References:
- API_SOT.md v9.3 标准响应格式
- DATA_SCHEMA.md v5.3 数据模型
- MASTER.md v4.8 §2.4 (6角色模型)
- ERROR_CODES_SOT.md v2.1 (错误码)

端点列表:
- GET  /ad-spend                       - 分页查询消耗记录
- GET  /ad-spend/statistics            - 获取消耗统计
- GET  /ad-spend/filter-options/*      - 获取筛选选项
- POST /ad-spend                       - 创建消耗记录
- POST /ad-spend/batch-import          - 批量导入消耗
- GET  /ad-spend/{spend_id}            - 获取单条记录
- DELETE /ad-spend/{spend_id}          - 删除记录 (仅admin)

权限矩阵 (MASTER.md v4.8 §2.4 - 6角色模型):
- ceo, finance, admin: 查看全部消耗数据
- project_owner: 查看自己项目的消耗
- pitcher: 查看自己导入的消耗，可导入新数据
- account_manager: 查看管理账户的消耗

依赖代码块:
- response-envelope: success_response, error_response
- pagination: PaginationParams
- error-codes: PERM-001, RES-001, BIZ-001, SYS-500
- permission-filter: require_role

Version: 2.0
Author: Claude Code
"""

import logging
import time
from typing import List, Optional
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.dependencies import get_current_user, require_role
from backend.core.response import success_response, error_response, StandardResponse
from backend.core.error_codes import SystemErrorCodes, BusinessErrorCodes
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
)
from backend.models import User
from backend.schemas.ad_spend import (
    AdSpendCreateRequest,
    AdSpendBatchImportRequest,
    AdSpendQueryParams,
    AdSpendResponse,
    AdSpendListResponse,
    AdSpendBatchImportResponse,
    AdSpendStatisticsResponse,
)
from backend.services.ad_spend_service import AdSpendService

logger = logging.getLogger(__name__)


# ========================================
# 错误响应辅助函数
# ========================================


def _handle_service_exception(e: Exception, context: str = "操作"):
    """处理服务层异常，转换为标准响应"""
    if isinstance(e, PermissionDeniedError):
        return error_response(code="PERM-001", message=str(e), status_code=403)
    elif isinstance(e, ResourceNotFoundError):
        return error_response(code="RES-001", message=str(e), status_code=404)
    elif isinstance(e, BusinessLogicError):
        return error_response(code="BIZ-001", message=str(e), status_code=400)
    else:
        logger.exception(f"服务异常 - {context}: {e}")
        return error_response(
            code="SYS-500", message=f"系统内部错误: {str(e)}", status_code=500
        )


router = APIRouter(prefix="/ad-spend", tags=["ad_spend"])


def get_ad_spend_service(db: Session = Depends(get_db)) -> AdSpendService:
    """Get AdSpend service instance"""
    return AdSpendService(db)


def _build_response(record) -> AdSpendResponse:
    """Build response with computed fields"""
    cpc = None
    ctr = None
    cvr = None
    if record.clicks and record.clicks > 0:
        cpc = record.spend_amount / record.clicks
    if record.impressions and record.impressions > 0:
        ctr = (record.clicks or 0) / record.impressions * 100
    if record.clicks and record.clicks > 0:
        cvr = (record.conversions or 0) / record.clicks * 100
    return AdSpendResponse(
        id=record.id,
        source_platform=record.source_platform,
        ad_account_code=record.ad_account_code,
        ad_account_id=record.ad_account_id,
        spend_date=record.spend_date,
        spend_amount=record.spend_amount,
        currency=record.currency,
        impressions=record.impressions or 0,
        clicks=record.clicks or 0,
        conversions=record.conversions or 0,
        raw_payload=record.raw_payload,
        imported_by=record.imported_by,
        imported_at=record.imported_at,
        created_at=record.created_at,
        cpc=cpc,
        ctr=ctr,
        cvr=cvr,
    )


# Static routes must be defined before /{spend_id}


@router.get(
    "",
    response_model=StandardResponse[AdSpendListResponse],
    summary="List ad spend records",
)
async def list_ad_spend(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    spend_date_start: Optional[date] = Query(None, description="开始日期"),
    spend_date_end: Optional[date] = Query(None, description="结束日期"),
    source_platform: Optional[str] = Query(None, description="平台筛选"),
    ad_account_code: Optional[str] = Query(None, description="账户代码筛选"),
    service: AdSpendService = Depends(get_ad_spend_service),
    current_user: User = Depends(get_current_user),
):
    """
    分页查询消耗记录

    权限 (MASTER.md v4.8 §2.4):
    - ceo, finance, admin: 查看全部记录
    - project_owner: 自己项目的记录
    - pitcher: 自己导入的记录
    """
    try:
        params = AdSpendQueryParams(
            spend_date_start=spend_date_start,
            spend_date_end=spend_date_end,
            source_platform=source_platform,
            ad_account_code=ad_account_code,
        )
        records, total = service.list_ad_spend(
            params=params, user=current_user, page=page, page_size=page_size
        )
        items = [_build_response(r) for r in records]
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return success_response(
            data=AdSpendListResponse(
                items=items, total=total, page=page, page_size=page_size, pages=pages
            ),
            message="查询成功",
        )
    except Exception as e:
        return _handle_service_exception(e, "查询消耗记录")


@router.get(
    "/statistics",
    response_model=StandardResponse[AdSpendStatisticsResponse],
    summary="Get spend statistics",
)
async def get_statistics(
    spend_date_start: Optional[date] = Query(None, description="开始日期"),
    spend_date_end: Optional[date] = Query(None, description="结束日期"),
    source_platform: Optional[str] = Query(None, description="平台筛选"),
    service: AdSpendService = Depends(get_ad_spend_service),
    current_user: User = Depends(get_current_user),
):
    """
    获取消耗统计: 总消耗、曝光、点击、转化、平均CPC

    权限 (MASTER.md v4.8 §2.4):
    - ceo, finance, admin: 全部统计
    - 其他角色: 根据权限范围统计
    """
    try:
        params = AdSpendQueryParams(
            spend_date_start=spend_date_start,
            spend_date_end=spend_date_end,
            source_platform=source_platform,
        )
        stats = service.get_statistics(params, current_user)
        return success_response(data=stats, message="获取统计成功")
    except Exception as e:
        return _handle_service_exception(e, "获取消耗统计")


@router.get(
    "/filter-options/platforms",
    response_model=StandardResponse[List[str]],
    summary="Get platform options",
)
async def get_platforms(
    service: AdSpendService = Depends(get_ad_spend_service),
    current_user: User = Depends(get_current_user),
):
    """获取所有平台选项 (用于筛选下拉)"""
    try:
        platforms = service.get_platforms()
        return success_response(data=platforms, message="获取成功")
    except Exception as e:
        return _handle_service_exception(e, "获取平台选项")


@router.get(
    "/filter-options/currencies",
    response_model=StandardResponse[List[str]],
    summary="Get currency options",
)
async def get_currencies(
    service: AdSpendService = Depends(get_ad_spend_service),
    current_user: User = Depends(get_current_user),
):
    """获取所有货币选项 (用于筛选下拉)"""
    try:
        currencies = service.get_currencies()
        return success_response(data=currencies, message="获取成功")
    except Exception as e:
        return _handle_service_exception(e, "获取货币选项")


# Routes with path parameters


@router.post(
    "",
    response_model=StandardResponse[AdSpendResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create spend record",
)
async def create_ad_spend(
    request_data: AdSpendCreateRequest,
    service: AdSpendService = Depends(get_ad_spend_service),
    current_user: User = Depends(require_role(["admin", "finance", "pitcher"])),
):
    """
    创建或更新消耗记录 (upsert)

    若存在相同日期+账户+平台的记录则更新，否则新建

    权限 (MASTER.md v4.8 §2.4): admin, finance, pitcher
    """
    try:
        record = service.create_ad_spend(request_data, current_user)
        response = _build_response(record)
        return success_response(data=response, message="创建成功", status_code=201)
    except Exception as e:
        return _handle_service_exception(e, "创建消耗记录")


@router.post(
    "/batch-import",
    response_model=StandardResponse[AdSpendBatchImportResponse],
    summary="Batch import spend data",
)
async def batch_import(
    request_data: AdSpendBatchImportRequest,
    service: AdSpendService = Depends(get_ad_spend_service),
    current_user: User = Depends(require_role(["admin", "finance"])),
):
    """
    批量导入消耗数据

    支持从 API/CSV/手动导入，最多 1000 条记录

    权限 (MASTER.md v4.8 §2.4): admin, finance
    """
    try:
        start_time = time.time()
        success_count, error_count, errors, imported_ids = service.batch_import(
            request_data, current_user
        )
        processing_time = time.time() - start_time
        return success_response(
            data=AdSpendBatchImportResponse(
                total_count=len(request_data.records),
                success_count=success_count,
                error_count=error_count,
                errors=errors,
                imported_ids=imported_ids,
                processing_time_seconds=round(processing_time, 3),
            ),
            message=f"导入成功 {success_count} 条，失败 {error_count} 条",
        )
    except Exception as e:
        return _handle_service_exception(e, "批量导入消耗")


@router.get(
    "/{spend_id}",
    response_model=StandardResponse[AdSpendResponse],
    summary="Get spend record",
)
async def get_ad_spend(
    spend_id: UUID,
    service: AdSpendService = Depends(get_ad_spend_service),
    current_user: User = Depends(get_current_user),
):
    """
    获取单条消耗记录

    权限 (MASTER.md v4.8 §2.4):
    - ceo, finance, admin: 查看所有
    - 其他角色: 根据权限过滤
    """
    try:
        record = service.get_ad_spend(spend_id, current_user)
        response = _build_response(record)
        return success_response(data=response, message="获取成功")
    except Exception as e:
        return _handle_service_exception(e, "获取消耗记录")


@router.delete(
    "/{spend_id}", response_model=StandardResponse[dict], summary="Delete spend record"
)
async def delete_ad_spend(
    spend_id: UUID,
    service: AdSpendService = Depends(get_ad_spend_service),
    current_user: User = Depends(require_role(["admin"])),
):
    """
    删除消耗记录

    权限 (MASTER.md v4.8 §2.4): 仅 admin
    """
    try:
        service.delete_ad_spend(spend_id, current_user)
        return success_response(data={"deleted_id": str(spend_id)}, message="删除成功")
    except Exception as e:
        return _handle_service_exception(e, "删除消耗记录")
