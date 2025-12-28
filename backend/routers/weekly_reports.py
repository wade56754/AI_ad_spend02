"""
周报管理 API 路由 (TASK-WEEKLY-002, TASK-WEEKLY-003, TASK-WEEKLY-004)

SoT References:
- DATA_SCHEMA.md v5.6 §weekly_briefs
- B3-weekly-brief.md §4.1
- STATE_MACHINE.md v2.6 §13.2 (周报状态机)
- MASTER.md v4.6 §2.4 (6角色模型)
- ERROR_CODES_SOT.md v2.1

端点列表:
- POST /weekly-reports - 创建周报
- PUT /weekly-reports/{id} - 更新周报
- POST /weekly-reports/{id}/submit - 提交周报

权限矩阵 (MASTER.md v4.6 §2.4):
- project_owner: 创建/更新/提交自己项目的周报
- admin: 创建/更新/提交任意项目周报

错误码:
- BIZ_001: 该周周报已存在
- BIZ_002: 只能编辑草稿状态的周报
- BIZ_003: 周报已提交，不可重复提交
- PERM-001: 权限不足
- RES-001: 资源不存在

Version: 1.2
"""

import logging

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from backend.core.dependencies import get_db, get_current_user
from backend.core.response import success_response, error_response
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
)
from backend.models import User
from backend.schemas.weekly_report import WeeklyReportCreate, WeeklyReportUpdate, WeeklyReportResponse
from backend.services.weekly_report_service import WeeklyReportService


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/weekly-reports", tags=["周报管理"])


def _handle_service_exception(e: Exception, context: str = "操作"):
    """处理服务层异常，转换为标准响应"""
    if isinstance(e, PermissionDeniedError):
        return error_response(
            code="PERM-001",
            message=str(e),
            status_code=403
        )
    elif isinstance(e, ResourceNotFoundError):
        return error_response(
            code="RES-001",
            message=str(e),
            status_code=404
        )
    elif isinstance(e, BusinessLogicError):
        return error_response(
            code="BIZ_001",
            message=str(e),
            status_code=400
        )
    else:
        logger.exception(f"服务异常 - {context}: {e}")
        return error_response(
            code="SYS-500",
            message=f"系统内部错误: {str(e)}",
            status_code=500
        )


