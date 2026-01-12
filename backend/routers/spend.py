"""
消耗导入 API 路由
Version: 1.0 (Financial SoT Phase 2)
Author: Claude Code

SoT 对齐:
- FINANCIAL_SOT_DESIGN.md v1.0: 消耗事件 API
- API_SOT.md v9.0: 标准响应格式
- AUTH_SPEC.md v2.0: 角色权限控制
- ERROR_CODES_SOT.md v2.1: 错误码规范

端点列表:
- POST /spend/import              - 导入 Excel 消耗数据
- POST /spend/events              - 手动创建消耗事件
- GET  /spend/events              - 查询消耗事件列表
- GET  /spend/events/{id}         - 获取消耗事件详情
- POST /spend/events/validate     - 验证消耗事件 (raw → pending)
- POST /spend/events/confirm      - 确认消耗事件 (pending → confirmed)
- POST /spend/events/post         - 入账消耗事件 (confirmed → posted)
- POST /spend/events/reverse      - 冲正消耗事件 (posted → reversed)
- POST /spend/events/batch-reverse - 批量冲正 (posted → reversed) [NEW]
- GET  /spend/statistics          - 获取消耗统计
- GET  /spend/export              - 导出消耗事件 Excel/CSV [NEW]
- GET  /spend/template            - 获取导入模板 [NEW]

权限要求:
- finance: 所有操作
- project_owner: 导入、验证
- admin: 所有操作
"""

from typing import List, Optional
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.dependencies import get_current_user, check_user_role
from backend.core.response import success_response, error_response, StandardResponse
from backend.core.error_codes import SystemErrorCodes, BusinessErrorCodes
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError,
)
from backend.models import User
from backend.models.finance.financial_event import EventStatus, SourceType
import logging

logger = logging.getLogger(__name__)
from backend.schemas.spend import (
    SpendImportRequest,
    SpendEventCreate,
    SpendImportResultResponse,
    SpendEventValidateRequest,
    SpendEventValidateResponse,
    SpendEventConfirmRequest,
    SpendEventConfirmResponse,
    SpendEventPostRequest,
    SpendEventPostResponse,
    SpendEventReverseRequest,
    SpendEventReverseResponse,
    SpendEventBatchReverseRequest,
    SpendEventBatchReverseResponse,
    SpendEventResponse,
    SpendEventListResponse,
    SpendEventQueryRequest,
    SpendStatisticsResponse,
    SpendTemplateResponse,
    TeamCodeEnum,
)
from backend.services.spend_import_service import SpendImportService

router = APIRouter(prefix="/spend", tags=["spend"])


def get_spend_service(db: Session = Depends(get_db)) -> SpendImportService:
    """获取消耗导入服务实例"""
    return SpendImportService(db)


