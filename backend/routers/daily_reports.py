"""
日报管理API路由 (重构版)

SoT Reference: STATE_MACHINE.md v2.6 §8 (日报 8 状态机)
SoT Reference: API_SOT.md v9.0 §9 (Daily Reports API)

状态机 (8状态):
raw_submitted → trend_pending → trend_ok → final_pending → final_confirmed → final_locked
                      ↓
               trend_flagged → trend_resolved ↗

依赖代码块:
- response-envelope: success_response, error_response, paginated_response
- pagination: Query params
- error-codes: StandardResponse, SystemErrorCodes, BusinessErrorCodes

Version: 2.0
"""

import logging
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum as PyEnum

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from pydantic import BaseModel, Field
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
import pandas as pd
import uuid

from backend.config.excel_column_mapping import (
    find_column_definition,
    validate_column_exists,
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    MAX_EXPORT_ROWS,
    EXCEL_COLUMN_DEFINITIONS,
)

from backend.core.db import get_db
from backend.core.dependencies import get_current_user, require_role
from backend.core.response import (
    success_response,
    error_response,
    paginated_response,
    StandardResponse,
)
from backend.core.error_codes import (
    SystemErrorCodes,
    BusinessErrorCodes,
    ValidationErrorCodes,
    AuthErrorCodes,
)
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError,
)
from backend.models import User
from backend.schemas.daily_report import (
    DailyReportCreateRequest,
    DailyReportUpdateRequest,
    DailyReportAuditRequest,
    DailyReportBatchImportRequest,
    DailyReportQueryParams,
    DailyReportResponse,
    DailyReportListResponse,
    DailyReportStatisticsResponse,
    DailyReportExportResponse,
    DailyReportBatchImportResponse,
    DailyReportImportError,
    DailyReportAuditLogResponse,
    RealSpendRequest,
)
from backend.services.daily_report_service import DailyReportService

# 创建logger实例
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/daily-reports", tags=["daily-reports"])


def get_daily_report_service(db: Session = Depends(get_db)) -> DailyReportService:
    """获取日报服务实例"""
    return DailyReportService(db)


# ============ 辅助函数：Excel数据解析 ============


def parse_excel_row_to_report(
    row: pd.Series, row_number: int, df_columns: List[str]
) -> Tuple[Optional[DailyReportCreateRequest], Optional[DailyReportImportError]]:
    """
    解析Excel单行数据为DailyReportCreateRequest对象

    Args:
        row: pandas Series对象（单行数据）
        row_number: 行号（从1开始，包含表头）
        df_columns: DataFrame的所有列名

    Returns:
        (DailyReportCreateRequest对象或None, DailyReportImportError对象或None)
        成功时返回(request, None)，失败时返回(None, error)
    """
    try:
        report_data = {}

        # 遍历所有列定义，尝试从Excel行中提取数据
        for col_def in EXCEL_COLUMN_DEFINITIONS:
            # 查找匹配的列名
            matched_column = None
            for df_col in df_columns:
                if find_column_definition(df_col) == col_def:
                    matched_column = df_col
                    break

            # 如果找不到列且是必需列，报错
            if matched_column is None:
                if col_def.required:
                    return None, DailyReportImportError(
                        row_number=row_number,
                        error_code="MISSING_REQUIRED_COLUMN",
                        error_message=f"缺少必需列：{col_def.cn_name}",
                        field_name=col_def.field_name,
                        suggestion=f"请确保Excel中包含'{col_def.cn_name}'或'{col_def.en_name}'列",
                    )
                # 可选列，使用默认值
                report_data[col_def.field_name] = col_def.default
                continue

            # 获取单元格值
            cell_value = row[matched_column]

            # 处理空值
            if pd.isna(cell_value) or cell_value == "":
                if col_def.required:
                    return None, DailyReportImportError(
                        row_number=row_number,
                        error_code="EMPTY_REQUIRED_FIELD",
                        error_message=f"必需字段为空",
                        field_name=col_def.field_name,
                        invalid_value="(空)",
                        suggestion=f"请填写'{col_def.cn_name}'",
                    )
                report_data[col_def.field_name] = col_def.default
                continue

            # 类型转换
            try:
                if col_def.data_type == "date":
                    # 日期类型
                    if isinstance(cell_value, pd.Timestamp):
                        converted_value = cell_value.date()
                    elif isinstance(cell_value, datetime):
                        converted_value = cell_value.date()
                    elif isinstance(cell_value, date):
                        converted_value = cell_value
                    else:
                        # 尝试解析字符串
                        converted_value = pd.to_datetime(str(cell_value)).date()

                elif col_def.data_type == "int":
                    # 整数类型
                    converted_value = int(float(cell_value))  # 处理"123.0"这种情况

                    # 范围验证
                    if (
                        col_def.min_value is not None
                        and converted_value < col_def.min_value
                    ):
                        return None, DailyReportImportError(
                            row_number=row_number,
                            error_code="VALUE_OUT_OF_RANGE",
                            error_message=f"值{converted_value}小于最小值{col_def.min_value}",
                            field_name=col_def.field_name,
                            invalid_value=str(cell_value),
                            suggestion=f"'{col_def.cn_name}'必须≥{col_def.min_value}",
                        )
                    if (
                        col_def.max_value is not None
                        and converted_value > col_def.max_value
                    ):
                        return None, DailyReportImportError(
                            row_number=row_number,
                            error_code="VALUE_OUT_OF_RANGE",
                            error_message=f"值{converted_value}超过最大值{col_def.max_value}",
                            field_name=col_def.field_name,
                            invalid_value=str(cell_value),
                            suggestion=f"'{col_def.cn_name}'必须≤{col_def.max_value}",
                        )

                elif col_def.data_type == "decimal":
                    # Decimal类型
                    converted_value = Decimal(str(cell_value))

                    # 范围验证
                    if col_def.min_value is not None and converted_value < Decimal(
                        str(col_def.min_value)
                    ):
                        return None, DailyReportImportError(
                            row_number=row_number,
                            error_code="VALUE_OUT_OF_RANGE",
                            error_message=f"值{converted_value}小于最小值{col_def.min_value}",
                            field_name=col_def.field_name,
                            invalid_value=str(cell_value),
                            suggestion=f"'{col_def.cn_name}'必须≥{col_def.min_value}",
                        )

                elif col_def.data_type == "str":
                    # 字符串类型
                    converted_value = str(cell_value).strip()

                    # 长度验证
                    if col_def.max_length and len(converted_value) > col_def.max_length:
                        return None, DailyReportImportError(
                            row_number=row_number,
                            error_code="STRING_TOO_LONG",
                            error_message=f"字符串长度{len(converted_value)}超过最大限制{col_def.max_length}",
                            field_name=col_def.field_name,
                            invalid_value=converted_value[:50] + "...",
                            suggestion=f"'{col_def.cn_name}'长度不能超过{col_def.max_length}字符",
                        )

                else:
                    converted_value = cell_value

                report_data[col_def.field_name] = converted_value

            except (ValueError, InvalidOperation, OverflowError) as e:
                return None, DailyReportImportError(
                    row_number=row_number,
                    error_code="TYPE_CONVERSION_ERROR",
                    error_message=f"数据类型转换失败：{str(e)}",
                    field_name=col_def.field_name,
                    invalid_value=str(cell_value),
                    suggestion=f"'{col_def.cn_name}'应为{col_def.data_type}类型",
                )

        # 创建请求对象（Pydantic会进行二次验证）
        try:
            request = DailyReportCreateRequest(**report_data)
            return request, None
        except Exception as e:
            return None, DailyReportImportError(
                row_number=row_number,
                error_code="VALIDATION_ERROR",
                error_message=f"数据验证失败：{str(e)}",
                invalid_data=report_data,
            )

    except Exception as e:
        logger.error(f"Unexpected error parsing row {row_number}: {e}", exc_info=True)
        return None, DailyReportImportError(
            row_number=row_number,
            error_code="PARSE_ERROR",
            error_message=f"解析行数据失败：{str(e)}",
            invalid_data=row.to_dict() if hasattr(row, "to_dict") else {},
        )