@router.post(
    "",
    summary="创建周报",
    description="""
创建项目周报。

**业务规则** (B3-weekly-brief.md §7.1):
- BR-BRIEF-001: 每项目每周只能有一份周报
- BR-BRIEF-002: project_owner 可创建自己项目的周报
- BR-BRIEF-003: week_start_date 必须是周一

**权限控制** (MASTER.md v4.6 §2.4):
- project_owner: 创建自己项目的周报
- admin: 创建任意项目周报

**自动汇总**:
- 周消耗: 自动汇总该周的 ad_spend_daily
- 周进粉: 自动汇总该周的 daily_reports.conversions_final
- 周CPL: 周消耗 / 周进粉
""",
    responses={
        201: {"description": "创建成功"},
        400: {"description": "业务错误 (BIZ_001: 该周周报已存在)"},
        403: {"description": "权限不足 (PERM-001)"},
        404: {"description": "资源不存在 (RES-001)"},
    },
    status_code=status.HTTP_201_CREATED
)
async def create_weekly_report(
    request: WeeklyReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建周报 (TASK-WEEKLY-002)

    SoT Reference:
    - DATA_SCHEMA.md v5.6 §weekly_briefs
    - B3-weekly-brief.md §7.1

    请求参数:
    - project_id: 项目ID (必填)
    - week_start_date: 周开始日期，必须是周一 (必填)
    - issues: 遇到问题 (可选)
    - next_week_plan: 下周计划 (可选)
    - achievements: 本周成果 (可选)
    - solutions: 解决方案 (可选)

    返回:
    - 创建的周报详情
    """
    logger.info(
        f"POST /weekly-reports: user={current_user.email}, "
        f"project_id={request.project_id}, week={request.week_start_date}"
    )

    try:
        service = WeeklyReportService(db)
        brief = service.create_weekly_report(request, current_user)

        return success_response(
            data=service.to_response(brief).model_dump(mode='json'),
            message="周报创建成功"
        )
    except Exception as e:
        return _handle_service_exception(e, "创建周报")


@router.put(
    "/{report_id}",
    summary="更新周报",
    description="""
更新项目周报。

**业务规则** (B3-weekly-brief.md §7.1):
- 只能更新 draft 状态的周报
- 不能修改 project_id 和 week_start_date
- 更新时自动刷新汇总数据

**权限控制** (MASTER.md v4.6 §2.4):
- project_owner: 更新自己项目的周报
- admin: 更新任意项目周报
""",
    responses={
        200: {"description": "更新成功"},
        400: {"description": "业务错误 (BIZ_002: 只能编辑草稿状态的周报)"},
        403: {"description": "权限不足 (PERM-001)"},
        404: {"description": "周报不存在 (RES-001)"},
    }
)
async def update_weekly_report(
    report_id: int = Path(..., gt=0, description="周报ID"),
    request: WeeklyReportUpdate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新周报 (TASK-WEEKLY-003)

    SoT Reference:
    - DATA_SCHEMA.md v5.6 §weekly_briefs
    - B3-weekly-brief.md §7.1

    路径参数:
    - report_id: 周报ID

    请求参数 (均为可选，只更新提供的字段):
    - issues: 遇到问题
    - next_week_plan: 下周计划
    - achievements: 本周成果
    - solutions: 解决方案

    返回:
    - 更新后的周报详情
    """
    logger.info(
        f"PUT /weekly-reports/{report_id}: user={current_user.email}"
    )

    try:
        service = WeeklyReportService(db)
        brief = service.update_weekly_report(report_id, request, current_user)

        return success_response(
            data=service.to_response(brief).model_dump(mode='json'),
            message="周报更新成功"
        )
    except Exception as e:
        return _handle_service_exception(e, "更新周报")


@router.post(
    "/{report_id}/submit",
    summary="提交周报",
    description="""
提交项目周报。

**状态机** (STATE_MACHINE.md v2.6 §13.2):
- draft → submitted (终态)

**业务规则** (B3-weekly-brief.md §7.2):
- BR-SUBMIT-001: 只能提交 draft 状态的周报
- BR-SUBMIT-002: project_owner 可提交自己项目的周报
- BR-SUBMIT-003: 提交时自动刷新汇总数据
- BR-SUBMIT-004: Phase 1 无强制必填项

**权限控制** (MASTER.md v4.6 §2.4):
- project_owner: 提交自己项目的周报
- admin: 提交任意项目周报

**提交后**:
- 状态变为 submitted (终态)
- 记录 submitted_at 时间戳
- 更新 submitter_id 为当前用户
""",
    responses={
        200: {"description": "提交成功"},
        400: {"description": "业务错误 (BIZ_003: 周报已提交，不可重复提交)"},
        403: {"description": "权限不足 (PERM-001)"},
        404: {"description": "周报不存在 (RES-001)"},
    }
)
async def submit_weekly_report(
    report_id: int = Path(..., gt=0, description="周报ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    提交周报 (TASK-WEEKLY-004)

    SoT Reference:
    - DATA_SCHEMA.md v5.6 §weekly_briefs
    - STATE_MACHINE.md v2.6 §13.2
    - B3-weekly-brief.md §7.2

    路径参数:
    - report_id: 周报ID

    返回:
    - 提交后的周报详情 (status=submitted)
    """
    logger.info(
        f"POST /weekly-reports/{report_id}/submit: user={current_user.email}"
    )

    try:
        service = WeeklyReportService(db)
        brief = service.submit_weekly_report(report_id, current_user)

        return success_response(
            data=service.to_response(brief).model_dump(mode='json'),
            message="周报提交成功"
        )
    except Exception as e:
        return _handle_service_exception(e, "提交周报")