def _build_event_response(event) -> SpendEventResponse:
    """构建消耗事件响应"""
    return SpendEventResponse(
        id=event.id,
        event_type=event.event_type,
        event_status=event.event_status,
        source_type=event.source_type,
        source_ref=event.source_ref,
        idempotency_key=event.idempotency_key,
        amount=event.amount,
        fee_amount=event.fee_amount,
        gross_amount=event.gross_amount,
        currency=event.currency,
        event_date=event.event_date,
        team_id=event.team_id,
        team_code=event.team.code if event.team else None,
        buyer_id=event.buyer_id,
        buyer_code=event.buyer.code if event.buyer else None,
        supplier_id=event.supplier_id,
        supplier_name=event.supplier.name if event.supplier else None,
        ad_account_id=event.ad_account_id,
        ad_account_name=event.ad_account.account_name if event.ad_account else None,
        project_id=event.project_id,
        project_name=event.project.name if event.project else None,
        today_max=event.payload.get("today_max") if event.payload else None,
        yesterday_max=event.payload.get("yesterday_max") if event.payload else None,
        fee_rate=event.payload.get("fee_rate") if event.payload else None,
        created_by=event.created_by,
        created_by_name=event.creator.username if event.creator else None,
        confirmed_by=event.confirmed_by,
        confirmed_by_name=event.confirmer.username if event.confirmer else None,
        confirmed_at=event.confirmed_at,
        posted_at=event.posted_at,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


# ========== 导入端点 ==========


@router.post(
    "/import",
    response_model=StandardResponse[SpendImportResultResponse],
    summary="导入 Excel 消耗数据",
    description="""
    从 Excel 文件导入消耗数据，创建 SPEND 类型的财务事件。

    导入流程:
    1. 解析 Excel 文件
    2. 验证数据完整性
    3. 去重检查 (基于 account_id + event_date)
    4. 创建 FinancialEvent (status=raw)

    支持的列:
    - 账户ID / account_id
    - 今日最大消耗 / today_max
    - 昨日最大消耗 / yesterday_max
    - 消耗 / spend (可选，默认 = today_max - yesterday_max)
    - 日期 / event_date (可选，从文件名推断)

    权限要求: finance, project_owner, admin
    """,
)
async def import_spend_from_excel(
    file: UploadFile = File(..., description="Excel 文件 (.xlsx, .xls)"),
    team_code: TeamCodeEnum = Query(..., description="团队代码 (SZ/ZZ)"),
    event_date: Optional[date] = Query(None, description="事件日期 (默认从文件名推断)"),
    dry_run: bool = Query(False, description="试运行 (仅验证不导入)"),
    skip_duplicates: bool = Query(True, description="跳过重复记录"),
    service: SpendImportService = Depends(get_spend_service),
    current_user: User = Depends(get_current_user),
):
    """导入消耗 Excel"""
    # 权限检查
    check_user_role(current_user, ["finance", "project_owner", "admin"])

    # 验证文件类型
    if not file.filename.endswith((".xlsx", ".xls")):
        raise BusinessLogicError("仅支持 Excel 文件 (.xlsx, .xls)", error_code="BIZ-500")

    try:
        # 读取文件内容
        file_content = await file.read()

        # 构建请求
        request = SpendImportRequest(
            team_code=team_code,
            event_date=event_date,
            dry_run=dry_run,
            skip_duplicates=skip_duplicates,
        )

        # 执行导入
        result = service.import_from_excel(
            file_content=file_content,
            file_name=file.filename,
            request=request,
            user_id=current_user.id,
        )

        return success_response(
            data=result, message=f"导入完成: {result.imported_rows}/{result.total_rows} 行"
        )

    except BusinessLogicError as e:
        return error_response(
            code=e.error_code if hasattr(e, 'error_code') else BusinessErrorCodes.IMPORT_ERROR.code,
            message=str(e),
            status_code=400
        )
    except Exception as e:
        logger.exception(f"导入失败: {e}")
        return error_response(
            code=BusinessErrorCodes.IMPORT_ERROR.code,
            message=f"导入失败: {str(e)}",
            status_code=BusinessErrorCodes.IMPORT_ERROR.status_code
        )


# ========== CRUD 端点 ==========


@router.post(
    "/events",
    response_model=StandardResponse[SpendEventResponse],
    summary="手动创建消耗事件",
    description="""
    手动创建单个消耗事件。

    权限要求: finance, admin
    """,
)
async def create_spend_event(
    request: SpendEventCreate,
    service: SpendImportService = Depends(get_spend_service),
    current_user: User = Depends(get_current_user),
):
    """手动创建消耗事件"""
    check_user_role(current_user, ["finance", "admin"])

    try:
        event = service.create_event(
            request=request,
            user_id=current_user.id,
        )
        return success_response(data=_build_event_response(event), message="消耗事件创建成功")
    except ResourceNotFoundError as e:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message=str(e),
            status_code=BusinessErrorCodes.RESOURCE_NOT_FOUND.status_code
        )
    except ResourceConflictError as e:
        # ResourceConflictError 会被 BaseCustomException 处理器自动处理
        raise e