@router.get(
    "",
    response_model=StandardResponse[DailyReportListResponse],
    summary="获取日报列表",
    description="获取日报列表，支持分页和筛选",
)
async def list_daily_reports(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    report_date_start: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    report_date_end: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    ad_account_id: Optional[int] = Query(None, description="广告账户ID"),
    status: Optional[str] = Query(
        None,
        pattern="^(raw_submitted|trend_pending|trend_ok|trend_flagged|trend_resolved|final_pending|final_confirmed|final_locked)$",
        description="日报状态（8状态机）",
    ),
    media_buyer_id: Optional[int] = Query(None, description="投手ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    region: Optional[str] = Query(None, description="投放地区"),
    platform: Optional[str] = Query(None, description="广告平台（FB/Google/TikTok）"),
    team_id: Optional[str] = Query(None, description="团队ID (UUID)"),
    submitter_name: Optional[str] = Query(None, description="投手名称（模糊匹配）"),
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(get_current_user),
):
    """
    获取日报列表API
    """
    try:
        # 构建查询参数
        params = DailyReportQueryParams(
            report_date_start=report_date_start,
            report_date_end=report_date_end,
            ad_account_id=ad_account_id,
            status=status,
            media_buyer_id=media_buyer_id,
            project_id=project_id,
            region=region,
            platform=platform,
            team_id=team_id,
            submitter_name=submitter_name,
        )

        # 获取日报列表
        reports, total = service.get_daily_reports(
            params, current_user, page, page_size
        )

        # 转换为响应格式，填充投手和团队信息
        report_responses = []
        for report in reports:
            # 准备额外字段
            report_submitter_name = None
            report_team_name = None

            # 填充投手名称
            if report.submitter:
                report_submitter_name = (
                    report.submitter.username or report.submitter.email
                )
            elif report.ad_account and report.ad_account.name:
                # 从账户名提取投手名（格式: "投手名_平台_地区"）
                account_parts = report.ad_account.name.split("_")
                if len(account_parts) >= 1:
                    report_submitter_name = account_parts[0]

            # 填充团队名称（通过 ad_account -> team）
            if report.ad_account and report.ad_account.team:
                report_team_name = report.ad_account.team.name

            # 创建响应对象，使用 model_copy 更新额外字段
            resp = DailyReportResponse.model_validate(report)
            resp = resp.model_copy(
                update={
                    "submitter_name": report_submitter_name,
                    "team_name": report_team_name,
                }
            )
            report_responses.append(resp)

        # 返回分页响应
        return paginated_response(
            items=report_responses, page=page, page_size=page_size, total=total
        )

    except (BusinessLogicError, ResourceNotFoundError, PermissionDeniedError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, "error_code") else "BIZ_001",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.exception(f"Unexpected error in list_daily_reports: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="系统内部错误",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.post(
    "",
    response_model=StandardResponse[DailyReportResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建日报",
    description="创建新的日报记录",
)
async def create_daily_report(
    request: DailyReportCreateRequest,
    service: DailyReportService = Depends(get_daily_report_service),
    # AUTH_SPEC.md v2.0: 仅 pitcher 和 admin 可创建日报
    current_user: User = Depends(require_role(["pitcher", "admin"])),
):
    """
    创建日报API

    错误码映射 (ERROR_CODES_SOT v2.1):
    - BIZ_002: 广告账户不存在 → 404
    - BIZ_003: 日报已存在（重复） → 409
    - BIZ_201: 报表日期为未来日期 → 400
    - AUTH_500: 无权限 → 403
    """
    try:
        # 创建日报
        report = service.create_daily_report(request, current_user)

        # 转换为响应格式
        report_response = DailyReportResponse.model_validate(report)

        return success_response(
            data=report_response, message="日报创建成功", status_code=status.HTTP_201_CREATED
        )

    except ResourceConflictError as e:
        # BIZ_003: 日报已存在 → 409
        return error_response(
            code=str(e.error_code) if hasattr(e, "error_code") else "BIZ_003",
            message=str(e),
            status_code=status.HTTP_409_CONFLICT,
        )
    except ResourceNotFoundError as e:
        # BIZ_002: 广告账户不存在 → 404
        return error_response(
            code=str(e.error_code) if hasattr(e, "error_code") else "BIZ_002",
            message=str(e),
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except BusinessLogicError as e:
        # BIZ_201: 报表日期为未来日期 → 400
        return error_response(
            code=str(e.error_code) if hasattr(e, "error_code") else "BIZ_001",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except PermissionDeniedError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, "error_code") else "PERMISSION_DENIED",
            message=str(e),
            status_code=status.HTTP_403_FORBIDDEN,
        )
    except Exception as e:
        logger.exception(f"Unexpected error in create_daily_report: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="系统内部错误",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.get(
    "/stats",
    response_model=StandardResponse[dict],
    summary="获取日报状态统计",
    description="获取各状态的日报数量统计",
)
async def get_daily_report_stats(
    project_id: Optional[int] = Query(None, description="项目ID"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(get_current_user),
):
    """
    获取日报状态统计API - 返回各状态的日报数量

    8状态机统计 (STATE_MACHINE.md v2.6):
    - raw_submitted: 原始提交
    - trend_pending: 趋势待审
    - trend_ok: 趋势通过
    - trend_flagged: 趋势异常
    - trend_resolved: 异常已处理
    - final_pending: 终审待审
    - final_confirmed: 终审确认
    - final_locked: 已锁定
    """
    try:
        stats = service.get_status_stats(
            current_user=current_user,
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
        )
        return success_response(data=stats)
    except Exception as e:
        logger.exception(f"Unexpected error in get_daily_report_stats: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="系统内部错误",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


# ============ 筛选选项端点 (v2.1) - 必须在 /{report_id} 之前 ============

from backend.models.finance.team import Team
from backend.models.accounts.ad_account import AdAccount


@router.get(
    "/filter-options/teams",
    response_model=StandardResponse[List[Dict[str, Any]]],
    summary="获取团队筛选选项",
    description="获取可用的团队列表，用于筛选下拉",
)
async def get_team_options(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    获取团队筛选选项 API (v2.1)
    返回所有激活状态的团队
    """
    try:
        teams = db.query(Team).filter(Team.status == "active").order_by(Team.name).all()
        options = [{"id": t.id, "name": t.name, "code": t.code} for t in teams]
        return success_response(data=options)
    except Exception as e:
        logger.exception(f"Error getting team options: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="获取团队选项失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.get(
    "/filter-options/submitters",
    response_model=StandardResponse[List[str]],
    summary="获取投手筛选选项",
    description="从账户名提取的投手列表，用于筛选下拉",
)
async def get_submitter_options(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    获取投手筛选选项 API (v2.1)
    从广告账户名称中提取投手名前缀（格式: 投手名_平台_地区）
    """
    try:
        # 获取所有账户名
        accounts = db.query(AdAccount.name).distinct().all()

        # 提取投手名（账户名的第一段）
        submitters = set()
        for (name,) in accounts:
            if name and "_" in name:
                submitter = name.split("_")[0]
                if submitter:
                    submitters.add(submitter)

        # 排序返回
        sorted_submitters = sorted(list(submitters))
        return success_response(data=sorted_submitters)
    except Exception as e:
        logger.exception(f"Error getting submitter options: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="获取投手选项失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.get(
    "/{report_id}",
    response_model=StandardResponse[DailyReportResponse],
    summary="获取日报详情",
    description="根据ID获取日报详情",
)
async def get_daily_report(
    report_id: int,
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(get_current_user),
):
    """
    获取日报详情API
    """
    try:
        # 获取日报详情
        report = service.get_daily_report(report_id, current_user)

        # 转换为响应格式
        report_response = DailyReportResponse.model_validate(report)

        return success_response(data=report_response)

    except ResourceNotFoundError as e:
        # BIZ_002: 日报不存在 → 404
        return error_response(
            code=str(e.error_code) if hasattr(e, "error_code") else "BIZ_002",
            message=str(e),
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except PermissionDeniedError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, "error_code") else "PERMISSION_DENIED",
            message=str(e),
            status_code=status.HTTP_403_FORBIDDEN,
        )
    except Exception as e:
        logger.exception(f"Unexpected error in get_daily_report: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="系统内部错误",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.put(
    "/{report_id}",
    response_model=StandardResponse[DailyReportResponse],
    summary="更新日报",
    description="更新日报信息（仅未审核的日报可更新）",
)
async def update_daily_report(
    report_id: int,
    request: DailyReportUpdateRequest,
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(require_role(["pitcher", "admin"])),
):
    """
    更新日报API
    """
    try:
        # 更新日报
        report = service.update_daily_report(report_id, request, current_user)

        # 转换为响应格式
        report_response = DailyReportResponse.model_validate(report)

        return success_response(data=report_response, message="日报更新成功")

    except ResourceNotFoundError as e:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message=str(e),
            status_code=BusinessErrorCodes.RESOURCE_NOT_FOUND.status_code,
        )
    except (BusinessLogicError, PermissionDeniedError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, "error_code") else "BIZ_001",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="系统内部错误",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除日报",
    description="删除日报记录（仅管理员可操作）",
)
async def delete_daily_report(
    report_id: int,
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(require_role(["admin"])),
):
    """
    删除日报API
    """
    try:
        # 删除日报
        service.delete_daily_report(report_id, current_user)

        return None

    except ResourceNotFoundError as e:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message=str(e),
            status_code=BusinessErrorCodes.RESOURCE_NOT_FOUND.status_code,
        )
    except PermissionDeniedError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, "error_code") else "PERMISSION_DENIED",
            message=str(e),
            status_code=status.HTTP_403_FORBIDDEN,
        )
    except Exception as e:
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="系统内部错误",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


