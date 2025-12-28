"""
周报管理 API 路由 (重构版)

SoT References:
- B3-weekly-brief.md §4.1 API 接口
- API_SOT.md v9.3 标准响应格式
- MASTER.md v4.4 §2.4 (7角色模型)
- ERROR_CODES_SOT.md v2.1 (错误码)

端点列表:
- GET  /weekly-briefs                              - 获取周报列表
- GET  /weekly-briefs/stats                        - 获取周报统计
- GET  /weekly-briefs/{id}                         - 获取周报详情
- POST /weekly-briefs                              - 创建周报
- PUT  /weekly-briefs/{id}                         - 更新周报
- POST /weekly-briefs/{id}/submit                  - 提交周报
- GET  /weekly-briefs/projects/{id}/weekly-summary - 获取项目周汇总

权限矩阵 (MASTER.md v4.4 §2.4 - 7角色模型):
- ceo, admin: 全部周报
- finance: 全部周报 (只读)
- project_owner: 自己负责的项目周报
- supervisor: 团队项目周报
- pitcher: 无权访问
- account_manager: 无权访问

依赖代码块:
- response-envelope: success_response, error_response
- pagination: 分页查询
- permission-filter: 权限过滤
- error-codes: PERM-001, RES-001, BIZ-001, SYS-500

Version: 2.0
Author: Claude Code
"""

import logging
from datetime import date, timedelta
from typing import Literal, Optional, List

from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.orm import Session

from backend.core.dependencies import get_db, get_current_user
from backend.core.response import success_response, error_response
from backend.exceptions.custom_exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ResourceConflictError,
)
from backend.models import User
from backend.schemas.weekly_brief import (
    WeeklyBriefCreateRequest,
    WeeklyBriefUpdateRequest,
    WeeklyBriefResponse,
    WeeklyBriefListResponse,
    WeeklyBriefStatsResponse,
    WeeklyBriefSubmitResponse,
    WeeklySummaryResponse,
)
from backend.services.weekly_brief_service import WeeklyBriefService, get_week_label

logger = logging.getLogger(__name__)