@router.get(
    "/events",
    response_model=StandardResponse[SpendEventListResponse],
    summary="查询消耗事件列表",
    description="""
    查询消耗事件列表，支持多种筛选条件。

    权限要求: finance, project_owner, admin
    """,
)
async def list_spend_events(
    event_status: Optional[str] = Query(None, description="事件状态"),
    team_id: Optional[UUID] = Query(None, description="团队ID"),
    supplier_id: Optional[int] = Query(None, description="供应商ID"),
    ad_account_id: Optional[int] = Query(None, description="广告账户ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    source_type: Optional[str] = Query(None, description="来源类型"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    service: SpendImportService = Depends(get_spend_service),
    current_user: User = Depends(get_current_user),
):
    """查询消耗事件列表"""
    check_user_role(current_user, ["finance", "project_owner", "admin"])

    events, total = service.get_events(
        event_status=event_status,
        team_id=team_id,
        supplier_id=supplier_id,
        ad_account_id=ad_account_id,
        start_date=start_date,
        end_date=end_date,
        source_type=source_type,
        page=page,
        page_size=page_size,
    )

    items = [_build_event_response(e) for e in events]
    total_pages = (total + page_size - 1) // page_size

    return success_response(
        data=SpendEventListResponse(
            items=items,
            meta={
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            },
        ),
        message="查询成功",
    )


@router.get(
    "/events/{event_id}",
    response_model=StandardResponse[SpendEventResponse],
    summary="获取消耗事件详情",
    description="""
    获取单个消耗事件的详细信息。

    权限要求: finance, project_owner, admin
    """,
)
async def get_spend_event(
    event_id: UUID,
    service: SpendImportService = Depends(get_spend_service),
    current_user: User = Depends(get_current_user),
):
    """获取消耗事件详情"""
    check_user_role(current_user, ["finance", "project_owner", "admin"])

    event = service.get_event_by_id(event_id)
    if not event:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message="消耗事件不存在",
            status_code=BusinessErrorCodes.RESOURCE_NOT_FOUND.status_code
        )

    return success_response(data=_build_event_response(event), message="获取成功")


# ========== 状态流转端点 ==========


@router.post(
    "/events/validate",
    response_model=StandardResponse[SpendEventValidateResponse],
    summary="验证消耗事件",
    description="""
    验证消耗事件，将状态从 raw 转换为 pending。

    验证内容:
    - 账户存在性
    - 供应商存在性
    - 金额有效性
    - 日期合理性

    权限要求: finance, project_owner, admin
    """,
)
async def validate_spend_events(
    request: SpendEventValidateRequest,
    service: SpendImportService = Depends(get_spend_service),
    current_user: User = Depends(get_current_user),
):
    """验证消耗事件 (raw → pending)"""
    check_user_role(current_user, ["finance", "project_owner", "admin"])

    result = service.validate_events(
        event_ids=request.event_ids,
        force=request.force,
        user_id=current_user.id,
    )

    return success_response(data=result, message=result.message)


@router.post(
    "/events/confirm",
    response_model=StandardResponse[SpendEventConfirmResponse],
    summary="确认消耗事件",
    description="""
    确认消耗事件，将状态从 pending 转换为 confirmed。

    只有 finance 和 admin 角色可以执行确认操作。

    权限要求: finance, admin
    """,
)
async def confirm_spend_events(
    request: SpendEventConfirmRequest,
    service: SpendImportService = Depends(get_spend_service),
    current_user: User = Depends(get_current_user),
):
    """确认消耗事件 (pending → confirmed)"""
    check_user_role(current_user, ["finance", "admin"])

    result = service.confirm_events(
        event_ids=request.event_ids,
        user_id=current_user.id,
        notes=request.notes,
    )

    return success_response(data=result, message=result.message)


@router.post(
    "/events/post",
    response_model=StandardResponse[SpendEventPostResponse],
    summary="入账消耗事件",
    description="""
    入账消耗事件，将状态从 confirmed 转换为 posted。

    入账流程:
    1. 生成 ledger_entries (DEBIT 到 SUPPLIER 和 ACCOUNT)
    2. 更新相关余额
    3. 状态转换: confirmed → posted

    只有 finance 和 admin 角色可以执行入账操作。

    权限要求: finance, admin
    """,
)
async def post_spend_events(
    request: SpendEventPostRequest,
    service: SpendImportService = Depends(get_spend_service),
    current_user: User = Depends(get_current_user),
):
    """入账消耗事件 (confirmed → posted)"""
    check_user_role(current_user, ["finance", "admin"])

    result = service.post_events(
        event_ids=request.event_ids,
        user_id=current_user.id,
        post_date=request.post_date,
    )

    return success_response(data=result, message=result.message)


@router.post(
    "/events/reverse",
    response_model=StandardResponse[SpendEventReverseResponse],
    summary="冲正消耗事件",
    description="""
    冲正已入账的消耗事件，将状态从 posted 转换为 reversed。

    冲正流程:
    1. 生成反向 ledger_entries
    2. 状态转换: posted → reversed

    只有 admin 角色可以执行冲正操作。

    权限要求: admin
    """,
)
async def reverse_spend_event(
    request: SpendEventReverseRequest,
    service: SpendImportService = Depends(get_spend_service),
    current_user: User = Depends(get_current_user),
):
    """冲正消耗事件 (posted → reversed)"""
    check_user_role(current_user, ["admin"])

    try:
        result = service.reverse_event(
            event_id=request.event_id,
            reason=request.reason,
            user_id=current_user.id,
        )
        return success_response(data=result, message=result.message)
    except ResourceNotFoundError as e:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message=str(e),
            status_code=BusinessErrorCodes.RESOURCE_NOT_FOUND.status_code
        )
    except BusinessLogicError as e:
        error_code = e.error_code if hasattr(e, 'error_code') else BusinessErrorCodes.INVALID_OPERATION.code
        return error_response(
            code=error_code,
            message=str(e),
            status_code=400
        )