# ============ 统一审核端点 (Phase C) ============

from enum import Enum as PyEnum


class ReviewAction(str, PyEnum):
    """审核动作枚举"""

    APPROVE = "approve"  # 通过（流转到下一状态）
    REJECT = "reject"  # 驳回（退回原始状态或标记异常）
    REQUEST_REVISION = "request_revision"  # 要求修改（退回投手修改）


class DailyReportReviewRequest(BaseModel):
    """统一审核请求"""

    action: str = Field(..., description="审核动作: approve/reject/request_revision")
    audit_notes: Optional[str] = Field(None, max_length=500, description="审核说明")


class DailyReportReviewResponse(BaseModel):
    """统一审核响应"""

    report_id: int
    old_status: str
    new_status: str
    action: str
    message: str
    warnings: List[str] = Field(default_factory=list, description="Phase 1 警告信息")


@router.post(
    "/{report_id}/review",
    response_model=StandardResponse[DailyReportReviewResponse],
    summary="统一审核日报",
    description="""
    统一的日报审核端点，支持多种审核动作。

    **动作说明:**
    - `approve`: 通过审核，流转到下一状态
    - `reject`: 驳回，标记异常或退回
    - `request_revision`: 要求投手修改

    **状态机流转规则 (STATE_MACHINE.md v2.6):**
    - trend_pending + approve → trend_ok
    - trend_pending + reject → trend_flagged
    - trend_flagged + approve → trend_resolved
    - trend_flagged + request_revision → raw_submitted
    - final_pending + approve → final_confirmed

    **权限:** project_owner/admin
    """,
)
async def review_daily_report(
    report_id: int,
    request: DailyReportReviewRequest,
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(require_role(["project_owner", "admin"])),
):
    """
    统一审核日报 API

    根据当前状态和动作，自动选择正确的状态流转路径。

    Phase 1 行为：
    - 记录审核操作
    - 返回 warnings 字段提示潜在问题
    - 不阻断任何操作
    """
    from backend.core.role_mapping import role_in_list
    from backend.core.phase_config import get_phase_config

    try:
        # 获取日报当前状态
        report = service.get_daily_report(report_id, current_user)
        old_status = report.status
        warnings = []

        # 验证动作有效性
        action = request.action.lower()
        if action not in ["approve", "reject", "request_revision"]:
            return error_response(
                code="VAL_001",
                message=f"无效的审核动作: {action}，允许的值: approve/reject/request_revision",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # 根据当前状态和动作确定目标状态
        transition_map = {
            # (current_status, action) -> target_status
            ("trend_pending", "approve"): "trend_ok",
            ("trend_pending", "reject"): "trend_flagged",
            ("trend_flagged", "approve"): "trend_resolved",
            ("trend_flagged", "request_revision"): "raw_submitted",
            ("trend_ok", "approve"): "final_pending",
            ("trend_resolved", "approve"): "final_pending",
            ("final_pending", "approve"): "final_confirmed",
            ("final_pending", "reject"): "trend_flagged",  # 退回到异常状态
        }

        transition_key = (old_status, action)
        if transition_key not in transition_map:
            return error_response(
                code="STATE_400",
                message=f"当前状态 '{old_status}' 不支持 '{action}' 操作",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        target_status = transition_map[transition_key]

        # 构造审核请求
        audit_request = DailyReportAuditRequest(audit_notes=request.audit_notes)

        # 执行状态流转
        if target_status == "trend_ok":
            report = service._transition_daily_report(
                report_id=report_id,
                target_status=DailyReportStatus.TREND_OK,
                audit_request=audit_request,
                current_user=current_user,
            )
        elif target_status == "trend_flagged":
            report = service.flag_trend_anomaly(report_id, audit_request, current_user)
            warnings.append("日报已标记为趋势异常，需人工复核")
        elif target_status == "trend_resolved":
            report = service.resolve_trend_anomaly(
                report_id, audit_request, current_user
            )
        elif target_status == "raw_submitted":
            # 退回投手修改
            report.status = "raw_submitted"
            report.trend_flag = "normal"
            report.trend_flag_reason = None
            service.db.commit()
            warnings.append("日报已退回投手修改")
        elif target_status == "final_pending":
            # 使用 enter_final_pending
            report = service._transition_daily_report(
                report_id=report_id,
                target_status=DailyReportStatus.FINAL_PENDING,
                audit_request=audit_request,
                current_user=current_user,
            )
        elif target_status == "final_confirmed":
            report = service.confirm_final_report(
                report_id, audit_request, current_user
            )

        # Phase 1 警告
        phase_config = get_phase_config()
        if phase_config.is_phase1_enabled():
            if action == "approve" and old_status == "trend_flagged":
                warnings.append("[Phase 1] 趋势异常已通过审核，Phase 2 将启用更严格的校验")

        new_status = report.status

        # 构建响应
        action_messages = {
            "approve": "审核通过",
            "reject": "审核驳回",
            "request_revision": "已要求修改",
        }

        response = DailyReportReviewResponse(
            report_id=report_id,
            old_status=old_status,
            new_status=new_status,
            action=action,
            message=f"{action_messages.get(action, action)}: {old_status} → {new_status}",
            warnings=warnings,
        )

        logger.info(
            f"Daily report reviewed: id={report_id}, action={action}, "
            f"{old_status} → {new_status}, user={current_user.id}"
        )

        return success_response(data=response, message=response.message)

    except ResourceNotFoundError as e:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message=str(e),
            status_code=BusinessErrorCodes.RESOURCE_NOT_FOUND.status_code,
        )
    except (BusinessLogicError, PermissionDeniedError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, "error_code") else "BIZ_001",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.exception(f"Error in review_daily_report: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="审核失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


# ============ 8 状态机流转端点 (STATE_MACHINE.md v2.6) ============


@router.post(
    "/{report_id}/trend-flag",
    response_model=StandardResponse[DailyReportResponse],
    summary="标记趋势异常",
    description="将日报标记为趋势异常，需人工复核 (trend_pending → trend_flagged)",
)
async def flag_trend_anomaly(
    report_id: int,
    request: DailyReportAuditRequest,
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(require_role(["project_owner", "admin"])),
):
    """
    标记趋势异常API (STATE_MACHINE.md v2.6 第8章)
    trend_pending → trend_flagged
    """
    try:
        report = service.flag_trend_anomaly(report_id, request, current_user)
        report_response = DailyReportResponse.model_validate(report)
        return success_response(data=report_response, message="日报已标记为趋势异常")
    except ResourceNotFoundError as e:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message=str(e),
            status_code=BusinessErrorCodes.RESOURCE_NOT_FOUND.status_code,
        )
    except (BusinessLogicError, PermissionDeniedError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, "error_code") else "BIZ_001",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="系统内部错误",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.post(
    "/{report_id}/trend-resolve",
    response_model=StandardResponse[DailyReportResponse],
    summary="解决趋势异常",
    description="运营确认趋势异常已解决 (trend_flagged → trend_resolved)",
)
async def resolve_trend_anomaly(
    report_id: int,
    request: DailyReportAuditRequest,
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(require_role(["project_owner", "admin"])),
):
    """
    解决趋势异常API (STATE_MACHINE.md v2.6 第8章)
    trend_flagged → trend_resolved
    """
    try:
        report = service.resolve_trend_anomaly(report_id, request, current_user)
        report_response = DailyReportResponse.model_validate(report)
        return success_response(data=report_response, message="趋势异常已解决")
    except ResourceNotFoundError as e:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message=str(e),
            status_code=BusinessErrorCodes.RESOURCE_NOT_FOUND.status_code,
        )
    except (BusinessLogicError, PermissionDeniedError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, "error_code") else "BIZ_001",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="系统内部错误",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.put(
    "/{report_id}/real-spend",
    response_model=StandardResponse[DailyReportResponse],
    summary="录入 real 消耗",
    description="运营录入真实消耗数据 (trend_ok/trend_resolved → final_pending)",
)
async def update_real_spend(
    report_id: int,
    request: RealSpendRequest,
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(require_role(["project_owner", "admin"])),
):
    """
    录入 real 消耗 API (API_SOT.md v9.0 第 9.5 节)
    trend_ok/trend_resolved → final_pending
    """
    try:
        report = service.update_real_spend(report_id, request, current_user)
        report_response = DailyReportResponse.model_validate(report)
        return success_response(data=report_response, message="真实消耗已录入，等待确认final粉数")
    except ResourceNotFoundError as e:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message=str(e),
            status_code=BusinessErrorCodes.RESOURCE_NOT_FOUND.status_code,
        )
    except (BusinessLogicError, PermissionDeniedError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, "error_code") else "BIZ_001",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="系统内部错误",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.put(
    "/{report_id}/final-confirm",
    response_model=StandardResponse[DailyReportResponse],
    summary="确认最终粉数",
    description="确认有效粉数 (TASK-RPT-007)。Phase 1: trend_ok → final_confirmed; Phase 2: final_pending → final_confirmed",
)
async def confirm_final_report(
    report_id: int,
    request: DailyReportAuditRequest,
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(require_role(["project_owner", "admin"])),
):
    """
    确认最终粉数API (TASK-RPT-007, STATE_MACHINE.md v2.8 §4)

    支持两种流转路径:
    - Phase 1 简化流程: trend_ok → final_confirmed (直接确认)
    - Phase 2 完整流程: final_pending → final_confirmed

    权限: project_owner, admin (BR-RPT-008)
    """
    try:
        report = service.confirm_final_report(report_id, request, current_user)
        report_response = DailyReportResponse.model_validate(report)
        return success_response(data=report_response, message="最终粉数已确认")
    except ResourceNotFoundError as e:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message=str(e),
            status_code=BusinessErrorCodes.RESOURCE_NOT_FOUND.status_code,
        )
    except (BusinessLogicError, PermissionDeniedError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, "error_code") else "BIZ_001",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="系统内部错误",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.post(
    "/{report_id}/final-lock",
    response_model=StandardResponse[DailyReportResponse],
    summary="锁定日报",
    description="锁定日报进入计费，终态 (final_confirmed → final_locked)",
)
async def lock_final_report(
    report_id: int,
    request: DailyReportAuditRequest,
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(require_role(["project_owner", "admin"])),
):
    """
    锁定日报API (STATE_MACHINE.md v2.6 第8章)
    final_confirmed → final_locked (终态)
    """
    try:
        report = service.lock_final_report(report_id, request, current_user)
        report_response = DailyReportResponse.model_validate(report)
        return success_response(data=report_response, message="日报已锁定，进入计费")
    except ResourceNotFoundError as e:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message=str(e),
            status_code=BusinessErrorCodes.RESOURCE_NOT_FOUND.status_code,
        )
    except (BusinessLogicError, PermissionDeniedError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, "error_code") else "BIZ_001",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="系统内部错误",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.post(
    "/batch-import",
    response_model=StandardResponse[DailyReportBatchImportResponse],
    summary="批量导入日报",
    description="批量导入日报记录",
)
async def batch_import_daily_reports(
    request: DailyReportBatchImportRequest,
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(require_role(["project_owner", "admin"])),
    parse_errors: List[DailyReportImportError] = [],
):
    """
    批量导入日报API

    Args:
        request: 批量导入请求
        service: 日报服务
        current_user: 当前用户
        parse_errors: 解析阶段的错误列表（来自Excel文件解析）
    """
    try:
        # 记录开始时间
        start_time = datetime.utcnow()

        logger.info(
            f"Starting batch import: user={current_user.id}, "
            f"total_reports={len(request.reports)}, skip_errors={request.skip_errors}"
        )

        # 批量导入
        (
            success_count,
            error_count,
            errors,
            imported_ids,
        ) = service.batch_import_daily_reports(request, current_user)

        # 计算处理时间
        processing_time = (datetime.utcnow() - start_time).total_seconds()

        # 转换错误格式
        error_responses = [
            DailyReportImportError.model_validate(error) for error in errors
        ]

        # 合并解析阶段的错误
        all_errors = parse_errors + error_responses
        total_error_count = len(all_errors)

        # 构建响应
        response = DailyReportBatchImportResponse(
            total_count=len(request.reports) + len(parse_errors),  # 总数包括解析失败的行
            success_count=success_count,
            error_count=total_error_count,
            errors=all_errors,
            imported_ids=imported_ids,
            processing_time_seconds=processing_time,
        )

        logger.info(
            f"Batch import completed: success={success_count}, "
            f"errors={total_error_count}, time={processing_time:.2f}s"
        )

        return success_response(
            data=response, message=f"批量导入完成，成功{success_count}条，失败{total_error_count}条"
        )

    except BusinessLogicError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, "error_code") else "BIZ_001",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="系统内部错误",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.post(
    "/import-file",
    response_model=StandardResponse[DailyReportBatchImportResponse],
    summary="文件导入日报",
    description="通过Excel文件导入日报",
)
async def import_daily_reports_from_file(
    file: UploadFile = File(..., description="Excel文件"),
    skip_errors: bool = Query(True, description="是否跳过错误继续导入（默认True）"),
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(require_role(["project_owner", "admin"])),
):
    """
    文件导入日报API

    改进点：
    - 文件大小限制（5MB）
    - 灵活列名匹配（支持中英文、别名）
    - 详细错误信息（行号+列名+错误原因+修复建议）
    - 支持部分成功（skip_errors=True）
    """
    try:
        logger.info(
            f"Starting Excel import: filename={file.filename}, "
            f"user={current_user.id}, skip_errors={skip_errors}"
        )

        # 1. 验证文件类型
        if not file.filename.endswith((".xlsx", ".xls")):
            logger.warning(f"Invalid file type: {file.filename}")
            return error_response(
                code=BusinessErrorCodes.INVALID_FILE_TYPE.code,
                message="只支持Excel文件格式（.xlsx, .xls）",
                status_code=BusinessErrorCodes.INVALID_FILE_TYPE.status_code,
            )

        # 2. 读取文件内容并验证大小
        contents = await file.read()
        file_size = len(contents)

        if file_size > MAX_FILE_SIZE_BYTES:
            logger.warning(
                f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE_BYTES})"
            )
            return error_response(
                code=BusinessErrorCodes.FILE_TOO_LARGE.code,
                message=f"文件大小{file_size / 1024 / 1024:.2f}MB超过限制{MAX_FILE_SIZE_MB}MB",
                status_code=BusinessErrorCodes.FILE_TOO_LARGE.status_code,
            )

        logger.info(f"File size: {file_size / 1024:.2f}KB")

        # 3. 解析Excel文件
        try:
            df = pd.read_excel(BytesIO(contents))
        except Exception as e:
            logger.error(f"Failed to parse Excel file: {e}")
            return error_response(
                code=BusinessErrorCodes.EXCEL_PARSE_ERROR.code,
                message=f"Excel文件解析失败：{str(e)}",
                status_code=BusinessErrorCodes.EXCEL_PARSE_ERROR.status_code,
            )

        if df.empty:
            logger.warning("Empty Excel file")
            return error_response(
                code=BusinessErrorCodes.EMPTY_FILE.code,
                message="Excel文件为空，没有数据可导入",
                status_code=BusinessErrorCodes.EMPTY_FILE.status_code,
            )

        logger.info(
            f"Excel parsed successfully: {len(df)} rows, columns={list(df.columns)}"
        )

        # 4. 验证列是否完整
        valid, missing_columns = validate_column_exists(list(df.columns))
        if not valid:
            logger.error(f"Missing required columns: {missing_columns}")
            return error_response(
                code=BusinessErrorCodes.MISSING_COLUMNS.code,
                message=f"缺少必需列：{', '.join(missing_columns)}",
                status_code=BusinessErrorCodes.MISSING_COLUMNS.status_code,
            )

        # 5. 逐行解析数据
        reports = []
        parse_errors = []

        for index, row in df.iterrows():
            row_number = index + 2  # +2因为Excel从1开始且第1行是表头

            request, error = parse_excel_row_to_report(
                row, row_number, list(df.columns)
            )

            if error:
                parse_errors.append(error)
                logger.debug(
                    f"Row {row_number} parse error: {error.error_code} - {error.error_message}"
                )
            else:
                reports.append(request)

        logger.info(
            f"Excel parsing completed: {len(reports)} valid rows, "
            f"{len(parse_errors)} error rows"
        )

        # 6. 如果有解析错误且不跳过错误，返回错误
        if parse_errors and not skip_errors:
            logger.warning("Import aborted due to parse errors (skip_errors=False)")
            return success_response(
                data=DailyReportBatchImportResponse(
                    total_count=len(df),
                    success_count=0,
                    error_count=len(parse_errors),
                    errors=parse_errors,
                    imported_ids=[],
                    processing_time_seconds=0,
                ),
                message=f"文件解析失败，共{len(parse_errors)}个错误。请修复后重新导入，或设置skip_errors=true跳过错误行",
            )

        # 7. 如果没有有效数据，返回错误
        if not reports:
            logger.warning("No valid data to import")
            return success_response(
                data=DailyReportBatchImportResponse(
                    total_count=len(df),
                    success_count=0,
                    error_count=len(parse_errors),
                    errors=parse_errors,
                    imported_ids=[],
                    processing_time_seconds=0,
                ),
                message="没有有效数据可导入",
            )

        # 8. 批量导入（调用现有的批量导入API）
        batch_request = DailyReportBatchImportRequest(
            reports=reports, skip_errors=skip_errors
        )

        return await batch_import_daily_reports(
            batch_request, service, current_user, parse_errors  # 传递解析阶段的错误
        )

    except Exception as e:
        logger.error(f"Unexpected error in file import: {e}", exc_info=True)
        return error_response(
            code="SYS-500",
            message=f"文件处理失败：{str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/export", summary="导出日报", description="导出日报数据为Excel文件")
async def export_daily_reports(
    report_date_start: Optional[str] = Query(None, description="开始日期"),
    report_date_end: Optional[str] = Query(None, description="结束日期"),
    ad_account_id: Optional[int] = Query(None, description="广告账户ID"),
    status: Optional[str] = Query(None, description="审核状态"),
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(
        require_role(["finance", "admin", "project_owner", "account_manager"])
    ),
):
    """
    导出日报API

    改进点：
    - 数据量限制（最多5000条）
    - 安全的属性访问（避免因User不存在导致报错）
    - 添加导出日志
    - RBAC过滤（自动应用用户权限）
    """
    try:
        logger.info(
            f"Starting export: user={current_user.id} ({current_user.role}), "
            f"filters: date={report_date_start}~{report_date_end}, "
            f"account={ad_account_id}, status={status}"
        )

        # 构建查询参数
        params = DailyReportQueryParams(
            report_date_start=report_date_start,
            report_date_end=report_date_end,
            ad_account_id=ad_account_id,
            status=status,
        )

        # 先统计总数（检查是否超限）
        _, total = service.get_daily_reports(params, current_user, page=1, page_size=1)

        if total > MAX_EXPORT_ROWS:
            logger.warning(
                f"Export aborted: data count {total} exceeds limit {MAX_EXPORT_ROWS}"
            )
            return error_response(
                code=BusinessErrorCodes.EXPORT_LIMIT_EXCEEDED.code,
                message=(
                    f"导出数据量({total}条)超过限制({MAX_EXPORT_ROWS}条)。"
                    f"请缩小筛选范围（如缩短日期范围、指定账户等）或分批导出"
                ),
                status_code=BusinessErrorCodes.EXPORT_LIMIT_EXCEEDED.status_code,
            )

        # 获取所有符合条件的日报
        reports, _ = service.get_daily_reports(
            params, current_user, page=1, page_size=MAX_EXPORT_ROWS
        )

        if not reports:
            logger.info("No data to export")
            return error_response(
                code=BusinessErrorCodes.NO_DATA.code,
                message="没有符合条件的数据可导出",
                status_code=BusinessErrorCodes.NO_DATA.status_code,
            )

        logger.info(f"Exporting {len(reports)} records")

        # 转换为DataFrame（使用安全的属性访问）
        data = []
        for report in reports:
            data.append(
                {
                    "ID": report.id,
                    "报表日期": report.report_date,
                    "广告账户ID": report.ad_account_id,
                    "广告账户": getattr(report.ad_account, "name", "")
                    if report.ad_account
                    else "",
                    "广告系列": report.campaign_name or "",
                    "广告组": report.ad_group_name or "",
                    "广告创意": report.ad_creative_name or "",
                    "展示次数": report.impressions,
                    "点击次数": report.clicks,
                    "消耗金额": float(report.spend),
                    "转化次数": report.conversions,
                    "新增粉丝": report.new_follows,
                    "CPA": float(report.cpa) if report.cpa else "",
                    "ROAS": float(report.roas) if report.roas else "",
                    "状态": report.status,
                    "创建人": getattr(report.creator, "name", "")
                    if report.creator
                    else "",
                    "创建时间": report.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    if report.created_at
                    else "",
                    "审核人": getattr(report.auditor, "name", "")
                    if report.auditor
                    else "",
                    "审核时间": report.audit_time.strftime("%Y-%m-%d %H:%M:%S")
                    if report.audit_time
                    else "",
                    "备注": report.notes or "",
                    "审核说明": report.audit_notes or "",
                }
            )

        df = pd.DataFrame(data)

        # 创建Excel文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="日报数据")

            # 调整列宽
            worksheet = writer.sheets["日报数据"]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        output.seek(0)

        # 生成文件名
        file_name = f"daily_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        logger.info(f"Export completed: {len(reports)} records, filename={file_name}")

        # 返回文件流
        return StreamingResponse(
            BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={file_name}"},
        )

    except Exception as e:
        logger.error(f"Unexpected error in export: {e}", exc_info=True)
        return error_response(
            code="SYS-500",
            message=f"导出失败：{str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get(
    "/statistics",
    response_model=StandardResponse[DailyReportStatisticsResponse],
    summary="获取日报统计",
    description="获取日报统计数据",
)
async def get_daily_report_statistics(
    report_date_start: Optional[str] = Query(None, description="开始日期"),
    report_date_end: Optional[str] = Query(None, description="结束日期"),
    ad_account_id: Optional[int] = Query(None, description="广告账户ID"),
    status: Optional[str] = Query(None, description="审核状态"),
    media_buyer_id: Optional[int] = Query(None, description="投手ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(
        require_role(["project_owner", "admin", "finance", "account_manager"])
    ),
):
    """
    获取日报统计API
    """
    try:
        # 构建查询参数
        params = DailyReportQueryParams(
            report_date_start=report_date_start,
            report_date_end=report_date_end,
            ad_account_id=ad_account_id,
            status=status,
            media_buyer_id=media_buyer_id,
            project_id=project_id,
        )

        # 获取统计数据
        stats = service.get_daily_report_statistics(params, current_user)

        # 转换为响应格式
        stats_response = DailyReportStatisticsResponse.model_validate(stats)

        return success_response(data=stats_response)

    except Exception as e:
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="系统内部错误",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.get(
    "/{report_id}/audit-logs",
    response_model=StandardResponse[List[DailyReportAuditLogResponse]],
    summary="获取日报审核日志",
    description="获取日报的操作日志记录",
)
async def get_daily_report_audit_logs(
    report_id: int,
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(get_current_user),
):
    """
    获取日报审核日志API

    使用通用 AuditLog 模型，转换为 DailyReportAuditLogResponse 格式
    """
    try:
        # 获取审核日志（返回通用 AuditLog 对象列表）
        logs = service.get_daily_report_audit_logs(report_id, current_user)

        # 转换 AuditLog 为 DailyReportAuditLogResponse 格式
        log_responses = []
        for log in logs:
            log_responses.append(
                DailyReportAuditLogResponse(
                    id=log.id,
                    daily_report_id=int(log.resource_id)
                    if log.resource_id
                    else report_id,
                    action=log.action,
                    old_status=log.old_values.get("status") if log.old_values else None,
                    new_status=log.new_values.get("status") if log.new_values else None,
                    audit_user_id=log.user_id,
                    audit_user_name=log.user.name if log.user else "Unknown",
                    audit_time=log.created_at,
                    audit_notes=log.new_values.get("audit_notes")
                    if log.new_values
                    else None,
                    ip_address=log.ip_address,
                    user_agent=log.user_agent,
                )
            )

        return success_response(data=log_responses)

    except ResourceNotFoundError as e:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message=str(e),
            status_code=BusinessErrorCodes.RESOURCE_NOT_FOUND.status_code,
        )
    except PermissionDeniedError as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, "error_code") else "PERMISSION_DENIED",
            message=str(e),
            status_code=status.HTTP_403_FORBIDDEN,
        )
    except Exception as e:
        logger.exception(f"Unexpected error in get_daily_report_audit_logs: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="系统内部错误",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


# ============ 趋势风控自动化端点 (STATE_MACHINE.md v2.6 第8.3节) ============

from backend.services.trend_risk_control_service import (
    TrendRiskControlService,
    TrendRiskCheckResult,
)
from pydantic import BaseModel
from typing import Dict, Any


class TrendCheckResponse(BaseModel):
    """趋势风控检查响应"""

    report_id: int
    passed: bool
    new_status: str
    triggered_rules: List[str]
    trend_flag_reason: Optional[str] = None
    details: Dict[str, Any]


class BatchTrendCheckResponse(BaseModel):
    """批量趋势风控检查响应"""

    total_checked: int
    passed_count: int
    flagged_count: int
    error_count: int
    results: List[Dict[str, Any]]


def get_trend_risk_service(db: Session = Depends(get_db)) -> TrendRiskControlService:
    """获取趋势风控服务实例"""
    return TrendRiskControlService(db)


@router.post(
    "/{report_id}/trend-check",
    response_model=StandardResponse[TrendCheckResponse],
    summary="执行趋势风控检查",
    description="对指定日报执行 TF-001/002/003 风控规则检查 (trend_pending → trend_ok/trend_flagged)",
)
async def execute_trend_check(
    report_id: int,
    trend_service: TrendRiskControlService = Depends(get_trend_risk_service),
    current_user: User = Depends(require_role(["project_owner", "admin"])),
):
    """
    执行趋势风控检查 API (STATE_MACHINE.md v2.6 第8.3节)

    风控规则:
    - TF-001: 粉数骤降检查 (conversions_raw < 昨日 × 0.5)
    - TF-002: 粉数骤增检查 (conversions_raw > 昨日 × 3)
    - TF-003: 消耗异常检查 (raw_spend > 昨日 × 2)

    状态流转:
    - trend_pending → trend_ok (风控通过)
    - trend_pending → trend_flagged (风控触发)
    """
    try:
        report, check_result = trend_service.execute_trend_check(report_id)

        response = TrendCheckResponse(
            report_id=report.id,
            passed=check_result.passed,
            new_status=report.status,
            triggered_rules=[r.value for r in check_result.triggered_rules],
            trend_flag_reason=check_result.trend_flag_reason,
            details=check_result.details,
        )

        message = (
            "风控检查通过"
            if check_result.passed
            else f"风控异常: {check_result.trend_flag_reason}"
        )
        return success_response(data=response, message=message)

    except ValueError as e:
        return error_response(
            code="STATE_400", message=str(e), status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.exception(f"Error in trend check for report {report_id}: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="风控检查失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.post(
    "/{report_id}/trigger-trend-check",
    response_model=StandardResponse[DailyReportResponse],
    summary="触发趋势风控检查",
    description="将日报状态从 raw_submitted 流转到 trend_pending，准备进行风控检查",
)
async def trigger_trend_check(
    report_id: int,
    trend_service: TrendRiskControlService = Depends(get_trend_risk_service),
    daily_report_service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(require_role(["pitcher", "project_owner", "admin"])),
):
    """
    触发趋势风控检查 API (STATE_MACHINE.md v2.6 第8章)

    状态流转: raw_submitted → trend_pending
    """
    try:
        # 获取日报
        report = daily_report_service.get_daily_report(report_id, current_user)

        # 触发风控检查
        updated_report = trend_service.trigger_trend_check_for_new_report(report)

        report_response = DailyReportResponse.model_validate(updated_report)
        return success_response(
            data=report_response, message="已触发趋势风控检查，状态已更新为 trend_pending"
        )

    except ValueError as e:
        return error_response(
            code="STATE_400", message=str(e), status_code=status.HTTP_400_BAD_REQUEST
        )
    except ResourceNotFoundError as e:
        return error_response(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message=str(e),
            status_code=BusinessErrorCodes.RESOURCE_NOT_FOUND.status_code,
        )
    except Exception as e:
        logger.exception(f"Error triggering trend check for report {report_id}: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="触发风控检查失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.post(
    "/batch-trend-check",
    response_model=StandardResponse[BatchTrendCheckResponse],
    summary="批量执行趋势风控检查",
    description="对所有 trend_pending 状态的日报执行风控检查",
)
async def batch_execute_trend_check(
    ad_account_id: Optional[int] = Query(None, description="广告账户ID筛选"),
    report_date: Optional[str] = Query(None, description="报告日期筛选 (YYYY-MM-DD)"),
    trend_service: TrendRiskControlService = Depends(get_trend_risk_service),
    current_user: User = Depends(require_role(["project_owner", "admin"])),
):
    """
    批量执行趋势风控检查 API (STATE_MACHINE.md v2.6 第8.3节)

    自动对所有 trend_pending 状态的日报执行风控检查

    风控规则:
    - TF-001: 粉数骤降检查
    - TF-002: 粉数骤增检查
    - TF-003: 消耗异常检查
    """
    try:
        # 解析日期
        parsed_date = None
        if report_date:
            from datetime import datetime as dt

            parsed_date = dt.strptime(report_date, "%Y-%m-%d").date()

        # 执行批量检查
        results = trend_service.batch_execute_trend_check(
            ad_account_id=ad_account_id, report_date=parsed_date
        )

        # 统计结果
        passed_count = sum(1 for r in results if r[1] and r[2] is None)
        flagged_count = sum(1 for r in results if not r[1] and r[2] is None)
        error_count = sum(1 for r in results if r[2] is not None)

        # 构建详细结果
        result_details = []
        for report_id, passed, error in results:
            result_details.append(
                {"report_id": report_id, "passed": passed, "error": error}
            )

        response = BatchTrendCheckResponse(
            total_checked=len(results),
            passed_count=passed_count,
            flagged_count=flagged_count,
            error_count=error_count,
            results=result_details,
        )

        return success_response(
            data=response,
            message=f"批量风控检查完成: 通过 {passed_count}, 异常 {flagged_count}, 错误 {error_count}",
        )

    except Exception as e:
        logger.exception(f"Error in batch trend check: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="批量风控检查失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.get(
    "/trend-flagged",
    response_model=StandardResponse[DailyReportListResponse],
    summary="获取趋势异常日报列表",
    description="获取所有被标记为 trend_flagged 状态的日报",
)
async def get_trend_flagged_reports(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    ad_account_id: Optional[int] = Query(None, description="广告账户ID筛选"),
    report_date_start: Optional[str] = Query(None, description="开始日期"),
    report_date_end: Optional[str] = Query(None, description="结束日期"),
    trend_service: TrendRiskControlService = Depends(get_trend_risk_service),
    current_user: User = Depends(require_role(["project_owner", "admin", "finance"])),
):
    """
    获取趋势异常日报列表 API

    返回所有 trend_flagged 状态的日报，用于运营复核
    """
    try:
        # 解析日期
        parsed_start = None
        parsed_end = None
        if report_date_start:
            from datetime import datetime as dt

            parsed_start = dt.strptime(report_date_start, "%Y-%m-%d").date()
        if report_date_end:
            from datetime import datetime as dt

            parsed_end = dt.strptime(report_date_end, "%Y-%m-%d").date()

        # 获取异常日报
        reports = trend_service.get_flagged_reports(
            ad_account_id=ad_account_id,
            report_date_start=parsed_start,
            report_date_end=parsed_end,
            limit=page_size * page,  # 获取足够的数据进行分页
        )

        # 手动分页
        total = len(reports)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_reports = reports[start_idx:end_idx]

        # 转换为响应格式
        report_responses = [
            DailyReportResponse.model_validate(report) for report in paginated_reports
        ]

        return paginated_response(
            items=report_responses, page=page, page_size=page_size, total=total
        )

    except Exception as e:
        logger.exception(f"Error getting flagged reports: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="获取异常日报列表失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


@router.get(
    "/trend-pending-count",
    response_model=StandardResponse[Dict[str, int]],
    summary="获取待风控检查日报数量",
    description="获取当前 trend_pending 状态的日报数量",
)
async def get_trend_pending_count(
    trend_service: TrendRiskControlService = Depends(get_trend_risk_service),
    current_user: User = Depends(require_role(["project_owner", "admin", "finance"])),
):
    """
    获取待风控检查日报数量 API
    """
    try:
        count = trend_service.get_pending_trend_check_count()
        return success_response(
            data={"pending_count": count}, message=f"当前有 {count} 个日报待风控检查"
        )
    except Exception as e:
        logger.exception(f"Error getting pending count: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="获取待检查数量失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
        )


# ============ 用户请求的新端点 (STATE_MACHINE.md v2.6) ============


class FinalCheckResponse(BaseModel):
    """终审检查响应"""

    report_id: int
    passed: bool
    old_status: str
    new_status: str
    message: str
    details: Dict[str, Any] = {}


class BatchApproveRequest(BaseModel):
    """批量审批请求"""

    report_ids: List[int] = Field(..., min_items=1, max_items=100, description="日报ID列表")
    action: str = Field("approve", description="审批动作: approve/confirm/lock")
    notes: Optional[str] = Field(None, max_length=500, description="审批备注")


class BatchApproveResult(BaseModel):
    """单个审批结果"""

    report_id: int
    success: bool
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    error: Optional[str] = None


class BatchApproveResponse(BaseModel):
    """批量审批响应"""

    total: int
    success_count: int
    failed_count: int
    results: List[BatchApproveResult]


@router.post(
    "/{report_id}/final-check",
    response_model=StandardResponse[FinalCheckResponse],
    summary="执行终审检查",
    description="""
    执行终审检查，自动完成 final_pending → final_confirmed 流转。

    检查规则:
    - 验证 real_spend 已录入
    - 验证 conversions_final 有效
    - Phase 1: 仅记录警告，不阻断
    - Phase 2: 强制验证通过

    状态流转 (STATE_MACHINE.md v2.6 §8):
    - final_pending → final_confirmed (检查通过)
    """,
)
async def execute_final_check(
    report_id: int,
    notes: Optional[str] = Query(None, description="审核备注"),
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(require_role(["project_owner", "admin", "finance"])),
):
    """
    执行终审检查 API (STATE_MACHINE.md v2.6 §8)

    类似 trend-check，但用于 final 阶段的自动验证和流转。
    """
    try:
        # 获取日报
        report = service.get_daily_report(report_id, current_user)
        old_status = report.status

        # 验证当前状态
        if report.status != "final_pending":
            return error_response(
                code="STATE-400",
                message=f"当前状态 '{report.status}' 不支持终审检查，需要 'final_pending' 状态",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # 执行检查
        check_details = {}
        warnings = []

        # 检查 real_spend
        if report.real_spend is None or report.real_spend <= 0:
            warnings.append("real_spend 未录入或为零")
            check_details["real_spend_valid"] = False
        else:
            check_details["real_spend_valid"] = True
            check_details["real_spend"] = float(report.real_spend)

        # 检查 conversions_final
        conversions_final = report.conversions_final or report.conversions_raw or 0
        if conversions_final <= 0:
            warnings.append("conversions_final 为零")
            check_details["conversions_valid"] = False
        else:
            check_details["conversions_valid"] = True
            check_details["conversions_final"] = conversions_final

        # Phase 1: 仅警告，不阻断
        from backend.core.phase_config import get_phase_config

        phase_config = get_phase_config()

        check_details["warnings"] = warnings
        check_details["phase"] = (
            "phase1" if phase_config.is_phase1_enabled() else "phase2"
        )

        # 执行状态转换
        audit_request = DailyReportAuditRequest(audit_notes=notes or "终审检查自动通过")
        report = service.confirm_final_report(report_id, audit_request, current_user)

        response = FinalCheckResponse(
            report_id=report.id,
            passed=True,
            old_status=old_status,
            new_status=report.status,
            message="终审检查通过" + (f"，警告: {', '.join(warnings)}" if warnings else ""),
            details=check_details,
        )

        return success_response(data=response, message=response.message)

    except ResourceNotFoundError as e:
        return error_response(
            code="RES-001", message=str(e), status_code=status.HTTP_404_NOT_FOUND
        )
    except (BusinessLogicError, PermissionDeniedError) as e:
        return error_response(
            code=str(e.error_code) if hasattr(e, "error_code") else "BIZ-001",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.exception(f"Error in final check for report {report_id}: {e}")
        return error_response(
            code="SYS-500",
            message="终审检查失败",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post(
    "/batch-approve",
    response_model=StandardResponse[BatchApproveResponse],
    summary="批量审批日报",
    description="""
    批量审批日报，支持多种动作。

    动作说明:
    - approve: 通用审批（根据当前状态自动流转到下一状态）
    - confirm: 确认终审 (final_pending → final_confirmed)
    - lock: 锁定日报 (final_confirmed → final_locked)

    状态机流转规则 (STATE_MACHINE.md v2.6 §8):
    - trend_pending → trend_ok
    - trend_ok/trend_resolved → final_pending
    - final_pending → final_confirmed
    - final_confirmed → final_locked

    权限: project_owner/finance/admin
    """,
)
async def batch_approve_reports(
    request: BatchApproveRequest,
    service: DailyReportService = Depends(get_daily_report_service),
    current_user: User = Depends(require_role(["project_owner", "finance", "admin"])),
):
    """
    批量审批日报 API (STATE_MACHINE.md v2.6 §8)

    支持一次性审批多个日报，提高运营效率。
    """
    results: List[BatchApproveResult] = []
    success_count = 0
    failed_count = 0

    # 定义动作到目标状态的映射
    action_transitions = {
        "approve": {
            "trend_pending": "trend_ok",
            "trend_ok": "final_pending",
            "trend_resolved": "final_pending",
            "final_pending": "final_confirmed",
        },
        "confirm": {
            "final_pending": "final_confirmed",
        },
        "lock": {
            "final_confirmed": "final_locked",
        },
    }

    action = request.action.lower()
    if action not in action_transitions:
        return error_response(
            code="VAL-001",
            message=f"无效的审批动作: {action}，允许值: approve/confirm/lock",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    transition_map = action_transitions[action]
    audit_request = DailyReportAuditRequest(audit_notes=request.notes or f"批量{action}")

    for report_id in request.report_ids:
        try:
            # 获取日报
            report = service.get_daily_report(report_id, current_user)
            old_status = report.status

            # 检查是否支持当前状态的转换
            if old_status not in transition_map:
                results.append(
                    BatchApproveResult(
                        report_id=report_id,
                        success=False,
                        old_status=old_status,
                        error=f"当前状态 '{old_status}' 不支持 '{action}' 操作",
                    )
                )
                failed_count += 1
                continue

            target_status = transition_map[old_status]

            # 执行状态转换
            if target_status == "trend_ok":
                report = service._transition_daily_report(
                    report_id=report_id,
                    target_status=DailyReportStatus.TREND_OK,
                    audit_request=audit_request,
                    current_user=current_user,
                )
            elif target_status == "final_pending":
                report = service._transition_daily_report(
                    report_id=report_id,
                    target_status=DailyReportStatus.FINAL_PENDING,
                    audit_request=audit_request,
                    current_user=current_user,
                )
            elif target_status == "final_confirmed":
                report = service.confirm_final_report(
                    report_id, audit_request, current_user
                )
            elif target_status == "final_locked":
                report = service.lock_final_report(
                    report_id, audit_request, current_user
                )

            results.append(
                BatchApproveResult(
                    report_id=report_id,
                    success=True,
                    old_status=old_status,
                    new_status=report.status,
                )
            )
            success_count += 1

        except ResourceNotFoundError as e:
            results.append(
                BatchApproveResult(
                    report_id=report_id, success=False, error=f"日报不存在: {str(e)}"
                )
            )
            failed_count += 1
        except (BusinessLogicError, PermissionDeniedError) as e:
            results.append(
                BatchApproveResult(report_id=report_id, success=False, error=str(e))
            )
            failed_count += 1
        except Exception as e:
            logger.exception(f"Error approving report {report_id}: {e}")
            results.append(
                BatchApproveResult(
                    report_id=report_id, success=False, error=f"处理失败: {str(e)}"
                )
            )
            failed_count += 1

    response = BatchApproveResponse(
        total=len(request.report_ids),
        success_count=success_count,
        failed_count=failed_count,
        results=results,
    )

    message = f"批量审批完成: 成功 {success_count}, 失败 {failed_count}"
    logger.info(f"Batch approve completed: {message}, user={current_user.id}")

    return success_response(data=response, message=message)