# ========================================
# 错误响应辅助函数
# ========================================

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
    elif isinstance(e, ResourceConflictError):
        return error_response(
            code="BIZ-002",
            message=str(e),
            status_code=409
        )
    elif isinstance(e, BusinessLogicError):
        return error_response(
            code="BIZ-001",
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


router = APIRouter(prefix="/weekly-briefs", tags=["周度简报"])


def _brief_to_response(brief, cpl_trend: Optional[float] = None) -> WeeklyBriefResponse:
    """将 WeeklyBrief 模型转换为响应"""
    return WeeklyBriefResponse(
        id=brief.id,
        project_id=brief.project_id,
        project_name=brief.project.name if brief.project else None,
        week_start=brief.week_start,
        week_end=brief.week_end,
        week_label=get_week_label(brief.week_start),
        submitter_id=brief.submitter_id,
        submitter_name=brief.submitter.full_name if brief.submitter else None,
        status=brief.status,
        weekly_spend=brief.weekly_spend,
        weekly_conversions=brief.weekly_conversions,
        weekly_cpl=brief.weekly_cpl,
        cpl_trend=cpl_trend,
        achievements=brief.achievements,
        issues=brief.issues,
        solutions=brief.solutions,
        next_week_plan=brief.next_week_plan,
        submitted_at=brief.submitted_at,
        created_at=brief.created_at,
        updated_at=brief.updated_at,
    )


@router.get("", response_model=dict)
async def get_weekly_briefs(
    week: Optional[str] = Query(None, description="周次 (如 2025-W51)"),
    week_start: Optional[date] = Query(None, description="周开始日期"),
    project_id: Optional[int] = Query(None, gt=0, description="项目ID"),
    status: Optional[Literal["draft", "submitted"]] = Query(None, description="状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取周报列表

    权限:
    - ceo, admin: 全部
    - project_owner: 仅自己项目
    - supervisor: 团队项目
    - finance: 全部 (只读)
    """
    try:
        service = WeeklyBriefService(db)

        # 解析周次
        parsed_week_start = week_start
        if week and not week_start:
            # 解析 "2025-W51" 格式
            try:
                parts = week.split('-W')
                if len(parts) == 2:
                    year = int(parts[0])
                    week_num = int(parts[1])
                    # 获取该年第一天，然后计算第 N 周的周一
                    first_day = date(year, 1, 1)
                    first_monday = first_day - timedelta(days=first_day.weekday())
                    parsed_week_start = first_monday + timedelta(weeks=week_num - 1)
            except (ValueError, IndexError):
                pass

        briefs, total = service.get_weekly_briefs(
            current_user=current_user,
            week_start=parsed_week_start,
            project_id=project_id,
            status=status,
            page=page,
            page_size=page_size
        )

        # 获取统计
        stats = service.get_weekly_brief_stats(current_user, parsed_week_start)

        items = [_brief_to_response(b) for b in briefs]

        return success_response(
            data={
                "items": [item.model_dump() for item in items],
                "total": total,
                "page": page,
                "page_size": page_size,
                "stats": stats.model_dump()
            },
            message="获取成功"
        )
    except Exception as e:
        return _handle_service_exception(e, "获取周报列表")


@router.get("/stats", response_model=dict)
async def get_weekly_brief_stats(
    week: Optional[str] = Query(None, description="周次 (如 2025-W51)"),
    week_start: Optional[date] = Query(None, description="周开始日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取周报统计

    权限 (MASTER.md v4.4 §2.4): ceo, supervisor, finance, admin
    """
    try:
        service = WeeklyBriefService(db)

        # 解析周次
        parsed_week_start = week_start
        if week and not week_start:
            try:
                parts = week.split('-W')
                if len(parts) == 2:
                    year = int(parts[0])
                    week_num = int(parts[1])
                    first_day = date(year, 1, 1)
                    first_monday = first_day - timedelta(days=first_day.weekday())
                    parsed_week_start = first_monday + timedelta(weeks=week_num - 1)
            except (ValueError, IndexError):
                pass

        stats = service.get_weekly_brief_stats(current_user, parsed_week_start)

        return success_response(
            data=stats.model_dump(),
            message="获取成功"
        )
    except Exception as e:
        return _handle_service_exception(e, "获取周报统计")


@router.get("/{brief_id}", response_model=dict)
async def get_weekly_brief(
    brief_id: int = Path(..., gt=0, description="周报ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取周报详情

    权限 (MASTER.md v4.4 §2.4): project_owner (自己项目), ceo, supervisor, finance, admin
    """
    try:
        service = WeeklyBriefService(db)
        brief = service.get_weekly_brief(brief_id, current_user)

        return success_response(
            data=_brief_to_response(brief).model_dump(),
            message="获取成功"
        )
    except Exception as e:
        return _handle_service_exception(e, "获取周报详情")


@router.post("", response_model=dict)
async def create_weekly_brief(
    request: WeeklyBriefCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建周报

    权限 (MASTER.md v4.4 §2.4): project_owner (自己项目), admin

    业务规则 (B3-weekly-brief.md §7.1):
    - BR-BRIEF-001: 每项目每周只能有一份周报
    - BR-BRIEF-003: week_start 必须是周一
    - BR-BRIEF-004: 创建时自动汇总周消耗/进粉
    """
    try:
        service = WeeklyBriefService(db)
        brief = service.create_weekly_brief(request, current_user)

        return success_response(
            data=_brief_to_response(brief).model_dump(),
            message="周报创建成功"
        )
    except Exception as e:
        return _handle_service_exception(e, "创建周报")


@router.put("/{brief_id}", response_model=dict)
async def update_weekly_brief(
    brief_id: int = Path(..., gt=0, description="周报ID"),
    request: WeeklyBriefUpdateRequest = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新周报

    权限 (MASTER.md v4.4 §2.4): project_owner (草稿, 自己项目), admin

    业务规则:
    - 只能更新草稿状态的周报
    """
    try:
        service = WeeklyBriefService(db)
        brief = service.update_weekly_brief(brief_id, request, current_user)

        return success_response(
            data=_brief_to_response(brief).model_dump(),
            message="周报更新成功"
        )
    except Exception as e:
        return _handle_service_exception(e, "更新周报")


@router.post("/{brief_id}/submit", response_model=dict)
async def submit_weekly_brief(
    brief_id: int = Path(..., gt=0, description="周报ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    提交周报

    权限 (MASTER.md v4.4 §2.4): project_owner (自己项目), admin

    业务规则 (B3-weekly-brief.md §7.2):
    - BR-BRIEF-010: Phase 1 无强制必填项
    - BR-BRIEF-011: 提交后状态变为 submitted，不可修改
    """
    try:
        service = WeeklyBriefService(db)
        brief = service.submit_weekly_brief(brief_id, current_user)

        return success_response(
            data=WeeklyBriefSubmitResponse(
                id=brief.id,
                status=brief.status,
                submitted_at=brief.submitted_at
            ).model_dump(),
            message="周报提交成功"
        )
    except Exception as e:
        return _handle_service_exception(e, "提交周报")


@router.get("/export", response_model=dict)
async def export_weekly_briefs(
    week: Optional[str] = Query(None, description="周次"),
    project_id: Optional[int] = Query(None, gt=0, description="项目ID"),
    format: Literal["pdf", "excel"] = Query("excel", description="导出格式"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出周报

    权限 (MASTER.md v4.4 §2.4): project_owner (自己项目), ceo, admin

    TODO: 实现实际的导出逻辑
    """
    try:
        # TODO: 实现导出逻辑
        return success_response(
            data={"message": "导出功能开发中"},
            message="导出功能开发中"
        )
    except Exception as e:
        return _handle_service_exception(e, "导出周报")


# ========== 项目周数据汇总 ==========

@router.get("/projects/{project_id}/weekly-summary", response_model=dict)
async def get_project_weekly_summary(
    project_id: int = Path(..., gt=0, description="项目ID"),
    week_start: date = Query(..., description="周开始日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目周数据汇总

    权限 (MASTER.md v4.4 §2.4): project_owner (自己项目), ceo, supervisor, admin
    """
    try:
        service = WeeklyBriefService(db)
        summary = service.get_project_weekly_summary(project_id, week_start, current_user)

        return success_response(
            data=summary.model_dump(),
            message="获取成功"
        )
    except Exception as e:
        return _handle_service_exception(e, "获取项目周数据汇总")