# ========== 统计端点 ==========


@router.get(
    "/statistics",
    response_model=StandardResponse[SpendStatisticsResponse],
    summary="获取消耗统计",
    description="""
    获取消耗事件的统计数据。

    权限要求: finance, project_owner, admin
    """,
)
async def get_spend_statistics(
    team_id: Optional[UUID] = Query(None, description="团队ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    service: SpendImportService = Depends(get_spend_service),
    current_user: User = Depends(get_current_user),
):
    """获取消耗统计"""
    check_user_role(current_user, ["finance", "project_owner", "admin"])

    stats = service.get_statistics(
        team_id=team_id,
        start_date=start_date,
        end_date=end_date,
    )

    return success_response(data=SpendStatisticsResponse(**stats), message="统计成功")


# ========== 批量冲正端点 ==========


@router.post(
    "/events/batch-reverse",
    response_model=StandardResponse[SpendEventBatchReverseResponse],
    summary="批量冲正消耗事件",
    description="""
    批量冲正已入账的消耗事件，将状态从 posted 转换为 reversed。

    批量冲正流程:
    1. 批量验证事件状态
    2. 生成反向 ledger_entries
    3. 状态转换: posted → reversed

    限制: 单次最多冲正 100 条记录

    权限要求: admin
    """,
)
async def batch_reverse_spend_events(
    request: SpendEventBatchReverseRequest,
    service: SpendImportService = Depends(get_spend_service),
    current_user: User = Depends(get_current_user),
):
    """批量冲正消耗事件 (posted → reversed)"""
    check_user_role(current_user, ["admin"])

    try:
        result = service.reverse_events(
            event_ids=request.event_ids,
            reason=request.reason,
            user_id=current_user.id,
        )
        return success_response(data=result, message=result.message)
    except BusinessLogicError as e:
        error_code = e.error_code if hasattr(e, 'error_code') else BusinessErrorCodes.INVALID_OPERATION.code
        return error_response(
            code=error_code,
            message=str(e),
            status_code=400
        )


# ========== 导出端点 ==========


@router.get(
    "/export",
    summary="导出消耗事件",
    description="""
    导出消耗事件为 Excel 或 CSV 文件。

    支持多种筛选条件，最多导出 10000 条记录。

    权限要求: finance, project_owner, admin
    """,
)
async def export_spend_events(
    event_status: Optional[str] = Query(None, description="事件状态"),
    team_id: Optional[UUID] = Query(None, description="团队ID"),
    supplier_id: Optional[int] = Query(None, description="供应商ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    format: str = Query("xlsx", description="导出格式 (xlsx/csv)"),
    service: SpendImportService = Depends(get_spend_service),
    current_user: User = Depends(get_current_user),
):
    """导出消耗事件为 Excel/CSV"""
    from fastapi.responses import Response

    check_user_role(current_user, ["finance", "project_owner", "admin"])

    file_content, file_name = service.export_events(
        event_status=event_status,
        team_id=team_id,
        supplier_id=supplier_id,
        start_date=start_date,
        end_date=end_date,
        export_format=format,
    )

    # 设置响应头
    content_type = (
        "text/csv"
        if format == "csv"
        else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    return Response(
        content=file_content,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


# ========== 模板生成端点 ==========


@router.get(
    "/template",
    summary="获取导入模板",
    description="""
    获取消耗数据导入模板 Excel 文件。

    模板包含:
    - 标准列名
    - 示例数据
    - 填写说明

    权限要求: finance, project_owner, admin
    """,
)
async def get_spend_template(
    service: SpendImportService = Depends(get_spend_service),
    current_user: User = Depends(get_current_user),
):
    """获取消耗导入模板"""
    from fastapi.responses import Response

    check_user_role(current_user, ["finance", "project_owner", "admin"])

    file_content, file_name, columns = service.generate_template()

    return Response(
        content=file_content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )
